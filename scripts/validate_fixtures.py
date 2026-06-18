#!/usr/bin/env python3
"""CareerFit Benchmark Validation Suite v1.5"""

import json
import os
import subprocess
import sys
from pathlib import Path


OUTPUT_DIR = Path("output")
REQUIREMENTS_DIR = Path("data/generated")
REPORT_PREFIX = "sample_report_"
INPUT_PREFIX = "sample_input_"
EXPECTED_COUNT = 10

VALID_CONFIDENCE_LEVELS = {"HIGH", "MEDIUM", "LOW"}
MIN_EVIDENCE_HIGH_MED = 8
MIN_EVIDENCE_LOW = 4
MIN_STRENGTHS = 3
MIN_GAPS = 2
MIN_RECOMMENDATIONS = 3
WEIGHT_UNIQUE = 0.65
WEIGHT_COMMON = 0.35
WEIGHT_TOLERANCE = 0.01
REQUIRED_ROADMAP_KEYS = ["30_days", "60_days", "90_days"]
LOW_FILENAME_KEYWORDS = ["low_confidence", "blocked"]
DEPRECATED_BLEND_KEYS = {"blend_display_mode", "profile_blend", "blend_description"}
REGISTRY_UNIQUE_WEIGHT_MIN = 0.1

REQUIRED_TOP_LEVEL_KEYS = {
    "meta",
    "summary",
    "careerProfile",
    "targetJobAnalysis",
    "skillMapping",
    "evidenceMapping",
    "scores",
    "strengths",
    "gaps",
    "recommendations",
    "roadmap",
    "reportSections",
}

REQUIREMENT_GROUPS = {}
WARNINGS = []


def load_reports() -> list[tuple[str, dict]]:
    reports = []
    for path in sorted(OUTPUT_DIR.glob(f"{REPORT_PREFIX}*.json")):
        try:
            with path.open(encoding="utf-8") as f:
                reports.append((path.name, json.load(f)))
        except Exception as exc:
            reports.append((path.name, {"__parse_error__": str(exc)}))
    return reports


def validate_schema(report: dict) -> list[str]:
    errors = []
    if "__parse_error__" in report:
        return [f"json parse: {report['__parse_error__']}"]
    missing = sorted(REQUIRED_TOP_LEVEL_KEYS - set(report))
    if missing:
        errors.append(f"top-level keys missing: {', '.join(missing)}")
    meta = report.get("meta", {})
    primary = meta.get("primary_profile")
    confidence = meta.get("confidence_level")
    if not isinstance(primary, str) or not primary.strip():
        errors.append("primary_profile: missing or empty")
    if confidence == "BLOCKED":
        errors.append("confidence_level: BLOCKED (BLOCKED는 허용되지 않음)")
    elif confidence not in VALID_CONFIDENCE_LEVELS:
        errors.append(f"confidence_level: invalid ({confidence})")
    text = json.dumps(report, ensure_ascii=False)
    for key in sorted(DEPRECATED_BLEND_KEYS):
        if f'"{key}"' in text:
            WARNINGS.append(f"blend key remains: {key}")
    if '"BLOCKED"' in text:
        errors.append("BLOCKED literal detected")
    return errors


def validate_confidence_mapping(filename: str, report: dict) -> list[str]:
    errors = []
    meta = report.get("meta", {})
    confidence = meta.get("confidence_level")
    evidence_count = meta.get("evidence_count")
    is_low_file = any(keyword in filename for keyword in LOW_FILENAME_KEYWORDS)
    if is_low_file and confidence != "LOW":
        errors.append(f"confidence_level: {confidence} (LOW fixture expected)")
    if confidence == "LOW":
        if not meta.get("warning_message"):
            errors.append("warning_message: missing (LOW fixture 필수)")
        if not isinstance(evidence_count, int) or evidence_count < MIN_EVIDENCE_LOW:
            errors.append(f"evidence_count: {evidence_count} (< {MIN_EVIDENCE_LOW})")
    return errors


def validate_content(report: dict) -> list[str]:
    errors = []
    meta = report.get("meta", {})
    confidence = meta.get("confidence_level")
    evidence = report.get("evidenceMapping", [])
    min_evidence = MIN_EVIDENCE_LOW if confidence == "LOW" else MIN_EVIDENCE_HIGH_MED
    if not isinstance(evidence, list) or len(evidence) < min_evidence:
        errors.append(f"evidenceMapping: {len(evidence) if isinstance(evidence, list) else 'invalid'} (< {min_evidence})")
    if len(report.get("strengths", [])) < MIN_STRENGTHS:
        errors.append(f"strengths: < {MIN_STRENGTHS}")
    if len(report.get("gaps", [])) < MIN_GAPS:
        errors.append(f"gaps: < {MIN_GAPS}")
    recs = report.get("recommendations", {}).get("items", [])
    if len(recs) < MIN_RECOMMENDATIONS:
        errors.append(f"recommendations: < {MIN_RECOMMENDATIONS}")
    roadmap = report.get("roadmap", {})
    for key in REQUIRED_ROADMAP_KEYS:
        actions = roadmap.get(key, {}).get("actions") if isinstance(roadmap, dict) else None
        if not isinstance(actions, list):
            errors.append(f"roadmap.{key}.actions: missing")
    score = report.get("scores", {}).get("total", report.get("summary", {}).get("total_score"))
    if not isinstance(score, (int, float)) or not 0 <= score <= 100:
        errors.append(f"score: invalid ({score})")
    return errors


def validate_weights(report: dict) -> list[str]:
    errors = []
    primary = report.get("meta", {}).get("primary_profile", "")
    for ev in report.get("evidenceMapping", []):
        skill_key = ev.get("skill_key", "")
        weight = ev.get("weight")
        if not isinstance(weight, (int, float)):
            errors.append(f"{ev.get('evidence_id')}: weight missing")
            continue
        profile, _, skill = skill_key.partition(".")
        profile = profile or primary
        skill = skill or skill_key
        group = REQUIREMENT_GROUPS.get(profile, {}).get(skill)
        if group is None:
            errors.append(f"{ev.get('evidence_id')}: unknown requirement ({skill_key})")
            continue
        expected = WEIGHT_UNIQUE if group == "UNIQUE" else WEIGHT_COMMON
        if abs(weight - expected) > WEIGHT_TOLERANCE:
            errors.append(f"{ev.get('evidence_id')}: {group} weight {weight} != {expected}")
    return errors


def run_determinism_check() -> bool:
    env = dict(os.environ)
    env["CAREERFIT_VALIDATE_CHILD"] = "1"
    outputs = []
    for _ in range(3):
        run = subprocess.run(
            [sys.executable, str(Path(__file__))],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        outputs.append((run.returncode, run.stdout, run.stderr))
    return outputs[0] == outputs[1] == outputs[2]


def main() -> int:
    global REQUIREMENT_GROUPS
    for path in sorted(REQUIREMENTS_DIR.glob("job_requirements_*.json")):
        profile = path.stem.replace("job_requirements_", "")
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        requirements = data.get("requirements", data if isinstance(data, list) else [])
        REQUIREMENT_GROUPS[profile] = {}
        for req in requirements:
            key = req.get("requirement_key") or req.get("skill_key")
            weight = req.get("weight", 0)
            group = "UNIQUE" if weight >= REGISTRY_UNIQUE_WEIGHT_MIN else "COMMON"
            REQUIREMENT_GROUPS[profile][key] = group

    report_files = sorted(OUTPUT_DIR.glob(f"{REPORT_PREFIX}*.json"))
    input_files = sorted(OUTPUT_DIR.glob(f"{INPUT_PREFIX}*.json"))
    reports = load_reports()
    failed = 0

    dataset_errors = []
    if len(report_files) != EXPECTED_COUNT:
        dataset_errors.append(f"report count {len(report_files)} != {EXPECTED_COUNT}")
    if len(input_files) != EXPECTED_COUNT:
        dataset_errors.append(f"input count {len(input_files)} != {EXPECTED_COUNT}")
    if dataset_errors:
        failed += 1
        print(f"[FAIL] dataset{' ' * 12} — " + "; ".join(dataset_errors))

    for filename, report in reports:
        fixture = filename.removeprefix(REPORT_PREFIX).removesuffix(".json")
        errors = []
        errors.extend(validate_schema(report))
        if "__parse_error__" not in report:
            errors.extend(validate_confidence_mapping(filename, report))
            errors.extend(validate_content(report))
            errors.extend(validate_weights(report))

        for warning in WARNINGS:
            print(f"[WARN] {fixture:<18} — {warning} (deprecated)")
        WARNINGS.clear()

        if errors:
            failed += 1
            print(f"[FAIL] {fixture:<18} — " + "; ".join(errors))
            continue

        meta = report["meta"]
        evidence_len = len(report.get("evidenceMapping", []))
        score = report.get("scores", {}).get("total", report.get("summary", {}).get("total_score"))
        if meta["confidence_level"] == "LOW":
            warning = "OK" if meta.get("warning_message") else "missing"
            print(f"[PASS] {fixture:<18} — primary:{meta['primary_profile']}, confidence:LOW, warning:{warning}")
        else:
            print(f"[PASS] {fixture:<18} — primary:{meta['primary_profile']}, confidence:{meta['confidence_level']}, evidence:{evidence_len}, score:{score:g}")

    passed = len(reports) - failed
    if failed:
        print(f"Fixture validation failed: {passed}/{len(reports)} reports")
        print("Fix the above before Day 8.")
    else:
        print(f"Fixture validation passed: {passed}/{len(reports)} reports")

    if os.environ.get("CAREERFIT_VALIDATE_CHILD") != "1":
        deterministic = run_determinism_check()
        print(f"Determinism check: {'PASS' if deterministic else 'FAIL'} (3/3 runs identical)")
        if not deterministic:
            failed += 1

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
