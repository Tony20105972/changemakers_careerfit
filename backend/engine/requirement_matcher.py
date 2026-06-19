#!/usr/bin/env python3
"""Deterministic requirement matcher for CareerFit."""

from __future__ import annotations

import glob
import json
from pathlib import Path


REQUIREMENTS_DIR = Path("data/generated")
FULL_THRESHOLD = 0.8
CONSERVATIVE_FULL_THRESHOLD = 0.85
STRONG_THRESHOLD = 0.6
PARTIAL_THRESHOLD = 0.5
CONSERVATIVE_FULL_PROFILES = ["hr", "marketing"]
MATCH_SCORE = {
    "FULL": 1.0,
    "STRONG": 0.75,
    "PARTIAL": 0.5,
    "WEAK": 0.25,
    "NONE": 0.0,
}


def load_requirements_for_profile(profile_id: str) -> list[dict]:
    """job_requirements_{profile_id}.json 로드."""
    path = REQUIREMENTS_DIR / f"job_requirements_{profile_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"requirements file not found for primary_profile='{profile_id}': {path}")
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    requirements = []
    for index, requirement in enumerate(data.get("requirements", []), start=1):
        normalized = dict(requirement)
        normalized["requirement_id"] = normalized.get("requirement_id") or f"req_{profile_id}_{index:03d}"
        normalized["skill_type"] = normalized.get("skill_type") or normalized.get("requirement_type", "COMMON")
        normalized["requirement_type"] = normalized["skill_type"]
        normalized["weight"] = round(float(normalized.get("weight", 0.0)), 4)
        requirements.append(normalized)
    return sorted(requirements, key=lambda item: item["requirement_id"])


def classify_match_level(requirement: dict, evidence_list: list[dict]) -> tuple[str, float, dict | None]:
    """requirement 1개에 대해 가장 높은 match_level을 반환."""
    exact_candidates = _matching_exact_evidence(requirement, evidence_list)
    if exact_candidates:
        selected, match_level = _best_exact_evidence(requirement, exact_candidates)
        return match_level, MATCH_SCORE[match_level], selected
    weak_candidates = _matching_weak_evidence(requirement, evidence_list)
    if weak_candidates:
        selected = _best_evidence(weak_candidates)
        return "WEAK", MATCH_SCORE["WEAK"], selected
    return "NONE", MATCH_SCORE["NONE"], None


def match_requirements(primary_profile: str, evidence: list[dict]) -> list[dict]:
    """전체 requirement_matches[] 생성. requirement_id 순서로 정렬."""
    requirements = load_requirements_for_profile(primary_profile)
    matches = []
    for requirement in requirements:
        match_level, match_score, matched_evidence = classify_match_level(requirement, evidence)
        matches.append(
            {
                "requirement_id": requirement["requirement_id"],
                "skill_key": requirement["skill_key"],
                "skill_type": requirement["skill_type"],
                "match_level": match_level,
                "match_score": round(match_score, 2),
                "matched_evidence_id": matched_evidence.get("evidence_id") if matched_evidence else None,
            }
        )
    return sorted(matches, key=lambda item: item["requirement_id"])


def _matching_exact_evidence(requirement: dict, evidence_list: list[dict]) -> list[dict]:
    skill_key = requirement.get("skill_key")
    candidates = []
    for evidence in evidence_list:
        if evidence.get("skill_key") == skill_key and float(evidence.get("confidence_score", 0.0)) >= PARTIAL_THRESHOLD:
            candidates.append(evidence)
    return candidates


def _matching_weak_evidence(requirement: dict, evidence_list: list[dict]) -> list[dict]:
    candidates = []
    for evidence in evidence_list:
        if evidence.get("skill_key") == requirement.get("skill_key"):
            continue
        if float(evidence.get("confidence_score", 0.0)) < PARTIAL_THRESHOLD:
            continue
        if _share_requirement_profile(requirement.get("skill_key", ""), evidence.get("skill_key", "")):
            candidates.append(evidence)
    return candidates


def _best_evidence(candidates: list[dict]) -> dict:
    return sorted(
        candidates,
        key=lambda item: (-float(item.get("confidence_score", 0.0)), str(item.get("evidence_id", ""))),
    )[0]


def _best_exact_evidence(requirement: dict, candidates: list[dict]) -> tuple[dict, str]:
    ranked = []
    for evidence in candidates:
        match_level = _exact_match_level(requirement, evidence)
        ranked.append((evidence, match_level))
    return sorted(
        ranked,
        key=lambda item: (
            -MATCH_SCORE[item[1]],
            -float(item[0].get("confidence_score", 0.0)),
            str(item[0].get("evidence_id", "")),
        ),
    )[0]


def _exact_match_level(requirement: dict, evidence: dict) -> str:
    confidence = round(float(evidence.get("confidence_score", 0.0)), 2)
    if evidence.get("source") == "target_priority_text":
        if confidence >= STRONG_THRESHOLD:
            return "PARTIAL"
        return "WEAK"
    if confidence >= _full_threshold_for_requirement(requirement):
        return "FULL"
    if confidence >= STRONG_THRESHOLD:
        return "STRONG"
    return "PARTIAL"


def _full_threshold_for_requirement(requirement: dict) -> float:
    source_profiles = requirement.get("source_profiles") or []
    profile_id = source_profiles[0] if source_profiles else ""
    if profile_id in CONSERVATIVE_FULL_PROFILES:
        return CONSERVATIVE_FULL_THRESHOLD
    return FULL_THRESHOLD


def _share_requirement_profile(requirement_skill: str, evidence_skill: str) -> bool:
    if not requirement_skill or not evidence_skill:
        return False
    for path in sorted(glob.glob(str(REQUIREMENTS_DIR / "job_requirements_*.json"))):
        with Path(path).open(encoding="utf-8") as file:
            data = json.load(file)
        profile_skills = []
        for requirement in data.get("requirements", []):
            profile_skills.append(requirement.get("skill_key"))
        if requirement_skill in profile_skills and evidence_skill in profile_skills:
            return True
    return False
