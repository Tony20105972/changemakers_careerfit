#!/usr/bin/env python3
"""Deterministic primary_profile selector for CareerFit Contract v1.5."""

from __future__ import annotations

import glob
import json
import re
from collections import OrderedDict
from pathlib import Path


CONFIDENCE_HIGH_THRESHOLD = 8
CONFIDENCE_MEDIUM_THRESHOLD = 5
DEFAULT_FALLBACK_PROFILE = "operations"
LOW_CONFIDENCE_WARNING = (
    "입력 정보가 부족하여 일부 결과는 추정에 기반합니다. "
    "경력 정보를 추가하면 더 정확한 분석이 가능합니다."
)
UNIQUE_MATCH_WEIGHT = 0.65
COMMON_MATCH_WEIGHT = 0.35
ZERO_TOLERANCE = 1e-9
MAX_SECONDARY_PROFILES = 2

PROFILE_HINT_ALIASES = {
    "customer_success": ["customer success", "고객 성공", "고객성공"],
    "data": ["data", "bi", "sql", "데이터", "분석가"],
    "engineering": ["backend", "api", "engineer", "engineering", "개발자", "엔지니어", "백엔드"],
    "hr": ["hr", "hrbp", "people", "인사", "인재", "채용", "온보딩"],
    "marketing": ["marketing", "ga", "roas", "마케팅", "브랜드", "캠페인"],
    "operations": ["ops", "operations", "operation", "오퍼레이션"],
    "product": ["pm", "prd", "product", "프로덕트", "제품", "기획"],
}

SKILL_ALIAS_OVERRIDES = {
    "ab_testing": ["a b 테스트", "ab 테스트", "실험 설계"],
    "account_health": ["계정 헬스", "사용률", "고객 건강도", "nps"],
    "account_management": ["계정 관리", "기존 고객 관리", "고객 관계"],
    "api_design": ["api", "rest api", "openapi", "api 설계"],
    "brand_management": ["브랜드", "브랜드 가이드", "브랜드 아이덴티티"],
    "campaign_management": ["캠페인", "마케팅 캠페인", "소재 테스트"],
    "churn_management": ["이탈 방지", "이탈률", "churn", "리텐션"],
    "code_review": ["코드 리뷰", "pr 리뷰", "코드 검토"],
    "communication": ["커뮤니케이션", "소통", "고객 응대", "문의 응대"],
    "competitive_analysis": ["경쟁사 분석", "시장 분석", "벤치마킹"],
    "content_marketing": ["콘텐츠", "블로그", "뉴스레터", "카피", "랜딩페이지"],
    "coordination": ["일정 조율", "업무 조율", "조율", "스케줄", "회의"],
    "cost_management": ["비용", "원가", "비용 절감", "비용 최적화", "예산"],
    "crm_management": ["crm", "세일즈포스", "hubspot", "허브스팟"],
    "crossfunctional_collab": ["협업", "타 부서", "크로스펑셔널", "연동"],
    "customer_feedback_analysis": ["voc", "고객 피드백", "nps", "피드백 분석"],
    "customer_onboarding": ["고객 온보딩", "도입 지원", "온보딩 완료율"],
    "data_analysis": ["데이터", "분석", "지표", "세그먼트", "인사이트"],
    "data_visualization": ["대시보드", "시각화", "tableau", "power bi", "bi"],
    "debugging": ["디버깅", "버그", "장애", "트러블슈팅", "오류"],
    "documentation": ["문서", "문서화", "보고서", "매뉴얼", "정리", "체크리스트"],
    "employee_relations": ["조직문화", "고충", "이탈률", "직원 관계"],
    "excel": ["엑셀", "스프레드시트", "피벗", "집계"],
    "labor_law": ["노동법", "근로기준법", "근로계약", "노사"],
    "logistics": ["물류", "재고", "공급망", "창고", "입출고"],
    "marketing_analytics": ["ga", "roas", "전환율", "마케팅 분석", "성과 분석"],
    "negotiation": ["계약 협상", "딜 클로징", "협상"],
    "negotiation_basic": ["협상", "조건 조율", "계약 조건"],
    "operations_management": ["운영 관리", "운영팀", "오퍼레이션", "현장 운영"],
    "payroll": ["급여", "연봉", "복리후생", "4대보험", "인건비"],
    "performance_management": ["성과 평가", "성과 관리", "kpi", "mbo", "평가"],
    "presentation": ["발표", "pt", "프레젠테이션", "공유"],
    "process_design": ["프로세스 설계", "업무 흐름", "절차", "표준화", "체계"],
    "process_improvement": ["프로세스 개선", "효율화", "자동화", "업무 표준화", "운영 개선"],
    "product_planning": ["prd", "제품 기획", "요구사항", "기능 기획"],
    "python": ["python", "파이썬", "pandas", "판다스"],
    "quality_control": ["품질", "검수", "품질 검토", "품질 기준", "확인"],
    "recruiting": ["채용", "공고", "jd", "서류 전형", "면접", "후보자", "오퍼"],
    "renewal_management": ["계약 갱신", "갱신", "리뉴얼", "연장 계약"],
    "roadmap_management": ["로드맵", "우선순위", "백로그"],
    "seo_sem": ["seo", "sem", "검색광고", "키워드 광고"],
    "social_media": ["sns", "소셜미디어", "채널"],
    "software_development": ["개발", "기능 구현", "프로그래밍", "코딩"],
    "sql": ["sql", "쿼리", "데이터베이스"],
    "sprint_management": ["스프린트", "스크럼", "애자일", "칸반"],
    "stakeholder_management": ["이해관계자", "현업", "리더", "경영진", "파트너"],
    "statistics": ["통계", "회귀분석", "가설 검정", "유의성"],
    "support_ticketing": ["고객 문의", "cs", "티켓", "헬프데스크", "응대"],
    "system_design": ["시스템 설계", "아키텍처", "인프라", "큐 기반"],
    "testing_qa": ["테스트", "qa", "단위 테스트", "통합 테스트", "e2e"],
    "training_and_onboarding": ["입사자 온보딩", "신규 입사자", "입문 교육", "ojt", "신입 교육", "멘토링"],
    "user_research": ["사용자 인터뷰", "사용자 리서치", "fgi", "사용성 테스트", "고객 문의"],
    "ux_sense": ["ux", "와이어프레임", "사용자 경험", "정보구조"],
    "vendor_coordination": ["협력사 소통", "벤더 커뮤니케이션", "소통 창구"],
    "vendor_management": ["벤더", "공급업체", "외주", "협력사 관리", "계약 조건"],
}

LAST_PRIMARY_SCORE = 0.0
LAST_TIE_BREAK = False


def load_taxonomy(path: str = "data/skill_taxonomy.json") -> dict:
    """skill_taxonomy.json 로드. 1회만 호출되도록 caller가 캐싱 책임."""
    with Path(path).open(encoding="utf-8") as file:
        data = json.load(file)
    return {skill["skill_key"]: skill for skill in data.get("skills", [])}


def load_requirements(pattern: str = "data/generated/job_requirements_*.json") -> dict[str, dict]:
    """glob으로 전체 로드. key=profile_id, value=requirement dict."""
    requirements = OrderedDict()
    for path in sorted(glob.glob(pattern)):
        with Path(path).open(encoding="utf-8") as file:
            data = json.load(file)
        profile_id = data.get("profile_id") or Path(path).stem.replace("job_requirements_", "")
        requirements[profile_id] = data
    return dict(requirements)


def extract_text_corpus(fixture: dict) -> str:
    """target_priority_text + career_histories[].description 결합 후 정규화."""
    parts = [fixture.get("target_priority_text", "")]
    for history in fixture.get("career_histories", []):
        for key in ["description", "responsibilities", "achievements", "title", "role"]:
            value = history.get(key)
            if value:
                parts.append(str(value))
    return _normalize(" ".join(parts))


def score_profiles(corpus: str, taxonomy: dict, requirements: dict) -> dict[str, float]:
    """profile_id -> raw_score 매핑. 정렬 순서는 점수 내림차순, 동점 시 profile_id 알파벳순."""
    scores = {}
    for profile_id, profile in sorted(requirements.items()):
        score = 0.0
        for req in profile.get("requirements", []):
            skill_key = req.get("skill_key")
            if skill_key not in taxonomy:
                print(f"[WARN] taxonomy missing skill_key: {skill_key}")
                continue
            count = _count_skill_matches(corpus, skill_key, taxonomy[skill_key])
            if count:
                group = req.get("requirement_type", "COMMON")
                capped_count = min(count, 2)
                score += capped_count * (UNIQUE_MATCH_WEIGHT if group == "UNIQUE" else COMMON_MATCH_WEIGHT)
        hint_bonus = _profile_hint_bonus(corpus, profile_id)
        scores[profile_id] = round(score + hint_bonus, 4)
    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return dict(ordered)


def count_evidence(corpus: str, taxonomy: dict, profile_id: str) -> int:
    """선택된 primary_profile 기준 키워드 매칭 횟수 (evidence_count 산출용)."""
    requirements = load_requirements()
    profile = requirements.get(profile_id, {})
    count = 0
    for req in profile.get("requirements", []):
        skill_key = req.get("skill_key")
        if skill_key in taxonomy:
            count += _count_skill_matches(corpus, skill_key, taxonomy[skill_key])
    return count


def select_primary_and_secondary(
    profile_scores: dict[str, float],
    secondary_threshold_ratio: float = 0.3,
) -> tuple[str, list[str]]:
    """
    primary = max(profile_scores)
    secondary = primary 점수의 30% 이상인 나머지 profile (최대 2개, 점수 내림차순)
    """
    global LAST_PRIMARY_SCORE, LAST_TIE_BREAK
    ordered = sorted(profile_scores.items(), key=lambda item: (-item[1], item[0]))
    if not ordered:
        LAST_PRIMARY_SCORE = 0.0
        LAST_TIE_BREAK = False
        return DEFAULT_FALLBACK_PROFILE, []
    primary, primary_score = ordered[0]
    LAST_PRIMARY_SCORE = primary_score
    LAST_TIE_BREAK = len(ordered) > 1 and abs(ordered[0][1] - ordered[1][1]) < ZERO_TOLERANCE
    threshold = primary_score * secondary_threshold_ratio
    secondary = []
    for profile_id, score in ordered[1:]:
        if score > ZERO_TOLERANCE and score + ZERO_TOLERANCE >= threshold:
            secondary.append(profile_id)
        if len(secondary) >= MAX_SECONDARY_PROFILES:
            break
    return primary, secondary


def classify_confidence(evidence_count: int) -> str:
    """HIGH >= 8, MEDIUM 5-7, LOW 0-4"""
    if evidence_count >= CONFIDENCE_HIGH_THRESHOLD:
        return "HIGH"
    if evidence_count >= CONFIDENCE_MEDIUM_THRESHOLD:
        return "MEDIUM"
    return "LOW"


def apply_fallback(primary_profile: str, confidence_level: str) -> tuple[str, str | None]:
    """
    confidence_level == "LOW" and primary_profile score == 0 인 경우
    primary_profile을 "operations"로 강제 대체.
    반환: (최종 primary_profile, warning_message or None)
    """
    if confidence_level == "LOW" and LAST_PRIMARY_SCORE <= ZERO_TOLERANCE:
        return DEFAULT_FALLBACK_PROFILE, LOW_CONFIDENCE_WARNING
    if confidence_level == "LOW":
        return primary_profile, LOW_CONFIDENCE_WARNING
    return primary_profile, None


def select_profile(fixture: dict) -> dict:
    """전체 파이프라인 실행. 아래 출력 스키마 반환."""
    taxonomy = load_taxonomy()
    requirements = load_requirements()
    corpus = extract_text_corpus(fixture)
    profile_scores = score_profiles(corpus, taxonomy, requirements)
    primary, secondary = select_primary_and_secondary(profile_scores)
    evidence_count = count_evidence(corpus, taxonomy, primary)
    confidence = classify_confidence(evidence_count)
    if confidence == "LOW":
        secondary = []
    primary, warning = apply_fallback(primary, confidence)
    if primary == DEFAULT_FALLBACK_PROFILE and LAST_PRIMARY_SCORE <= ZERO_TOLERANCE:
        secondary = []
        evidence_count = count_evidence(corpus, taxonomy, primary)
        confidence = classify_confidence(evidence_count)
        warning = LOW_CONFIDENCE_WARNING
    reason = _selection_reason(primary, secondary, evidence_count, confidence)
    if LAST_TIE_BREAK:
        reason += " 동점 처리: 알파벳순 우선."
    visible_scores = profile_scores
    if primary == DEFAULT_FALLBACK_PROFILE and LAST_PRIMARY_SCORE <= ZERO_TOLERANCE:
        visible_scores = {DEFAULT_FALLBACK_PROFILE: 0.0}
    return {
        "primary_profile": primary,
        "secondary_profiles": secondary,
        "confidence_level": confidence,
        "evidence_count": evidence_count,
        "warning_message": warning,
        "selection_reason": reason,
        "profile_scores": visible_scores,
    }


def load_sample_inputs(directory: str = "output") -> list[tuple[str, dict]]:
    """sample_input_*.json 전체 로드. (filename, fixture) 리스트 반환."""
    samples = []
    for path in sorted(Path(directory).glob("sample_input_*.json")):
        with path.open(encoding="utf-8") as file:
            samples.append((path.name, json.load(file)))
    return samples


def _normalize(text: str) -> str:
    lowered = text.lower()
    cleaned = re.sub(r"[^0-9a-zA-Z가-힣]+", " ", lowered)
    return re.sub(r"\s+", " ", cleaned).strip()


def _skill_aliases(skill_key: str, skill: dict) -> list[str]:
    aliases = [skill_key.replace("_", " "), skill.get("label_ko", ""), skill.get("description", "")]
    aliases.extend(SKILL_ALIAS_OVERRIDES.get(skill_key, []))
    normalized = []
    for alias in aliases:
        value = _normalize(alias)
        if value and value not in normalized:
            normalized.append(value)
    return sorted(normalized, key=lambda value: (-len(value), value))


def _count_skill_matches(corpus: str, skill_key: str, skill: dict) -> int:
    count = 0
    for alias in _skill_aliases(skill_key, skill):
        if len(alias) < 2:
            continue
        pattern = r"(?<![0-9a-zA-Z])" + re.escape(alias) + r"(?![0-9a-zA-Z])"
        count += len(re.findall(pattern, corpus))
    return count


def _profile_hint_bonus(corpus: str, profile_id: str) -> float:
    aliases = PROFILE_HINT_ALIASES.get(profile_id, [])
    return round(sum(_count_alias(corpus, alias) for alias in aliases) * 1.5, 4)


def _count_alias(corpus: str, alias: str) -> int:
    value = _normalize(alias)
    if not value:
        return 0
    pattern = r"(?<![0-9a-zA-Z])" + re.escape(value) + r"(?![0-9a-zA-Z])"
    return len(re.findall(pattern, corpus))


def _selection_reason(primary: str, secondary: list[str], evidence_count: int, confidence: str) -> str:
    if confidence == "LOW" and primary == DEFAULT_FALLBACK_PROFILE and LAST_PRIMARY_SCORE <= ZERO_TOLERANCE:
        return "직무 관련 키워드 매칭 부족으로 default_fallback_profile(operations) 적용."
    if confidence == "LOW":
        return "입력 정보가 부족하여 일부 결과는 추정에 기반합니다."
    if secondary:
        return f"{primary} 키워드가 우세하며 보조 프로필 {', '.join(secondary)} 신호도 확인됨."
    return f"{primary} 키워드가 가장 높게 매칭되어 primary_profile로 선택됨. evidence_count={evidence_count}."


if __name__ == "__main__":
    for filename, sample in load_sample_inputs():
        result = select_profile(sample)
        print(filename, result["primary_profile"], result["secondary_profiles"], result["confidence_level"])
