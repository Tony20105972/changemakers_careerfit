# 14 — Narrative Composer Architecture

CareerFit의 Narrative Composer는 `skill_descriptions.json`을 단순 설명 사전이 아니라
Report JSON 전체에 영향을 주는 **Skill Intelligence Registry**로 확장하기 위한 설계다.

이 문서는 구현 코드가 아니라 문서 계약이다. 현재 V1의 `text_template.py`와 `report_builder.py`를
대체하지 않고, 다음 단계에서 어떤 책임을 분리해야 하는지 정의한다.

> **V1 기준:** Composer는 현재 `data/skill_descriptions.json`에 존재하는 필드만 사용한다.  
> `frames`, `narrative_blocks`, `report_hooks`, `market_signals`, `evidence_patterns`,
> `quality_rules`는 V2 확장안이며 V1 구현 필드가 아니다.

---

## 1. 목적

현재 `text_template.py`는 `strengths`, `gaps`, `scores`, `evidenceMapping`을 읽어
`executive_summary`, `skill_explanations`, `skill_narratives`를 결정론적으로 생성한다.
이 구조는 V1에는 충분하지만, Skill 하나가 리포트 전체의 해석 품질을 끌어올리는 구조로는 부족하다.

Narrative Composer의 목적은 다음과 같다.

| 목표 | 설명 |
|------|------|
| Skill 중심 해석 | `skill_key`별 의미가 Executive Summary, Strength, Gap, Job Outlook, Final Assessment에 일관되게 반영된다. |
| Evidence 연결 | 모든 문장은 실제 Evidence, match level, score, primary_profile을 재료로만 생성된다. |
| 결정론 유지 | 동일 Report JSON 입력은 동일 Registry 필드 선택과 동일 출력으로 이어진다. |
| Registry 확장성 | 새 Skill을 추가하면 해당 Skill의 설명 필드가 전체 리포트 품질을 함께 개선한다. |

---

## 2. 왜 `text_template.py`만으로 부족한가

`text_template.py`는 현재 “문장 생성 함수”에 가깝다. Registry의 필드를 읽고 문단을 만들지만,
Skill이 리포트의 어느 위치에서 어떤 관점으로 쓰여야 하는지까지 충분히 표현하지 않는다.

한계는 다음과 같다.

| 한계 | 영향 |
|------|------|
| 단일 설명 필드 중심 | `definition`, `market_context`가 여러 리포트 섹션에서 같은 방식으로 재사용될 수 있다. |
| report hook 부재 | 어떤 Skill이 `summary`, `skill_explanations`, `skill_narratives` 중 어디에 강하게 반영될지 명시하기 어렵다. |
| block 선택 기준 부족 | V1은 현재 Registry 필드 조합으로 선택하며, 별도 block 후보 구조는 V2에서 다룬다. |
| 품질 감사 분리 부족 | 반복 문장, 행동 지시, Evidence 없는 주장 여부를 Composer 입력 단계에서 통제하기 어렵다. |

따라서 다음 단계의 `text_template.py`는 최종 렌더러에 가까워지고,
Skill별 의미 선택과 조합은 Composer가 담당해야 한다.

---

## 3. 왜 외부 LLM 프레임워크보다 자체 Composer인가

CareerFit은 RAG, 에이전트 프레임워크, 외부 채용 공고 API에 의존하지 않는
Deterministic First 제품이다. LangChain, CrewAI 같은 외부 프레임워크는 narrative 조합을 유연하게 만들 수는 있지만,
다음 리스크를 만든다.

| 외부 프레임워크 리스크 | CareerFit 기준 |
|------------------------|----------------|
| 실행 경로가 복잡해짐 | 동일 입력 → 동일 출력 검증이 어려워진다. |
| Evidence 외 정보 혼입 가능성 | Evidence First 원칙과 충돌한다. |
| Report JSON 외부 상태 의존 | Report JSON First 원칙이 약해진다. |
| 디버깅 단위가 커짐 | 어떤 Skill이 어떤 문장에 영향을 줬는지 추적하기 어렵다. |

자체 Composer는 JSON Registry, Engine Output, Report JSON만 사용한다.
따라서 block 선택, 정렬, fallback, audit을 모두 코드와 데이터 계약으로 추적할 수 있다.

---

## 4. 전체 흐름

```
Skill Intelligence Registry
        ↓
Narrative Block Selector
        ↓
Report Composer
        ↓
Template Renderer
        ↓
Quality Audit
        ↓
Report JSON
```

| 단계 | 책임 | 금지 |
|------|------|------|
| Skill Intelligence Registry | V1 Skill별 definition, behavior, value, narrative 필드 보관 | 사용자 Evidence 생성 |
| Narrative Block Selector | strength/gap/score/confidence에 맞는 V1 Registry 필드 선택 | 점수 재계산 |
| Report Composer | 선택된 필드를 `summary`, `skill_explanations`, `skill_narratives`로 조합 | 새 강점/갭 생성 |
| Template Renderer | 문장 표면을 Report JSON 필드에 맞게 렌더링 | 의미 변경 |
| Quality Audit | 반복 문구, 빈 필드, action wording, Evidence anchor 누락 검사 | 리포트 내용 임의 수정 |

---

## 5. 핵심 컴포넌트

### 5.1 Skill Intelligence Registry

V1 Registry는 현재 `data/skill_descriptions.json`의 실제 필드 구조를 기준으로 한다.
각 Skill은 설명 문장만 가지는 것이 아니라 리포트 전체에서 쓰일 해석 재료를 가진다.

V1 필드:

| 필드 | 의미 |
|------|------|
| `skill_key` | JSON object key로 존재하는 Skill 식별자. `strengths[].skill_key`, `gaps[].skill_key`와 연결된다. |
| `label_ko` | 리포트에 표시할 한국어 스킬명. |
| `definition` | 사용자의 커리어 안에서 해당 스킬을 해석하는 기본 정의. |
| `person_profile` | 이 스킬이 강한 사람에게 나타나는 관점과 판단 방식. |
| `workplace_behavior` | 실제 업무 장면에서 드러나는 행동 패턴. |
| `business_value` | 조직 기여, 운영 안정성, 의사결정 품질 등 비즈니스 의미. |
| `career_relevance` | 사용자의 경험을 커리어 맥락에서 읽는 기준. |
| `market_context` | 실시간 시장 데이터가 아닌 V1 수동 Registry 기반 시장/직무 맥락. |
| `strength_narrative` | 해당 스킬이 strength일 때 사용할 해석 문장 재료. |
| `gap_narrative` | 해당 스킬이 gap일 때 사용할 해석 문장 재료. |
| `development_direction` | 실행 지시가 아닌 설명상 보완 방향. |
| `summary_phrase` | summary, outlook, final assessment에서 짧게 재사용할 핵심 구문. |
| `keywords` | Evidence 연결과 표시 보조에 쓰는 키워드 목록. 새 Evidence를 만들지는 않는다. |

V1 Composer는 위 필드 외의 Registry 입력을 요구하지 않는다.
없는 필드를 임의로 가정하거나 생성하지 않는다.

### 5.2 Narrative Block Selector

Block Selector는 분석을 하지 않는다. 이미 생성된 Engine Output을 읽고
현재 Registry 필드 중 어떤 문장 재료를 사용할지 선택한다.

입력:

- `meta.primary_profile`
- `meta.confidence_level`
- `strengths[]`
- `gaps[]`
- `scores`
- `evidenceMapping[]`
- Skill Registry

선택 기준:

- `source = strength | gap`
- `match_level = FULL | STRONG | PARTIAL | WEAK | NONE`
- `skill_group = UNIQUE | COMMON`
- `is_core`
- evidence 존재 여부
- LOW confidence 여부

V1에서는 별도 `narrative_blocks` 구조를 사용하지 않는다.
`strength_narrative`, `gap_narrative`, `business_value`, `market_context`,
`career_relevance`, `development_direction`, `summary_phrase`를 결정론적으로 조합한다.

### 5.3 Report Composer

Report Composer는 선택된 Registry 필드를 Report JSON 섹션에 배치한다.
새로운 점수, 강점, gap을 만들지 않고, 이미 존재하는 Engine Output을 narrative로 연결한다.

연결 대상:

- `summary.one_line` 또는 summary narrative
- `skill_explanations[]`
- `skill_narratives.career_context`
- `skill_narratives.market_context`
- `skill_narratives.development_direction`
- `skill_narratives.job_outlook`
- `skill_narratives.final_assessment`

V1 중간 출력 매핑:

| Composer output | Report JSON 위치 |
|-----------------|------------------|
| `executive_summary` | `summary.one_line` 또는 `summary` 내부 narrative 필드 |
| `strength_narratives` | `skill_explanations[]` 중 `source="strength"` 항목 |
| `gap_narratives` | `skill_explanations[]` 중 `source="gap"` 항목 |
| `skill_explanations` | `skill_explanations[]` |
| `job_outlook` | `skill_narratives.job_outlook` |
| `final_assessment` | `skill_narratives.final_assessment` |

### 5.4 Template Renderer

Renderer는 Composer가 선택한 Registry 필드를 최종 문장으로 표면화한다.
LLM이 사용되더라도 Renderer 이후의 optional polish로만 동작하며, 내용 변경은 금지된다.

Renderer가 유지해야 하는 값:

- score 수치
- `primary_profile`
- `confidence_level`
- strength/gap 항목과 순서
- Evidence 참조
- `skill_group`, `severity`, `match_level`

### 5.5 Quality Audit

Quality Audit은 Registry와 출력 문장을 모두 검사한다.

검사 항목:

- 빈 필드 0
- schema key 누락 0
- 반복 generic phrase 감소
- 행동 지시 표현 금지: “~하세요”, “권장합니다”, “추천합니다”
- Evidence 없는 경험 주장 금지
- deprecated field 생성 금지: `recommendations`, `roadmap`, `expected_score_gain`, `difficulty`, `time_estimate`

---

## 6. 원칙 연결

### Evidence First

Composer는 Evidence를 생성하지 않는다.
`evidenceMapping[]`, `strengths[].evidence_ids`, `gaps[].reason`에 존재하는 근거만 사용한다.

V1의 `keywords`는 Evidence 연결과 표시를 돕는 보조 정보일 뿐,
없는 경험을 추가하는 규칙이 아니다.

### Deterministic First

Registry 필드 선택은 정렬 가능한 입력값으로만 결정한다.
동점 처리도 `rank`, `skill_key`, `match_level`, `source` 같은 고정 값으로 수행한다.

LLM은 Composer 내부에 들어오지 않는다.
필요한 경우 `09_TEXT_TEMPLATE_RULES.md`의 optional polish 단계에서만 의미를 바꾸지 않고 사용한다.

### Report JSON First

Composer의 최종 출력은 반드시 `05_REPORT_SCHEMA.md`의 공식 Report JSON 섹션에 들어간다.
새 top-level key를 만들지 않는다.

특히 V1에서는 다음 12개 top-level key를 유지한다.

`meta`, `summary`, `careerProfile`, `targetJobAnalysis`, `skillMapping`, `evidenceMapping`,
`scores`, `strengths`, `gaps`, `skill_explanations`, `skill_narratives`, `reportSections`

---

## 7. Skill 추가 시 품질이 좋아지는 구조

새 Skill은 단순히 label과 definition을 추가하는 것이 아니다.
해당 Skill이 리포트 전체의 어느 문장에 어떤 의미로 반영될지 함께 정의한다.

V1 추가 순서:

1. `skill_key`와 taxonomy 등록
2. profile requirement에서 UNIQUE/COMMON 및 weight 연결
3. Evidence extraction keyword 연결
4. Skill Intelligence Registry의 V1 설명 필드 작성
5. Quality Audit 통과

이 구조에서는 Skill이 추가될수록 다음 품질이 함께 좋아진다.

- Executive Summary가 더 구체적인 강점/갭 언어를 사용한다.
- Strength 설명이 단순 칭찬이 아니라 조직 기여로 연결된다.
- Gap 설명이 결핍 단정이 아니라 Evidence 공백 해석이 된다.
- Job Outlook이 score뿐 아니라 Skill 조합을 읽는다.
- Final Assessment가 사용자의 경험 의미를 더 정확히 요약한다.

---

## 8. 예시 JSON — `recruiting`

아래 예시는 V1 Registry 필드 구조를 보여주는 축약 예시다.
실제 `data/skill_descriptions.json`의 긴 문장을 줄인 형태다.

```json
{
  "label_ko": "채용 관리",
  "definition": "채용 관리는 조직에 필요한 역량을 정의하고 후보자 경험을 통해 채용 결과로 연결하는 HR 역량입니다.",
  "person_profile": "이 역량이 강한 사람은 JD 작성, 소싱, 서류 검토, 면접 운영, 오퍼, 후보자 커뮤니케이션을 다루는 모습에서 핵심 변수를 파악합니다.",
  "workplace_behavior": "실무에서는 채용 funnel 운영, 면접 조율, 후보자 커뮤니케이션, 선발 기준 관리로 나타납니다.",
  "business_value": "조직 안에서 채용 관리 역량은 성장에 필요한 사람을 적시에 확보하고 조직의 첫 인상을 설계합니다.",
  "career_relevance": "커리어 관점에서 이 스킬은 채용을 진행했다는 사실보다 어떤 역할을 어떤 기준으로 선발했는지가 중요합니다.",
  "market_context": "HR 시장에서 채용 경험은 운영력, 커뮤니케이션, 사업 이해가 결합된 핵심 역량으로 평가됩니다.",
  "strength_narrative": "채용 관리가 강점으로 확인되면 후보자를 많이 만난 경험보다 조직에 필요한 역할을 정의하고 선발 기준을 운영한 경험으로 해석합니다.",
  "gap_narrative": "채용 관리가 gap으로 나타나면 JD 작성, funnel 운영, 면접 조율, 오퍼 과정의 Evidence가 부족한 상태로 해석합니다.",
  "development_direction": "이 역량은 포지션 목적, funnel 관리, 채용 결과가 함께 보이면 강한 HR 근거가 됩니다.",
  "summary_phrase": "조직 성장에 필요한 사람을 선발 경험으로 연결하는 역량",
  "keywords": ["채용 관리", "JD", "서류", "면접", "오퍼", "후보자"]
}
```

---

## 8.1 V2 확장안

아래 필드는 V1 구현 계약이 아니라 V2 확장안이다.
V1 Composer는 이 필드가 없어도 동작해야 하며, 현재 Registry에 필수로 요구하지 않는다.

| 필드 | V2 의미 |
|------|---------|
| `frames[]` | 해당 Skill을 읽는 관점. 예: growth, risk, accuracy, collaboration. |
| `narrative_blocks` | summary, strength, gap, outlook, final assessment에 사용할 block 후보. |
| `report_hooks` | 어떤 Report JSON 섹션에 영향을 줄 수 있는지 명시한다. |
| `market_signals` | 실시간 시장 데이터가 아닌 수동 Registry 기반 시장 맥락 신호. |
| `evidence_patterns` | 어떤 Evidence 유형과 원문 패턴이 해석 강도를 높이는지 설명한다. |
| `quality_rules` | 금지 표현, Evidence anchor 필수 여부, fallback 조건. |

## 9. 기존 문서와의 관계

| 문서 | 관계 |
|------|------|
| `00_PROJECT_VISION.md` | Evidence First, Deterministic First, Report JSON First 원칙을 그대로 따른다. |
| `05_REPORT_SCHEMA.md` | Composer 출력은 공식 Report JSON top-level key를 변경하지 않는다. |
| `09_TEXT_TEMPLATE_RULES.md` | 현재 V1 템플릿 규칙의 후속 구조이며, LLM optional polish 제한을 유지한다. |
| `data/skill_descriptions.json` | V1 Registry 기준이다. 현재 설명 필드를 사용하며, V2에서 `frames`, `report_hooks`, `quality_rules` 등을 품을 수 있다. |
| `backend/engine/text_template.py` | 현재 Renderer 역할에 가깝고, 향후 Selector/Composer와 분리될 수 있다. |
| `backend/engine/report_builder.py` | Composer 결과를 Report JSON에 조립하는 경계를 유지한다. |

---

## 10. 비범위

이 문서는 다음을 구현하지 않는다.

- FastAPI/API Layer
- 외부 LLM 프레임워크
- RAG 또는 벡터 DB
- 새 Report JSON top-level key
- action recommendation, roadmap, expected score gain
- 실시간 시장 데이터 연동
