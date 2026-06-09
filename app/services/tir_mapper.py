"""Map Smartsheet TIR rows into domain objects."""

from pathlib import Path
from typing import Any

from pydantic import ValidationError
import yaml

from app.domain.tir import TechnicalIntakeRequest

DEFAULT_TIR_COLUMN_MAP_PATH = Path("config/mappings/tir_column_map.yaml")


class TIRMappingError(ValueError):
    """Raised when a TIR row cannot be mapped."""


def load_tir_column_map(path: str | Path = DEFAULT_TIR_COLUMN_MAP_PATH) -> dict[str, str]:
    """Load display-name to internal-field TIR column mappings."""
    mapping_path = Path(path)
    try:
        raw_data = yaml.safe_load(mapping_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise TIRMappingError(f"TIR column map YAML is invalid: {exc}") from exc
    except OSError as exc:
        raise TIRMappingError(f"TIR column map could not be read: {mapping_path}") from exc

    if not isinstance(raw_data, dict) or not isinstance(raw_data.get("columns"), dict):
        raise TIRMappingError("TIR column map must contain a 'columns' mapping")

    return {str(display_name): str(field_name) for display_name, field_name in raw_data["columns"].items()}


class TIRMapper:
    """Map Smartsheet sheet rows into TechnicalIntakeRequest objects."""

    def __init__(self, column_map: dict[str, str] | None = None) -> None:
        self._column_map = column_map or load_tir_column_map()
        self._required_fields = set(TechnicalIntakeRequest.model_fields)

    def map_row(
        self,
        *,
        row: dict[str, Any],
        columns: list[dict[str, Any]],
    ) -> TechnicalIntakeRequest:
        """Map one Smartsheet row into a TIR domain model."""
        display_to_id = _display_name_to_column_id(columns)
        missing_display_names = self.missing_columns(columns)
        if missing_display_names:
            formatted_names = ", ".join(missing_display_names)
            raise TIRMappingError(f"Smartsheet sheet is missing required TIR columns: {formatted_names}")

        cells_by_column_id = _cells_by_column_id(row.get("cells", []))
        model_data: dict[str, Any] = {}
        for display_name, field_name in self._column_map.items():
            column_id = display_to_id[display_name]
            model_data[field_name] = _cell_value(cells_by_column_id.get(column_id, {}))

        missing_fields = sorted(self._required_fields - set(model_data))
        if missing_fields:
            raise TIRMappingError(f"TIR column map is missing fields: {', '.join(missing_fields)}")

        try:
            return TechnicalIntakeRequest.model_validate(model_data)
        except ValidationError as exc:
            raise TIRMappingError(f"TIR row validation failed: {exc}") from exc

    def missing_columns(self, columns: list[dict[str, Any]]) -> list[str]:
        """Return required display columns that are absent from a Smartsheet column list."""
        display_to_id = _display_name_to_column_id(columns)
        return [display_name for display_name in self._column_map if display_name not in display_to_id]


def _display_name_to_column_id(columns: list[dict[str, Any]]) -> dict[str, int]:
    return {str(column["title"]): int(column["id"]) for column in columns if "title" in column and "id" in column}


def _cells_by_column_id(cells: Any) -> dict[int, dict[str, Any]]:
    if not isinstance(cells, list):
        return {}

    return {
        int(cell["columnId"]): cell
        for cell in cells
        if isinstance(cell, dict) and "columnId" in cell
    }


def _cell_value(cell: dict[str, Any]) -> Any:
    for key in ("value", "displayValue"):
        value = cell.get(key)
        if value is not None:
            return value

    return ""
