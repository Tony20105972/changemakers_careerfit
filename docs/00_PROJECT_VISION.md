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
점수 계산 로직, requirement matching, gap 분류, **primary_profile 선택**은 모두  
코드로 구현된 결정론적 알고리즘이다. LLM은 결정론적 결과물을 **윤색**하는  
역할에만 개입한다.

```
input → deterministic_engine (profile_select + score) → Report JSON → (optional) LLM polish → output
```

**중요:** 이 원칙은 "사용자 요청 시점에 외부 API(채용 공고 검색, 임베딩 모델 호출 등)를  
호출하지 않음"을 포함한다. primary_profile 선택은 Evidence 기반 규칙과  
프로필별 매칭 신호 계산으로 수행되며, 어떤 외부 모델에도 의존하지 않는다.

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

### 5. Primary Profile Selection — 카테고리 선택 없는 대표 프로필 (v3.1 핵심)

CareerFit은 사용자에게 "어떤 직무 카테고리인지 선택"을 요구하지 않는다.  
대신, **사전 정의된 N개의 직무 프로필을 requirement registry로 취급**하고,  
사용자의 경험 근거와 목표 텍스트를 바탕으로 엔진이 `primary_profile`을 선택한다.

```
기존 N개 프로필 = requirement registry (job_requirements_*.json, 각각 검증된 65/35 구조)
사용자 입력      = 79차원 벡터 (08_EVIDENCE_RULES.md로 추출, {skill_key: confidence_total})

선택 = target_priority_text hint + profile별 evidence signal → primary_profile → 65/35 scoring
```

이로써 사용자가 "10개 중 하나를 직접 골라야 한다"는 제약이 사라진다.  
리포트는 `meta.primary_profile`을 중심으로 점수·갭·추천을 생성하고,  
보조 신호는 `secondary_profiles`로만 표시한다.

**한계 (의도적으로 명시):** 79개 스킬 풀 자체에 없는 어휘(예: 매핑되지 않은 신조어,  
산업 특화 용어)는 Evidence가 0으로 남을 수 있다. 이 경우에도 V1은 차단하지 않고  
fallback profile과 LOW warning으로 report_json을 완성한다.

### 6. Structure-Once, Scale-Many

직무 프로필(좌표축)과 스킬 풀은 **무제한 확장 가능한 데이터**여야 하며,  
코드 변경을 요구해서는 안 된다.

```
공통 Skill Taxonomy (점진적 확장)
    │
    ├─ 프로필 A = 핵심 스킬 4~5개 + weight 자동 배분 규칙
    ├─ 프로필 B = 핵심 스킬 4~5개 + weight 자동 배분 규칙
    └─ 프로필 N = ...  ← 새 좌표축 추가 = JSON 파일 1개

profile selection 코드는 N에 의존하지 않는다.
```

LOW 비율, fallback 빈도, secondary_profiles 패턴은 **새 profile 또는 skill taxonomy 확장이 필요한 영역**을  
가리키는 진단 신호로 활용된다 — 추측이 아닌 데이터 기반 확장.

---

## What CareerFit Is Not

| 아닌 것 | 이유 |
|---------|------|
| AI 자기소개서 생성기 | 텍스트 생성이 목적이 아님 |
| 이력서 교정 서비스 | 원문 수정이 아닌 분석이 목적 |
| 실시간 채용 공고 매칭 서비스 | 사용자 요청 시점에 외부 API를 호출하지 않음 (Deterministic First) |
| 일반 AI 챗봇 | 대화형이 아닌 리포트 생성 파이프라인 |
| 단순 직무 분류기(classifier) | 카테고리 라벨만 맞히는 것이 아니라, Evidence 기반 점수·갭·추천을 완성하는 것이 목적 |
| 임베딩/LLM 기반 유사도 매칭 서비스 | 코사인 유사도는 `{skill_key: confidence}` 딕셔너리 산술이며, 신경망 임베딩을 사용하지 않음 (결정론 보존) |

---

## Strategic Positioning

```
[낮은 분석 깊이]                              [높은 분석 깊이]
     ↑
잡코리아/사람인    →    LinkedIn Insights    →    CareerFit
 (공고 매칭)              (연결 분석)          (적합도 인텔리전스 + 프로필 선택)
```

CareerFit은 시장에서 가장 깊은 수준의 개인 커리어 적합도 분석을 제공하며,  
"카테고리 선택" 없이도 모든 사용자에게 맞춤형 weight 프로필을 즉시 생성한다.

---

## 시장 데이터의 역할 — 두 개의 독립 트랙

```
[트랙 1 — Primary Profile Selection, 사용자 요청 시점, 항상 결정론적]
사용자 입력 → Evidence → user_vector
    → N개 requirement profile(job_requirements_*.json)과 매칭 신호 계산
    → primary_profile 선택 → 65/35 scoring
  데이터 출처: 사용자 본인의 경험 (Evidence First, 항상 충족)

[트랙 2 — 기저 벡터 자체의 weight, 오프라인 배치, V1.1+]
사람인/워크넷 공고 수집 → requirement 빈도/중요도 집계
    → job_requirements_*.json의 weight 갱신
    → meta.weight_source: "MANUAL_V1" → "CRAWLED_2026Q3" 등으로 갱신
  데이터 출처: 시장 공고 데이터
```

**두 트랙은 `job_requirements_*.json`이라는 파일 인터페이스로 분리되어 있다.**  
트랙 2가 완료되면 트랙 1(profile selection)은 무변경으로 "공고 기반 weight"를 사용한다.  
트랙 2가 아직 완료되지 않은 상태에서도, 트랙 1만으로 §5의 가치(카테고리 제약 해소,  
대표 프로필 설명, 결정론)는 전부 유효하다. 단, 이 상태에서는 "이 분석이 시장 데이터에  
기반했다"고 주장할 수 없다 — `meta.weight_source` 필드가 이 한계를 투명하게 표시한다.

---

## 알려진 한계 (§ Limitations)

| 한계 | 영향 범위 | 해소 경로 |
|------|-----------|-----------|
| 79개 스킬 풀 밖의 어휘는 인식 못함 | Evidence 추출 단계 | `07_SKILL_TAXONOMY.md` 점진적 확장 (living document) |
| primary_profile 선택 근거가 부족할 수 있음 | 사용자 경험, `summary.one_line` | `confidence_level=LOW`, `warning_message`, `evidence_count` 표시 |
| 입력이 빈약하면 user_vector가 거의 zero vector | 선택 정확도 | fallback profile로 생성하되 LOW warning 필수 |
| 좌표축(N개) 자체의 weight가 시장 데이터 기반이 아닐 수 있음 (V1) | 분석 정확도의 "신뢰도" | `meta.weight_source` 명시, 트랙 2 완료 시 자동 승격 |
| N개 profile로 설명하기 어려운 직무 | fallback 가능성 증가 | LOW/fallback 패턴을 profile 확장 신호로 사용 |
