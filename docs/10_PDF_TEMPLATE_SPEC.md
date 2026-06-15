# 10 — PDF Template Spec

Report JSON → PDF 변환 규격.  
PDF는 Report JSON의 렌더링 결과물이며, Report JSON 없이 생성되지 않는다. (`00_PROJECT_VISION.md` §3)

> v2 변경: 13섹션 → **12섹션** (Market Intelligence 제외, V1.1로 이동).  
> `skill_group`(UNIQUE/COMMON) 구분을 색상 코드로 전체 문서에 일관 적용.

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
| **UNIQUE 강조 색상 (v2)** | #2B6CB0 (진한 파랑) |
| **COMMON 강조 색상 (v2)** | #90CDF4 (연한 파랑) |

---

## 2. 섹션 구성 (12개)

`05_REPORT_SCHEMA.md` §12 `reportSections`의 `order` 값과 1:1 대응.

### Section 1 (order=1): 표지 (Cover)

```
┌────────────────────────────────────┐
│                                    │
│         CareerFit                  │  ← 서비스명 (32pt, Primary)
│   커리어 적합도 전략 리포트          │  ← 부제 (16pt)
│                                    │
│   목표 직무: 인사(HR)               │  ← meta.target_job_family_ko
│   분석 일시: 2025년 6월 1일         │  ← meta.generated_at
│   리포트 ID: 550e8400...            │  ← meta.report_id (앞 8자리)
│                                    │
└────────────────────────────────────┘
```

**데이터 소스:** `meta`

---

### Section 2 (order=2): Executive Summary

```
┌────────────────────────────────────┐
│  종합 적합도 점수                    │
│                                    │
│         78.5 / 100                 │  ← summary.total_score (48pt, bold)
│           우수 ★★★★☆              │  ← summary.score_label + 별점
│                                    │
│  ┌──────────────┬──────────────┐  │
│  │ 직무 고유 역량 │  범용 역량    │  │  ← v2 신규: 도넛 차트 2개
│  │  58.4 / 65    │  20.1 / 35    │  │     unique_score / unique_score_max
│  │   (90%)       │   (57%)       │  │     common_score / common_score_max
│  └──────────────┴──────────────┘  │
│                                    │
│  요약                               │
│  채용과 온보딩 역량은 시장 기준을    │  ← summary.one_line
│  충족하나, 노동법과 급여 관리        │
│  보강이 필요합니다.                  │
│                                    │
│  핵심 강점: 채용 관리, 교육/온보딩   │  ← summary.key_strengths
│  주요 갭:   노동법, 급여 관리        │  ← summary.key_gaps
└────────────────────────────────────┘
```

**데이터 소스:** `summary`

**v2 디자인 노트:** 도넛 차트 2개는 각각 65/35 만점 기준으로 그려지며, 색상은 UNIQUE=#2B6CB0, COMMON=#90CDF4 사용.

---

### Section 3 (order=3): Career Profile

- 총 경력 기간, 직장 수 (`careerProfile.total_experience_label`, `.career_count`)
- 경력 타임라인 테이블 (회사명 | 직책 | 기간)
- 추출된 스킬 태그 클라우드 — `extracted_skills[].skill_group`에 따라 UNIQUE는 진한 배경, COMMON은 연한 배경 태그로 표시

**데이터 소스:** `careerProfile`

---

### Section 4 (order=4): Target Job Analysis

2개 테이블로 구성:

```
[테이블 1] 직무 고유 역량 (65%)               [테이블 2] 범용 역량 (35%)
┌────────────┬──────┬────────┬────────┐    ┌────────────┬──────┬────────┐
│ 역량        │ 비중  │ 핵심   │ 적합도  │    │ 역량        │ 비중  │ 적합도  │
├────────────┼──────┼────────┼────────┤    ├────────────┼──────┼────────┤
│ 채용 관리    │ 16.3%│  ★    │ FULL   │    │ 커뮤니케이션 │ 7.0% │ STRONG │
│ 온보딩       │ 16.3%│  ★    │ FULL   │    │ ...         │      │        │
│ 노동법       │ 16.3%│  ★    │ NONE   │    └────────────┴──────┴────────┘
│ 급여 관리    │ 16.3%│       │ FULL   │
└────────────┴──────┴────────┴────────┘
```

- `is_core=true` 항목은 ★ 표시
- 테이블 1 헤더 배경 = UNIQUE 색상(#2B6CB0), 테이블 2 헤더 배경 = COMMON 색상(#90CDF4)

**데이터 소스:** `targetJobAnalysis.unique_requirements`, `.common_requirements`

---

### Section 5 (order=5): Skill Mapping

```
[matched]
채용 관리 (UNIQUE)     ████████████████ FULL     16.0점
문서화 (COMMON)        ████████████████ FULL      7.0점
커뮤니케이션 (COMMON)   ████████████░░░░ STRONG    5.25점

[unmatched]
노동법 (UNIQUE)        ░░░░░░░░░░░░░░░░ NONE      0.0점
데이터 분석 (COMMON)    ░░░░░░░░░░░░░░░░ NONE      0.0점
```

- progress bar 색상: `match_level`에 따라 FULL=#48BB78, STRONG=연두, PARTIAL=노랑, WEAK=주황, NONE=#E53E3E
- 막대 우측에 `(UNIQUE)` / `(COMMON)` 라벨 표기 (텍스트, 색상 아님 — 인쇄 시 흑백 대비 고려)

**데이터 소스:** `skillMapping.matched`, `.unmatched`

---

### Section 6 (order=6): Evidence Mapping

```
채용 관리 (UNIQUE) [FULL]
  ↳ "신입 채용 전 과정 운영. JD 작성, 서류 검토, 임원 면접 일정 조율 및 진행."
     출처: 주식회사 ABC / HR 매니저 (2020.03 – 2023.12) · EXPLICIT
  ↳ "연간 채용 목표 120% 달성."
     출처: 주식회사 ABC / HR 매니저 (2020.03 – 2023.12) · ACHIEVED
```

**데이터 소스:** `evidenceMapping`  
**주의:** 원문 텍스트는 따옴표로 구분하여 가공되지 않음을 명시. `evidence_type`을 작게 표기.

---

### Section 7 (order=7): Fit Score

- 레이더 차트: UNIQUE 4~5개 + COMMON 5개, 총 9~10개 축
  - UNIQUE 축은 진한 파랑 영역, COMMON 축은 연한 파랑 영역으로 겹쳐 표시
- 점수 breakdown 테이블 (`scores.breakdown` 전체, requirement_key별)
- 하단에 `unique_total` / `common_total` / `core_penalty` / `total` 요약 박스

**데이터 소스:** `scores`

---

### Section 8 (order=8): Strength Analysis

강점 Top 3 카드형 레이아웃:

```
┌─────────────────────────────────┐
│  #1  채용 관리 [UNIQUE · FULL]    │
│  채용 전 과정을 직접 운영한       │
│  검증된 경험                     │
│                                  │
│  근거: "JD 작성부터 온보딩까지..." │
└─────────────────────────────────┘
```

각 카드 좌상단에 `skill_group` 배지(UNIQUE/COMMON) 표시.

**데이터 소스:** `strengths`

---

### Section 9 (order=9): Gap Analysis

```
┌──────┬─────────────┬──────────┬────────┬──────────────────┐
│ 우선순위│ 역량         │ 구분      │ 심각도  │ 설명              │
├──────┼─────────────┼──────────┼────────┼──────────────────┤
│  1   │ 노동법       │ UNIQUE   │ CRITICAL│ 관련 경험 없음     │
│  2   │ 급여 관리    │ UNIQUE   │ MAJOR   │ 간접 경험만 존재   │
│  3   │ 데이터 분석   │ COMMON   │ MINOR   │ 경험 없음, 보강 권장│
└──────┴─────────────┴──────────┴────────┴──────────────────┘
```

심각도 색상: CRITICAL=#E53E3E, MAJOR=주황, MINOR=노랑

**데이터 소스:** `gaps`

---

### Section 10 (order=10): Recommendation Strategy

```
단기 (1–2개월)
  ☐ 노동법 온라인 강의 수강 (40시간)           [관련: 노동법 · UNIQUE]
  ☐ 급여 시스템(ERP) 운영 실습 참여            [관련: 급여 관리 · UNIQUE]

중기 (3–6개월)
  ☐ HR 제너럴리스트 포지션 지원 준비
```

`related_skill_key`가 있는 항목은 우측에 `[관련: {label_ko} · {skill_group}]` 표기, null이면 표기 생략.

**데이터 소스:** `recommendations`

---

### Section 11 (order=11): 90-Day Roadmap

```
[1–30일: 갭 보완] → [31–60일: 역량 심화] → [61–90일: 지원 준비]
```

3단계 가로 타임라인, 각 단계 하단에 `actions[]` 1~3개 bullet.

**데이터 소스:** `roadmap`

---

### Section 12 (order=12): Final Assessment

- 종합 결론 문장 (`09_TEXT_TEMPLATE_RULES.md` §6 CONCLUSION_TEMPLATES)
- 다음 단계 행동 3가지 (`recommendations.short_term` + `mid_term` 통합)
- CareerFit 워터마크 및 생성 일시 (`meta.generated_at`)

**데이터 소스:** `summary.one_line` + `recommendations`

---

## 3. 디자인 규칙

| 항목 | 규칙 |
|------|------|
| 페이지 번호 | 우하단, "X / 12" 형식 (12섹션 기준, 단 섹션이 여러 페이지에 걸칠 수 있으므로 실제 총 페이지수와는 다름) |
| 섹션 헤더 | 배경색 Primary, 흰 텍스트, 좌측 order 숫자 |
| 표 테두리 | 1px solid #E2E8F0 |
| 강조 텍스트 | Bold, Primary 색상 |
| 원문 인용 | 이탤릭 + 따옴표 + 회색 배경 (#F7FAFC) |
| UNIQUE 배지 | 배경 #2B6CB0, 흰 텍스트, 작은 라운드 사각형 |
| COMMON 배지 | 배경 #90CDF4, 진한 텍스트, 작은 라운드 사각형 |
| FULL 색상 | #48BB78 (초록) |
| NONE/CRITICAL 색상 | #E53E3E (빨강) |

---

## 4. 템플릿 파일 구조

```
backend/pdf/templates/
├── report.html.j2              # 메인 템플릿, reportSections 순서대로 partials include
├── partials/
│   ├── cover.html.j2           # Section 1
│   ├── summary.html.j2         # Section 2 (도넛 차트 2개 포함)
│   ├── career_profile.html.j2  # Section 3
│   ├── target_job.html.j2      # Section 4 (2개 테이블)
│   ├── skill_mapping.html.j2   # Section 5
│   ├── evidence_mapping.html.j2# Section 6
│   ├── fit_score.html.j2       # Section 7 (레이더 차트)
│   ├── strength_analysis.html.j2# Section 8
│   ├── gap_analysis.html.j2    # Section 9
│   ├── recommendations.html.j2 # Section 10
│   ├── roadmap.html.j2         # Section 11
│   └── final_assessment.html.j2# Section 12
└── static/
    └── report.css               # UNIQUE/COMMON 색상 변수 정의 (CSS custom properties)
```

`report.css` 색상 변수 예시:
```css
:root {
  --color-primary: #2B6CB0;
  --color-accent: #48BB78;
  --color-danger: #E53E3E;
  --color-unique: #2B6CB0;
  --color-common: #90CDF4;
  --color-match-full: #48BB78;
  --color-match-strong: #9AE6B4;
  --color-match-partial: #F6E05E;
  --color-match-weak: #ED8936;
  --color-match-none: #E53E3E;
}
```