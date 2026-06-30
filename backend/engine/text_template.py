"""Text template orchestrator for CareerFit narratives.

Narrative generation lives in ``narrative_composer.py``. This module preserves
the existing public API and delegates to the composer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.engine.narrative_composer import (
    DEFAULT_REGISTRY_PATH,
    compose_report_narratives,
    load_skill_registry,
)


def load_skill_descriptions(path: str | Path | None = None) -> dict[str, dict[str, Any]]:
    """Load the V1 skill intelligence registry."""
    return load_skill_registry(path)


def generate_narratives(
    report: dict[str, Any],
    registry: dict[str, dict[str, Any]] | None = None,
    registry_path: str | Path | None = None,
) -> dict[str, Any]:
    """Generate narrative text from a report-shaped dictionary."""
    return build_narrative_text(
        meta=_as_dict(report.get("meta")),
        scores=_as_dict(report.get("scores")),
        strengths=_as_list(report.get("strengths")),
        gaps=_as_list(report.get("gaps")),
        evidence_mapping=_as_list(report.get("evidenceMapping") or report.get("evidence_mapping")),
        registry=registry,
        registry_path=registry_path,
    )


def build_narrative_text(
    meta: dict[str, Any],
    scores: dict[str, Any],
    strengths: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    evidence_mapping: list[dict[str, Any]],
    registry: dict[str, dict[str, Any]] | None = None,
    registry_path: str | Path | None = None,
) -> dict[str, Any]:
    """Delegate narrative composition to the Narrative Composer engine."""
    return compose_report_narratives(
        meta=_as_dict(meta),
        scores=_as_dict(scores),
        strengths=_as_list(strengths),
        gaps=_as_list(gaps),
        evidence_mapping=_as_list(evidence_mapping),
        registry=registry,
        registry_path=registry_path,
    )


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []
