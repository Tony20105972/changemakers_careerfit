#!/usr/bin/env python3
"""Deterministic gap analyzer for CareerFit Contract v1.5."""

from __future__ import annotations


GAP_LEVELS = {"NONE", "WEAK", "PARTIAL"}
GAP_LEVEL_FACTOR = {
    "NONE": 1.0,
    "WEAK": 0.75,
    "PARTIAL": 0.5,
}
SKILL_TYPE_WEIGHT = {
    "UNIQUE": 0.65,
    "COMMON": 0.35,
}
SEVERITY_PRIORITY = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
}
REASON_LEVEL_KO = {
    "NONE": "확인되지 않음",
    "WEAK": "매우 부족함",
    "PARTIAL": "부분적으로 부족함",
    "STRONG": "일부 확인됨",
    "FULL": "충분히 확인됨",
}
HIGH_MEDIUM_LIMIT = 4
LOW_LIMIT = 2


def filter_gap_candidates(matches: list[dict]) -> list[dict]:
    """NONE, WEAK, PARTIAL match만 gap 후보로 통과시킨다."""
    candidates = []
    for match in matches or []:
        if _match_level(match) in GAP_LEVELS:
            candidates.append(dict(match))
    return candidates


def classify_severity(match: dict, requirements: list[dict]) -> str:
    """is_core, skill_type, match_level을 severity matrix에 따라 분류한다."""
    requirement = _find_requirement(match, requirements)
    is_core = bool(requirement.get("is_core", False))
    skill_type = _skill_type(match, requirement)
    level = _match_level(match)
    if is_core and level in {"NONE", "WEAK"}:
        return "CRITICAL"
    if skill_type == "UNIQUE" and level in {"NONE", "WEAK"}:
        return "HIGH"
    if skill_type == "UNIQUE" and level == "PARTIAL":
        return "MEDIUM"
    if skill_type == "COMMON" and level in {"NONE", "WEAK"}:
        return "MEDIUM"
    return "LOW"


def compute_gap_score(match: dict) -> float:
    """결여도 factor와 skill_type weight를 곱해 gap_score를 계산한다."""
    level = _match_level(match)
    skill_type = _skill_type(match, {})
    score = GAP_LEVEL_FACTOR.get(level, 0.0) * SKILL_TYPE_WEIGHT.get(skill_type, SKILL_TYPE_WEIGHT["COMMON"])
    return round(score, 4)


def build_gap_reason(match: dict, taxonomy: dict) -> str:
    """label_ko와 match_level을 사용해 template reason을 생성한다."""
    label = _label_ko(match, {}, taxonomy)
    level_ko = REASON_LEVEL_KO.get(_match_level(match), "부분적으로 부족함")
    evidence_note = _gap_evidence_note(match)
    return f"{label} 관련 경험이 {level_ko}. {evidence_note}"


def build_recommendation_hint(match: dict, taxonomy: dict) -> str:
    """label_ko를 사용해 template recommendation hint를 생성한다."""
    label = _label_ko(match, {}, taxonomy)
    return f"{label} 관련 프로젝트 또는 자격 취득 검토 권장"


def rank_gaps(candidates: list[dict]) -> list[dict]:
    """core/UNIQUE 결핍 우선, severity와 gap_score, skill_key 순으로 정렬한다."""
    ranked = sorted(
        candidates or [],
        key=_gap_rank_key,
    )
    return [dict(item) for item in ranked]


def analyze_gaps(
    matches: list[dict],
    requirements: list[dict],
    taxonomy: dict,
    confidence_level: str,
) -> list[dict]:
    """gap 후보 필터링, severity/점수화, 정렬, LOW fallback을 수행해 gaps[]를 반환한다."""
    candidates = []
    for match in filter_gap_candidates(matches):
        requirement = _find_requirement(match, requirements)
        normalized = _merge_match_requirement(match, requirement)
        normalized["requirement_order"] = _requirement_order(normalized, requirements)
        normalized["severity"] = classify_severity(normalized, requirements)
        normalized["gap_score"] = compute_gap_score(normalized)
        candidates.append(normalized)

    candidates = _deduplicate_by_skill_key(candidates)
    selected = _rank_for_confidence(candidates, confidence_level)
    limit = LOW_LIMIT if str(confidence_level).upper() == "LOW" else HIGH_MEDIUM_LIMIT
    selected = selected[:limit]
    if str(confidence_level).upper() == "LOW" and not selected:
        selected = _fallback_gap_candidates(matches, requirements)[:1]
    return [_build_gap(item, taxonomy, rank) for rank, item in enumerate(selected, start=1)]


def _deduplicate_by_skill_key(candidates: list[dict]) -> list[dict]:
    best_by_skill = {}
    for candidate in candidates or []:
        skill_key = _skill_key(candidate)
        if not skill_key:
            continue
        current = best_by_skill.get(skill_key)
        if current is None or _gap_dedupe_key(candidate) < _gap_dedupe_key(current):
            best_by_skill[skill_key] = candidate
    return [best_by_skill[key] for key in sorted(best_by_skill)]


def _fallback_gap_candidates(matches: list[dict], requirements: list[dict]) -> list[dict]:
    fallback_pool = []
    for match in matches or []:
        if _match_level(match) in {"FULL", "STRONG"}:
            continue
        requirement = _find_requirement(match, requirements)
        normalized = _merge_match_requirement(match, requirement)
        normalized["requirement_order"] = _requirement_order(normalized, requirements)
        normalized["severity"] = classify_severity(normalized, requirements)
        normalized["gap_score"] = compute_gap_score(normalized)
        fallback_pool.append(normalized)
    return rank_gaps(fallback_pool)


def _build_gap(match: dict, taxonomy: dict, rank: int) -> dict:
    label = _label_ko(match, {}, taxonomy)
    return {
        "rank": rank,
        "skill_key": _skill_key(match),
        "label_ko": label,
        "severity": str(match.get("severity") or "LOW"),
        "match_level": _match_level(match),
        "gap_score": round(float(match.get("gap_score", compute_gap_score(match))), 4),
        "reason": build_gap_reason(match, taxonomy),
        "recommendation_hint": build_recommendation_hint(match, taxonomy),
    }


def _merge_match_requirement(match: dict, requirement: dict) -> dict:
    merged = dict(requirement)
    merged.update(match)
    if not merged.get("skill_type"):
        merged["skill_type"] = _skill_type(match, requirement)
    if not merged.get("label_ko"):
        merged["label_ko"] = requirement.get("label_ko")
    return merged


def _find_requirement(match: dict, requirements: list[dict]) -> dict:
    match_requirement_id = match.get("requirement_id")
    match_skill_key = _skill_key(match)
    for requirement in requirements or []:
        if match_requirement_id and requirement.get("requirement_id") == match_requirement_id:
            return dict(requirement)
    for requirement in requirements or []:
        if _skill_key(requirement) == match_skill_key:
            return dict(requirement)
    return {}


def _requirement_order(match: dict, requirements: list[dict]) -> int:
    requirement_id = match.get("requirement_id")
    skill_key = _skill_key(match)
    for index, requirement in enumerate(requirements or []):
        if requirement_id and requirement.get("requirement_id") == requirement_id:
            return index
        if _skill_key(requirement) == skill_key:
            return index
    return 999


def _gap_dedupe_key(match: dict) -> tuple:
    return _gap_rank_key(match)


def _gap_rank_key(match: dict) -> tuple:
    return (
        0 if bool(match.get("is_core", False)) else 1,
        0 if _skill_type(match, {}) == "UNIQUE" else 1,
        -SEVERITY_PRIORITY.get(str(match.get("severity") or "LOW"), 0),
        -float(match.get("gap_score", compute_gap_score(match))),
        _match_level_rank(_match_level(match)),
        int(match.get("requirement_order", 999)),
        _skill_key(match),
    )


def _rank_for_confidence(candidates: list[dict], confidence_level: str) -> list[dict]:
    if str(confidence_level).upper() != "LOW":
        return rank_gaps(candidates)
    return sorted(
        candidates or [],
        key=lambda item: (
            int(item.get("requirement_order", 999)),
            _gap_rank_key(item),
        ),
    )


def _match_level_rank(level: str) -> int:
    return {"NONE": 0, "WEAK": 1, "PARTIAL": 2}.get(level, 9)


def _gap_evidence_note(match: dict) -> str:
    matched_id = match.get("matched_evidence_id")
    match_score = float(match.get("match_score", 0.0))
    if matched_id:
        return f"대표 근거 {matched_id}, match_score {match_score:.2f} 기준입니다."
    return f"대표 근거가 없어 match_score {match_score:.2f} 기준으로 결핍 판단했습니다."


def _taxonomy_lookup(taxonomy: dict) -> dict:
    if not isinstance(taxonomy, dict):
        return {}
    if "skills" in taxonomy:
        return {item.get("skill_key"): item for item in taxonomy.get("skills", []) if item.get("skill_key")}
    return taxonomy


def _label_ko(match: dict, requirement: dict, taxonomy: dict) -> str:
    skill_key = _skill_key(match) or _skill_key(requirement)
    if match.get("label_ko"):
        return str(match["label_ko"])
    if requirement.get("label_ko"):
        return str(requirement["label_ko"])
    lookup = _taxonomy_lookup(taxonomy)
    meta = lookup.get(skill_key, {}) if isinstance(lookup, dict) else {}
    return str(meta.get("label_ko") or skill_key)


def _skill_key(item: dict) -> str:
    return str(item.get("skill_key") or item.get("requirement_key") or "")


def _skill_type(match: dict, requirement: dict) -> str:
    value = (
        match.get("skill_type")
        or match.get("requirement_type")
        or match.get("skill_group")
        or requirement.get("skill_type")
        or requirement.get("requirement_type")
        or requirement.get("skill_group")
        or "COMMON"
    )
    return str(value).upper()


def _match_level(item: dict) -> str:
    return str(item.get("match_level") or "NONE").upper()
