"""Read-only MISE filesystem connector."""

from datetime import UTC, datetime
from pathlib import Path
import re

from pydantic import BaseModel, ConfigDict, Field

REGISTRY_REF_PATTERN = re.compile(r"\b(?:MISE[-_\s]?)?[A-Z]{2,6}[-_\s]?\d{2,6}\b", re.IGNORECASE)


class FolderInventoryEntry(BaseModel):
    """Read-only folder inventory record."""

    model_config = ConfigDict(frozen=True)

    folder_path: str
    folder_name: str
    parent_path: str
    modified_time: datetime | None
    inferred_registry_file_ref: str | None = None
    inferred_project_name: str | None = None
    file_count: int = Field(ge=0)


class FilesystemScanError(ValueError):
    """Raised when filesystem discovery cannot scan a requested root."""


class MISEFilesystem:
    """Read-only scanner for MISE project and registry folders."""

    def scan(self, root: str | Path, *, max_depth: int = 4) -> list[FolderInventoryEntry]:
        """Scan folders under a root up to max_depth."""
        root_path = Path(root).expanduser()
        if max_depth < 0:
            raise FilesystemScanError("max_depth must be zero or greater")
        if not root_path.exists():
            raise FilesystemScanError(f"Root path does not exist: {root_path}")
        if not root_path.is_dir():
            raise FilesystemScanError(f"Root path is not a directory: {root_path}")

        entries: list[FolderInventoryEntry] = []
        self._scan_directory(root_path, depth=0, max_depth=max_depth, entries=entries)
        return entries

    def _scan_directory(
        self,
        directory: Path,
        *,
        depth: int,
        max_depth: int,
        entries: list[FolderInventoryEntry],
    ) -> None:
        entries.append(_folder_entry(directory))

        if depth >= max_depth:
            return

        try:
            children = sorted(directory.iterdir(), key=lambda path: path.name.lower())
        except OSError:
            return

        for child in children:
            try:
                if child.is_dir() and not child.is_symlink():
                    self._scan_directory(child, depth=depth + 1, max_depth=max_depth, entries=entries)
            except OSError:
                continue


def infer_registry_file_ref(folder_name: str) -> str | None:
    """Infer a registry reference from a folder name."""
    match = REGISTRY_REF_PATTERN.search(folder_name)
    if not match:
        return None

    return re.sub(r"[-_\s]+", "-", match.group(0).upper())


def infer_project_name(folder_name: str, registry_file_ref: str | None) -> str | None:
    """Infer a project name by removing a leading registry reference."""
    if not registry_file_ref:
        return folder_name.strip() or None

    pattern = re.compile(re.escape(registry_file_ref).replace("\\-", r"[-_\s]+"), re.IGNORECASE)
    project_name = pattern.sub("", folder_name, count=1)
    project_name = project_name.strip(" -_")
    return project_name or None


def _folder_entry(directory: Path) -> FolderInventoryEntry:
    registry_file_ref = infer_registry_file_ref(directory.name)
    return FolderInventoryEntry(
        folder_path=str(directory),
        folder_name=directory.name,
        parent_path=str(directory.parent),
        modified_time=_modified_time(directory),
        inferred_registry_file_ref=registry_file_ref,
        inferred_project_name=infer_project_name(directory.name, registry_file_ref),
        file_count=_direct_file_count(directory),
    )


def _modified_time(directory: Path) -> datetime | None:
    try:
        return datetime.fromtimestamp(directory.stat().st_mtime, tz=UTC)
    except OSError:
        return None


def _direct_file_count(directory: Path) -> int:
    count = 0
    try:
        for child in directory.iterdir():
            if child.is_file():
                count += 1
    except OSError:
        return 0

    return count
