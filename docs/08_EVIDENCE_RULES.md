# 08 — Evidence Rules

사용자 경험 텍스트 → Evidence 변환 규칙.  
**원문은 절대 수정하지 않는다.** (`00_PROJECT_VISION.md` §1 Evidence First)

> **v3 변경:** 입력 소스가 `career_histories`(기존) + `target_priority_text`(신규) 두 곳이 됨.  
> `target_priority_text`에서 추출된 Evidence는 `source="target_priority_text"`,  
> `career_history_id=NULL`로 저장된다 (`03_ERD.md` §2.4).  
> 두 소스에서 추출된 Evidence가 동일 `skill_key`에 매핑되면,  
> `confidence_total`에 합산되어 `06_SCORING_RULES.md` §4의 matchLevel 결정에 사용된다.

---

## 1. Evidence 추출 원칙

1. `original_text`는 사용자가 입력한 문장 그대로 저장 (수정, 요약 금지)
2. 하나의 원문 구간은 여러 `skill_key`로 동시 매핑 가능
3. 모호한 경우 `INFERRED`로 처리하고 `confidence_score`를 낮춘다
4. 추출 불가능한 경우 Evidence를 생성하지 않는다 (빈 배열 반환)
5. `confidence_score < 0.5`인 Evidence는 생성하지 않는다
6. **v3 신규:** `target_priority_text`에서 추출 시 동일 규칙 적용.  
   단, `target_priority_text`는 "미래 지향적 의도" 텍스트이므로 ACHIEVED 타입은 나오지 않으며  
   EXPLICIT/INFERRED만 추출된다. confidence 범위도 동일.

---

## 2. evidence_type 정의

| type | confidence 범위 | 판단 기준 |
|------|-----------------|----------|
| `EXPLICIT` | 1.0 | 스킬명 또는 명확한 업무명이 직접 언급됨 |
| `INFERRED` | 0.5–0.8 | 업무 맥락에서 스킬이 합리적으로 추론됨 |
| `ACHIEVED` | 0.7–0.9 | 성과/결과 기술에서 스킬이 역산됨 (`career_histories`에서만 발생) |

---

## 3. EXPLICIT 매핑 (직접 언급)

### 3.1 공통 스킬 (COMMON Pool)

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
| "근로기준법", "노동법", "노사 관계", "근로계약" | labor_law |
| "급여", "연봉", "복리후생", "4대보험", "인건비" | payroll |
| "성과 평가", "KPI", "MBO", "인사 평가" | performance_management |
| "고충 처리", "조직문화", "이직률 관리" | employee_relations |
| "취업규칙", "인사규정", "HR 정책" | hr_policy |
| "HRIS", "인사 시스템 운영" | hris |

**target_priority_text EXPLICIT 예시:**
```
"1순위: 인사관리(인력운영/평가, 급여)" → performance_management, payroll
"2순위: 인재개발(기업교육, 채용)" → training_and_onboarding, recruiting
"노동법 및 근로기준법과 관련하여 공부하고" → labor_law
"급여 관련 업무에 가장 큰 흥미를 느낌" → payroll
```

### 3.3 Marketing

| 입력 키워드/문구 | skill_key |
|-----------------|-----------|
| "캠페인", "마케팅 캠페인 기획" | campaign_management |
| "SEO", "SEM", "검색광고", "키워드 광고" | seo_sem |
| "블로그 작성", "콘텐츠 제작", "카피라이팅" | content_marketing |
| "브랜드 가이드", "브랜드 아이덴티티" | brand_management |
| "SNS 운영", "소셜미디어 채널 관리" | social_media |
| "GA", "전환율 분석", "ROAS", "퍼포먼스 마케팅" | marketing_analytics |

### 3.4 Data

| 입력 키워드/문구 | skill_key |
|-----------------|-----------|
| "SQL", "쿼리", "데이터베이스" | sql |
| "Python", "파이썬", "판다스", "pandas" | python |
| "대시보드", "시각화", "Tableau", "Power BI", "루커" | data_visualization |
| "통계", "회귀분석", "가설 검정", "유의성" | statistics |
| "ETL", "데이터 파이프라인", "Airflow" | data_pipeline |
| "A/B 테스트", "실험 설계", "AB 테스트" | ab_testing |

### 3.5 Product

| 입력 키워드/문구 | skill_key |
|-----------------|-----------|
| "PRD", "제품 기획", "요구사항 정의", "기능 기획" | product_planning |
| "로드맵", "우선순위 설정", "백로그 관리" | roadmap_management |
| "사용자 인터뷰", "FGI", "사용성 테스트", "UX 리서치" | user_research |
| "와이어프레임", "UX 설계", "IA", "정보구조" | ux_sense |
| "스프린트", "스크럼", "애자일", "칸반" | sprint_management |
| "경쟁사 분석", "시장 분석", "벤치마킹" | competitive_analysis |

### 3.6 Operations

| 입력 키워드/문구 | skill_key |
|-----------------|-----------|
| "프로세스 개선", "효율화", "자동화", "표준화" | process_improvement |
| "벤더", "공급업체", "외주 계약", "협력사 관리" | vendor_management |
| "운영 관리", "오퍼레이션 총괄", "시설 관리" | operations_management |
| "물류", "재고 관리", "공급망", "창고 관리" | logistics |
| "품질 관리 체계", "ISO", "품질 기준" | quality_management |
| "비용 절감", "원가 관리", "비용 최적화" | cost_management |

### 3.7 Sales

| 입력 키워드/문구 | skill_key |
|-----------------|-----------|
| "리드 발굴", "신규 영업", "콜드 콜", "아웃바운드" | lead_generation |
| "계정 관리", "기존 고객 관리", "어카운트 관리" | account_management |
| "계약 협상", "딜 클로징", "조건 협상" | negotiation |
| "CRM", "세일즈포스", "Salesforce", "허브스팟", "HubSpot" | crm_management |
| "매출 예측", "수요 예측", "파이프라인 예측" | forecasting |
| "영업 파이프라인", "딜 단계 관리", "세일즈 파이프라인" | pipeline_management |

### 3.8 Design

| 입력 키워드/문구 | skill_key |
|-----------------|-----------|
| "UI 디자인", "인터페이스 디자인", "시각 디자인" | ui_design |
| "프로토타입", "Figma", "인터랙션 디자인", "피그마" | prototyping |
| "디자인 시스템", "컴포넌트 라이브러리", "디자인 가이드" | design_systems |
| "와이어프레임", "스케치", "목업" | wireframing |
| "접근성", "웹 접근성 표준", "WCAG" | accessibility |
| "사용자 리서치", "UI 리서치" | user_research |

### 3.9 Finance

| 입력 키워드/문구 | skill_key |
|-----------------|-----------|
| "재무 모델", "재무 모델링", "DCF", "밸류에이션" | financial_modeling |
| "예산 수립", "연간 예산 계획", "예산안 작성" | budgeting_advanced |
| "회계", "재무제표", "전표 처리", "결산" | accounting |
| "재무 보고", "투자자 리포트", "IR 자료" | financial_reporting |
| "세무", "세금 신고", "세무 신고" | tax_compliance |

### 3.10 Engineering

| 입력 키워드/문구 | skill_key |
|-----------------|-----------|
| "개발", "기능 구현", "프로그래밍", "코딩" | software_development |
| "코드 리뷰", "PR 리뷰", "코드 검토" | code_review |
| "시스템 설계", "아키텍처 설계", "인프라 설계" | system_design |
| "디버깅", "버그 수정", "트러블슈팅" | debugging |
| "API 설계", "REST API", "OpenAPI" | api_design |
| "테스트 코드", "QA", "단위 테스트", "E2E 테스트" | testing_qa |

### 3.11 Customer Success

| 입력 키워드/문구 | skill_key |
|-----------------|-----------|
| "고객 온보딩", "도입 지원", "고객 입문 교육" | customer_onboarding |
| "이탈 방지", "churn 관리", "이탈률 감소" | churn_management |
| "CS 티켓", "고객 문의 응대", "헬프데스크" | support_ticketing |
| "계정 헬스", "사용률 모니터링", "고객 건강도" | account_health |
| "VOC", "고객 피드백 분석", "NPS 분석" | customer_feedback_analysis |
| "계약 갱신", "리뉴얼", "연장 계약" | renewal_management |

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
| "신규 입사자 서류 처리" | hris | 0.6 |
| "사내 행사 일정 조율" | coordination | 0.8 |
| "고객 관계 유지" | account_management | 0.7 |
| "디자인 가이드 준수" | design_systems | 0.6 |
| "버그 리포트 작성" | debugging | 0.6 |
| "계약서 검토" | negotiation_basic | 0.65 |
| "HRM 관련 경력", "인사 직무 경력" | performance_management, payroll | 0.7 |
| "HRD 업무", "인재개발" | training_and_onboarding | 0.75 |

**target_priority_text INFERRED 예시:**
```
"HR 분야에 더 적합하다고 판단" → performance_management(0.6), communication(0.6)
"성취 중심의 직업적 가치관" → leadership(0.5)
"데이터 작업에 가장 큰 흥미" → data_analysis(0.7)
```

---

## 5. ACHIEVED 매핑 (성과 역산, career_histories 전용)

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
| "온보딩 만족도 X점 달성" | training_and_onboarding | 0.9 |

---

## 6. 추출 알고리즘 (의사코드)

```python
def extract_evidences_from_all_sources(
    career_histories: list[CareerHistory],
    target_priority_text: str
) -> list[Evidence]:
    """
    v3: 두 소스에서 모두 추출. 동일 skill_key에 매핑된 Evidence들은
    confidence_total로 합산되어 06_SCORING_RULES.md §4에서 matchLevel 결정에 사용.
    """
    evidences = []

    # 소스 1: career_histories (기존)
    for ch in career_histories:
        evidences.extend(extract_evidences_from_text(
            text=ch.responsibilities + " " + (ch.achievements or ""),
            career_history_id=ch.id,
            source="career_history"
        ))

    # 소스 2: target_priority_text (v3 신규)
    # ACHIEVED 타입 제외 (미래 지향 텍스트에서 성과 역산은 무의미)
    tpt_evidences = extract_evidences_from_text(
        text=target_priority_text,
        career_history_id=None,
        source="target_priority_text",
        exclude_types=["ACHIEVED"]
    )
    evidences.extend(tpt_evidences)

    # confidence_score < 0.5 필터링
    evidences = [e for e in evidences if e.confidence_score >= 0.5]

    return deduplicate(evidences)


def extract_evidences_from_text(text, career_history_id, source, exclude_types=None):
    evidences = []
    exclude_types = exclude_types or []

    # EXPLICIT 추출
    if "EXPLICIT" not in exclude_types:
        for keyword, skill_key in EXPLICIT_RULES.items():
            if keyword in text:
                sentence = extract_sentence(text, keyword)
                evidences.append(Evidence(
                    skill_key=skill_key, original_text=sentence,
                    evidence_type="EXPLICIT", confidence_score=1.0,
                    career_history_id=career_history_id, source=source
                ))

    # INFERRED 추출
    if "INFERRED" not in exclude_types:
        covered = {e.skill_key for e in evidences}
        for pattern, skill_key, confidence in INFERRED_RULES:
            if skill_key not in covered and pattern in text:
                evidences.append(Evidence(
                    skill_key=skill_key, original_text=extract_sentence(text, pattern),
                    evidence_type="INFERRED", confidence_score=confidence,
                    career_history_id=career_history_id, source=source
                ))

    # ACHIEVED 추출 (career_history 소스에서만)
    if "ACHIEVED" not in exclude_types and source == "career_history":
        for pattern, skill_key, confidence in ACHIEVED_RULES:
            if re.search(pattern, text):
                evidences.append(Evidence(
                    skill_key=skill_key, original_text=extract_sentence(text, pattern),
                    evidence_type="ACHIEVED", confidence_score=confidence,
                    career_history_id=career_history_id, source=source
                ))

    return evidences


def deduplicate(evidences: list[Evidence]) -> list[Evidence]:
    """
    동일 (skill_key, original_text, evidence_type) 조합 중복 제거.
    같은 skill_key에 서로 다른 evidence_type은 모두 보존
    (06_SCORING_RULES.md §4 confidence_total 합산을 위해).
    서로 다른 source에서 같은 (skill_key, original_text, evidence_type)이 나오는 것도
    중복으로 간주하여 제거 (동일 텍스트를 양쪽에 적었을 가능성 방어).
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
3. **동일 skill_key에 서로 다른 evidence_type은 모두 보존** — `confidence_total` 합산의 입력값.
4. `confidence_score < 0.5`인 Evidence는 생성하지 않는다.
5. Evidence가 0개인 requirement는 `match_level = NONE`, `confidence_total = 0.0`.
6. 새 skill_key를 매핑에 추가하기 전, `07_SKILL_TAXONOMY.md`에 먼저 등록.
7. **v3 신규:** `target_priority_text`에서 ACHIEVED 타입 추출 금지.
8. **v3 신규:** `target_priority_text` 유래 Evidence는 `career_history_id=NULL`, `source="target_priority_text"` 필수.

---

## 8. 알려진 문제점 (§ Limitations)

| 문제 | 영향 | 비고 |
|------|------|------|
| EXPLICIT 매핑이 단순 문자열 포함 검사 → 맥락 무시 | "채용 대행사에 업무 위탁" 문장에서도 "채용"이 감지되어 `recruiting` Evidence 생성 가능 | 현재 허용 — confidence_score=1.0이지만 문장 전체가 `original_text`로 저장되므로 리뷰어가 확인 가능 |
| `target_priority_text`의 INFERRED 추출이 과도하게 많을 수 있음 | "HR 분야에 더 적합하다고 판단" 한 문장에서 여러 skill_key가 낮은 confidence로 추출될 수 있음 → user_vector가 artificially dense해질 위험 | INFERRED confidence 범위(0.5~0.8)가 낮게 설정되어 있어 matchLevel에 미치는 영향 제한적 |
| 동의어/방언/신조어 처리 없음 | "AI 모델 파인튜닝" → `python` 또는 `software_development` 미추출 | `08_EVIDENCE_RULES.md`를 living document로 관리하여 점진적 추가 |
| `target_priority_text`에서 같은 스킬이 `career_histories`에서도 추출되면 confidence_total이 높아짐 | 의도한 스킬에 대한 매칭 강화 — 이는 **의도된 설계** ("목표에 경험이 부합할수록 높은 점수") | 단, 사용자가 `target_priority_text`에 과도한 스킬 어필을 나열하면 실제 경험 없이도 score가 올라가는 부작용 가능 |