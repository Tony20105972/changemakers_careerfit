"""Deterministic narrative template engine for CareerFit Day 12.

This module turns scored report data into deterministic reader-facing career
narratives. It only uses report fields and the skill description registry.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_REGISTRY_PATH = Path(__file__).resolve().parents[2] / "data" / "skill_descriptions.json"

PROFILE_LABELS = {
    "hr": "인사(HR)",
    "marketing": "마케팅",
    "data": "데이터",
    "product": "프로덕트",
    "operations": "운영(Operations)",
    "sales": "영업(Sales)",
    "design": "디자인",
    "finance": "재무(Finance)",
    "engineering": "엔지니어링",
    "customer_success": "Customer Success",
}

FIT_LABELS = {
    "EXCELLENT_FIT": "매우 높은 적합도",
    "GOOD_FIT": "높은 적합도",
    "MODERATE_FIT": "기본적인 적합도",
    "LOW_FIT": "제한적인 적합도",
}

LOW_CONFIDENCE_PREFIX = (
    "입력 정보가 제한적이므로 아래 해석은 확인된 근거 안에서 조심스럽게 읽어야 합니다."
)


def load_skill_descriptions(path: str | Path | None = None) -> dict[str, dict[str, Any]]:
    """Load the Day 12 skill intelligence registry."""
    registry_path = Path(path) if path is not None else DEFAULT_REGISTRY_PATH
    with registry_path.open(encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("skill description registry must be a JSON object")
    return data


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
    """Build all Day 12 narrative fields.

    Output keys:
    - executive_summary
    - strength_narratives[]
    - gap_narratives[]
    - skill_explanations[]
    - job_outlook
    - final_assessment
    """
    descriptions = registry if registry is not None else load_skill_descriptions(registry_path)
    meta = _as_dict(meta)
    scores = _as_dict(scores)
    strengths = _ordered_items(strengths)
    gaps = _ordered_items(gaps)
    evidence_mapping = _as_list(evidence_mapping)

    confidence_level = str(meta.get("confidence_level") or "").upper()
    is_low_confidence = confidence_level == "LOW"
    primary_profile = str(meta.get("primary_profile") or "")
    profile_label = _profile_label(primary_profile)
    score = _score_value(scores)
    fit_level = str(meta.get("fit_level") or scores.get("fit_level") or "")

    strength_narratives = [
        _build_strength_narrative(item, descriptions, evidence_mapping, is_low_confidence)
        for item in strengths
    ]
    gap_narratives = [
        _build_gap_narrative(item, descriptions, evidence_mapping, is_low_confidence)
        for item in gaps
    ]
    skill_explanations = _build_skill_explanations(
        strengths=strengths,
        gaps=gaps,
        registry=descriptions,
        evidence_mapping=evidence_mapping,
        is_low_confidence=is_low_confidence,
    )

    output = {
        "executive_summary": _build_executive_summary(
            profile_label=profile_label,
            score=score,
            fit_level=fit_level,
            strengths=strengths,
            gaps=gaps,
            registry=descriptions,
            is_low_confidence=is_low_confidence,
        ),
        "strength_narratives": strength_narratives,
        "gap_narratives": gap_narratives,
        "skill_explanations": skill_explanations,
        "job_outlook": _build_job_outlook(
            profile_label=profile_label,
            score=score,
            scores=scores,
            strengths=strengths,
            gaps=gaps,
            registry=descriptions,
            is_low_confidence=is_low_confidence,
        ),
        "final_assessment": _build_final_assessment(
            profile_label=profile_label,
            score=score,
            strengths=strengths,
            gaps=gaps,
            registry=descriptions,
            is_low_confidence=is_low_confidence,
        ),
    }
    _validate_output(output)
    return output


def _build_executive_summary(
    profile_label: str,
    score: float,
    fit_level: str,
    strengths: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    registry: dict[str, dict[str, Any]],
    is_low_confidence: bool,
) -> str:
    strength_labels = _labels_for_items(strengths[:3], registry)
    gap_labels = _labels_for_items(gaps[:2], registry)
    fit_text = FIT_LABELS.get(fit_level, _fit_text_from_score(score))
    strength_text = _join_korean(strength_labels) if strength_labels else "확인된 강점"
    gap_text = _join_korean(gap_labels) if gap_labels else "추가 확인이 필요한 영역"
    prefix = f"{LOW_CONFIDENCE_PREFIX} " if is_low_confidence else ""
    return (
        f"{prefix}{profile_label} 기준 리포트는 {fit_text}를 보여주며, 현재 점수는 {score:.1f}점입니다. "
        f"강점은 {strength_text} 영역에서 주로 확인되고, 해석상 보완 공백은 {gap_text} 영역에 집중됩니다."
    )


def _build_strength_narrative(
    item: dict[str, Any],
    registry: dict[str, dict[str, Any]],
    evidence_mapping: list[dict[str, Any]],
    is_low_confidence: bool,
) -> dict[str, Any]:
    skill_key = _skill_key(item)
    description = _description_for(skill_key, item, registry)
    evidence_text = _evidence_summary(item, evidence_mapping)
    tone = " 다만 입력 근거가 제한적이므로 강점의 범위는 보수적으로 해석됩니다." if is_low_confidence else ""
    narrative = (
        f"{description['strength_narrative']} {description['business_value']} "
        f"{evidence_text}{tone}"
    )
    return {
        "skill_key": skill_key,
        "label_ko": description["label_ko"],
        "rank": _rank_value(item),
        "narrative": _clean_text(narrative),
        "evidence_summary": evidence_text,
        "summary_phrase": description["summary_phrase"],
    }


def _build_gap_narrative(
    item: dict[str, Any],
    registry: dict[str, dict[str, Any]],
    evidence_mapping: list[dict[str, Any]],
    is_low_confidence: bool,
) -> dict[str, Any]:
    skill_key = _skill_key(item)
    description = _description_for(skill_key, item, registry)
    evidence_text = _evidence_summary(item, evidence_mapping)
    severity = str(item.get("severity") or item.get("gap_severity") or "UNKNOWN")
    tone = " 입력 정보가 적기 때문에 이 공백은 실제 부재보다 서술 부족에 가까울 수 있습니다." if is_low_confidence else ""
    narrative = (
        f"{description['gap_narrative']} {description['market_context']} "
        f"{evidence_text}{tone}"
    )
    return {
        "skill_key": skill_key,
        "label_ko": description["label_ko"],
        "rank": _rank_value(item),
        "severity": severity,
        "narrative": _clean_text(narrative),
        "evidence_summary": evidence_text,
        "summary_phrase": description["summary_phrase"],
    }


def _build_skill_explanations(
    strengths: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    registry: dict[str, dict[str, Any]],
    evidence_mapping: list[dict[str, Any]],
    is_low_confidence: bool,
) -> list[dict[str, Any]]:
    explanations = []
    seen = set()
    for source, items in (("strength", strengths), ("gap", gaps)):
        for item in items:
            skill_key = _skill_key(item)
            if not skill_key or skill_key in seen:
                continue
            seen.add(skill_key)
            description = _description_for(skill_key, item, registry)
            evidence_text = _evidence_summary(item, evidence_mapping)
            development_direction = description["development_direction"]
            if is_low_confidence:
                development_direction = (
                    f"{development_direction} 현재 입력 정보가 제한적이므로 이 방향은 확정 행동 지시가 아니라 "
                    "리포트 해석을 위한 보수적 설명으로 다룹니다."
                )
            explanations.append(
                {
                    "skill_key": skill_key,
                    "label_ko": description["label_ko"],
                    "source": source,
                    "career_context": _clean_text(f"{description['definition']} {evidence_text}"),
                    "market_context": description["market_context"],
                    "development_direction": _clean_text(development_direction),
                }
            )
    return explanations


def _build_job_outlook(
    profile_label: str,
    score: float,
    scores: dict[str, Any],
    strengths: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    registry: dict[str, dict[str, Any]],
    is_low_confidence: bool,
) -> str:
    unique_score = _number(scores.get("unique_total") or scores.get("unique_score"))
    common_score = _number(scores.get("common_total") or scores.get("common_score"))
    top_strength = _label_for_item(strengths[0], registry) if strengths else "확인된 강점"
    top_gap = _label_for_item(gaps[0], registry) if gaps else "추가 검증 영역"
    prefix = f"{LOW_CONFIDENCE_PREFIX} " if is_low_confidence else ""
    return (
        f"{prefix}{profile_label} 관점에서 현재 전망은 {top_strength} 같은 확인된 강점이 직무 적합도를 지탱하는 구조입니다. "
        f"고유 역량 {unique_score:.1f}점, 공통 역량 {common_score:.1f}점의 분포를 보면 {top_gap} 영역의 설명 공백이 "
        f"전체 평가의 해석 폭을 결정하며, 총점 {score:.1f}점은 강점과 보완 영역이 함께 존재하는 상태로 읽힙니다."
    )


def _build_final_assessment(
    profile_label: str,
    score: float,
    strengths: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    registry: dict[str, dict[str, Any]],
    is_low_confidence: bool,
) -> str:
    strength_text = _join_korean(_labels_for_items(strengths[:2], registry)) or "확인된 강점"
    gap_text = _join_korean(_labels_for_items(gaps[:2], registry)) or "추가 확인 영역"
    prefix = f"{LOW_CONFIDENCE_PREFIX} " if is_low_confidence else ""
    return (
        f"{prefix}최종적으로 이 리포트는 {profile_label} 기준에서 {strength_text}을 중심으로 한 커리어 근거를 확인합니다. "
        f"동시에 {gap_text}은 점수나 Evidence를 새로 만들지 않고도 설명상 보완이 필요한 영역이며, "
        f"현재 {score:.1f}점은 확인된 경험과 드러나지 않은 경험 사이의 균형으로 해석됩니다."
    )


def _evidence_summary(item: dict[str, Any], evidence_mapping: list[dict[str, Any]]) -> str:
    evidence_items = _evidence_for_item(item, evidence_mapping)
    if not evidence_items:
        return "현재 연결된 원문 근거는 제한적이며, 해당 스킬은 점수와 매칭 결과를 중심으로 해석됩니다."
    texts = []
    for evidence in evidence_items[:2]:
        original = _clean_text(str(evidence.get("original_text") or ""))
        if original:
            texts.append(f"“{_clip(original, 90)}”")
    if not texts:
        return "연결된 evidence_id는 있으나 원문 텍스트가 없어 매칭 결과를 중심으로 해석됩니다."
    return f"확인 근거로는 {' / '.join(texts)}가 사용됩니다."


def _evidence_for_item(item: dict[str, Any], evidence_mapping: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {str(e.get("evidence_id")): e for e in evidence_mapping if e.get("evidence_id")}
    evidence_ids = [str(value) for value in item.get("evidence_ids", []) if str(value) in by_id]
    if evidence_ids:
        return [by_id[evidence_id] for evidence_id in sorted(set(evidence_ids))]
    skill_key = _skill_key(item)
    return [e for e in evidence_mapping if str(e.get("skill_key") or "") == skill_key]


def _description_for(
    skill_key: str,
    item: dict[str, Any],
    registry: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    description = dict(registry.get(skill_key) or {})
    label = str(item.get("label_ko") or description.get("label_ko") or skill_key or "스킬")
    fallback = {
        "label_ko": label,
        "definition": f"{label} 역량은 목표 직무에서 업무 맥락을 이해하고 실행 기준을 만드는 데 사용됩니다. 현재 registry에 상세 설명이 없어 리포트의 매칭 결과를 중심으로 보수적으로 해석합니다.",
        "person_profile": f"{label} 역량이 강한 사람은 관련 상황의 목적과 기준을 먼저 파악합니다. 이후 필요한 정보를 정리해 팀이 같은 방향으로 움직이도록 돕습니다.",
        "workplace_behavior": f"실무에서는 {label} 관련 회의, 문서, 고객 접점, 내부 협업 과정에서 드러납니다. 특히 여러 사람이 같은 기준으로 일해야 할 때 업무 흐름을 정리하는 방식으로 나타납니다.",
        "business_value": f"조직 안에서 {label} 역량은 실행 기준을 명확하게 만들고 협업 비용을 줄입니다. 이 역량은 개인의 경험을 팀의 반복 가능한 성과로 확장하는 데 기여합니다.",
        "career_relevance": f"{label} 경험은 목표 직무 적합도를 설명하는 보조 근거가 됩니다. 특히 관련 경험이 구체적으로 드러날수록 커리어 해석의 설득력이 높아집니다.",
        "market_context": f"채용시장에서는 {label} 역량을 실제 업무 장면에서 어떻게 사용했는지를 중요하게 봅니다. 단순 보유 여부보다 조직 기여 방식과 결과를 함께 읽습니다.",
        "strength_narrative": f"당신의 경험에서 {label} 역량이 강점으로 나타난다면, 이는 관련 업무 장면을 실제로 다루어본 근거가 있다는 의미입니다. 이 강점은 목표 직무에서 실행과 협업을 안정적으로 만드는 기반이 됩니다.",
        "gap_narrative": f"{label} 역량이 부족한 영역으로 나타난다면, 이는 경험 서술에서 관련 장면이 충분히 드러나지 않았다는 의미일 수 있습니다. 목표 직무에서 이 역량이 중요할수록 설명 공백으로 해석됩니다.",
        "development_direction": f"{label} 역량은 관련 상황, 본인의 역할, 판단 기준, 결과를 함께 설명할 때 더 선명하게 드러납니다. 이 설명은 행동 지시가 아니라 현재 Evidence를 읽는 방향을 제시합니다.",
        "summary_phrase": f"{label} 경험을 직무 맥락과 조직 기여로 연결하는 역량",
        "keywords": [label],
    }
    for key, value in fallback.items():
        if not description.get(key):
            description[key] = value
    return description


def _validate_output(output: dict[str, Any]) -> None:
    _assert_no_banned_text(output)
    _assert_no_empty(output)


def _assert_no_banned_text(value: Any) -> None:
    banned_terms = (
        "expected" + "_score" + "_gain",
        "diffi" + "culty",
        "time" + "_estimate",
        "{",
        "}",
        "TO" + "DO",
        "T" + "BD",
    )
    if isinstance(value, dict):
        for child in value.values():
            _assert_no_banned_text(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_banned_text(child)
    elif isinstance(value, str):
        for term in banned_terms:
            if term in value:
                raise ValueError(f"narrative output contains forbidden or placeholder text: {term}")


def _assert_no_empty(value: Any) -> None:
    if isinstance(value, dict):
        for child in value.values():
            _assert_no_empty(child)
    elif isinstance(value, list):
        if not value:
            return
        for child in value:
            _assert_no_empty(child)
    elif isinstance(value, str) and not value.strip():
        raise ValueError("narrative output contains an empty string")


def _ordered_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        [_as_dict(item) for item in _as_list(items)],
        key=lambda item: (_rank_value(item), _skill_key(item)),
    )


def _rank_value(item: dict[str, Any]) -> int:
    value = item.get("rank", item.get("priority_order", 999))
    try:
        return int(value)
    except (TypeError, ValueError):
        return 999


def _skill_key(item: dict[str, Any]) -> str:
    return str(item.get("skill_key") or item.get("requirement_key") or "").strip()


def _label_for_item(item: dict[str, Any], registry: dict[str, dict[str, Any]]) -> str:
    skill_key = _skill_key(item)
    return str(item.get("label_ko") or registry.get(skill_key, {}).get("label_ko") or skill_key or "스킬")


def _labels_for_items(items: list[dict[str, Any]], registry: dict[str, dict[str, Any]]) -> list[str]:
    return [_label_for_item(item, registry) for item in items if _skill_key(item) or item.get("label_ko")]


def _profile_label(profile: str) -> str:
    return PROFILE_LABELS.get(profile, profile or "목표 직무")


def _score_value(scores: dict[str, Any]) -> float:
    return _number(scores.get("total") or scores.get("total_score"))


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _fit_text_from_score(score: float) -> str:
    if score >= 90:
        return "매우 높은 적합도"
    if score >= 70:
        return "높은 적합도"
    if score >= 50:
        return "기본적인 적합도"
    return "제한적인 적합도"


def _join_korean(values: list[str]) -> str:
    cleaned = [value for value in values if value]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    return ", ".join(cleaned[:-1]) + f", {cleaned[-1]}"


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _clean_text(text: str) -> str:
    return " ".join(str(text or "").split())


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []
