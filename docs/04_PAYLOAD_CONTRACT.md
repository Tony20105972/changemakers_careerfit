# 04 — Payload Contract

프론트엔드 → 백엔드 → 엔진 간 데이터 계약 정의.  
모든 인터페이스는 이 문서를 단일 기준으로 삼는다.

> **v3.1 핵심 변경:** `target_job_family` ENUM 제거 유지. `target_priority_text`(자유 텍스트) 추가.  
> Algorithm Response는 사용자-facing 기준으로 `primary_profile`, `secondary_profiles`, `confidence_level`을 반환한다.  
> `profile_blend`는 V1에서 필수 계약이 아니며, 필요 시 내부 디버그 값으로만 둔다.
> **Schema-First 원칙:** 이 문서는 `05_REPORT_SCHEMA.md`, `03_ERD.md`보다 먼저 확정된다.

---

## 1. Frontend → Backend

### POST /reports (리포트 생성 요청)

**Request Body:**
```json
{
  "target_priority_text": "1순위: 인사관리(인력운영/평가, 급여), 2순위: 인재개발(교육, 채용). 데이터 작업과 급여 관련 업무에 가장 흥미를 느끼고, 노동법 공부를 통해 실무에 적용하는 데 보람을 느낍니다.",
  "career_histories": [
    {
      "company_name": "주식회사 예시",
      "title": "HR 매니저",
      "start_date": "2021-03",
      "end_date": "2023-12",
      "is_current": false,
      "responsibilities": "신입사원 채용 전 과정 담당. JD 작성, 서류 검토, 면접 진행, 합격자 온보딩 프로세스 설계 및 운영.",
      "achievements": "연간 채용 목표 120% 달성. 온보딩 만족도 4.6/5.0 달성."
    }
  ]
}
```

**Validation Rules:**

| 필드 | 타입 | 제약 |
|------|------|------|
| ~~`target_job_family`~~ | ~~ENUM~~ | **v3에서 제거** |
| `target_priority_text` | string | min 30, max 1000 (v3 신규, 필수) |
| `career_histories` | array | min 1, max 10 |
| `career_histories[].company_name` | string | max 100 |
| `career_histories[].title` | string | max 100 |
| `career_histories[].start_date` | string | `"YYYY-MM"` |
| `career_histories[].end_date` | string \| null | `"YYYY-MM"` 또는 null (is_current=true일 때) |
| `career_histories[].is_current` | boolean | default false |
| `career_histories[].responsibilities` | string | min 50, max 3000 |
| `career_histories[].achievements` | string \| null | max 2000 |

**Response (201 Created):**
```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "CREATED",
  "created_at": "2025-06-01T12:00:00Z"
}
```

---

### GET /reports/{report_id} (상태 조회 및 리포트 조회)

**Response (200 OK) — READY 상태:**
```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "READY",
  "created_at": "2025-06-01T12:00:00Z",
  "completed_at": "2025-06-01T12:03:45Z",
  "report": { /* 05_REPORT_SCHEMA.md 구조 */ }
}
```

> v2의 `"target_job_family": "HR"` 필드는 제거됨.  
> 대신 `report.meta.primary_profile`에 엔진이 선택한 대표 프로필이 포함된다.

**Response (200 OK) — 진행 중:**
```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "ANALYZING",
  "created_at": "2025-06-01T12:00:00Z",
  "completed_at": null,
  "report": null
}
```

**Response (200 OK) — FAILED:**
```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "FAILED",
  "error": {
    "code": "ENGINE_TIMEOUT",
    "message": "분석 중 시간 초과가 발생했습니다."
  }
}
```

---

## 2. Backend → Engine

### Algorithm Request

백엔드가 분석 엔진을 호출할 때 전달하는 구조체.

```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "target_priority_text": "1순위: 인사관리(인력운영/평가, 급여), 2순위: 인재개발(교육, 채용)...",
  "career_histories": [
    {
      "id": "ch-uuid-001",
      "company_name": "주식회사 예시",
      "title": "HR 매니저",
      "start_date": "2021-03-01",
      "end_date": "2023-12-31",
      "is_current": false,
      "responsibilities": "신입사원 채용 전 과정 담당...",
      "achievements": "연간 채용 목표 120% 달성...",
      "sort_order": 0
    }
  ],
  "profile_pool": [
    {
      "profile_key": "hr",
      "label_ko": "인사(HR)",
      "requirements": [
        { "requirement_key": "recruiting", "skill_group": "UNIQUE", "weight": 0.1625, "is_core": true, "label_ko": "채용 관리" },
        { "requirement_key": "communication", "skill_group": "COMMON", "weight": 0.07, "is_core": false, "label_ko": "커뮤니케이션" }
      ]
    },
    {
      "profile_key": "operations",
      "label_ko": "운영(Operations)",
      "requirements": [ "...9개 requirement..." ]
    }
  ]
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `target_priority_text` | string | v3 신규. Evidence 추출 시 `career_histories`와 함께 입력으로 사용 |
| `profile_pool` | array | **N개 프로필 전체** (`data/job_requirements_*.json` 10개, `13_Development_Roadmap.md` Day 6 산출물). primary profile 선택과 fallback에 사용 |
| `profile_pool[].profile_key` | string | 내부 식별자 (구 `target_job_family` 값과 동일한 문자열셋: hr, marketing, data, ...) — **사용자에게 노출되지 않음** |

> `04_PAYLOAD_CONTRACT.md` v2의 `job_requirements` 단일 배열(선택된 1개 프로필)이  
> v3.1에서는 `profile_pool`(N개 프로필 전체)로 대체된다. 엔진은 이 중 하나를 `primary_profile`로 선택한다.

---

### Algorithm Response

엔진이 백엔드로 반환하는 분석 결과.

```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUCCESS",
  "user_vector": {
    "recruiting": 1.9,
    "training_and_onboarding": 1.85,
    "payroll": 1.9,
    "performance_management": 0.85,
    "labor_law": 0.0
  },
  "primary_profile": "hr",
  "secondary_profiles": ["operations"],
  "confidence_level": "HIGH",
  "evidence_count": 10,
  "warning_message": null,
  "evidences": [
    {
      "career_history_id": "ch-uuid-001",
      "skill_key": "recruiting",
      "original_text": "신입사원 채용 전 과정 담당. JD 작성, 서류 검토, 면접 진행",
      "evidence_type": "EXPLICIT",
      "confidence_score": 1.0
    }
  ],
  "requirement_matches": [
    {
      "requirement_key": "recruiting",
      "skill_group": "UNIQUE",
      "match_level": "FULL",
      "match_score": 1.0,
      "matched_evidence_ids": ["ev-uuid-001"],
      "confidence_total": 1.9,
      "reasoning": "JD 작성, 서류 검토, 면접 진행 등 채용 전 과정에 대한 직접 경험 존재 (EXPLICIT 1.0 + ACHIEVED 0.9)"
    }
  ],
  "selected_requirements": [
    {
      "requirement_key": "recruiting",
      "skill_group": "UNIQUE",
      "weight": 0.1625,
      "is_core": true,
      "label_ko": "채용 관리"
    }
  ],
  "total_score": 78.5,
  "score_breakdown": {
    "recruiting": {
      "weight": 0.1625,
      "skill_group": "UNIQUE",
      "match_level": "FULL",
      "match_score": 1.0,
      "weighted_score": 15.8,
      "evidence_count": 2
    }
  },
  "gaps": [
    {
      "requirement_key": "labor_law",
      "skill_group": "UNIQUE",
      "gap_severity": "MAJOR",
      "gap_reason": "노동법 관련 직접 경험이나 언급이 없음",
      "recommendation": "노동법 자격증 취득 또는 관련 프로젝트 경험 추가",
      "priority_order": 1
    }
  ],
  "report_json": { /* 05_REPORT_SCHEMA.md 전체 구조 */ }
}
```

### v3 신규 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `user_vector` | object | `{skill_key: confidence_total}`. `08_EVIDENCE_RULES.md`로 `career_histories + target_priority_text`에서 추출된 79차원 벡터 (0인 차원은 생략 가능) |
| `primary_profile` | string | 엔진이 최종 리포트 기준으로 선택한 대표 `profile_id`. 예: `hr`, `data`, `marketing` |
| `secondary_profiles` | array<string> | 선택. 입력에서 일부 근거가 감지된 보조 프로필 목록. 사용자-facing 핵심 판단에는 사용하지 않음 |
| `confidence_level` | enum | `HIGH \| MEDIUM \| LOW`. evidence_count 기준 (`06_SCORING_RULES.md` §2.6) |
| `evidence_count` | integer | 추출된 evidence 총 개수. confidence 산정과 LOW warning에 사용 |
| `warning_message` | string \| null | LOW에서는 필수. 반드시 "입력 정보가 부족하여 일부 결과는 추정에 기반합니다" 문구 포함 |
| `selected_requirements` | array | `primary_profile`의 65/35 requirement. `requirement_matches`, `score_breakdown` 계산의 기준 |
| `confidence_total` (기존 유지) | number | `requirement_matches[]`의 동일 skill_key에 매핑된 모든 evidence의 confidence_score 합 |

> `profile_blend`, `blended_requirements`, `blend_display_mode`, `blend_description`은 V1 사용자-facing 계약에서 제거된다.  
> 디버깅이 필요하면 `report_json.internal_debug.profile_blend`처럼 optional 내부 필드로만 허용한다.

---

## 3. Report Status 정의

| status | 의미 | 다음 상태 |
|--------|------|----------|
| `CREATED` | 요청 접수, 큐 대기 | ANALYZING |
| `ANALYZING` | 엔진 분석 진행 중 (Evidence 추출 + primary profile 선택 + 점수 계산) | PDF_GENERATING or FAILED |
| `PDF_GENERATING` | PDF 생성 진행 중 | READY or FAILED |
| `READY` | 완료, 리포트 열람 가능 | (종단) |
| `FAILED` | 실패 | CREATED (수동 재시도) |

**상태 전이 허용 표 (구현 시 강제):**
```python
VALID_TRANSITIONS = {
    "CREATED":        ["ANALYZING", "FAILED"],
    "ANALYZING":      ["PDF_GENERATING", "FAILED"],
    "PDF_GENERATING": ["READY", "FAILED"],
    "READY":          [],
    "FAILED":         [],
}
```

---

## 4. Error Format

모든 에러 응답은 아래 구조를 따른다.

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "입력 데이터가 올바르지 않습니다.",
    "details": [
      {
        "field": "target_priority_text",
        "message": "목표 직무와 이유는 최소 30자 이상 입력해주세요."
      }
    ]
  }
}
```

**Error Code 목록:**

| code | HTTP | 설명 |
|------|------|------|
| `VALIDATION_ERROR` | 400 | 입력값 유효성 오류 (글자 수 등) |
| ~~`INVALID_JOB_FAMILY`~~ | ~~400~~ | **v3에서 제거** (ENUM 없음) |
| ~~`LOW_CONFIDENCE_INPUT`~~ | ~~422~~ | **v3.1에서 비활성화**. 낮은 근거량은 `confidence_level=LOW` 리포트로 흡수 |
| ~~`INSUFFICIENT_EVIDENCE`~~ | ~~422~~ | **v3.1에서 비활성화**. 분석 불가로 차단하지 않음 |
| `REPORT_NOT_FOUND` | 404 | report_id 없음 |
| `REPORT_EXPIRED` | 410 | 리포트 만료 (30일 초과) |
| `REPORT_STILL_PROCESSING` | 202 | 아직 생성 중 (폴링 필요) |
| `ENGINE_ERROR` | 500 | 분석 엔진 내부 오류 |
| `ENGINE_TIMEOUT` | 504 | 분석 엔진 타임아웃 |
| `PDF_GENERATION_FAILED` | 500 | PDF 생성 실패 |
| `INTERNAL_ERROR` | 500 | 알 수 없는 내부 오류 |

---

## 5. 알려진 문제점 (§ Limitations)

| 문제 | 영향 | 비고 |
|------|------|------|
| `profile_pool`을 매 요청마다 Algorithm Request에 통째로 전달 (N=10 × 9 requirements) | 요청 페이로드 크기 증가 (미미하지만 N이 커지면 누적) | N이 50+ 규모가 되면 엔진 측에 캐싱하고 `profile_pool_version`만 전달하는 방식으로 전환 검토 |
| `confidence_level: LOW`일 때도 `report_json`은 동일한 구조로 생성됨 | "신뢰도 낮음"이 구조적 차이가 아니라 플래그로만 표현 → 화면/PDF에서 이 플래그를 누락하면 사용자가 인지 못함 | `02_USER_FLOW.md` §2.4, `10_PDF_TEMPLATE_SPEC.md`에서 필수 렌더링 항목으로 명시 필요 |
| evidence가 거의 없으면 `primary_profile`이 fallback으로 선택될 수 있음 | 점수와 추천이 추정 기반이 됨 | `warning_message`와 `evidence_count`를 필수 렌더링해 차단 대신 투명하게 고지 |
