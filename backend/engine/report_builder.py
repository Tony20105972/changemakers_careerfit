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
    "summary",
    "careerProfile",
    "targetJobAnalysis",
    "skillMapping",
    "evidenceMapping",
    "scores",
    "strengths",
    "gaps",
    "skill_explanations",
    "skill_narratives",
    "reportSections",
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
    report_id: str | None = None,
    llm_used: bool = False,
    weight_source: str = "MANUAL_V1",
    evidence_count: int | None = None,
    careerProfile: Any | None = None,
    targetJobAnalysis: Any | None = None,
    skillMapping: Any | None = None,
    skill_narratives: Any | None = None,
    reportSections: Any | None = None,
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
            report_id=report_id,
            llm_used=llm_used,
            weight_source=weight_source,
            evidence_count=evidence_count,
        ),
        "summary": _build_summary(executive_summary),
        "careerProfile": _json_ready(careerProfile or {}),
        "targetJobAnalysis": _json_ready(targetJobAnalysis or {}),
        "skillMapping": _json_ready(skillMapping or {}),
        "evidenceMapping": _json_ready(evidenceMapping),
        "scores": _json_ready(scores),
        "strengths": _json_ready(strengths),
        "gaps": _json_ready(gaps),
        "skill_explanations": _build_skill_explanations(
            skill_explanations=skill_explanations,
            strength_narratives=strength_narratives,
            gap_narratives=gap_narratives,
        ),
        "skill_narratives": _build_skill_narratives(
            executive_summary=executive_summary,
            skill_narratives=skill_narratives,
            strength_narratives=strength_narratives,
            gap_narratives=gap_narratives,
            job_outlook=job_outlook,
            final_assessment=final_assessment,
        ),
        "reportSections": _json_ready(reportSections or _default_report_sections()),
    }
    return {key: report[key] for key in REPORT_TOP_LEVEL_KEYS}


def _build_summary(executive_summary: Any) -> dict[str, Any]:
    summary = _json_ready(executive_summary)
    if isinstance(summary, dict):
        return summary
    return {"one_line": summary}


def _build_meta(
    *,
    primary_profile: str,
    secondary_profiles: list[str],
    confidence_level: str,
    warning_message: str | None,
    version: str,
    generated_at: str | None,
    report_id: str | None,
    llm_used: bool,
    weight_source: str,
    evidence_count: int | None,
) -> dict[str, Any]:
    return {
        "report_id": report_id,
        "generated_at": generated_at,
        "engine_version": version,
        "llm_used": llm_used,
        "primary_profile": primary_profile,
        "secondary_profiles": _json_ready(secondary_profiles),
        "weight_source": weight_source,
        "confidence_level": confidence_level,
        "evidence_count": evidence_count,
        "warning_message": warning_message,
    }


def _build_skill_narratives(
    *,
    executive_summary: Any,
    skill_narratives: Any,
    strength_narratives: Any,
    gap_narratives: Any,
    job_outlook: Any,
    final_assessment: Any,
) -> dict[str, Any]:
    narratives = _json_ready(skill_narratives or {})
    if not isinstance(narratives, dict):
        narratives = {}
    return {
        "career_context": narratives.get("career_context", _summary_one_line(executive_summary)),
        "market_context": narratives.get("market_context", _first_narrative_text(gap_narratives, job_outlook)),
        "development_direction": narratives.get("development_direction", _json_ready(final_assessment)),
        "job_outlook": _json_ready(job_outlook),
        "final_assessment": _json_ready(final_assessment),
    }


def _build_skill_explanations(
    *,
    skill_explanations: Any,
    strength_narratives: Any,
    gap_narratives: Any,
) -> list[Any]:
    explanations = _json_ready(skill_explanations)
    if isinstance(explanations, list) and explanations:
        return explanations
    assembled = []
    assembled.extend(_narratives_to_explanations(strength_narratives, "strength"))
    assembled.extend(_narratives_to_explanations(gap_narratives, "gap"))
    return assembled


def _narratives_to_explanations(narratives: Any, source: str) -> list[dict[str, Any]]:
    items = _json_ready(narratives)
    if not isinstance(items, list):
        return []
    explanations = []
    for item in items:
        if not isinstance(item, dict):
            continue
        explanations.append(
            {
                "skill_key": item.get("skill_key"),
                "label_ko": item.get("label_ko"),
                "source": source,
                "career_context": item.get("narrative"),
                "market_context": item.get("evidence_summary"),
                "development_direction": item.get("summary_phrase"),
            }
        )
    return explanations


def _summary_one_line(executive_summary: Any) -> Any:
    summary = _build_summary(executive_summary)
    return summary.get("one_line")


def _first_narrative_text(narratives: Any, fallback: Any) -> Any:
    items = _json_ready(narratives)
    if isinstance(items, list) and items and isinstance(items[0], dict):
        return items[0].get("narrative") or _json_ready(fallback)
    return _json_ready(fallback)


def _default_report_sections() -> list[dict[str, Any]]:
    return [
        {"section_id": "cover", "order": 1, "enabled": True},
        {"section_id": "executive_summary", "order": 2, "enabled": True},
        {"section_id": "career_profile", "order": 3, "enabled": True},
        {"section_id": "target_job", "order": 4, "enabled": True},
        {"section_id": "skill_mapping", "order": 5, "enabled": True},
        {"section_id": "evidence_mapping", "order": 6, "enabled": True},
        {"section_id": "fit_score", "order": 7, "enabled": True},
        {"section_id": "strength_analysis", "order": 8, "enabled": True},
        {"section_id": "gap_analysis", "order": 9, "enabled": True},
        {"section_id": "skill_intelligence", "order": 10, "enabled": True},
        {"section_id": "career_narrative", "order": 11, "enabled": True},
        {"section_id": "final_assessment", "order": 12, "enabled": True},
    ]


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
