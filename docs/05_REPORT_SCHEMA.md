# 05 — Report JSON Schema

> **이 문서는 CareerFit에서 가장 중요한 문서다.**  
> Report JSON은 시스템의 **단일 진실 공급원(Single Source of Truth)**이며,  
> PDF, 화면, API 응답은 모두 이 구조를 파싱해 렌더링한다.

> **v3.1 핵심 변경:** `meta.target_job_family`(ENUM) 제거 유지.  
> `meta.primary_profile`, `meta.secondary_profiles`, `meta.confidence_level`, `meta.evidence_count`,  
> `meta.warning_message`를 추가한다. `targetJobAnalysis`는 `primary_profile`의 requirement를 기준으로 작성한다.

---

## 0. 설계 원칙

1. **모든 필드는 타입과 예시 값을 함께 명시한다.** placeholder가 아닌 실제 값으로 작성한다.
2. **구조 통일성:** 어떤 입력이든, LOW confidence 포함, Report JSON의 **key 집합은 100% 동일**하다. 값만 달라진다.
3. **고유(UNIQUE) / 공통(COMMON) 스킬 구분이 스키마 레벨에 반영된다.**
4. **대표 프로필 투명성 (v3.1 신규):** `meta.primary_profile`이 리포트의 점수·갭·추천 기준이다.  
   입력 근거가 부족하면 `confidence_level=LOW`와 `warning_message`로 명시한다.
5. 각 섹션 끝에는 **"PDF 렌더링 위치"** 주석이 있다. (`10_PDF_TEMPLATE_SPEC.md`와 연결)

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

> `marketAnalysis`는 V1.1에서 추가 예정 (트랙 2 — 사람인/워크넷 배치 데이터 연동 시).  
> V1에서는 12개 top-level key로 구성된다. (변경 없음)

---

## 1. `meta`

리포트 메타데이터. PDF 표지(Section 1) 및 모든 페이지 헤더에 사용.

```json
{
  "meta": {
    "report_id": "550e8400-e29b-41d4-a716-446655440000",
    "generated_at": "2025-06-01T12:03:45Z",
    "engine_version": "3.0.0",
    "llm_used": true,
    "primary_profile": "hr",
    "secondary_profiles": ["operations"],
    "weight_source": "MANUAL_V1",
    "confidence_level": "HIGH",
    "evidence_count": 10,
    "warning_message": null
  }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `report_id` | string (UUID) | 리포트 식별자 |
| `generated_at` | string (ISO 8601) | 생성 완료 시각 |
| ~~`target_job_family`~~ | ~~enum~~ | **v3에서 제거** |
| ~~`target_job_family_ko`~~ | ~~string~~ | **v3에서 제거** |
| `engine_version` | string (semver) | 엔진 버전 |
| `llm_used` | boolean | 텍스트 윤색에 LLM이 실제로 사용되었는지 |
| **`primary_profile`** | string | **v3.1 신규.** 엔진이 최종 리포트 기준으로 선택한 대표 profile_id |
| **`secondary_profiles`** | array<string> | **v3.1 신규, optional.** 일부 근거가 감지된 보조 프로필. 핵심 판단 기준은 아님 |
| **`weight_source`** | enum | **v3 신규.** `MANUAL_V1 \| CRAWLED_<YYYYQn>`. N개 좌표축(`job_requirements_*.json`)의 weight 출처 (`00_PROJECT_VISION.md` 트랙 2) |
| **`confidence_level`** | enum | **v3 신규.** `HIGH \| MEDIUM \| LOW`. `04_PAYLOAD_CONTRACT.md`의 동일 필드와 일치 |
| **`evidence_count`** | integer | **v3.1 신규.** 추출된 evidence 총 개수 |
| **`warning_message`** | string \| null | **v3.1 신규.** LOW에서는 required. "입력 정보가 부족하여 일부 결과는 추정에 기반합니다" 문구 포함 |

> `profile_blend`는 V1 사용자-facing 핵심 필드에서 제거된다. 필요 시 `internal_debug.profile_blend` optional 필드로만 저장한다.

**PDF 렌더링 위치:** Section 1 (표지) — `report_id`, `generated_at`, `weight_source`(작은 글씨로 데이터 근거 표기)

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
    "primary_profile_summary": "입력된 채용, 온보딩, 급여 운영 근거를 기준으로 인사(HR)를 대표 프로필로 선택했습니다.",
    "unique_score": 51.2,
    "unique_score_max": 65.0,
    "common_score": 27.3,
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
| **`primary_profile_summary`** | string | **v3.1 신규.** 대표 프로필 선택 근거 설명. `09_TEXT_TEMPLATE_RULES.md` §2 템플릿 |
| `unique_score` | number | UNIQUE 스킬군(primary_profile 고유 핵심 역량) 합산 점수, 최대 65.0 |
| `unique_score_max` | number | 항상 65.0 |
| `common_score` | number | COMMON 스킬군(primary_profile 범용 역량) 합산 점수, 최대 35.0 |
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

> `unique_score + common_score == total_score` (penalty 적용 후 합계가 일치해야 함. `06_SCORING_RULES.md` §6 참조)

**PDF 렌더링 위치:** Section 2 (Executive Summary) — 총점 큰 숫자, **Primary Profile Selection 박스**, LOW warning banner, UNIQUE/COMMON 분리 도넛 차트, one_line, 강점/갭 미리보기

---

## 3. `careerProfile`

사용자가 입력한 경력 데이터를 정리한 프로필. (v2에서 구조 변경 없음)

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

> `extracted_skills[].skill_group`은 `meta.primary_profile`의 requirement 분류를 기준으로 표시한다.

**PDF 렌더링 위치:** Section 3 (Career Profile) — 경력 타임라인 테이블 + 추출 스킬 태그 클라우드

---

## 4. `targetJobAnalysis` (v3.1 변경)

> v2: "사용자가 선택한 1개 Job Family의 요구사항"  
> v3.1: "엔진이 선택한 `primary_profile`의 unique/common requirements"

```json
{
  "targetJobAnalysis": {
    "primary_profile": "hr",
    "primary_profile_label_ko": "인사(HR)",
    "secondary_profiles": ["operations"],
    "unique_requirements": [
      {
        "requirement_key": "recruiting",
        "label_ko": "채용 관리",
        "weight": 0.1625,
        "is_core": true,
        "match_level": "FULL",
        "source_profiles": ["hr"]
      },
      {
        "requirement_key": "training_and_onboarding",
        "label_ko": "교육/온보딩",
        "weight": 0.1625,
        "is_core": true,
        "match_level": "FULL",
        "source_profiles": ["hr"]
      },
      {
        "requirement_key": "labor_law",
        "label_ko": "노동법",
        "weight": 0.1625,
        "is_core": true,
        "match_level": "NONE",
        "source_profiles": ["hr"]
      },
      {
        "requirement_key": "payroll",
        "label_ko": "급여 관리",
        "weight": 0.1625,
        "is_core": true,
        "match_level": "FULL",
        "source_profiles": ["hr"]
      }
    ],
    "common_requirements": [
      {
        "requirement_key": "communication",
        "label_ko": "커뮤니케이션",
        "weight": 0.07,
        "is_core": false,
        "match_level": "STRONG",
        "source_profiles": ["hr", "operations"]
      }
    ],
    "requirement_overview": "입력된 근거를 기준으로 인사(HR)를 대표 프로필로 선택했습니다. 채용·온보딩·노동법·급여 관리 등 고유 역량(65%)과 커뮤니케이션 등 범용 역량(35%)을 평가합니다."
  }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| **`primary_profile`** | string | `meta.primary_profile`과 동일 |
| **`primary_profile_label_ko`** | string | 대표 프로필의 사용자 표시명 |
| **`secondary_profiles`** | array<string> | 선택. 보조 프로필 목록 |
| `unique_requirements` | array | `primary_profile`의 `skill_group=UNIQUE` requirement 전체. weight 합 = 0.65 |
| `common_requirements` | array | `primary_profile`의 `skill_group=COMMON` requirement 전체. weight 합 = 0.35 |
| `source_profiles` | array<string> | V1에서는 보통 `[primary_profile]`. 보조 프로필 힌트 표시가 필요할 때만 사용 |
| `requirement_overview` | string | 대표 프로필 선택 설명과 평가 기준 요약 |

**PDF 렌더링 위치:** Section 4 (Target Job Analysis) — Primary Profile Selection 요약,  
2개 테이블 (대표 프로필 고유 요구사항 / 공통 요구사항), `source_profiles` 배지는 보조 정보로만 표시, is_core 항목 강조

---

## 5. `skillMapping`

전체 requirement에 대한 매칭 결과를 FULL~NONE 순으로 정렬. (구조 변경 없음, weight 값은 primary_profile requirement 기준)

```json
{
  "skillMapping": {
    "matched": [
      {
        "skill_key": "recruiting",
        "label_ko": "채용 관리",
        "skill_group": "UNIQUE",
        "match_level": "FULL",
        "weight": 0.158,
        "weighted_score": 15.8
      }
    ],
    "unmatched": [
      {
        "skill_key": "labor_law",
        "label_ko": "노동법",
        "skill_group": "UNIQUE",
        "match_level": "NONE",
        "weight": 0.132,
        "weighted_score": 0.0
      }
    ]
  }
}
```

**PDF 렌더링 위치:** Section 5 (Skill Mapping) — progress bar 테이블, `skill_group`별 색상 구분

---

## 6. `evidenceMapping`

스킬별 원문 근거. (구조 변경 없음 — 단, `08_EVIDENCE_RULES.md`의 입력 소스가  
`career_histories` + `target_priority_text`로 확장됨에 따라, `target_priority_text`에서  
추출된 Evidence도 동일한 구조로 포함된다)

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
          "career_history_id": null,
          "company_name": null,
          "title": null,
          "original_text": "1순위: 인사관리(인력운영/평가, 급여)... 데이터 작업과 급여 관련 업무에 가장 큰 흥미를 느낌",
          "evidence_type": "EXPLICIT",
          "confidence_score": 0.9,
          "source": "target_priority_text"
        }
      ]
    }
  ]
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `evidences[].career_history_id` | string \| null | **v3 변경.** `target_priority_text`에서 추출된 evidence는 `null` |
| `evidences[].source` | string | **v3 신규.** `"career_history"` (기본, 생략 가능) \| `"target_priority_text"` |

**PDF 렌더링 위치:** Section 6 (Evidence Mapping) — 인용구 형태, `source="target_priority_text"`인  
항목은 "목표 입력에서 확인됨" 라벨 추가 표시

---

## 7. `scores`

점수 계산 결과 전체. (구조 변경 없음 — 단, `breakdown`의 weight는 primary_profile requirement 기준)

```json
{
  "scores": {
    "total": 78.5,
    "unique_total": 51.2,
    "common_total": 27.3,
    "core_penalty": -2.5,
    "breakdown": {
      "recruiting": {
        "weight": 0.158,
        "skill_group": "UNIQUE",
        "match_level": "FULL",
        "match_score": 1.0,
        "weighted_score": 15.8,
        "evidence_count": 2,
        "confidence_total": 1.9
      },
      "labor_law": {
        "weight": 0.132,
        "skill_group": "UNIQUE",
        "match_level": "NONE",
        "match_score": 0.0,
        "weighted_score": 0.0,
        "evidence_count": 0,
        "confidence_total": 0.0
      }
    }
  }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `total` | number | 최종 점수 (penalty 반영 후, 0–100) |
| `unique_total` | number | primary_profile UNIQUE 스킬군 weighted_score 합 (penalty 반영 후) |
| `common_total` | number | primary_profile COMMON 스킬군 weighted_score 합 |
| `core_penalty` | number | `is_core=true`이며 NONE/WEAK인 항목의 페널티 합 |
| `breakdown` | object | `primary_profile` requirement 전체 포함 |

> `total == round(unique_total + common_total, 1)` 이어야 한다.

**PDF 렌더링 위치:** Section 7 (Fit Score) — 레이더 차트, 점수 breakdown 테이블

---

## 8~11. `strengths`, `gaps`, `recommendations`, `roadmap`

**구조 변경 없음** (v2와 동일). 단, 이 섹션들이 참조하는 `skill_key`/`weight`/`is_core`는  
모두 §4의 `primary_profile` 기준 `unique_requirements`/`common_requirements`에서 가져온다.

`09_TEXT_TEMPLATE_RULES.md`의 템플릿에서 `{job_family_ko}` 같은 단일 라벨 변수는  
v3.1에서 `{primary_profile_label_ko}`로 대체된다 (`09_TEXT_TEMPLATE_RULES.md` 참조).

**PDF 렌더링 위치:** Section 8~11 (변경 없음)

---

## 12. `reportSections`

PDF 렌더링 순서 제어. V1은 12개 섹션 고정. (구조 변경 없음)

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

**PDF 렌더링 위치:** 전체 문서 구조 결정

---

## 부록 A: 구조 통일성 — 검증 방법 (v2와 동일)

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

# 서로 다른 primary_profile 결과를 가진 두 리포트도 key 구조는 100% 동일해야 함
hr_dominant = json.load(open("output/sample_report_hr_dominant.json"))
mixed = json.load(open("output/sample_report_mixed.json"))

assert extract_keys(hr_dominant) == extract_keys(mixed), "구조 불일치"
print("구조 통일성 검증 통과")
```

---

## 부록 B: 알려진 문제점 (§ Limitations)

| 문제 | 영향 | 비고 |
|------|------|------|
| LOW 리포트도 동일 구조를 사용함 | 점수는 산출되지만 신뢰도가 낮을 수 있음 | `meta.warning_message`를 화면/PDF에서 필수 표시 |
| `source_profiles`가 2개 이상인 requirement의 "어느 프로필에서 왔는지" 표시가 사용자에게 큰 의미가 없을 수 있음 | UI 복잡도 증가 대비 가치가 작을 가능성 | V1에서는 보조 배지로만 표시 |
| `meta.confidence_level == LOW`인 리포트도 `summary.fit_level`을 동일한 4단계로 표시함 | "낮은 신뢰도"와 "낮은 점수(LOW_FIT)"가 시각적으로 혼동될 위험 | `02_USER_FLOW.md`의 신뢰도 배너가 `fit_level` 표시와 명확히 분리되어야 함 |
| fallback으로 `operations`가 선택된 LOW 리포트 | 사용자가 직무 판단을 과신할 수 있음 | `warning_message`와 추가 입력 권장 문구를 함께 표시 |
