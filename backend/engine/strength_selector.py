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
STRENGTH_LEVELS = {"FULL", "STRONG", "PARTIAL"}
HEADLINE_LEVEL_KO = {
    "FULL": "명확히",
    "STRONG": "충분히",
    "PARTIAL": "부분적으로",
    "WEAK": "약하게",
    "NONE": "확인되지 않음",
}
HIGH_MEDIUM_LIMIT = 5
LOW_LIMIT = 3
PARTIAL_STRENGTH_THRESHOLD = 0.4


def filter_strength_candidates(matches: list[dict]) -> list[dict]:
    """FULL, STRONG, PARTIAL match만 strength 후보로 통과시킨다."""
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
    """UNIQUE 우선, strength_score 내림차순, skill_key 오름차순으로 정렬한다."""
    ranked = sorted(
        candidates or [],
        key=lambda item: (
            0 if _skill_type(item) == "UNIQUE" else 1,
            -float(item.get("strength_score", compute_strength_score(item))),
            _skill_key(item),
        ),
    )
    return [dict(item) for item in ranked]


def build_strength_headline(match: dict, taxonomy: dict) -> str:
    """label_ko와 match_level을 사용해 template headline을 생성한다."""
    label = _label_ko(match, taxonomy)
    level_ko = HEADLINE_LEVEL_KO.get(_match_level(match), "부분적으로")
    return f"{label} 역량이 {level_ko} 확인됨"


def select_strengths(
    matches: list[dict],
    evidence: list[dict],
    taxonomy: dict,
    confidence_level: str,
) -> list[dict]:
    """strength 후보 필터링, 점수화, 정렬, fallback을 수행해 strengths[]를 반환한다."""
    candidates = filter_strength_candidates(matches)
    candidates = [_with_strength_score(candidate) for candidate in candidates]
    candidates = _resolve_partial_overlap(candidates, confidence_level)
    candidates = deduplicate_by_skill_key(candidates)
    candidates = rank_strengths(candidates)
    if not candidates:
        candidates = _fallback_strength_candidates(matches)

    limit = LOW_LIMIT if str(confidence_level).upper() == "LOW" else HIGH_MEDIUM_LIMIT
    selected = candidates[:limit]
    if str(confidence_level).upper() == "LOW" and not selected:
        selected = _fallback_strength_candidates(matches)[:1]
    return [_build_strength(item, evidence, taxonomy, rank) for rank, item in enumerate(selected, start=1)]


def _with_strength_score(match: dict) -> dict:
    normalized = dict(match)
    normalized["strength_score"] = compute_strength_score(normalized)
    return normalized


def _resolve_partial_overlap(candidates: list[dict], confidence_level: str) -> list[dict]:
    resolved = []
    for candidate in candidates:
        if _match_level(candidate) != "PARTIAL":
            resolved.append(candidate)
            continue
        if float(candidate.get("strength_score", 0.0)) >= PARTIAL_STRENGTH_THRESHOLD:
            resolved.append(candidate)
    if resolved or str(confidence_level).upper() != "LOW":
        return resolved
    return list(candidates)


def _fallback_strength_candidates(matches: list[dict]) -> list[dict]:
    partials = []
    weaks = []
    for match in matches or []:
        normalized = _with_strength_score(match)
        level = _match_level(normalized)
        if level == "PARTIAL":
            partials.append(normalized)
        elif level == "WEAK":
            normalized["headline_suffix"] = "(추정)"
            weaks.append(normalized)
    fallback_pool = partials if partials else weaks
    return sorted(
        fallback_pool,
        key=lambda item: (-float(item.get("match_score", 0.0)), _skill_key(item)),
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
    if matched_id and str(matched_id) in valid_ids:
        ids.append(str(matched_id))
    for evidence_id, item in valid_ids.items():
        if item.get("skill_key") == skill_key:
            ids.append(evidence_id)
    return sorted({evidence_id for evidence_id in ids if evidence_id in valid_ids})


def _strength_dedupe_key(match: dict) -> tuple:
    return (
        -float(match.get("strength_score", compute_strength_score(match))),
        _match_level_rank(_match_level(match)),
        _skill_key(match),
    )


def _match_level_rank(level: str) -> int:
    return {"FULL": 0, "STRONG": 1, "PARTIAL": 2, "WEAK": 3, "NONE": 4}.get(level, 5)


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
