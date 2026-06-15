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
      "company_name": "주식회사 ABC",
      "title": "HR 매니저",
      "start_date": "2020-03",
      "end_date": "2023-12",
      "is_current": false,
      "responsibilities": "신입 채용 전 과정 운영. JD 작성, 서류 검토, 임원 면접 일정 조율 및 진행...",
      "achievements": "연간 채용 목표 120% 달성. 온보딩 만족도 4.6/5.0 달성."
    }
  ]
}
```

`target_job_family`는 다음 10개 값 중 하나 (`04_PAYLOAD_CONTRACT.md` §1, `03_ERD.md` §2.2):

```
HR | MARKETING | DATA | PRODUCT | OPERATIONS |
SALES | DESIGN | FINANCE | ENGINEERING | CUSTOMER_SUCCESS
```

**Response 201:**
```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "CREATED",
  "created_at": "2025-06-01T12:00:00Z"
}
```

**Response 400 (잘못된 job_family):**
```json
{
  "error": {
    "code": "INVALID_JOB_FAMILY",
    "message": "target_job_family는 HR, MARKETING, DATA, PRODUCT, OPERATIONS, SALES, DESIGN, FINANCE, ENGINEERING, CUSTOMER_SUCCESS 중 하나여야 합니다."
  }
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
  "report": { /* 05_REPORT_SCHEMA.md — 12 top-level keys */ }
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

## 내부 참조 — Error Code 전체 목록

`04_PAYLOAD_CONTRACT.md` §4와 동일. API 구현 시 이 표를 단일 기준으로 삼는다.

| code | HTTP | 설명 |
|------|------|------|
| `VALIDATION_ERROR` | 400 | 입력값 유효성 오류 |
| `INVALID_JOB_FAMILY` | 400 | target_job_family가 10개 ENUM에 포함되지 않음 |
| `REPORT_NOT_FOUND` | 404 | report_id 없음 |
| `REPORT_EXPIRED` | 410 | 리포트 만료 (30일 초과) |
| `REPORT_STILL_PROCESSING` | 202 | 아직 생성 중 (폴링 필요) |
| `ENGINE_ERROR` | 500 | 분석 엔진 내부 오류 |
| `ENGINE_TIMEOUT` | 504 | 분석 엔진 타임아웃 |
| `PDF_GENERATION_FAILED` | 500 | PDF 생성 실패 |
| `INTERNAL_ERROR` | 500 | 알 수 없는 내부 오류 |

---

## V2 예정 API (구현 안 함)

| Method | Path | 설명 |
|--------|------|------|
| POST | /admin/sync-job-postings | 사람인/워크넷 공고 동기화 → `job_requirement_stats.weight` 갱신 (오프라인 배치, `00_PROJECT_VISION.md` 시장 데이터 섹션 참조) |
| GET | /job-families | 10개(이상) Job Family 목록 + 고유/공통 스킬 구성 |
| GET | /job-families/{family}/requirements | Job Family별 요구사항 (UNIQUE/COMMON 구분 포함) |
| GET | /reports/{id}/share | 공유 링크 생성 |
| GET | /reports/{id}/market-analysis | `marketAnalysis` 섹션 (V1.1에서 Report JSON에 추가 예정) |