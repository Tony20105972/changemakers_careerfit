#!/usr/bin/env python3
"""Validate the Day 12 narrative template pipeline."""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.engine.text_template import generate_narratives  # noqa: E402


TAXONOMY_PATH = REPO_ROOT / "data" / "skill_taxonomy.json"
REGISTRY_PATH = REPO_ROOT / "data" / "skill_descriptions.json"
FIXTURE_PATTERN = str(REPO_ROOT / "output" / "sample_report_*.json")
EXPECTED_FIXTURE_COUNT = 10

REQUIRED_REGISTRY_FIELDS = {
    "label_ko",
    "definition",
    "person_profile",
    "workplace_behavior",
    "business_value",
    "career_relevance",
    "market_context",
    "strength_narrative",
    "gap_narrative",
    "development_direction",
    "summary_phrase",
    "keywords",
}

REQUIRED_OUTPUT_FIELDS = {
    "executive_summary",
    "strength_narratives",
    "gap_narratives",
    "skill_explanations",
    "job_outlook",
    "final_assessment",
}

FORBIDDEN_OUTPUT_TERMS = {
    "expected" + "_score" + "_gain",
    "diffi" + "culty",
    "time" + "_estimate",
    "TO" + "DO",
    "T" + "BD",
    "{{",
    "}}",
    "{skill",
    "{score",
    "{profile",
    "{}",
    "하세요",
}


def run_all_checks() -> tuple[bool, list[str], int]:
    """Run registry, fixture, output, serialization, and determinism checks."""
    errors = []
    taxonomy_keys = load_taxonomy_keys()
    registry = load_json(REGISTRY_PATH)
    errors.extend(validate_registry(registry, taxonomy_keys))

    fixture_paths = sorted(glob.glob(FIXTURE_PATTERN))
    if len(fixture_paths) != EXPECTED_FIXTURE_COUNT:
        errors.append(f"fixture count {len(fixture_paths)} != {EXPECTED_FIXTURE_COUNT}")

    passed = 0
    for fixture_path in fixture_paths:
        path = Path(fixture_path)
        fixture_errors = validate_fixture(path, registry)
        if fixture_errors:
            errors.extend(f"{path.name}: {error}" for error in fixture_errors)
        else:
            passed += 1

    return not errors, errors, passed


def load_taxonomy_keys() -> set[str]:
    data = load_json(TAXONOMY_PATH)
    return {item["skill_key"] for item in data.get("skills", []) if item.get("skill_key")}


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def validate_registry(registry: Any, taxonomy_keys: set[str]) -> list[str]:
    errors = []
    if not isinstance(registry, dict):
        return ["skill_descriptions.json must parse to an object"]

    registry_keys = set(registry)
    missing = sorted(taxonomy_keys - registry_keys)
    extra = sorted(registry_keys - taxonomy_keys)
    if missing:
        errors.append(f"registry missing taxonomy keys: {', '.join(missing)}")
    if extra:
        errors.append(f"registry contains unknown keys: {', '.join(extra)}")

    for skill_key in sorted(taxonomy_keys & registry_keys):
        item = registry.get(skill_key)
        if not isinstance(item, dict):
            errors.append(f"{skill_key}: registry entry must be an object")
            continue
        fields = set(item)
        missing_fields = sorted(REQUIRED_REGISTRY_FIELDS - fields)
        extra_fields = sorted(fields - REQUIRED_REGISTRY_FIELDS)
        if missing_fields:
            errors.append(f"{skill_key}: missing fields {', '.join(missing_fields)}")
        if extra_fields:
            errors.append(f"{skill_key}: unknown fields {', '.join(extra_fields)}")
        errors.extend(_validate_no_empty_strings(item, f"registry.{skill_key}"))
        keywords = item.get("keywords")
        if not isinstance(keywords, list) or not keywords:
            errors.append(f"{skill_key}: keywords must be a non-empty array")
    return errors


def validate_fixture(path: Path, registry: dict[str, dict[str, Any]]) -> list[str]:
    errors = []
    report = load_json(path)

    runs = []
    for _index in range(3):
        output = generate_narratives(report, registry=registry)
        json.dumps(output, ensure_ascii=False, sort_keys=True)
        runs.append(output)

    if not (runs[0] == runs[1] == runs[2]):
        errors.append("deterministic 3-run check failed")

    output = runs[0]
    missing = sorted(REQUIRED_OUTPUT_FIELDS - set(output))
    if missing:
        errors.append(f"missing output fields: {', '.join(missing)}")
        return errors

    for field in REQUIRED_OUTPUT_FIELDS:
        value = output.get(field)
        if isinstance(value, list):
            if not value:
                errors.append(f"{field}: empty array")
        elif not isinstance(value, str) or not value.strip():
            errors.append(f"{field}: empty or invalid string")

    errors.extend(_validate_no_empty_strings(output, "output"))
    errors.extend(_validate_no_placeholders(output, "output"))
    return errors


def _validate_no_empty_strings(value: Any, path: str) -> list[str]:
    errors = []
    if isinstance(value, dict):
        for key, child in value.items():
            errors.extend(_validate_no_empty_strings(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_validate_no_empty_strings(child, f"{path}[{index}]"))
    elif isinstance(value, str) and not value.strip():
        errors.append(f"{path}: empty string")
    return errors


def _validate_no_placeholders(value: Any, path: str) -> list[str]:
    errors = []
    if isinstance(value, dict):
        for key, child in value.items():
            errors.extend(_validate_no_placeholders(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_validate_no_placeholders(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        for term in sorted(FORBIDDEN_OUTPUT_TERMS):
            if term in value:
                errors.append(f"{path}: forbidden placeholder/action text '{term}'")
    return errors


def main() -> int:
    ok, errors, passed = run_all_checks()
    for error in errors:
        print(f"[FAIL] {error}")
    if ok:
        print(f"Text template check passed: {passed}/{EXPECTED_FIXTURE_COUNT}")
        print("Determinism: PASS (3/3 runs identical)")
        return 0
    print(f"Text template check failed: {passed}/{EXPECTED_FIXTURE_COUNT}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
