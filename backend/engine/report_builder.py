"""Report JSON builder for CareerFit Day 13.

The builder is intentionally thin: it does not analyze, score, rank, or write
narrative text. It only places completed engine outputs into the Report JSON
contract used by downstream renderers.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any


REPORT_TOP_LEVEL_KEYS = (
    "meta",
    "career_profile",
    "target_job_analysis",
    "market_intelligence",
    "skill_mapping",
    "evidence_mapping",
    "requirement_matching",
    "fit_score",
    "strength_analysis",
    "gap_analysis",
    "career_guidance",
    "executive_summary",
    "final_assessment",
)


def build_report(
    *,
    primary_profile: str,
    secondary_profiles: list[str],
    confidence_level: str,
    warning_message: str | None,
    evidenceMapping: Any,
    scores: Any,
    strengths: Any,
    gaps: Any,
    executive_summary: Any,
    strength_narratives: Any,
    gap_narratives: Any,
    skill_explanations: Any,
    job_outlook: Any,
    final_assessment: Any,
    version: str = "1.0.0",
    generated_at: str | None = None,
    career_profile: Any | None = None,
    target_job_analysis: Any | None = None,
    market_intelligence: Any | None = None,
    skill_mapping: Any | None = None,
    requirement_matching: Any | None = None,
) -> dict[str, Any]:
    """Assemble a Report JSON from completed engine outputs.

    `generated_at` is supplied by the caller so repeated calls with the same
    inputs stay deterministic.
    """

    report = {
        "meta": _build_meta(
            primary_profile=primary_profile,
            secondary_profiles=secondary_profiles,
            confidence_level=confidence_level,
            warning_message=warning_message,
            version=version,
            generated_at=generated_at,
        ),
        "career_profile": _json_ready(career_profile or {}),
        "target_job_analysis": _json_ready(target_job_analysis or {}),
        "market_intelligence": _json_ready(market_intelligence or {}),
        "skill_mapping": _json_ready(skill_mapping or {}),
        "evidence_mapping": _json_ready(evidenceMapping),
        "requirement_matching": _json_ready(requirement_matching or {}),
        "fit_score": _json_ready(scores),
        "strength_analysis": _json_ready(strengths),
        "gap_analysis": _json_ready(gaps),
        "career_guidance": _build_career_guidance(
            strength_narratives=strength_narratives,
            gap_narratives=gap_narratives,
            skill_explanations=skill_explanations,
            job_outlook=job_outlook,
        ),
        "executive_summary": _json_ready(executive_summary),
        "final_assessment": _json_ready(final_assessment),
    }
    return {key: report[key] for key in REPORT_TOP_LEVEL_KEYS}


def _build_meta(
    *,
    primary_profile: str,
    secondary_profiles: list[str],
    confidence_level: str,
    warning_message: str | None,
    version: str,
    generated_at: str | None,
) -> dict[str, Any]:
    return {
        "primary_profile": primary_profile,
        "secondary_profiles": _json_ready(secondary_profiles),
        "confidence_level": confidence_level,
        "warning_message": warning_message,
        "version": version,
        "generated_at": generated_at,
    }


def _build_career_guidance(
    *,
    strength_narratives: Any,
    gap_narratives: Any,
    skill_explanations: Any,
    job_outlook: Any,
) -> dict[str, Any]:
    return {
        "strength_narratives": _json_ready(strength_narratives),
        "gap_narratives": _json_ready(gap_narratives),
        "skill_explanations": _json_ready(skill_explanations),
        "job_outlook": _json_ready(job_outlook),
    }


def _json_ready(value: Any) -> Any:
    """Return a JSON-serializable copy without changing report semantics."""
    if hasattr(value, "model_dump"):
        return _json_ready(value.model_dump())
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _json_ready(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(child) for child in value]
    return value
