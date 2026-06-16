# 10 — PDF Template Spec

Report JSON → PDF 변환 규격.  
PDF는 Report JSON의 렌더링 결과물이며, Report JSON 없이 생성되지 않는다.

> **v3 변경:**  
> - Section 1(표지)에서 `target_job_family_ko` 단일 라벨 제거 → `blend_description` 또는 상위 프로필명으로 대체  
> - Section 2(Executive Summary)에 블렌딩 Explanation 박스 추가 (최상단)  
> - Section 4(Target Job Analysis)에 `profile_blend` 막대 시각화 + `source_profiles` 배지 추가

---

## 1. PDF 기본 설정

| 항목 | 값 |
|------|-----|
| 페이지 크기 | A4 (210 × 297mm) |
| 마진 | 상하 20mm, 좌우 20mm |
| 기본 폰트 | Noto Sans KR |
| 기본 폰트 크기 | 10pt |
| 생성 도구 | Playwright (Chromium) |
| Primary 색상 | #2B6CB0 |
| Accent 색상 | #48BB78 |
| Danger 색상 | #E53E3E |
| UNIQUE 강조 색상 | #2B6CB0 (진한 파랑) |
| COMMON 강조 색상 | #90CDF4 (연한 파랑) |
| Blend 1위 색상 | #2B6CB0 |
| Blend 2위 색상 | #4299E1 |
| Blend 3위 색상 | #90CDF4 |

---

## 2. 섹션 구성 (12개)

### Section 1 (order=1): 표지 (Cover)

```
┌────────────────────────────────────┐
│                                    │
│         CareerFit                  │
│   커리어 적합도 전략 리포트          │
│                                    │
│   [blend_display_mode=SINGLE]      │
│   분석 프로필: 인사(HR)             │ ← top_profile_ko (가장 비중 큰 프로필)
│                                    │
│   [blend_display_mode=MIXED]       │
│   분석 프로필: HR 81% + Operations 19%│ ← blend_description 요약
│                                    │
│   분석 일시: 2025년 6월 1일         │
│   리포트 ID: 550e8400...            │
│   데이터 기준: MANUAL_V1            │ ← meta.weight_source (작은 글씨)
└────────────────────────────────────┘
```

**데이터 소스:** `meta.profile_blend`, `meta.weight_source`, `meta.generated_at`, `meta.report_id`

---

### Section 2 (order=2): Executive Summary

```
┌────────────────────────────────────┐
│  ┌──────────────────────────────┐  │
│  │  [블렌딩 Explanation 박스]    │  │  ← v3 신규, 최상단
│  │  "당신의 경험은 'HR' 특성 81% │  │
│  │   와 'Operations' 특성 19%가  │  │
│  │   혼합된 프로필로 분석되었습니다"│  │
│  │                               │  │
│  │  ████████████████████░░ HR 81%│  │  ← profile_blend 수평 막대
│  │  ████░░░░░░░░░░░░░░░░ Ops 19% │  │
│  └──────────────────────────────┘  │
│                                    │
│         78.5 / 100                 │
│           우수 ★★★★☆              │
│                                    │
│  ┌──────────────┬──────────────┐  │
│  │ 직무 고유 역량 │  범용 역량   │  │
│  │  51.2 / 65    │  27.3 / 35   │  │
│  │   (79%)       │   (78%)      │  │
│  └──────────────┴──────────────┘  │
│                                    │
│  채용과 온보딩 역량은 시장 기준을    │
│  충족하나, 노동법과 급여 관리        │
│  보강이 필요합니다.                  │
│                                    │
│  핵심 강점: 채용 관리, 교육/온보딩   │
│  주요 갭:   노동법, 급여 관리        │
└────────────────────────────────────┘
```

**v3 신규 — 블렌딩 Explanation 박스:**
- `summary.blend_description` 텍스트
- `meta.profile_blend` 기준 수평 막대 차트 (ratio 내림차순, 상위 3개만, 나머지는 "기타"로 합산)
- Blend 1/2/3위 색상(§1)으로 각 막대 색상 구분

**데이터 소스:** `summary`, `meta.profile_blend`

---

### Section 3 (order=3): Career Profile

- 총 경력 기간, 직장 수
- 경력 타임라인 테이블 (회사명 | 직책 | 기간)
- 추출된 스킬 태그 클라우드 — UNIQUE는 진한 배경(#2B6CB0), COMMON은 연한 배경(#90CDF4)
- **v3 신규:** `source="target_priority_text"` Evidence에서 추출된 스킬은 별도 "목표 기반 역량" 섹션에 따로 표시 (동일 스킬이면 하나만 표시, 출처 라벨만 구분)

**데이터 소스:** `careerProfile`, `evidenceMapping[].evidences[].source`

---

### Section 4 (order=4): Target Job Analysis (v3 대폭 변경)

```
[상단] Profile Blend 시각화
  HR      ████████████████████████ 81%
  Operations ████████            19%

[테이블 1] 직무 고유 역량 (UNIQUE, 65%)
┌──────────────┬──────┬───────┬────────┬────────────────┐
│ 역량          │ 비중  │ 핵심  │ 출처   │ 매칭 결과       │
├──────────────┼──────┼───────┼────────┼────────────────┤
│ 채용 관리     │ 13.2%│  ★   │ [HR]   │ FULL           │
│ 온보딩        │ 13.2%│  ★   │ [HR]   │ FULL           │
│ 노동법        │ 13.2%│  ★   │ [HR]   │ NONE ⚠         │
│ 급여 관리     │ 13.2%│       │ [HR]   │ FULL           │
│ 프로세스 개선 │  3.1%│  ★   │ [Ops]  │ PARTIAL        │
│ ...           │      │       │        │                │
└──────────────┴──────┴───────┴────────┴────────────────┘

[테이블 2] 범용 역량 (COMMON, 35%)
┌──────────────┬──────┬────────────────┬────────────────┐
│ 역량          │ 비중  │ 출처            │ 매칭 결과       │
├──────────────┼──────┼────────────────┼────────────────┤
│ 커뮤니케이션  │ 7.4% │ [HR] [Ops]     │ STRONG         │
│ ...           │      │                │                │
└──────────────┴──────┴────────────────┴────────────────┘
```

- **`source_profiles` 배지:** `[HR]`, `[Ops]` 형태의 작은 배지로 각 역량의 출처 좌표축 표시
- `is_core` 항목 ★ 표시, `match_level=NONE`인 is_core 항목 ⚠ 표시
- 테이블 1 헤더 배경 = UNIQUE 색상(#2B6CB0), 테이블 2 헤더 배경 = COMMON 색상(#90CDF4)

**데이터 소스:** `targetJobAnalysis.profile_blend`, `.unique_requirements`, `.common_requirements`

---

### Section 5 (order=5): Skill Mapping

```
[matched]
채용 관리 (UNIQUE · [HR])     ████████████████ FULL     13.2점
온보딩 (UNIQUE · [HR])        ████████████████ FULL     13.2점
커뮤니케이션 (COMMON · [HR][Ops])████████████░░░░ STRONG  5.6점

[unmatched]
노동법 (UNIQUE · [HR])        ░░░░░░░░░░░░░░░░ NONE ⚠   0.0점
프로세스 개선 (UNIQUE · [Ops]) ░░░░░░░░░░░░░░░░ WEAK      0.8점
```

- `source_profiles` 배지를 막대 우측에 표기
- 막대 색상: FULL=#48BB78, STRONG=연두, PARTIAL=노랑, WEAK=주황, NONE=#E53E3E

**데이터 소스:** `skillMapping.matched`, `.unmatched`

---

### Section 6 (order=6): Evidence Mapping

```
채용 관리 (UNIQUE · [HR]) [FULL]
  ↳ "신입 채용 전 과정 운영. JD 작성, 서류 검토, 임원 면접 일정 조율 및 진행."
     출처: 주식회사 ABC / HR 매니저 (2020.03 – 2023.12) · EXPLICIT
  ↳ "연간 채용 목표 120% 달성."
     출처: 주식회사 ABC / HR 매니저 (2020.03 – 2023.12) · ACHIEVED
  ↳ "1순위: 인사관리(인력운영/평가, 급여)... 채용 업무를 직접 수행하며 성취를 느낌"
     출처: 목표 입력 (target_priority_text) · EXPLICIT   ← v3 신규 표시
```

**v3 신규:** `source="target_priority_text"` Evidence는 출처를 "목표 입력"으로 표기.

**데이터 소스:** `evidenceMapping`

---

### Section 7 (order=7): Fit Score

- 레이더 차트: UNIQUE 4~8개(블렌딩 결과, 가변) + COMMON 5개
  - UNIQUE 축은 진한 파랑 영역, COMMON 축은 연한 파랑 영역
- 점수 breakdown 테이블 (블렌딩된 requirement 전체)
- 하단 요약 박스: `unique_total` / `common_total` / `core_penalty` / `total`

**데이터 소스:** `scores`

---

### Section 8 (order=8): Strength Analysis

```
┌─────────────────────────────────┐
│  #1  채용 관리 [UNIQUE · HR]     │  ← source_profiles 배지 추가
│  채용 전 과정을 직접 운영한        │
│  검증된 경험                     │
│                                  │
│  근거: "JD 작성부터 온보딩까지..." │
│  ✓ 목표 직무에서도 중요 역량으로   │  ← priority_clause (target_priority_text 유래 시)
│    언급됨                        │
└─────────────────────────────────┘
```

**데이터 소스:** `strengths`

---

### Section 9 (order=9): Gap Analysis

```
┌──────┬──────────────┬──────────┬────────┬──────────────────┐
│ 순위  │ 역량          │ 출처      │ 심각도  │ 설명              │
├──────┼──────────────┼──────────┼────────┼──────────────────┤
│  1   │ 노동법       │ [HR]     │ CRITICAL│ 관련 경험 없음     │
│  2   │ 프로세스 개선 │ [Ops]    │ MAJOR   │ 부분 경험만 존재   │
└──────┴──────────────┴──────────┴────────┴──────────────────┘
```

심각도 색상: CRITICAL=#E53E3E, MAJOR=주황, MINOR=노랑

**데이터 소스:** `gaps`

---

### Section 10 (order=10): Recommendation Strategy

```
단기 (1–2개월)
  ☐ 노동법 온라인 강의 수강        [관련: 노동법 · UNIQUE · HR]
  ☐ 프로세스 개선 사내 프로젝트 참여 [관련: 프로세스 개선 · UNIQUE · Ops]

중기 (3–6개월)
  ☐ HR/Operations 복합 역할 포지션 지원 준비
```

**데이터 소스:** `recommendations`

---

### Section 11 (order=11): 90-Day Roadmap

3단계 가로 타임라인:
```
[1–30일: 갭 보완] → [31–60일: 역량 심화] → [61–90일: 지원 준비]
```

**데이터 소스:** `roadmap`

---

### Section 12 (order=12): Final Assessment

- 종합 결론 문장 (`09_TEXT_TEMPLATE_RULES.md` §7)
- 다음 단계 행동 3가지
- **v3 신규:** `meta.weight_source == "MANUAL_V1"`인 경우  
  "이 분석의 직무별 역량 비중(weight)은 전문가 기준으로 설정되었으며,  
  향후 시장 공고 데이터 기반으로 업데이트됩니다" 안내 (작은 글씨)
- CareerFit 워터마크 및 생성 일시

**데이터 소스:** `summary.one_line`, `recommendations`, `meta.weight_source`

---

## 3. 디자인 규칙

| 항목 | 규칙 |
|------|------|
| 페이지 번호 | 우하단, "X / 총 페이지" 형식 |
| 섹션 헤더 | 배경색 Primary, 흰 텍스트 |
| 표 테두리 | 1px solid #E2E8F0 |
| 원문 인용 | 이탤릭 + 따옴표 + 회색 배경 (#F7FAFC) |
| UNIQUE 배지 | 배경 #2B6CB0, 흰 텍스트 |
| COMMON 배지 | 배경 #90CDF4, 진한 텍스트 |
| source_profiles 배지 | 배경 #EDF2F7(회색), 진한 텍스트, 작은 라운드 (예: `[HR]`, `[Ops]`) |
| FULL 색상 | #48BB78 (초록) |
| NONE/CRITICAL 색상 | #E53E3E (빨강) |

---

## 4. 템플릿 파일 구조

```
backend/pdf/templates/
├── report.html.j2
├── partials/
│   ├── cover.html.j2
│   ├── summary.html.j2           ← v3: blend_description 박스 + 막대 차트 추가
│   ├── career_profile.html.j2
│   ├── target_job.html.j2        ← v3: profile_blend 막대 + source_profiles 배지
│   ├── skill_mapping.html.j2     ← v3: source_profiles 배지
│   ├── evidence_mapping.html.j2  ← v3: target_priority_text 출처 표시
│   ├── fit_score.html.j2
│   ├── strength_analysis.html.j2 ← v3: priority_clause 추가
│   ├── gap_analysis.html.j2      ← v3: source_profiles 배지
│   ├── recommendations.html.j2
│   ├── roadmap.html.j2
│   └── final_assessment.html.j2  ← v3: weight_source 안내 추가
└── static/
    └── report.css
```

`report.css` 추가 변수 (v3):
```css
:root {
  --color-primary: #2B6CB0;
  --color-accent: #48BB78;
  --color-danger: #E53E3E;
  --color-unique: #2B6CB0;
  --color-common: #90CDF4;
  --color-blend-1: #2B6CB0;
  --color-blend-2: #4299E1;
  --color-blend-3: #90CDF4;
  --color-source-badge: #EDF2F7;
  --color-match-full: #48BB78;
  --color-match-strong: #9AE6B4;
  --color-match-partial: #F6E05E;
  --color-match-weak: #ED8936;
  --color-match-none: #E53E3E;
}
```

---

## 5. 알려진 문제점 (§ Limitations)

| 문제 | 영향 | 비고 |
|------|------|------|
| Section 4 테이블 행 수가 가변 (UNIQUE 4~8개) | PDF 레이아웃에서 테이블이 한 페이지를 초과하거나 여백이 과도할 수 있음 | Playwright CSS `page-break-inside: avoid` + 최대 행 수 제한(8개) 권장 |
| `source_profiles` 배지가 여러 개(예: [HR][Ops][Product])이면 셀 넘침 | 표 레이아웃 깨짐 | 최대 2개 배지 표시, 초과 시 "+N" 축약 |
| Section 2 blend 막대 차트를 HTML/CSS로 구현 시 Playwright 렌더링 지연 가능 | PDF 생성 시간 증가 | 막대 차트는 CSS `width` 퍼센트로 구현 (Canvas/JS 불필요) |
| `meta.weight_source` 안내 문구(Section 12)가 기술적으로 들릴 수 있음 | 일반 사용자에게 불필요한 정보처럼 느껴질 가능성 | 폰트 사이즈 8pt, 회색 (#718096)으로 최소 존재감 유지 |