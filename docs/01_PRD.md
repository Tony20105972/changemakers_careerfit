# 01 — Product Requirements Document (PRD)

**Version:** 3.0  
**Status:** Confirmed  
**Last Updated:** 2026-06 (v3.1: 직무 선택 제거, primary_profile 도입)

---

## 1. Product Overview

### 1.1 Product Name
CareerFit

### 1.2 One-line Description
커리어 경험과 목표를 입력하면, 직무 카테고리 선택 없이 대표 직무 프로필을  
즉시 생성하고 전략 리포트를 제공하는 Career Intelligence Platform.

### 1.3 Product Goal
사용자가 자신의 커리어 경험과 목표(자유 텍스트)를 입력하면,  
시스템이 사전 정의된 N개 직무 프로필 중 `primary_profile`을 선택하고, 강점·갭·전략적 추천이 포함된  
PDF 리포트를 5분 이내에 생성한다.

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
| 니즈 | "내 경험이 어떤 방향에 가까운지 가이드받고 싶다" |

### 2.3 v3에서 새롭게 포괄되는 사용자

| 상황 | v2(10개 select)에서의 문제 | v3.1(primary_profile)에서의 처리 |
|------|---------------------------|----------------------|
| "그로스해커", "HRBP" 같은 인접/혼합 직무 | 10개 중 억지로 1개 선택 | 대표 프로필 1개와 보조 프로필 신호로 설명 |
| 1순위/2순위 목표가 다른 사용자 | 1개만 표현 가능 | `target_priority_text`로 우선순위/이유까지 입력 → profile 선택에 반영 |
| "10개에 내 직무가 없음" | 부정확한 카테고리로 강제 매칭 | 입력 근거가 부족하면 LOW warning과 fallback profile로 리포트 생성 |

---

## 3. Problem Statement

### 3.1 해결하는 문제
1. **적합도 불명확성**: "내가 이 직무에 맞는가?"에 대한 객관적 기준이 없다.
2. **경험 번역 불가**: 자신의 경험이 직무 언어로 어떻게 매핑되는지 모른다.
3. **갭 인식 부재**: 어떤 역량이 부족한지, 어떻게 채워야 하는지 모른다.
4. **고비용 대안**: 전문 커리어 컨설팅은 1회 10–30만원 이상.
5. **카테고리 강제의 부정확성** (v3 신규): 기존 자가진단 도구는 사용자를 고정된  
   카테고리 중 하나로 강제 분류하여, 혼합/경계 직무 사용자에게 부정확한 결과를 준다.

### 3.2 해결하지 않는 문제 (V1 범위 외)
- 특정 채용 공고에 대한 맞춤 분석
- 이력서/자기소개서 직접 작성
- 사용자 요청 시점의 실시간 외부 API 연동
- 79개 스킬 풀에 전혀 없는 영역의 직무 분석 (§10 한계)

---

## 4. Primary Profile Selection — 핵심 메커니즘

### 4.1 설계 원칙

```
기존 N개 프로필 (job_requirements_*.json) = requirement registry
    │
    ├─ 각 프로필은 06_SCORING_RULES.md §2의 allocate_weights()로 생성됨
    │  (core_skill_keys 65% / common_skill_keys 35%, 검증됨)
    │
    ▼
사용자 입력 (career_histories + target_priority_text)
    → Evidence 추출 (08_EVIDENCE_RULES.md)
    → user_vector = {skill_key: confidence_total}
    │
    ▼
profile별 evidence signal 계산 + target_priority_text hint 반영
    │
    ▼
primary_profile 선택 → 해당 profile의 65/35 requirements로 scoring
```

### 4.2 N개 프로필의 역할 변화

| v2 (10개 ENUM select) | v3.1 (primary_profile registry) |
|------------------------|---------------------|
| 사용자가 직접 선택하는 "카테고리" | 엔진이 선택하는 대표 profile |
| 선택된 1개의 weight를 그대로 사용 | 엔진이 선택한 primary_profile weight 사용 |
| `target_job_family` (입력값) | 내부 식별자로만 존재 (`data/job_requirements_*.json`의 파일명) |
| N=10 고정 | N≥10, 점진적 확장 가능 (코드 변경 없음) |

### 4.3 N (좌표축 개수)

V1은 **N=10**으로 시작한다 (기존 HR/Marketing/Data/Product/Operations/Sales/Design/  
Finance/Engineering/Customer Success — `13_Development_Roadmap.md` Day 6 산출물 재사용).

N을 늘리는 기준은 추측이 아니라 **운영 리포트의 LOW 비율, fallback 빈도, secondary_profiles 패턴**이다:
- 특정 primary_profile으로 과도하게 fallback 반복 → 프로필 세분화 검토
- LOW가 반복되는 입력군 → 스킬 taxonomy 또는 profile 추가 검토

---

## 5. V1 Scope

### 5.1 포함 기능 (In Scope)

| 기능 | 설명 |
|------|------|
| 커리어 경험 입력 | 회사명, 직책, 기간, 담당업무 자유 텍스트 입력 |
| **목표/우선순위 입력 (v3 신규)** | `target_priority_text` — 목표 직무와 그 이유를 자유 텍스트로 입력 |
| **Primary Profile Selection (v3.1 신규)** | N=10 registry 중 대표 profile 선택 |
| **Secondary Profiles (v3.1 신규)** | 보조 신호가 있는 프로필을 선택적으로 표시 |
| **LOW warning (v3.1 신규)** | Evidence 부족 시 차단하지 않고 신뢰도 안내 |
| 적합도 점수 계산 | 100점 만점, primary_profile weight 기반 결정론적 계산 |
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
| **직무 카테고리 select (v3에서 제거)** | primary_profile 선택으로 대체. ENUM, INVALID_JOB_FAMILY 에러 제거 |
| 특정 채용 공고 분석 | profile registry 기반 분석으로 대체 |
| 사용자 요청 시 실시간 외부 API 호출 | Deterministic First 원칙과 충돌 |
| 임베딩/LLM 기반 유사도 계산 | 코사인 유사도(키워드 벡터)로 충분, 결정론 보존 우선 |
| 멀티 직무 비교 | V2 기능 |
| 공유 기능 | V2 기능 |
| 모바일 앱 | 웹 우선 |
| N>10 좌표축 사전 추가 | V1은 N=10으로 검증. 확장은 §4.3 기준 데이터 확보 후 |

---

## 6. User Stories

### 핵심 User Story
```
As a 이직 준비 중인 직장인,
I want to 내 커리어 경험과 목표를 자유롭게 입력하고 맞춤형 적합도 리포트를 받고 싶다,
So that 정해진 카테고리에 억지로 맞추지 않고도 내가 어떤 방향에 가까운지 알 수 있다.
```

### 세부 User Stories

| ID | Story |
|----|-------|
| US-01 | 나는 과거 직장 경험을 자유 텍스트로 입력할 수 있다 |
| US-02 (v3 변경) | ~~나는 10개 Job Family 중 목표 직무를 선택할 수 있다~~ → 나는 목표 직무와 그 이유를 자유 텍스트로 입력할 수 있다 |
| US-03 | 나는 리포트 생성 중 진행 상태를 확인할 수 있다 |
| US-04 | 나는 완성된 리포트를 웹에서 열람할 수 있다 |
| US-05 | 나는 리포트를 PDF로 다운로드할 수 있다 |
| US-06 | 나는 report_id를 통해 이전 리포트를 재열람할 수 있다 |
| US-07 (v3 변경) | 나는 리포트에서 "내 경험이 어떤 직무 특성들의 조합으로 분석되었는지" 확인할 수 있다 |
| US-08 (v3 신규) | 나는 입력이 너무 짧거나 모호하면, 분석 전에 보완 안내를 받는다 |

---

## 7. Success Criteria (V1)

| 지표 | 목표값 |
|------|--------|
| 리포트 생성 성공률 | ≥ 95% |
| 리포트 생성 소요 시간 | ≤ 5분 |
| PDF 생성 성공률 | ≥ 98% |
| 적합도 점수 일관성 | 동일 입력 → 동일 점수 (100%, profile selection 포함) |
| LLM 실패 시 폴백 성공률 | 100% (템플릿 기반 폴백) |
| 좌표축(N=10)별 weight 합계 검증 | 10개 전부 1.0 ± 0.001, UNIQUE 0.65 / COMMON 0.35 |
| **Primary profile weight 합계 검증 (v3.1 신규)** | 모든 selected_requirements UNIQUE 0.65 / COMMON 0.35 |
| **LOW confidence 비율 (v3.1 신규)** | 추적 지표로 수집 (목표값 없음 — §4.3 확장 판단용) |

---

## 8. Non-Functional Requirements

| 항목 | 요구사항 |
|------|---------|
| 언어 | 한국어 우선 (UI, 리포트 모두) |
| 접근성 | report_id URL로 비로그인 접근 가능 |
| 데이터 보존 | 생성된 리포트 30일 보존 |
| 보안 | report_id는 UUID v4 (추측 불가) |
| 확장성 | 좌표축(N) 추가 시 코드 변경 없이 데이터(JSON)만 추가 |
| 결정론 | 사용자 요청 경로에서 외부 API/임베딩 모델 호출 없음 |
| 투명성 (v3.1 신규) | `meta.primary_profile`, `meta.confidence_level`, `meta.warning_message`, `meta.weight_source`로 분석 근거 노출 |

---

## 9. Engineering Priorities (Schema-First, v3 갱신)

```
1. 04_PAYLOAD_CONTRACT.md  — target_job_family 제거, target_priority_text 추가,
                              Algorithm Response에 primary_profile 추가
2. 05_REPORT_SCHEMA.md     — meta.primary_profile, meta.warning_message, meta.weight_source 추가,
                              targetJobAnalysis를 primary_profile 기반으로 재정의
3. 03_ERD.md               — reports.target_job_family(ENUM) → reports.primary_profile(TEXT)
4. Migration               — ERD 확정 후 실행
5. 06_SCORING_RULES.md     — select_primary_profile(), fallback_profile 추가
                              (allocate_weights()는 그대로, 좌표축 생성용으로 유지)
6. 07_SKILL_TAXONOMY.md    — 변경 없음 (79개 풀, living document 원칙 유지)
7. 08_EVIDENCE_RULES.md    — 변경 없음 (career_histories + target_priority_text 모두 입력)
8. sample_input/report.json — target_priority_text 필드 추가, primary_profile 결과 포함
```

---

## 10. 알려진 한계 (V1 출시 시 명시)

| 한계 | 사용자 영향 | 완화 방법 |
|------|------------|-----------|
| N=10 좌표축의 weight가 시장 데이터 기반이 아님 (`weight_source: MANUAL_V1`) | 분석의 "정밀도"는 신뢰할 수 있으나 "시장 대표성"은 검증 전 | 리포트 내 `weight_source` 고지, 트랙 2(공고 기반) 완료 시 자동 승격 |
| 79개 스킬 풀 밖의 표현은 인식 안 됨 | 산업 특화 용어가 많은 직무는 user_vector가 sparse해질 수 있음 | `07_SKILL_TAXONOMY.md` 점진적 확장 |
| primary_profile 선택 근거가 부족할 수 있음 | "왜 이 프로필인가?" 의문 | `primary_profile_summary`와 `evidence_count` 표시 |
| 입력이 빈약하면 정확도 급락 | 부정확한 리포트 수령 위험 | LOW warning + 추가 입력 권장, 차단 없음 |
