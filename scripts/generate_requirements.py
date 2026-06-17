#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = ROOT / "data" / "skill_taxonomy.json"
PROFILE_DIR = ROOT / "data" / "requirement_profiles"
GENERATED_DIR = ROOT / "data" / "generated"
UNIQUE_TOTAL = Decimal("0.65")
COMMON_TOTAL = Decimal("0.35")
TOTAL_WEIGHT = Decimal("1.0")
TOLERANCE = Decimal("0.001")
REQUIREMENT_TYPES = {"UNIQUE", "COMMON"}


class ValidationError(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def load_taxonomy() -> dict[str, dict[str, str]]:
    data = load_json(TAXONOMY_PATH)
    skills = data.get("skills")
    if not isinstance(skills, list):
        raise ValidationError(f"{TAXONOMY_PATH}: skills must be a list")

    lookup: dict[str, dict[str, str]] = {}
    for skill in skills:
        key = skill.get("skill_key")
        if not key:
            raise ValidationError(f"{TAXONOMY_PATH}: skill_key is required")
        if key in lookup:
            raise ValidationError(f"{TAXONOMY_PATH}: duplicate skill_key={key}")
        lookup[key] = skill
    return lookup


def profile_paths() -> list[Path]:
    return sorted(PROFILE_DIR.glob("*.json"))


def quantize(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def decimal_sum(values: list[Decimal]) -> Decimal:
    return quantize(sum(values, Decimal("0")))


def normalize_group(items: list[dict[str, Any]], target: Decimal, profile_path: Path) -> list[Decimal]:
    base_weights = [Decimal(str(item.get("base_weight"))) for item in items]
    base_total = sum(base_weights, Decimal("0"))
    if base_total <= 0:
        raise ValidationError(f"{profile_path}: base_weight sum must be positive")

    normalized: list[Decimal] = []
    for index, base_weight in enumerate(base_weights):
        if index == len(base_weights) - 1:
            normalized.append(quantize(target - sum(normalized, Decimal("0"))))
        else:
            normalized.append(quantize(target * base_weight / base_total))
    return normalized


def validate_profile(profile: dict[str, Any], path: Path, taxonomy: dict[str, dict[str, str]]) -> None:
    profile_id = profile.get("profile_id")
    if profile_id != path.stem:
        raise ValidationError(f"{path}: profile_id must match filename")

    requirements = profile.get("requirements")
    if not isinstance(requirements, list):
        raise ValidationError(f"{path}: requirements must be a list")

    seen: set[str] = set()
    counts = {"UNIQUE": 0, "COMMON": 0}
    for item in requirements:
        skill_key = item.get("skill_key")
        if skill_key not in taxonomy:
            raise ValidationError(f"{path}: unknown skill_key={skill_key}")
        if skill_key in seen:
            raise ValidationError(f"{path}: duplicate skill_key={skill_key}")
        seen.add(skill_key)

        requirement_type = item.get("requirement_type")
        if requirement_type not in REQUIREMENT_TYPES:
            raise ValidationError(f"{path}: {skill_key} invalid requirement_type={requirement_type}")
        counts[requirement_type] += 1

        try:
            base_weight = Decimal(str(item.get("base_weight")))
        except Exception as exc:
            raise ValidationError(f"{path}: {skill_key} invalid base_weight") from exc
        if base_weight <= 0:
            raise ValidationError(f"{path}: {skill_key} base_weight must be positive")

    if counts["UNIQUE"] < 3:
        raise ValidationError(f"{path}: UNIQUE requirements must be at least 3")
    if counts["COMMON"] < 3:
        raise ValidationError(f"{path}: COMMON requirements must be at least 3")


def build_output(profile: dict[str, Any], path: Path, taxonomy: dict[str, dict[str, str]]) -> dict[str, Any]:
    validate_profile(profile, path, taxonomy)
    profile_id = profile["profile_id"]
    requirements = profile["requirements"]
    unique_items = [item for item in requirements if item["requirement_type"] == "UNIQUE"]
    common_items = [item for item in requirements if item["requirement_type"] == "COMMON"]
    unique_weights = normalize_group(unique_items, UNIQUE_TOTAL, path)
    common_weights = normalize_group(common_items, COMMON_TOTAL, path)
    weight_by_key = {
        item["skill_key"]: weight
        for item, weight in [*zip(unique_items, unique_weights), *zip(common_items, common_weights)]
    }

    output_requirements = []
    for item in requirements:
        skill_key = item["skill_key"]
        skill = taxonomy[skill_key]
        output_requirements.append(
            {
                "skill_key": skill_key,
                "label_ko": skill["label_ko"],
                "description": skill["description"],
                "requirement_type": item["requirement_type"],
                "weight": float(weight_by_key[skill_key]),
                "is_core": bool(item.get("is_core", False)),
                "source_profiles": [profile_id],
            }
        )

    unique_sum = decimal_sum([weight_by_key[item["skill_key"]] for item in unique_items])
    common_sum = decimal_sum([weight_by_key[item["skill_key"]] for item in common_items])
    total_sum = quantize(unique_sum + common_sum)

    if abs(unique_sum - UNIQUE_TOTAL) > TOLERANCE:
        raise ValidationError(f"{path}: normalized UNIQUE sum={unique_sum}")
    if abs(common_sum - COMMON_TOTAL) > TOLERANCE:
        raise ValidationError(f"{path}: normalized COMMON sum={common_sum}")
    if abs(total_sum - TOTAL_WEIGHT) > TOLERANCE:
        raise ValidationError(f"{path}: normalized TOTAL sum={total_sum}")

    return {
        "profile_id": profile_id,
        "profile_name": profile["profile_name"],
        "profile_name_ko": profile["profile_name_ko"],
        "version": "MANUAL_V1_NORMALIZED",
        "weight_source": profile.get("weight_source", "MANUAL_V1"),
        "weight_policy": {
            "unique_total": float(UNIQUE_TOTAL),
            "common_total": float(COMMON_TOTAL),
            "total": float(TOTAL_WEIGHT),
        },
        "requirements": output_requirements,
        "validation": {
            "unique_weight_sum": float(unique_sum),
            "common_weight_sum": float(common_sum),
            "total_weight_sum": float(total_sum),
            "requirement_count": len(output_requirements),
        },
    }


def json_text(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def active_profiles(selected_profile: str | None) -> list[tuple[Path, dict[str, Any]]]:
    profiles: list[tuple[Path, dict[str, Any]]] = []
    for path in profile_paths():
        profile = load_json(path)
        if selected_profile and path.stem != selected_profile:
            continue
        if profile.get("status") == "ACTIVE":
            profiles.append((path, profile))

    if selected_profile and not profiles:
        raise ValidationError(f"{PROFILE_DIR}/{selected_profile}.json: ACTIVE profile not found")
    return profiles


def validate_outputs(outputs: list[dict[str, Any]]) -> None:
    rendered_once = [json_text(output) for output in outputs]
    rendered_twice = [json_text(output) for output in outputs]
    if rendered_once != rendered_twice:
        raise ValidationError("determinism check failed")


def run(args: argparse.Namespace) -> int:
    taxonomy = load_taxonomy()
    profiles = active_profiles(args.profile)
    outputs = [(path, build_output(profile, path, taxonomy)) for path, profile in profiles]
    validate_outputs([output for _, output in outputs])

    if args.list:
        for _, output in outputs:
            print(output["profile_id"])
        return 0

    if not args.check:
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        for _, output in outputs:
            output_path = GENERATED_DIR / f"job_requirements_{output['profile_id']}.json"
            output_path.write_text(json_text(output), encoding="utf-8")
        print(f"생성 완료: {len(outputs)} profiles")
        return 0

    print(f"검증 통과: {len(outputs)}/{len(outputs)} profiles")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate normalized CareerFit requirement profiles.")
    parser.add_argument("--check", action="store_true", help="validate without writing generated files")
    parser.add_argument("--profile", help="generate or validate one profile_id")
    parser.add_argument("--list", action="store_true", help="list ACTIVE profile ids")
    return parser.parse_args()


def main() -> int:
    try:
        return run(parse_args())
    except ValidationError as exc:
        print(f"검증 실패: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
