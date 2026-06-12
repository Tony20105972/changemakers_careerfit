# CareerFit — Founder Mode Roadmap

> **엔진이 전부다. 프론트는 나중이다.**
>
> 성공 배분: Engine 60% / Backend 20% / Frontend 20%

---

## 전체 파이프라인

```
Career Intake (사용자 입력)
        ↓
Input Normalizer (정제)
        ↓
Skill Tagger (스킬 태깅)
        ↓
Evidence Extractor (근거 추출)
        ↓
Requirement Matcher (요구사항 매칭)
        ↓
Scoring Engine (점수 계산)
        ↓
Gap Analyzer (갭 분류)
        ↓
Recommendation Engine (추천 생성)
        ↓
Report Builder → report.json
        ↓
Text Template Engine (문장 생성)
        ↓
HTML Renderer → report.html
        ↓
PDF Engine → report.pdf
```

---

## 레포 구조

```
careerfit/
├── backend/
│   ├── engine/
│   │   ├── input_normalizer.py
│   │   ├── skill_tagger.py
│   │   ├── evidence_extractor.py
│   │   ├── requirement_matcher.py
│   │   ├── scoring_engine.py
│   │   ├── gap_analyzer.py
│   │   ├── recommendation_engine.py
│   │   └── report_builder.py
│   ├── api/
│   │   └── routes/
│   │       └── reports.py
│   ├── services/
│   │   └── report_service.py
│   ├── models/
│   │   ├── db.py
│   │   └── schemas.py
│   ├── pdf/
│   │   ├── templates/
│   │   │   └── report.html.j2
│   │   └── generator.py
│   └── main.py
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Landing.tsx
│       │   ├── ReportNew.tsx
│       │   └── ReportResult.tsx
│       └── api/
│           └── reports.ts
├── data/
│   ├── job_requirements_hr.json
│   ├── job_requirements_marketing.json
│   ├── job_requirements_data.json
│   ├── job_requirements_product.json
│   └── job_requirements_operations.json
├── docs/
│   └── *.md
├── scripts/
│   ├── seed_requirements.py
│   └── test_engine.py
└── output/
    ├── sample_input.json
    ├── sample_report.json
    └── sample_report.pdf
```

---

---

# WEEK 1 — 설계 + Engine 뼈대

**목표:** `input.json` → `report.json` 구조 100% 확정. 코드 50%.

---

## Day 1 — 프로젝트 세팅 + Vision 문서

### 작업

```bash
mkdir -p careerfit/{backend/engine,backend/api,backend/services,backend/models,backend/pdf/templates,frontend/src/{pages,api},data,docs,scripts,output}
cd careerfit && git init
touch .cursorrules .gitignore README.md
```

### 문서 작성

- `docs/00_PROJECT_VISION.md` — 미션, 4대 원칙 (Evidence First / Deterministic First / Report JSON First / LLM Optional)
- `docs/01_PRD.md` — 목표, 타겟 유저, V1 In/Out Scope, 성공 기준

### 완료 기준

- [ ] 레포 구조 생성 완료
- [ ] Vision 문서 읽으면 "뭘 만드는지" 3줄로 설명 가능

---

## Day 2 — 핵심 데이터 계약 확정

### 작업

- `docs/02_USER_FLOW.md` — Landing → Form → Generating → Result → PDF
- `docs/03_ERD.md` — 8개 테이블, 관계, SQL DDL 전체
- `docs/04_PAYLOAD_CONTRACT.md` — Frontend Request / Backend Request / Algorithm Request / Algorithm Response / Error Format

### 핵심 산출물: `output/sample_input.json`

```json
{
  "target_job_family": "HR",
  "career_histories": [
    {
      "company_name": "주식회사 ABC",
      "title": "HR 매니저",
      "start_date": "2020-03",
      "end_date": "2023-12",
      "is_current": false,
      "responsibilities": "신입 채용 전 과정 운영. JD 작성, 서류 검토, 임원 면접 조율. 온보딩 프로그램 설계 및 운영. HR 데이터북 분기별 작성.",
      "achievements": "연간 채용 목표 120% 달성. 온보딩 만족도 4.6/5.0. 이직률 18% → 11% 감소."
    }
  ]
}
```

### 완료 기준

- [ ] `sample_input.json` 확정
- [ ] ERD 테이블 8개 전부 컬럼/타입/관계 정의 완료
- [ ] Payload 계약 문서에 Request/Response 예시 전부 있음

---

## Day 3 — Report JSON 스키마 확정

### 작업

- `docs/05_REPORT_SCHEMA.md` — 13개 섹션 전체 JSON 구조 정의

### 핵심 산출물: `output/sample_report.json` 뼈대

Report JSON의 모든 key가 존재하는 빈 뼈대를 손으로 작성한다.  
값은 임시 placeholder여도 됨. **구조만 확정.**

```json
{
  "meta": { "report_id": "...", "target_job_family": "HR", "engine_version": "1.0.0" },
  "summary": { "total_score": 0, "fit_level": "", "one_line": "" },
  "careerProfile": { "total_experience_months": 0, "extracted_skills": [] },
  "targetJobAnalysis": { "core_requirements": [] },
  "skillMapping": { "matched": [], "unmatched": [] },
  "evidenceMapping": [],
  "scores": { "total": 0, "breakdown": {} },
  "strengths": [],
  "gaps": [],
  "recommendations": { "short_term": [], "mid_term": [] },
  "roadmap": { "phases": [] },
  "reportSections": []
}
```

### 완료 기준

- [ ] `sample_report.json` 뼈대 확정 (모든 key 존재)
- [ ] "이 JSON만 있으면 PDF를 만들 수 있다"는 확신

---

## Day 4 — Skill Taxonomy 확정

### 작업

- `docs/07_SKILL_TAXONOMY.md` — 100~150개 스킬 정의

### 스킬 카테고리 구성

```
공통 (15개)
  communication, stakeholder_management, documentation,
  project_management, data_analysis, presentation,
  problem_solving, coordination, leadership, mentoring,
  excel, reporting, budgeting, process_design, training

HR 특화 (12개)
  recruiting, onboarding, performance_management,
  payroll, hr_policy, labor_law, employee_relations,
  hris, headcount_planning, org_design, culture_building,
  exit_management

Marketing 특화 (12개)
  content_marketing, campaign_management, seo_sem,
  brand_management, copywriting, social_media,
  growth_hacking, marketing_analytics, email_marketing,
  influencer_marketing, event_management, crm

Data 특화 (12개)
  sql, python, r, data_visualization, statistics,
  ml_fundamentals, data_pipeline, ab_testing,
  data_governance, bi_tools, feature_engineering, tableau

Product 특화 (12개)
  product_planning, user_research, roadmap_management,
  ux_sense, sprint_management, metric_definition,
  competitive_analysis, wireframing, go_to_market,
  pricing_strategy, feature_prioritization, product_analytics

Operations 특화 (12개)
  process_improvement, operations_management,
  vendor_management, quality_management, cost_management,
  logistics, customer_success, sla_management,
  inventory_management, erp_management, compliance, risk_management
```

### 완료 기준

- [ ] 각 스킬마다 `skill_key`, `label_ko`, `description`, `category` 정의
- [ ] 총 75개 이상 확정

---

## Day 5 — Evidence Rules 확정

### 작업

- `docs/08_EVIDENCE_RULES.md` — 키워드 → skill_key 매핑 전체 테이블

### EXPLICIT 매핑 (직접 언급, 50개 이상)

```
"채용", "JD 작성", "서류 전형", "면접" → recruiting
"온보딩", "OJT", "입문 교육" → onboarding
"성과 평가", "KPI", "MBO" → performance_management
"SQL", "쿼리" → sql
"Python", "파이썬" → python
"대시보드", "시각화" → data_visualization
"A/B 테스트" → ab_testing
"캠페인" → campaign_management
"SEO", "SEM" → seo_sem
"PRD", "제품 기획" → product_planning
"스프린트", "스크럼" → sprint_management
"벤더", "외주" → vendor_management
"프로세스 개선" → process_improvement
...
```

### INFERRED 매핑 (맥락 추론, 30개 이상)

```
"후보자 관리" → recruiting (0.8)
"데이터 취합" → data_analysis (0.7)
"엑셀로 집계" → excel (0.8)
"일정 조율" → coordination (0.8)
"팀원 피드백" → performance_management (0.6)
"고객 응대" → customer_success (0.75)
"예산 관리" → budgeting (0.8)
...
```

### 완료 기준

- [ ] EXPLICIT 50개 이상 매핑 테이블 완성
- [ ] INFERRED 30개 이상 매핑 테이블 완성
- [ ] `sample_input.json` 텍스트를 손으로 파싱해서 Evidence 추출 결과 검증

---

## Day 6 — Scoring Rules + Requirement DB

### 작업 1: `docs/06_SCORING_RULES.md`

점수 공식 확정:

```
total_score = Σ (weight × match_score × 100)

matchLevel → match_score:
  FULL    = 1.00
  STRONG  = 0.75
  PARTIAL = 0.50
  WEAK    = 0.25
  NONE    = 0.00

core penalty:
  is_core + NONE → -5.0
  is_core + WEAK → -2.5
```

### 작업 2: `data/` Requirement JSON 5개 작성

`data/job_requirements_hr.json` 예시:

```json
[
  { "requirement_key": "recruiting",          "label_ko": "채용 관리",   "weight": 0.20, "is_core": true  },
  { "requirement_key": "onboarding",          "label_ko": "온보딩",      "weight": 0.15, "is_core": true  },
  { "requirement_key": "performance_management","label_ko": "성과 관리", "weight": 0.15, "is_core": true  },
  { "requirement_key": "hr_policy",           "label_ko": "HR 정책",    "weight": 0.12, "is_core": false },
  { "requirement_key": "payroll",             "label_ko": "급여 관리",   "weight": 0.10, "is_core": false },
  { "requirement_key": "labor_law",           "label_ko": "노동법",      "weight": 0.10, "is_core": false },
  { "requirement_key": "stakeholder_management","label_ko": "이해관계자","weight": 0.08, "is_core": false },
  { "requirement_key": "documentation",       "label_ko": "문서화",      "weight": 0.05, "is_core": false },
  { "requirement_key": "data_analysis",       "label_ko": "데이터 분석", "weight": 0.05, "is_core": false }
]
```

**weight 합계 = 1.0 필수 검증**

### 완료 기준

- [ ] 5개 Job Family Requirement JSON 완성, 각 weight 합계 = 1.0
- [ ] `sample_input.json` → 수작업 점수 계산으로 예상 점수 도출

---

## Day 7 — Engine Skeleton

### 작업: 각 파일 인터페이스(함수 시그니처) 작성

```python
# input_normalizer.py
def normalize_input(raw_input: dict) -> NormalizedInput:
    """Frontend payload → 엔진용 정제 구조체"""

# skill_tagger.py
def tag_skills(career_history: CareerHistory) -> list[SkillTag]:
    """경력 텍스트 → skill_key 리스트"""

# evidence_extractor.py
def extract_evidences(career_history: CareerHistory) -> list[Evidence]:
    """경력 텍스트 → Evidence 리스트 (original_text 보존)"""

# requirement_matcher.py
def match_requirements(
    evidences: list[Evidence],
    requirements: list[Requirement]
) -> list[RequirementMatch]:
    """Evidence × Requirement → matchLevel 결정"""

# scoring_engine.py
def calculate_score(matches: list[RequirementMatch]) -> ScoreResult:
    """matchLevel + weight → 총점 + breakdown"""

# gap_analyzer.py
def analyze_gaps(matches: list[RequirementMatch], requirements: list[Requirement]) -> list[Gap]:
    """미충족 요구사항 → Gap + severity"""

# recommendation_engine.py
def generate_recommendations(gaps: list[Gap], job_family: str) -> Recommendations:
    """Gap → 단기/중기 추천 행동"""

# report_builder.py
def build_report(
    normalized_input: NormalizedInput,
    evidences: list[Evidence],
    matches: list[RequirementMatch],
    score: ScoreResult,
    gaps: list[Gap],
    recommendations: Recommendations
) -> ReportJSON:
    """모든 결과 → report.json 조립"""
```

### Pydantic 모델 초안

```python
# models/schemas.py
class Evidence(BaseModel):
    career_history_id: str
    skill_key: str
    original_text: str          # 절대 수정 금지
    evidence_type: EvidenceType # EXPLICIT | INFERRED | ACHIEVED
    confidence_score: float     # 0.0 ~ 1.0

class RequirementMatch(BaseModel):
    requirement_key: str
    match_level: MatchLevel     # FULL|STRONG|PARTIAL|WEAK|NONE
    match_score: float
    matched_evidence_ids: list[str]

class ScoreResult(BaseModel):
    total: float
    breakdown: dict[str, BreakdownItem]

class Gap(BaseModel):
    requirement_key: str
    gap_severity: GapSeverity   # CRITICAL|MAJOR|MINOR
    gap_reason: str
    recommendation: str
    priority_order: int
```

### 완료 기준

- [ ] 7개 engine 파일 생성, 함수 시그니처 전부 작성
- [ ] Pydantic 스키마 초안 작성
- [ ] `python -c "from engine import report_builder"` 오류 없음

---

---

# WEEK 2 — Engine 구현 + PDF

**목표:** `python scripts/test_engine.py` → `output/report.json` 생성

---

## Day 8 — Skill Tagger 구현

### 구현 목표

```python
input:  "신입 채용 전 과정 운영. JD 작성, 서류 검토, 임원 면접 조율."
output: [
  SkillTag(skill_key="recruiting", evidence_type="EXPLICIT", confidence=1.0),
  SkillTag(skill_key="stakeholder_management", evidence_type="INFERRED", confidence=0.7)
]
```

### 구현 방식

1. `08_EVIDENCE_RULES.md`의 EXPLICIT 키워드 테이블을 Python dict로 로드
2. 텍스트에서 키워드 매칭 (단순 `in` 연산자, 정규식 보조)
3. INFERRED 패턴은 별도 리스트로 관리

### 테스트

```bash
python scripts/test_engine.py --step skill_tagger --input output/sample_input.json
```

### 완료 기준

- [ ] `sample_input.json`에서 최소 5개 skill_key 추출
- [ ] `original_text`가 원문 그대로 보존됨

---

## Day 9 — Evidence Extractor 구현

### 구현 목표

```json
{
  "skill_key": "recruiting",
  "original_text": "신입 채용 전 과정 운영. JD 작성, 서류 검토, 임원 면접 조율.",
  "evidence_type": "EXPLICIT",
  "confidence_score": 1.0
}
```

### 구현 포인트

- 키워드가 속한 문장 전체를 `original_text`로 추출 (문장 분리 기준: `.` 또는 `\n`)
- 동일 `skill_key`에 여러 문장 매핑 가능
- `achievements` 필드는 ACHIEVED 타입으로 별도 처리

### 테스트

```bash
python scripts/test_engine.py --step evidence_extractor --input output/sample_input.json
```

### 완료 기준

- [ ] `sample_input.json` → `evidences[]` 배열 출력
- [ ] 각 evidence에 `original_text` 원문 포함 확인

---

## Day 10 — Requirement Matcher 구현

### 구현 목표

```python
input:
  evidences: [Evidence(skill_key="recruiting", confidence=1.0), ...]
  requirements: job_requirements_hr.json 로드

output:
  [
    RequirementMatch(requirement_key="recruiting", match_level="FULL", match_score=1.0),
    RequirementMatch(requirement_key="payroll", match_level="NONE", match_score=0.0),
    ...
  ]
```

### matchLevel 결정 로직

```python
def determine_match_level(evidences: list[Evidence]) -> MatchLevel:
    explicit = [e for e in evidences if e.evidence_type == "EXPLICIT"]
    inferred = [e for e in evidences if e.evidence_type == "INFERRED"]
    achieved = [e for e in evidences if e.evidence_type == "ACHIEVED"]

    if len(explicit) >= 2:                          return FULL
    if len(explicit) >= 1 and sum_confidence >= 1.8: return FULL
    if len(explicit) >= 1:                          return STRONG
    if len(inferred) >= 2:                          return PARTIAL
    if len(inferred) >= 1 and len(achieved) >= 1:   return PARTIAL
    if len(inferred) >= 1:                          return WEAK
    return NONE
```

### 완료 기준

- [ ] 9개 HR requirement 전부 matchLevel 결정됨
- [ ] NONE이 아닌 항목은 반드시 `matched_evidence_ids` 존재

---

## Day 11 — Scoring Engine 구현

### 구현 목표

```python
input:  [RequirementMatch, ...]
output: ScoreResult(total=78.5, breakdown={...})
```

### 구현 로직

```python
def calculate_score(matches, requirements) -> ScoreResult:
    raw_score = sum(
        req.weight * MATCH_SCORE[match.match_level] * 100
        for req, match in zip(requirements, matches)
    )
    penalty = apply_core_penalty(matches, requirements)
    total = max(0.0, raw_score + penalty)
    return ScoreResult(total=round(total, 1), breakdown=build_breakdown(...))
```

### 결정론적 검증

```bash
# 동일 입력 3회 실행, 점수 동일한지 확인
for i in 1 2 3; do
  python scripts/test_engine.py --step scoring --input output/sample_input.json | grep total_score
done
```

### 완료 기준

- [ ] `sample_input.json` → `total_score` 출력
- [ ] 3회 실행 동일 점수 확인
- [ ] breakdown에 9개 requirement 전부 포함

---

## Day 12 — Gap Analyzer 구현

### 구현 목표

```json
{
  "requirement_key": "payroll",
  "label_ko": "급여 관리",
  "gap_severity": "MAJOR",
  "gap_reason": "급여 관련 직접 경험이 확인되지 않습니다.",
  "recommendation": "급여 계산 실무 경험 또는 ERP정보관리사 자격증 취득을 권장합니다.",
  "priority_order": 1
}
```

### severity 분류 기준

```python
def classify_severity(req, match) -> GapSeverity:
    if req.is_core and match.match_level in [NONE, WEAK]:
        return CRITICAL
    if req.weight >= 0.10 and match.match_level <= PARTIAL:
        return MAJOR
    return MINOR
```

### 추천 텍스트: `data/gap_recommendations.json`

각 skill_key별 gap 발생 시 추천 행동을 사전 정의.

```json
{
  "payroll": "급여 계산 실무 경험 또는 ERP정보관리사 자격증 취득을 권장합니다.",
  "labor_law": "노동법 온라인 강의 수강 (40시간) 또는 노무사 시험 준비를 권장합니다.",
  "sql": "프로그래머스 SQL 코딩 테스트 Level 2 이상 완료를 목표로 학습하세요."
}
```

### 완료 기준

- [ ] Gap 목록 생성, priority_order 1부터 정렬
- [ ] CRITICAL/MAJOR/MINOR 분류 정확성 수동 검증

---

## Day 13 — Recommendation Engine + Report Builder

### Recommendation Engine

```python
input:  gaps: list[Gap], job_family: str
output: Recommendations(
  short_term=[Action(action="...", timeframe="1-2개월"), ...],
  mid_term=[Action(action="...", timeframe="3-6개월"), ...]
)
```

**단기:** CRITICAL/MAJOR gap 중 상위 3개 → 즉시 행동
**중기:** MINOR gap + 전반적 지원 전략

### Report Builder

7개 엔진 결과를 `05_REPORT_SCHEMA.md` 구조로 조립.

```python
def build_report(...) -> dict:
    return {
        "meta": build_meta(report_id, job_family),
        "summary": build_summary(score, matches),
        "careerProfile": build_career_profile(input, evidences),
        "targetJobAnalysis": build_target_job(requirements),
        "skillMapping": build_skill_mapping(matches),
        "evidenceMapping": build_evidence_mapping(evidences),
        "scores": build_scores(score),
        "strengths": build_strengths(matches, evidences),
        "gaps": build_gaps(gaps),
        "recommendations": build_recommendations(recommendations),
        "roadmap": build_roadmap(gaps, job_family),
        "reportSections": build_sections()
    }
```

### 완료 기준

- [ ] `output/sample_report.json` 생성 완료
- [ ] Day 3에서 만든 뼈대와 구조 일치 확인
- [ ] 모든 key 채워짐, null 없음

---

## Day 14 — End-to-End Engine 테스트

### E2E 테스트 스크립트

```bash
python scripts/test_engine.py \
  --input output/sample_input.json \
  --output output/sample_report.json \
  --job-family HR
```

### 검증 체크리스트

```
[ ] sample_report.json 생성됨
[ ] total_score 0 < score < 100
[ ] evidences[] 최소 3개 이상
[ ] gaps[] 최소 1개 이상
[ ] recommendations.short_term 최소 2개 이상
[ ] 모든 evidence에 original_text 존재
[ ] 3회 실행 동일 점수 (결정론적 검증)
[ ] LLM 없이도 report_json 완성됨
```

### 5개 Job Family 테스트

```bash
for family in HR Marketing Data Product Operations; do
  python scripts/test_engine.py \
    --input output/sample_input_${family,,}.json \
    --output output/sample_report_${family,,}.json \
    --job-family $family
  echo "$family: done"
done
```

### 완료 기준

- [ ] 5개 Job Family 전부 report.json 생성 성공
- [ ] 오류 없이 완주

---

---

# WEEK 3 — PDF + Backend + Frontend

**목표:** 브라우저에서 리포트 결과 페이지 열람 가능

---

## Day 15 — Text Template Engine

### 작업

- `docs/09_TEXT_TEMPLATE_RULES.md` 구현
- 점수별/갭 severity별 문장 템플릿 Python 코드로 작성

```python
# text_template.py
SUMMARY_TEMPLATES = {
    "EXCELLENT_FIT": "{job_family_ko} 직무에 매우 높은 적합도({score}점)를 보입니다...",
    "GOOD_FIT":      "{job_family_ko} 직무에 높은 적합도({score}점)를 보입니다...",
    "MODERATE_FIT":  "{job_family_ko} 직무에 기본적인 적합도({score}점)를 보입니다...",
    "LOW_FIT":       "{job_family_ko} 직무와의 적합도({score}점)는 현재 낮은 수준입니다...",
}

def generate_summary_text(score: float, job_family: str) -> str: ...
def generate_strength_text(strength: Strength) -> str: ...
def generate_gap_text(gap: Gap) -> str: ...
def generate_conclusion_text(score: float, gaps: list[Gap]) -> str: ...
```

### LLM 폴백 구조

```python
def polish_text(template_text: str) -> str:
    try:
        return llm_polish(template_text)  # 선택적 윤색
    except Exception:
        return template_text              # 폴백: 템플릿 그대로
```

### 완료 기준

- [ ] LLM 없이도 모든 텍스트 생성됨
- [ ] `sample_report.json`에 텍스트 필드 전부 채워짐

---

## Day 16 — HTML Report 렌더링

### Jinja2 템플릿 구조

```
backend/pdf/templates/
├── report.html.j2          # 메인 템플릿
├── partials/
│   ├── cover.html.j2
│   ├── summary.html.j2
│   ├── skill_mapping.html.j2
│   ├── evidence_mapping.html.j2
│   ├── score_chart.html.j2
│   ├── strength_analysis.html.j2
│   ├── gap_analysis.html.j2
│   ├── recommendations.html.j2
│   └── roadmap.html.j2
└── static/
    └── report.css
```

### 렌더링

```python
from jinja2 import Environment, FileSystemLoader

def render_html(report_json: dict) -> str:
    env = Environment(loader=FileSystemLoader("pdf/templates"))
    template = env.get_template("report.html.j2")
    return template.render(**report_json)
```

### 완료 기준

- [ ] `output/sample_report.html` 생성
- [ ] 브라우저에서 열어 13개 섹션 전부 확인

---

## Day 17 — PDF Engine

### Playwright 방식

```python
# pdf/generator.py
from playwright.sync_api import sync_playwright

def generate_pdf(html_content: str, output_path: str) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content)
        page.pdf(
            path=output_path,
            format="A4",
            margin={"top": "20mm", "bottom": "20mm",
                    "left": "20mm", "right": "20mm"},
            print_background=True
        )
        browser.close()
```

### 테스트

```bash
python -c "
from pdf.generator import generate_pdf
html = open('output/sample_report.html').read()
generate_pdf(html, 'output/sample_report.pdf')
print('PDF 생성 완료')
"
```

### 완료 기준

- [ ] `output/sample_report.pdf` 생성
- [ ] 13개 섹션 전부 렌더링 확인
- [ ] A4 기준 20–35페이지 범위

---

## Day 18 — FastAPI 구현

### 엔드포인트 3개

```python
# api/routes/reports.py

@router.post("/reports", status_code=201)
async def create_report(payload: ReportCreateRequest, background_tasks: BackgroundTasks):
    report_id = str(uuid4())
    # DB에 CREATED 상태로 저장
    background_tasks.add_task(run_engine, report_id, payload)
    return {"report_id": report_id, "status": "CREATED"}

@router.get("/reports/{report_id}")
async def get_report(report_id: str):
    report = await db.get_report(report_id)
    if not report:
        raise HTTPException(404, "REPORT_NOT_FOUND")
    return report

@router.get("/reports/{report_id}/pdf")
async def get_pdf(report_id: str):
    report = await db.get_report(report_id)
    if report.status != "READY":
        raise HTTPException(202, "REPORT_STILL_PROCESSING")
    return FileResponse(report.pdf_url, media_type="application/pdf")
```

### 완료 기준

- [ ] `uvicorn main:app --reload` 실행
- [ ] `POST /reports` curl 테스트 성공
- [ ] `GET /reports/{id}` 상태 반환 확인

---

## Day 19 — Supabase 연동

### 마이그레이션 실행

```sql
-- 순서대로 실행
1. CREATE TYPE report_status, job_family, evidence_type, match_level, gap_severity
2. CREATE TABLE users
3. CREATE TABLE reports
4. CREATE TABLE career_histories
5. CREATE TABLE career_evidences
6. CREATE TABLE job_requirement_stats
7. CREATE TABLE report_scores
8. CREATE TABLE requirement_matches
9. CREATE TABLE report_gaps
```

### 시딩

```bash
python scripts/seed_requirements.py
# data/ 폴더의 5개 JSON → job_requirement_stats 테이블에 INSERT
```

### 완료 기준

- [ ] Supabase Studio에서 9개 테이블 확인
- [ ] `POST /reports` → DB에 레코드 생성 확인
- [ ] 엔진 완료 후 `report_json` 저장 확인

---

## Day 20 — React 3개 페이지

### Landing (`/`)

- 서비스 설명 + CTA 버튼
- 지원 Job Family 5개 표시

### Report Form (`/report/new`)

```tsx
// 동적 경력 추가
const [careers, setCareers] = useState([defaultCareer]);
const addCareer = () => setCareers([...careers, defaultCareer]);

// 제출
const handleSubmit = async () => {
  const res = await api.createReport({ target_job_family, career_histories });
  router.push(`/report/${res.report_id}?status=generating`);
};
```

### Report Result (`/report/:id`)

```tsx
// 폴링
useEffect(() => {
  const poll = setInterval(async () => {
    const res = await api.getReport(reportId);
    if (res.status === "READY") {
      setReport(res.report);
      clearInterval(poll);
    }
  }, 3000);
  return () => clearInterval(poll);
}, [reportId]);
```

### 완료 기준

- [ ] 3개 페이지 브라우저에서 정상 동작
- [ ] Form 제출 → Generating 화면 → Result 화면 전환

---

## Day 21 — Full Stack 연결 + 통합 테스트

### E2E 시나리오

```
1. 브라우저 /report/new 접속
2. HR 선택, 경력 1개 입력, 제출
3. /report/:id?status=generating 화면 → 폴링
4. READY 전환 → 결과 페이지
5. PDF 다운로드 버튼 클릭 → PDF 다운로드
```

### 완료 기준

- [ ] 위 시나리오 오류 없이 완주
- [ ] PDF 다운로드 성공
- [ ] 생성 소요 시간 5분 이내

---

---

# WEEK 4 — MVP 완성 + 배포

**목표:** 실제 URL로 접근 가능한 MVP

---

## Day 22 — 디자인 개선

- 결과 페이지 점수 시각화 (Recharts 또는 Chart.js)
- Skill Mapping progress bar
- Gap severity 색상 구분 (CRITICAL=빨강, MAJOR=주황, MINOR=노랑)

---

## Day 23 — PDF 고급화

- 레이더 차트 (핵심 역량 5개)
- Skill Mapping 바 차트
- 13섹션 페이지 구분 및 목차
- 표지 디자인 완성

---

## Day 24 — 샘플 리포트 5개 생성

```bash
for family in HR Marketing Data Product Operations; do
  python scripts/generate_sample.py --job-family $family
done
```

Landing 페이지에 샘플 리포트 미리보기 추가.

---

## Day 25 — 사람인 연동 (선택)

- 사람인 공고 키워드 크롤링
- `job_requirement_stats` 자동 업데이트 스크립트

```bash
python scripts/sync_job_postings.py --job-family HR --limit 50
```

---

## Day 26 — 버그 수정 + 엣지 케이스

테스트 케이스:
- 경력 1개 / 경력 10개
- responsibilities 50자 최소값
- LLM 실패 시 폴백 동작
- PDF 생성 실패 시 재시도

---

## Day 27 — 성능 + 보안

```
[ ] report_id UUID 추측 불가 확인
[ ] expires_at 30일 만료 동작 확인
[ ] PDF 생성 타임아웃 설정
[ ] FastAPI 에러 핸들러 전체 커버
[ ] CORS 설정 (프론트 도메인만 허용)
```

---

## Day 28 — 배포

### Frontend → Vercel

```bash
cd frontend && vercel --prod
```

### Backend → Render

```yaml
# render.yaml
services:
  - type: web
    name: careerfit-api
    runtime: python
    buildCommand: pip install -r requirements.txt && playwright install chromium
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### DB → Supabase

- 이미 클라우드, 연결 문자열만 환경변수로 설정

### 환경변수 체크리스트

```
SUPABASE_URL
SUPABASE_SERVICE_KEY
OPENAI_API_KEY (optional, LLM 폴백)
PDF_OUTPUT_DIR
FRONTEND_URL (CORS용)
```

### 완료 기준

- [ ] `https://careerfit.kr` (또는 Vercel URL) 접속 가능
- [ ] 리포트 생성 → PDF 다운로드 전체 플로우 성공
- [ ] 5분 이내 완료

---

---

# 체크리스트 요약

## Week 1 마감 기준

```
[ ] sample_input.json 확정
[ ] sample_report.json 뼈대 확정
[ ] Skill Taxonomy 75개 이상
[ ] Evidence Rules EXPLICIT 50개 이상
[ ] Requirement JSON 5개 (weight 합계 = 1.0)
[ ] Engine 7개 파일 인터페이스 작성 완료
```

## Week 2 마감 기준

```
[ ] sample_input.json → sample_report.json E2E 성공
[ ] 5개 Job Family 전부 통과
[ ] 결정론적 검증 (동일 입력 = 동일 점수)
[ ] sample_report.pdf 생성 성공
```

## Week 3 마감 기준

```
[ ] POST /reports → DB 저장 → 엔진 실행 → READY 전환
[ ] 브라우저에서 결과 페이지 열람
[ ] PDF 다운로드 성공
```

## Week 4 마감 기준

```
[ ] 실제 URL 접속 가능
[ ] 샘플 리포트 5개 Landing에 표시
[ ] 생성 소요 5분 이내
[ ] 오류율 5% 미만
```

---

## 핵심 원칙 (매일 확인)

```
1. 오늘 report.json이 더 완성됐는가?
2. 오늘 추가한 코드가 결정론적인가?
3. original_text를 수정한 코드가 없는가?
4. LLM 없이도 리포트가 생성되는가?
5. React를 열기 전에 Engine이 완성됐는가?
```