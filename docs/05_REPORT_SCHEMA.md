# 05 — Report JSON Schema

> **이 문서는 CareerFit에서 가장 중요한 문서다.**  
> Report JSON은 시스템의 **단일 진실 공급원(Single Source of Truth)**이며,  
> PDF, 화면, API 응답은 모두 이 구조를 파싱해 렌더링한다.  
> 코드 100줄보다 이 문서의 정확성이 더 큰 가치를 가진다.

---

## 0. 설계 원칙

1. **모든 필드는 타입과 예시 값을 함께 명시한다.** placeholder가 아닌 실제 값으로 작성한다.
2. **Job Family 무관 구조 통일성:** 어떤 Job Family(10개 중 무엇이든)를 선택해도 이 구조의 **key 집합은 100% 동일**하다. 값만 달라진다.
3. **고유(UNIQUE) / 공통(COMMON) 스킬 구분이 스키마 레벨에 반영된다.** (`01_PRD.md` §4, `04_PAYLOAD_CONTRACT.md` §2 참조)
4. 이 문서의 각 섹션 끝에는 **"PDF 렌더링 위치"** 주석이 있다. (`10_PDF_TEMPLATE_SPEC.md`와 연결)

---

## 전체 구조 (Top-level Keys)

```json
{
  "meta": { ... },
  "summary": { ... },
  "careerProfile": { ... },
  "targetJobAnalysis": { ... },
  "skillMapping": { ... },
  "evidenceMapping": [ ... ],
  "scores": { ... },
  "strengths": [ ... ],
  "gaps": [ ... ],
  "recommendations": { ... },
  "roadmap": { ... },
  "reportSections": [ ... ]
}
```

> `marketAnalysis`는 V1.1에서 추가 예정 (사람인/워크넷 배치 데이터 연동 시).  
> V1에서는 12개 top-level key로 구성된다.

---

## 1. `meta`

리포트 메타데이터. PDF 표지(Section 1) 및 모든 페이지 헤더에 사용.

```json
{
  "meta": {
    "report_id": "550e8400-e29b-41d4-a716-446655440000",
    "generated_at": "2025-06-01T12:03:45Z",
    "target_job_family": "HR",
    "target_job_family_ko": "인사(HR)",
    "engine_version": "2.0.0",
    "llm_used": true
  }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `report_id` | string (UUID) | 리포트 식별자 |
| `generated_at` | string (ISO 8601) | 생성 완료 시각 |
| `target_job_family` | enum | 10개 ENUM 중 하나 |
| `target_job_family_ko` | string | 화면 표시용 한글명 |
| `engine_version` | string (semver) | 엔진 버전 (결정론 검증 시 버전별 점수 비교용) |
| `llm_used` | boolean | 텍스트 윤색에 LLM이 실제로 사용되었는지 |

**PDF 렌더링 위치:** Section 1 (표지) — `report_id`, `target_job_family_ko`, `generated_at`

---

## 2. `summary`

Executive Summary. 리포트 전체에서 가장 먼저 노출되는 핵심 요약.

```json
{
  "summary": {
    "total_score": 78.5,
    "score_label": "우수",
    "fit_level": "GOOD_FIT",
    "one_line": "채용과 온보딩 역량은 시장 기준을 충족하나, 노동법과 급여 관리 보강이 필요합니다.",
    "unique_score": 58.4,
    "unique_score_max": 65.0,
    "common_score": 20.1,
    "common_score_max": 35.0,
    "key_strengths": ["recruiting", "training_and_onboarding", "communication"],
    "key_gaps": ["labor_law", "payroll"]
  }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `total_score` | number (0–100) | `scores.total`과 동일, 요약 표시용 중복 |
| `score_label` | string | 한글 등급 레이블 |
| `fit_level` | enum | `EXCELLENT_FIT \| GOOD_FIT \| MODERATE_FIT \| LOW_FIT` |
| `one_line` | string | 템플릿/LLM 생성 한 줄 요약 |
| `unique_score` | number | UNIQUE 스킬군(고유 핵심 역량) 합산 점수, 최대 65.0 |
| `unique_score_max` | number | 항상 65.0 (06_SCORING_RULES.md 비율 고정) |
| `common_score` | number | COMMON 스킬군(범용 역량) 합산 점수, 최대 35.0 |
| `common_score_max` | number | 항상 35.0 |
| `key_strengths` | array<string> | skill_key 상위 3개 (rank 기준) |
| `key_gaps` | array<string> | skill_key 상위 2개 (priority_order 기준) |

**fit_level 기준:**

| fit_level | score 범위 |
|-----------|-----------|
| EXCELLENT_FIT | 90–100 |
| GOOD_FIT | 75–89 |
| MODERATE_FIT | 55–74 |
| LOW_FIT | 0–54 |

> `unique_score + common_score == total_score` (penalty 적용 후 합계가 일치해야 함. 06_SCORING_RULES.md §6 참조)

**PDF 렌더링 위치:** Section 2 (Executive Summary) — 총점 큰 숫자, UNIQUE/COMMON 분리 도넛 차트, one_line, 강점/갭 미리보기

---

## 3. `careerProfile`

사용자가 입력한 경력 데이터를 정리한 프로필.

```json
{
  "careerProfile": {
    "total_experience_months": 60,
    "total_experience_label": "5년",
    "career_count": 2,
    "most_recent_title": "HR 매니저",
    "most_recent_company": "주식회사 ABC",
    "extracted_skills": [
      {
        "skill_key": "recruiting",
        "label_ko": "채용 관리",
        "skill_group": "UNIQUE",
        "evidence_count": 3,
        "confidence_total": 1.9,
        "confidence_label": "HIGH"
      },
      {
        "skill_key": "communication",
        "label_ko": "커뮤니케이션",
        "skill_group": "COMMON",
        "evidence_count": 1,
        "confidence_total": 0.7,
        "confidence_label": "MEDIUM"
      }
    ]
  }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `total_experience_months` | integer | 모든 career_history 기간 합산 (월 단위, 중복 기간은 합산만 — 겹침 보정 없음) |
| `total_experience_label` | string | "N년 M개월" 형태 |
| `career_count` | integer | career_histories 배열 길이 |
| `most_recent_title` / `most_recent_company` | string | sort_order=0 항목 기준 |
| `extracted_skills` | array | 추출된 모든 skill_key (evidence_count ≥ 1) |
| `extracted_skills[].confidence_label` | enum | `confidence_total` 기준: ≥1.5 → HIGH, 0.7–1.5 → MEDIUM, <0.7 → LOW |

**PDF 렌더링 위치:** Section 3 (Career Profile) — 경력 타임라인 테이블 + 추출 스킬 태그 클라우드 (UNIQUE는 강조색, COMMON은 보조색)

---

## 4. `targetJobAnalysis`

목표 Job Family의 요구사항 개요. UNIQUE/COMMON 구분이 핵심.

```json
{
  "targetJobAnalysis": {
    "job_family": "HR",
    "job_family_ko": "인사(HR)",
    "unique_requirements": [
      {
        "requirement_key": "recruiting",
        "label_ko": "채용 관리",
        "weight": 0.16,
        "is_core": true,
        "match_level": "FULL"
      },
      {
        "requirement_key": "training_and_onboarding",
        "label_ko": "교육/온보딩",
        "weight": 0.16,
        "is_core": true,
        "match_level": "FULL"
      },
      {
        "requirement_key": "payroll",
        "label_ko": "급여 관리",
        "weight": 0.165,
        "is_core": false,
        "match_level": "WEAK"
      },
      {
        "requirement_key": "labor_law",
        "label_ko": "노동법",
        "weight": 0.165,
        "is_core": true,
        "match_level": "NONE"
      }
    ],
    "common_requirements": [
      {
        "requirement_key": "communication",
        "label_ko": "커뮤니케이션",
        "weight": 0.07,
        "is_core": false,
        "match_level": "STRONG"
      },
      {
        "requirement_key": "stakeholder_management",
        "label_ko": "이해관계자 관리",
        "weight": 0.07,
        "is_core": false,
        "match_level": "WEAK"
      },
      {
        "requirement_key": "data_analysis",
        "label_ko": "데이터 분석",
        "weight": 0.07,
        "is_core": false,
        "match_level": "NONE"
      },
      {
        "requirement_key": "documentation",
        "label_ko": "문서화",
        "weight": 0.07,
        "is_core": false,
        "match_level": "FULL"
      },
      {
        "requirement_key": "coordination",
        "label_ko": "일정/업무 조율",
        "weight": 0.07,
        "is_core": false,
        "match_level": "STRONG"
      }
    ],
    "requirement_overview": "HR 직무는 채용·온보딩·노동법의 고유 역량(65%)과 커뮤니케이션·이해관계자 관리 등 범용 역량(35%)을 함께 요구합니다."
  }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `unique_requirements` | array | `skill_group=UNIQUE`인 requirement 전체. weight 합 = 0.65 |
| `common_requirements` | array | `skill_group=COMMON`인 requirement 전체. weight 합 = 0.35 |
| `unique_requirements[].weight` / `common_requirements[].weight` | number | 06_SCORING_RULES.md의 자동 배분 결과 |
| `requirement_overview` | string | 템플릿 생성 1~2문장 |

> `unique_requirements`의 개수는 Job Family마다 4~5개로 다를 수 있으나, weight 합은 항상 0.65다.  
> `common_requirements`는 모든 Job Family에서 동일한 5개 후보 풀(communication, stakeholder_management, data_analysis, documentation, coordination 등)에서 선택되며, weight 합은 항상 0.35다.

**PDF 렌더링 위치:** Section 4 (Target Job Analysis) — 2개 테이블 (고유 요구사항 / 공통 요구사항), is_core 항목 강조

---

## 5. `skillMapping`

전체 requirement에 대한 매칭 결과를 FULL~NONE 순으로 정렬.

```json
{
  "skillMapping": {
    "matched": [
      {
        "skill_key": "recruiting",
        "label_ko": "채용 관리",
        "skill_group": "UNIQUE",
        "match_level": "FULL",
        "weight": 0.16,
        "weighted_score": 16.0
      },
      {
        "skill_key": "documentation",
        "label_ko": "문서화",
        "skill_group": "COMMON",
        "match_level": "FULL",
        "weight": 0.07,
        "weighted_score": 7.0
      }
    ],
    "unmatched": [
      {
        "skill_key": "labor_law",
        "label_ko": "노동법",
        "skill_group": "UNIQUE",
        "match_level": "NONE",
        "weight": 0.165,
        "weighted_score": 0.0
      },
      {
        "skill_key": "data_analysis",
        "label_ko": "데이터 분석",
        "skill_group": "COMMON",
        "match_level": "NONE",
        "weight": 0.07,
        "weighted_score": 0.0
      }
    ]
  }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `matched` | array | `match_level ∈ {FULL, STRONG, PARTIAL}`, weighted_score 내림차순 |
| `unmatched` | array | `match_level ∈ {WEAK, NONE}`, weight 내림차순 (영향도 큰 갭 우선) |

**PDF 렌더링 위치:** Section 6 (Skill Mapping) — progress bar 테이블, `skill_group`별 색상 구분 (UNIQUE=진한 파랑, COMMON=연한 파랑)

---

## 6. `evidenceMapping`

스킬별 원문 근거. 사용자가 "내가 왜 이 점수를 받았는지" 확인하는 핵심 섹션.

```json
{
  "evidenceMapping": [
    {
      "skill_key": "recruiting",
      "label_ko": "채용 관리",
      "skill_group": "UNIQUE",
      "evidences": [
        {
          "career_history_id": "ch-uuid-001",
          "company_name": "주식회사 ABC",
          "title": "HR 매니저",
          "original_text": "신입 채용 전 과정 운영. JD 작성, 서류 검토, 임원 면접 일정 조율 및 진행.",
          "evidence_type": "EXPLICIT",
          "confidence_score": 1.0
        },
        {
          "career_history_id": "ch-uuid-001",
          "company_name": "주식회사 ABC",
          "title": "HR 매니저",
          "original_text": "연간 채용 목표 120% 달성.",
          "evidence_type": "ACHIEVED",
          "confidence_score": 0.9
        }
      ]
    }
  ]
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `evidenceMapping[]` | array | skill_key 단위로 그룹화, evidence_count ≥ 1인 스킬만 포함 |
| `evidences[].original_text` | string | **사용자 입력 원문 그대로.** 절대 수정/요약 금지 (00_PROJECT_VISION.md §1) |
| `evidences[].evidence_type` | enum | `EXPLICIT \| INFERRED \| ACHIEVED` |

**PDF 렌더링 위치:** Section 7 (Evidence Mapping) — 인용구 형태(이탤릭 + 따옴표), 출처(회사명/직책/기간) 표기

---

## 7. `scores`

점수 계산 결과 전체. `summary`의 압축 버전을 풀어서 모든 requirement의 breakdown을 포함.

```json
{
  "scores": {
    "total": 78.5,
    "unique_total": 58.4,
    "common_total": 20.1,
    "core_penalty": -2.5,
    "breakdown": {
      "recruiting": {
        "weight": 0.16,
        "skill_group": "UNIQUE",
        "match_level": "FULL",
        "match_score": 1.0,
        "weighted_score": 16.0,
        "evidence_count": 2,
        "confidence_total": 1.9
      },
      "labor_law": {
        "weight": 0.165,
        "skill_group": "UNIQUE",
        "match_level": "NONE",
        "match_score": 0.0,
        "weighted_score": 0.0,
        "evidence_count": 0,
        "confidence_total": 0.0
      },
      "communication": {
        "weight": 0.07,
        "skill_group": "COMMON",
        "match_level": "STRONG",
        "match_score": 0.75,
        "weighted_score": 5.25,
        "evidence_count": 1,
        "confidence_total": 1.0
      }
    }
  }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `total` | number | 최종 점수 (penalty 반영 후, 0–100) |
| `unique_total` | number | UNIQUE 스킬군 weighted_score 합 (penalty 반영 후) |
| `common_total` | number | COMMON 스킬군 weighted_score 합 |
| `core_penalty` | number | `is_core=true`이며 NONE/WEAK인 항목의 페널티 합 (06_SCORING_RULES.md §6) |
| `breakdown` | object | requirement_key를 key로 하는 dict. **Job Family의 모든 requirement(보통 9~10개) 포함, 누락 없음** |

> `total == round(unique_total + common_total, 1)` 이어야 한다. (penalty는 unique/common 각자에 분배되어 이미 반영됨)

**PDF 렌더링 위치:** Section 8 (Fit Score) — 레이더 차트 (UNIQUE 5개 + COMMON 일부), 점수 breakdown 테이블

---

## 8. `strengths`

강점 Top 3. `match_level ∈ {FULL, STRONG}`인 항목 중 `weighted_score` 상위 3개.

```json
{
  "strengths": [
    {
      "rank": 1,
      "skill_key": "recruiting",
      "label_ko": "채용 관리",
      "skill_group": "UNIQUE",
      "match_level": "FULL",
      "headline": "채용 전 과정을 직접 운영한 검증된 경험",
      "detail": "JD 작성부터 온보딩까지 채용 사이클 전반을 직접 담당했으며, 연간 목표 120% 달성의 성과를 보유합니다.",
      "supporting_evidence_ids": ["ev-001", "ev-006"]
    },
    {
      "rank": 2,
      "skill_key": "training_and_onboarding",
      "label_ko": "교육/온보딩",
      "skill_group": "UNIQUE",
      "match_level": "FULL",
      "headline": "온보딩 프로그램을 설계하고 성과로 입증한 경험",
      "detail": "온보딩 프로그램을 직접 설계 및 운영했으며, 만족도 4.6/5.0이라는 구체적 성과를 달성했습니다.",
      "supporting_evidence_ids": ["ev-002", "ev-007"]
    },
    {
      "rank": 3,
      "skill_key": "documentation",
      "label_ko": "문서화",
      "skill_group": "COMMON",
      "match_level": "FULL",
      "headline": "정기적인 데이터 기반 보고 체계 운영 경험",
      "detail": "분기별 HR 데이터북을 작성하고 경영진에 보고한 경험이 있어, 데이터 기반 의사소통 역량을 보여줍니다.",
      "supporting_evidence_ids": ["ev-003"]
    }
  ]
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `rank` | integer | 1–3 |
| `headline` | string | 템플릿 생성 (09_TEXT_TEMPLATE_RULES.md) |
| `detail` | string | 템플릿 생성, evidence 내용을 자연어로 재구성 (원문 그대로 아님 — 단, evidence의 사실관계는 변경 불가) |
| `supporting_evidence_ids` | array<string> | `evidenceMapping`의 evidence를 가리키는 임시 ID (engine 내부에서만 사용, ev-NNN 형태) |

> 강점은 `skill_group`이 UNIQUE/COMMON 섞여서 선정될 수 있다. 다만 rank 1, 2는 가능한 UNIQUE를 우선한다 (06_SCORING_RULES.md §7).

**PDF 렌더링 위치:** Section 9 (Strength Analysis) — 카드형 레이아웃 3개

---

## 9. `gaps`

미충족 요구사항. severity 및 priority_order로 정렬.

```json
{
  "gaps": [
    {
      "rank": 1,
      "skill_key": "labor_law",
      "label_ko": "노동법",
      "skill_group": "UNIQUE",
      "gap_severity": "CRITICAL",
      "headline": "노동법 전문성 확보가 시급합니다",
      "detail": "노동법은 HR 직무의 핵심 요건(is_core)이나, 현재 경력에서 관련 경험이 전혀 확인되지 않습니다.",
      "recommendation": "노동법 온라인 강의 수강(40시간) 또는 노무사 시험 준비를 권장합니다.",
      "priority_order": 1
    },
    {
      "rank": 2,
      "skill_key": "payroll",
      "label_ko": "급여 관리",
      "skill_group": "UNIQUE",
      "gap_severity": "MAJOR",
      "headline": "급여 관리 실무 경험 보강이 필요합니다",
      "detail": "급여 정산 보조 경험은 있으나, 급여 체계 설계나 운영 경험은 확인되지 않습니다.",
      "recommendation": "ERP정보관리사 자격증 취득 또는 급여 시스템 운영 프로젝트 참여를 권장합니다.",
      "priority_order": 2
    },
    {
      "rank": 3,
      "skill_key": "data_analysis",
      "label_ko": "데이터 분석",
      "skill_group": "COMMON",
      "gap_severity": "MINOR",
      "headline": "데이터 기반 의사결정 역량을 보강하면 좋습니다",
      "detail": "데이터 분석 관련 직접 경험이 확인되지 않으나, 문서화 역량은 보유하고 있어 보강 시 시너지가 예상됩니다.",
      "recommendation": "엑셀/구글시트 기반 HR 데이터 분석 입문 강의 수강을 권장합니다.",
      "priority_order": 3
    }
  ]
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `gap_severity` | enum | `CRITICAL \| MAJOR \| MINOR` (06_SCORING_RULES.md §8 기준 분류) |
| `priority_order` | integer | 1부터 시작, severity → weight 내림차순 |
| `recommendation` | string | `data/gap_recommendations.json`에서 skill_key 기준 조회 |

**PDF 렌더링 위치:** Section 10 (Gap Analysis) — 우선순위 표, severity별 색상 (CRITICAL=빨강, MAJOR=주황, MINOR=노랑)

---

## 10. `recommendations`

```json
{
  "recommendations": {
    "short_term": [
      {
        "action": "노동법 온라인 강의 수강 (40시간)",
        "related_skill_key": "labor_law",
        "rationale": "CRITICAL 갭인 노동법 역량을 1차로 보완합니다.",
        "timeframe": "1–2개월"
      },
      {
        "action": "급여 시스템(ERP) 운영 실습 프로그램 참여",
        "related_skill_key": "payroll",
        "rationale": "MAJOR 갭인 급여 관리 실무 경험을 보강합니다.",
        "timeframe": "1–2개월"
      }
    ],
    "mid_term": [
      {
        "action": "HR 제너럴리스트 포지션 지원 준비",
        "related_skill_key": null,
        "rationale": "현재 적합도 78.5점은 중견기업 HR 제너럴리스트 지원에 충분한 수준입니다.",
        "timeframe": "3–6개월"
      }
    ]
  }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `short_term` | array | 최소 2개. `gaps`의 CRITICAL/MAJOR 상위 항목 기반 |
| `mid_term` | array | 최소 1개. 종합 점수 기반 지원 전략 |
| `related_skill_key` | string \| null | 특정 스킬과 연결되지 않는 추천(mid_term의 지원 전략 등)은 null 허용 |

**PDF 렌더링 위치:** Section 11 (Recommendation Strategy) — 체크리스트 형태

---

## 11. `roadmap`

90일 로드맵. 3개 phase로 고정.

```json
{
  "roadmap": {
    "period": "90일",
    "phases": [
      {
        "phase": 1,
        "label": "1–30일: 갭 보완",
        "actions": [
          "노동법 기초 강의 수강 시작",
          "급여 관련 사내 프로세스 학습"
        ]
      },
      {
        "phase": 2,
        "label": "31–60일: 역량 심화",
        "actions": [
          "HR 데이터 분석 포트폴리오 작성",
          "채용 KPI 대시보드 구축 경험 쌓기"
        ]
      },
      {
        "phase": 3,
        "label": "61–90일: 지원 준비",
        "actions": [
          "목표 직무 이력서 최종 수정",
          "타겟 기업 3–5개 선정 및 지원"
        ]
      }
    ]
  }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `phases` | array | 정확히 3개 (phase 1, 2, 3 고정) |
| `phases[].actions` | array<string> | 각 phase당 1~3개 |

**PDF 렌더링 위치:** Section 12 (90-Day Roadmap) — 3단계 가로 타임라인

---

## 12. `reportSections`

PDF 렌더링 순서 제어. V1은 12개 섹션 고정.

```json
{
  "reportSections": [
    { "section_id": "cover",            "order": 1,  "enabled": true },
    { "section_id": "executive_summary","order": 2,  "enabled": true },
    { "section_id": "career_profile",   "order": 3,  "enabled": true },
    { "section_id": "target_job",       "order": 4,  "enabled": true },
    { "section_id": "skill_mapping",    "order": 5,  "enabled": true },
    { "section_id": "evidence_mapping", "order": 6,  "enabled": true },
    { "section_id": "fit_score",        "order": 7,  "enabled": true },
    { "section_id": "strength_analysis","order": 8,  "enabled": true },
    { "section_id": "gap_analysis",     "order": 9,  "enabled": true },
    { "section_id": "recommendation",   "order": 10, "enabled": true },
    { "section_id": "roadmap",          "order": 11, "enabled": true },
    { "section_id": "final_assessment", "order": 12, "enabled": true }
  ]
}
```

> v1(기존 13섹션)에서 `market_intelligence`가 제외되어 12섹션으로 조정됨 (marketAnalysis는 V1.1).  
> `final_assessment`는 별도 top-level key 없이 `summary.one_line` + `recommendations`를 조합해 렌더링.

**PDF 렌더링 위치:** 전체 문서 구조 결정 (목차 생성에도 사용)

---

## 부록: Job Family 무관 구조 통일성 — 검증 방법

Week 1 Day 7에서 `sample_report_hr.json`과 `sample_report_data.json`을 작성한 뒤, 다음 스크립트로 구조 동일성을 검증한다.

```python
import json

def extract_keys(obj, prefix=""):
    keys = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            full_key = f"{prefix}.{k}" if prefix else k
            keys.add(full_key)
            keys |= extract_keys(v, full_key)
    elif isinstance(obj, list) and obj:
        keys |= extract_keys(obj[0], f"{prefix}[]")
    return keys

hr = json.load(open("output/sample_report_hr.json"))
data = json.load(open("output/sample_report_data.json"))

hr_keys = extract_keys(hr)
data_keys = extract_keys(data)

assert hr_keys == data_keys, f"구조 불일치: {hr_keys ^ data_keys}"
print("구조 통일성 검증 통과")
```