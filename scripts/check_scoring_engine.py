#!/usr/bin/env python3
"""Scoring Engine End-to-End Validation"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.engine import evidence_extractor
from backend.engine import profile_selector
from backend.engine import scoring_engine


SCORE_TOLERANCE = 10
UNIQUE_CAP = 0.65
COMMON_CAP = 0.35
EXPECTED_FIXTURE_COUNT = 10
INPUT_PATTERN = "output/sample_input_*.json"
HIGH_FILENAME_HINTS = ["dominant"]
LOW_FILENAME_HINTS = ["low_confidence", "blocked"]


def run_pipeline(fixture: dict) -> dict:
    """profile_selector -> evidence_extractor -> matcher -> scoring_engine 순차 실행."""
    selected = profile_selector.select_profile(fixture)
    taxonomy = evidence_extractor.load_taxonomy()
    evidence = evidence_extractor.extract_evidence(fixture, taxonomy)
    result = scoring_engine.score_fixture(selected["primary_profile"], evidence)
    result["primary_profile"] = selected["primary_profile"]
    result["evidence_count"] = len(evidence)
    return result


def load_gold_score(filename: str) -> int:
    """대응하는 sample_report_*.json에서 total_score 추출."""
    report_path = Path("output") / filename.replace("sample_input_", "sample_report_")
    with report_path.open(encoding="utf-8") as file:
        report = json.load(file)
    score = report.get("summary", {}).get("total_score")
    if score is None:
        score = report.get("scores", {}).get("total")
    if score is None:
        raise ValueError(f"gold total_score not found: {report_path}")
    return int(round(float(score)))


def check_score_range(result: dict) -> list[str]:
    """0 <= total_score <= 100, unique_total <= 0.65, common_total <= 0.35."""
    errors = []
    scores = result.get("scores", {})
    total_score = scores.get("total_score")
    unique_total = scores.get("unique_total")
    common_total = scores.get("common_total")
    if not result.get("requirement_matches"):
        errors.append("requirement_matches is empty")
    if total_score is None or not 0 <= total_score <= 100:
        errors.append(f"score={total_score} outside 0..100")
    if unique_total is None or unique_total > UNIQUE_CAP:
        errors.append(f"unique_total={unique_total} exceeds {UNIQUE_CAP}")
    if common_total is None or common_total > COMMON_CAP:
        errors.append(f"common_total={common_total} exceeds {COMMON_CAP}")
    return errors


def check_against_gold(filename: str, result: dict) -> list[str]:
    """|result.total_score - gold_score| <= SCORE_TOLERANCE 검증."""
    score = int(result["scores"]["total_score"])
    gold = load_gold_score(filename)
    diff = abs(score - gold)
    if diff > SCORE_TOLERANCE:
        return [f"score={score} gold={gold} diff={diff} (tolerance {SCORE_TOLERANCE})"]
    return []


def check_relative_ordering(results: dict[str, dict]) -> list[str]:
    """HIGH(*_dominant) 평균 score > LOW(low_confidence, blocked) 평균 score 검증."""
    high_scores = []
    low_scores = []
    for filename, result in sorted(results.items()):
        display_name = _display_name(filename)
        score = int(result["scores"]["total_score"])
        if any(hint in display_name for hint in HIGH_FILENAME_HINTS):
            high_scores.append(score)
        if any(hint in display_name for hint in LOW_FILENAME_HINTS):
            low_scores.append(score)
    high_avg = _average(high_scores)
    low_avg = _average(low_scores)
    if not high_scores or not low_scores:
        return ["Ordering check: FAIL (missing HIGH or LOW fixtures)"]
    if high_avg <= low_avg:
        return [f"Ordering check: FAIL (HIGH avg={high_avg:.1f} <= LOW avg={low_avg:.1f})"]
    return []


def run_determinism_check(fixture_path: str) -> bool:
    """동일 fixture 파이프라인 3회 실행, total_score 완전 일치 확인."""
    fixture = _load_fixture(Path(fixture_path))
    scores = []
    for _index in range(3):
        result = run_pipeline(fixture)
        scores.append(result["scores"]["total_score"])
    return scores[0] == scores[1] == scores[2]


def main() -> int:
    """전체 fixture 순회 + 종합 리포트 출력."""
    fixture_paths = sorted(glob.glob(INPUT_PATTERN))
    passed = 0
    determinism_passed = 0
    results = {}
    any_failure = False

    if len(fixture_paths) != EXPECTED_FIXTURE_COUNT:
        print(f"[FAIL] fixture_count        found={len(fixture_paths)} (expected {EXPECTED_FIXTURE_COUNT})")
        any_failure = True

    for fixture_path in fixture_paths:
        path = Path(fixture_path)
        display_name = _display_name(path.name)
        try:
            fixture = _load_fixture(path)
            result = run_pipeline(fixture)
            results[path.name] = result
            gold = load_gold_score(path.name)
            score = int(result["scores"]["total_score"])
            diff = abs(score - gold)
            errors = []
            errors.extend(check_score_range(result))
            errors.extend(check_against_gold(path.name, result))
            if run_determinism_check(fixture_path):
                determinism_passed += 1
            else:
                errors.append("determinism check failed")
        except Exception as exc:
            score = "ERR"
            gold = "ERR"
            diff = "ERR"
            errors = [f"{type(exc).__name__}: {exc}"]

        if errors:
            any_failure = True
            for error in errors:
                if str(error).startswith("score="):
                    print(f"[FAIL] {display_name:<20} {error}")
                else:
                    print(f"[FAIL] {display_name:<20} score={score} gold={gold} diff={diff} {error}")
        else:
            passed += 1
            print(f"[PASS] {display_name:<20} score={score} gold={gold} diff={diff}")

    ordering_errors = check_relative_ordering(results)
    if ordering_errors:
        any_failure = True
        for error in ordering_errors:
            print(error)

    print(f"Scoring engine check passed: {passed}/{EXPECTED_FIXTURE_COUNT}")
    if not ordering_errors and results:
        high_avg, low_avg = _ordering_averages(results)
        print(f"Ordering check: PASS (HIGH avg={high_avg:.1f} > LOW avg={low_avg:.1f})")
    if determinism_passed == len(fixture_paths):
        print("Determinism: PASS (3/3 runs identical)")
    else:
        print(f"Determinism: FAIL ({determinism_passed}/{len(fixture_paths)} fixtures identical)")
    if any_failure:
        print("Fix the above before Day 11.")
        return 1
    return 0


def _load_fixture(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def _display_name(filename: str) -> str:
    return filename.removeprefix("sample_input_").removesuffix(".json")


def _average(values: list[int]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _ordering_averages(results: dict[str, dict]) -> tuple[float, float]:
    high_scores = []
    low_scores = []
    for filename, result in sorted(results.items()):
        display_name = _display_name(filename)
        score = int(result["scores"]["total_score"])
        if any(hint in display_name for hint in HIGH_FILENAME_HINTS):
            high_scores.append(score)
        if any(hint in display_name for hint in LOW_FILENAME_HINTS):
            low_scores.append(score)
    return _average(high_scores), _average(low_scores)


if __name__ == "__main__":
    raise SystemExit(main())
