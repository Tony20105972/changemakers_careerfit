# 07 — Skill Taxonomy

> 이 문서는 `06_SCORING_RULES.md` §2의 weight 자동 배분 알고리즘이 참조하는  
> **스킬 풀(Skill Pool)**을 정의한다.  
> 구조: **공통 스킬 풀(COMMON 후보, ~20개)** + **Job Family별 고유 스킬(UNIQUE, 4~5개 × 10)**

---

## 0. 설계 원칙

1. 모든 스킬은 `skill_key`(영문 snake_case), `label_ko`, `description`, `category`를 가진다.
2. 스킬은 **공통(common pool)**과 **직무 고유(unique per job family)**로 나뉜다.
3. 하나의 skill_key가 여러 Job Family에서 UNIQUE로 동시에 지정될 수 있다  
   (예: `user_research`는 Product와 Design 둘 다의 UNIQUE 핵심 스킬).
4. Job Family를 추가할 때 새 스킬이 필요하면 이 문서에 먼저 등록한다 (`.cursorrules` Rule 10).
5. 총 스킬 수 목표: **약 65~75개** (공통 ~20개 + 직무 고유 중복 제거 후 ~45~55개)

---

## 1. 공통 스킬 풀 (COMMON Pool) — 20개

`06_SCORING_RULES.md` §2.1의 `common_skill_keys`는 이 풀에서 Job Family당 5개를 선택한다.

| skill_key | label_ko | description |
|-----------|----------|--------------|
| `communication` | 커뮤니케이션 | 내외부 이해관계자와의 효과적 소통 |
| `stakeholder_management` | 이해관계자 관리 | 다양한 이해관계자 조율 및 관계 관리 |
| `documentation` | 문서화 | 보고서, 기획서, 매뉴얼 등 문서 작성 |
| `project_management` | 프로젝트 관리 | 일정, 리소스, 리스크 관리 |
| `data_analysis` | 데이터 분석 | 데이터 수집, 정리, 인사이트 도출 |
| `presentation` | 발표/프레젠테이션 | 데이터와 아이디어를 청중에게 전달 |
| `problem_solving` | 문제 해결 | 문제 정의 → 원인 분석 → 해결책 도출 |
| `coordination` | 일정/업무 조율 | 여러 팀/부서 간 업무 조율 |
| `leadership` | 리더십 | 팀 또는 프로젝트 리드 경험 |
| `mentoring` | 멘토링 | 후배/팀원 성장 지원 |
| `excel` | Excel/스프레드시트 | 피벗, 수식, 매크로 등 고급 활용 |
| `reporting` | 보고/리포팅 | 정기 보고서 작성 및 경영진 보고 |
| `budgeting` | 예산 관리 | 예산 편성, 집행, 모니터링 |
| `process_design` | 프로세스 설계 | 업무 절차 설계 및 표준화 |
| `training` | 교육/트레이닝 | 사내 교육 프로그램 기획 및 진행 |
| `negotiation_basic` | 협상 기초 | 내부/외부 협상 및 합의 도출 |
| `vendor_coordination` | 외부 업체 소통 | 협력사/벤더와의 일상적 커뮤니케이션 |
| `quality_control` | 품질 관리 기초 | 결과물 검토 및 품질 기준 적용 |
| `tooling_adoption` | 신규 도구 활용 | 새로운 업무 도구/시스템 학습 및 적용 |
| `crossfunctional_collab` | 부서간 협업 | 타 부서와의 정기적 협업 프로젝트 경험 |

---

## 2. Job Family별 고유 스킬 (UNIQUE)

각 Job Family는 4~5개의 고유 핵심 스킬을 가진다. 이 목록이 `06_SCORING_RULES.md` §2.1의  
`core_skill_keys` 입력값이며, weight 자동 배분 알고리즘에 의해 합계 65%로 배분된다.

### 2.1 HR

| skill_key | label_ko | description |
|-----------|----------|--------------|
| `recruiting` | 채용 관리 | JD 작성, 서류 검토, 면접 진행 등 채용 전 과정 |
| `training_and_onboarding` | 교육/온보딩 | 신입·경력 교육 프로그램 설계 및 운영 |
| `labor_law` | 노동법 | 근로기준법, 노동관계법령 이해 및 적용 |
| `payroll` | 급여 관리 | 급여 계산, 복리후생 설계 및 관리 |

> 참고 스킬(이 Job Family에서 COMMON으로 선택될 가능성이 높음): `performance_management`, `employee_relations`, `hr_policy`, `hris` — 이들은 §3 "보조 스킬 풀"에 등록.

### 2.2 Marketing

| skill_key | label_ko | description |
|-----------|----------|--------------|
| `campaign_management` | 캠페인 관리 | 마케팅 캠페인 기획, 실행, 성과 분석 |
| `seo_sem` | SEO/SEM | 검색 최적화 및 검색광고 운영 |
| `content_marketing` | 콘텐츠 마케팅 | 블로그, SNS, 광고 카피 등 콘텐츠 제작 |
| `brand_management` | 브랜드 관리 | 브랜드 아이덴티티 관리 및 가이드라인 수립 |

### 2.3 Data

| skill_key | label_ko | description |
|-----------|----------|--------------|
| `sql` | SQL | 데이터베이스 쿼리 작성 및 분석 |
| `python` | Python | 데이터 처리 및 분석을 위한 Python 활용 |
| `data_visualization` | 데이터 시각화 | 대시보드, 차트 등 시각화 도구 활용 |
| `statistics` | 통계 | 기초 통계, 가설 검정, 회귀 분석 |

> 참고: `data_analysis`는 COMMON 풀에 이미 존재하므로 Data Job Family의 UNIQUE에는 포함하지 않음 (중복 방지). Data는 `data_analysis`를 COMMON 5개 중 하나로 선택해 일관성 유지.

### 2.4 Product

| skill_key | label_ko | description |
|-----------|----------|--------------|
| `product_planning` | 제품 기획 | 제품 요구사항 정의, PRD 작성 |
| `roadmap_management` | 로드맵 관리 | 제품 로드맵 수립 및 우선순위 결정 |
| `user_research` | 사용자 리서치 | 인터뷰, 설문, 사용성 테스트 |
| `ux_sense` | UX 감각 | 사용자 경험 설계 및 와이어프레임 |

### 2.5 Operations

| skill_key | label_ko | description |
|-----------|----------|--------------|
| `process_improvement` | 프로세스 개선 | 업무 효율화, 표준화, 자동화 |
| `vendor_management` | 벤더 관리 | 외주/공급업체 선정, 계약, 관계 관리 |
| `operations_management` | 운영 관리 | 일상 운영 프로세스 총괄 |
| `logistics` | 물류/공급망 | 물류, 재고, 공급망 관리 |

### 2.6 Sales

| skill_key | label_ko | description |
|-----------|----------|--------------|
| `lead_generation` | 리드 발굴 | 신규 영업 기회 발굴 및 관리 |
| `account_management` | 계정 관리 | 기존 고객 관계 유지 및 추가 매출 창출 |
| `negotiation` | 협상 | 계약 조건 협상 및 클로징 |
| `crm_management` | CRM 운영 | Salesforce, HubSpot 등 CRM 시스템 활용 |

> `negotiation`(고급, Sales UNIQUE)과 `negotiation_basic`(COMMON)은 별개 스킬로 취급한다.  
> `negotiation`은 거래 클로징 수준, `negotiation_basic`은 일상적 합의 도출 수준으로 난이도가 다르다.

### 2.7 Design

| skill_key | label_ko | description |
|-----------|----------|--------------|
| `ui_design` | UI 디자인 | 인터페이스 시각 디자인 |
| `prototyping` | 프로토타이핑 | Figma 등으로 인터랙티브 프로토타입 제작 |
| `design_systems` | 디자인 시스템 | 컴포넌트 라이브러리 및 디자인 가이드 운영 |
| `user_research` | 사용자 리서치 | (Product와 공유 — §0 원칙 4) |

### 2.8 Finance

| skill_key | label_ko | description |
|-----------|----------|--------------|
| `financial_modeling` | 재무 모델링 | 엑셀/스프레드시트 기반 재무 모델 구축 |
| `budgeting_advanced` | 예산 수립 (고급) | 조직 단위 예산 편성 및 시나리오 분석 |
| `accounting` | 회계 | 재무제표 작성, 회계 처리 |
| `financial_reporting` | 재무 보고 | 경영진/투자자 대상 재무 리포트 작성 |

> `budgeting_advanced`(Finance UNIQUE)와 `budgeting`(COMMON)은 별개 — 후자는 부서 단위 예산 집행 수준.

### 2.9 Engineering

| skill_key | label_ko | description |
|-----------|----------|--------------|
| `software_development` | 소프트웨어 개발 | 프로그래밍 언어를 활용한 기능 구현 |
| `code_review` | 코드 리뷰 | 동료 코드 검토 및 피드백 |
| `system_design` | 시스템 설계 | 아키텍처 설계 및 기술적 의사결정 |
| `debugging` | 디버깅 | 버그 원인 분석 및 해결 |

### 2.10 Customer Success

| skill_key | label_ko | description |
|-----------|----------|--------------|
| `customer_onboarding` | 고객 온보딩 | 신규 고객 도입 지원 및 초기 정착 |
| `churn_management` | 이탈 관리 | 고객 이탈 신호 감지 및 방지 활동 |
| `support_ticketing` | 고객 지원 티켓 처리 | CS 티켓 응대 및 해결 |
| `account_health` | 계정 헬스 관리 | 고객 사용률/만족도 모니터링 |

---

## 3. 보조 스킬 풀 (Job Family별 COMMON 선택 후보)

각 Job Family의 `common_skill_keys`(5개)는 §1의 공통 풀에서 우선 선택하되,  
직무 연관성이 높은 보조 스킬이 필요한 경우 아래 목록에서 추가한다.  
보조 스킬도 COMMON으로 분류되며, weight 배분 방식은 동일하다.

| skill_key | label_ko | description | 주요 연관 Job Family |
|-----------|----------|--------------|----------------------|
| `performance_management` | 성과 관리 | KPI 설정, 평가 프로세스 운영 | HR, Operations |
| `employee_relations` | 직원 관계 관리 | 직원 고충 처리, 조직문화 관리 | HR |
| `hr_policy` | HR 정책 수립 | 취업규칙, 인사규정 등 정책 수립 | HR |
| `hris` | HRIS 운영 | HR 정보 시스템 관리 및 데이터 유지 | HR |
| `social_media` | 소셜 미디어 | SNS 채널 운영 및 커뮤니티 관리 | Marketing |
| `marketing_analytics` | 마케팅 분석 | GA, 전환율, ROAS 등 마케팅 지표 분석 | Marketing |
| `data_pipeline` | 데이터 파이프라인 | ETL 설계 및 데이터 처리 자동화 | Data, Engineering |
| `ab_testing` | A/B 테스트 | 실험 설계 및 통계적 유의성 검증 | Data, Product, Marketing |
| `sprint_management` | 스프린트 관리 | 애자일/스크럼 운영 경험 | Product, Engineering |
| `competitive_analysis` | 경쟁사 분석 | 시장 및 경쟁 제품 분석 | Product, Marketing |
| `cost_management` | 비용 관리 | 예산 편성 및 비용 최적화 | Operations, Finance |
| `quality_management` | 품질 관리 (고급) | 품질 기준 설정 및 모니터링 체계 운영 | Operations |
| `wireframing` | 와이어프레임 | 정보 구조 설계 및 화면 설계도 작성 | Design, Product |
| `accessibility` | 접근성 | 웹/앱 접근성 표준 준수 설계 | Design |
| `forecasting` | 매출/수요 예측 | 데이터 기반 매출 또는 수요 예측 | Sales, Finance |
| `pipeline_management` | 영업 파이프라인 관리 | 영업 단계별 기회 관리 | Sales |
| `tax_compliance` | 세무 처리 | 세금 신고 및 컴플라이언스 대응 | Finance |
| `api_design` | API 설계 | RESTful API 등 인터페이스 설계 | Engineering |
| `testing_qa` | 테스트/QA | 단위/통합 테스트 작성 및 품질 검증 | Engineering |
| `customer_feedback_analysis` | 고객 피드백 분석 | VOC 수집 및 정성/정량 분석 | Customer Success |
| `renewal_management` | 갱신 관리 | 계약 갱신율 관리 및 협상 | Customer Success, Sales |

---

## 4. Job Family별 권장 COMMON 5종 (참고)

`06_SCORING_RULES.md` §2.1의 `common_skill_keys` 작성 시 참고용 권장 조합.  
필수는 아니며, 시딩 시 조정 가능 — 단 항상 5개, weight 합 0.35를 만족해야 한다.

| Job Family | 권장 COMMON 5종 |
|------------|------------------|
| HR | communication, stakeholder_management, documentation, performance_management, employee_relations |
| Marketing | communication, data_analysis, presentation, social_media, marketing_analytics |
| Data | communication, documentation, data_analysis, ab_testing, presentation |
| Product | communication, stakeholder_management, data_analysis, sprint_management, competitive_analysis |
| Operations | process_design, vendor_coordination, cost_management, quality_control, coordination |
| Sales | communication, negotiation_basic, crossfunctional_collab, forecasting, pipeline_management |
| Design | communication, stakeholder_management, wireframing, accessibility, presentation |
| Finance | excel, reporting, budgeting, cost_management, tax_compliance |
| Engineering | documentation, problem_solving, api_design, testing_qa, crossfunctional_collab |
| Customer Success | communication, stakeholder_management, customer_feedback_analysis, renewal_management, data_analysis |

---

## 5. 명명 규칙

1. `skill_key`는 snake_case, 소문자만 사용
2. 새 스킬 추가 시 이 문서에 먼저 등록 후 `08_EVIDENCE_RULES.md`, `data/job_requirements_*.json`에서 사용
3. 동일 개념이라도 난이도/범위가 다르면 별개 skill_key 사용 (예: `negotiation` vs `negotiation_basic`, `budgeting` vs `budgeting_advanced`)
4. 하나의 skill_key는 여러 Job Family에서 UNIQUE로 중복 지정 가능 (`user_research`)
5. 하나의 Evidence는 여러 skill_key에 동시 매핑 가능 (`08_EVIDENCE_RULES.md` §1)

---

## 6. 스킬 수 요약

```
공통 풀 (§1):        20개
직무 고유 (§2):      40개 (10 families × 4개, user_research 중복 1개 제외 시 39개 유니크)
보조 풀 (§3):        21개

총 유니크 skill_key: 약 79개
```