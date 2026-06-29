# 13 — Development Roadmap (v3)

> **현재 상태:**  
> - `docs/00~13` (14개) 전체 v3.1 primary_profile 체계로 재정리  
> - `data/skill_taxonomy.json` (80개), `data/job_requirements_*.json` × 10 생성 완료 (Day 6 산출물)  
> - `scripts/generate_requirements.py` — weight 자동 배분 + 검증 완료 (10/10 통과)  
>
> **다음 작업:** Day 7 (sample_input/report 손작성 — dominant, mixed, LOW)

---

# WEEK 1 (잔여) — Day 7

## Day 7 — Sample Input + Sample Report (primary_profile 기준)

### 두 케이스를 손으로 작성하는 이유

v3.1에서 모든 입력은 `primary_profile`을 선택하고 report_json을 생성한다. Week 2 엔진 검증을 위해  
**"정답 fixture" 역할을 하는 케이스**가 필요하다:

| 케이스 | 파일명 | 특징 |
|--------|--------|------|
| Dominant | `output/sample_input_*_dominant.json` | 해당 primary_profile의 UNIQUE skill 4개 이상 커버 |
| Mixed | `output/sample_input_*_mixed.json` | primary_profile 1개 + secondary_profiles 1~2개 |
| LOW | `output/sample_input_low_confidence.json` | evidence_count 0~4, fallback_profile로 리포트 생성 |

### 작업 순서

```
1. sample_input 작성 (career_histories + target_priority_text)
2. 08_EVIDENCE_RULES.md로 evidences[] 수작업 추출
3. user_vector 계산 ({skill_key: confidence_total})
4. 06_SCORING_RULES.md §2.5 알고리즘으로 primary_profile 선택
5. selected_requirements 도출 (primary_profile requirement)
6. matchLevel 결정 (06_SCORING_RULES.md §4)
7. 점수 계산 (unique_total, common_total, core_penalty, total)
8. 05_REPORT_SCHEMA.md 12개 top-level key 전부 실제 값으로 채움
```

### 완료 기준

```
[ ] sample_input_hr_dominant.json + sample_report_hr_dominant.json
    - primary_profile: "hr"
    - meta.confidence_level: HIGH
    - 12개 top-level key 전부 실제 값, null 없음

[ ] mixed fixture + sample_report
    - primary_profile 1개 명확
    - secondary_profiles 1~2개 명확
    - summary.primary_profile_summary 템플릿 적용

[ ] low_confidence fixture + sample_report
    - confidence_level: LOW
    - evidence_count 0~4
    - warning_message 필수
    - report_json 생성 성공

[ ] 두 report의 key 구조 동일 (05_REPORT_SCHEMA.md 부록 검증 스크립트 통과)
[ ] unique_total + common_total == total (각 케이스)
[ ] primary_profile expected 값 일치 (각 케이스)
[ ] Σ selected_requirements weight (UNIQUE) == 0.65 (각 케이스)
[ ] Σ selected_requirements weight (COMMON) == 0.35 (각 케이스)
```

---

# WEEK 2 — Engine Week

**목표:** `sample_input_*.json` → (엔진) → Day 7의 sample_report와 구조 일치하는 결과 자동 생성.  
**v3.1 추가:** `profile_selector.py`를 Day 8에 먼저 완성하고, 나머지 모듈이 임포트.

---

## Day 8 — profile_selector.py (v3.1 핵심 신규)

### 작업: `scripts/profile_selector.py`

`06_SCORING_RULES.md` §2.5~2.6의 모든 함수를 구현한다.

```python
score_profile_signal(user_vector, requirements) -> float
detect_profile_hint(target_priority_text, profile_pool) -> str | None
select_primary_profile(user_vector, target_priority_text, profile_pool) -> tuple[str, list[str]]
select_requirements(primary_profile, profile_pool) -> list[Requirement]
determine_confidence_level(evidence_count) -> str
build_warning_message(confidence_level) -> str | None
```

### 단위 테스트 (수작업 케이스로 검증)

```bash
python scripts/profile_selector.py \
  --user_vector '{"recruiting": 1.9, "training_and_onboarding": 1.85, "payroll": 1.9}' \
  --profile_pool data/

# 예상 출력:
# primary_profile = "hr"
# secondary_profiles = [...]
# confidence_level = HIGH|MEDIUM|LOW
# Σ selected weight (UNIQUE) = 0.65 ✓
# Σ selected weight (COMMON) = 0.35 ✓
```

### 완료 기준

```
[ ] select_primary_profile — 동일 입력 3회 동일 결과
[ ] HR dominant → primary_profile="hr"
[ ] MIXED → primary_profile + secondary_profiles 일치
[ ] LOW → confidence_level="LOW", fallback_profile="operations" 가능
[ ] selected_requirements 합계 UNIQUE=0.65, COMMON=0.35
```

---

## Day 9 — Evidence Extractor (듀얼 소스)

### 작업: `engine/evidence_extractor.py`

```python
def extract_evidences_from_all_sources(
    career_histories: list[CareerHistory],
    target_priority_text: str
) -> list[Evidence]:
    """08_EVIDENCE_RULES.md §6 의사코드 구현. 듀얼 소스."""
```

### 완료 기준

```
[ ] career_histories에서 EXPLICIT/INFERRED/ACHIEVED 추출
[ ] target_priority_text에서 EXPLICIT/INFERRED만 추출 (ACHIEVED 제외)
[ ] 동일 (skill_key, original_text, evidence_type) 중복 제거
[ ] career_history_id=NULL인 Evidence의 source="target_priority_text" 확인
[ ] sample_input_hr_dominant → evidences 최소 8개 (target_priority_text 기여분 포함)
[ ] sample_input_mixed → evidences 최소 6개 (Marketing+Data 혼합 신호)
```

---

## Day 10 — Requirement Matcher + Scoring (primary_profile 기반)

### 작업: `engine/requirement_matcher.py`, `engine/scoring_engine.py`

```python
def match_requirements(evidences, selected_requirements) -> list[RequirementMatch]:
    """06_SCORING_RULES.md §4 determine_match_level() 사용.
       selected_requirements의 weight를 그대로 사용."""

def calculate_score(matches, selected_requirements) -> ScoreResult:
    """06_SCORING_RULES.md §1, §6 구현. primary_profile 65/35 불변."""
```

### 완료 기준

```
[ ] HR dominant: unique_total + common_total == total (±0.1)
[ ] LOW: confidence_level=LOW여도 점수 계산 성공
[ ] 3회 실행 동일 점수 (결정론)
[ ] 06_SCORING_RULES.md §10 불변규칙 1~12 assert 통과
[ ] 분석 차단 상태 enum 또는 분석 차단 경로 없음
```

---

## Day 11 — Gap Analyzer + Strength Selector

### 작업: `engine/gap_analyzer.py`, `engine/strength_selector.py`

```python
def analyze_gaps(matches, selected_requirements) -> list[Gap]:
    """06_SCORING_RULES.md §8. primary_profile requirement 기준."""

def select_strengths(matches, selected_requirements) -> list[Strength]:
    """06_SCORING_RULES.md §9. UNIQUE 우선."""
```

### 완료 기준

```
[ ] MIXED 케이스에서 secondary_profiles가 gap severity를 변경하지 않음
[ ] is_core는 primary_profile registry 기준
[ ] COMMON + CRITICAL 조합 없음 (불변규칙 확인)
[ ] strengths rank 1, 2가 가능하면 UNIQUE
```

---

## Day 12 — Skill Intelligence + Narrative Template Layer

### 작업: `engine/text_template.py`

`09_TEXT_TEMPLATE_RULES.md` §1~9 전체 구현. Day 12는 Evidence를 바꾸는 작업이 아니라,
이미 계산된 Evidence/strength/gap/score를 사람이 읽고 공감할 수 있는 Career Narrative로 설명하는 레이어다.

```python
build_primary_profile_summary(primary_profile, secondary_profiles, confidence_level) -> str
build_low_confidence_warning(confidence_level, evidence_count) -> str | None
select_split_template(unique_score, common_score) -> str
# strengths/gaps/skill_explanations/skill_narratives 템플릿 전부 포함
build_skill_explanations(strengths, gaps, selected_requirements, primary_profile) -> list[dict]
build_skill_narratives(summary, strengths, gaps, skill_explanations, primary_profile) -> dict
polish_text(template_text) -> str  # LLM 폴백 구조 포함
```

### 완료 기준

```
[ ] HR dominant → primary_profile_summary 템플릿
[ ] MIXED → primary_profile + secondary_profiles 설명
[ ] LOW → warning_message 필수
[ ] skill_explanations 생성 (career_context, market_context, development_direction)
[ ] skill_narratives 생성 (career_context, market_context, development_direction, job_outlook, final_assessment)
[ ] LLM 없이 모든 텍스트 필드 채워짐 (폴백 동작)
[ ] LLM은 선택적 윤색만 수행하고 score/Evidence/strength/gap/순서 변경 없음
[ ] Evidence 모델 변경 없음
[ ] expected_score_gain/difficulty/time_estimate 생성 없음
[ ] priority_clause: target_priority_text 유래 강점에만 추가
```

---

## Day 13 — Report Builder (12 top-level keys 조립)

### 작업: `engine/report_builder.py`

```python
def build_report(
    report_id, target_priority_text,
    evidences, user_vector, primary_profile, secondary_profiles, selected_requirements,
    matches, score, gaps, strengths, skill_explanations, skill_narratives,
    weight_source="MANUAL_V1"
) -> dict:
    return {
        "meta": build_meta(report_id, primary_profile, secondary_profiles, weight_source, confidence_level),
        "summary": build_summary(score, matches, primary_profile, ...),
        "careerProfile": build_career_profile(career_histories, evidences),
        "targetJobAnalysis": build_target_job(primary_profile, selected_requirements, matches),
        "skillMapping": build_skill_mapping(matches, selected_requirements),
        "evidenceMapping": build_evidence_mapping(evidences),
        "scores": score.dict(),
        "strengths": [s.dict() for s in strengths],
        "gaps": [g.dict() for g in gaps],
        "skill_explanations": skill_explanations,
        "skill_narratives": skill_narratives,
        "reportSections": DEFAULT_12_SECTIONS,
    }
```

### 완료 기준

```
[ ] HR dominant + MIXED + LOW 각각 generated_report.json 자동 생성 성공
[ ] meta.primary_profile 포함
[ ] targetJobAnalysis.unique_requirements[].source_profiles 포함
[ ] evidenceMapping에 source="target_priority_text" 항목 포함
[ ] summary.primary_profile_summary, LOW warning 정확
[ ] skill_explanations/skill_narratives 포함
[ ] recommendations/roadmap/expected_score_gain/difficulty/time_estimate 미생성
```

---

## Day 14 — 통합 검증 (버퍼)

### E2E 검증

```bash
for case in hr_dominant mixed; do
  python scripts/test_engine.py \
    --input output/sample_input_${case}.json \
    --output output/generated_report_${case}.json
done
```

### 검증 체크리스트

```
[ ] 2개 케이스 generated_report 생성 성공
[ ] generated_report 구조 == sample_report 구조 (05_REPORT_SCHEMA.md 부록 스크립트)
[ ] HR dominant: primary_profile = "hr"
[ ] MIXED: primary_profile + secondary_profiles 정확
[ ] LOW: confidence_level=LOW, warning_message 포함
[ ] 06_SCORING_RULES.md §10 불변규칙 전부 assert 통과
[ ] 3회 실행 동일 결과 (결정론)
[ ] LLM 없이 완성 (이 시점 LLM 연동 없음)
[ ] selected UNIQUE Σ == 0.65, COMMON Σ == 0.35 (각 케이스)
[ ] (선택) 나머지 8개 좌표축 조합으로 임의 입력 생성 후 에러 없이 report 생성 확인
```

### 버퍼 규칙

- Day 14 안에 완료 → Day 15(Text Template) 선작업
- 완료 안 되면 → Day 20(React 디자인 마감) 축소해 흡수

---

# WEEK 3 — Product Week

## Day 15 — HTML Renderer (primary_profile 표시 포함)

```
backend/pdf/templates/
├── report.html.j2
├── partials/
│   ├── summary.html.j2      ← primary_profile_summary + LOW warning
│   ├── target_job.html.j2   ← primary_profile + source_profiles 보조 배지
│   └── (나머지 10개)
└── static/report.css        ← --color-warning, --color-source-badge 추가
```

### 완료 기준

```
[ ] output/sample_report_hr_dominant.html — Section 2에 Primary Profile Selection 박스
[ ] output/sample_report_mixed.html — Section 2에 primary + secondary 설명
[ ] LOW report — warning banner 확인
[ ] 흑백 출력 시에도 UNIQUE/COMMON 텍스트 라벨로 구분 가능
```

---

## Day 16 — PDF Engine

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

```
[ ] output/sample_report_hr_dominant.pdf 생성
[ ] output/sample_report_mixed.pdf 생성
[ ] 10_PDF_TEMPLATE_SPEC.md §5 Limitations — 가변 행 수 레이아웃 확인 (최대 8행 초과 테스트)
```

---

## Day 17 — FastAPI

### 3개 엔드포인트 (`11_API_SPEC.md` 기반)

```python
POST /reports      # target_priority_text 필수, target_job_family 없음
                   # LOW도 201/READY 리포트 생성
GET  /reports/{id} # primary_profile 포함 응답
GET  /reports/{id}/pdf
```

### 완료 기준

```
[ ] target_job_family 필드 전송해도 무시 (하위 호환)
[ ] target_priority_text 30자 미만 → VALIDATION_ERROR
[ ] LOW 입력도 422 없이 생성 진행
[ ] confidence_level="LOW" + warning_message 포함
[ ] GET 응답에 primary_profile 포함 확인
```

---

## Day 18 — Supabase 연동

### 작업

1. `03_ERD.md` v3 migration 실행 (ENUM 6종 → job_requirement_profiles 테이블 포함)
2. `data/job_requirements_*.json` 10개 → `job_requirement_profiles` 테이블 시딩
3. 시딩 후 weight 합계 검증 쿼리 실행 (UNIQUE=0.65, COMMON=0.35 × 10개 profile_key)
4. `reports.primary_profile`, `reports.secondary_profiles`, `reports.confidence_level` 저장 확인

### 완료 기준

```
[ ] job_requirement_profiles: 10개 profile_key × 9개 requirement = 90행
[ ] weight 합계 검증 쿼리: 10개 전부 UNIQUE=0.65, COMMON=0.35
[ ] reports.primary_profile 저장 확인
[ ] career_evidences: source 컬럼, career_history_id nullable FK 확인
[ ] LOW confidence의 경우 reports 테이블에 confidence_level='LOW' 저장 확인
```

---

## Day 19 — React

### 3개 페이지 (v3)

```
/             Landing (예시 카드 5~6개, Job Family 그리드 없음)
/report/new   Form (target_priority_text textarea, career_histories, select 없음)
              LOW 입력도 제출 가능, 보완 안내는 사전 도움말로만 표시
/report/:id   Result → primary_profile_summary 표시
              confidence_level=LOW → 안내 배너
              PDF 다운로드 버튼
```

### 완료 기준

```
[ ] Landing에 "직무 선택 없이 자유롭게 입력" UX 전달
[ ] Form: target_priority_text textarea + 최소 30자 가이드
[ ] Form: LOW 입력도 차단 없이 제출
[ ] Result: meta.primary_profile 표시
[ ] Result: confidence_level=LOW → 배너 표시
[ ] PDF 다운로드 동작
```

---

## Day 20 — Bug Fix + Deploy

### 오전: Bug Fix

```
[ ] target_priority_text 30자 경계값 테스트
[ ] career_histories 1개 / 10개 엣지 케이스
[ ] user_vector가 거의 zero vector인 경우 LOW 리포트 생성 확인
[ ] LLM 실패 시 폴백 동작 (09_TEXT_TEMPLATE_RULES.md §8)
[ ] primary_profile fallback이 결정론적으로 선택되는지 확인
[ ] CORS 설정
[ ] MIXED 케이스에서 secondary_profiles 문장이 모든 브라우저에서 정상 렌더링
```

### 오후: Deploy

```bash
cd frontend && vercel --prod
# backend: render.yaml (playwright chromium 빌드 커맨드 포함 필수)
```

### 환경변수 체크리스트

```
SUPABASE_URL
SUPABASE_SERVICE_KEY
OPENAI_API_KEY (optional, LLM polish)
FRONTEND_URL (CORS)
```

### 최종 완료 체크리스트

```
[ ] 실제 URL 접속 가능
[ ] HR dominant 케이스: 리포트 생성 → primary_profile=hr → PDF 다운로드 성공
[ ] MIXED 케이스: 리포트 생성 → primary_profile + secondary_profiles → PDF 다운로드 성공
[ ] 생성 소요 시간 ≤ 5분
[ ] 동일 입력 재실행 시 동일 점수 (배포 환경에서도 결정론 재검증)
[ ] meta.weight_source = "MANUAL_V1" PDF Section 12에 작은 글씨로 표시 확인
```

---

# 부록 A: v2 → v3 변경 요약

| 항목 | v2 | v3 |
|------|----|----|
| 직무 입력 방식 | `target_job_family` ENUM select (10개) | `target_priority_text` 자유 텍스트 |
| Weight 결정 방식 | 선택된 1개 프로필의 고정 weight | 엔진이 선택한 `primary_profile`의 고정 weight |
| Report meta | `target_job_family_ko` | `primary_profile`, `secondary_profiles`, `weight_source`, `confidence_level`, `warning_message` |
| targetJobAnalysis | 1개 프로필의 9개 requirement | primary_profile의 9개 requirement, `source_profiles`는 보조 배지 |
| evidence 소스 | `career_histories`만 | `career_histories` + `target_priority_text` (듀얼) |
| DB | `job_requirement_stats(job_family ENUM)` | `job_requirement_profiles(profile_key TEXT)` |
| ERD | `reports.target_job_family` ENUM | `reports.primary_profile` TEXT |
| 신규 엔진 모듈 | 없음 | `scripts/profile_selector.py` |
| sample fixture | HR, Data 각 1종 | HR dominant, MIXED 각 1종 |

---

# 부록 B: 매일 자가 점검

```
1. 오늘 작업이 04 또는 05를 건드리는가? → 문서 먼저 수정했는가?
2. selected_requirements의 Σ UNIQUE == 0.65, Σ COMMON == 0.35인가?
3. primary_profile이 유효한 profile key인가?
4. confidence_level이 HIGH|MEDIUM|LOW만 사용하는가?
5. original_text를 수정한 코드가 없는가?
6. 동일 입력 → 동일 출력인가? (외부 모델/랜덤 없음)
7. target_job_family ENUM, INVALID_JOB_FAMILY가 코드에 남아있지 않은가?
8. N을 10보다 늘리고 싶은 유혹이 들지 않았는가? (데이터 없이 확장 금지)
```

---

# 알려진 문제점 (§ Limitations — 전체 로드맵 관점)

| 문제 | 영향 | 비고 |
|------|------|------|
| Day 8(profile_selector.py)이 Week 2의 모든 후속 모듈의 선행 조건 | Day 8에서 막히면 Day 9~13이 연쇄 지연 | 선택 알고리즘은 순수 산술/규칙 기반이라 빠른 구현 가능 |
| MIXED 케이스 sample_report가 보조 프로필 설명을 포함 | Day 7 작성 기준 혼동 가능 | 점수/갭/추천은 primary_profile 기준임을 고정 |
| LOW 케이스도 PDF까지 생성 | 부정확한 결과 과신 가능 | warning_message 필수 표시 |
