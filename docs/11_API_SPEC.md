# 11 — API Specification

**Base URL:** `https://api.careerfit.kr/v1`  
**Content-Type:** `application/json`  
**인증:** V1 없음 (비로그인)

> **v3 변경:** `target_job_family` ENUM 완전 제거. `target_priority_text` 추가.  
> 응답에서 `target_job_family` → `primary_profile`로 대체.  
> `INVALID_JOB_FAMILY` 에러 코드 제거.

---

## V1 API

### POST /reports

리포트 생성 요청.

**Request:**
```http
POST /v1/reports
Content-Type: application/json

{
  "target_priority_text": "1순위: 인사관리(인력운영/평가, 급여), 2순위: 인재개발(교육, 채용). 노동법 공부를 통해 실무에 적용하는 데 보람을 느끼고, 급여/데이터 작업에 가장 큰 흥미를 느낍니다.",
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

**Validation:**

| 필드 | 타입 | 제약 |
|------|------|------|
| `target_priority_text` | string | min 30, max 1000 |
| `career_histories` | array | min 1, max 10 |
| `career_histories[].company_name` | string | max 100 |
| `career_histories[].title` | string | max 100 |
| `career_histories[].start_date` | string | `"YYYY-MM"` |
| `career_histories[].end_date` | string \| null | `"YYYY-MM"` 또는 null |
| `career_histories[].responsibilities` | string | min 50, max 3000 |
| `career_histories[].achievements` | string \| null | max 2000 |

> `target_job_family` ENUM 필드는 v3에서 완전히 제거됨. 클라이언트가 이 필드를 전송해도 무시한다.

**Response 201:**
```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "CREATED",
  "created_at": "2025-06-01T12:00:00Z"
}
```

> LOW confidence 입력도 201로 접수된다. 분석 불가로 422를 반환하지 않으며,  
> 완료 리포트의 `meta.confidence_level="LOW"`와 `meta.warning_message`로 안내한다.  
> `force: true`는 v3.1에서 deprecated이며 사용할 필요가 없다.

---

### GET /reports/{report_id}

리포트 상태 조회 및 완료 결과 반환.

**Response 200 (READY):**
```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "READY",
  "created_at": "2025-06-01T12:00:00Z",
  "completed_at": "2025-06-01T12:03:45Z",
  "report": {
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
}
```

> v2의 `"target_job_family": "HR"` 응답 필드가 제거됨.  
> 대신 `report.meta.primary_profile`에서 대표 프로필을 확인한다.

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

## Error Code 목록

`04_PAYLOAD_CONTRACT.md` §4와 동일. 단 v3 변경 사항 반영:

| code | HTTP | 설명 |
|------|------|------|
| `VALIDATION_ERROR` | 400 | 입력값 유효성 오류 (길이 등) |
| ~~`INVALID_JOB_FAMILY`~~ | ~~400~~ | **v3에서 제거** |
| ~~`LOW_CONFIDENCE_INPUT`~~ | ~~422~~ | **v3.1에서 deprecated.** LOW는 정상 리포트로 생성 |
| ~~`INSUFFICIENT_EVIDENCE`~~ | ~~422~~ | **v3.1에서 deprecated.** 분석 불가 차단 없음 |
| `REPORT_NOT_FOUND` | 404 | report_id 없음 |
| `REPORT_EXPIRED` | 410 | 리포트 만료 |
| `REPORT_STILL_PROCESSING` | 202 | 아직 생성 중 |
| `ENGINE_ERROR` | 500 | 분석 엔진 내부 오류 |
| `ENGINE_TIMEOUT` | 504 | 분석 엔진 타임아웃 |
| `PDF_GENERATION_FAILED` | 500 | PDF 생성 실패 |
| `INTERNAL_ERROR` | 500 | 알 수 없는 내부 오류 |

---

## V2 예정 API

| Method | Path | 설명 |
|--------|------|------|
| POST | /admin/sync-job-postings | 사람인/워크넷 공고 동기화 → `job_requirement_profiles.weight` 갱신 (트랙 2) |
| GET | /profiles | N개 requirement profile 목록 + 고유/공통 스킬 구성 |
| GET | /profiles/{profile_key}/requirements | 좌표축별 요구사항 |
| GET | /reports/{id}/share | 공유 링크 생성 |
| GET | /reports/{id}/market-analysis | `marketAnalysis` 섹션 (V1.1) |

---

## 알려진 문제점 (§ Limitations)

| 문제 | 영향 | 비고 |
|------|------|------|
| LOW 입력도 성공 응답으로 진행됨 | 사용자가 결과를 과신할 수 있음 | `warning_message`를 화면/PDF에서 필수 표시 |
| `primary_profile` fallback이 사용자 의도와 다를 수 있음 | 낮은 근거 입력에서 추천 방향이 부정확할 수 있음 | `evidence_count`와 추가 입력 권장 문구를 함께 제공 |
