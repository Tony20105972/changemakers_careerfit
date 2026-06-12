# 06 — Scoring Rules

점수 계산은 **완전 결정론적**이다.  
동일한 입력 → 동일한 점수. LLM 개입 없음.

---

## 1. 기본 공식

```
total_score = Σ (requirement_weight × match_score × 100)
```

- 각 `requirement_weight`의 합 = 1.0
- `match_score` 범위: 0.0 – 1.0
- 최종 점수 범위: 0 – 100점

---

## 2. matchLevel 정의

| matchLevel | match_score | 판단 기준 |
|------------|-------------|----------|
| `FULL` | 1.00 | 해당 역량을 직접 수행한 명확한 Evidence가 2개 이상 |
| `STRONG` | 0.75 | 직접 수행 Evidence 1개 + 관련 맥락 |
| `PARTIAL` | 0.50 | 간접적 수행 또는 보조적 역할로 Evidence 존재 |
| `WEAK` | 0.25 | 관련성 있는 키워드 언급, 직접 수행 증거 없음 |
| `NONE` | 0.00 | Evidence 없음 |

---

## 3. matchLevel 결정 알고리즘

```python
def determine_match_level(evidences: list[Evidence], requirement_key: str) -> MatchLevel:
    relevant = [e for e in evidences if e.skill_key == requirement_key]
    
    if not relevant:
        return MatchLevel.NONE
    
    explicit_count = sum(1 for e in relevant if e.evidence_type == "EXPLICIT")
    inferred_count = sum(1 for e in relevant if e.evidence_type == "INFERRED")
    achieved_count = sum(1 for e in relevant if e.evidence_type == "ACHIEVED")
    
    total_confidence = sum(e.confidence_score for e in relevant)
    
    if explicit_count >= 2 or (explicit_count >= 1 and total_confidence >= 1.8):
        return MatchLevel.FULL
    elif explicit_count >= 1 or (inferred_count >= 1 and achieved_count >= 1):
        return MatchLevel.STRONG
    elif inferred_count >= 2 or (inferred_count >= 1 and total_confidence >= 0.7):
        return MatchLevel.PARTIAL
    elif inferred_count >= 1 or achieved_count >= 1:
        return MatchLevel.WEAK
    else:
        return MatchLevel.NONE
```

---

## 4. 점수 계산 예시 (HR, 총점 78.5)

| requirement_key | weight | match_level | match_score | weighted_score |
|-----------------|--------|-------------|-------------|----------------|
| recruiting | 0.20 | FULL | 1.00 | 20.0 |
| training_and_onboarding | 0.15 | STRONG | 0.75 | 11.25 |
| performance_management | 0.15 | PARTIAL | 0.50 | 7.5 |
| hr_policy | 0.12 | STRONG | 0.75 | 9.0 |
| payroll | 0.10 | WEAK | 0.25 | 2.5 |
| labor_law | 0.10 | NONE | 0.00 | 0.0 |
| stakeholder_management | 0.08 | FULL | 1.00 | 8.0 |
| documentation | 0.05 | FULL | 1.00 | 5.0 |
| data_analysis | 0.05 | PARTIAL | 0.50 | 2.5 |
| **합계** | **1.00** | | | **65.75** |

> 위 예시의 합계는 65.75이며, 실제 점수는 입력 데이터에 따라 다름.

---

## 5. 등급 레이블

| 점수 범위 | fit_level | 한국어 레이블 |
|-----------|-----------|--------------|
| 90–100 | EXCELLENT_FIT | 최우수 |
| 75–89 | GOOD_FIT | 우수 |
| 55–74 | MODERATE_FIT | 보통 |
| 0–54 | LOW_FIT | 미흡 |

---

## 6. 핵심 요구사항(is_core) 페널티

`is_core = TRUE`인 요구사항이 `NONE` 또는 `WEAK`이면 총점에서 페널티를 적용한다.

```python
CORE_PENALTY_NONE = -5.0   # is_core + NONE
CORE_PENALTY_WEAK = -2.5   # is_core + WEAK

def apply_core_penalty(raw_score: float, matches: list[RequirementMatch], requirements: list[Requirement]) -> float:
    penalty = 0.0
    for req in requirements:
        if req.is_core:
            match = next(m for m in matches if m.requirement_key == req.requirement_key)
            if match.match_level == MatchLevel.NONE:
                penalty += CORE_PENALTY_NONE
            elif match.match_level == MatchLevel.WEAK:
                penalty += CORE_PENALTY_WEAK
    return max(0.0, raw_score + penalty)
```

---

## 7. 불변 규칙

1. 점수는 항상 0–100 범위. 음수 불가.
2. 동일 입력 → 동일 점수 (결정론적 보장).
3. LLM은 점수 계산에 개입하지 않는다.
4. `original_text`가 없는 Evidence는 점수에 반영하지 않는다.
# 07 — Skill Taxonomy

CareerFit에서 사용하는 범용 스킬 사전.  
`skill_key`는 시스템 전체에서 일관되게 사용되는 식별자다.

---

## 공통 역량 (Cross-functional)

| skill_key | label_ko | 설명 |
|-----------|----------|------|
| communication | 커뮤니케이션 | 내외부 이해관계자와의 효과적 소통 |
| stakeholder_management | 이해관계자 관리 | 다양한 이해관계자 조율 및 관계 관리 |
| documentation | 문서화 | 보고서, 기획서, 매뉴얼 등 문서 작성 |
| project_management | 프로젝트 관리 | 일정, 리소스, 리스크 관리 |
| data_analysis | 데이터 분석 | 데이터 수집, 정리, 인사이트 도출 |
| presentation | 발표/프레젠테이션 | 데이터와 아이디어를 청중에게 전달 |
| problem_solving | 문제 해결 | 문제 정의 → 원인 분석 → 해결책 도출 |
| coordination | 일정/업무 조율 | 여러 팀/부서 간 업무 조율 |
| leadership | 리더십 | 팀 또는 프로젝트 리드 경험 |
| mentoring | 멘토링 | 후배/팀원 성장 지원 |

---

## HR 특화 역량

| skill_key | label_ko | 설명 |
|-----------|----------|------|
| recruiting | 채용 관리 | JD 작성, 서류 검토, 면접 진행 등 채용 전 과정 |
| training_and_onboarding | 교육/온보딩 | 신입·경력 교육 프로그램 설계 및 운영 |
| performance_management | 성과 관리 | KPI 설정, 평가 프로세스 운영 |
| payroll | 급여/복리후생 | 급여 계산, 복리후생 설계 및 관리 |
| hr_policy | HR 정책 수립 | 취업규칙, 인사규정 등 정책 수립 |
| labor_law | 노동법 | 근로기준법, 노동관계법령 이해 및 적용 |
| employee_relations | 직원 관계 관리 | 직원 고충 처리, 조직문화 관리 |
| hris | HRIS 운영 | HR 정보 시스템 관리 및 데이터 유지 |

---

## Marketing 특화 역량

| skill_key | label_ko | 설명 |
|-----------|----------|------|
| marketing_content | 마케팅 콘텐츠 | 블로그, SNS, 광고 카피 등 콘텐츠 제작 |
| campaign_management | 캠페인 관리 | 마케팅 캠페인 기획, 실행, 성과 분석 |
| seo_sem | SEO/SEM | 검색 최적화 및 검색광고 운영 |
| brand_management | 브랜드 관리 | 브랜드 아이덴티티 관리 및 가이드라인 수립 |
| copywriting | 카피라이팅 | 설득력 있는 마케팅 문구 작성 |
| social_media | 소셜 미디어 | SNS 채널 운영 및 커뮤니티 관리 |
| growth_hacking | 그로스 해킹 | 데이터 기반 퍼포먼스 마케팅 |
| marketing_analytics | 마케팅 분석 | GA, 전환율, ROAS 등 마케팅 지표 분석 |

---

## Data 특화 역량

| skill_key | label_ko | 설명 |
|-----------|----------|------|
| sql | SQL | 데이터베이스 쿼리 작성 및 분석 |
| python | Python | 데이터 처리 및 분석을 위한 Python 활용 |
| data_visualization | 데이터 시각화 | 대시보드, 차트 등 시각화 도구 활용 |
| statistics | 통계 | 기초 통계, 가설 검정, 회귀 분석 |
| ml_fundamentals | ML 기초 | 머신러닝 모델 이해 및 적용 |
| data_pipeline | 데이터 파이프라인 | ETL 설계 및 데이터 처리 자동화 |
| excel | Excel/스프레드시트 | 피벗, 수식, 매크로 등 고급 활용 |
| ab_testing | A/B 테스트 | 실험 설계 및 통계적 유의성 검증 |

---

## Product 특화 역량

| skill_key | label_ko | 설명 |
|-----------|----------|------|
| product_planning | 제품 기획 | 제품 요구사항 정의, PRD 작성 |
| user_research | 사용자 리서치 | 인터뷰, 설문, 사용성 테스트 |
| roadmap_management | 로드맵 관리 | 제품 로드맵 수립 및 우선순위 결정 |
| ux_sense | UX 감각 | 사용자 경험 설계 및 와이어프레임 |
| sprint_management | 스프린트 관리 | 애자일/스크럼 운영 경험 |
| metric_definition | 지표 정의 | 제품 KPI 설정 및 측정 |
| competitive_analysis | 경쟁사 분석 | 시장 및 경쟁 제품 분석 |

---

## Operations 특화 역량

| skill_key | label_ko | 설명 |
|-----------|----------|------|
| process_improvement | 프로세스 개선 | 업무 효율화, 표준화, 자동화 |
| operations_management | 운영 관리 | 일상 운영 프로세스 총괄 |
| vendor_management | 벤더 관리 | 외주/공급업체 선정, 계약, 관계 관리 |
| quality_management | 품질 관리 | 품질 기준 설정 및 모니터링 |
| cost_management | 비용 관리 | 예산 편성 및 비용 최적화 |
| logistics | 물류/공급망 | 물류, 재고, 공급망 관리 |
| customer_success | 고객 성공 관리 | 고객 온보딩, 유지, 만족도 관리 |

---

## 추가 규칙

1. `skill_key`는 snake_case, 소문자만 사용
2. 새 스킬 추가 시 이 문서에 먼저 등록 후 사용
3. `job_requirement_stats`의 `requirement_key`는 반드시 이 목록의 `skill_key`여야 함
4. 하나의 Evidence는 여러 `skill_key`에 동시 매핑 가능
# 08 — Evidence Rules

사용자 경험 텍스트 → Evidence 변환 규칙.  
**원문은 절대 수정하지 않는다.**

---

## 1. Evidence 추출 원칙

1. `original_text`는 사용자가 입력한 문장 그대로 저장 (수정, 요약 금지)
2. 하나의 원문 구간은 여러 `skill_key`로 동시 매핑 가능
3. 모호한 경우 `INFERRED`로 처리하고 `confidence_score`를 낮춘다
4. 추출 불가능한 경우 Evidence를 생성하지 않는다 (빈 배열 반환)

---

## 2. evidence_type 정의

| type | confidence | 판단 기준 |
|------|-----------|----------|
| `EXPLICIT` | 1.0 | 스킬명 또는 명확한 업무명이 직접 언급됨 |
| `INFERRED` | 0.5–0.8 | 업무 맥락에서 스킬이 합리적으로 추론됨 |
| `ACHIEVED` | 0.7–0.9 | 성과/결과 기술에서 스킬이 역산됨 |

---

## 3. 키워드 → skill_key 매핑 규칙

### EXPLICIT 트리거 (직접 언급)

| 입력 키워드/문구 | skill_key | evidence_type |
|-----------------|-----------|---------------|
| "채용", "공고 작성", "JD 작성", "서류 전형", "면접" | recruiting | EXPLICIT |
| "온보딩", "입문 교육", "OJT", "신입 교육" | training_and_onboarding | EXPLICIT |
| "성과 평가", "KPI", "MBO", "인사 평가" | performance_management | EXPLICIT |
| "급여", "연봉", "복리후생", "4대보험" | payroll | EXPLICIT |
| "취업규칙", "인사규정", "HR 정책" | hr_policy | EXPLICIT |
| "근로기준법", "노동법", "노사 관계" | labor_law | EXPLICIT |
| "SQL", "쿼리", "데이터베이스" | sql | EXPLICIT |
| "Python", "파이썬" | python | EXPLICIT |
| "대시보드", "시각화", "Tableau", "Power BI" | data_visualization | EXPLICIT |
| "A/B 테스트", "실험 설계" | ab_testing | EXPLICIT |
| "SEO", "SEM", "검색광고" | seo_sem | EXPLICIT |
| "캠페인", "마케팅 캠페인" | campaign_management | EXPLICIT |
| "PRD", "기획서", "제품 기획" | product_planning | EXPLICIT |
| "로드맵", "우선순위" | roadmap_management | EXPLICIT |
| "스프린트", "스크럼", "애자일" | sprint_management | EXPLICIT |
| "벤더", "공급업체", "외주" | vendor_management | EXPLICIT |
| "프로세스 개선", "효율화", "자동화" | process_improvement | EXPLICIT |
| "보고서 작성", "문서화", "매뉴얼" | documentation | EXPLICIT |
| "발표", "PT", "프레젠테이션" | presentation | EXPLICIT |
| "멘토링", "코칭" | mentoring | EXPLICIT |

---

### INFERRED 트리거 (맥락 추론)

| 입력 문구 | 추론 skill_key | confidence |
|-----------|---------------|-----------|
| "후보자 관리" | recruiting | 0.8 |
| "신입사원 적응 지원" | training_and_onboarding | 0.75 |
| "팀원 피드백" | performance_management | 0.6 |
| "데이터 취합 및 정리" | data_analysis | 0.7 |
| "엑셀로 집계" | excel | 0.8 |
| "일정 조율", "미팅 조율" | coordination | 0.8 |
| "여러 부서와 협업" | stakeholder_management | 0.7 |
| "팀 리드", "팀장 역할" | leadership | 0.85 |
| "블로그 작성", "SNS 운영" | marketing_content | 0.8 |
| "고객 응대", "CS" | customer_success | 0.75 |
| "예산 관리", "비용 절감" | cost_management | 0.8 |
| "재고 관리", "입출고" | logistics | 0.8 |
| "사용자 인터뷰", "FGI" | user_research | 0.85 |
| "와이어프레임", "목업" | ux_sense | 0.8 |

---

### ACHIEVED 트리거 (성과 역산)

| 성과 기술 패턴 | 역산 skill_key | confidence |
|---------------|---------------|-----------|
| "채용 목표 X% 달성" | recruiting | 0.9 |
| "만족도 X점 달성 (온보딩)" | training_and_onboarding | 0.85 |
| "이직률 X% 감소" | employee_relations | 0.8 |
| "프로세스 X% 단축" | process_improvement | 0.9 |
| "비용 X% 절감" | cost_management | 0.85 |
| "전환율 X% 향상" | marketing_analytics | 0.85 |
| "MAU X명 달성" | growth_hacking | 0.8 |

---

## 4. 추출 알고리즘 (의사코드)

```python
def extract_evidences(career_history: CareerHistory) -> list[Evidence]:
    evidences = []
    text = career_history.responsibilities + " " + (career_history.achievements or "")
    
    # Step 1: EXPLICIT 추출
    for keyword, skill_key in EXPLICIT_RULES.items():
        if keyword in text:
            span = find_span(text, keyword)
            evidences.append(Evidence(
                skill_key=skill_key,
                original_text=extract_sentence(text, span),
                evidence_type="EXPLICIT",
                confidence_score=1.0
            ))
    
    # Step 2: INFERRED 추출 (EXPLICIT로 이미 커버된 skill_key는 스킵)
    covered = {e.skill_key for e in evidences}
    for pattern, skill_key, confidence in INFERRED_RULES:
        if skill_key not in covered and pattern in text:
            span = find_span(text, pattern)
            evidences.append(Evidence(
                skill_key=skill_key,
                original_text=extract_sentence(text, span),
                evidence_type="INFERRED",
                confidence_score=confidence
            ))
    
    # Step 3: ACHIEVED 추출 (achievements 필드에서만)
    if career_history.achievements:
        for pattern, skill_key, confidence in ACHIEVED_RULES:
            if re.search(pattern, career_history.achievements):
                evidences.append(Evidence(
                    skill_key=skill_key,
                    original_text=extract_sentence(career_history.achievements, pattern),
                    evidence_type="ACHIEVED",
                    confidence_score=confidence
                ))
    
    return deduplicate(evidences)
```

---

## 5. 불변 규칙

1. `original_text`는 사용자 입력 원문의 **문장 단위**로 추출. 임의로 수정/요약 금지.
2. 동일 문장이 동일 skill_key에 2번 매핑되면 중복 제거 (더 높은 confidence 유지).
3. confidence_score < 0.5인 Evidence는 생성하지 않는다.
4. Evidence가 0개인 requirement는 match_level = NONE으로 처리.