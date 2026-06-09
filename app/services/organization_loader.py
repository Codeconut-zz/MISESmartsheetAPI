"""Load and validate MISE organization blueprints."""

from pathlib import Path
from typing import Any

from pydantic import ValidationError
import yaml

from app.domain.organization import OrganizationBlueprint


class BlueprintLoadError(ValueError):
    """Raised when a blueprint cannot be loaded or validated."""


def load_organization_blueprint(path: str | Path) -> OrganizationBlueprint:
    """Load and validate an organization blueprint YAML file."""
    blueprint_path = Path(path)
    if not blueprint_path.exists():
        raise BlueprintLoadError(f"Blueprint file not found: {blueprint_path}")

    try:
        raw_data = yaml.safe_load(blueprint_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise BlueprintLoadError(f"Blueprint YAML is invalid: {exc}") from exc

    if not isinstance(raw_data, dict):
        raise BlueprintLoadError("Blueprint YAML must contain a mapping at the document root")

    try:
        return OrganizationBlueprint.model_validate(raw_data)
    except ValidationError as exc:
        raise BlueprintLoadError(f"Blueprint validation failed: {exc}") from exc


def summarize_blueprint(blueprint: OrganizationBlueprint) -> dict[str, Any]:
    """Return a compact JSON-serializable blueprint summary."""
    return {
        "ministry_code": blueprint.ministry.code,
        "department_count": len(blueprint.departments),
        "division_count": sum(len(department.divisions) for department in blueprint.departments),
        "role_count": len(blueprint.roles),
        "reporting_line_count": len(blueprint.reporting_lines),
    }
