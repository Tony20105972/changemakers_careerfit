#!/usr/bin/env python3
"""Deterministic strength selector for CareerFit Contract v1.5."""

from __future__ import annotations


MATCH_LEVEL_FACTOR = {
    "FULL": 1.0,
    "STRONG": 0.75,
    "PARTIAL": 0.5,
    "WEAK": 0.25,
    "NONE": 0.0,
}
SKILL_TYPE_WEIGHT = {
    "UNIQUE": 0.65,
    "COMMON": 0.35,
}
STRENGTH_LEVELS = {"FULL", "STRONG"}
HEADLINE_LEVEL_KO = {
    "FULL": "명확히",
    "STRONG": "충분히",
    "PARTIAL": "부분적으로",
    "WEAK": "약하게",
    "NONE": "확인되지 않음",
}
HIGH_MEDIUM_LIMIT = 5
LOW_LIMIT = 3
LOW_STRENGTH_PRIORITY = {
    "documentation": 0,
    "communication": 1,
    "coordination": 2,
    "vendor_coordination": 3,
    "operations_management": 4,
    "process_improvement": 5,
    "process_design": 8,
    "quality_control": 9,
}
LOW_STRENGTH_PRIORITY_LIMIT = 5


def filter_strength_candidates(matches: list[dict]) -> list[dict]:
    """FULL, STRONG match만 strength 후보로 통과시킨다."""
    candidates = []
    for match in matches or []:
        if _match_level(match) in STRENGTH_LEVELS:
            candidates.append(dict(match))
    return candidates


def compute_strength_score(match: dict) -> float:
    """match_level factor와 skill_type weight를 곱해 strength_score를 계산한다."""
    level = _match_level(match)
    skill_type = _skill_type(match)
    score = SKILL_TYPE_WEIGHT.get(skill_type, SKILL_TYPE_WEIGHT["COMMON"])
    score *= MATCH_LEVEL_FACTOR.get(level, 0.0)
    return round(score, 4)


def deduplicate_by_skill_key(candidates: list[dict]) -> list[dict]:
    """같은 skill_key 후보 중 strength_score가 가장 높은 항목만 유지한다."""
    best_by_skill = {}
    for candidate in candidates or []:
        normalized = dict(candidate)
        normalized["strength_score"] = compute_strength_score(normalized)
        skill_key = _skill_key(normalized)
        if not skill_key:
            continue
        current = best_by_skill.get(skill_key)
        if current is None or _strength_dedupe_key(normalized) < _strength_dedupe_key(current):
            best_by_skill[skill_key] = normalized
    return [best_by_skill[key] for key in sorted(best_by_skill)]


def rank_strengths(candidates: list[dict]) -> list[dict]:
    """match/evidence 품질 우선, UNIQUE 보조 우선순위, skill_key 순으로 정렬한다."""
    ranked = sorted(
        candidates or [],
        key=_strength_rank_key,
    )
    return [dict(item) for item in ranked]


def build_strength_headline(match: dict, taxonomy: dict) -> str:
    """label_ko와 match_level을 사용해 template headline을 생성한다."""
    label = _label_ko(match, taxonomy)
    level_ko = HEADLINE_LEVEL_KO.get(_match_level(match), "부분적으로")
    context = "핵심 직무 역량" if _skill_type(match) == "UNIQUE" else "협업 기반 역량"
    evidence_note = _headline_evidence_note(match)
    return f"{label} 역량은 {context}으로 {level_ko} 확인됨{evidence_note}"


def select_strengths(
    matches: list[dict],
    evidence: list[dict],
    taxonomy: dict,
    confidence_level: str,
) -> list[dict]:
    """strength 후보 필터링, 점수화, 정렬, fallback을 수행해 strengths[]를 반환한다."""
    candidates = filter_strength_candidates(matches)
    candidates = [_with_strength_evidence(candidate, evidence) for candidate in candidates]
    candidates = deduplicate_by_skill_key(candidates)
    candidates = _rank_for_confidence(candidates, confidence_level)
    if not candidates:
        candidates = _fallback_strength_candidates(matches, evidence, confidence_level)

    limit = LOW_LIMIT if str(confidence_level).upper() == "LOW" else HIGH_MEDIUM_LIMIT
    selected = candidates[:limit]
    if str(confidence_level).upper() == "LOW" and not selected:
        selected = _fallback_strength_candidates(matches, evidence, confidence_level)[:1]
    return [_build_strength(item, evidence, taxonomy, rank) for rank, item in enumerate(selected, start=1)]


def _with_strength_score(match: dict) -> dict:
    normalized = dict(match)
    normalized["strength_score"] = compute_strength_score(normalized)
    return normalized


def _with_strength_evidence(match: dict, evidence: list[dict]) -> dict:
    normalized = _with_strength_score(match)
    stats = _evidence_stats(_skill_key(match), evidence)
    normalized.update(stats)
    return normalized


def _fallback_strength_candidates(matches: list[dict], evidence: list[dict], confidence_level: str) -> list[dict]:
    fallback = []
    for match in matches or []:
        allowed_levels = {"STRONG"}
        if str(confidence_level).upper() == "LOW":
            allowed_levels = {"STRONG", "PARTIAL", "WEAK"}
        if _match_level(match) not in allowed_levels:
            continue
        normalized = _with_strength_evidence(match, evidence)
        normalized["headline_suffix"] = "(추정)"
        if str(confidence_level).upper() == "LOW" and _low_strength_priority(normalized) > LOW_STRENGTH_PRIORITY_LIMIT:
            continue
        fallback.append(normalized)
    return sorted(
        fallback,
        key=lambda item: (_low_strength_priority(item), _strength_rank_key(item)),
    )[:1]


def _build_strength(match: dict, evidence: list[dict], taxonomy: dict, rank: int) -> dict:
    headline = build_strength_headline(match, taxonomy)
    suffix = str(match.get("headline_suffix") or "").strip()
    if suffix:
        headline = f"{headline} {suffix}"
    return {
        "rank": rank,
        "skill_key": _skill_key(match),
        "label_ko": _label_ko(match, taxonomy),
        "match_level": _match_level(match),
        "strength_score": round(float(match.get("strength_score", compute_strength_score(match))), 4),
        "headline": headline,
        "evidence_ids": _evidence_ids_for_match(match, evidence),
    }


def _evidence_ids_for_match(match: dict, evidence: list[dict]) -> list[str]:
    skill_key = _skill_key(match)
    valid_ids = {}
    for item in evidence or []:
        evidence_id = item.get("evidence_id")
        if evidence_id:
            valid_ids[str(evidence_id)] = item
    ids = []
    matched_id = match.get("matched_evidence_id")
    if matched_id and str(matched_id) in valid_ids and valid_ids[str(matched_id)].get("skill_key") == skill_key:
        ids.append(str(matched_id))
    for evidence_id, item in valid_ids.items():
        if item.get("skill_key") == skill_key:
            ids.append(evidence_id)
    return sorted({evidence_id for evidence_id in ids if evidence_id in valid_ids})


def _evidence_stats(skill_key: str, evidence: list[dict]) -> dict:
    items = [item for item in evidence or [] if item.get("skill_key") == skill_key]
    type_counts = {"EXPLICIT": 0, "ACHIEVED": 0, "INFERRED": 0}
    confidence_total = 0.0
    for item in items:
        evidence_type = str(item.get("evidence_type") or "").upper()
        if evidence_type in type_counts:
            type_counts[evidence_type] += 1
        confidence_total += float(item.get("confidence_score", 0.0))
    return {
        "evidence_count": len(items),
        "confidence_total": round(confidence_total, 4),
        "explicit_count": type_counts["EXPLICIT"],
        "achieved_count": type_counts["ACHIEVED"],
        "inferred_count": type_counts["INFERRED"],
    }


def _strength_rank_key(match: dict) -> tuple:
    return (
        -_match_level_value(_match_level(match)),
        -int(match.get("explicit_count", 0)),
        -int(match.get("achieved_count", 0)),
        -float(match.get("confidence_total", 0.0)),
        -int(match.get("evidence_count", 0)),
        0 if _skill_type(match) == "UNIQUE" else 1,
        -float(match.get("strength_score", compute_strength_score(match))),
        _skill_key(match),
    )


def _rank_for_confidence(candidates: list[dict], confidence_level: str) -> list[dict]:
    if str(confidence_level).upper() != "LOW":
        return rank_strengths(candidates)
    candidates = [
        item
        for item in candidates or []
        if _low_strength_priority(item) <= LOW_STRENGTH_PRIORITY_LIMIT
    ]
    return sorted(candidates or [], key=lambda item: (_low_strength_priority(item), _strength_rank_key(item)))


def _low_strength_priority(match: dict) -> int:
    return LOW_STRENGTH_PRIORITY.get(_skill_key(match), 8)


def _strength_dedupe_key(match: dict) -> tuple:
    return (
        _strength_rank_key(match),
        _skill_key(match),
    )


def _match_level_value(level: str) -> int:
    return {"FULL": 4, "STRONG": 3, "PARTIAL": 2, "WEAK": 1, "NONE": 0}.get(level, 0)


def _headline_evidence_note(match: dict) -> str:
    explicit = int(match.get("explicit_count", 0))
    achieved = int(match.get("achieved_count", 0))
    evidence_count = int(match.get("evidence_count", 0))
    if explicit:
        return f" (명시 근거 {explicit}건)"
    if achieved:
        return f" (성과 근거 {achieved}건)"
    if evidence_count:
        return f" (간접 근거 {evidence_count}건)"
    return ""


def _taxonomy_lookup(taxonomy: dict) -> dict:
    if not isinstance(taxonomy, dict):
        return {}
    if "skills" in taxonomy:
        return {item.get("skill_key"): item for item in taxonomy.get("skills", []) if item.get("skill_key")}
    return taxonomy


def _label_ko(match: dict, taxonomy: dict) -> str:
    skill_key = _skill_key(match)
    if match.get("label_ko"):
        return str(match["label_ko"])
    lookup = _taxonomy_lookup(taxonomy)
    meta = lookup.get(skill_key, {}) if isinstance(lookup, dict) else {}
    return str(meta.get("label_ko") or skill_key)


def _skill_key(item: dict) -> str:
    return str(item.get("skill_key") or item.get("requirement_key") or "")


def _skill_type(item: dict) -> str:
    return str(item.get("skill_type") or item.get("requirement_type") or item.get("skill_group") or "COMMON").upper()


def _match_level(item: dict) -> str:
    return str(item.get("match_level") or "NONE").upper()
