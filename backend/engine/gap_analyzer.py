#!/usr/bin/env python3
"""Deterministic gap analyzer for CareerFit Contract v1.5."""

from __future__ import annotations


GAP_LEVELS = {"NONE", "WEAK", "PARTIAL"}
GAP_LEVEL_FACTOR = {
    "NONE": 1.0,
    "WEAK": 0.75,
    "PARTIAL": 0.5,
    "STRONG": 0.25,
    "FULL": 0.0,
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
PARTIAL_STRENGTH_THRESHOLD = 0.4
MIN_NON_LOW_GAPS = 2


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
    return f"{label} 관련 경험이 {level_ko}"


def build_recommendation_hint(match: dict, taxonomy: dict) -> str:
    """label_ko를 사용해 template recommendation hint를 생성한다."""
    label = _label_ko(match, {}, taxonomy)
    return f"{label} 관련 프로젝트 또는 자격 취득 검토 권장"


def rank_gaps(candidates: list[dict]) -> list[dict]:
    """severity 우선, gap_score 내림차순, skill_key 오름차순으로 정렬한다."""
    ranked = sorted(
        candidates or [],
        key=lambda item: (
            -SEVERITY_PRIORITY.get(str(item.get("severity") or "LOW"), 0),
            -float(item.get("gap_score", compute_gap_score(item))),
            _skill_key(item),
        ),
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
        normalized["severity"] = classify_severity(normalized, requirements)
        normalized["gap_score"] = compute_gap_score(normalized)
        if _is_strength_side_partial(normalized):
            continue
        candidates.append(normalized)

    candidates = _deduplicate_by_skill_key(candidates)
    candidates = _supplement_soft_gaps(candidates, matches, requirements, confidence_level)
    selected = rank_gaps(candidates)
    limit = LOW_LIMIT if str(confidence_level).upper() == "LOW" else HIGH_MEDIUM_LIMIT
    selected = selected[:limit]
    if str(confidence_level).upper() == "LOW" and not selected:
        selected = _fallback_gap_candidates(matches, requirements)[:1]
    return [_build_gap(item, taxonomy, rank) for rank, item in enumerate(selected, start=1)]


def _is_strength_side_partial(match: dict) -> bool:
    if _match_level(match) != "PARTIAL":
        return False
    strength_score = SKILL_TYPE_WEIGHT.get(_skill_type(match, {}), SKILL_TYPE_WEIGHT["COMMON"]) * 0.5
    return round(strength_score, 4) >= PARTIAL_STRENGTH_THRESHOLD


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
        normalized["severity"] = classify_severity(normalized, requirements)
        normalized["gap_score"] = compute_gap_score(normalized)
        fallback_pool.append(normalized)
    return rank_gaps(fallback_pool)


def _supplement_soft_gaps(
    candidates: list[dict],
    matches: list[dict],
    requirements: list[dict],
    confidence_level: str,
) -> list[dict]:
    if str(confidence_level).upper() == "LOW" or len(candidates) == 0 or len(candidates) >= MIN_NON_LOW_GAPS:
        return candidates
    used = {_skill_key(item) for item in candidates}
    supplements = []
    for match in matches or []:
        if _skill_key(match) in used or _match_level(match) != "STRONG":
            continue
        requirement = _find_requirement(match, requirements)
        normalized = _merge_match_requirement(match, requirement)
        normalized["severity"] = "LOW"
        normalized["gap_score"] = compute_gap_score(normalized)
        supplements.append(normalized)
    needed = MIN_NON_LOW_GAPS - len(candidates)
    return candidates + rank_gaps(supplements)[:needed]


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


def _gap_dedupe_key(match: dict) -> tuple:
    return (
        -SEVERITY_PRIORITY.get(str(match.get("severity") or "LOW"), 0),
        -float(match.get("gap_score", compute_gap_score(match))),
        _skill_key(match),
    )


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
