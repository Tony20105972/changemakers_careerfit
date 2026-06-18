# 06 — Scoring Rules

점수 계산은 **완전 결정론적**이다. 동일한 입력 → 동일한 점수. LLM 개입 없음.

> **v3.1 핵심 변경:** §2(Weight 자동 배분)는 **프로필 registry 생성 알고리즘**으로 유지된다.  
> 런타임 scoring은 항상 `primary_profile`의 requirement를 기준으로 수행한다.  
> LOW confidence도 차단하지 않고 fallback profile로 report_json을 생성한다.

---

## 1. 기본 점수 공식 (변경 없음)

```
total_score = unique_total + common_total + core_penalty

unique_total = Σ (weight × match_score × 100)   for requirement where skill_group = UNIQUE
common_total = Σ (weight × match_score × 100)   for requirement where skill_group = COMMON

core_penalty ≤ 0  (§6 참조)
```

- `primary_profile` requirement는 항상 `Σ weight (UNIQUE) = 0.65`, `Σ weight (COMMON) = 0.35`
- `match_score` 범위: 0.0 – 1.0
- 최종 `total_score` 범위: 0 – 100 (음수 방지를 위해 `max(0, ...)` 적용)

---

## 2. Requirement Profile Registry 생성 — Weight 자동 배분 규칙

> v2에서 "Job Family weight 자동 배분"이었던 이 절은, v3.1에서 **"N개 requirement profile을 만드는  
> 1회성 절차"**로 역할이 바뀐다. `13_Development_Roadmap.md` Day 6에서 이미 실행되어  
> `data/job_requirements_*.json` 10개가 생성되었다 — 이 절은 그 산출물의 생성 방법을  
> 문서화한 것이며, **§2.5(primary profile 선택)의 입력을 만드는 절차**다.

### 2.1 입력값 (사람이 정의하는 것 — 좌표축당 1회)

```json
{
  "profile_key": "hr",
  "core_skill_keys": ["recruiting", "training_and_onboarding", "labor_law", "payroll"],
  "common_skill_keys": ["communication", "stakeholder_management", "data_analysis", "documentation", "coordination"],
  "is_core_overrides": {
    "recruiting": true,
    "training_and_onboarding": true,
    "labor_law": true
  }
}
```

### 2.2 자동 배분 알고리즘 (변경 없음)

```python
UNIQUE_TOTAL_WEIGHT = 0.65
COMMON_TOTAL_WEIGHT = 0.35

def allocate_weights(core_skill_keys, common_skill_keys, is_core_overrides, skill_lookup):
    requirements = []
    n_unique = len(core_skill_keys)
    unique_weight = round(UNIQUE_TOTAL_WEIGHT / n_unique, 4)
    for i, key in enumerate(core_skill_keys):
        w = unique_weight
        if i == n_unique - 1:
            w = round(UNIQUE_TOTAL_WEIGHT - unique_weight * (n_unique - 1), 4)
        meta = skill_lookup[key]
        requirements.append(Requirement(
            requirement_key=key, skill_group="UNIQUE",
            label_ko=meta["label_ko"], weight=w,
            is_core=is_core_overrides.get(key, False), description=meta["description"]
        ))

    n_common = len(common_skill_keys)
    common_weight = round(COMMON_TOTAL_WEIGHT / n_common, 4)
    for i, key in enumerate(common_skill_keys):
        w = common_weight
        if i == n_common - 1:
            w = round(COMMON_TOTAL_WEIGHT - common_weight * (n_common - 1), 4)
        meta = skill_lookup[key]
        requirements.append(Requirement(
            requirement_key=key, skill_group="COMMON",
            label_ko=meta["label_ko"], weight=w,
            is_core=False, description=meta["description"]
        ))
    return requirements
```

### 2.3 예시 — HR Profile (Day 6 산출물)

```
recruiting:               0.1625 (UNIQUE)
training_and_onboarding:  0.1625 (UNIQUE)
labor_law:                0.1625 (UNIQUE)
payroll:                  0.1625 (UNIQUE)
communication:            0.07   (COMMON)
stakeholder_management:   0.07   (COMMON)
data_analysis:            0.07   (COMMON)
documentation:            0.07   (COMMON)
coordination:             0.07   (COMMON)
```

### 2.4 검증 규칙 (변경 없음 — profile 생성 시 1회 실행)

```python
def validate_job_family_weights(profile_key, requirements):
    unique_sum = round(sum(r.weight for r in requirements if r.skill_group == "UNIQUE"), 4)
    common_sum = round(sum(r.weight for r in requirements if r.skill_group == "COMMON"), 4)
    assert abs(unique_sum - 0.65) < 0.001, f"[{profile_key}] UNIQUE sum = {unique_sum}"
    assert abs(common_sum - 0.35) < 0.001, f"[{profile_key}] COMMON sum = {common_sum}"
```

---

## 2.5 Primary Profile 선택 (v3.1 핵심)

### 2.5.1 입력

```
user_vector: {skill_key: confidence_total}
    08_EVIDENCE_RULES.md로 career_histories + target_priority_text에서 추출

profile_pool: N개 requirement profile (job_requirement_profiles, status='ACTIVE')
    각 profile_i = {requirement_key: weight}  (§2에서 생성됨, 합계 1.0)
```

### 2.5.2 프로필별 매칭 신호 계산 (순수 산술)

```python
def score_profile_signal(user_vector: dict[str, float], requirements: list[Requirement]) -> float:
    return round(sum(user_vector.get(r.requirement_key, 0.0) for r in requirements), 4)
```

`score_profile_signal`은 해당 프로필 requirement에 매칭된 confidence_total의 합이다.  
동점이면 `target_priority_text`에서 직접 언급된 profile hint를 우선하고, 그래도 동점이면 registry 순서를 사용한다.

### 2.5.3 선택 알고리즘

```python
DEFAULT_FALLBACK_PROFILE = "operations"  # V1에는 business profile이 없으므로 operations 사용

def select_primary_profile(user_vector, target_priority_text, profile_pool) -> tuple[str, list[str]]:
    hinted = detect_profile_hint(target_priority_text, profile_pool)
    if hinted:
        primary = hinted
    else:
        scores = {key: score_profile_signal(user_vector, reqs) for key, reqs in profile_pool.items()}
        primary = max(scores, key=lambda k: (scores[k], -profile_registry_order(k)))
        if scores[primary] == 0:
            primary = DEFAULT_FALLBACK_PROFILE

    secondary = select_secondary_profiles(user_vector, profile_pool, exclude=primary)
    return primary, secondary
```

선택 우선순위:
1. `target_priority_text`에서 가장 명확한 직무/산업 표현
2. `career_histories`에서 가장 많이 매칭된 skill의 profile
3. 그래도 부족하면 `operations`를 `default_fallback_profile`로 사용

`secondary_profiles`는 선택 필드이며, 사용자-facing 핵심 판단에는 사용하지 않는다.

### 2.5.4 선택된 requirement

```python
def select_requirements(primary_profile: str, profile_pool: dict[str, list[Requirement]]) -> list[Requirement]:
    requirements = profile_pool[primary_profile]
    validate_profile_weights(primary_profile, requirements)
    return requirements
```

`selected_requirements`의 UNIQUE 합계는 0.65, COMMON 합계는 0.35다.  
점수, 갭, 추천은 이 requirement 집합만 기준으로 계산한다.

---

## 2.6 Confidence Level — evidence_count 기준

```python
HIGH_EVIDENCE_COUNT = 8
MEDIUM_EVIDENCE_COUNT = 5

def determine_confidence_level(evidence_count: int) -> str:
    if evidence_count >= HIGH_EVIDENCE_COUNT:
        return "HIGH"
    if evidence_count >= MEDIUM_EVIDENCE_COUNT:
        return "MEDIUM"
    return "LOW"
```

LOW도 report_json 생성, scoring, PDF 생성 대상이다. LOW에서는 `warning_message`가 필수이며  
"입력 정보가 부족하여 일부 결과는 추정에 기반합니다" 문구를 포함해야 한다.

---

## 3. matchLevel 정의 (변경 없음)

| matchLevel | match_score | 판단 기준 |
|------------|-------------|----------|
| `FULL` | 1.00 | 해당 역량을 직접 수행한 명확한 Evidence가 2개 이상, 또는 1개 + 높은 confidence_total |
| `STRONG` | 0.75 | 직접 수행 Evidence 1개 (EXPLICIT) |
| `PARTIAL` | 0.50 | 간접적 수행 또는 보조적 역할 Evidence 존재 |
| `WEAK` | 0.25 | 관련 키워드 언급, 직접 수행 증거 없음 |
| `NONE` | 0.00 | Evidence 없음 |

---

## 4. matchLevel 결정 알고리즘 (변경 없음)

```python
FULL_CONFIDENCE_THRESHOLD = 1.8
PARTIAL_CONFIDENCE_THRESHOLD = 0.7

def determine_match_level(evidences_for_skill: list[Evidence]) -> tuple[MatchLevel, float]:
    if not evidences_for_skill:
        return MatchLevel.NONE, 0.0

    explicit = [e for e in evidences_for_skill if e.evidence_type == "EXPLICIT"]
    inferred = [e for e in evidences_for_skill if e.evidence_type == "INFERRED"]
    achieved = [e for e in evidences_for_skill if e.evidence_type == "ACHIEVED"]

    confidence_total = round(sum(e.confidence_score for e in evidences_for_skill), 2)

    if len(explicit) >= 2:
        return MatchLevel.FULL, confidence_total
    if len(explicit) >= 1 and confidence_total >= FULL_CONFIDENCE_THRESHOLD:
        return MatchLevel.FULL, confidence_total
    if len(explicit) >= 1:
        return MatchLevel.STRONG, confidence_total
    if len(inferred) >= 2:
        return MatchLevel.PARTIAL, confidence_total
    if len(inferred) >= 1 and len(achieved) >= 1:
        return MatchLevel.PARTIAL, confidence_total
    if len(inferred) >= 1 and confidence_total >= PARTIAL_CONFIDENCE_THRESHOLD:
        return MatchLevel.PARTIAL, confidence_total
    if len(inferred) >= 1 or len(achieved) >= 1:
        return MatchLevel.WEAK, confidence_total
    return MatchLevel.NONE, confidence_total


MATCH_SCORE = {
    "FULL":    1.00,
    "STRONG":  0.75,
    "PARTIAL": 0.50,
    "WEAK":    0.25,
    "NONE":    0.00,
}
```

---

## 5. 점수 계산 예시 (v3.1 — primary_profile requirements 기준)

`primary_profile=hr`의 requirement에 사용자 Evidence를 적용한 예시:

| requirement_key | skill_group | weight | match_level | match_score | weighted_score |
|-----------------|-------------|------------------|-------------|-------------|-----------------|
| recruiting | UNIQUE | 0.1625 | FULL | 1.00 | 16.25 |
| training_and_onboarding | UNIQUE | 0.1625 | FULL | 1.00 | 16.25 |
| payroll | UNIQUE | 0.1625 | FULL | 1.00 | 16.25 |
| labor_law | UNIQUE | 0.1625 | NONE | 0.00 | 0.0 |
| (COMMON 5개, 별도 계산) | COMMON | Σ=0.35 | ... | ... | ... |

```
unique_total (raw) = 16.25×3 + 0 = 48.75
core_penalty: labor_law는 is_core=true이고 match_level=NONE → -5.0

unique_total (final) = 48.75 - 5.0 = 43.75 ≈ 43.8
```

> COMMON 부분도 동일하게 primary_profile의 COMMON requirement 기준으로 계산되며, `total = unique_total + common_total`이다.

---

## 6. Core Penalty 규칙

```python
CORE_PENALTY_NONE = -5.0
CORE_PENALTY_WEAK = -2.5

def apply_core_penalty(matches: list[RequirementMatch], requirements: list[Requirement]) -> float:
    """
    requirements는 primary_profile의 selected_requirements.
    is_core는 해당 profile registry의 값을 그대로 사용한다.
    """
    penalty = 0.0
    for req in requirements:
        if req.is_core and req.skill_group == "UNIQUE":
            match = next(m for m in matches if m.requirement_key == req.requirement_key)
            if match.match_level == MatchLevel.NONE:
                penalty += CORE_PENALTY_NONE
            elif match.match_level == MatchLevel.WEAK:
                penalty += CORE_PENALTY_WEAK
    return penalty


def calculate_final_scores(unique_raw: float, common_total: float, penalty: float) -> dict:
    unique_final = max(0.0, round(unique_raw + penalty, 1))
    total = round(unique_final + common_total, 1)
    return {
        "unique_total": unique_final,
        "common_total": round(common_total, 1),
        "core_penalty": round(penalty, 1),
        "total": min(100.0, total),
    }
```

---

## 7. 등급 레이블 (변경 없음)

| 점수 범위 | fit_level | 한국어 레이블 |
|-----------|-----------|--------------|
| 90–100 | EXCELLENT_FIT | 최우수 |
| 75–89 | GOOD_FIT | 우수 |
| 55–74 | MODERATE_FIT | 보통 |
| 0–54 | LOW_FIT | 미흡 |

---

## 8. Gap Severity 분류 (변경 없음, selected_requirements 기준으로 적용)

```python
def classify_gap_severity(req: Requirement, match: RequirementMatch) -> GapSeverity:
    if req.is_core and match.match_level in (MatchLevel.NONE, MatchLevel.WEAK):
        return GapSeverity.CRITICAL
    if req.weight >= 0.10 and match.match_level in (
        MatchLevel.NONE, MatchLevel.WEAK, MatchLevel.PARTIAL
    ):
        return GapSeverity.MAJOR
    if match.match_level in (MatchLevel.NONE, MatchLevel.WEAK, MatchLevel.PARTIAL):
        return GapSeverity.MINOR
    return None
```

```python
def assign_priority_order(gaps: list[Gap]) -> list[Gap]:
    severity_rank = {"CRITICAL": 0, "MAJOR": 1, "MINOR": 2}
    sorted_gaps = sorted(gaps, key=lambda g: (severity_rank[g.gap_severity], -g.weight))
    for i, gap in enumerate(sorted_gaps, start=1):
        gap.priority_order = i
    return sorted_gaps
```

---

## 9. Strength 선정 규칙 (변경 없음, selected_requirements 기준)

```python
def select_strengths(matches: list[RequirementMatch], requirements: list[Requirement]) -> list[Strength]:
    candidates = [
        (req, m) for req, m in zip(requirements, matches)
        if m.match_level in (MatchLevel.FULL, MatchLevel.STRONG)
    ]

    def sort_key(item):
        req, m = item
        weighted_score = req.weight * MATCH_SCORE[m.match_level] * 100
        unique_priority = 0 if req.skill_group == "UNIQUE" else 1
        return (-weighted_score, unique_priority)

    candidates.sort(key=sort_key)
    return candidates[:3]
```

---

## 10. 불변 규칙 (Invariants) — v3 갱신

```
1. 0 <= total_score <= 100
2. total_score == round(unique_total + common_total, 1)
3. 0 <= unique_total <= 65
4. 0 <= common_total <= 35
5. core_penalty <= 0
6. Σ weight (skill_group=UNIQUE, selected_requirements) == 0.65  (±0.001)
7. Σ weight (skill_group=COMMON, selected_requirements) == 0.35  (±0.001)
8. 동일 입력 → 동일 출력 (결정론적, 3회 실행 비교)
9. confidence_score < 0.5인 Evidence는 매칭 계산에 포함하지 않음
10. original_text는 절대 수정되지 않음
11. primary_profile은 항상 유효한 profile_pool key
12. confidence_level은 HIGH | MEDIUM | LOW만 허용, LOW도 report_json 생성 대상
```

---

## 11. 알려진 문제점 (§ Limitations)

| 문제 | 영향 | 비고 |
|------|------|------|
| fallback으로 `operations`가 선택되는 LOW 입력 | 사용자 의도와 다를 수 있음 | `warning_message`와 추가 입력 권장 문구를 필수 표시 |
| target_priority_text의 직무 표현이 모호함 | primary_profile 선택이 career evidence에 더 의존 | 선택 이유를 `primary_profile_summary`에 짧게 설명 |
| secondary_profiles가 사용자에게 과해 보일 수 있음 | 핵심 판단 혼란 | V1에서는 선택적 보조 정보로만 렌더링 |
