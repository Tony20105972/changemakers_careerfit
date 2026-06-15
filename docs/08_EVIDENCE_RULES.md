# 08 — Evidence Rules

사용자 경험 텍스트 → Evidence 변환 규칙.  
**원문은 절대 수정하지 않는다.** (`00_PROJECT_VISION.md` §1 Evidence First)

> v2 변경: `07_SKILL_TAXONOMY.md`의 ~79개 스킬 전체를 커버하도록 매핑 확장.  
> `confidence_score`는 `06_SCORING_RULES.md` §4의 `confidence_total` 합산 알고리즘 입력값이다.

---

## 1. Evidence 추출 원칙

1. `original_text`는 사용자가 입력한 문장 그대로 저장 (수정, 요약 금지)
2. 하나의 원문 구간은 여러 `skill_key`로 동시 매핑 가능
3. 모호한 경우 `INFERRED`로 처리하고 `confidence_score`를 낮춘다
4. 추출 불가능한 경우 Evidence를 생성하지 않는다 (빈 배열 반환)
5. `confidence_score < 0.5`인 Evidence는 생성하지 않는다 (06_SCORING_RULES.md §10 불변규칙 9)

---

## 2. evidence_type 정의

| type | confidence 범위 | 판단 기준 |
|------|-----------|----------|
| `EXPLICIT` | 1.0 | 스킬명 또는 명확한 업무명이 직접 언급됨 |
| `INFERRED` | 0.5–0.8 | 업무 맥락에서 스킬이 합리적으로 추론됨 |
| `ACHIEVED` | 0.7–0.9 | 성과/결과 기술에서 스킬이 역산됨 |

---

## 3. EXPLICIT 매핑 (직접 언급)

### 3.1 공통 스킬 (COMMON Pool, 07_SKILL_TAXONOMY.md §1)

| 입력 키워드/문구 | skill_key |
|-----------------|-----------|
| "보고서 작성", "문서화", "매뉴얼", "기획서 작성" | documentation |
| "발표", "PT", "프레젠테이션" | presentation |
| "일정 조율", "미팅 조율", "스케줄 관리" | coordination |
| "팀 리드", "팀장", "조직 관리" | leadership |
| "멘토링", "코칭", "OJT 지도" | mentoring |
| "엑셀", "스프레드시트", "피벗테이블" | excel |
| "정기 보고", "주간 보고", "경영진 보고" | reporting |
| "예산 편성", "예산 관리" | budgeting |
| "프로세스 설계", "업무 표준화" | process_design |
| "사내 교육", "교육 프로그램 기획" | training |
| "협상", "조건 조율" | negotiation_basic |
| "협력사 소통", "벤더 커뮤니케이션" | vendor_coordination |
| "품질 검토", "QC", "검수" | quality_control |
| "신규 툴 도입", "시스템 전환" | tooling_adoption |
| "타 부서 협업", "크로스펑셔널" | crossfunctional_collab |
| "이해관계자 관리", "스테이크홀더" | stakeholder_management |
| "데이터 취합", "데이터 정리 및 분석" | data_analysis |
| "프로젝트 관리", "PM", "일정/리소스 관리" | project_management |
| "문제 해결", "이슈 해결" | problem_solving |
| "커뮤니케이션", "소통" | communication |

### 3.2 HR

| 입력 키워드/문구 | skill_key |
|-----------------|-----------|
| "채용", "공고 작성", "JD 작성", "서류 전형", "면접" | recruiting |
| "온보딩", "입문 교육", "OJT", "신입 교육" | training_and_onboarding |
| "근로기준법", "노동법", "노사 관계" | labor_law |
| "급여", "연봉", "복리후생", "4대보험" | payroll |
| "성과 평가", "KPI", "MBO", "인사 평가" | performance_management |
| "고충 처리", "조직문화", "이직률 관리" | employee_relations |
| "취업규칙", "인사규정", "HR 정책" | hr_policy |
| "HRIS", "인사 시스템 운영" | hris |

### 3.3 Marketing

| 입력 키워드/문구 | skill_key |
|-----------------|-----------|
| "캠페인", "마케팅 캠페인 기획" | campaign_management |
| "SEO", "SEM", "검색광고" | seo_sem |
| "블로그 작성", "콘텐츠 제작", "카피라이팅" | content_marketing |
| "브랜드 가이드", "브랜드 아이덴티티" | brand_management |
| "SNS 운영", "소셜미디어 채널 관리" | social_media |
| "GA", "전환율 분석", "ROAS" | marketing_analytics |

### 3.4 Data

| 입력 키워드/문구 | skill_key |
|-----------------|-----------|
| "SQL", "쿼리", "데이터베이스" | sql |
| "Python", "파이썬" | python |
| "대시보드", "시각화", "Tableau", "Power BI" | data_visualization |
| "통계", "회귀분석", "가설 검정" | statistics |
| "ETL", "데이터 파이프라인" | data_pipeline |
| "A/B 테스트", "실험 설계" | ab_testing |

### 3.5 Product

| 입력 키워드/문구 | skill_key |
|-----------------|-----------|
| "PRD", "제품 기획", "요구사항 정의" | product_planning |
| "로드맵", "우선순위 설정" | roadmap_management |
| "사용자 인터뷰", "FGI", "사용성 테스트" | user_research |
| "와이어프레임", "UX 설계" | ux_sense |
| "스프린트", "스크럼", "애자일" | sprint_management |
| "경쟁사 분석", "시장 분석" | competitive_analysis |

### 3.6 Operations

| 입력 키워드/문구 | skill_key |
|-----------------|-----------|
| "프로세스 개선", "효율화", "자동화" | process_improvement |
| "벤더", "공급업체", "외주 계약" | vendor_management |
| "운영 관리", "오퍼레이션 총괄" | operations_management |
| "물류", "재고 관리", "공급망" | logistics |
| "품질 관리 체계", "ISO" | quality_management |
| "비용 절감", "원가 관리" | cost_management |

### 3.7 Sales

| 입력 키워드/문구 | skill_key |
|-----------------|-----------|
| "리드 발굴", "신규 영업", "콜드 콜" | lead_generation |
| "계정 관리", "기존 고객 관리" | account_management |
| "계약 협상", "딜 클로징" | negotiation |
| "CRM", "세일즈포스", "허브스팟" | crm_management |
| "매출 예측", "수요 예측" | forecasting |
| "영업 파이프라인", "딜 단계 관리" | pipeline_management |

### 3.8 Design

| 입력 키워드/문구 | skill_key |
|-----------------|-----------|
| "UI 디자인", "인터페이스 디자인" | ui_design |
| "프로토타입", "Figma", "인터랙션 디자인" | prototyping |
| "디자인 시스템", "컴포넌트 라이브러리" | design_systems |
| "와이어프레임" | wireframing |
| "접근성", "웹 접근성 표준" | accessibility |

### 3.9 Finance

| 입력 키워드/문구 | skill_key |
|-----------------|-----------|
| "재무 모델", "재무 모델링" | financial_modeling |
| "예산 수립", "연간 예산 계획" | budgeting_advanced |
| "회계", "재무제표", "전표 처리" | accounting |
| "재무 보고", "투자자 리포트" | financial_reporting |
| "세무", "세금 신고" | tax_compliance |

### 3.10 Engineering

| 입력 키워드/문구 | skill_key |
|-----------------|-----------|
| "개발", "기능 구현", "프로그래밍" | software_development |
| "코드 리뷰", "PR 리뷰" | code_review |
| "시스템 설계", "아키텍처 설계" | system_design |
| "디버깅", "버그 수정" | debugging |
| "API 설계", "REST API" | api_design |
| "테스트 코드", "QA", "단위 테스트" | testing_qa |

### 3.11 Customer Success

| 입력 키워드/문구 | skill_key |
|-----------------|-----------|
| "고객 온보딩", "도입 지원" | customer_onboarding |
| "이탈 방지", "churn 관리" | churn_management |
| "CS 티켓", "고객 문의 응대" | support_ticketing |
| "계정 헬스", "사용률 모니터링" | account_health |
| "VOC", "고객 피드백 분석" | customer_feedback_analysis |
| "계약 갱신", "리뉴얼" | renewal_management |

---

## 4. INFERRED 매핑 (맥락 추론)

| 입력 문구 | 추론 skill_key | confidence |
|-----------|---------------|-----------|
| "후보자 관리" | recruiting | 0.8 |
| "신입사원 적응 지원" | training_and_onboarding | 0.75 |
| "팀원 피드백" | performance_management | 0.6 |
| "데이터 취합 및 정리" | data_analysis | 0.7 |
| "엑셀로 집계" | excel | 0.8 |
| "여러 부서와 협업" | crossfunctional_collab | 0.7 |
| "팀 리드", "팀장 역할" | leadership | 0.85 |
| "블로그 작성", "SNS 운영" (단독) | content_marketing | 0.7 |
| "고객 응대", "CS" | support_ticketing | 0.6 |
| "예산 관리", "비용 절감" (단독) | cost_management | 0.7 |
| "재고 관리", "입출고" | logistics | 0.8 |
| "사용자 인터뷰", "FGI" (단독) | user_research | 0.7 |
| "신규 입사자 서류 처리", "사내 시스템 등록" | hris | 0.6 |
| "사내 행사 일정 조율" | coordination | 0.8 |
| "고객 관계 유지" | account_management | 0.7 |
| "디자인 가이드 준수" | design_systems | 0.6 |
| "정기 미팅 진행" | coordination | 0.7 |
| "코드 작성 보조" | software_development | 0.6 |
| "버그 리포트 작성" | debugging | 0.6 |
| "계약서 검토" | negotiation_basic | 0.65 |

---

## 5. ACHIEVED 매핑 (성과 역산)

| 성과 기술 패턴 | 역산 skill_key | confidence |
|---------------|---------------|-----------|
| "채용 목표 X% 달성" | recruiting | 0.9 |
| "만족도 X점 달성 (온보딩)" | training_and_onboarding | 0.85 |
| "이직률 X% 감소" | employee_relations | 0.8 |
| "급여 정산 오류율 X%" | payroll | 0.9 |
| "프로세스 X% 단축" | process_improvement | 0.9 |
| "비용 X% 절감" | cost_management | 0.85 |
| "전환율 X% 향상" | marketing_analytics | 0.85 |
| "MAU X명 달성", "트래픽 X% 증가" | content_marketing | 0.8 |
| "쿼리 성능 X% 개선" | sql | 0.85 |
| "매출 X% 증가" (Sales 맥락) | account_management | 0.85 |
| "계약 갱신율 X%" | renewal_management | 0.85 |
| "디자인 작업 시간 X% 단축" | design_systems | 0.8 |
| "장애 X건 해결", "버그 X% 감소" | debugging | 0.85 |
| "예산 X% 절감" | budgeting_advanced | 0.85 |
| "NPS X점 달성" | account_health | 0.85 |

---

## 6. 추출 알고리즘 (의사코드)

```python
def extract_evidences(career_history: CareerHistory) -> list[Evidence]:
    evidences = []
    resp_text = career_history.responsibilities
    achv_text = career_history.achievements or ""

    # Step 1: EXPLICIT 추출 (responsibilities + achievements 모두 대상)
    full_text = resp_text + " " + achv_text
    for keyword, skill_key in EXPLICIT_RULES.items():
        if keyword in full_text:
            sentence = extract_sentence(full_text, keyword)
            evidences.append(Evidence(
                skill_key=skill_key,
                original_text=sentence,
                evidence_type="EXPLICIT",
                confidence_score=1.0
            ))

    # Step 2: INFERRED 추출 (EXPLICIT로 이미 커버된 skill_key는 스킵)
    covered = {e.skill_key for e in evidences}
    for pattern, skill_key, confidence in INFERRED_RULES:
        if skill_key not in covered and pattern in full_text:
            sentence = extract_sentence(full_text, pattern)
            evidences.append(Evidence(
                skill_key=skill_key,
                original_text=sentence,
                evidence_type="INFERRED",
                confidence_score=confidence
            ))

    # Step 3: ACHIEVED 추출 (achievements 필드 전용)
    if achv_text:
        for pattern, skill_key, confidence in ACHIEVED_RULES:
            if re.search(pattern, achv_text):
                sentence = extract_sentence(achv_text, pattern)
                evidences.append(Evidence(
                    skill_key=skill_key,
                    original_text=sentence,
                    evidence_type="ACHIEVED",
                    confidence_score=confidence
                ))

    # Step 4: confidence_score < 0.5 필터링
    evidences = [e for e in evidences if e.confidence_score >= 0.5]

    return deduplicate(evidences)


def deduplicate(evidences: list[Evidence]) -> list[Evidence]:
    """
    동일 (skill_key, original_text, evidence_type) 조합 중복 제거.
    단, 같은 skill_key에 서로 다른 evidence_type(EXPLICIT + ACHIEVED 등)이
    존재하는 것은 중복이 아니다 — 06_SCORING_RULES.md §4의 confidence_total
    합산을 위해 모두 보존한다.
    """
    seen = set()
    result = []
    for e in evidences:
        key = (e.skill_key, e.original_text, e.evidence_type)
        if key not in seen:
            seen.add(key)
            result.append(e)
    return result
```

---

## 7. 불변 규칙

1. `original_text`는 사용자 입력 원문의 **문장 단위**로 추출. 임의로 수정/요약 금지.
2. 동일 `(skill_key, original_text, evidence_type)` 조합 중복 제거.
3. **동일 skill_key에 서로 다른 evidence_type은 모두 보존** — `confidence_total` 합산의 입력값이 된다 (06_SCORING_RULES.md §4).
4. `confidence_score < 0.5`인 Evidence는 생성하지 않는다.
5. Evidence가 0개인 requirement는 `match_level = NONE`, `confidence_total = 0.0`으로 처리.
6. 새 skill_key를 매핑에 추가하기 전, `07_SKILL_TAXONOMY.md`에 먼저 등록되어 있는지 확인한다.