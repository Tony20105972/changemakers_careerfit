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
| `summary`, `final_assessment`, `roadmap` | `text_template.py` | 리포트 요약, 최종 판단, 단계별 행동 문장 생성 |
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
| `severity` | `CRITICAL \| HIGH \| MEDIUM \| LOW` 표시 및 추천 우선순위 입력 |
| `reason` | gap 카드/본문의 기본 설명. 엔진이 생성한 원문을 유지 |
| `recommendation_hint` | 추천 엔진의 입력 hint. 완성 recommendation 문장으로 간주하지 않음 |
| `gap_score` | 결핍 강도와 예상 개선폭 산정 입력 |
| `rank`, `skill_key`, `label_ko` | key_gaps, recommendation, roadmap 연결 기준 |

---

## 7. 추천 문장 (`recommendations`)

Day 12 recommendation schema 초안은 gap을 source로 하는 독립 섹션이다.
`gaps[].recommendation_hint`는 추천의 재료이며, 최종 추천 문장은 아래 구조에서 생성한다.

```json
{
  "recommendation_id": "rec_001",
  "source_gap_skill_key": "labor_law",
  "title": "노동법 실무 적용 경험 보강",
  "detail": "노동법 관련 프로젝트 또는 자격 취득을 통해 핵심 결핍을 보완합니다.",
  "priority": "HIGH",
  "difficulty": "MEDIUM",
  "expected_score_gain": 4.2,
  "time_estimate": "4-6 weeks"
}
```

| 필드 | 생성 규칙 |
|------|-----------|
| `recommendation_id` | deterministic id. 예: `rec_001` |
| `source_gap_skill_key` | 연결된 `gaps[].skill_key` |
| `priority` | `severity`와 `rank` 기준 (`CRITICAL/HIGH` 우선) |
| `difficulty` | skill별 action template에서 결정. 없으면 `MEDIUM` |
| `expected_score_gain` | `gap_score`와 requirement weight 기반 추정값 |
| `time_estimate` | action template의 기본 기간 |

```python
RECOMMENDATION_TEMPLATES = {
    "short_term": "{gap_label_ko} 역량 강화를 위해 {timeframe} 내 {action}을(를) 권장합니다.",
    "mid_term_high_score": "현재 적합도 수준({score}점, 고유 역량 {unique_score}/65)에서 {primary_profile_label_ko} 포지션 지원이 가능합니다. {action}을(를) 통해 경쟁력을 높이세요.",
    "mid_term_low_score":  "현재 적합도 수준({score}점)에서는 핵심 역량 보강을 우선하는 것을 권장합니다. {action}을(를) 통해 고유 역량({unique_score}/65)을 끌어올리세요.",
}

def select_mid_term_template(unique_score: float) -> str:
    return "mid_term_high_score" if (unique_score / 65) >= 0.6 else "mid_term_low_score"
```

---

## 8. 로드맵 문장 (`roadmap`)

Day 12 roadmap schema 초안은 recommendation을 기간별로 묶은 단계형 구조다.

```json
{
  "phase": "phase_1",
  "period": "0-30 days",
  "theme": "핵심 결핍 보완",
  "actions": ["노동법 실무 사례 3건 정리", "관련 프로젝트 포트폴리오 초안 작성"],
  "expected_outcome": "핵심 gap에 대한 설명 가능한 근거 확보"
}
```

`actions[]`는 recommendation의 `detail`, `difficulty`, `time_estimate`를 사용해 생성한다.
LOW confidence에서는 추가 입력 확보 행동을 첫 단계에 포함할 수 있다.

---

## 9. 결론 문장 (`final_assessment`)

```python
CONCLUSION_TEMPLATES = {
    "EXCELLENT_FIT": "현재 역량 수준으로 {primary_profile_label_ko} 포지션 지원을 강력히 권장합니다.",
    "GOOD_FIT":      "{key_gap_ko} 역량을 보강하면 {primary_profile_label_ko} 포지션에서 높은 경쟁력을 갖출 수 있습니다.",
    "MODERATE_FIT":  "90일 로드맵에 따른 역량 보완 후 {primary_profile_label_ko} 포지션 지원을 권장합니다.",
    "LOW_FIT":       "현재 단계에서는 고유 핵심 역량({unique_score}/65) 확보가 선행되어야 합니다. 6개월 이상의 준비 기간을 권장합니다.",
}
```

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
        내용(점수, 강점 항목, 갭 항목, 추천 행동, UNIQUE/COMMON 구분,
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
