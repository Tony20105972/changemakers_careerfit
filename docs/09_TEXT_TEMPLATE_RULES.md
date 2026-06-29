# 09 — Text Template Rules

결정론적 텍스트 생성 규칙.  
LLM은 이 템플릿 결과를 **윤색만** 가능. 내용 변경 불가. (`00_PROJECT_VISION.md` §4 LLM Optional)

> **v3.1 변경:** `{job_family_ko}` 단일 라벨 변수 → `{primary_profile_label_ko}`로 대체.  
> §2(Primary Profile Explanation), §3(LOW Warning), §4(Score Split) 추가.
> **v1.5 정렬:** strengths/gaps는 엔진 출력 스키마를 그대로 사용한다.

---

## 0. 책임 경계

| 책임 | 소유 모듈 | 설명 |
|------|-----------|------|
| `strengths[].headline` | `strength_selector.py` | 스킬/직무 맥락/근거 수를 담은 짧은 결정론 문장 |
| `gaps[].reason` | `gap_analyzer.py` | match_level, 대표 evidence, confidence를 담은 짧은 결정론 문장 |
| `gaps[].recommendation_hint` | `gap_analyzer.py` | gap별 후속 행동을 안내하는 짧은 hint 문장 |
| `summary`, `skill_explanations`, `skill_narratives` | `text_template.py` | 리포트 요약, 스킬별 의미 설명, 커리어 내러티브 문장 생성 |
| LLM | optional polish | 템플릿 결과의 윤색만 허용. 필드, 점수, 항목, 순서 변경 금지 |

---

## 1. 점수별 요약 문장 (`summary.one_line`)

```python
SUMMARY_TEMPLATES = {
    "EXCELLENT_FIT": "{primary_profile_label_ko} 기준에서 매우 높은 적합도({score}점)를 보입니다. 핵심 역량과 범용 역량 모두에서 검증된 경험이 확인됩니다.",
    "GOOD_FIT":      "{primary_profile_label_ko} 기준에서 높은 적합도({score}점)를 보입니다. {top_gap_label_ko} 영역의 보강을 통해 경쟁력을 더욱 높일 수 있습니다.",
    "MODERATE_FIT":  "{primary_profile_label_ko} 기준에서 기본적인 적합도({score}점)를 보입니다. {top_gap_label_ko} 등 주요 갭을 체계적으로 보완하면 목표 달성이 가능합니다.",
    "LOW_FIT":       "{primary_profile_label_ko} 기준 적합도({score}점)는 현재 낮은 수준입니다. 핵심 역량({unique_score}/65점) 확보를 위한 전략적 준비가 필요합니다.",
}
```

| 변수 | 출처 |
|------|------|
| `{primary_profile_label_ko}` | `meta.primary_profile` 라벨 lookup 결과 |
| `{score}` | `summary.total_score` |
| `{top_gap_label_ko}` | `gaps[0].label_ko` (`rank=1`) |
| `{unique_score}` | `summary.unique_score` |

---

## 2. Primary Profile Explanation 템플릿 (`summary.primary_profile_summary`)

```python
PRIMARY_PROFILE_TEMPLATES = {
    "HIGH": "입력된 근거를 기준으로 {primary_profile_label_ko}를 대표 프로필로 선택했습니다.",
    "MEDIUM": "입력된 근거로 {primary_profile_label_ko}를 대표 프로필로 선택할 수 있습니다. 일부 보조 신호는 {secondary_profile_labels}에서도 확인됩니다.",
    "LOW": "입력 정보가 제한적이므로 {primary_profile_label_ko}를 임시 대표 프로필로 선택했습니다.",
}

def build_primary_profile_summary(primary_profile_label_ko: str, secondary_profile_labels: list[str],
                                  confidence_level: str) -> str:
    labels = ", ".join(secondary_profile_labels[:2]) if secondary_profile_labels else "다른 프로필"
    return PRIMARY_PROFILE_TEMPLATES[confidence_level].format(
        primary_profile_label_ko=primary_profile_label_ko,
        secondary_profile_labels=labels,
    )
```

---

## 3. LOW Warning 템플릿

```python
LOW_CONFIDENCE_WARNING = (
    "입력 정보가 부족하여 일부 결과는 추정에 기반합니다. "
    "담당 업무, 성과, 목표 직무를 더 구체적으로 입력하면 분석 정확도가 높아집니다."
)
```

LOW에서는 `meta.warning_message`에 위 문구 또는 같은 의미의 문구가 반드시 들어간다.

---

## 4. UNIQUE/COMMON 분리 요약 (`summary` 보조)

```python
SCORE_SPLIT_TEMPLATES = {
    "unique_high_common_high":  "{primary_profile_label_ko} 고유 역량({unique_score}/65점)과 범용 역량({common_score}/35점) 모두 우수한 수준입니다.",
    "unique_high_common_low":   "{primary_profile_label_ko} 고유 역량({unique_score}/65점)은 우수하나, 협업·문서화 등 범용 역량({common_score}/35점)의 보완이 권장됩니다.",
    "unique_low_common_high":   "범용 역량({common_score}/35점)은 우수하나, {primary_profile_label_ko} 고유 역량({unique_score}/65점)의 확보가 우선적으로 필요합니다.",
    "unique_low_common_low":    "{primary_profile_label_ko} 고유 역량과 범용 역량 모두({unique_score}/65점, {common_score}/35점) 보완이 필요한 단계입니다.",
}

def select_split_template(unique_score: float, common_score: float) -> str:
    u = "high" if (unique_score / 65) >= 0.7 else "low"
    c = "high" if (common_score / 35) >= 0.7 else "low"
    return SCORE_SPLIT_TEMPLATES[f"unique_{u}_common_{c}"]
```

---

## 5. 강점 텍스트 입력 (`strengths[]`)

`strengths[]`는 `05_REPORT_SCHEMA.md` §8의 v1.5 구조를 사용한다.
`text_template.py`는 강점 항목을 새로 판정하지 않고 아래 필드만 문장 재료로 사용한다.

| 필드 | 텍스트 사용 |
|------|-------------|
| `headline` | 강점 카드/요약의 기본 문장. 엔진이 생성한 원문을 유지 |
| `strength_score` | 강점 강조 정도 산정. 값 변경 금지 |
| `evidence_ids` | 근거 참조 연결. 존재하지 않는 evidence를 새로 만들지 않음 |
| `match_level` | `FULL > STRONG > PARTIAL` 순으로 표현 강도 조절 |
| `skill_key`, `label_ko` | summary/key_strengths/본문 라벨 표시 |

```python
STRENGTH_EMPHASIS_LABELS = {
    "FULL": "명확한 강점",
    "STRONG": "충분한 강점",
    "PARTIAL": "보완 중인 강점",
}
```

`evidence_ids`가 비어 있으면 근거 상세 문장을 만들지 않고 `headline`만 사용한다.
LOW confidence에서는 `meta.warning_message`와 함께 추정 가능성을 유지한다.

---

## 6. Gap 텍스트 입력 (`gaps[]`)

`gaps[]`는 `05_REPORT_SCHEMA.md` §9의 v1.5 구조를 사용한다.
gap 후보는 `NONE`, `WEAK`, `PARTIAL`만 허용하며 `STRONG`, `FULL`은 제외한다.

```python
GAP_SEVERITY_LABELS = {
    "CRITICAL": "핵심 결핍",
    "HIGH": "우선 보강",
    "MEDIUM": "계획 보강",
    "LOW": "추가 보완",
}
```

| 필드 | 텍스트 사용 |
|------|-------------|
| `severity` | `CRITICAL \| HIGH \| MEDIUM \| LOW` 표시 및 설명 강도 입력 |
| `reason` | gap 카드/본문의 기본 설명. 엔진이 생성한 원문을 유지 |
| `recommendation_hint` | gap 설명의 보조 재료. 완성 action recommendation 문장으로 간주하지 않음 |
| `gap_score` | 결핍 강도 표현 입력. 예상 개선폭 산정에는 사용하지 않음 |
| `rank`, `skill_key`, `label_ko` | key_gaps, skill_explanations 연결 기준 |

---

## 7. 스킬 설명 (`skill_explanations`)

Day 12는 Action Recommendation이 아니라 Skill Intelligence Layer다.
`text_template.py`는 Evidence, strength, gap을 변경하지 않고 각 스킬이 사용자의 커리어와 대표 프로필 시장에서
어떤 의미를 갖는지 설명한다.

```json
{
  "skill_key": "labor_law",
  "label_ko": "노동법",
  "source": "gap",
  "career_context": "HR 직무에서 노동법은 채용, 평가, 보상, 조직 운영 판단의 기준이 되는 핵심 역량입니다.",
  "market_context": "인사 직무 채용 시장에서는 법적 리스크를 이해하고 실무 의사결정에 적용할 수 있는 역량을 중요하게 봅니다.",
  "development_direction": "현재 Evidence에는 노동법 적용 경험이 확인되지 않으므로, 향후 경험 서술에서는 관련 판단 과정과 적용 사례를 보강하는 방향이 적절합니다."
}
```

| 필드 | 생성 규칙 |
|------|-----------|
| `skill_key` | `strengths[].skill_key` 또는 `gaps[].skill_key` |
| `label_ko` | 원본 strength/gap의 라벨 유지 |
| `source` | `strength \| gap` |
| `career_context` | Evidence가 보여주는 현재 커리어 맥락 또는 Evidence 부재가 의미하는 설명 공백 |
| `market_context` | `primary_profile` requirement의 `weight`, `is_core`, `skill_group` 기준 시장/직무 의미 |
| `development_direction` | 실행 명령이 아닌 설명 방향. Evidence를 새로 만들거나 점수를 바꾸지 않음 |

```python
SKILL_EXPLANATION_TEMPLATES = {
    "strength_career_context": "{label_ko}은(는) 현재 Evidence에서 반복적으로 확인되는 강점이며, {primary_profile_label_ko} 직무 설명의 핵심 재료가 됩니다.",
    "gap_career_context": "{label_ko}은(는) 현재 Evidence에서 충분히 확인되지 않아 커리어 설명에서 공백으로 남아 있습니다.",
    "core_market_context": "{primary_profile_label_ko} 시장에서 {label_ko}은(는) 핵심 요구 역량으로 해석되므로, 적합도 판단의 중요한 기준입니다.",
    "common_market_context": "{label_ko}은(는) 여러 직무에서 함께 요구되는 범용 역량이며, 협업과 실행 신뢰도를 설명하는 데 사용됩니다.",
    "strength_development_direction": "이미 확인된 근거를 중심으로 역할, 성과, 판단 과정을 더 선명하게 연결하는 방향이 적절합니다.",
    "gap_development_direction": "새 Evidence를 임의로 추가하지 않고, 부족한 지점을 앞으로 설명해야 할 성장 방향으로 표현합니다.",
}
```

---

## 8. 커리어 내러티브 (`skill_narratives`)

Day 12 Narrative Template Layer는 `skill_explanations`를 바탕으로 리포트 후반부의 읽히는 문단을 만든다.
이는 단계별 행동 계획이 아니라 career/market/development/job outlook/final assessment를 연결하는 설명 레이어다.

```json
{
  "career_context": "확인된 강점은 채용과 온보딩 실행 경험에 집중되어 있으며, HR 운영형 역할과 잘 맞습니다.",
  "market_context": "시장 관점에서는 채용 운영 경험에 더해 노동법, 급여, 평가 운영처럼 리스크와 제도를 다루는 역량이 함께 요구됩니다.",
  "development_direction": "새 Evidence를 만들거나 점수를 조정하지 않고, 현재 확인된 gap을 커리어 설명에서 보완해야 할 방향으로 해석합니다.",
  "job_outlook": "대표 프로필인 HR 기준으로는 실무 운영 경험이 강점이며, 제도/법무 기반 역량 설명이 강화될수록 지원 가능성이 높아집니다.",
  "final_assessment": "현재 리포트는 HR 적합성을 설명할 충분한 실무 근거를 포함하지만, 노동법과 급여 관리에 대한 설명 가능성은 보완이 필요합니다."
}
```

| 필드 | 생성 규칙 |
|------|-----------|
| `career_context` | 상위 strengths와 gaps를 함께 읽어 사용자의 현재 커리어 서사를 설명 |
| `market_context` | `primary_profile` requirement 기준으로 시장/직무 요구를 설명. 외부 실시간 API 사용 금지 |
| `development_direction` | action list가 아니라 보완해야 할 설명 방향을 제시 |
| `job_outlook` | `fit_level`, `unique_score`, `common_score`, 핵심 gap을 바탕으로 직무 전망을 설명 |
| `final_assessment` | 점수와 Evidence를 변경하지 않는 최종 판단 문단 |

---

## 9. 최종 평가 문장 (`skill_narratives.final_assessment`)

```python
CONCLUSION_TEMPLATES = {
    "EXCELLENT_FIT": "현재 역량 수준으로 {primary_profile_label_ko} 포지션 지원을 강력히 권장합니다.",
    "GOOD_FIT":      "{key_gap_ko} 역량을 보강하면 {primary_profile_label_ko} 포지션에서 높은 경쟁력을 갖출 수 있습니다.",
    "MODERATE_FIT":  "90일 로드맵에 따른 역량 보완 후 {primary_profile_label_ko} 포지션 지원을 권장합니다.",
    "LOW_FIT":       "현재 단계에서는 고유 핵심 역량({unique_score}/65) 확보가 선행되어야 합니다. 6개월 이상의 준비 기간을 권장합니다.",
}
```

`final_assessment`는 독립 action recommendation이 아니며 `skill_narratives` 내부의 최종 평가 문단이다.
LLM은 선택적 윤색만 가능하고, 판단 등급·점수·Evidence 참조를 변경할 수 없다.

---

## 9.1 Deprecated Action Recommendation Fields

아래 필드는 Day 12 action recommendation 초안의 잔재이며 V1 Skill Intelligence Layer에서는 생성하지 않는다.

| 필드 | 처리 |
|------|------|
| `recommendations` | optional deprecated. 새 Day 12 구현의 기준이 아님 |
| `roadmap` | optional deprecated. 새 Day 12 구현의 기준이 아님 |
| `difficulty` | deprecated. 난이도 추정은 설명 레이어 범위가 아님 |
| `expected_score_gain` | deprecated. 예상 점수 상승값은 생성하지 않음 |
| `time_estimate` | deprecated. 기간 추정은 생성하지 않음 |

---

## 10. LLM 윤색 지침

**허용:**
- 문장 자연스러움 개선
- 존댓말 통일
- 접속사 추가/변경
- 문장 분리 또는 결합 (의미 유지 시)

**금지:**
- 점수 수치 변경 (`total_score`, `unique_score`, `common_score` 등 모든 숫자)
- `primary_profile`, `secondary_profiles`, `confidence_level`, `warning_message` 변경 또는 누락
- 강점/갭 항목 추가 또는 제거
- `skill_group`(UNIQUE/COMMON), `severity`, `match_level` 분류 변경
- `strength_score`, `gap_score`, `evidence_ids`, `recommendation_hint` 변경
- Evidence에 없는 경험 추가
- `fit_level` 평가 변경
- LOW warning 의미 약화 또는 삭제 금지

**LLM 프롬프트 구조:**
```
System: 당신은 커리어 리포트 문장을 자연스럽게 다듬는 편집자입니다.
        내용(점수, 강점 항목, 갭 항목, 스킬 설명, UNIQUE/COMMON 구분,
        primary_profile, confidence_level, warning_message)는 절대 변경하지 마세요.
        문장의 흐름과 자연스러움만 개선하세요.

User: 다음 텍스트를 자연스럽게 윤색해주세요:
      {template_generated_text}
```

**폴백 (필수):**
```python
def polish_text(template_text: str) -> str:
    try:
        return llm_polish(template_text)
    except Exception:
        return template_text  # 폴백 — 템플릿 결과 그대로
```

---

## 11. 알려진 문제점 (§ Limitations)

| 문제 | 영향 | 비고 |
|------|------|------|
| skill별 action template이 없으면 추천 문장이 일반적으로 보일 수 있음 | 추천 품질 저하 | `recommendation_hint`를 기본값으로 사용하고 template 확장 필요 |
| LOW warning이 반복적으로 보이면 사용자 불안이 커질 수 있음 | 리포트 신뢰 저하 | 경고는 1회 명확히 표시하고, 나머지는 추가 입력 권장으로 연결 |
