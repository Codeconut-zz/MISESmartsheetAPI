"""Reconcile TIR records with discovered project folders."""

from pathlib import Path
import json
import re
from typing import Literal

from difflib import SequenceMatcher
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from app.connectors.mise_filesystem import FolderInventoryEntry
from app.domain.tir import TechnicalIntakeRequest

ReconciliationCategory = Literal[
    "MATCHED",
    "MISSING_FOLDER",
    "DUPLICATE_REGISTRY_REFERENCE",
    "MISSING_REGISTRY_REFERENCE",
    "POSSIBLE_MATCH",
    "MANUAL_REVIEW_REQUIRED",
]


class ReconciliationResult(BaseModel):
    """Result of reconciling one TIR record."""

    model_config = ConfigDict(frozen=True)

    registry_file_ref: str
    project_name: str
    contact_email: str
    category: ReconciliationCategory
    confidence_score: int = Field(ge=0, le=100)
    matched_folder_path: str | None = None
    reasons: list[str]


class ReconciliationService:
    """Match TIR records against folder inventory."""

    def reconcile(
        self,
        *,
        tir_records: list[TechnicalIntakeRequest],
        folder_inventory: list[FolderInventoryEntry],
    ) -> list[ReconciliationResult]:
        """Return reconciliation results for each TIR record."""
        folders_by_ref = _folders_by_registry_ref(folder_inventory)
        folders_by_project_name = _folders_by_project_name(folder_inventory)

        return [
            self._reconcile_one(
                tir,
                folder_inventory=folder_inventory,
                folders_by_ref=folders_by_ref,
                folders_by_project_name=folders_by_project_name,
            )
            for tir in tir_records
        ]

    def _reconcile_one(
        self,
        tir: TechnicalIntakeRequest,
        *,
        folder_inventory: list[FolderInventoryEntry],
        folders_by_ref: dict[str, list[FolderInventoryEntry]],
        folders_by_project_name: dict[str, list[FolderInventoryEntry]],
    ) -> ReconciliationResult:
        registry_file_ref = tir.registry_file_ref.strip()
        if not registry_file_ref:
            return _result(
                tir,
                category="MISSING_REGISTRY_REFERENCE",
                confidence_score=0,
                reasons=["TIR record does not include a registry file reference"],
            )

        ref_matches = folders_by_ref.get(_normalize_ref(registry_file_ref), [])
        if len(ref_matches) > 1:
            return _result(
                tir,
                category="DUPLICATE_REGISTRY_REFERENCE",
                confidence_score=80,
                matched_folder_path=ref_matches[0].folder_path,
                reasons=[
                    f"Registry reference {registry_file_ref} matched {len(ref_matches)} folders",
                    "Manual review is required before choosing a project folder",
                ],
            )
        if len(ref_matches) == 1:
            return _result(
                tir,
                category="MATCHED",
                confidence_score=100,
                matched_folder_path=ref_matches[0].folder_path,
                reasons=[f"Exact registry reference match on {registry_file_ref}"],
            )

        name_matches = folders_by_project_name.get(_normalize_name(tir.project_name), [])
        if len(name_matches) == 1:
            return _result(
                tir,
                category="MATCHED",
                confidence_score=85,
                matched_folder_path=name_matches[0].folder_path,
                reasons=["Exact normalized project name match"],
            )
        if len(name_matches) > 1:
            return _result(
                tir,
                category="MANUAL_REVIEW_REQUIRED",
                confidence_score=65,
                matched_folder_path=name_matches[0].folder_path,
                reasons=["Multiple folders share the normalized project name"],
            )

        possible_matches = _possible_project_name_matches(tir.project_name, folder_inventory)
        if len(possible_matches) == 1:
            folder, score = possible_matches[0]
            return _result(
                tir,
                category="POSSIBLE_MATCH",
                confidence_score=score,
                matched_folder_path=folder.folder_path,
                reasons=["Fuzzy project name similarity requires manual review"],
            )
        if len(possible_matches) > 1:
            folder, score = possible_matches[0]
            return _result(
                tir,
                category="MANUAL_REVIEW_REQUIRED",
                confidence_score=score,
                matched_folder_path=folder.folder_path,
                reasons=["Multiple fuzzy project name candidates require manual review"],
            )

        return _result(
            tir,
            category="MISSING_FOLDER",
            confidence_score=0,
            reasons=["No folder matched registry reference or project name"],
        )


def load_tir_records_export(path: str | Path) -> list[TechnicalIntakeRequest]:
    """Load normalized TIR records from a TIR pull export."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    records = payload.get("normalized", payload) if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise ValueError("TIR export must contain a list or a 'normalized' list")

    return [TechnicalIntakeRequest.model_validate(record) for record in records]


def load_folder_inventory_export(path: str | Path) -> list[FolderInventoryEntry]:
    """Load folder inventory from a filesystem discovery export."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    records = payload.get("inventory", payload) if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise ValueError("Folder export must contain a list or an 'inventory' list")

    return [FolderInventoryEntry.model_validate(record) for record in records]


def export_reconciliation_results(results: list[ReconciliationResult], out: str | Path) -> None:
    """Export reconciliation results as XLSX, CSV, or JSON."""
    output_path = Path(out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [result.model_dump(mode="json") for result in results]
    if output_path.suffix.lower() == ".xlsx":
        pd.DataFrame(rows).to_excel(output_path, index=False)
        return
    if output_path.suffix.lower() == ".csv":
        pd.DataFrame(rows).to_csv(output_path, index=False)
        return

    output_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def _folders_by_registry_ref(
    folder_inventory: list[FolderInventoryEntry],
) -> dict[str, list[FolderInventoryEntry]]:
    folders_by_ref: dict[str, list[FolderInventoryEntry]] = {}
    for folder in folder_inventory:
        if folder.inferred_registry_file_ref:
            folders_by_ref.setdefault(_normalize_ref(folder.inferred_registry_file_ref), []).append(folder)

    return folders_by_ref


def _folders_by_project_name(
    folder_inventory: list[FolderInventoryEntry],
) -> dict[str, list[FolderInventoryEntry]]:
    folders_by_name: dict[str, list[FolderInventoryEntry]] = {}
    for folder in folder_inventory:
        if folder.inferred_project_name:
            folders_by_name.setdefault(_normalize_name(folder.inferred_project_name), []).append(folder)

    return folders_by_name


def _possible_project_name_matches(
    project_name: str,
    folder_inventory: list[FolderInventoryEntry],
) -> list[tuple[FolderInventoryEntry, int]]:
    normalized_project_name = _normalize_name(project_name)
    scored_matches: list[tuple[FolderInventoryEntry, int]] = []
    for folder in folder_inventory:
        if not folder.inferred_project_name:
            continue

        score = int(
            SequenceMatcher(
                None,
                normalized_project_name,
                _normalize_name(folder.inferred_project_name),
            ).ratio()
            * 100
        )
        if score >= 70:
            scored_matches.append((folder, score))

    return sorted(scored_matches, key=lambda item: item[1], reverse=True)


def _result(
    tir: TechnicalIntakeRequest,
    *,
    category: ReconciliationCategory,
    confidence_score: int,
    reasons: list[str],
    matched_folder_path: str | None = None,
) -> ReconciliationResult:
    return ReconciliationResult(
        registry_file_ref=tir.registry_file_ref,
        project_name=tir.project_name,
        contact_email=tir.contact_email,
        category=category,
        confidence_score=confidence_score,
        matched_folder_path=matched_folder_path,
        reasons=reasons,
    )


def _normalize_ref(value: str) -> str:
    return re.sub(r"[-_\s]+", "-", value.strip().upper())


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
