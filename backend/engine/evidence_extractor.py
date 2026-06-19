"""Deterministic skill evidence extractor for CareerFit Contract v1.5."""

from __future__ import annotations

import glob
import json
import re
from pathlib import Path


CONFIDENCE_THRESHOLD = 0.5
LOW_FALLBACK_LIMIT = 1
CONFIDENCE_BASE = 0.35
CONFIDENCE_PER_KEYWORD = 0.15
CONFIDENCE_DENSITY_CAP = 0.15
EVIDENCE_ID_PREFIX = "ev_"
SOURCE_CAREER = "career_histories"
SOURCE_TARGET = "target_priority_text"

EXPLICIT_KEYWORDS = {
    "ab_testing": ["a/b 테스트", "ab 테스트", "실험 설계"],
    "account_health": ["계정 헬스", "사용률 모니터링", "고객 건강도", "nps"],
    "account_management": ["계정 관리", "기존 고객 관리", "어카운트 관리"],
    "accounting": ["회계", "재무제표", "전표 처리", "결산"],
    "accessibility": ["접근성", "웹 접근성 표준", "wcag"],
    "api_design": ["api 설계", "rest api", "openapi", "api"],
    "brand_management": ["브랜드 가이드", "브랜드 아이덴티티", "브랜드"],
    "budgeting": ["예산 편성", "예산 관리"],
    "budgeting_advanced": ["예산 수립", "연간 예산 계획", "예산안 작성"],
    "campaign_management": ["마케팅 캠페인 기획", "캠페인", "마케팅 캠페인"],
    "churn_management": ["이탈 방지", "churn 관리", "이탈률 감소", "리텐션"],
    "code_review": ["코드 리뷰", "pr 리뷰", "코드 검토"],
    "communication": ["커뮤니케이션", "소통", "고객 응대", "문의 응대"],
    "competitive_analysis": ["경쟁사 분석", "시장 분석", "벤치마킹"],
    "content_marketing": ["블로그 작성", "콘텐츠 제작", "카피라이팅", "뉴스레터", "랜딩페이지"],
    "coordination": ["일정 조율", "미팅 조율", "스케줄 관리", "조율"],
    "cost_management": ["비용 절감", "원가 관리", "비용 최적화"],
    "crm_management": ["crm", "세일즈포스", "salesforce", "허브스팟", "hubspot"],
    "crossfunctional_collab": ["타 부서 협업", "크로스펑셔널", "협업"],
    "customer_feedback_analysis": ["voc", "고객 피드백 분석", "nps 분석", "피드백 분석"],
    "customer_onboarding": ["고객 온보딩", "도입 지원", "고객 입문 교육"],
    "data_analysis": ["데이터 취합", "데이터 정리 및 분석", "데이터", "분석", "지표"],
    "data_pipeline": ["etl", "데이터 파이프라인", "airflow"],
    "data_visualization": ["대시보드", "시각화", "tableau", "power bi", "루커", "bi"],
    "debugging": ["디버깅", "버그 수정", "트러블슈팅", "장애", "오류"],
    "design_systems": ["디자인 시스템", "컴포넌트 라이브러리", "디자인 가이드"],
    "documentation": ["보고서 작성", "문서화", "매뉴얼", "기획서 작성", "문서", "정리"],
    "employee_relations": ["고충 처리", "조직문화", "이직률 관리", "직원 관계"],
    "excel": ["엑셀", "스프레드시트", "피벗테이블", "피벗"],
    "financial_modeling": ["재무 모델", "재무 모델링", "dcf", "밸류에이션"],
    "financial_reporting": ["재무 보고", "투자자 리포트", "ir 자료"],
    "forecasting": ["매출 예측", "수요 예측", "파이프라인 예측"],
    "hr_policy": ["취업규칙", "인사규정", "hr 정책"],
    "hris": ["hris", "인사 시스템 운영"],
    "labor_law": ["근로기준법", "노동법", "노사 관계", "근로계약"],
    "lead_generation": ["리드 발굴", "신규 영업", "콜드 콜", "아웃바운드"],
    "leadership": ["팀 리드", "팀장", "조직 관리"],
    "logistics": ["물류", "재고 관리", "공급망", "창고 관리", "입출고"],
    "marketing_analytics": ["ga", "전환율 분석", "roas", "퍼포먼스 마케팅", "성과 분석"],
    "mentoring": ["멘토링", "코칭", "ojt 지도"],
    "negotiation": ["계약 협상", "딜 클로징", "조건 협상"],
    "negotiation_basic": ["협상", "조건 조율", "계약서 검토"],
    "operations_management": ["운영 관리", "오퍼레이션 총괄", "시설 관리", "현장 운영"],
    "payroll": ["급여", "연봉", "복리후생", "4대보험", "인건비", "비용 정산"],
    "performance_management": ["성과 평가", "kpi", "mbo", "인사 평가", "성과 관리", "평가"],
    "pipeline_management": ["영업 파이프라인", "딜 단계 관리", "세일즈 파이프라인"],
    "presentation": ["발표", "pt", "프레젠테이션", "공유"],
    "problem_solving": ["문제 해결", "이슈 해결"],
    "process_design": ["프로세스 설계", "업무 표준화", "절차", "체계", "업무 흐름"],
    "process_improvement": ["프로세스 개선", "효율화", "자동화", "표준화", "업무"],
    "product_planning": ["prd", "제품 기획", "요구사항 정의", "기능 기획", "요구사항"],
    "prototyping": ["프로토타입", "figma", "인터랙션 디자인", "피그마"],
    "python": ["python", "파이썬", "판다스", "pandas"],
    "quality_control": ["품질 검토", "qc", "검수", "확인"],
    "quality_management": ["품질 관리 체계", "iso", "품질 기준", "품질 관리"],
    "recruiting": ["채용", "공고 작성", "jd 작성", "서류 전형", "면접", "후보자", "오퍼"],
    "renewal_management": ["계약 갱신", "리뉴얼", "연장 계약", "갱신율"],
    "reporting": ["정기 보고", "주간 보고", "경영진 보고", "보고"],
    "roadmap_management": ["로드맵", "우선순위 설정", "백로그 관리", "우선순위"],
    "seo_sem": ["seo", "sem", "검색광고", "키워드 광고"],
    "social_media": ["sns 운영", "소셜미디어 채널 관리", "소셜미디어", "sns"],
    "software_development": ["기능을 개발", "기능 개발", "기능 구현", "프로그래밍", "코딩"],
    "sprint_management": ["스프린트", "스크럼", "애자일", "칸반"],
    "sql": ["sql", "쿼리", "데이터베이스"],
    "stakeholder_management": ["이해관계자 관리", "스테이크홀더", "현업", "경영진", "리더"],
    "statistics": ["통계", "회귀분석", "가설 검정", "유의성", "통계적"],
    "support_ticketing": ["cs 티켓", "고객 문의 응대", "헬프데스크", "고객 문의", "cs"],
    "system_design": ["시스템 설계", "아키텍처 설계", "인프라 설계", "아키텍처"],
    "tax_compliance": ["세무", "세금 신고", "세무 신고"],
    "testing_qa": ["테스트 코드", "qa", "단위 테스트", "e2e 테스트", "통합 테스트"],
    "tooling_adoption": ["신규 툴 도입", "시스템 전환"],
    "training": ["사내 교육", "교육 프로그램 기획"],
    "training_and_onboarding": ["온보딩", "입문 교육", "ojt", "신입 교육", "신규 입사자"],
    "ui_design": ["ui 디자인", "인터페이스 디자인", "시각 디자인"],
    "user_research": ["사용자 인터뷰", "fgi", "사용성 테스트", "ux 리서치", "사용자 리서치"],
    "ux_sense": ["와이어프레임", "ux 설계", "ia", "정보구조", "ux"],
    "vendor_coordination": ["협력사 소통", "벤더 커뮤니케이션", "소통 창구"],
    "vendor_management": ["벤더", "공급업체", "외주 계약", "협력사 관리"],
    "wireframing": ["와이어프레임", "스케치", "목업"],
}

INFERRED_RULES = [
    ("후보자 관리", "recruiting", 0.8),
    ("신입사원 적응 지원", "training_and_onboarding", 0.75),
    ("팀원 피드백", "performance_management", 0.6),
    ("데이터 취합 및 정리", "data_analysis", 0.7),
    ("엑셀로 집계", "excel", 0.8),
    ("여러 부서와 협업", "crossfunctional_collab", 0.7),
    ("팀장 역할", "leadership", 0.85),
    ("고객 응대", "support_ticketing", 0.6),
    ("예산 관리", "cost_management", 0.7),
    ("재고 관리", "logistics", 0.8),
    ("신규 입사자 서류 처리", "hris", 0.6),
    ("사내 행사 일정 조율", "coordination", 0.8),
    ("고객 관계 유지", "account_management", 0.7),
    ("디자인 가이드 준수", "design_systems", 0.6),
    ("버그 리포트 작성", "debugging", 0.6),
    ("hrm 관련 경력", "performance_management", 0.7),
    ("hrm 관련 경력", "payroll", 0.7),
    ("인사 직무 경력", "performance_management", 0.7),
    ("인사 직무 경력", "payroll", 0.7),
    ("hrd 업무", "training_and_onboarding", 0.75),
    ("인재개발", "training_and_onboarding", 0.75),
    ("hr 분야", "performance_management", 0.6),
    ("hr 분야", "communication", 0.6),
    ("성취 중심", "leadership", 0.5),
    ("데이터 작업", "data_analysis", 0.7),
]

ACHIEVED_PATTERNS = [
    (r"채용.*(?:달성|충원)|충원", "recruiting", 0.9),
    (r"온보딩.*(?:만족도|달성)|만족도.*온보딩", "training_and_onboarding", 0.85),
    (r"이직률.*(?:감소|낮)", "employee_relations", 0.8),
    (r"급여.*오류율", "payroll", 0.9),
    (r"프로세스.*(?:단축|개선)|처리 시간.*단축", "process_improvement", 0.9),
    (r"비용.*(?:절감|줄)", "cost_management", 0.85),
    (r"전환율.*(?:향상|개선|높)", "marketing_analytics", 0.85),
    (r"(?:mau|트래픽).*증가", "content_marketing", 0.8),
    (r"쿼리.*성능.*개선", "sql", 0.85),
    (r"매출.*증가", "account_management", 0.85),
    (r"계약 갱신율|갱신율", "renewal_management", 0.85),
    (r"디자인.*시간.*단축", "design_systems", 0.8),
    (r"(?:장애|버그|오류).*(?:해결|감소|줄)", "debugging", 0.85),
    (r"예산.*(?:절감|줄)", "budgeting_advanced", 0.85),
    (r"nps.*달성", "account_health", 0.85),
]

ACHIEVED_MARKERS = ["달성", "기록", "감소", "낮췄", "줄", "개선", "상승", "증가", "단축", "완료", "해결", "높이"]


def load_taxonomy(path: str = "data/skill_taxonomy.json") -> dict:
    """skill_key -> {label_ko, keywords[], skill_type} 매핑 로드."""
    with Path(path).open(encoding="utf-8") as file:
        data = json.load(file)
    taxonomy = {}
    for skill in data.get("skills", []):
        key = skill.get("skill_key")
        if key:
            taxonomy[key] = {
                "label_ko": skill.get("label_ko", key),
                "keywords": EXPLICIT_KEYWORDS.get(key, []),
                "skill_type": skill.get("skill_type", ""),
            }
    return taxonomy


def normalize_text(text: str) -> str:
    """소문자 변환, 공백 정리. 원본은 별도 보존."""
    lowered = str(text or "").lower()
    spaced = re.sub(r"[^0-9a-zA-Z가-힣/%]+", " ", lowered)
    return re.sub(r"\s+", " ", spaced).strip()


def find_keyword_matches(text: str, keywords: list[str]) -> list[str]:
    """정규화된 text에서 매칭된 keyword 리스트 반환 (중복 제거, 정렬)."""
    matches = []
    padded_text = f" {text} "
    for keyword in sorted(keywords):
        normalized_keyword = normalize_text(keyword)
        if normalized_keyword and _contains_keyword(padded_text, normalized_keyword):
            if normalized_keyword not in matches:
                matches.append(normalized_keyword)
    return sorted(matches)


def compute_confidence(matched_keywords: list[str], text_length: int) -> float:
    """매칭 keyword 수와 문장 내 밀도 기반 confidence 계산."""
    if not matched_keywords:
        return 0.0
    density = min(CONFIDENCE_DENSITY_CAP, len(matched_keywords) / max(text_length, 1) * 8)
    score = CONFIDENCE_BASE + CONFIDENCE_PER_KEYWORD * len(matched_keywords) + density
    return round(min(1.0, score), 2)


def classify_evidence_type(source: str, matched_keywords: list[str], text: str) -> str:
    """source와 성과 표현을 기준으로 EXPLICIT, INFERRED, ACHIEVED를 분류."""
    normalized = normalize_text(text)
    if source == SOURCE_TARGET:
        return "EXPLICIT" if len(matched_keywords) >= 2 else "INFERRED"
    if matched_keywords and _has_achieved_marker(normalized):
        return "ACHIEVED"
    return "EXPLICIT" if len(matched_keywords) >= 2 else "INFERRED"


def extract_from_career_histories(fixture: dict, taxonomy: dict) -> list[dict]:
    """career_histories[].description 순회하며 evidence 생성."""
    evidences = []
    for history in fixture.get("career_histories", []) or []:
        for text in _history_text_units(history):
            evidences.extend(_extract_from_text(text, SOURCE_CAREER, taxonomy, allow_achieved=True))
    return evidences


def extract_from_target_priority(fixture: dict, taxonomy: dict) -> list[dict]:
    """target_priority_text에서 evidence 생성. ACHIEVED 강제 차단."""
    text = fixture.get("target_priority_text") or ""
    evidences = _extract_from_text(text, SOURCE_TARGET, taxonomy, allow_achieved=False)
    for evidence in evidences:
        if evidence["evidence_type"] == "ACHIEVED":
            evidence["evidence_type"] = "INFERRED"
    return evidences


def extract_evidence(fixture: dict, taxonomy: dict) -> list[dict]:
    """전체 파이프라인. evidence_id는 ev_001부터 순번 부여."""
    candidates = []
    candidates.extend(extract_from_career_histories(fixture, taxonomy))
    candidates.extend(extract_from_target_priority(fixture, taxonomy))
    filtered = [item for item in candidates if item["confidence_score"] >= CONFIDENCE_THRESHOLD]
    if not filtered and candidates:
        filtered = _best_low_confidence_candidates(candidates)
    deduped = _deduplicate_by_skill_source(filtered)
    for index, evidence in enumerate(deduped, start=1):
        evidence["evidence_id"] = f"{EVIDENCE_ID_PREFIX}{index:03d}"
    return [_ordered_evidence(evidence) for evidence in deduped]


def load_sample_inputs(directory: str = "output") -> list[tuple[str, dict]]:
    """sample_input_*.json 전체 로드, 파일명순 정렬."""
    samples = []
    for path in sorted(glob.glob(str(Path(directory) / "sample_input_*.json"))):
        with Path(path).open(encoding="utf-8") as file:
            samples.append((Path(path).name, json.load(file)))
    return samples


def _extract_from_text(text: str, source: str, taxonomy: dict, allow_achieved: bool) -> list[dict]:
    evidences = []
    for sentence in _split_sentences(text):
        normalized = normalize_text(sentence)
        if not normalized:
            continue
        for skill_key, meta in sorted(taxonomy.items()):
            matched = find_keyword_matches(normalized, meta.get("keywords", []))
            inferred_confidence = _inferred_confidence(normalized, skill_key)
            achieved_confidence = _achieved_confidence(normalized, skill_key) if allow_achieved else 0.0
            if not matched and inferred_confidence <= 0.0 and achieved_confidence <= 0.0:
                continue
            keywords = matched or _rule_keywords(normalized, skill_key)
            confidence = max(compute_confidence(keywords, len(normalized)), inferred_confidence, achieved_confidence)
            evidence_type = classify_evidence_type(source, keywords, sentence)
            if achieved_confidence > 0.0 and source == SOURCE_CAREER:
                evidence_type = "ACHIEVED"
            evidences.append(
                {
                    "skill_key": skill_key,
                    "label_ko": meta.get("label_ko", skill_key),
                    "evidence_type": evidence_type,
                    "source": source,
                    "original_text": sentence,
                    "confidence_score": round(confidence, 2),
                    "matched_keywords": sorted(keywords),
                }
            )
    return evidences


def _history_text_units(history: dict) -> list[str]:
    units = []
    for key in ["description", "responsibilities", "achievements"]:
        value = history.get(key)
        if value:
            units.extend(_split_sentences(str(value)))
    return units


def _split_sentences(text: str) -> list[str]:
    if not text:
        return []
    parts = re.split(r"(?<=[.!?。！？습니다다요죠함음됨됨니다])\s+", str(text).strip())
    sentences = []
    for part in parts:
        cleaned = part.strip()
        if cleaned:
            sentences.append(cleaned)
    return sentences


def _contains_keyword(padded_text: str, keyword: str) -> bool:
    if re.fullmatch(r"[a-z0-9/]+", keyword):
        return f" {keyword} " in padded_text
    return keyword in padded_text


def _has_achieved_marker(normalized: str) -> bool:
    for marker in ACHIEVED_MARKERS:
        if normalize_text(marker) in normalized:
            return True
    return False


def _inferred_confidence(normalized: str, skill_key: str) -> float:
    best = 0.0
    for pattern, mapped_skill, confidence in INFERRED_RULES:
        if mapped_skill == skill_key and normalize_text(pattern) in normalized:
            best = max(best, confidence)
    return best


def _achieved_confidence(normalized: str, skill_key: str) -> float:
    best = 0.0
    for pattern, mapped_skill, confidence in ACHIEVED_PATTERNS:
        if mapped_skill == skill_key and re.search(pattern, normalized):
            best = max(best, confidence)
    return best


def _rule_keywords(normalized: str, skill_key: str) -> list[str]:
    keywords = []
    for pattern, mapped_skill, _confidence in INFERRED_RULES:
        normalized_pattern = normalize_text(pattern)
        if mapped_skill == skill_key and normalized_pattern in normalized:
            keywords.append(normalized_pattern)
    for pattern, mapped_skill, _confidence in ACHIEVED_PATTERNS:
        if mapped_skill == skill_key and re.search(pattern, normalized):
            keywords.append(pattern)
    return sorted(keywords)


def _best_low_confidence_candidates(candidates: list[dict]) -> list[dict]:
    ordered = sorted(
        candidates,
        key=lambda item: (-item["confidence_score"], item["skill_key"], item["source"], item["original_text"]),
    )
    fallback = []
    for item in ordered[:LOW_FALLBACK_LIMIT]:
        copied = dict(item)
        copied["evidence_type"] = "INFERRED"
        fallback.append(copied)
    return fallback


def _deduplicate_by_skill_source(evidences: list[dict]) -> list[dict]:
    best_items = []
    best_keys = []
    for evidence in evidences:
        key = (evidence["skill_key"], evidence["source"])
        if key not in best_keys:
            best_keys.append(key)
            best_items.append(evidence)
            continue
        index = best_keys.index(key)
        current = best_items[index]
        if evidence["confidence_score"] > current["confidence_score"]:
            best_items[index] = evidence
    return best_items


def _ordered_evidence(evidence: dict) -> dict:
    return {
        "evidence_id": evidence["evidence_id"],
        "skill_key": evidence["skill_key"],
        "label_ko": evidence["label_ko"],
        "evidence_type": evidence["evidence_type"],
        "source": evidence["source"],
        "original_text": evidence["original_text"],
        "confidence_score": evidence["confidence_score"],
        "matched_keywords": evidence["matched_keywords"],
    }


if __name__ == "__main__":
    loaded_taxonomy = load_taxonomy()
    for filename, sample in load_sample_inputs()[:10]:
        print(filename, len(extract_evidence(sample, loaded_taxonomy)))
