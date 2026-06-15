# 13 — Development Roadmap (v3)

> **현재 상태:** `docs/00`~`12` (13개 중 문서 12개) 작성 완료.  
> Job Family **10개** (HR/Marketing/Data/Product/Operations/Sales/Design/Finance/Engineering/Customer Success),  
> weight 자동 배분(UNIQUE 65% / COMMON 35%, `06_SCORING_RULES.md` §2) 구조 확정.
>
> 이 로드맵은 **Week 1 잔여 작업(Day 6~7) + Week 2 + Week 3**를 다룬다.  
> Day 1~5에 해당하는 작업(Vision/PRD/Payload/Schema/ERD/Scoring/Taxonomy/Evidence)은 이미 완료되었다.

---

## 전체 요약

```
Week 1 — Architecture Week  (Day 1~5 완료, Day 6~7 잔여)
  완료: 00~09 문서 (Vision, PRD, User Flow, ERD, Payload, Report Schema,
                    Scoring Rules, Skill Taxonomy, Evidence Rules)
  잔여: data/job_requirements_*.json 10종 생성 + sample_input/report.json (HR, Data)

Week 2 — Engine Week
  목표: 6개 엔진 모듈 → report.json 자동 생성 (HR, Data로 검증)

Week 3 — Product Week
  목표: Template → HTML → PDF → API → DB → React → Deploy
```

---

---

# WEEK 1 (잔여) — Requirement DB + Fixture 작성

---

## Day 6 — Job Family Requirement DB 생성 (10개)

### 작업: `data/job_requirements_*.json` × 10

`06_SCORING_RULES.md` §2.2 `allocate_weights()` 알고리즘을 실행하는 시딩 스크립트를 작성한다.

```python
# scripts/generate_requirements.py
import json
from pathlib import Path

JOB_FAMILIES = {
    "hr": {
        "core_skill_keys": ["recruiting", "training_and_onboarding", "labor_law", "payroll"],
        "common_skill_keys": ["communication", "stakeholder_management", "documentation",
                               "performance_management", "employee_relations"],
        "is_core_overrides": {"recruiting": True, "training_and_onboarding": True, "labor_law": True},
    },
    "marketing": {
        "core_skill_keys": ["campaign_management", "seo_sem", "content_marketing", "brand_management"],
        "common_skill_keys": ["communication", "data_analysis", "presentation",
                               "social_media", "marketing_analytics"],
        "is_core_overrides": {"campaign_management": True, "seo_sem": True},
    },
    "data": {
        "core_skill_keys": ["sql", "python", "data_visualization", "statistics"],
        "common_skill_keys": ["communication", "documentation", "data_analysis",
                               "ab_testing", "presentation"],
        "is_core_overrides": {"sql": True, "python": True},
    },
    "product": {
        "core_skill_keys": ["product_planning", "roadmap_management", "user_research", "ux_sense"],
        "common_skill_keys": ["communication", "stakeholder_management", "data_analysis",
                               "sprint_management", "competitive_analysis"],
        "is_core_overrides": {"product_planning": True, "roadmap_management": True},
    },
    "operations": {
        "core_skill_keys": ["process_improvement", "vendor_management", "operations_management", "logistics"],
        "common_skill_keys": ["process_design", "vendor_coordination", "cost_management",
                               "quality_control", "coordination"],
        "is_core_overrides": {"process_improvement": True, "operations_management": True},
    },
    "sales": {
        "core_skill_keys": ["lead_generation", "account_management", "negotiation", "crm_management"],
        "common_skill_keys": ["communication", "negotiation_basic", "crossfunctional_collab",
                               "forecasting", "pipeline_management"],
        "is_core_overrides": {"lead_generation": True, "account_management": True},
    },
    "design": {
        "core_skill_keys": ["ui_design", "prototyping", "design_systems", "user_research"],
        "common_skill_keys": ["communication", "stakeholder_management", "wireframing",
                               "accessibility", "presentation"],
        "is_core_overrides": {"ui_design": True, "prototyping": True},
    },
    "finance": {
        "core_skill_keys": ["financial_modeling", "budgeting_advanced", "accounting", "financial_reporting"],
        "common_skill_keys": ["excel", "reporting", "budgeting", "cost_management", "tax_compliance"],
        "is_core_overrides": {"financial_modeling": True, "accounting": True},
    },
    "engineering": {
        "core_skill_keys": ["software_development", "code_review", "system_design", "debugging"],
        "common_skill_keys": ["documentation", "problem_solving", "api_design",
                               "testing_qa", "crossfunctional_collab"],
        "is_core_overrides": {"software_development": True, "system_design": True},
    },
    "customer_success": {
        "core_skill_keys": ["customer_onboarding", "churn_management", "support_ticketing", "account_health"],
        "common_skill_keys": ["communication", "stakeholder_management", "customer_feedback_analysis",
                               "renewal_management", "data_analysis"],
        "is_core_overrides": {"customer_onboarding": True, "churn_management": True},
    },
}

# label_ko, description은 07_SKILL_TAXONOMY.md에서 조회 (생략, 실제로는 lookup table 사용)

for family, config in JOB_FAMILIES.items():
    requirements = allocate_weights(config["core_skill_keys"], config["common_skill_keys"])
    for req in requirements:
        req.is_core = config["is_core_overrides"].get(req.requirement_key, False)
    validate_job_family_weights(requirements)  # 06_SCORING_RULES.md §2.4

    output_path = Path(f"data/job_requirements_{family}.json")
    output_path.write_text(json.dumps([r.dict() for r in requirements], ensure_ascii=False, indent=2))
    print(f"{family}: UNIQUE={sum(r.weight for r in requirements if r.skill_group=='UNIQUE')}, "
          f"COMMON={sum(r.weight for r in requirements if r.skill_group=='COMMON')}")
```

### 완료 기준

- [ ] `data/job_requirements_*.json` 10개 생성
- [ ] 10개 전부 `validate_job_family_weights()` 통과 (UNIQUE=0.65, COMMON=0.35, ±0.001)
- [ ] `product`와 `design`의 `user_research` 중복 지정 확인 (07_SKILL_TAXONOMY.md §0 원칙 3 — 의도된 설계)
- [ ] `data/gap_recommendations.json` — 79개 skill_key 전체에 대한 추천 문구 작성 (08_EVIDENCE_RULES.md 커버리지와 1:1)

---

## Day 7 — Sample Input + Sample Report (HR, Data — 손작성)

### 오전: `output/sample_input_hr.json`, `output/sample_input_data.json`

각 Job Family당 경력 2개, `08_EVIDENCE_RULES.md`의 EXPLICIT/INFERRED/ACHIEVED 키워드가  
풍부하게 들어간 실제와 같은 텍스트로 작성한다. (이전 대화에서 작성한 `sample_input_hr.json` 재사용 가능)

### 오후: `output/sample_report_hr.json`, `output/sample_report_data.json` — **손으로 직접 작성**

> Week 1의 진짜 핵심 산출물. 엔진 없이 사람이 직접 채운 "정답".

작업 순서:
```
1. sample_input_*.json의 responsibilities/achievements를 읽는다
2. 08_EVIDENCE_RULES.md 매핑표로 evidences[] 직접 추출 (confidence_total 계산 포함)
3. 06_SCORING_RULES.md §4 알고리즘으로 matchLevel 수작업 결정
4. job_requirements_hr.json / job_requirements_data.json의 weight로 점수 계산
   (06_SCORING_RULES.md §5 예시와 동일한 방식 — unique_total/common_total/core_penalty/total)
5. 05_REPORT_SCHEMA.md 12개 top-level key 전부 값 채우기
```

### 완료 기준

- [ ] `sample_input_hr.json`, `sample_input_data.json` 완성
- [ ] `sample_report_hr.json`, `sample_report_data.json` — 12개 key 전부 실제 값, null 없음
- [ ] 두 sample_report에 **`05_REPORT_SCHEMA.md` 부록의 구조 검증 스크립트** 실행 → 키 집합 100% 동일
- [ ] `sample_report_hr.json.scores.total == unique_total + common_total` 등 06_SCORING_RULES.md §10 불변규칙 10개 전부 수동 검증

### Week 1 최종 마감 체크리스트

```
[ ] docs/00~12 (13개 중 12개) 확정          ← 이미 완료
[ ] data/job_requirements_*.json × 10       ← Day 6
[ ] data/gap_recommendations.json (79 skills) ← Day 6
[ ] sample_input_hr/data.json                ← Day 7
[ ] sample_report_hr/data.json (손작성 정답)  ← Day 7
[ ] 구조 통일성 검증 통과                     ← Day 7
```

**이 시점 체감 완성도: 약 35%** (문서 작업이 v2에서 더 무거워진 만큼 기준 상향)

---

---

# WEEK 2 — Engine Week

**목표:** `sample_input_*.json` → (엔진) → Day 7의 `sample_report_*.json`과 거의 일치하는 결과를 코드가 자동 생성한다.

**버퍼 전략:** Day 14는 통합 검증일. 막힐 경우 Week 3 Day 15(Text Template, 코드량 적음)와 순서 교체 가능.

---

## Day 8 — Evidence Extractor

### 작업: `engine/evidence_extractor.py`

```python
def extract_evidences(career_history: CareerHistory) -> list[Evidence]:
    """08_EVIDENCE_RULES.md §6 의사코드 그대로 구현. 79개 skill_key 전체 매핑 dict 로드."""
```

### 구현 순서
1. `08_EVIDENCE_RULES.md` §3~5의 EXPLICIT/INFERRED/ACHIEVED 매핑을 `data/evidence_rules.json`으로 분리
2. 문장 분리 (`.` `\n` 기준)
3. 키워드 매칭 → Evidence 생성 (§6 의사코드)
4. `confidence_score < 0.5` 필터링, 중복 제거 (§7 불변규칙)

### 검증
```bash
python scripts/test_engine.py --step evidence --input output/sample_input_hr.json
# diff 비교: 추출 결과 vs sample_report_hr.json.evidenceMapping
```

### 완료 기준
- [ ] `sample_input_hr.json` → evidences[] 최소 8개 추출
- [ ] `sample_report_hr.json.evidenceMapping`과 skill_key 기준 80% 이상 일치
- [ ] `sample_input_data.json`도 동일 테스트 통과
- [ ] EXPLICIT+ACHIEVED 동시 존재 케이스(예: recruiting)에서 둘 다 보존되는지 확인 (중복 제거 로직이 evidence_type 다른 건 살리는지)

---

## Day 9 — Requirement Matching + confidence_total

### 작업: `engine/requirement_matcher.py`

```python
def match_requirements(
    evidences: list[Evidence],
    requirements: list[Requirement]  # data/job_requirements_<family>.json에서 로드
) -> list[RequirementMatch]:
    """06_SCORING_RULES.md §4 determine_match_level() 사용.
       반환값에 confidence_total 포함 (04_PAYLOAD_CONTRACT.md §2 Algorithm Response 필드)."""
```

`06_SCORING_RULES.md` §4의 `determine_match_level()`을 그대로 구현한다 (이미 알고리즘 확정됨 — 신규 작성 아님).

### 완료 기준
- [ ] HR 9개 requirement 전부 matchLevel + confidence_total 산출
- [ ] `06_SCORING_RULES.md` §5 예시 표(recruiting=FULL/1.9, labor_law=NONE/0.0 등)와 일치
- [ ] `sample_report_hr.json.skillMapping`과 매칭 결과 비교 → 불일치 시 둘 중 하나 수정

---

## Day 10 — Scoring Engine (UNIQUE/COMMON 분리 + Core Penalty)

### 작업: `engine/scoring_engine.py`

```python
def calculate_score(matches: list[RequirementMatch], requirements: list[Requirement]) -> ScoreResult:
    """
    06_SCORING_RULES.md §1, §6 구현.
    - unique_total, common_total 분리 계산
    - apply_core_penalty() 적용 (penalty는 unique_total에서만 차감)
    - calculate_final_scores()로 최종 total 산출
    """
```

### 결정론적 검증 (필수)
```bash
for i in 1 2 3; do
  python scripts/test_engine.py --step score --input output/sample_input_hr.json | grep -E "total|unique|common|penalty"
done
# 3회 동일 값 확인
```

### 완료 기준
- [ ] HR/Data 각각 `total`, `unique_total`, `common_total`, `core_penalty` 산출
- [ ] `06_SCORING_RULES.md` §5 예시(total=63.0)와 동일한 입력으로 동일 결과 재현
- [ ] 3회 실행 동일 점수
- [ ] §10 불변규칙 1~7 코드 검증 (assert)

---

## Day 11 — Gap Analyzer (skill_group 포함)

### 작업: `engine/gap_analyzer.py`

```python
def analyze_gaps(matches: list[RequirementMatch], requirements: list[Requirement]) -> list[Gap]:
    """
    06_SCORING_RULES.md §8 classify_gap_severity() + assign_priority_order() 구현.
    report_gaps.skill_group 컬럼(03_ERD.md §2.8)에 대응하는 필드 포함.
    """
```

### 완료 기준
- [ ] gaps[] 생성, `skill_group`(UNIQUE/COMMON) 포함, priority_order 정렬 확인
- [ ] `data/gap_recommendations.json`(79개) 전체에서 recommendation 텍스트 조회 성공
- [ ] `sample_report_hr.json.gaps`와 severity 분류 일치 확인
- [ ] COMMON + CRITICAL 조합이 발생하지 않는지 확인 (09_TEXT_TEMPLATE_RULES.md §4 주석)

---

## Day 12 — Recommendation Engine + Strength Selector

### 작업 1: `engine/recommendation_engine.py`

```python
def generate_recommendations(gaps: list[Gap], unique_score: float, job_family: str) -> Recommendations:
    """09_TEXT_TEMPLATE_RULES.md §5 select_mid_term_template() 사용
       (unique_score/65 >= 0.6 기준으로 high/low 템플릿 분기)"""

def generate_roadmap(gaps: list[Gap]) -> Roadmap:
    """3 phase 고정 (05_REPORT_SCHEMA.md §11)"""
```

### 작업 2: `engine/strength_selector.py`

```python
def select_strengths(matches, requirements) -> list[Strength]:
    """06_SCORING_RULES.md §9 select_strengths() 구현.
       FULL/STRONG만 후보, weighted_score 내림차순, 동점시 UNIQUE 우선."""
```

### 완료 기준
- [ ] recommendations.short_term ≥2, mid_term ≥1
- [ ] roadmap 3 phase 전부 생성
- [ ] strengths[] 3개, rank 1·2가 가능한 UNIQUE인지 확인 (sample_report와 비교)

---

## Day 13 — Report Builder (12 top-level keys 조립)

### 작업: `engine/report_builder.py`

```python
def build_report(normalized_input, evidences, matches, score, gaps, strengths, recommendations, roadmap) -> dict:
    return {
        "meta": build_meta(report_id, job_family, engine_version="2.0.0"),
        "summary": build_summary(score, matches, gaps, strengths),  # unique_score/common_score 포함
        "careerProfile": build_career_profile(normalized_input, evidences),
        "targetJobAnalysis": build_target_job(requirements, matches),  # unique/common_requirements 분리
        "skillMapping": build_skill_mapping(matches, requirements),
        "evidenceMapping": build_evidence_mapping(evidences),
        "scores": score.dict(),  # unique_total, common_total, core_penalty 포함
        "strengths": [s.dict() for s in strengths],
        "gaps": [g.dict() for g in gaps],
        "recommendations": recommendations.dict(),
        "roadmap": roadmap.dict(),
        "reportSections": DEFAULT_12_SECTIONS  # 10_PDF_TEMPLATE_SPEC.md §2
    }
```

### 완료 기준
- [ ] `python scripts/test_engine.py --input output/sample_input_hr.json --output output/generated_report_hr.json` 실행 성공
- [ ] `generated_report_hr.json`이 `05_REPORT_SCHEMA.md`의 12개 top-level key 전부 포함, null 없음
- [ ] `summary.unique_score + summary.common_score == summary.total_score`

---

## Day 14 — 통합 검증 (버퍼 데이)

### E2E 테스트

```bash
for family in hr data; do
  python scripts/test_engine.py \
    --input output/sample_input_${family}.json \
    --output output/generated_report_${family}.json
done
```

### 검증 체크리스트

```
[ ] 2개 Job Family 전부 generated_report 생성 성공
[ ] generated_report.json 구조(key) == sample_report.json 구조(key) — 05_REPORT_SCHEMA.md 부록 스크립트로 검증
[ ] generated_report_hr.json 구조 == generated_report_data.json 구조 (Job Family 무관 통일성)
[ ] 0 < total_score < 100, 0 <= unique_total <= 65, 0 <= common_total <= 35
[ ] evidences ≥ 5개, gaps ≥ 1개, recommendations ≥ 2개
[ ] 3회 실행 동일 결과 (결정론적)
[ ] 06_SCORING_RULES.md §10 불변규칙 10개 전부 통과
[ ] LLM 없이 완성 (이 시점에 LLM 코드 없음 — 자연히 충족)
```

### 버퍼 규칙
- 위 체크리스트가 Day 14 안에 끝나면 → Week 3 Day 15(Text Template) 선작업 시작
- 끝나지 않으면 → Day 15를 통합 검증 마무리로 쓰고, Day 21(Deploy)은 고정한 채 Day 20(React 디자인 다듬기)을 축소해 흡수

### Week 2 마감 체크리스트

```
[ ] sample_input_*.json → generated_report_*.json 자동 생성 파이프라인 완성
[ ] 결정론적 검증 통과
[ ] HR, Data 2개 Job Family 모두 통과
[ ] (선택) 나머지 8개 Job Family도 job_requirements_*.json만 바꿔 끼워서 generated_report 생성 시도
    → 에러 없이 생성되면 "Structure-Once, Scale-Many" 원칙이 코드 레벨에서도 검증된 것
```

**이 시점 체감 완성도: 약 65%**

---

---

# WEEK 3 — Product Week

**목표:** 사용자 입력 → Report JSON → PDF → 웹 다운로드 전체 흐름이 실제 URL에서 동작한다.

---

## Day 15 — Text Template Engine

### 작업: `engine/text_template.py`

`09_TEXT_TEMPLATE_RULES.md` §1~6 전체 구현:

```python
SUMMARY_TEMPLATES = {...}          # §1
SCORE_SPLIT_TEMPLATES = {...}      # §2 (v2 신규 — unique/common 분리 서술)
STRENGTH_HEADLINE_TEMPLATES = {...}# §3
GAP_HEADLINE_TEMPLATES = {...}     # §4
RECOMMENDATION_TEMPLATES = {...}   # §5
CONCLUSION_TEMPLATES = {...}       # §6

def polish_text(template_text: str) -> str:
    try:
        return llm_polish(template_text)
    except Exception:
        return template_text  # 폴백 (§7)
```

### 완료 기준
- [ ] LLM 없이 `generated_report_*.json`의 모든 텍스트 필드(`summary.one_line`, `strengths[].headline/detail`, `gaps[].headline/detail`, `recommendations`, conclusion) 채워짐
- [ ] `select_split_template()`(§2)이 HR과 Data 양쪽에서 정상 동작 — unique_ratio/common_ratio 기준 4분류 중 올바른 템플릿 선택
- [ ] LLM 폴백 구조 작성 (실제 LLM 연동은 선택)

---

## Day 16 — HTML Renderer (12 섹션 + UNIQUE/COMMON 시각화)

### 작업: `10_PDF_TEMPLATE_SPEC.md` §4 템플릿 구조 그대로 생성

```
backend/pdf/templates/
├── report.html.j2
├── partials/  (12개 — cover ~ final_assessment)
└── static/report.css  (--color-unique, --color-common 등 CSS 변수, §3)
```

`summary.html.j2`에 도넛 차트 2개(unique_score/65, common_score/35), `target_job.html.j2`에 2개 테이블(UNIQUE/COMMON 헤더 색상 구분) 구현.

### 완료 기준
- [ ] `output/sample_report_hr.html` 생성, 브라우저에서 12섹션 확인
- [ ] `sample_report_data.html`도 동일 템플릿으로 정상 렌더링 (구조 통일성 재확인)
- [ ] UNIQUE 배지(#2B6CB0)와 COMMON 배지(#90CDF4)가 Section 3~10에서 일관되게 표시되는지 확인

---

## Day 17 — PDF Engine

### 작업: `backend/pdf/generator.py` (Playwright)

```python
def generate_pdf(html_content: str, output_path: str) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content)
        page.pdf(path=output_path, format="A4",
                 margin={"top":"20mm","bottom":"20mm","left":"20mm","right":"20mm"},
                 print_background=True)
        browser.close()
```

### 완료 기준
- [ ] `output/sample_report_hr.pdf`, `output/sample_report_data.pdf` 생성
- [ ] A4 기준 12~20페이지 (12섹션 기준, 13섹션 대비 약간 축소)
- [ ] 색상이 인쇄 시(흑백 시뮬레이션)에도 UNIQUE/COMMON 텍스트 라벨로 구분 가능한지 확인 (10_PDF_TEMPLATE_SPEC.md §2 Section 5 주의사항)

---

## Day 18 — FastAPI

### 3개 엔드포인트 (`11_API_SPEC.md` 기반)

```python
POST /reports                  # CREATED 반환, background task로 엔진 실행
GET  /reports/{report_id}      # 상태/결과 반환
GET  /reports/{report_id}/pdf  # PDF 반환
```

`target_job_family` 검증 시 10개 ENUM(`04_PAYLOAD_CONTRACT.md` §1) 체크 → `INVALID_JOB_FAMILY` 에러 처리.

### 완료 기준
- [ ] `uvicorn main:app --reload` 정상 동작
- [ ] curl로 3개 엔드포인트 E2E 테스트 (HR로 생성 → 폴링 → PDF)
- [ ] 잘못된 job_family("ACCOUNTING" 등) 입력 시 400 + `INVALID_JOB_FAMILY` 확인

---

## Day 19 — Supabase 연동

### 작업
1. `03_ERD.md` migration 실행 (ENUM 6종: report_status, job_family(10), evidence_type, skill_group, match_level, gap_severity + 테이블 8개)
2. `job_requirement_stats` 시딩 — Day 6에서 생성한 `data/job_requirements_*.json` 10개 전부 INSERT
3. 시딩 후 `03_ERD.md` §2.5 weight 합계 검증 쿼리 실행 → 10개 Job Family 전부 UNIQUE=0.65, COMMON=0.35 확인
4. FastAPI에서 Supabase client 연동, report 상태 저장

### 완료 기준
- [ ] `POST /reports` → DB 레코드 생성 확인
- [ ] 엔진 완료 후 `reports.report_json` 저장 확인 (`reports.target_job_family` ENUM 10개 값 모두 INSERT 가능한지 확인)
- [ ] `report_scores`(unique_total/common_total/core_penalty 컬럼 포함), `requirement_matches`(skill_group, confidence_total 포함), `report_gaps`(skill_group 포함) 정규화 저장 확인

---

## Day 20 — React (Form + Result)

### 3개 페이지

```
/             — Landing (10개 Job Family 그리드, HR/Data 샘플 미리보기)
/report/new   — 입력 폼 (target_job_family select 10개 옵션, career_histories 동적 추가)
/report/:id   — Generating(폴링) → Result(UNIQUE/COMMON 점수 분리 표시) → PDF 다운로드
```

### 완료 기준
- [ ] Form 제출 → report_id 받음 → Generating 화면
- [ ] 폴링으로 READY 전환 → Result 화면에 `summary.unique_score`/`common_score` 도넛 2개 렌더링
- [ ] PDF 다운로드 버튼 동작
- [ ] 10개 Job Family select 옵션이 `04_PAYLOAD_CONTRACT.md` ENUM과 정확히 일치

---

## Day 21 — Bug Fix + Deploy

### 오전: Bug Fix

```
[ ] career_histories 1개 / 10개 엣지 케이스
[ ] responsibilities 50자 최소값 검증
[ ] LLM 실패 시 폴백 동작 확인 (09_TEXT_TEMPLATE_RULES.md §7)
[ ] PDF 생성 실패 시 에러 응답 확인
[ ] 10개 Job Family 중 HR/Data 외 나머지 8개도 최소 1회 생성 테스트 (job_requirements json만 다르므로 에러 시 즉시 발견 가능해야 함)
[ ] CORS 설정
```

### 오후: Deploy

```bash
# Frontend
cd frontend && vercel --prod

# Backend (render.yaml — playwright install chromium 빌드 커맨드 포함 필수)
```

### 환경변수 체크리스트

```
SUPABASE_URL
SUPABASE_SERVICE_KEY
OPENAI_API_KEY (optional)
FRONTEND_URL (CORS)
```

### Week 3 마감 = 프로젝트 완료 체크리스트

```
[ ] 실제 URL 접속 가능
[ ] HR/Data 둘 다 리포트 생성 → PDF 다운로드 성공
[ ] 생성 소요 시간 5분 이내
[ ] 동일 입력 재실행 시 동일 점수 (배포 환경에서도 재검증)
[ ] 10개 Job Family select에서 임의의 항목 선택 시 에러 없이 리포트 생성 (job_requirements json 10종이 모두 유효함을 실증)
```

**이 시점 체감 완성도: 100% (V1 MVP, 10 Job Families)**

---

---

# 부록 A: v2 → v3 변경 요약

| 항목 | v2 | v3 |
|------|----|----|
| Job Family | 2개 (HR, Data) | **10개**, weight는 알고리즘으로 자동 배분 |
| Skill Taxonomy | ~39개 (HR+Data 전용) | **~79개** (공통 20 + 고유 40 + 보조 21) |
| weight 정의 방식 | 사람이 9개 직접 입력 | **`core_skill_keys` 4~5개만 입력 → 자동 배분 (65/35)** |
| Report Schema 신규 필드 | - | `skill_group`, `confidence_total`, `unique_score`, `common_score`, `unique_total`, `common_total`, `core_penalty` |
| reportSections | 13개 | **12개** (marketAnalysis 제외, V1.1로) |
| Week 1 산출물 상태 | 작성 예정 | **00~12 중 12개 문서 이미 완료** |
| Day 1~5 | Vision~Evidence Rules 작성 | **완료됨 — 이 로드맵에서 제외** |
| Day 6 (신규) | - | 10개 Job Family requirement DB 생성 (알고리즘 1회 실행) |

---

# 부록 B: 매일 자가 점검

```
1. 오늘 작업이 04_PAYLOAD_CONTRACT.md 또는 05_REPORT_SCHEMA.md를 건드리는가?
   → 그렇다면 문서부터 수정했는가? (.cursorrules Rule 10)
2. sample_report_hr.json과 sample_report_data.json의 구조가 여전히 동일한가?
3. 오늘 추가한 코드가 결정론적인가? (06_SCORING_RULES.md §10)
4. original_text를 수정한 코드가 없는가?
5. UNIQUE/COMMON weight 합이 65/35를 유지하는가?
6. 새 Job Family(11번째 이상)를 추가하고 싶은 유혹이 들지 않았는가? (V1.1로 미룰 것)
```