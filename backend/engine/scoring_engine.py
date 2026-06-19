#!/usr/bin/env python3
"""Deterministic scoring engine for CareerFit requirement matches."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend.engine import requirement_matcher


UNIQUE_CAP = 0.65
COMMON_CAP = 0.35
CORE_PENALTY_NONE = -5.0
CORE_PENALTY_WEAK = -2.5
MIN_TOTAL_SCORE = 0
MAX_TOTAL_SCORE = 100


def compute_unique_total(matches: list[dict], requirements: list[dict]) -> float:
    """UNIQUE skill_type만 필터링, weight * match_score 합산."""
    total = _weighted_total(matches, requirements, "UNIQUE")
    return round(min(UNIQUE_CAP, total), 2)


def compute_common_total(matches: list[dict], requirements: list[dict]) -> float:
    """COMMON skill_type만 필터링, weight * match_score 합산."""
    total = _weighted_total(matches, requirements, "COMMON")
    return round(min(COMMON_CAP, total), 2)


def compute_core_penalty(matches: list[dict], requirements: list[dict]) -> float:
    """is_core=true인 UNIQUE requirement의 NONE/WEAK 패널티를 계산."""
    if not requirements or not _requirements_have_is_core(requirements):
        print("[WARN] requirements missing is_core; core_penalty=0")
        return 0.0
    penalty = 0.0
    match_lookup = _match_lookup(matches)
    for requirement in requirements:
        if not requirement.get("is_core") or _skill_type(requirement) != "UNIQUE":
            continue
        match = match_lookup.get(requirement.get("requirement_id"))
        if not match:
            continue
        if match.get("match_level") == "NONE":
            penalty += CORE_PENALTY_NONE
        elif match.get("match_level") == "WEAK":
            penalty += CORE_PENALTY_WEAK
    return round(penalty, 2)


def compute_total_score(unique_total: float, common_total: float, core_penalty: float) -> int:
    """(unique_total + common_total) * 100 + core_penalty, 0~100 클램핑."""
    raw_score = round((unique_total + common_total) * 100 + core_penalty, 2)
    clamped = max(MIN_TOTAL_SCORE, min(MAX_TOTAL_SCORE, raw_score))
    return int(round(clamped))


def score_fixture(primary_profile: str, evidence: list[dict]) -> dict:
    """전체 파이프라인 실행. 출력 스키마 반환."""
    requirements = requirement_matcher.load_requirements_for_profile(primary_profile)
    matches = requirement_matcher.match_requirements(primary_profile, evidence)
    unique_total = compute_unique_total(matches, requirements)
    common_total = compute_common_total(matches, requirements)
    core_penalty = compute_core_penalty(matches, requirements)
    return {
        "requirement_matches": matches,
        "scores": {
            "total_score": compute_total_score(unique_total, common_total, core_penalty),
            "unique_total": unique_total,
            "common_total": common_total,
            "core_penalty": core_penalty,
        },
    }


def _weighted_total(matches: list[dict], requirements: list[dict], skill_type: str) -> float:
    total = 0.0
    match_lookup = _match_lookup(matches)
    for requirement in requirements:
        if _skill_type(requirement) != skill_type:
            continue
        match = match_lookup.get(requirement.get("requirement_id"))
        if match:
            total += float(requirement.get("weight", 0.0)) * float(match.get("match_score", 0.0))
    return round(total, 2)


def _skill_type(requirement: dict) -> str:
    return str(requirement.get("skill_type") or requirement.get("requirement_type") or "COMMON")


def _match_lookup(matches: list[dict]) -> dict:
    lookup = {}
    for match in matches:
        lookup[match.get("requirement_id")] = match
    return lookup


def _requirements_have_is_core(requirements: list[dict]) -> bool:
    for requirement in requirements:
        if "is_core" in requirement:
            return True
    return False
