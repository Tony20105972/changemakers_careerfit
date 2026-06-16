# 13 — Development Roadmap (v3)

> **현재 상태:**  
> - `docs/00~13` (14개) 전체 v3 블렌딩 체계로 재작성 완료  
> - `data/skill_taxonomy.json` (80개), `data/job_requirements_*.json` × 10 생성 완료 (Day 6 산출물)  
> - `scripts/generate_requirements.py` — weight 자동 배분 + 검증 완료 (10/10 통과)  
>
> **다음 작업:** Day 7 (sample_input/report 손작성 — HR dominant + MIXED 2종)

---

# WEEK 1 (잔여) — Day 7

## Day 7 — Sample Input + Sample Report (두 케이스 손작성)

### 두 케이스를 손으로 작성하는 이유

v3에서 블렌딩 결과는 입력마다 다르다. Week 2 엔진 검증을 위해  
**"정답 fixture" 역할을 하는 두 케이스**가 필요하다:

| 케이스 | 파일명 | 특징 |
|--------|--------|------|
| HR dominant | `output/sample_input_hr_dominant.json` | user_vector가 HR과 높은 유사도, blend_display_mode=SINGLE |
| MIXED | `output/sample_input_mixed.json` | Marketing + Data 혼합, blend_display_mode=MIXED |

### 작업 순서

```
1. sample_input 작성 (career_histories + target_priority_text)
2. 08_EVIDENCE_RULES.md로 evidences[] 수작업 추출
3. user_vector 계산 ({skill_key: confidence_total})
4. 06_SCORING_RULES.md §2.5 알고리즘으로 profile_blend 수계산
5. blended_requirements 도출 (renormalize_to_65_35)
6. matchLevel 결정 (06_SCORING_RULES.md §4)
7. 점수 계산 (unique_total, common_total, core_penalty, total)
8. 05_REPORT_SCHEMA.md 12개 top-level key 전부 실제 값으로 채움
```

### 완료 기준

```
[ ] sample_input_hr_dominant.json + sample_report_hr_dominant.json
    - profile_blend: {hr: >= 0.7} (SINGLE 케이스)
    - meta.confidence_level: HIGH
    - 12개 top-level key 전부 실제 값, null 없음

[ ] sample_input_mixed.json + sample_report_mixed.json
    - profile_blend: 최댓값 < 0.7 (MIXED 케이스, 예: {marketing: 0.55, data: 0.45})
    - summary.blend_display_mode: "MIXED"
    - blend_description: "MIXED_2" 템플릿 적용

[ ] 두 report의 key 구조 동일 (05_REPORT_SCHEMA.md 부록 검증 스크립트 통과)
[ ] unique_total + common_total == total (각 케이스)
[ ] Σ profile_blend == 1.0 (각 케이스)
[ ] Σ blended_requirements weight (UNIQUE) == 0.65 (각 케이스)
[ ] Σ blended_requirements weight (COMMON) == 0.35 (각 케이스)
```

---

# WEEK 2 — Engine Week

**목표:** `sample_input_*.json` → (엔진) → Day 7의 sample_report와 구조 일치하는 결과 자동 생성.  
**v3 추가:** `blend_profiles.py` (블렌딩 코어)를 Day 8에 먼저 완성하고, 나머지 모듈이 임포트.

---

## Day 8 — blend_profiles.py (v3 핵심 신규)

### 작업: `scripts/blend_profiles.py`

`06_SCORING_RULES.md` §2.5의 모든 함수를 구현한다.

```python
# 구현 대상 함수 (06_SCORING_RULES.md §2.5에서 그대로 복사 후 구현)
cosine_similarity(vec_a, vec_b) -> float
compute_blend_weights(user_vector, profile_pool) -> dict[str, float]
blend_requirements(user_vector, profile_pool) -> tuple[dict, list[Requirement]]
renormalize_to_65_35(blended, skill_groups, source_profiles) -> list[Requirement]
_fix_rounding(requirements, group, target) -> None
validate_blended_weights(requirements) -> None

# 추가 구현
determine_blend_display_mode(profile_blend) -> str  # 06_SCORING_RULES.md §2.7
determine_confidence_level(user_vector) -> str       # 06_SCORING_RULES.md §2.6
```

### 단위 테스트 (수작업 케이스로 검증)

```bash
python scripts/blend_profiles.py \
  --user_vector '{"recruiting": 1.9, "training_and_onboarding": 1.85, "payroll": 1.9}' \
  --profile_pool data/

# 예상 출력:
# profile_blend = {"hr": X, "operations": Y, ...}
# blend_display_mode = SINGLE (if hr >= 0.7)
# Σ blended weight (UNIQUE) = 0.65 ✓
# Σ blended weight (COMMON) = 0.35 ✓
```

### 완료 기준

```
[ ] cosine_similarity — 동일 입력 3회 동일 결과 (결정론 확인)
[ ] validate_blended_weights — HR dominant 케이스 통과
[ ] validate_blended_weights — MIXED 케이스 통과
[ ] compute_blend_weights — 모든 유사도가 0인 입력에서 ValueError (BLOCKED 케이스 확인)
[ ] renormalize_to_65_35 — _fix_rounding 후 합계가 0.6500, 0.3500 (±0.001)
[ ] sample_report_hr_dominant.json의 profile_blend와 수작업 계산값 일치
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

## Day 10 — Requirement Matcher + Scoring (블렌딩 기반)

### 작업: `engine/requirement_matcher.py`, `engine/scoring_engine.py`

```python
def match_requirements(evidences, blended_requirements) -> list[RequirementMatch]:
    """06_SCORING_RULES.md §4 determine_match_level() 사용.
       blended_requirements의 weight(블렌딩 결과)를 그대로 사용."""

def calculate_score(matches, blended_requirements) -> ScoreResult:
    """06_SCORING_RULES.md §1, §6 구현. 블렌딩 후에도 65/35 불변."""
```

### 완료 기준

```
[ ] HR dominant: unique_total + common_total == total (±0.1)
[ ] MIXED: unique_total ≤ 65, common_total ≤ 35
[ ] 3회 실행 동일 점수 (결정론)
[ ] 06_SCORING_RULES.md §10 불변규칙 1~12 assert 통과
[ ] confidence_level = BLOCKED 시 match_requirements 호출 전 차단 확인
```

---

## Day 11 — Gap Analyzer + Strength Selector

### 작업: `engine/gap_analyzer.py`, `engine/strength_selector.py`

```python
def analyze_gaps(matches, blended_requirements) -> list[Gap]:
    """06_SCORING_RULES.md §8. is_core 전파 규칙(source_profiles 중 하나라도 true면 true) 적용."""

def select_strengths(matches, blended_requirements) -> list[Strength]:
    """06_SCORING_RULES.md §9. UNIQUE 우선."""
```

### 완료 기준

```
[ ] MIXED 케이스에서 source_profiles=["hr", "operations"] 복합 requirement의 gap severity 정확
[ ] is_core 전파: HR에서 is_core=true였던 recruiting이 MIXED 블렌딩 후에도 is_core=true
[ ] COMMON + CRITICAL 조합 없음 (불변규칙 확인)
[ ] strengths rank 1, 2가 가능하면 UNIQUE
```

---

## Day 12 — Text Template Engine + Recommendation

### 작업: `engine/text_template.py`

`09_TEXT_TEMPLATE_RULES.md` §1~7 전체 구현:

```python
build_blend_display(profile_blend, blend_display_mode, profile_label_lookup) -> str
build_blend_description(profile_blend, blend_display_mode, profile_label_lookup) -> str
select_split_template(unique_score, common_score) -> str
# strengths/gaps/recommendations 템플릿 전부 포함
polish_text(template_text) -> str  # LLM 폴백 구조 포함
```

### 완료 기준

```
[ ] HR dominant → blend_description: "SINGLE" 템플릿
[ ] MIXED → blend_description: "MIXED_2" 템플릿 (2개 프로필 이름 + %)
[ ] LLM 없이 모든 텍스트 필드 채워짐 (폴백 동작)
[ ] priority_clause: target_priority_text 유래 강점에만 추가
```

---

## Day 13 — Report Builder (12 top-level keys 조립)

### 작업: `engine/report_builder.py`

```python
def build_report(
    report_id, target_priority_text,
    evidences, user_vector, profile_blend, blended_requirements,
    matches, score, gaps, strengths, recommendations, roadmap,
    weight_source="MANUAL_V1"
) -> dict:
    return {
        "meta": build_meta(report_id, profile_blend, weight_source),
        "summary": build_summary(score, matches, profile_blend, ...),
        "careerProfile": build_career_profile(career_histories, evidences),
        "targetJobAnalysis": build_target_job(profile_blend, blended_requirements, matches),
        "skillMapping": build_skill_mapping(matches, blended_requirements),
        "evidenceMapping": build_evidence_mapping(evidences),
        "scores": score.dict(),
        "strengths": [s.dict() for s in strengths],
        "gaps": [g.dict() for g in gaps],
        "recommendations": recommendations.dict(),
        "roadmap": roadmap.dict(),
        "reportSections": DEFAULT_12_SECTIONS,
    }
```

### 완료 기준

```
[ ] HR dominant + MIXED 각각 generated_report.json 자동 생성 성공
[ ] meta.profile_blend 포함, Σ == 1.0
[ ] targetJobAnalysis.unique_requirements[].source_profiles 포함
[ ] evidenceMapping에 source="target_priority_text" 항목 포함
[ ] summary.blend_description, blend_display_mode 정확
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
[ ] HR dominant: blend_display_mode = SINGLE
[ ] MIXED: blend_display_mode = MIXED, blend_description에 2개 프로필 이름
[ ] 06_SCORING_RULES.md §10 불변규칙 1~12 전부 assert 통과
[ ] 3회 실행 동일 결과 (결정론, 블렌딩 포함)
[ ] LLM 없이 완성 (이 시점 LLM 연동 없음)
[ ] profile_blend Σ == 1.0 (각 케이스)
[ ] blended UNIQUE Σ == 0.65, COMMON Σ == 0.35 (각 케이스)
[ ] (선택) 나머지 8개 좌표축 조합으로 임의 입력 생성 후 에러 없이 report 생성 확인
```

### 버퍼 규칙

- Day 14 안에 완료 → Day 15(Text Template) 선작업
- 완료 안 되면 → Day 20(React 디자인 마감) 축소해 흡수

---

# WEEK 3 — Product Week

## Day 15 — HTML Renderer (블렌딩 시각화 포함)

```
backend/pdf/templates/
├── report.html.j2
├── partials/
│   ├── summary.html.j2      ← blend_description 박스 + 수평 막대 (CSS width %)
│   ├── target_job.html.j2   ← profile_blend 막대 + source_profiles 배지 [HR][Ops]
│   └── (나머지 10개)
└── static/report.css        ← --color-blend-1/2/3, --color-source-badge 추가
```

### 완료 기준

```
[ ] output/sample_report_hr_dominant.html — Section 2에 SINGLE 블렌딩 박스
[ ] output/sample_report_mixed.html — Section 2에 MIXED 블렌딩 박스 (막대 2개)
[ ] Section 4: source_profiles 배지 [HR], [Ops] 확인
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
                   # BLOCKED 시 422 LOW_CONFIDENCE_INPUT
                   # force=true 파라미터 지원
GET  /reports/{id} # profile_blend 포함 응답
GET  /reports/{id}/pdf
```

### 완료 기준

```
[ ] target_job_family 필드 전송해도 무시 (하위 호환)
[ ] target_priority_text 30자 미만 → VALIDATION_ERROR
[ ] BLOCKED 상태 → LOW_CONFIDENCE_INPUT 422
[ ] force=true → BLOCKED에도 분석 진행, confidence_level="LOW"
[ ] GET 응답에 profile_blend 포함 확인
```

---

## Day 18 — Supabase 연동

### 작업

1. `03_ERD.md` v3 migration 실행 (ENUM 6종 → job_requirement_profiles 테이블 포함)
2. `data/job_requirements_*.json` 10개 → `job_requirement_profiles` 테이블 시딩
3. 시딩 후 weight 합계 검증 쿼리 실행 (UNIQUE=0.65, COMMON=0.35 × 10개 profile_key)
4. `reports.profile_blend` (JSONB, GIN 인덱스) 저장 확인

### 완료 기준

```
[ ] job_requirement_profiles: 10개 profile_key × 9개 requirement = 90행
[ ] weight 합계 검증 쿼리: 10개 전부 UNIQUE=0.65, COMMON=0.35
[ ] reports.profile_blend JSONB 저장 + GIN 인덱스 생성 확인
[ ] career_evidences: source 컬럼, career_history_id nullable FK 확인
[ ] BLOCKED confidence_level의 경우 reports 테이블에 confidence_level='LOW' 저장 확인
```

---

## Day 19 — React

### 3개 페이지 (v3)

```
/             Landing (예시 카드 5~6개, Job Family 그리드 없음)
/report/new   Form (target_priority_text textarea, career_histories, select 없음)
              서버 422 LOW_CONFIDENCE_INPUT → 모달 ([수정하기] / [그래도 분석하기])
/report/:id   Result → profile_blend 막대 + blend_description 표시
              confidence_level=LOW → 안내 배너
              PDF 다운로드 버튼
```

### 완료 기준

```
[ ] Landing에 "직무 선택 없이 자유롭게 입력" UX 전달
[ ] Form: target_priority_text textarea + 최소 30자 가이드
[ ] Form: 422 수신 시 확인 모달 → force=true 재요청
[ ] Result: meta.profile_blend → 수평 막대 차트 렌더링 (CSS only)
[ ] Result: confidence_level=LOW → 배너 표시
[ ] PDF 다운로드 동작
```

---

## Day 20 — Bug Fix + Deploy

### 오전: Bug Fix

```
[ ] target_priority_text 30자 경계값 테스트
[ ] career_histories 1개 / 10개 엣지 케이스
[ ] user_vector가 거의 zero vector인 경우 (BLOCKED) 정상 422 반환 확인
[ ] LLM 실패 시 폴백 동작 (09_TEXT_TEMPLATE_RULES.md §8)
[ ] profile_blend Σ == 1.0인지 응답에서 확인 (부동소수점 누적 오차 방어)
[ ] CORS 설정
[ ] MIXED 케이스에서 blend_description 문장이 모든 브라우저에서 정상 렌더링
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
[ ] HR dominant 케이스: 리포트 생성 → blend_display_mode=SINGLE → PDF 다운로드 성공
[ ] MIXED 케이스: 리포트 생성 → blend_display_mode=MIXED → PDF 다운로드 성공
[ ] 생성 소요 시간 ≤ 5분
[ ] 동일 입력 재실행 시 동일 점수 (배포 환경에서도 결정론 재검증)
[ ] meta.weight_source = "MANUAL_V1" PDF Section 12에 작은 글씨로 표시 확인
```

---

# 부록 A: v2 → v3 변경 요약

| 항목 | v2 | v3 |
|------|----|----|
| 직무 입력 방식 | `target_job_family` ENUM select (10개) | `target_priority_text` 자유 텍스트 |
| Weight 결정 방식 | 선택된 1개 프로필의 고정 weight | N개 프로필과의 코사인 유사도 블렌딩 → 65/35 재정규화 |
| Report meta | `target_job_family_ko` | `profile_blend`, `weight_source`, `confidence_level` |
| targetJobAnalysis | 1개 프로필의 9개 requirement | N개 블렌딩 결과, 4~8개 UNIQUE + COMMON, `source_profiles` 배지 |
| evidence 소스 | `career_histories`만 | `career_histories` + `target_priority_text` (듀얼) |
| DB | `job_requirement_stats(job_family ENUM)` | `job_requirement_profiles(profile_key TEXT)` |
| ERD | `reports.target_job_family` ENUM | `reports.profile_blend` JSONB |
| 신규 엔진 모듈 | 없음 | `scripts/blend_profiles.py` |
| sample fixture | HR, Data 각 1종 | HR dominant, MIXED 각 1종 |

---

# 부록 B: 매일 자가 점검

```
1. 오늘 작업이 04 또는 05를 건드리는가? → 문서 먼저 수정했는가?
2. blended_requirements의 Σ UNIQUE == 0.65, Σ COMMON == 0.35인가?
3. Σ profile_blend.values() == 1.0인가?
4. confidence_level = BLOCKED인 경우 blend_requirements()를 호출하는 코드 경로가 없는가?
5. original_text를 수정한 코드가 없는가?
6. 동일 입력 → 동일 출력인가? (외부 모델/랜덤 없음)
7. target_job_family ENUM, INVALID_JOB_FAMILY가 코드에 남아있지 않은가?
8. N을 10보다 늘리고 싶은 유혹이 들지 않았는가? (데이터 없이 확장 금지)
```

---

# 알려진 문제점 (§ Limitations — 전체 로드맵 관점)

| 문제 | 영향 | 비고 |
|------|------|------|
| Day 8(blend_profiles.py)이 Week 2의 모든 후속 모듈의 선행 조건 | Day 8에서 막히면 Day 9~13이 연쇄 지연 | 블렌딩 알고리즘 자체는 순수 산술이라 언어/프레임워크 의존성 없음 — 빠른 구현 가능 |
| MIXED 케이스 sample_report 손작성이 HR dominant보다 복잡 | Day 7 작업량이 v2 대비 약 1.5배 | MIXED 케이스는 "2개 좌표축의 blended_requirements union"이므로 requirement 수가 더 많음 |
| Render 배포 환경에서 Playwright + 블렌딩 계산이 동시에 동작할 때 메모리 부담 | OOM(Out of Memory) 가능성 | 블렌딩은 순수 딕셔너리 산술이라 메모리 부담 매우 낮음. Playwright만 주의 |