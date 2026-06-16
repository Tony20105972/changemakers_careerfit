# 06 — Scoring Rules

점수 계산은 **완전 결정론적**이다. 동일한 입력 → 동일한 점수. LLM 개입 없음.

> **v3 핵심 변경:** §2(Weight 자동 배분)는 **좌표축(profile) 생성 알고리즘**으로 역할이  
> 재정의된다. §2.5(블렌딩), §2.6(confidence_level)이 신규 추가되어, "사용자 입력 →  
> N개 좌표축과의 유사도 → 맞춤 weight"의 전체 파이프라인을 정의한다.

---

## 1. 기본 점수 공식 (변경 없음)

```
total_score = unique_total + common_total + core_penalty

unique_total = Σ (weight × match_score × 100)   for requirement where skill_group = UNIQUE
common_total = Σ (weight × match_score × 100)   for requirement where skill_group = COMMON

core_penalty ≤ 0  (§6 참조)
```

- **블렌딩 후에도** `Σ weight (UNIQUE) = 0.65`, `Σ weight (COMMON) = 0.35`
- `match_score` 범위: 0.0 – 1.0
- 최종 `total_score` 범위: 0 – 100 (음수 방지를 위해 `max(0, ...)` 적용)

---

## 2. 좌표축(Profile) 생성 — Weight 자동 배분 규칙 (역할 재정의)

> v2에서 "Job Family weight 자동 배분"이었던 이 절은, v3에서 **"N개 좌표축을 만드는  
> 1회성 절차"**로 역할이 바뀐다. `13_Development_Roadmap.md` Day 6에서 이미 실행되어  
> `data/job_requirements_*.json` 10개가 생성되었다 — 이 절은 그 산출물의 생성 방법을  
> 문서화한 것이며, **§2.5(블렌딩)의 입력(기저 벡터)을 만드는 절차**다.

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

### 2.3 예시 — HR 좌표축 (Day 6 산출물)

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

### 2.4 검증 규칙 (변경 없음 — 좌표축 생성 시 1회 실행)

```python
def validate_job_family_weights(profile_key, requirements):
    unique_sum = round(sum(r.weight for r in requirements if r.skill_group == "UNIQUE"), 4)
    common_sum = round(sum(r.weight for r in requirements if r.skill_group == "COMMON"), 4)
    assert abs(unique_sum - 0.65) < 0.001, f"[{profile_key}] UNIQUE sum = {unique_sum}"
    assert abs(common_sum - 0.35) < 0.001, f"[{profile_key}] COMMON sum = {common_sum}"
```

---

## 2.5 프로필 블렌딩 (v3 핵심 신규)

### 2.5.1 입력

```
user_vector: {skill_key: confidence_total}
    08_EVIDENCE_RULES.md로 career_histories + target_priority_text에서 추출

profile_pool: N개 좌표축 (job_requirement_profiles, status='ACTIVE')
    각 profile_i = {requirement_key: weight}  (§2에서 생성됨, 합계 1.0)
```

### 2.5.2 코사인 유사도 (순수 산술)

```python
def cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    keys = set(vec_a) | set(vec_b)
    dot = sum(vec_a.get(k, 0) * vec_b.get(k, 0) for k in keys)
    norm_a = sum(v ** 2 for v in vec_a.values()) ** 0.5
    norm_b = sum(v ** 2 for v in vec_b.values()) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
```

> `vec_a`(user_vector)는 confidence_total(0~수, 보통 0~2 범위) 값이고  
> `vec_b`(profile_i)는 weight(0~0.65 범위) 값이다. 단위가 달라도 코사인 유사도는  
> **방향(비율 패턴)만 비교**하므로 스케일 차이는 영향 없다.

### 2.5.3 블렌딩 가중치 산출

```python
def compute_blend_weights(user_vector: dict, profile_pool: dict[str, dict]) -> dict[str, float]:
    """
    Returns: {profile_key: blend_ratio}, sum = 1.0
    """
    similarities = {
        key: cosine_similarity(user_vector, pvec)
        for key, pvec in profile_pool.items()
    }

    # 음수/0 유사도는 0으로 clamp, 거듭제곱으로 "가장 가까운 것"의 영향력을 키움
    # (단순 정규화는 모든 프로필을 비슷하게 섞어 의미 없는 블렌드가 될 수 있음)
    POWER = 2
    weights = {k: max(0.0, s) ** POWER for k, s in similarities.items()}
    total = sum(weights.values())

    if total == 0:
        # 모든 유사도가 0 (user_vector가 거의 zero vector)
        # → §2.6 confidence_level=LOW로 처리되며, 이 경우 blend는 호출되지 않음
        #   (04_PAYLOAD_CONTRACT.md 가드레일에서 사전 차단)
        raise ValueError("user_vector가 모든 프로필과 유사도 0 — 가드레일에서 차단되어야 함")

    return {k: round(w / total, 4) for k, w in weights.items()}
```

### 2.5.4 가중 선형결합 + 65/35 재정규화

```python
def blend_requirements(user_vector: dict, profile_pool: dict[str, list[Requirement]]) -> tuple[dict, list[Requirement]]:
    """
    Returns: (profile_blend, blended_requirements)
    """
    # 1. 각 프로필을 {requirement_key: weight} 벡터로 변환
    profile_vectors = {
        key: {r.requirement_key: r.weight for r in reqs}
        for key, reqs in profile_pool.items()
    }

    # 2. 블렌딩 비율
    profile_blend = compute_blend_weights(user_vector, profile_vectors)

    # 3. 79차원 공간에서 가중 선형결합
    blended_vector: dict[str, float] = {}
    skill_group_lookup: dict[str, str] = {}
    source_profiles: dict[str, set[str]] = {}

    for profile_key, pvec in profile_vectors.items():
        ratio = profile_blend[profile_key]
        if ratio == 0:
            continue
        for req in profile_pool[profile_key]:
            k = req.requirement_key
            blended_vector[k] = blended_vector.get(k, 0) + ratio * req.weight
            skill_group_lookup[k] = req.skill_group  # 충돌 시 마지막 값 (실무상 거의 일치)
            source_profiles.setdefault(k, set()).add(profile_key)

    # 4. UNIQUE/COMMON 그룹별 65/35 재정규화
    blended_requirements = renormalize_to_65_35(blended_vector, skill_group_lookup, source_profiles)

    return profile_blend, blended_requirements


def renormalize_to_65_35(blended: dict[str, float], skill_groups: dict[str, str],
                          source_profiles: dict[str, set[str]]) -> list[Requirement]:
    unique_items = {k: v for k, v in blended.items() if skill_groups[k] == "UNIQUE"}
    common_items = {k: v for k, v in blended.items() if skill_groups[k] == "COMMON"}

    unique_sum = sum(unique_items.values())
    common_sum = sum(common_items.values())

    requirements = []
    for k, v in unique_items.items():
        requirements.append(Requirement(
            requirement_key=k, skill_group="UNIQUE",
            weight=round(0.65 * v / unique_sum, 4),
            source_profiles=sorted(source_profiles[k]),
            # label_ko, is_core, description은 skill_taxonomy.json + 첫 source_profile 기준 lookup
        ))
    for k, v in common_items.items():
        requirements.append(Requirement(
            requirement_key=k, skill_group="COMMON",
            weight=round(0.35 * v / common_sum, 4),
            source_profiles=sorted(source_profiles[k]),
        ))

    # 라운딩 오차 보정 — 최대 weight 항목에서 흡수
    _fix_rounding(requirements, "UNIQUE", 0.65)
    _fix_rounding(requirements, "COMMON", 0.35)

    validate_blended_weights(requirements)
    return requirements


def _fix_rounding(requirements: list[Requirement], group: str, target: float) -> None:
    items = [r for r in requirements if r.skill_group == group]
    diff = round(target - sum(r.weight for r in items), 4)
    if diff != 0 and items:
        max_item = max(items, key=lambda r: r.weight)
        max_item.weight = round(max_item.weight + diff, 4)


def validate_blended_weights(requirements: list[Requirement]) -> None:
    """06_SCORING_RULES.md §10 불변규칙 6, 7 — 블렌딩 후에도 적용"""
    unique_sum = round(sum(r.weight for r in requirements if r.skill_group == "UNIQUE"), 4)
    common_sum = round(sum(r.weight for r in requirements if r.skill_group == "COMMON"), 4)
    assert abs(unique_sum - 0.65) < 0.001, f"blended UNIQUE sum = {unique_sum}"
    assert abs(common_sum - 0.35) < 0.001, f"blended COMMON sum = {common_sum}"
```

### 2.5.5 예시 — "HR 81% + Operations 19%" 블렌딩

```
profile_blend = {"hr": 0.81, "operations": 0.19}

HR 좌표축 (UNIQUE):
  recruiting: 0.1625, training_and_onboarding: 0.1625,
  labor_law: 0.1625, payroll: 0.1625

Operations 좌표축 (UNIQUE):
  process_improvement: 0.1625, vendor_management: 0.1625,
  operations_management: 0.1625, logistics: 0.1625

가중 선형결합 (UNIQUE 항목 일부):
  recruiting             = 0.81 × 0.1625 = 0.1316
  training_and_onboarding= 0.81 × 0.1625 = 0.1316
  labor_law              = 0.81 × 0.1625 = 0.1316
  payroll                = 0.81 × 0.1625 = 0.1316
  process_improvement    = 0.19 × 0.1625 = 0.0309
  vendor_management       = 0.19 × 0.1625 = 0.0309
  operations_management   = 0.19 × 0.1625 = 0.0309
  logistics                = 0.19 × 0.1625 = 0.0309

unique_sum (블렌딩 직후) = 0.1316×4 + 0.0309×4 = 0.65 (정확히 맞아떨어짐 — 둘 다 4개 UNIQUE이고
                                                         0.1625로 동일했기 때문)

→ 이미 0.65이므로 재정규화 비율 = 1.0
→ blended_requirements (UNIQUE 8개):
   recruiting: 0.1316, training_and_onboarding: 0.1316,
   labor_law: 0.1316, payroll: 0.1316,
   process_improvement: 0.0309, vendor_management: 0.0309,
   operations_management: 0.0309, logistics: 0.0309
```

> 이 예시는 "양쪽 다 UNIQUE 4개씩, weight가 동일(0.1625)"이라는 우연으로 합이 정확히  
> 0.65가 되었다. 일반적으로는 재정규화(`_fix_rounding`)가 작동해 합을 0.65로 맞춘다.  
> COMMON도 동일한 절차로 8~10개(중복 제거 시 5~9개)가 생성되며 합 0.35로 정규화된다.

---

## 2.6 Confidence Level — 입력 가드레일 기준

```python
MIN_TOTAL_CONFIDENCE_FOR_ANALYSIS = 2.0   # 이 미만이면 04_PAYLOAD_CONTRACT.md 가드레일에서 경고
HIGH_CONFIDENCE_THRESHOLD = 6.0
MEDIUM_CONFIDENCE_THRESHOLD = 3.0

def determine_confidence_level(user_vector: dict[str, float]) -> str:
    total = sum(user_vector.values())
    if total >= HIGH_CONFIDENCE_THRESHOLD:
        return "HIGH"
    elif total >= MEDIUM_CONFIDENCE_THRESHOLD:
        return "MEDIUM"
    elif total >= MIN_TOTAL_CONFIDENCE_FOR_ANALYSIS:
        return "LOW"
    else:
        return "BLOCKED"  # 04_PAYLOAD_CONTRACT.md 가드레일: 사용자에게 보완 안내
```

> 임계값(2.0 / 3.0 / 6.0)은 V1 초기값이다. `meta.confidence_level`의 분포가 누적되면  
> (`03_ERD.md` §6 인덱스로 분석 가능) 실제 사용자 입력 분포에 맞춰 보정한다.

---

## 2.7 단일/혼합 정체성 분기 (blend_display_mode)

```python
SINGLE_IDENTITY_THRESHOLD = 0.7

def determine_blend_display_mode(profile_blend: dict[str, float]) -> str:
    max_ratio = max(profile_blend.values())
    return "SINGLE" if max_ratio >= SINGLE_IDENTITY_THRESHOLD else "MIXED"
```

`05_REPORT_SCHEMA.md` §2 `summary.blend_display_mode`, `09_TEXT_TEMPLATE_RULES.md` §2의  
`blend_description` 템플릿 선택에 사용된다.

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

## 5. 점수 계산 예시 (v3 — 블렌딩된 requirements 기준)

`§2.5.5`의 블렌딩 결과(HR 81% + Operations 19%, UNIQUE 8개)에 사용자 Evidence를 적용한 예시:

| requirement_key | skill_group | weight (블렌딩) | match_level | match_score | weighted_score |
|-----------------|-------------|------------------|-------------|-------------|-----------------|
| recruiting | UNIQUE | 0.1316 | FULL | 1.00 | 13.16 |
| training_and_onboarding | UNIQUE | 0.1316 | FULL | 1.00 | 13.16 |
| payroll | UNIQUE | 0.1316 | FULL | 1.00 | 13.16 |
| labor_law | UNIQUE | 0.1316 | NONE | 0.00 | 0.0 |
| process_improvement | UNIQUE | 0.0309 | PARTIAL | 0.50 | 1.545 |
| vendor_management | UNIQUE | 0.0309 | NONE | 0.00 | 0.0 |
| operations_management | UNIQUE | 0.0309 | WEAK | 0.25 | 0.7725 |
| logistics | UNIQUE | 0.0309 | NONE | 0.00 | 0.0 |
| (COMMON 5~9개, 별도 계산) | COMMON | Σ=0.35 | ... | ... | ... |

```
unique_total (raw) = 13.16×3 + 0 + 1.545 + 0 + 0.7725 + 0 = 41.8575
core_penalty: labor_law는 is_core=true(HR 좌표축에서 유래)이고 match_level=NONE → -5.0
              (06_SCORING_RULES.md §6 — is_core는 source_profiles 중 하나라도 true면 적용)

unique_total (final) = 41.8575 - 5.0 = 36.8575 ≈ 36.86
```

> COMMON 부분은 §2.5.5에서 생략되었으나 동일한 절차로 계산되며, `total = unique_total + common_total`이다.

---

## 6. Core Penalty 규칙 (v3: source_profiles 고려)

```python
CORE_PENALTY_NONE = -5.0
CORE_PENALTY_WEAK = -2.5

def apply_core_penalty(matches: list[RequirementMatch], requirements: list[Requirement]) -> float:
    """
    v3: requirements는 blended_requirements (renormalize_to_65_35 결과).
    is_core는 §2.5.4에서 원본 좌표축의 is_core_overrides를 따라가며,
    여러 source_profiles 중 하나라도 is_core=true였다면 블렌딩 결과에서도 is_core=true로 유지한다.
    (06_SCORING_RULES.md §2.5.4 renormalize_to_65_35 — is_core 전파 규칙)
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

## 8. Gap Severity 분류 (변경 없음, blended_requirements 기준으로 적용)

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

## 9. Strength 선정 규칙 (변경 없음, blended_requirements 기준)

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
6. Σ weight (skill_group=UNIQUE, blended_requirements) == 0.65  (±0.001)   [v3: 블렌딩 후에도 적용]
7. Σ weight (skill_group=COMMON, blended_requirements) == 0.35  (±0.001)   [v3: 블렌딩 후에도 적용]
8. 동일 입력 → 동일 출력 (결정론적, 3회 실행 비교) — 블렌딩 포함
9. confidence_score < 0.5인 Evidence는 매칭 계산에 포함하지 않음
10. original_text는 절대 수정되지 않음
11. (v3 신규) Σ profile_blend.values() == 1.0  (±0.001)
12. (v3 신규) confidence_level == "BLOCKED"인 입력은 blend_requirements()가 호출되지 않음
              (04_PAYLOAD_CONTRACT.md 가드레일에서 사전 차단)
```

---

## 11. 알려진 문제점 (§ Limitations)

| 문제 | 영향 | 비고 |
|------|------|------|
| `compute_blend_weights`의 `POWER=2`는 임의로 선택된 값 | 블렌딩 비율의 "쏠림 정도"가 이 값에 민감 (POWER가 클수록 1등 프로필에 더 쏠림) | V1은 POWER=2로 시작, `profile_blend` 분포 데이터를 보고 조정 — `01_PRD.md` §4.3 |
| `renormalize_to_65_35`에서 `skill_groups[k]`가 프로필 간 충돌 시 "마지막 값" 사용 | 동일 requirement_key가 한 프로필에서 UNIQUE, 다른 프로필에서 COMMON으로 정의되어 있으면 비결정적일 수 있음 | V1의 N=10 데이터(Day 6 산출물)에서는 충돌 사례 없음(확인 필요). N 확장 시 충돌 검증 스크립트 필요 |
| `is_core` 전파 규칙(§6 — "하나라도 true면 true") | 블렌딩 비율이 낮은(예: 5%) 프로필에서 유래한 is_core가 전체 결과의 core_penalty를 좌우할 수 있음 | 의도된 보수적 설계(누락 방지)지만, MIXED 모드에서 penalty가 사용자 기대보다 크게 느껴질 가능성 |
| §2.5.3 `total == 0` 예외가 발생하면 `ValueError` | 가드레일(§2.6 BLOCKED)이 정상 동작한다는 전제 하에 "발생하지 않아야 하는" 코드 경로 | 방어적 코드이지만, 가드레일 우회 경로(예: API 직접 호출)에서는 500 에러로 노출될 수 있음 — `04_PAYLOAD_CONTRACT.md` `ENGINE_ERROR` 처리 확인 필요 |
| 라운딩 보정(`_fix_rounding`)이 항상 "최대 weight 항목"에 흡수 | 동일한 두 항목이 최댓값으로 동률일 때 처리 순서가 dict 순서에 의존 | Python 3.7+ dict는 입력 순서 보존이므로 결정론은 유지되나, "왜 이 항목이 보정됐는지"는 직관적이지 않을 수 있음 |