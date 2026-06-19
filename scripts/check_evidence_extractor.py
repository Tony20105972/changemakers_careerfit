#!/usr/bin/env python3
"""Evidence Extractor Fixture Validation"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.engine import evidence_extractor


MIN_EVIDENCE_HIGH = 8
MIN_EVIDENCE_MEDIUM = 5
MIN_EVIDENCE_LOW = 1
ALLOWED_SOURCES = {"career_histories", "target_priority_text"}
ALLOWED_TYPES = {"EXPLICIT", "INFERRED", "ACHIEVED"}
HIGH_FILENAME_HINTS = ["dominant"]
MEDIUM_FILENAME_HINTS = ["mixed"]
LOW_FILENAME_HINTS = ["low_confidence", "blocked"]

INPUT_PATTERN = "output/sample_input_*.json"
TAXONOMY_PATH = "data/skill_taxonomy.json"
EXPECTED_FIXTURE_COUNT = 10


def load_taxonomy_keys() -> set[str]:
    """skill_taxonomy.json에서 유효 skill_key 집합 추출."""
    with Path(TAXONOMY_PATH).open(encoding="utf-8") as file:
        data = json.load(file)
    return {skill["skill_key"] for skill in data.get("skills", []) if skill.get("skill_key")}


def run_extraction(fixture: dict) -> list[dict]:
    """evidence_extractor.extract_evidence() 호출 wrapper."""
    taxonomy = evidence_extractor.load_taxonomy()
    return evidence_extractor.extract_evidence(fixture, taxonomy)


def check_count(filename: str, evidence: list[dict]) -> list[str]:
    """파일명 힌트 기반 evidence_count 최소치 검증."""
    minimum = _minimum_for_filename(filename)
    if len(evidence) < minimum:
        return [f"evidence={len(evidence)} (min {minimum})"]
    return []


def check_skill_key_validity(evidence: list[dict], valid_keys: set[str]) -> list[str]:
    """모든 skill_key가 taxonomy에 존재하는지 검증."""
    errors = []
    for item in evidence:
        skill_key = item.get("skill_key")
        if skill_key not in valid_keys:
            evidence_id = item.get("evidence_id", "<missing_id>")
            errors.append(f"{evidence_id} skill_key '{skill_key}' not in taxonomy")
    return errors


def check_fields(evidence: list[dict]) -> list[str]:
    """original_text 존재, source 허용값, evidence_type 허용값 검증."""
    errors = []
    for item in evidence:
        evidence_id = item.get("evidence_id", "<missing_id>")
        if not str(item.get("original_text") or "").strip():
            errors.append(f"{evidence_id} original_text is empty")
        if item.get("source") not in ALLOWED_SOURCES:
            errors.append(f"{evidence_id} source '{item.get('source')}' is not allowed")
        if item.get("evidence_type") not in ALLOWED_TYPES:
            errors.append(f"{evidence_id} evidence_type '{item.get('evidence_type')}' is not allowed")
    return errors


def check_target_priority_not_achieved(evidence: list[dict]) -> list[str]:
    """source == target_priority_text인 evidence의 evidence_type != ACHIEVED 검증."""
    errors = []
    for item in evidence:
        if item.get("source") == "target_priority_text" and item.get("evidence_type") == "ACHIEVED":
            evidence_id = item.get("evidence_id", "<missing_id>")
            errors.append(f"{evidence_id} target_priority_text evidence cannot be ACHIEVED")
    return errors


def run_determinism_check(fixture_path: str) -> bool:
    """동일 fixture로 3회 추출 후 evidence_id 순서까지 동일한지 비교."""
    fixture = _load_fixture(Path(fixture_path))
    runs = []
    for _index in range(3):
        evidence = run_extraction(fixture)
        runs.append([(item["evidence_id"], item["skill_key"], item["confidence_score"]) for item in evidence])
    return runs[0] == runs[1] == runs[2]


def main() -> int:
    """전체 fixture 순회, 결과 집계, 출력, 종료코드 반환."""
    valid_keys = load_taxonomy_keys()
    fixture_paths = sorted(glob.glob(INPUT_PATTERN))
    passed = 0
    determinism_passed = 0
    any_failure = False

    if len(fixture_paths) != EXPECTED_FIXTURE_COUNT:
        print(f"[FAIL] fixture_count        found={len(fixture_paths)} (expected {EXPECTED_FIXTURE_COUNT})")
        any_failure = True

    for fixture_path in fixture_paths:
        path = Path(fixture_path)
        filename = _display_name(path.name)
        minimum = _minimum_for_filename(path.name)
        try:
            fixture = _load_fixture(path)
            evidence = run_extraction(fixture)
            json.dumps(evidence, ensure_ascii=False)
            errors = []
            errors.extend(check_count(path.name, evidence))
            errors.extend(check_skill_key_validity(evidence, valid_keys))
            errors.extend(check_fields(evidence))
            errors.extend(check_target_priority_not_achieved(evidence))
            deterministic = run_determinism_check(fixture_path)
            if deterministic:
                determinism_passed += 1
            else:
                errors.append("determinism check failed")
        except Exception as exc:
            errors = [f"{type(exc).__name__}: {exc}"]

        if errors:
            any_failure = True
            for error in errors:
                print(f"[FAIL] {filename:<20} {error}")
        else:
            passed += 1
            print(f"[PASS] {filename:<20} evidence={len(evidence)} (min {minimum})")

    print(f"Evidence extractor check passed: {passed}/{EXPECTED_FIXTURE_COUNT}")
    if determinism_passed == len(fixture_paths):
        print("Determinism: PASS (3/3 runs identical)")
    else:
        print(f"Determinism: FAIL ({determinism_passed}/{len(fixture_paths)} fixtures identical)")
    if any_failure:
        print("Fix the above before Day 10.")
        return 1
    return 0


def _load_fixture(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def _display_name(filename: str) -> str:
    return filename.removeprefix("sample_input_").removesuffix(".json")


def _minimum_for_filename(filename: str) -> int:
    display_name = _display_name(filename)
    if any(hint in display_name for hint in HIGH_FILENAME_HINTS):
        return MIN_EVIDENCE_HIGH
    if any(hint in display_name for hint in MEDIUM_FILENAME_HINTS):
        return MIN_EVIDENCE_MEDIUM
    if any(hint in display_name for hint in LOW_FILENAME_HINTS):
        return MIN_EVIDENCE_LOW
    return MIN_EVIDENCE_LOW


if __name__ == "__main__":
    raise SystemExit(main())
