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
점수 계산 로직, requirement matching, gap 분류, **프로필 블렌딩**은 모두  
코드로 구현된 결정론적 알고리즘이다. LLM은 결정론적 결과물을 **윤색**하는  
역할에만 개입한다.

```
input → deterministic_engine (blend + score) → Report JSON → (optional) LLM polish → output
```

**중요:** 이 원칙은 "사용자 요청 시점에 외부 API(채용 공고 검색, 임베딩 모델 호출 등)를  
호출하지 않음"을 포함한다. 프로필 블렌딩은 `{skill_key: confidence_total}` 딕셔너리 간의  
코사인 유사도 — 즉 **순수 산술 연산**이며, 어떤 외부 모델에도 의존하지 않는다.

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

### 5. Profile Blending — 카테고리가 아닌 좌표 (v3 핵심)

CareerFit은 사용자에게 "어떤 직무 카테고리인지 선택"을 요구하지 않는다.  
대신, **사전 정의된 N개의 직무 프로필을 79차원 스킬 공간의 좌표축(기저 벡터)으로  
취급**하고, 사용자의 경험 벡터와 각 좌표축의 코사인 유사도를 계산해  
**그 자리에서 맞춤 프로필을 블렌딩**한다.

```
기존 N개 프로필 = 좌표축 (job_requirements_*.json, 각각 검증된 65/35 구조)
사용자 입력      = 79차원 벡터 (08_EVIDENCE_RULES.md로 추출, {skill_key: confidence_total})

블렌딩 = Σ (cosine_similarity(user, profile_i) × profile_i) → 65/35 재정규화
```

이로써 "10개(또는 N개) 중 하나를 골라야 한다"는 제약이 사라지고,  
사용자는 N개 좌표축이 만드는 **연속적인 스펙트럼 위의 한 점**으로 분석된다.  
`meta.profile_blend`에 그 블렌딩 비율이 기록되며, 이는 점수의 **Explanation Layer**로  
직접 사용된다 (예: "HR 81% + Operations 19% 특성이 혼합된 프로필").

**한계 (의도적으로 명시):** 블렌딩은 "N개 좌표축이 만드는 부분공간(span) 안"에서만  
의미 있는 위치를 찾는다. 79개 스킬 풀 자체에 없는 어휘(예: 매핑되지 않은 신조어,  
산업 특화 용어)는 블렌딩과 무관하게 Evidence가 0으로 남는다. 이는 §6 Structure-Once,  
Scale-Many의 스킬 풀 확장으로 별도 해결되는 문제이며, 블렌딩이 대신할 수 없다.

### 6. Structure-Once, Scale-Many

직무 프로필(좌표축)과 스킬 풀은 **무제한 확장 가능한 데이터**여야 하며,  
코드 변경을 요구해서는 안 된다.

```
공통 Skill Taxonomy (점진적 확장)
    │
    ├─ 프로필 A = 핵심 스킬 4~5개 + weight 자동 배분 규칙
    ├─ 프로필 B = 핵심 스킬 4~5개 + weight 자동 배분 규칙
    └─ 프로필 N = ...  ← 새 좌표축 추가 = JSON 파일 1개

블렌딩 코드는 N에 의존하지 않는다 (for문 1개).
```

`meta.profile_blend`의 누적 분포(예: "특정 프로필에 90%+ 쏠림이 반복됨",  
"전체적으로 모든 유사도가 낮음")는 **새 좌표축이 필요한 영역을 가리키는 진단 신호**로  
활용된다 — 추측이 아닌 데이터 기반 확장.

---

## What CareerFit Is Not

| 아닌 것 | 이유 |
|---------|------|
| AI 자기소개서 생성기 | 텍스트 생성이 목적이 아님 |
| 이력서 교정 서비스 | 원문 수정이 아닌 분석이 목적 |
| 실시간 채용 공고 매칭 서비스 | 사용자 요청 시점에 외부 API를 호출하지 않음 (Deterministic First) |
| 일반 AI 챗봇 | 대화형이 아닌 리포트 생성 파이프라인 |
| 직무 분류기(classifier) | "정답 카테고리 1개를 맞히는" 것이 목적이 아니라, 연속적인 적합도 스펙트럼 위의 위치를 설명하는 것이 목적 |
| 임베딩/LLM 기반 유사도 매칭 서비스 | 코사인 유사도는 `{skill_key: confidence}` 딕셔너리 산술이며, 신경망 임베딩을 사용하지 않음 (결정론 보존) |

---

## Strategic Positioning

```
[낮은 분석 깊이]                              [높은 분석 깊이]
     ↑
잡코리아/사람인    →    LinkedIn Insights    →    CareerFit
 (공고 매칭)              (연결 분석)          (적합도 인텔리전스 + 블렌딩)
```

CareerFit은 시장에서 가장 깊은 수준의 개인 커리어 적합도 분석을 제공하며,  
"카테고리 선택" 없이도 모든 사용자에게 맞춤형 weight 프로필을 즉시 생성한다.

---

## 시장 데이터의 역할 — 두 개의 독립 트랙

```
[트랙 1 — 블렌딩, 사용자 요청 시점, 항상 결정론적]
사용자 입력 → Evidence → user_vector
    → N개 기저 벡터(job_requirements_*.json)와 코사인 유사도
    → 블렌딩 → 65/35 재정규화 → scoring
  데이터 출처: 사용자 본인의 경험 (Evidence First, 항상 충족)

[트랙 2 — 기저 벡터 자체의 weight, 오프라인 배치, V1.1+]
사람인/워크넷 공고 수집 → requirement 빈도/중요도 집계
    → job_requirements_*.json의 weight 갱신
    → meta.weight_source: "MANUAL_V1" → "CRAWLED_2026Q3" 등으로 갱신
  데이터 출처: 시장 공고 데이터
```

**두 트랙은 `job_requirements_*.json`이라는 파일 인터페이스로 분리되어 있다.**  
트랙 2가 완료되면 트랙 1(블렌딩 코드)은 무변경으로 "공고 기반 블렌딩"이 된다.  
트랙 2가 아직 완료되지 않은 상태에서도, 트랙 1만으로 §5의 가치(카테고리 제약 해소,  
Explanation, 결정론)는 전부 유효하다. 단, 이 상태에서는 "이 분석이 시장 데이터에  
기반했다"고 주장할 수 없다 — `meta.weight_source` 필드가 이 한계를 투명하게 표시한다.

---

## 알려진 한계 (§ Limitations)

| 한계 | 영향 범위 | 해소 경로 |
|------|-----------|-----------|
| 79개 스킬 풀 밖의 어휘는 인식 못함 | Evidence 추출 단계 | `07_SKILL_TAXONOMY.md` 점진적 확장 (living document) |
| 블렌딩 결과가 모호(여러 프로필에 고르게 분산)할 수 있음 | 사용자 경험, `summary.one_line` | 임계값 기반 단일/혼합 정체성 표현 분기 (`09_TEXT_TEMPLATE_RULES.md`) |
| 입력이 빈약하면 user_vector가 거의 zero vector | 블렌딩 안정성 | 입력 단계 가드레일 (`04_PAYLOAD_CONTRACT.md` — Evidence 총량 기준 최소 검증) |
| 좌표축(N개) 자체의 weight가 시장 데이터 기반이 아닐 수 있음 (V1) | 분석 정확도의 "신뢰도" | `meta.weight_source` 명시, 트랙 2 완료 시 자동 승격 |
| N개 좌표축이 만드는 부분공간 밖의 직무(예: 79개 스킬로 전혀 설명 안 되는 영역) | 블렌딩 자체의 적용 가능 범위 | `meta.profile_blend`의 최댓값이 임계값 미달일 때 "분석 신뢰도 낮음" 고지 |