# 04 — Payload Contract

프론트엔드 → 백엔드 → 엔진 간 데이터 계약 정의.  
모든 인터페이스는 이 문서를 단일 기준으로 삼는다.

---

## 1. Frontend → Backend

### POST /reports (리포트 생성 요청)

**Request Body:**
```json
{
  "target_job_family": "HR",
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
- `target_job_family`: ENUM (HR|MARKETING|DATA|PRODUCT|OPERATIONS)
- `career_histories`: array, min 1, max 10
- `career_histories[].company_name`: string, max 100
- `career_histories[].title`: string, max 100
- `career_histories[].start_date`: "YYYY-MM" format
- `career_histories[].end_date`: "YYYY-MM" format or null
- `career_histories[].responsibilities`: string, min 50, max 3000
- `career_histories[].achievements`: string, max 2000, nullable

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
  "target_job_family": "HR",
  "created_at": "2025-06-01T12:00:00Z",
  "completed_at": "2025-06-01T12:03:45Z",
  "report": { /* 05_REPORT_SCHEMA.md 구조 */ }
}
```

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
  "target_job_family": "HR",
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
  "job_requirements": [
    {
      "requirement_key": "recruiting",
      "label_ko": "채용 관리",
      "weight": 0.20,
      "is_core": true
    }
  ]
}
```

---

### Algorithm Response

엔진이 백엔드로 반환하는 분석 결과.

```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUCCESS",
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
      "match_level": "FULL",
      "match_score": 1.0,
      "matched_evidence_ids": ["ev-uuid-001"],
      "reasoning": "JD 작성, 서류 검토, 면접 진행 등 채용 전 과정에 대한 직접 경험 존재"
    }
  ],
  "total_score": 78.5,
  "score_breakdown": {
    "recruiting": {
      "weight": 0.20,
      "match_level": "FULL",
      "match_score": 1.0,
      "weighted_score": 20.0,
      "evidence_count": 2
    }
  },
  "gaps": [
    {
      "requirement_key": "labor_law",
      "gap_severity": "MAJOR",
      "gap_reason": "노동법 관련 직접 경험이나 언급이 없음",
      "recommendation": "노동법 자격증 취득 또는 관련 프로젝트 경험 추가",
      "priority_order": 1
    }
  ],
  "report_json": { /* 05_REPORT_SCHEMA.md 전체 구조 */ }
}
```

---

## 3. Report Status 정의

| status | 의미 | 다음 상태 |
|--------|------|----------|
| `CREATED` | 요청 접수, 큐 대기 | ANALYZING |
| `ANALYZING` | 엔진 분석 진행 중 | PDF_GENERATING or FAILED |
| `PDF_GENERATING` | PDF 생성 진행 중 | READY or FAILED |
| `READY` | 완료, 리포트 열람 가능 | (종단) |
| `FAILED` | 실패 | CREATED (수동 재시도) |

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
        "field": "career_histories[0].responsibilities",
        "message": "담당 업무는 최소 50자 이상 입력해주세요."
      }
    ]
  }
}
```

**Error Code 목록:**

| code | HTTP | 설명 |
|------|------|------|
| `VALIDATION_ERROR` | 400 | 입력값 유효성 오류 |
| `REPORT_NOT_FOUND` | 404 | report_id 없음 |
| `REPORT_EXPIRED` | 410 | 리포트 만료 (30일 초과) |
| `REPORT_STILL_PROCESSING` | 202 | 아직 생성 중 (폴링 필요) |
| `ENGINE_ERROR` | 500 | 분석 엔진 내부 오류 |
| `ENGINE_TIMEOUT` | 504 | 분석 엔진 타임아웃 |
| `PDF_GENERATION_FAILED` | 500 | PDF 생성 실패 |
| `INTERNAL_ERROR` | 500 | 알 수 없는 내부 오류 |
# 11 — API Specification

**Base URL:** `https://api.careerfit.kr/v1`  
**Content-Type:** `application/json`  
**인증:** V1 없음 (비로그인)

---

## V1 API

### POST /reports
리포트 생성 요청.

**Request:**
```http
POST /v1/reports
Content-Type: application/json

{
  "target_job_family": "HR",
  "career_histories": [
    {
      "company_name": "주식회사 예시",
      "title": "HR 매니저",
      "start_date": "2021-03",
      "end_date": "2023-12",
      "is_current": false,
      "responsibilities": "신입사원 채용 전 과정 담당...",
      "achievements": "채용 목표 120% 달성..."
    }
  ]
}
```

**Response 201:**
```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "CREATED",
  "created_at": "2025-06-01T12:00:00Z"
}
```

---

### GET /reports/{report_id}
리포트 상태 조회 및 완료 결과 반환.

**Response 200 (READY):**
```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "READY",
  "target_job_family": "HR",
  "created_at": "2025-06-01T12:00:00Z",
  "completed_at": "2025-06-01T12:03:45Z",
  "report": { /* Report JSON */ }
}
```

**Response 200 (진행 중):**
```json
{
  "report_id": "...",
  "status": "ANALYZING",
  "report": null
}
```

**Response 404:**
```json
{ "error": { "code": "REPORT_NOT_FOUND", "message": "리포트를 찾을 수 없습니다." } }
```

**Response 410:**
```json
{ "error": { "code": "REPORT_EXPIRED", "message": "리포트가 만료되었습니다." } }
```

---

### GET /reports/{report_id}/pdf
생성된 PDF 다운로드.

**Response 200:**
```http
Content-Type: application/pdf
Content-Disposition: attachment; filename="careerfit-{report_id}.pdf"

[PDF binary]
```

**Response 202 (아직 PDF 생성 중):**
```json
{ "error": { "code": "REPORT_STILL_PROCESSING", "message": "PDF를 생성 중입니다." } }
```

---

## V2 예정 API (구현 안 함)

| Method | Path | 설명 |
|--------|------|------|
| POST | /admin/sync-job-postings | 채용 공고 동기화 |
| GET | /job-families | 지원 Job Family 목록 |
| GET | /job-families/{family}/requirements | Job Family별 요구사항 |
| GET | /reports/{id}/share | 공유 링크 생성 |