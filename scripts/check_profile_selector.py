#!/usr/bin/env python3
"""Validate profile_selector.py against Day 7 gold fixtures."""

import json
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT_DIR / "output"
EXPECTED_COUNT = 10

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.engine.profile_selector import select_profile  # noqa: E402


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def report_path_for(input_path: Path) -> Path:
    name = input_path.name.replace("sample_input_", "sample_report_", 1)
    return input_path.with_name(name)


def is_deterministic(fixture: dict) -> bool:
    first = select_profile(fixture)
    second = select_profile(fixture)
    third = select_profile(fixture)
    return first == second == third


def check_fixture(input_path: Path) -> tuple[bool, bool]:
    fixture = load_json(input_path)
    gold = load_json(report_path_for(input_path))
    expected = gold["meta"]
    actual = select_profile(fixture)

    expected_secondary = expected.get("secondary_profiles", [])
    actual_secondary = actual.get("secondary_profiles", [])
    deterministic = is_deterministic(fixture)

    errors = []
    if actual.get("primary_profile") is None:
        errors.append("primary_profile is null")
    if expected["primary_profile"] != actual.get("primary_profile"):
        errors.append("primary_profile mismatch")
    if expected["confidence_level"] != actual.get("confidence_level"):
        errors.append("confidence_level mismatch")
    if not all(profile in actual_secondary for profile in expected_secondary):
        errors.append("secondary_profiles missing expected entries")
    if expected["confidence_level"] == "LOW":
        if actual.get("confidence_level") != "LOW":
            errors.append("LOW fixture confidence mismatch")
        if not actual.get("warning_message"):
            errors.append("LOW fixture warning_message missing")
    if not deterministic:
        errors.append("determinism mismatch")

    passed = not errors
    print("PASS" if passed else "FAIL")
    print(input_path.name)
    print()
    print(f"expected_primary={expected['primary_profile']}")
    print(f"actual_primary={actual.get('primary_profile')}")
    if errors:
        print(f"errors={'; '.join(errors)}")
    print()
    return passed, deterministic


def main() -> int:
    input_paths = sorted(INPUT_DIR.glob("sample_input_*.json"))
    passed = 0
    deterministic_all = True

    if len(input_paths) != EXPECTED_COUNT:
        print(f"Profile selector check failed: 0/{EXPECTED_COUNT}")
        print(f"errors=fixture count {len(input_paths)} != {EXPECTED_COUNT}")
        return 1

    for input_path in input_paths:
        ok, deterministic = check_fixture(input_path)
        if ok:
            passed += 1
        deterministic_all = deterministic_all and deterministic

    if passed == EXPECTED_COUNT and deterministic_all:
        print(f"Profile selector check passed: {passed}/{EXPECTED_COUNT}")
        return 0
    print(f"Profile selector check failed: {passed}/{EXPECTED_COUNT}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
