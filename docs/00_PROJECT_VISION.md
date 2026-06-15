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

**중요:** 이 원칙은 "사용자 요청 시점에 외부 API(채용 공고 검색 등)를 호출하지 않음"을 포함한다.  
시장 데이터(사람인/워크넷 등)는 오프라인 배치로 수집되어 `job_requirement_stats`에 사전 반영되며,  
사용자 요청 경로는 항상 로컬 데이터만으로 완결된다.

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

### 5. Structure-Once, Scale-Many (신규)

Job Family(직무 카테고리)는 **무제한 확장 가능한 데이터**여야 하며, 코드 변경을 요구해서는 안 된다.

```
공통 Skill Taxonomy (1회 구축)
    │
    ├─ Job Family A = 핵심 스킬 4~5개 + weight 자동 배분 규칙
    ├─ Job Family B = 핵심 스킬 4~5개 + weight 자동 배분 규칙
    ├─ Job Family C = ...
    └─ Job Family N = ...  ← 새 직무 추가 = JSON 파일 1개
```

새로운 직무를 지원해야 할 때, 엔지니어가 할 일은 "핵심 스킬 목록 정의"뿐이며,  
weight 산정·정규화·점수 계산 로직은 모든 Job Family에서 동일하게 동작한다.  
이 원칙이 깨지는 변경(예: Job Family별로 별도 매칭 로직 분기)은 설계 오류로 간주한다.

---

## What CareerFit Is Not

| 아닌 것 | 이유 |
|---------|------|
| AI 자기소개서 생성기 | 텍스트 생성이 목적이 아님 |
| 이력서 교정 서비스 | 원문 수정이 아닌 분석이 목적 |
| 실시간 채용 공고 매칭 서비스 | 사용자 요청 시점에 외부 API를 호출하지 않음 (Deterministic First) |
| 일반 AI 챗봇 | 대화형이 아닌 리포트 생성 파이프라인 |
| 무한 직무 분류 시스템 | Job Family는 "충분히 범용적인 카테고리 + 공통 스킬 풀"의 조합으로 다양성을 흡수한다 |

---

## Strategic Positioning

```
[낮은 분석 깊이]                              [높은 분석 깊이]
     ↑
잡코리아/사람인    →    LinkedIn Insights    →    CareerFit
 (공고 매칭)              (연결 분석)          (적합도 인텔리전스)
```

CareerFit은 시장에서 가장 깊은 수준의 개인 커리어 적합도 분석을 제공하며,  
동시에 직무 카테고리를 8~10개 이상으로 운영해 폭넓은 사용자층을 커버한다.

---

## 시장 데이터의 역할 (사람인/워크넷 연동에 대한 입장)

CareerFit은 채용 공고 검색 서비스가 아니다. 그러나 `job_requirement_stats`의 weight 값이  
"개발자의 직관"이 아니라 **실제 시장의 채용 공고 분석 결과**에 기반하면 리포트의 신뢰도가 크게 높아진다.

```
[오프라인, 배치 — V1.1 이후]
사람인/워크넷에서 Job Family별 공고 N개 수집
    → requirement 키워드 빈도/중요도 집계
    → job_requirement_stats.weight 갱신
    → 이 갱신은 "데이터 동기화"이며 코드 배포가 아님

[온라인, 사용자 요청 시 — V1부터 항상]
사용자 입력 → job_requirement_stats(사전 계산됨) 조회 → 매칭 → 점수 → 리포트
    (외부 API 호출 없음 → Deterministic First 유지)
```