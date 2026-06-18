# 02 — User Flow

---

## 1. 전체 흐름

```
Landing Page (/)
    │
    │  [리포트 만들기] 클릭
    ▼
Report Form (/report/new)
    │
    │  [분석 시작] 클릭
    │  (※ LOW 입력도 진행, 리포트에서 warning 표시 — §2.2 참조)
    ▼
Generating (/report/:id?status=generating)
    │
    │  polling → status: READY
    ▼
Report Result (/report/:id)
    │  (※ primary_profile 기반 Explanation 표시 — §2.4 참조)
    │
    │  [PDF 다운로드] 클릭
    ▼
PDF Download
```

---

## 2. 화면 상세

### 2.1 Landing Page — `/`

**목적:** 서비스 가치 전달 및 입력 시작 유도

**필수 요소:**
- 서비스 한 줄 설명: "직무를 선택하지 않아도, 당신의 경험을 분석해 맞춤 적합도를 알려드립니다"
- N=10 좌표축은 **사용자에게 직접 노출하지 않음**. 대신 "이런 경험을 분석할 수 있어요" 형태의  
  예시 카드 5~6개를 보여줌 (예: "HR 매니저", "그로스해커", "데이터 분석가", "HRBP" 등 —  
  대표 직무와 보조 가능성이 모두 드러나는 예시로 "카테고리 강제 없음"을 직관적으로 전달)
- 예시 리포트 썸네일 또는 스코어 미리보기 (HR, Data 단일 정체성 샘플 + 혼합형 샘플 1개)
- CTA 버튼: "지금 무료로 분석하기"

**v2 → v3 변경:** "10개 Job Family 그리드"가 제거됨. 좌표축은 내부 구현 디테일이며  
사용자에게 "선택지"로 노출되지 않는다.

**상태:** 정적 페이지, 인증 불필요

---

### 2.2 Report Form — `/report/new`

**목적:** 분석에 필요한 커리어 정보 및 목표/우선순위 수집

**입력 필드:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| ~~target_job_family~~ | ~~select~~ | ~~✅~~ | **v3에서 제거** |
| **target_priority_text** | textarea | ✅ (v3 신규) | 목표 직무와 그 이유를 자유롭게 입력 (최소 30자) |
| career_histories | array | ✅ | 1개 이상 |
| └ company_name | text | ✅ | 회사명 |
| └ title | text | ✅ | 직책/직함 |
| └ start_date | month picker | ✅ | 입사 연월 |
| └ end_date | month picker | ✅ | 퇴사 연월 (재직 중이면 "현재" 선택) |
| └ is_current | checkbox | - | 현재 재직 중 여부 |
| └ responsibilities | textarea | ✅ | 담당 업무 자유 텍스트 (최소 50자) |
| └ achievements | textarea | - | 주요 성과 자유 텍스트 |

**target_priority_text 입력 가이드 (placeholder 예시):**
```
"1순위: 인사관리(인력운영/평가, 급여), 2순위: 인재개발(교육, 채용).
 데이터 작업과 급여 관련 업무에 가장 흥미를 느끼고,
 노동법 공부를 통해 실무에 적용하는 데 보람을 느낍니다."
```

**UX 규칙:**
- 경력 추가는 "+ 경력 추가" 버튼으로 동적 추가
- 경력은 최소 1개, 최대 10개
- 각 경력의 responsibilities는 최소 50자 (가이드 문구 표시)
- `target_priority_text`는 최소 30자 (가이드 문구 표시)
- 제출 전 클라이언트 사이드 유효성 검사 (길이 기준)

**LOW confidence 안내 (v3.1 신규 — 핵심):**

```
제출 시 클라이언트 검증(글자 수)을 통과해도,
서버에서 Evidence 추출 후 evidence_count가 낮아도 리포트 생성을 차단하지 않는다.
→ POST /reports는 정상 접수
→ 완료 리포트에서 `confidence_level=LOW`, `warning_message`, `evidence_count`를 표시
→ 폼에서는 사전 도움말로 "더 구체적으로 작성하면 분석 정확도가 높아집니다"를 안내
```

LOW는 **차단이 아니라 리포트 상태 플래그**다. 사용자는 별도 force 재요청 없이  
결과를 받으며, 리포트 내에서 낮은 신뢰도임을 확인한다 (`05_REPORT_SCHEMA.md` 참조).

**제출 시 동작:**
1. `POST /reports` API 호출 (`target_priority_text` 포함)
2. 응답으로 `report_id` 수신
3. `/report/:id?status=generating` 으로 리다이렉트

---

### 2.3 Generating — `/report/:id?status=generating`

**목적:** 리포트 생성 진행 상태 표시 및 완료 감지

**동작:**
- 3초 간격으로 `GET /reports/:id` 폴링
- `status`에 따라 UI 업데이트:

| status | 표시 내용 |
|--------|----------|
| CREATED | "요청이 접수되었습니다..." |
| ANALYZING | "경험을 분석하고 대표 프로필을 선택하고 있습니다..." |
| PDF_GENERATING | "리포트를 생성 중입니다..." |
| READY | 자동으로 `/report/:id` 로 이동 |
| FAILED | 오류 메시지 표시 + 재시도 버튼 |

**최대 대기 시간:** 10분 (초과 시 오류 처리)

---

### 2.4 Report Result — `/report/:id`

**목적:** 생성된 리포트 열람

**표시 내용 (Report JSON 기반):**

1. 적합도 총점 (큰 숫자로 강조)
2. **Primary Profile Selection (v3.1 신규, 최상단)**:
   ```
   "대표 프로필: 인사(HR)"
   "입력된 채용, 온보딩, 급여 운영 근거를 기준으로 HR 프로필을 선택했습니다."
   "보조 신호: Operations" (있는 경우만 표시)
   ```
3. Executive Summary
4. **고유 역량 vs 공통 역량 점수 분리 표시** (직무 정체성 65% / 범용 역량 35% —  
   primary_profile 기준)
5. 강점 Top 3
6. 갭 Top 3
7. 섹션별 상세 내용
8. **신뢰도 안내 (조건부, v3 신규)**: `meta.confidence_level == LOW`인 경우,  
   "입력 내용이 다소 제한적이어서, 더 구체적으로 작성하시면 분석이 더 정교해집니다"  
   안내 배너 표시
9. PDF 다운로드 버튼

**접근 규칙:**
- `report_id` (UUID)를 아는 누구나 접근 가능
- 만료된 리포트 접근 시 → 안내 메시지 표시

---

## 3. Error States

| 상황 | 처리 |
|------|------|
| 폼 유효성 실패 (글자 수 미달) | 인라인 에러 메시지, 스크롤 이동 |
| LOW confidence 안내 | 리포트 내 warning banner, 폼에서는 사전 도움말 |
| API 503/500 | 재시도 버튼 + "잠시 후 다시 시도해주세요" |
| 리포트 만료 | "리포트가 만료되었습니다. 새로 분석하시겠어요?" |
| 리포트 FAILED | "분석 중 문제가 발생했습니다" + 재분석 링크 |
| PDF 생성 실패 | "PDF 생성에 실패했습니다. 잠시 후 다시 시도해주세요" |

---

## 4. 알려진 한계 (UX 관점)

| 한계 | 영향 | 비고 |
|------|------|------|
| `target_priority_text`를 형식적으로("잘 모르겠어요") 작성하는 사용자 | evidence_count 낮음 → LOW 리포트 생성 | warning banner와 추가 입력 권장으로 보완 |
| secondary_profiles 표현이 일부 사용자에게 모호하게 느껴질 수 있음 | 대표 판단 혼란 | primary_profile을 항상 먼저 표시 |
| Landing의 "예시 카드"가 N=10 profile을 완전히 대표하지 못할 수 있음 | 사용자가 "내 경험과 비슷한 예시가 없다"고 느낄 가능성 | LOW/fallback 패턴 데이터 기반으로 예시 갱신 |
