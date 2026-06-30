# 15 — Career Pattern Library Architecture

Career Pattern Library는 Skill Intelligence Registry와 Narrative Composer 사이에 위치하는
해석 계층(Interpretation Layer)이다.

이 문서는 구현 코드가 아니라 Architecture Contract다. Pattern Library가 무엇을 입력으로 받고,
어떤 해석 신호를 출력하며, Skill Registry, Narrative Composer, Report Builder와 어떤 책임 경계를
가지는지 먼저 고정한다. 이후 구현은 이 계약을 기준으로 진행한다.

---

## 1. 목적

현재 CareerFit Narrative는 다음 구조에 가깝다.

```
Skill Intelligence Registry -> Narrative Composer
```

이 구조에서는 Narrative가 주로 Skill 단위로 생성된다. `recruiting`이 있으면 채용 설명을 만들고,
`communication`이 있으면 커뮤니케이션 설명을 만드는 1:1 매핑에 가깝다. Skill 수가 늘어나면 설명
재료는 늘어나지만, 여러 Skill 사이의 관계가 어떤 커리어 의미를 갖는지는 별도의 계층에서 해석되지 않는다.

사람이 채용 공고나 이력서를 읽을 때 보는 것은 개별 스킬의 나열만이 아니다. 예를 들어
`recruiting`, `negotiation`, `relationship_building`이 따로 설명되는 것과, 이 조합을
"Ownership 기반 채용 운영자"라는 상위 패턴으로 읽는 것은 전혀 다른 가치다. Executive Summary와
Final Assessment는 이런 상위 판단이 필요하지만, 현재 구조에서는 Narrative Composer 내부에서
임시로 여러 Skill을 조합해야 하므로 책임이 모호해진다.

Career Pattern Library의 목적은 여러 Skill, Evidence, Profile, Market Context를 함께 관찰해
반복적으로 나타나는 Career Story를 감지하고, Narrative Composer에게 이미 해석된 신호를 전달하는 것이다.

---

## 2. Architecture

### Before

```
Evidence
  -> Skill Registry
  -> Narrative Composer
  -> Text Template
  -> Report Builder
  -> Report JSON
```

Before 구조에서는 Skill Registry가 Skill별 의미를 제공하고, Narrative Composer가 이를 문장으로
조합한다. 이 흐름은 개별 Skill 설명에는 충분하지만, 여러 Skill의 공존이 만드는 패턴을 별도 산출물로
분리하지 못한다.

### After

```
Evidence
  -> Evidence Mapping
  -> Skill Registry
  -> Career Pattern Library
  -> Narrative Composer
  -> Text Template
  -> Report Builder
  -> Report JSON
```

추가되는 것은 `Career Pattern Library`이며, 위치는 Skill Registry 이후와 Narrative Composer 이전이다.
이 위치가 중요한 이유는 Pattern이 원문 Evidence나 Skill 자체를 생성하는 계층이 아니라, 이미 추출되고
정규화된 Evidence/Skill 신호를 Career Story 단위로 해석하는 계층이기 때문이다.

Pattern Library가 앞단에 있으면 Evidence Engine이나 Scoring Engine의 책임과 섞이고, 뒤쪽에 있으면
Narrative Composer가 다시 Skill 조합 판단을 떠안게 된다. 따라서 Pattern은 "분석 결과를 바꾸지 않고
해석 단위를 만드는" 중간 계층으로 고정한다.

---

## 3. Career Pattern Library의 역할

Career Pattern Library는 단일 Skill 설명을 만드는 사전이 아니다. 여러 Skill과 Evidence가 동시에
나타날 때 그 조합이 어떤 커리어 의미를 갖는지 읽는 해석 계층이다.

입력은 다음과 같다.

- `evidenceMapping[]` 또는 엔진 Evidence 목록
- Skill Registry의 Skill별 설명 필드
- `strengths[]`, `gaps[]`, `scores`
- `meta.primary_profile`, `meta.secondary_profiles`, `meta.confidence_level`
- V1 수동 Registry 기반 Market Context

출력은 다음과 같은 중간 해석 신호다.

- 감지된 Pattern 목록
- Pattern별 우선순위
- Pattern을 설명하는 Evidence anchor
- Narrative Composer가 사용할 hook
- 사용자가 왜 이 Pattern으로 해석되었는지 설명하는 explainability

Pattern Library는 Report JSON의 새 top-level key를 강제하지 않는다. V1에서는 Composer가 이 중간 신호를
`summary`, `skill_explanations`, `skill_narratives`의 기존 공식 위치로 렌더링한다.

---

## 4. Pattern Detection

Pattern Detection은 여러 Skill과 Evidence를 함께 읽어 반복 가능한 커리어 의미를 감지하는 책임이다.
개별 Skill의 match level을 다시 계산하지 않고, 이미 생성된 `strengths[]`, `gaps[]`, `evidenceMapping[]`,
`scores`를 입력으로만 사용한다.

Detection이 필요한 이유는 Skill 단위 Narrative가 "무엇을 할 수 있는가"를 설명하는 데 강하지만,
"어떤 유형의 일꾼인가"를 설명하기 어렵기 때문이다. Pattern Detection은 다음 질문에 답한다.

- 강점 Skill들이 같은 업무 장면을 가리키는가?
- Evidence가 실행, 판단, 조율, 개선, 고객 영향 중 어떤 반복 장면을 보여주는가?
- gap이 단순 결핍인지, 특정 Career Story를 완성하기 위해 필요한 설명 공백인지?
- `primary_profile`에서 이 조합이 어떤 직무적 의미를 갖는가?

Detection은 결정론적으로 동작해야 한다. 같은 Engine Output과 같은 Registry 입력은 같은 Pattern 후보와
같은 confidence를 만들어야 한다.

---

## 5. Pattern Priority

Pattern Priority는 감지된 여러 Pattern 중 어떤 해석을 Executive Summary, Job Outlook, Final Assessment에
먼저 반영할지 정하는 책임이다.

우선순위는 점수를 새로 계산하는 것이 아니다. 이미 존재하는 점수와 Evidence 품질을 읽어 Narrative 상의
강조 순서를 정한다.

우선순위 입력 예시는 다음과 같다.

- 연결된 Evidence 수와 Evidence type
- 관련 Skill의 `match_level`
- 관련 Skill이 UNIQUE인지 COMMON인지
- 관련 Skill이 `is_core`인지
- `primary_profile`과의 관련성
- LOW confidence 여부
- strength와 gap이 같은 Pattern 안에서 함께 설명되는지

이 책임이 Pattern Library에 있어야 하는 이유는 Composer가 문장을 만들기 전에 "어떤 Career Story가
핵심인가"가 정해져야 하기 때문이다. Composer가 우선순위까지 직접 판단하면 텍스트 렌더링과 해석 판단이
섞이고, 향후 Skill Registry가 확장될수록 책임 경계가 흐려진다.

---

## 6. Pattern Composition

Pattern Composition은 하나의 Pattern 안에서 Skill, Evidence, Profile, Market Context를 어떤 Career Story로
묶을지 정의한다.

Composition은 단순히 Skill 이름을 이어 붙이는 것이 아니다. 예를 들어 채용 관련 Skill, 협상 관련 Skill,
관계 구축 Evidence가 함께 있을 때 이를 "사람을 뽑았다"가 아니라 "조직의 필요와 후보자의 기대를 연결해
채용 결과를 만든 운영형 역할"로 해석하는 책임이다.

Composition은 다음을 만든다.

- Pattern의 핵심 해석 문장
- Pattern을 뒷받침하는 주요 Skill 목록
- Pattern과 연결되는 Evidence anchor
- strength와 gap을 함께 읽는 보완 관점
- `primary_profile` 시장 맥락에서의 의미

이 계층이 있어야 Executive Summary와 Final Assessment가 개별 Skill 설명의 합이 아니라, 사용자의 커리어를
상위 레벨에서 읽는 판단 문단이 될 수 있다.

---

## 7. Narrative Hook

Narrative Hook은 Pattern Library가 Narrative Composer에게 전달하는 사용처 신호다. Composer는 Pattern을
새로 판단하지 않고, hook을 읽어 기존 Report JSON 섹션에 문장을 배치한다.

대표 hook은 다음 위치를 가리킬 수 있다.

- `summary.one_line`
- `summary.primary_profile_summary`의 보조 문맥
- `skill_explanations[]`
- `skill_narratives.career_context`
- `skill_narratives.market_context`
- `skill_narratives.development_direction`
- `skill_narratives.job_outlook`
- `skill_narratives.final_assessment`

Hook이 필요한 이유는 Pattern Library가 해석 계층이고, Composer가 렌더링 계층이기 때문이다. Pattern은
"이 조합은 어떤 Career Story인가"를 말하고, Composer는 "그 Story를 어느 문단에 어떤 길이로 배치할 것인가"를
담당한다.

---

## 8. Pattern Explainability

Pattern Explainability는 감지된 Pattern이 왜 선택되었는지 추적 가능한 형태로 남기는 책임이다.

Pattern은 상위 해석이기 때문에, 근거가 불투명하면 Evidence First 원칙을 약화시킨다. 따라서 모든 Pattern은
다음 질문에 답할 수 있어야 한다.

- 어떤 Skill 조합 때문에 이 Pattern이 감지되었는가?
- 어떤 Evidence 원문 또는 Evidence ID가 이 Pattern을 뒷받침하는가?
- 어떤 Profile/Market Context에서 이 Pattern이 의미를 갖는가?
- confidence가 낮다면 어떤 설명 공백 때문에 낮은가?
- Pattern이 strength 중심인지, gap 보완 중심인지, 혼합형인지?

Explainability는 사용자에게 항상 그대로 노출되는 문장이 아니라, Composer와 Quality Audit이 사용할 수 있는
추적 가능한 해석 근거다.

---

## 9. Evidence 연결 방식

Pattern Library는 Evidence를 생성하지 않는다. 기존 Evidence를 참조하고 묶을 뿐이다.

Evidence 연결은 다음 원칙을 따른다.

- `original_text`는 절대 수정하지 않는다.
- 존재하지 않는 Evidence ID를 만들지 않는다.
- Evidence가 없는 Skill을 Pattern의 확정 근거로 사용하지 않는다.
- `target_priority_text`에서 나온 Evidence는 `source="target_priority_text"` 맥락을 유지한다.
- LOW confidence에서는 Pattern을 단정하지 않고 설명 공백과 함께 표시한다.

Pattern은 Evidence를 Career Story로 해석하지만, Evidence 자체를 보강하거나 대체하지 않는다. 이 경계가
무너지면 Pattern Library가 Evidence Engine처럼 동작하게 되고, 사용자 입력에 없는 경험을 만든 것처럼 보일
위험이 생긴다.

---

## 10. Skill Registry와의 관계

Skill Registry는 Skill 단위 의미의 원천이다. Pattern Library는 Skill Registry를 대체하지 않는다.

Skill Registry가 제공하는 것은 `skill_key`, label, definition, strength/gap narrative, market context 같은
Skill별 해석 재료다. Pattern Library는 이 재료를 여러 Skill에 걸쳐 읽고, 특정 조합이 어떤 Career Story를
만드는지 판단한다.

이 관계가 중요한 이유는 확장 방향이 다르기 때문이다. Skill Registry 확장은 "더 많은 Skill을 더 정확히
설명"하는 일이고, Pattern Library 확장은 "여러 Skill의 관계를 더 깊게 해석"하는 일이다. 두 책임이 섞이면
새 Skill을 추가할 때마다 Pattern 로직이 비대해지거나, 반대로 Pattern을 추가할 때 Skill definition이
불필요하게 복잡해진다.

---

## 11. Narrative Composer와의 관계

Narrative Composer는 Pattern Library가 만든 해석 신호를 Report JSON의 기존 narrative 위치로 조합한다.

Composer가 담당하는 것은 다음이다.

- Pattern hook을 읽어 문단 위치를 선택한다.
- Skill Registry 문장과 Pattern 해석을 중복 없이 조합한다.
- Text Template 규칙에 맞게 문장을 렌더링한다.
- 점수, Evidence, strength/gap 순서를 변경하지 않는다.
- optional LLM polish 전에도 유효한 템플릿 문장을 만든다.

Pattern Library가 Composer 앞에 있어야 하는 이유는 Composer가 "문장을 만드는 책임"과 "상위 커리어 패턴을
감지하는 책임"을 동시에 갖지 않게 하기 위해서다. 이 분리는 Executive Summary와 Final Assessment의 품질을
구조적으로 높인다.

---

## 12. Report Builder와의 관계

Report Builder는 최종 Report JSON을 조립하는 계층이다. Pattern Library는 Report Builder를 직접 대체하거나
Report JSON 구조를 임의로 확장하지 않는다.

V1 기준으로 Pattern 신호는 Composer와 Text Template을 거쳐 다음 공식 필드에 반영된다.

- `summary`
- `skill_explanations`
- `skill_narratives`

Report Builder는 기존 `05_REPORT_SCHEMA.md`의 top-level key 집합을 유지한다. Pattern Library가 별도
top-level key를 요구하지 않는 이유는 Report JSON First 원칙 때문이다. 새 해석 계층을 추가하더라도 PDF,
화면, API 응답의 공식 계약은 안정적으로 유지되어야 한다.

---

## 13. Pattern 책임 범위

### Pattern이 하지 않는 것

- 점수를 계산하지 않는다.
- Requirement Match를 수정하지 않는다.
- Evidence를 생성하지 않는다.
- Skill을 대체하지 않는다.

### Pattern이 하는 것

- Evidence, Skill, Profile, Market Context를 하나의 Career Story로 해석한다.
- 여러 Skill 사이의 관계를 감지한다.
- Executive Summary와 Final Assessment에 사용할 상위 해석 신호를 만든다.
- 감지된 Pattern의 Evidence anchor와 explainability를 제공한다.
- Narrative Composer가 사용할 hook과 priority를 제공한다.

이 경계가 중요한 이유는 Scoring/Evidence Engine과 해석 계층이 섞이면 결정론과 추적 가능성이 약해지기
때문이다. Pattern이 점수나 match를 바꾸기 시작하면 같은 Evidence에서 다른 점수가 나올 수 있고, Pattern이
Evidence를 만들기 시작하면 사용자 원문에 없는 경험이 리포트에 들어갈 수 있다. Pattern은 판단 결과를
바꾸는 계층이 아니라, 이미 계산된 결과를 더 높은 커리어 의미로 읽는 계층이다.

---

## 14. Pattern 예시 이름

아래 Pattern 이름은 예시이며 구현을 강제하지 않는다.

- Ownership
- Decision Making
- Operational Excellence
- Relationship Building
- Analytical Thinking
- Process Improvement
- Customer Impact
- Leadership
- Learning Agility

실제 구현 시 Pattern 이름, 개수, trigger 조건은 운영 데이터와 Skill Registry 확장 상태를 보고 별도 커밋에서
정의한다.

---

## 15. Pattern Contract 예시

아래 JSON은 Pattern Contract의 예시이며 실제 Schema 정의 파일이 아니다. 구현을 강제하는 대량 Pattern 데이터가
아니며, 문서 계약을 설명하기 위한 단 하나의 예시다.

```json
{
  "pattern_id": "ownership_recruiting_operator",
  "title": "Ownership 기반 채용 운영자",
  "description": "채용 실행, 이해관계자 조율, 후보자 커뮤니케이션 Evidence가 함께 확인될 때 사용자의 역할을 단순 채용 수행자가 아니라 채용 결과를 끝까지 책임지는 운영형 인재로 해석한다.",
  "trigger_condition": {
    "required_strength_skills": ["recruiting"],
    "supporting_skills_any": ["stakeholder_management", "communication", "coordination"],
    "minimum_evidence_count": 3,
    "allowed_profiles": ["hr", "operations"],
    "excluded_when_confidence_level": []
  },
  "priority": {
    "base": "HIGH",
    "boost_when": ["primary_profile=hr", "recruiting.match_level=FULL", "explicit_evidence_count>=2"],
    "lower_when": ["confidence_level=LOW", "evidence_anchor_missing"]
  },
  "related_skills": ["recruiting", "stakeholder_management", "communication", "coordination"],
  "related_job_families": ["hr", "operations"],
  "narrative_hooks": ["summary.one_line", "skill_narratives.career_context", "skill_narratives.final_assessment"],
  "explainability": {
    "why_detected": "채용 실행 Skill과 조율/커뮤니케이션 Skill이 함께 확인되어, 사람을 선발하는 업무뿐 아니라 프로세스와 관계를 끝까지 운영한 신호로 해석한다.",
    "evidence_anchor_policy": "관련 Skill의 기존 evidence_ids만 참조하며 original_text는 수정하지 않는다.",
    "gap_interpretation": "노동법, 평가, 급여 등 HR 제도 Skill이 gap이면 채용 운영 Pattern의 확장 공백으로 설명할 수 있다."
  },
  "confidence_rule": {
    "HIGH": "필수 Skill이 FULL이고 supporting Skill 중 2개 이상이 STRONG 이상이며 Evidence가 4개 이상일 때",
    "MEDIUM": "필수 Skill이 STRONG 이상이고 supporting Skill 중 1개 이상이 확인될 때",
    "LOW": "필수 Skill Evidence는 있으나 supporting Skill 또는 Evidence anchor가 부족할 때"
  }
}
```

---

## 16. 불변 규칙

1. Pattern Library는 결정론적으로 동작한다.
2. Pattern Library는 기존 Evidence와 Skill 신호만 사용한다.
3. Pattern Library는 Report JSON top-level key를 임의로 추가하지 않는다.
4. Pattern Library는 `05_REPORT_SCHEMA.md`의 공식 출력 구조를 변경하지 않는다.
5. Pattern Library는 `06_SCORING_RULES.md`의 점수, match, gap, strength 규칙을 변경하지 않는다.
6. Pattern Library는 `09_TEXT_TEMPLATE_RULES.md`의 LLM optional polish 제한을 유지한다.
7. Pattern Library output은 Quality Audit에서 Evidence anchor와 금지 표현 검사를 통과해야 한다.

---

## 17. 기존 문서와의 관계

| 문서 | 관계 |
|------|------|
| `00_PROJECT_VISION.md` | Evidence First, Deterministic First, Report JSON First 원칙을 따른다. |
| `04_PAYLOAD_CONTRACT.md` | API/Engine payload 계약을 변경하지 않는다. 향후 Pattern output을 Engine 내부 중간 산출물로 다룬다. |
| `05_REPORT_SCHEMA.md` | 공식 Report JSON top-level key를 변경하지 않는다. |
| `06_SCORING_RULES.md` | 점수, match, gap, strength 판단을 변경하지 않는다. |
| `09_TEXT_TEMPLATE_RULES.md` | Pattern hook은 템플릿 문장 재료가 되며, LLM은 optional polish로만 남는다. |
| `14_NARRATIVE_COMPOSER_ARCHITECTURE.md` | Composer 앞에 Pattern Library를 추가해 Skill 단위 해석과 Career Story 단위 해석을 분리한다. |

---

## 18. 비범위

이 문서는 다음을 구현하지 않는다.

- Backend 코드
- Engine 코드
- JSON 데이터 파일
- Skill Registry 수정
- Report Schema 수정
- 대량 Pattern 생성
- 외부 LLM 프레임워크
- RAG 또는 벡터 DB
- 실시간 채용 공고 API 연동
