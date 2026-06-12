# 00 — Project Vision

> CareerFit is not an AI PDF generator.  
> CareerFit is a **Career Intelligence Platform**.

---

## Mission

**사람의 경험을 직무의 언어로 번역한다.**

사용자가 입력한 날것의 커리어 경험을 구조화된 직무 적합도 인텔리전스로 변환하고,  
그 결과를 실행 가능한 전략 리포트로 전달한다.

---

## Core Principles

### 1. Evidence First

모든 분석 결과는 사용자가 직접 입력한 경험 원문에 근거한다.  
근거 없는 점수, 근거 없는 강점 서술은 존재하지 않는다.  
LLM이 생성한 문장도 반드시 Evidence에 anchoring되어야 한다.

```
user_input → evidence_extraction → scoring → text_generation
                    ↑
             원문 보존 필수
```

### 2. Deterministic First

동일한 입력은 동일한 점수를 생성해야 한다.  
점수 계산 로직, requirement matching, gap 분류는 모두 코드로 구현된 결정론적 알고리즘이다.  
LLM은 결정론적 결과물을 **윤색**하는 역할에만 개입한다.

```
input → deterministic_engine → Report JSON → (optional) LLM polish → output
```

### 3. Report JSON First

Report JSON은 시스템의 **단일 진실 공급원(Single Source of Truth)**이다.  
PDF, 화면 렌더링, API 응답은 모두 Report JSON에서 파생된다.  
Report JSON 없이는 어떤 출력물도 생성되지 않는다.

```
Report JSON
    ├── → PDF 생성
    ├── → 결과 페이지 렌더링
    └── → API 응답 payload
```

### 4. LLM Optional

LLM 호출이 실패해도 리포트는 생성되어야 한다.  
LLM 없이 생성된 리포트는 템플릿 기반 텍스트로 구성되며, 이것도 유효한 완성 리포트다.

```
LLM available   → deterministic_result + LLM_polish → full report
LLM unavailable → deterministic_result + template_text → valid report
```

---

## What CareerFit Is Not

| 아닌 것 | 이유 |
|---------|------|
| AI 자기소개서 생성기 | 텍스트 생성이 목적이 아님 |
| 이력서 교정 서비스 | 원문 수정이 아닌 분석이 목적 |
| 채용 공고 매칭 서비스 | 특정 공고가 아닌 Job Family 기준 분석 |
| 일반 AI 챗봇 | 대화형이 아닌 리포트 생성 파이프라인 |

---

## Strategic Positioning

```
[낮은 분석 깊이]                              [높은 분석 깊이]
     ↑
잡코리아/사람인    →    LinkedIn Insights    →    CareerFit
 (공고 매칭)              (연결 분석)          (적합도 인텔리전스)
```

CareerFit은 시장에서 가장 깊은 수준의 개인 커리어 적합도 분석을 제공한다.
# 01 — Product Requirements Document (PRD)

**Version:** 1.0  
**Status:** Confirmed  
**Last Updated:** 2025-06

---

## 1. Product Overview

### 1.1 Product Name
CareerFit

### 1.2 One-line Description
커리어 경험을 입력하면 목표 직무 적합도를 분석하고 전략 리포트를 생성하는 Career Intelligence Platform.

### 1.3 Product Goal
사용자가 자신의 커리어 경험과 목표 직무를 입력하면,  
시스템이 직무 요구사항 기준으로 적합도를 정량화하고,  
강점·갭·전략적 추천이 포함된 PDF 리포트를 5분 이내에 생성한다.

---

## 2. Target Users

### 2.1 Primary User
| 구분 | 내용 |
|------|------|
| 연령대 | 25–38세 |
| 상황 | 이직 준비 중이거나 직무 전환을 고려 중인 직장인 |
| 니즈 | "내가 이 직무에 얼마나 맞는지 객관적으로 알고 싶다" |
| 현재 대안 | 지인 조언, 채용 공고 자가 비교, 커리어 컨설팅 (비용 높음) |

### 2.2 Secondary User
| 구분 | 내용 |
|------|------|
| 상황 | 신입 또는 경력 1-2년차, 커리어 방향성 탐색 중 |
| 니즈 | "어떤 직무가 내 경험과 맞는지 가이드받고 싶다" |

---

## 3. Problem Statement

### 3.1 해결하는 문제
1. **적합도 불명확성**: "내가 이 직무에 맞는가?"에 대한 객관적 기준이 없다.
2. **경험 번역 불가**: 자신의 경험이 직무 언어로 어떻게 매핑되는지 모른다.
3. **갭 인식 부재**: 어떤 역량이 부족한지, 어떻게 채워야 하는지 모른다.
4. **고비용 대안**: 전문 커리어 컨설팅은 1회 10–30만원 이상.

### 3.2 해결하지 않는 문제 (V1 범위 외)
- 특정 채용 공고에 대한 맞춤 분석
- 이력서/자기소개서 직접 작성
- 실시간 취업 시장 데이터 연동

---

## 4. V1 Scope

### 4.1 포함 기능 (In Scope)

| 기능 | 설명 |
|------|------|
| 커리어 경험 입력 | 회사명, 직책, 기간, 담당업무 자유 텍스트 입력 |
| 목표 직무 선택 | V1 지원 Job Family 5개 중 선택 |
| 적합도 점수 계산 | 100점 만점, requirement weight 기반 결정론적 계산 |
| 강점 분석 | Evidence 기반 매핑된 역량 항목 |
| 갭 분석 | 미충족 requirement + 우선순위 |
| 추천 전략 | 단기/중기 행동 계획 |
| 90-Day Roadmap | 구체적 실행 계획 |
| PDF 리포트 생성 | 13개 섹션 구성된 전략 리포트 |
| 리포트 조회 | 생성된 리포트 재열람 |

### 4.2 제외 기능 (Out of Scope — V1)

| 기능 | 제외 사유 |
|------|----------|
| 회원 가입 / 로그인 | V1은 비로그인 기반 (report_id로 접근) |
| 리포트 히스토리 | Auth 없이 구현 불가 |
| 특정 채용 공고 분석 | Job Family 기준 분석으로 충분 |
| 실시간 시장 데이터 | 외부 API 연동 복잡도 |
| 멀티 직무 비교 | V2 기능 |
| 공유 기능 | V2 기능 |
| 모바일 앱 | 웹 우선 |

---

## 5. Supported Job Families (V1)

| Job Family | 분석 대상 역량 예시 |
|------------|-------------------|
| **HR** | recruiting, training_and_onboarding, payroll, performance_management, hr_policy, labor_law |
| **Marketing** | marketing_content, campaign_management, seo_sem, brand_management, data_analysis, copywriting |
| **Data** | sql, python, data_analysis, data_visualization, statistics, ml_fundamentals, data_pipeline |
| **Product** | product_planning, user_research, roadmap_management, stakeholder_management, data_analysis, ux_sense |
| **Operations** | process_improvement, project_management, vendor_management, operations_management, coordination, documentation |

각 Job Family는 `job_requirement_stats` 테이블에 요구사항 목록과 weight로 사전 정의된다.

---

## 6. User Stories

### 핵심 User Story
```
As a 이직 준비 중인 직장인,
I want to 내 커리어 경험을 입력하고 목표 직무 적합도 리포트를 받고 싶다,
So that 내가 이 직무에 얼마나 준비되었는지 객관적으로 파악할 수 있다.
```

### 세부 User Stories

| ID | Story |
|----|-------|
| US-01 | 나는 과거 직장 경험을 자유 텍스트로 입력할 수 있다 |
| US-02 | 나는 목표 Job Family를 선택할 수 있다 |
| US-03 | 나는 리포트 생성 중 진행 상태를 확인할 수 있다 |
| US-04 | 나는 완성된 리포트를 웹에서 열람할 수 있다 |
| US-05 | 나는 리포트를 PDF로 다운로드할 수 있다 |
| US-06 | 나는 report_id를 통해 이전 리포트를 재열람할 수 있다 |

---

## 7. Success Criteria (V1)

| 지표 | 목표값 |
|------|--------|
| 리포트 생성 성공률 | ≥ 95% |
| 리포트 생성 소요 시간 | ≤ 5분 |
| PDF 생성 성공률 | ≥ 98% |
| 적합도 점수 일관성 | 동일 입력 → 동일 점수 (100%) |
| LLM 실패 시 폴백 성공률 | 100% (템플릿 기반 폴백) |

---

## 8. Non-Functional Requirements

| 항목 | 요구사항 |
|------|---------|
| 언어 | 한국어 우선 (UI, 리포트 모두) |
| 접근성 | report_id URL로 비로그인 접근 가능 |
| 데이터 보존 | 생성된 리포트 30일 보존 |
| 보안 | report_id는 UUID v4 (추측 불가) |
| 확장성 | Job Family 추가 시 코드 변경 없이 DB만 수정으로 가능 |
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
    ▼
Generating (/report/:id?status=generating)
    │
    │  polling → status: READY
    ▼
Report Result (/report/:id)
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
- 서비스 한 줄 설명: "내 경험이 이 직무에 얼마나 맞는지 분석해드립니다"
- 지원 Job Family 5개 표시
- 예시 리포트 썸네일 또는 스코어 미리보기
- CTA 버튼: "지금 무료로 분석하기"

**상태:** 정적 페이지, 인증 불필요

---

### 2.2 Report Form — `/report/new`

**목적:** 분석에 필요한 커리어 정보 수집

**입력 필드:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| target_job_family | select | ✅ | HR / Marketing / Data / Product / Operations |
| career_histories | array | ✅ | 1개 이상 |
| └ company_name | text | ✅ | 회사명 |
| └ title | text | ✅ | 직책/직함 |
| └ start_date | month picker | ✅ | 입사 연월 |
| └ end_date | month picker | ✅ | 퇴사 연월 (재직 중이면 "현재" 선택) |
| └ is_current | checkbox | - | 현재 재직 중 여부 |
| └ responsibilities | textarea | ✅ | 담당 업무 자유 텍스트 (최소 50자) |
| └ achievements | textarea | - | 주요 성과 자유 텍스트 |

**UX 규칙:**
- 경력 추가는 "+ 경력 추가" 버튼으로 동적 추가
- 경력은 최소 1개, 최대 10개
- 각 경력의 responsibilities는 최소 50자 (가이드 문구 표시)
- 제출 전 클라이언트 사이드 유효성 검사

**제출 시 동작:**
1. `POST /reports` API 호출
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
| ANALYZING | "경험을 분석 중입니다..." |
| PDF_GENERATING | "리포트를 생성 중입니다..." |
| READY | 자동으로 `/report/:id` 로 이동 |
| FAILED | 오류 메시지 표시 + 재시도 버튼 |

**최대 대기 시간:** 10분 (초과 시 오류 처리)

---

### 2.4 Report Result — `/report/:id`

**목적:** 생성된 리포트 열람

**표시 내용 (Report JSON 기반):**
1. 적합도 총점 (큰 숫자로 강조)
2. Executive Summary
3. 강점 Top 3
4. 갭 Top 3
5. 섹션별 상세 내용
6. PDF 다운로드 버튼

**접근 규칙:**
- `report_id` (UUID)를 아는 누구나 접근 가능
- 만료된 리포트 접근 시 → 안내 메시지 표시

---

## 3. Error States

| 상황 | 처리 |
|------|------|
| 폼 유효성 실패 | 인라인 에러 메시지, 스크롤 이동 |
| API 503/500 | 재시도 버튼 + "잠시 후 다시 시도해주세요" |
| 리포트 만료 | "리포트가 만료되었습니다. 새로 분석하시겠어요?" |
| 리포트 FAILED | "분석 중 문제가 발생했습니다" + 재분석 링크 |
| PDF 생성 실패 | "PDF 생성에 실패했습니다. 잠시 후 다시 시도해주세요" |