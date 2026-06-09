"""Read-only filesystem discovery workflow."""

import csv
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.config import get_settings
from app.connectors.mise_filesystem import (
    FilesystemScanError,
    FolderInventoryEntry,
    MISEFilesystem,
)


class FilesystemDiscoverySummary(BaseModel):
    """Summary of a filesystem discovery run."""

    model_config = ConfigDict(frozen=True)

    roots_scanned: list[str]
    folders_scanned: int
    warnings: list[str] = Field(default_factory=list)


class FilesystemDiscoveryResult(BaseModel):
    """Filesystem discovery result."""

    model_config = ConfigDict(frozen=True)

    summary: FilesystemDiscoverySummary
    inventory: list[FolderInventoryEntry]

    def to_export_payload(self) -> dict[str, Any]:
        """Return a JSON-serializable export payload."""
        return self.model_dump(mode="json")


class FilesystemDiscoveryService:
    """Coordinate read-only filesystem scans."""

    def __init__(self, filesystem: MISEFilesystem | None = None) -> None:
        self._filesystem = filesystem or MISEFilesystem()

    def scan(
        self,
        *,
        root: str | Path | None = None,
        max_depth: int = 4,
        out: str | Path | None = None,
        pretty: bool = False,
    ) -> FilesystemDiscoveryResult:
        """Scan one root, or configured MISE roots when root is omitted."""
        roots = [Path(root)] if root is not None else _configured_roots()
        if not roots:
            raise FilesystemScanError(
                "No filesystem root provided and MISE_PROJECT_ROOT/MISE_REGISTRY_ROOT are empty"
            )

        inventory: list[FolderInventoryEntry] = []
        warnings: list[str] = []
        scanned_roots: list[str] = []
        for scan_root in roots:
            try:
                entries = self._filesystem.scan(scan_root, max_depth=max_depth)
            except FilesystemScanError as exc:
                warnings.append(str(exc))
                continue

            scanned_roots.append(str(scan_root))
            inventory.extend(entries)

        result = FilesystemDiscoveryResult(
            summary=FilesystemDiscoverySummary(
                roots_scanned=scanned_roots,
                folders_scanned=len(inventory),
                warnings=warnings,
            ),
            inventory=inventory,
        )

        if out is not None:
            export_inventory(result, out=out, pretty=pretty)

        return result


def export_inventory(
    result: FilesystemDiscoveryResult,
    *,
    out: str | Path,
    pretty: bool = False,
) -> None:
    """Export folder inventory as JSON or CSV based on file extension."""
    output_path = Path(out)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.suffix.lower() == ".csv":
        _write_csv(result, output_path)
        return

    indent = 2 if pretty else None
    output_path.write_text(
        json.dumps(result.to_export_payload(), indent=indent, sort_keys=pretty),
        encoding="utf-8",
    )


def _write_csv(result: FilesystemDiscoveryResult, output_path: Path) -> None:
    fieldnames = [
        "folder_path",
        "folder_name",
        "parent_path",
        "modified_time",
        "inferred_registry_file_ref",
        "inferred_project_name",
        "file_count",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for entry in result.inventory:
            writer.writerow(entry.model_dump(mode="json"))


def _configured_roots() -> list[Path]:
    filesystem_settings = get_settings().filesystem
    return [
        Path(root)
        for root in (filesystem_settings.mise_project_root, filesystem_settings.mise_registry_root)
        if root
    ]
