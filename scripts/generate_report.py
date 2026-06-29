#!/usr/bin/env python3
"""Run the deterministic CareerFit engine pipeline and save Report JSON."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.engine import (  # noqa: E402
    evidence_extractor,
    gap_analyzer,
    profile_selector,
    requirement_matcher,
    scoring_engine,
    strength_selector,
    text_template,
)
from backend.engine.report_builder import REPORT_TOP_LEVEL_KEYS, build_report  # noqa: E402


DEFAULT_OUTPUT = REPO_ROOT / "output" / "debug_report.json"
DEFAULT_GENERATED_AT = "2025-01-01T00:00:00Z"
REFERENCE_DATE = date(2025, 1, 1)
ENGINE_VERSION = "3.1.0"
FIT_LABELS = (
    (90, "EXCELLENT_FIT", "최우수"),
    (75, "GOOD_FIT", "우수"),
    (55, "MODERATE_FIT", "보통"),
    (0, "LOW_FIT", "미흡"),
)
PROFILE_LABELS = text_template.PROFILE_LABELS


def main() -> int:
    args = parse_args()
    fixture_path = resolve_fixture_path(args.fixture)
    output_path = resolve_output_path(args.output)

    fixture = load_json(fixture_path)
    report = generate_report(fixture=fixture, fixture_name=fixture_path.stem)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2, sort_keys=False)
        file.write("\n")

    validate_written_json(output_path, report)
    print(f"Report JSON written: {output_path.relative_to(REPO_ROOT)}")
    print("JSON Parse: PASS")
    print("Determinism: PASS (3/3 runs identical)")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CareerFit Report JSON from a fixture.")
    parser.add_argument(
        "--fixture",
        default="hr_dominant",
        help="Fixture name such as 'hr_dominant' or a direct JSON path.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Output JSON path. Default: output/debug_report.json",
    )
    return parser.parse_args()


def generate_report(fixture: dict[str, Any], fixture_name: str) -> dict[str, Any]:
    runs = [_run_pipeline(fixture, fixture_name) for _index in range(3)]
    if not (runs[0] == runs[1] == runs[2]):
        raise RuntimeError("determinism check failed: repeated runs produced different reports")
    return runs[0]


def _run_pipeline(fixture: dict[str, Any], fixture_name: str) -> dict[str, Any]:
    profile_result = profile_selector.select_profile(fixture)
    primary_profile = str(profile_result["primary_profile"])
    confidence_level = str(profile_result["confidence_level"])

    taxonomy = evidence_extractor.load_taxonomy()
    evidences = evidence_extractor.extract_evidence(fixture, taxonomy)
    requirements = requirement_matcher.load_requirements_for_profile(primary_profile)
    requirement_profile = load_requirement_profile(primary_profile)
    requirement_matches = requirement_matcher.match_requirements(primary_profile, evidences)
    scores = build_scores(requirement_matches, requirements)
    strengths = strength_selector.select_strengths(
        requirement_matches,
        evidences,
        taxonomy,
        confidence_level,
    )
    gaps = gap_analyzer.analyze_gaps(
        requirement_matches,
        requirements,
        taxonomy,
        confidence_level,
    )

    seed_report = {
        "meta": {
            "primary_profile": primary_profile,
            "confidence_level": confidence_level,
            "fit_level": scores["fit_level"],
        },
        "scores": scores,
        "strengths": strengths,
        "gaps": gaps,
        "evidenceMapping": evidences,
    }
    narratives = text_template.generate_narratives(seed_report)
    summary = build_summary(
        profile_result=profile_result,
        scores=scores,
        strengths=strengths,
        gaps=gaps,
        executive_summary=narratives["executive_summary"],
    )
    skill_narratives = build_skill_narratives(narratives)

    return build_report(
        report_id=fixture_name.replace("sample_input_", "debug_"),
        generated_at=DEFAULT_GENERATED_AT,
        version=ENGINE_VERSION,
        llm_used=False,
        weight_source=str(requirement_profile.get("weight_source") or "MANUAL_V1"),
        evidence_count=int(profile_result.get("evidence_count") or len(evidences)),
        primary_profile=primary_profile,
        secondary_profiles=list(profile_result.get("secondary_profiles") or []),
        confidence_level=confidence_level,
        warning_message=profile_result.get("warning_message"),
        evidenceMapping=evidences,
        scores=scores,
        strengths=strengths,
        gaps=gaps,
        executive_summary=summary,
        strength_narratives=narratives["strength_narratives"],
        gap_narratives=narratives["gap_narratives"],
        skill_explanations=narratives["skill_explanations"],
        job_outlook=narratives["job_outlook"],
        final_assessment=narratives["final_assessment"],
        careerProfile=build_career_profile(fixture, evidences, requirements),
        targetJobAnalysis=build_target_job_analysis(
            primary_profile=primary_profile,
            secondary_profiles=list(profile_result.get("secondary_profiles") or []),
            profile=requirement_profile,
            requirements=requirements,
            matches=requirement_matches,
        ),
        skillMapping=build_skill_mapping(requirements, requirement_matches),
        skill_narratives=skill_narratives,
    )


def build_scores(matches: list[dict[str, Any]], requirements: list[dict[str, Any]]) -> dict[str, Any]:
    unique_fraction = scoring_engine.compute_unique_total(matches, requirements)
    common_fraction = scoring_engine.compute_common_total(matches, requirements)
    core_penalty = scoring_engine.compute_core_penalty(matches, requirements)
    total_score = scoring_engine.compute_total_score(unique_fraction, common_fraction, core_penalty)
    fit_level, score_label = classify_fit(total_score)
    return {
        "total": total_score,
        "total_score": total_score,
        "score_label": score_label,
        "fit_level": fit_level,
        "unique_total": round(unique_fraction * 100, 1),
        "common_total": round(common_fraction * 100, 1),
        "core_penalty": core_penalty,
        "breakdown": build_score_breakdown(requirements, matches),
    }


def build_score_breakdown(
    requirements: list[dict[str, Any]],
    matches: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    match_lookup = {str(match.get("requirement_id")): match for match in matches}
    breakdown = {}
    for requirement in requirements:
        match = match_lookup.get(str(requirement.get("requirement_id")), {})
        skill_key = str(requirement.get("skill_key"))
        match_score = float(match.get("match_score", 0.0))
        evidence_id = match.get("matched_evidence_id")
        breakdown[skill_key] = {
            "weight": requirement.get("weight"),
            "skill_group": skill_group(requirement),
            "match_level": match.get("match_level", "NONE"),
            "match_score": match_score,
            "weighted_score": round(float(requirement.get("weight", 0.0)) * match_score * 100, 2),
            "evidence_count": 1 if evidence_id else 0,
            "confidence_total": 0.0,
        }
    return breakdown


def build_summary(
    *,
    profile_result: dict[str, Any],
    scores: dict[str, Any],
    strengths: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    executive_summary: str,
) -> dict[str, Any]:
    primary_profile = str(profile_result.get("primary_profile") or "")
    confidence_level = str(profile_result.get("confidence_level") or "LOW")
    return {
        "total_score": scores["total"],
        "score_label": scores["score_label"],
        "fit_level": scores["fit_level"],
        "one_line": executive_summary,
        "primary_profile_summary": build_primary_profile_summary(
            primary_profile=primary_profile,
            secondary_profiles=list(profile_result.get("secondary_profiles") or []),
            confidence_level=confidence_level,
        ),
        "unique_score": scores["unique_total"],
        "unique_score_max": 65.0,
        "common_score": scores["common_total"],
        "common_score_max": 35.0,
        "key_strengths": [item["skill_key"] for item in strengths[:3]],
        "key_gaps": [item["skill_key"] for item in gaps[:2]],
    }


def build_career_profile(
    fixture: dict[str, Any],
    evidences: list[dict[str, Any]],
    requirements: list[dict[str, Any]],
) -> dict[str, Any]:
    histories = list(fixture.get("career_histories") or [])
    requirement_by_skill = {str(item.get("skill_key")): item for item in requirements}
    grouped = group_evidence_by_skill(evidences)
    extracted_skills = []
    for skill_key in sorted(grouped):
        if skill_key not in requirement_by_skill:
            continue
        items = grouped[skill_key]
        confidence_total = round(sum(float(item.get("confidence_score", 0.0)) for item in items), 2)
        extracted_skills.append(
            {
                "skill_key": skill_key,
                "label_ko": items[0].get("label_ko") or skill_key,
                "skill_group": skill_group(requirement_by_skill[skill_key]),
                "evidence_count": len(items),
                "confidence_total": confidence_total,
                "confidence_label": confidence_label(confidence_total),
            }
        )
    return {
        "total_experience_months": total_experience_months(histories),
        "total_experience_label": experience_label(total_experience_months(histories)),
        "career_count": len(histories),
        "most_recent_title": histories[0].get("title") if histories else None,
        "most_recent_company": histories[0].get("company_name") if histories else None,
        "extracted_skills": extracted_skills,
    }


def build_target_job_analysis(
    *,
    primary_profile: str,
    secondary_profiles: list[str],
    profile: dict[str, Any],
    requirements: list[dict[str, Any]],
    matches: list[dict[str, Any]],
) -> dict[str, Any]:
    unique_requirements = []
    common_requirements = []
    match_by_requirement = {str(item.get("requirement_id")): item for item in matches}
    for requirement in requirements:
        item = {
            "requirement_key": requirement.get("skill_key"),
            "label_ko": requirement.get("label_ko"),
            "weight": requirement.get("weight"),
            "is_core": bool(requirement.get("is_core", False)),
            "match_level": match_by_requirement.get(str(requirement.get("requirement_id")), {}).get(
                "match_level",
                "NONE",
            ),
            "source_profiles": list(requirement.get("source_profiles") or [primary_profile]),
        }
        if skill_group(requirement) == "UNIQUE":
            unique_requirements.append(item)
        else:
            common_requirements.append(item)
    return {
        "primary_profile": primary_profile,
        "primary_profile_label_ko": profile_label(primary_profile, profile),
        "secondary_profiles": secondary_profiles,
        "unique_requirements": unique_requirements,
        "common_requirements": common_requirements,
        "requirement_overview": build_requirement_overview(primary_profile, profile),
    }


def build_skill_mapping(
    requirements: list[dict[str, Any]],
    matches: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    matched = []
    unmatched = []
    match_by_requirement = {str(item.get("requirement_id")): item for item in matches}
    for requirement in requirements:
        match = match_by_requirement.get(str(requirement.get("requirement_id")), {})
        match_level = str(match.get("match_level") or "NONE")
        match_score = float(match.get("match_score", 0.0))
        item = {
            "skill_key": requirement.get("skill_key"),
            "label_ko": requirement.get("label_ko"),
            "skill_group": skill_group(requirement),
            "match_level": match_level,
            "weight": requirement.get("weight"),
            "weighted_score": round(float(requirement.get("weight", 0.0)) * match_score * 100, 2),
        }
        if match_level in {"FULL", "STRONG"}:
            matched.append(item)
        else:
            unmatched.append(item)
    return {"matched": matched, "unmatched": unmatched}


def build_skill_narratives(narratives: dict[str, Any]) -> dict[str, Any]:
    return {
        "career_context": narratives["executive_summary"],
        "market_context": narratives["job_outlook"],
        "development_direction": narratives["final_assessment"],
        "job_outlook": narratives["job_outlook"],
        "final_assessment": narratives["final_assessment"],
    }


def build_primary_profile_summary(
    *,
    primary_profile: str,
    secondary_profiles: list[str],
    confidence_level: str,
) -> str:
    label = PROFILE_LABELS.get(primary_profile, primary_profile)
    secondary_labels = [PROFILE_LABELS.get(item, item) for item in secondary_profiles[:2]]
    if confidence_level == "LOW":
        return f"입력 정보가 제한적이므로 {label}를 임시 대표 프로필로 선택했습니다."
    if confidence_level == "MEDIUM" and secondary_labels:
        return f"입력된 근거로 {label}를 대표 프로필로 선택할 수 있습니다. 일부 보조 신호는 {', '.join(secondary_labels)}에서도 확인됩니다."
    return f"입력된 근거를 기준으로 {label}를 대표 프로필로 선택했습니다."


def classify_fit(score: float) -> tuple[str, str]:
    for minimum, fit_level, label in FIT_LABELS:
        if score >= minimum:
            return fit_level, label
    return "LOW_FIT", "미흡"


def confidence_label(confidence_total: float) -> str:
    if confidence_total >= 1.5:
        return "HIGH"
    if confidence_total >= 0.7:
        return "MEDIUM"
    return "LOW"


def skill_group(requirement: dict[str, Any]) -> str:
    return str(requirement.get("skill_type") or requirement.get("requirement_type") or "COMMON").upper()


def profile_label(profile_id: str, profile: dict[str, Any]) -> str:
    return str(profile.get("profile_name_ko") or PROFILE_LABELS.get(profile_id) or profile_id)


def build_requirement_overview(primary_profile: str, profile: dict[str, Any]) -> str:
    label = profile_label(primary_profile, profile)
    return f"입력된 근거를 기준으로 {label}를 대표 프로필로 선택하고 해당 요구사항을 평가합니다."


def group_evidence_by_skill(evidences: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for evidence in evidences:
        grouped[str(evidence.get("skill_key"))].append(evidence)
    return dict(grouped)


def total_experience_months(histories: list[dict[str, Any]]) -> int:
    total = 0
    for history in histories:
        start = parse_month(history.get("start_date"))
        end = REFERENCE_DATE if history.get("is_current") else parse_month(history.get("end_date"))
        if not start or not end:
            continue
        total += max(0, (end.year - start.year) * 12 + end.month - start.month + 1)
    return total


def experience_label(months: int) -> str:
    years, remaining_months = divmod(months, 12)
    if years and remaining_months:
        return f"{years}년 {remaining_months}개월"
    if years:
        return f"{years}년"
    return f"{remaining_months}개월"


def parse_month(value: Any) -> date | None:
    if not value:
        return None
    text = str(value)
    parts = text.split("-")
    if len(parts) < 2:
        return None
    return date(int(parts[0]), int(parts[1]), 1)


def load_requirement_profile(primary_profile: str) -> dict[str, Any]:
    path = REPO_ROOT / "data" / "generated" / f"job_requirements_{primary_profile}.json"
    return load_json(path)


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def resolve_fixture_path(value: str) -> Path:
    raw_path = Path(value)
    if raw_path.exists():
        return raw_path
    named_path = REPO_ROOT / "output" / f"sample_input_{value}.json"
    if named_path.exists():
        return named_path
    raise FileNotFoundError(f"fixture not found: {value}")


def resolve_output_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def validate_written_json(path: Path, expected_report: dict[str, Any]) -> None:
    parsed = load_json(path)
    if parsed != expected_report:
        raise RuntimeError("written report does not match generated report")
    if tuple(parsed.keys()) != REPORT_TOP_LEVEL_KEYS:
        raise RuntimeError("report top-level keys do not match docs/05 schema")
    json.dumps(parsed, ensure_ascii=False)


if __name__ == "__main__":
    raise SystemExit(main())
