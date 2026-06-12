# 09 — Text Template Rules

결정론적 텍스트 생성 규칙.  
LLM은 이 템플릿 결과를 **윤색만** 가능. 내용 변경 불가.

---

## 1. 점수별 요약 문장 템플릿

```python
SUMMARY_TEMPLATES = {
    "EXCELLENT_FIT": "{job_family_ko} 직무에 매우 높은 적합도({score}점)를 보입니다. 핵심 역량 전반에서 검증된 경험이 확인됩니다.",
    "GOOD_FIT":      "{job_family_ko} 직무에 높은 적합도({score}점)를 보입니다. 일부 역량의 보강을 통해 경쟁력을 더욱 높일 수 있습니다.",
    "MODERATE_FIT":  "{job_family_ko} 직무에 기본적인 적합도({score}점)를 보입니다. 주요 갭을 체계적으로 보완하면 목표 달성이 가능합니다.",
    "LOW_FIT":       "{job_family_ko} 직무와의 적합도({score}점)는 현재 낮은 수준입니다. 핵심 역량 확보를 위한 전략적 준비가 필요합니다.",
}
```

---

## 2. 강점 문장 템플릿

```python
STRENGTH_TEMPLATES = {
    "FULL": "{label_ko} 역량에서 직접적이고 풍부한 경험이 확인됩니다. {company_name}에서의 경험이 이를 뒷받침합니다.",
    "STRONG": "{label_ko} 역량에서 핵심 경험이 확인됩니다. 실무 적용 깊이를 심화하면 완전한 강점으로 발전 가능합니다.",
}

# 강점은 match_level이 FULL 또는 STRONG인 항목에서만 생성
# rank 1–3까지만 포함
```

---

## 3. Gap 문장 템플릿

```python
GAP_TEMPLATES = {
    "CRITICAL": "{label_ko}은(는) {job_family_ko} 직무의 핵심 요건이나, 현재 경력에서 관련 경험이 확인되지 않습니다. 즉각적인 역량 확보가 필요합니다.",
    "MAJOR": "{label_ko} 경험이 부족하여 직무 수행에 어려움이 예상됩니다. 우선순위를 두고 보완을 시작하세요.",
    "MINOR": "{label_ko} 역량이 다소 부족하나, 단기 학습으로 보완 가능한 수준입니다.",
}
```

---

## 4. 추천 문장 템플릿

```python
RECOMMENDATION_TEMPLATES = {
    "short_term": "{gap_label_ko} 역량 강화를 위해 {timeframe} 내 {action}을(를) 권장합니다.",
    "mid_term": "현재 적합도 수준({score}점)에서 {job_family_ko} 포지션 지원이 가능합니다. {action}을(를) 통해 경쟁력을 높이세요.",
}
```

---

## 5. 결론 문장 템플릿

```python
CONCLUSION_TEMPLATES = {
    "EXCELLENT_FIT": "현재 역량 수준으로 {job_family_ko} 직무 지원을 강력히 권장합니다. 상위 기업의 포지션을 목표로 설정하세요.",
    "GOOD_FIT":      "{key_gap_ko} 역량을 보강하면 {job_family_ko} 직무 지원에서 높은 경쟁력을 갖출 수 있습니다.",
    "MODERATE_FIT":  "90일 로드맵에 따른 역량 보완 후 {job_family_ko} 직무 지원을 권장합니다.",
    "LOW_FIT":       "현재 단계에서는 {job_family_ko} 직무의 기초 역량 확보가 선행되어야 합니다. 6개월 이상의 준비 기간을 권장합니다.",
}
```

---

## 6. LLM 윤색 지침

LLM이 위 템플릿 결과를 윤색할 때 반드시 따라야 하는 규칙:

**허용:**
- 문장 자연스러움 개선
- 존댓말 통일
- 접속사 추가/변경
- 문장 분리 또는 결합 (의미 유지 시)

**금지:**
- 점수 수치 변경
- 강점/갭 항목 추가 또는 제거
- Evidence에 없는 경험 추가
- 추천 행동 항목 임의 생성
- `fit_level` 평가 변경

**LLM 프롬프트 구조:**
```
System: 당신은 커리어 리포트 문장을 자연스럽게 다듬는 편집자입니다.
        내용(점수, 강점 항목, 갭 항목, 추천 행동)은 절대 변경하지 마세요.
        문장의 흐름과 자연스러움만 개선하세요.

User: 다음 텍스트를 자연스럽게 윤색해주세요:
      {template_generated_text}
```
# 10 — PDF Template Spec

Report JSON → PDF 변환 규격.  
PDF는 Report JSON의 렌더링 결과물이며, Report JSON 없이 생성되지 않는다.

---

## 1. PDF 기본 설정

| 항목 | 값 |
|------|-----|
| 페이지 크기 | A4 (210 × 297mm) |
| 마진 | 상하 20mm, 좌우 20mm |
| 기본 폰트 | Noto Sans KR |
| 기본 폰트 크기 | 10pt |
| 생성 도구 | WeasyPrint 또는 Puppeteer |
| 색상 팔레트 | Primary: #2B6CB0, Accent: #48BB78, Danger: #E53E3E |

---

## 2. 섹션 구성 (13개)

### Section 1: 표지 (Cover)

```
┌────────────────────────────────────┐
│                                    │
│         CareerFit                  │  ← 서비스명 (32pt, Primary)
│   커리어 적합도 전략 리포트          │  ← 부제 (16pt)
│                                    │
│   목표 직무: 인사(HR)               │  ← target_job_family_ko
│   분석 일시: 2025년 6월 1일         │  ← generated_at
│   리포트 ID: 550e8400...            │  ← report_id (앞 8자리)
│                                    │
└────────────────────────────────────┘
```

**데이터 소스:** `meta`

---

### Section 2: Executive Summary

```
┌────────────────────────────────────┐
│  종합 적합도 점수                    │
│                                    │
│         78.5 / 100                 │  ← total_score (48pt, bold)
│           우수 ★★★★☆              │  ← fit_level 레이블 + 별점
│                                    │
│  요약                               │
│  채용과 온보딩 역량은 시장 기준을    │  ← summary.one_line
│  충족하나, 노동법과 급여 관리        │
│  보강이 필요합니다.                  │
│                                    │
│  핵심 강점: 채용 관리, 교육/온보딩   │  ← key_strengths
│  주요 갭:   노동법, 급여 관리        │  ← key_gaps
└────────────────────────────────────┘
```

**데이터 소스:** `summary`

---

### Section 3: Career Profile

- 총 경력 기간, 직장 수
- 경력 타임라인 테이블 (회사명 | 직책 | 기간)
- 추출된 스킬 태그 목록

**데이터 소스:** `careerProfile`

---

### Section 4: Target Job Analysis

- 목표 Job Family 개요
- 핵심 요구사항 목록 (weight 순 정렬)
- is_core 항목 강조 표시

**데이터 소스:** `targetJobAnalysis`

---

### Section 5: Market Intelligence

- 해당 Job Family 시장 수요 레이블
- 일반적 요구 경력 연수
- 주요 채용 기업 유형 (대기업/중견/스타트업)

**데이터 소스:** `marketAnalysis`

---

### Section 6: Skill Mapping

2열 테이블:

| 역량 | 적합도 수준 | 비중 | 점수 |
|------|------------|------|------|
| 채용 관리 | ████████ FULL | 20% | 20.0 |
| 노동법 | ░░░░░░░░ NONE | 10% | 0.0 |

- match_level을 progress bar 스타일로 시각화
- FULL: 진한 초록, STRONG: 연초록, PARTIAL: 노랑, WEAK: 주황, NONE: 빨강

**데이터 소스:** `skillMapping`

---

### Section 7: Evidence Mapping

스킬별 원문 근거 표시:

```
채용 관리 [FULL]
  ↳ "신입사원 채용 전 과정 담당. JD 작성, 서류 검토, 면접 진행..."
     출처: 주식회사 예시 / HR 매니저 (2021.03 – 2023.12)
```

**데이터 소스:** `evidenceMapping`  
**주의:** 원문 텍스트는 따옴표로 구분하여 가공되지 않음을 명시

---

### Section 8: Fit Score

- 레이더 차트 (5–8개 핵심 역량 시각화)
- 요구사항별 점수 바 차트
- 총점 및 breakdown 테이블

**데이터 소스:** `scores`

---

### Section 9: Strength Analysis

강점 Top 3 카드형 레이아웃:

```
┌─────────────────────────────────┐
│  #1  채용 관리  [FULL]           │
│  채용 전 과정을 직접 운영한       │
│  검증된 경험                     │
│                                  │
│  근거: "JD 작성부터 온보딩까지..." │
└─────────────────────────────────┘
```

**데이터 소스:** `strengths`

---

### Section 10: Gap Analysis

갭 항목 우선순위 표:

| 우선순위 | 역량 | 심각도 | 설명 |
|---------|------|--------|------|
| 1 | 노동법 | MAJOR | 관련 경험 없음 |
| 2 | 급여 관리 | MAJOR | 간접 경험만 존재 |

**데이터 소스:** `gaps`

---

### Section 11: Recommendation Strategy

단기/중기 추천 행동 목록:

```
단기 (1–2개월)
  ☐ 노동법 온라인 강의 수강 (40시간)
  ☐ 급여 계산 실습 프로그램 참여

중기 (3–6개월)
  ☐ HR 제너럴리스트 포지션 지원 준비
  ☐ HR 자격증 취득 검토
```

**데이터 소스:** `recommendations`

---

### Section 12: 90-Day Roadmap

3단계 타임라인 시각화:

```
[1–30일: 갭 보완] → [31–60일: 역량 심화] → [61–90일: 지원 준비]
```

각 단계별 구체적 행동 항목 목록.

**데이터 소스:** `roadmap`

---

### Section 13: Final Assessment

- 종합 결론 문장
- 다음 단계 행동 3가지
- CareerFit 워터마크 및 생성 일시

**데이터 소스:** `summary.one_line` + `recommendations`

---

## 3. 디자인 규칙

| 항목 | 규칙 |
|------|------|
| 페이지 번호 | 우하단, "X / Y" 형식 |
| 섹션 헤더 | 배경색 Primary, 흰 텍스트, 좌측 숫자 |
| 표 테두리 | 1px solid #E2E8F0 |
| 강조 텍스트 | Bold, Primary 색상 |
| 원문 인용 | 이탤릭 + 따옴표 + 회색 배경 (#F7FAFC) |
| FULL 색상 | #48BB78 (초록) |
| NONE/CRITICAL 색상 | #E53E3E (빨강) |