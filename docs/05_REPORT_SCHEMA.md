# 05 — Report JSON Schema

> **이 문서는 CareerFit에서 가장 중요한 문서다.**  
> Report JSON은 시스템의 **단일 진실 공급원(Single Source of Truth)**이며,  
> PDF, 화면, API 응답은 모두 이 구조를 파싱해 렌더링한다.

> **v3 핵심 변경:** `meta.target_job_family`(ENUM) → `meta.profile_blend`(object) +  
> `meta.weight_source`, `meta.confidence_level` 추가. `targetJobAnalysis`는  
> "선택된 1개 프로필"이 아니라 "블렌딩된 unique/common_requirements"를 담는다.

---

## 0. 설계 원칙

1. **모든 필드는 타입과 예시 값을 함께 명시한다.** placeholder가 아닌 실제 값으로 작성한다.
2. **구조 통일성:** N개 좌표축 중 어떤 비율로 블렌딩되었든, 이 구조의 **key 집합은 100% 동일**하다. 값만 달라진다.
3. **고유(UNIQUE) / 공통(COMMON) 스킬 구분이 스키마 레벨에 반영된다.**
4. **블렌딩 투명성 (v3 신규):** `meta.profile_blend`가 모든 weight 계산의 "근거"이며, 이 필드 없이는  
   `targetJobAnalysis`, `scores`의 값이 어떻게 도출되었는지 설명할 수 없다.
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
    "profile_blend": {
      "hr": 0.81,
      "operations": 0.19
    },
    "weight_source": "MANUAL_V1",
    "confidence_level": "HIGH"
  }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `report_id` | string (UUID) | 리포트 식별자 |
| `generated_at` | string (ISO 8601) | 생성 완료 시각 |
| ~~`target_job_family`~~ | ~~enum~~ | **v3에서 제거** |
| ~~`target_job_family_ko`~~ | ~~string~~ | **v3에서 제거** (대신 `profile_blend`의 각 키를 `data/skill_taxonomy.json` 또는 프로필 라벨 lookup으로 변환해 화면/PDF에서 표시) |
| `engine_version` | string (semver) | 엔진 버전 |
| `llm_used` | boolean | 텍스트 윤색에 LLM이 실제로 사용되었는지 |
| **`profile_blend`** | object | **v3 신규.** `{profile_key: ratio}`, 합계 1.0. `06_SCORING_RULES.md` §2.5의 블렌딩 결과 |
| **`weight_source`** | enum | **v3 신규.** `MANUAL_V1 \| CRAWLED_<YYYYQn>`. N개 좌표축(`job_requirements_*.json`)의 weight 출처 (`00_PROJECT_VISION.md` 트랙 2) |
| **`confidence_level`** | enum | **v3 신규.** `HIGH \| MEDIUM \| LOW`. `04_PAYLOAD_CONTRACT.md`의 동일 필드와 일치 |

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
    "blend_description": "당신의 경험은 'HR' 특성 81%와 'Operations' 특성 19%가 혼합된 프로필로 분석되었습니다.",
    "blend_display_mode": "MIXED",
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
| **`blend_description`** | string | **v3 신규.** `meta.profile_blend` 기반 자연어 설명. `09_TEXT_TEMPLATE_RULES.md` §2 템플릿 |
| **`blend_display_mode`** | enum | **v3 신규.** `SINGLE \| MIXED`. 최댓값 유사도 ≥ 0.7 → `SINGLE`, 미만 → `MIXED` (`06_SCORING_RULES.md` §2.5 임계값) |
| `unique_score` | number | UNIQUE 스킬군(블렌딩된 고유 핵심 역량) 합산 점수, 최대 65.0 |
| `unique_score_max` | number | 항상 65.0 |
| `common_score` | number | COMMON 스킬군(블렌딩된 범용 역량) 합산 점수, 최대 35.0 |
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

> `unique_score + common_score == total_score` (penalty 적용 후 합계가 일치해야 함. `06_SCORING_RULES.md` §6 참조 — 블렌딩 후에도 이 불변규칙은 유지됨)

**`blend_display_mode` 별 `blend_description` 예시:**

```
SINGLE (최댓값 >= 0.7):
  "당신의 경험은 'HR' 직무 특성과 강하게 일치합니다 (유사도 84%)."

MIXED (최댓값 < 0.7):
  "당신의 경험은 'HR' 특성 52%와 'Operations' 특성 31%가
   혼합된 프로필로 분석되었습니다."
```

**PDF 렌더링 위치:** Section 2 (Executive Summary) — 총점 큰 숫자, **블렌딩 Explanation 박스(최상단, v3 신규)**, UNIQUE/COMMON 분리 도넛 차트, one_line, 강점/갭 미리보기

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

> `extracted_skills[].skill_group`은 `meta.profile_blend`에서 가장 비중이 큰 프로필의  
> `skill_group` 분류를 기준으로 표시한다 (블렌딩된 `targetJobAnalysis.unique_requirements`/  
> `common_requirements`와 일치시킴 — §4 참조).

**PDF 렌더링 위치:** Section 3 (Career Profile) — 경력 타임라인 테이블 + 추출 스킬 태그 클라우드

---

## 4. `targetJobAnalysis` (v3 대폭 변경)

> v2: "선택된 1개 Job Family의 요구사항"  
> v3: "**블렌딩된 결과**로 만들어진, 이 사용자만의 unique/common requirements"

```json
{
  "targetJobAnalysis": {
    "profile_blend": {
      "hr": 0.81,
      "operations": 0.19
    },
    "unique_requirements": [
      {
        "requirement_key": "recruiting",
        "label_ko": "채용 관리",
        "weight": 0.158,
        "is_core": true,
        "match_level": "FULL",
        "source_profiles": ["hr"]
      },
      {
        "requirement_key": "training_and_onboarding",
        "label_ko": "교육/온보딩",
        "weight": 0.142,
        "is_core": true,
        "match_level": "FULL",
        "source_profiles": ["hr"]
      },
      {
        "requirement_key": "process_improvement",
        "label_ko": "프로세스 개선",
        "weight": 0.098,
        "is_core": false,
        "match_level": "PARTIAL",
        "source_profiles": ["operations"]
      },
      {
        "requirement_key": "labor_law",
        "label_ko": "노동법",
        "weight": 0.132,
        "is_core": true,
        "match_level": "NONE",
        "source_profiles": ["hr"]
      },
      {
        "requirement_key": "payroll",
        "label_ko": "급여 관리",
        "weight": 0.120,
        "is_core": false,
        "match_level": "FULL",
        "source_profiles": ["hr"]
      }
    ],
    "common_requirements": [
      {
        "requirement_key": "communication",
        "label_ko": "커뮤니케이션",
        "weight": 0.0735,
        "is_core": false,
        "match_level": "STRONG",
        "source_profiles": ["hr", "operations"]
      }
    ],
    "requirement_overview": "당신의 경험은 'HR' 특성 81%와 'Operations' 특성 19%가 혼합된 프로필로 분석되었습니다. 채용·온보딩·노동법 등 고유 역량(65%)과 커뮤니케이션 등 범용 역량(35%)을 함께 평가합니다."
  }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| **`profile_blend`** | object | `meta.profile_blend`와 동일 (이 섹션 내에서도 참조 가능하도록 중복 포함) |
| `unique_requirements` | array | 블렌딩 후 `skill_group=UNIQUE`인 requirement 전체. weight 합 = 0.65 |
| `common_requirements` | array | 블렌딩 후 `skill_group=COMMON`인 requirement 전체. weight 합 = 0.35 |
| **`unique_requirements[].source_profiles`** | array<string> | **v3 신규.** 이 requirement가 어느 좌표축(profile_key)에서 유래했는지. 여러 프로필에 공통으로 존재하면 배열에 여러 값 |
| `requirement_overview` | string | 템플릿 생성, `blend_description`과 일관된 내용 |

> **블렌딩 + 재정규화 규칙 (06_SCORING_RULES.md §2.5):**  
> N개 프로필의 requirement들을 `profile_blend` 비율로 가중합 → `requirement_key`별로 합산 →  
> UNIQUE 그룹 합계를 0.65로, COMMON 그룹 합계를 0.35로 재정규화.  
> 동일 `requirement_key`가 여러 프로필에 존재하면(`source_profiles`에 2개 이상) weight가 가중 합산된다  
> (예: `communication`이 hr과 operations 양쪽의 COMMON에 있으면 두 기여분이 합산됨).

> `unique_requirements`의 개수는 블렌딩 결과에 따라 4~6개로 가변적일 수 있다  
> (두 프로필의 UNIQUE 항목 union, 중복 시 병합). weight 합은 항상 0.65다.

**PDF 렌더링 위치:** Section 4 (Target Job Analysis) — **상단에 profile_blend 시각화(막대 또는 도넛, v3 신규)**,  
2개 테이블 (블렌딩된 고유 요구사항 / 공통 요구사항), `source_profiles`를 작은 배지로 표시,  
is_core 항목 강조

---

## 5. `skillMapping`

전체 requirement에 대한 매칭 결과를 FULL~NONE 순으로 정렬. (구조 변경 없음, weight 값이 블렌딩 결과로 대체됨)

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

점수 계산 결과 전체. (구조 변경 없음 — 단, `breakdown`의 weight가 블렌딩 결과)

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
| `unique_total` | number | 블렌딩된 UNIQUE 스킬군 weighted_score 합 (penalty 반영 후) |
| `common_total` | number | 블렌딩된 COMMON 스킬군 weighted_score 합 |
| `core_penalty` | number | `is_core=true`이며 NONE/WEAK인 항목의 페널티 합 |
| `breakdown` | object | **블렌딩된** requirement 전체 포함 (4~6개 UNIQUE + COMMON 합 union, 가변) |

> `total == round(unique_total + common_total, 1)` 이어야 한다. 블렌딩 후에도 이 불변규칙 유지.

**PDF 렌더링 위치:** Section 7 (Fit Score) — 레이더 차트, 점수 breakdown 테이블

---

## 8~11. `strengths`, `gaps`, `recommendations`, `roadmap`

**구조 변경 없음** (v2와 동일). 단, 이 섹션들이 참조하는 `skill_key`/`weight`/`is_core`는  
모두 §4의 블렌딩된 `unique_requirements`/`common_requirements`에서 가져온다.

`09_TEXT_TEMPLATE_RULES.md`의 템플릿에서 `{job_family_ko}` 같은 단일 라벨 변수는  
v3에서 `{blend_description}` 또는 가장 비중이 큰 프로필의 `label_ko`로 대체된다  
(`09_TEXT_TEMPLATE_RULES.md` 참조).

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

# 서로 다른 profile_blend 결과를 가진 두 리포트도 key 구조는 100% 동일해야 함
hr_dominant = json.load(open("output/sample_report_hr_dominant.json"))
mixed = json.load(open("output/sample_report_mixed.json"))

assert extract_keys(hr_dominant) == extract_keys(mixed), "구조 불일치"
print("구조 통일성 검증 통과")
```

---

## 부록 B: 알려진 문제점 (§ Limitations)

| 문제 | 영향 | 비고 |
|------|------|------|
| `unique_requirements`/`common_requirements`의 개수가 가변(4~6개)이라 PDF 테이블 행 수가 리포트마다 다름 | `10_PDF_TEMPLATE_SPEC.md`의 고정 레이아웃 가정과 충돌 가능 | 테이블을 동적 행 수 대응 레이아웃으로 설계 필요 |
| `source_profiles`가 2개 이상인 requirement의 "어느 프로필에서 왔는지" 표시가 사용자에게 큰 의미가 없을 수 있음 | UI 복잡도 증가 대비 가치가 작을 가능성 | v3.1에서 배지 노출 여부 A/B 검토 |
| `meta.confidence_level == LOW`인 리포트도 `summary.fit_level`을 동일한 4단계로 표시함 | "낮은 신뢰도"와 "낮은 점수(LOW_FIT)"가 시각적으로 혼동될 위험 | `02_USER_FLOW.md`의 신뢰도 배너가 `fit_level` 표시와 명확히 분리되어야 함 |
| `blend_display_mode=MIXED`일 때 `requirement_overview` 문장이 두 프로필 이름을 모두 언급해야 해서 문장이 길어짐 | 가독성 저하 가능 | `09_TEXT_TEMPLATE_RULES.md`에서 2개까지만 언급, 3개 이상 혼합 시 "복합적" 등으로 단순화 |