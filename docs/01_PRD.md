# 01 — Product Requirements Document (PRD)

**Version:** 2.0  
**Status:** Confirmed  
**Last Updated:** 2025-06 (v2: Job Family 10개 확장, Schema-First 순서 반영)

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
5. **직무 카테고리의 협소함**: 기존 자가진단 도구는 IT/사무직 등 일부 직군에 편중되어 있다.

### 3.2 해결하지 않는 문제 (V1 범위 외)
- 특정 채용 공고에 대한 맞춤 분석 (대신 Job Family 단위 분석)
- 이력서/자기소개서 직접 작성
- 사용자 요청 시점의 실시간 외부 API 연동

---

## 4. Why 10 Job Families (V1)

### 4.1 설계 원칙

V1은 단순히 "5개에서 10개로 늘린 것"이 아니라, **구조적으로 확장 가능한 아키텍처**를 V1부터 적용한다.

```
공통 Skill Taxonomy (~65개)
    │
    ├─ 각 Job Family는 "고유 핵심 스킬 4~5개"만 정의
    └─ weight 배분 규칙(06_SCORING_RULES.md)이 나머지를 자동 계산
        - 고유 스킬군: weight 합계 65%  (직무 정체성 보장)
        - 공통 스킬군: weight 합계 35%  (범용 역량 평가)
```

이 구조 덕분에 Job Family를 5개에서 10개로 늘리는 것이 Skill Taxonomy나 Evidence Rules의  
작업량을 5배로 증가시키지 않는다. 각 Job Family 추가 비용은 "핵심 스킬 4~5개 선정" 수준이다.

### 4.2 V1 종료 후에도 Job Family는 계속 늘어날 수 있는가?

가능하다. 새 Job Family 추가 절차는 다음과 같으며 코드 배포가 필요 없다:

```
1. 해당 직무의 고유 핵심 스킬 4~5개를 Skill Taxonomy에서 선택 (없으면 신규 추가)
2. data/job_requirements_<family>.json 생성 (06_SCORING_RULES.md 규칙대로 weight 자동 생성)
3. job_requirement_stats 테이블에 INSERT
```

---

## 5. V1 Scope

### 5.1 포함 기능 (In Scope)

| 기능 | 설명 |
|------|------|
| 커리어 경험 입력 | 회사명, 직책, 기간, 담당업무 자유 텍스트 입력 |
| 목표 직무 선택 | V1 지원 Job Family 10개 중 선택 |
| 적합도 점수 계산 | 100점 만점, requirement weight 기반 결정론적 계산 |
| 강점 분석 | Evidence 기반 매핑된 역량 항목 |
| 갭 분석 | 미충족 requirement + 우선순위 |
| 추천 전략 | 단기/중기 행동 계획 |
| 90-Day Roadmap | 구체적 실행 계획 |
| PDF 리포트 생성 | 12개 섹션 구성된 전략 리포트 |
| 리포트 조회 | 생성된 리포트 재열람 (report_id 기반) |

### 5.2 제외 기능 (Out of Scope — V1)

| 기능 | 제외 사유 |
|------|----------|
| 회원 가입 / 로그인 | V1은 비로그인 기반 (report_id로 접근) |
| 리포트 히스토리 | Auth 없이 구현 불가 |
| 특정 채용 공고 분석 | Job Family 기준 분석으로 대체 |
| 사용자 요청 시 실시간 외부 API 호출 | Deterministic First 원칙과 충돌 (00_PROJECT_VISION.md 참조) |
| 멀티 직무 비교 | V2 기능 |
| 공유 기능 | V2 기능 |
| 모바일 앱 | 웹 우선 |
| 11개 이상 Job Family | 구조상 가능하나 V1 검증 범위는 10개로 한정 |

---

## 6. Supported Job Families (V1) — 10개

각 Job Family는 "고유 핵심 스킬(core skills)"과 "선택적 보조 스킬(secondary skills)"로 정의되며,  
나머지는 공통 스킬 풀에서 weight 배분 규칙에 따라 자동 채워진다. (07_SKILL_TAXONOMY.md 참조)

| # | Job Family | 고유 핵심 스킬 (4~5개) |
|---|------------|------------------------|
| 1 | **HR** | recruiting, training_and_onboarding, payroll, labor_law |
| 2 | **Marketing** | campaign_management, seo_sem, content_marketing, brand_management |
| 3 | **Data** | sql, python, data_analysis, data_visualization, statistics |
| 4 | **Product** | product_planning, roadmap_management, user_research, ux_sense |
| 5 | **Operations** | process_improvement, vendor_management, operations_management |
| 6 | **Sales** | lead_generation, account_management, negotiation, crm_management |
| 7 | **Design** | ui_design, prototyping, design_systems, user_research |
| 8 | **Finance** | financial_modeling, budgeting, accounting, financial_reporting |
| 9 | **Engineering** | software_development, code_review, system_design, debugging |
| 10 | **Customer Success** | customer_onboarding, churn_management, support_ticketing, account_health |

> 일부 스킬(`user_research` 등)은 2개 이상의 Job Family에서 고유 핵심 스킬로 중복 지정될 수 있다.  
> 이는 의도된 설계이며, 인접 직무 간 점수 비교 시 의미 있는 신호가 된다.

---

## 7. User Stories

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
| US-02 | 나는 10개 Job Family 중 목표 직무를 선택할 수 있다 |
| US-03 | 나는 리포트 생성 중 진행 상태를 확인할 수 있다 |
| US-04 | 나는 완성된 리포트를 웹에서 열람할 수 있다 |
| US-05 | 나는 리포트를 PDF로 다운로드할 수 있다 |
| US-06 | 나는 report_id를 통해 이전 리포트를 재열람할 수 있다 |
| US-07 | 나는 리포트에서 "직무 고유 역량"과 "범용 역량"을 구분해서 볼 수 있다 |

---

## 8. Success Criteria (V1)

| 지표 | 목표값 |
|------|--------|
| 리포트 생성 성공률 | ≥ 95% |
| 리포트 생성 소요 시간 | ≤ 5분 |
| PDF 생성 성공률 | ≥ 98% |
| 적합도 점수 일관성 | 동일 입력 → 동일 점수 (100%) |
| LLM 실패 시 폴백 성공률 | 100% (템플릿 기반 폴백) |
| Job Family별 weight 합계 검증 | 10개 전부 1.0 ± 0.001 |
| 고유/공통 스킬 weight 비율 | 10개 전부 65% / 35% ± 2%p |

---

## 9. Non-Functional Requirements

| 항목 | 요구사항 |
|------|---------|
| 언어 | 한국어 우선 (UI, 리포트 모두) |
| 접근성 | report_id URL로 비로그인 접근 가능 |
| 데이터 보존 | 생성된 리포트 30일 보존 |
| 보안 | report_id는 UUID v4 (추측 불가) |
| 확장성 | Job Family 추가 시 코드 변경 없이 데이터(JSON)만 추가 |
| 결정론 | 사용자 요청 경로에서 외부 API 호출 없음 |

---

## 10. Engineering Priorities (Schema-First)

V1 개발은 다음 순서를 따른다 (코드보다 계약을 먼저 고정한다):

```
1. 04_PAYLOAD_CONTRACT.md  — 입출력 계약 확정
2. 05_REPORT_SCHEMA.md     — Report JSON 구조 확정 (최우선 품질 투자 대상)
3. 03_ERD.md               — Report JSON을 저장하기 위한 DB 구조 도출
4. Migration               — ERD 확정 후 실행
5. 06_SCORING_RULES.md     — weight 배분 규칙 + matchLevel 알고리즘
6. 07_SKILL_TAXONOMY.md    — 공통 스킬 풀 + Job Family별 고유 스킬
7. 08_EVIDENCE_RULES.md    — 키워드 매핑 규칙
8. sample_input/report.json (HR, Data) — 손으로 작성한 정답 fixture
```

이 순서는 `.cursorrules`의 **Rule 10 (Documentation First)**과 직접 연결된다:  
구현 중 Payload Contract 또는 Report Schema 변경이 필요하다고 판단되면,  
코드 작업을 멈추고 문서를 먼저 수정한다.