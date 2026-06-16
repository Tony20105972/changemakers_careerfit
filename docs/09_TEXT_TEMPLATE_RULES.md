# 09 — Text Template Rules

결정론적 텍스트 생성 규칙.  
LLM은 이 템플릿 결과를 **윤색만** 가능. 내용 변경 불가. (`00_PROJECT_VISION.md` §4 LLM Optional)

> **v3 변경:** `{job_family_ko}` 단일 라벨 변수 → `{blend_description}` 또는  
> `{top_profile_ko}`(단일 정체성일 때)로 대체.  
> §2(Blend Description), §3(Score Split) 신규 추가.

---

## 1. 점수별 요약 문장 (`summary.one_line`)

```python
SUMMARY_TEMPLATES = {
    "EXCELLENT_FIT": "{blend_display}에서 매우 높은 적합도({score}점)를 보입니다. 핵심 역량과 범용 역량 모두에서 검증된 경험이 확인됩니다.",
    "GOOD_FIT":      "{blend_display}에서 높은 적합도({score}점)를 보입니다. {top_gap_label_ko} 영역의 보강을 통해 경쟁력을 더욱 높일 수 있습니다.",
    "MODERATE_FIT":  "{blend_display}에서 기본적인 적합도({score}점)를 보입니다. {top_gap_label_ko} 등 주요 갭을 체계적으로 보완하면 목표 달성이 가능합니다.",
    "LOW_FIT":       "{blend_display}에서의 적합도({score}점)는 현재 낮은 수준입니다. 핵심 역량({unique_score}/65점) 확보를 위한 전략적 준비가 필요합니다.",
}

def build_blend_display(profile_blend: dict, blend_display_mode: str, profile_label_lookup: dict) -> str:
    """
    blend_display_mode에 따라 단일/혼합 표현 선택.
    profile_label_lookup: {profile_key: label_ko} — data/job_requirement_profiles에서 조회
    """
    sorted_blend = sorted(profile_blend.items(), key=lambda x: -x[1])
    if blend_display_mode == "SINGLE":
        top_key, top_ratio = sorted_blend[0]
        return f"'{profile_label_lookup[top_key]}' 직무"
    else:  # MIXED
        top2 = sorted_blend[:2]
        parts = [f"'{profile_label_lookup[k]}' {round(r*100)}%" for k, r in top2]
        return f"{' + '.join(parts)} 혼합 프로필"
```

| 변수 | 출처 |
|------|------|
| `{blend_display}` | `build_blend_display()` 결과 |
| `{score}` | `summary.total_score` |
| `{top_gap_label_ko}` | `gaps[0].label_ko` (priority_order=1) |
| `{unique_score}` | `summary.unique_score` |

---

## 2. Blend Description 템플릿 (v3 신규 — `summary.blend_description`)

```python
BLEND_DESCRIPTION_TEMPLATES = {
    "SINGLE": "당신의 경험은 '{top_profile_ko}' 직무 특성과 강하게 일치합니다 (유사도 {top_pct}%).",
    "MIXED_2": "당신의 경험은 '{p1_ko}' 특성 {p1_pct}%와 '{p2_ko}' 특성 {p2_pct}%가 혼합된 프로필로 분석되었습니다.",
    "MIXED_3": "당신의 경험은 '{p1_ko}' {p1_pct}%, '{p2_ko}' {p2_pct}%, '{p3_ko}' {p3_pct}%의 특성이 혼합된 프로필로 분석되었습니다.",
    "MIXED_MANY": "당신의 경험은 여러 직무 특성이 복합적으로 혼합된 프로필로 분석되었습니다 (최상위: '{top_profile_ko}' {top_pct}%).",
}

SINGLE_IDENTITY_THRESHOLD = 0.7  # 06_SCORING_RULES.md §2.7과 동기화

def build_blend_description(profile_blend: dict, blend_display_mode: str,
                              profile_label_lookup: dict) -> str:
    sorted_blend = sorted(profile_blend.items(), key=lambda x: -x[1])
    # 표시 대상: ratio >= 0.05 이상인 것만 (1% 미만은 너무 미미해서 혼란을 줌)
    significant = [(k, v) for k, v in sorted_blend if v >= 0.05]

    if blend_display_mode == "SINGLE" or len(significant) == 1:
        k, v = significant[0]
        return BLEND_DESCRIPTION_TEMPLATES["SINGLE"].format(
            top_profile_ko=profile_label_lookup[k], top_pct=round(v * 100)
        )
    elif len(significant) == 2:
        (k1, v1), (k2, v2) = significant[:2]
        return BLEND_DESCRIPTION_TEMPLATES["MIXED_2"].format(
            p1_ko=profile_label_lookup[k1], p1_pct=round(v1 * 100),
            p2_ko=profile_label_lookup[k2], p2_pct=round(v2 * 100)
        )
    elif len(significant) == 3:
        (k1, v1), (k2, v2), (k3, v3) = significant[:3]
        return BLEND_DESCRIPTION_TEMPLATES["MIXED_3"].format(
            p1_ko=profile_label_lookup[k1], p1_pct=round(v1 * 100),
            p2_ko=profile_label_lookup[k2], p2_pct=round(v2 * 100),
            p3_ko=profile_label_lookup[k3], p3_pct=round(v3 * 100)
        )
    else:
        k_top, v_top = significant[0]
        return BLEND_DESCRIPTION_TEMPLATES["MIXED_MANY"].format(
            top_profile_ko=profile_label_lookup[k_top], top_pct=round(v_top * 100)
        )
```

---

## 3. UNIQUE/COMMON 분리 요약 (`summary` 보조 — v3 유지)

```python
SCORE_SPLIT_TEMPLATES = {
    "unique_high_common_high":  "{blend_display} 직무 고유 역량({unique_score}/65점)과 범용 역량({common_score}/35점) 모두 우수한 수준입니다.",
    "unique_high_common_low":   "{blend_display} 직무 고유 역량({unique_score}/65점)은 우수하나, 협업·문서화 등 범용 역량({common_score}/35점)의 보완이 권장됩니다.",
    "unique_low_common_high":   "범용 역량({common_score}/35점)은 우수하나, {blend_display} 직무 고유 역량({unique_score}/65점)의 확보가 우선적으로 필요합니다.",
    "unique_low_common_low":    "{blend_display} 직무 고유 역량과 범용 역량 모두({unique_score}/65점, {common_score}/35점) 보완이 필요한 단계입니다.",
}

def select_split_template(unique_score: float, common_score: float) -> str:
    u = "high" if (unique_score / 65) >= 0.7 else "low"
    c = "high" if (common_score / 35) >= 0.7 else "low"
    return SCORE_SPLIT_TEMPLATES[f"unique_{u}_common_{c}"]
```

---

## 4. 강점 문장 (`strengths[].headline`, `.detail`)

```python
STRENGTH_HEADLINE_TEMPLATES = {
    ("UNIQUE", "FULL"):   "{label_ko}: {blend_display} 핵심 역량을 직접 수행한 검증된 경험",
    ("UNIQUE", "STRONG"): "{label_ko}: {blend_display} 핵심 역량에서 실무 경험 확인",
    ("COMMON", "FULL"):   "{label_ko}: 직무 전반에 적용 가능한 범용 역량을 입증한 경험",
    ("COMMON", "STRONG"): "{label_ko}: 범용 역량 영역에서 실무 경험 확인",
}

STRENGTH_DETAIL_TEMPLATE = (
    "{evidence_summary}. "
    "{achievement_clause}"
    "{priority_clause}"
)
# evidence_summary: original_text를 자연어로 재구성 (사실관계 변경 불가)
# achievement_clause: ACHIEVED 타입 evidence가 있으면 "이를 통해 {metric}이라는 구체적 성과를 달성했습니다." / 없으면 빈 문자열
# priority_clause: source="target_priority_text" evidence가 있으면 "이 역량은 목표 직무에서도 중요하게 언급되었습니다." / 없으면 빈 문자열 (v3 신규)
```

---

## 5. Gap 문장 (`gaps[].headline`, `.detail`)

```python
GAP_HEADLINE_TEMPLATES = {
    ("UNIQUE", "CRITICAL"): "{label_ko} 역량 확보가 시급합니다",
    ("UNIQUE", "MAJOR"):    "{label_ko} 역량 보강이 필요합니다",
    ("UNIQUE", "MINOR"):    "{label_ko} 역량을 보완하면 좋습니다",
    ("COMMON", "MAJOR"):    "{label_ko} 등 범용 역량 보강이 권장됩니다",
    ("COMMON", "MINOR"):    "{label_ko} 영역을 보완하면 좋습니다",
}

GAP_DETAIL_TEMPLATES = {
    "CRITICAL": "{label_ko}은(는) {blend_display} 직무의 핵심 요건이나, 현재 경력에서 관련 경험이 확인되지 않습니다. 즉각적인 역량 확보가 필요합니다.",
    "MAJOR":    "{label_ko} 경험이 부족하여 직무 수행에 어려움이 예상됩니다. 우선순위를 두고 보완을 시작하세요.",
    "MINOR":    "{label_ko} 역량이 다소 부족하나, 단기 학습으로 보완 가능한 수준입니다.",
}

# COMMON + CRITICAL 조합은 발생하지 않음
# (is_core_overrides는 06_SCORING_RULES.md §2.1에 따라 UNIQUE 스킬에만 적용됨)
```

---

## 6. 추천 문장 (`recommendations`)

```python
RECOMMENDATION_TEMPLATES = {
    "short_term": "{gap_label_ko} 역량 강화를 위해 {timeframe} 내 {action}을(를) 권장합니다.",
    "mid_term_high_score": "현재 적합도 수준({score}점, 고유 역량 {unique_score}/65)에서 {blend_display} 포지션 지원이 가능합니다. {action}을(를) 통해 경쟁력을 높이세요.",
    "mid_term_low_score":  "현재 적합도 수준({score}점)에서는 핵심 역량 보강을 우선하는 것을 권장합니다. {action}을(를) 통해 고유 역량({unique_score}/65)을 끌어올리세요.",
}

def select_mid_term_template(unique_score: float) -> str:
    return "mid_term_high_score" if (unique_score / 65) >= 0.6 else "mid_term_low_score"
```

---

## 7. 결론 문장 (`final_assessment`)

```python
CONCLUSION_TEMPLATES = {
    "EXCELLENT_FIT": "현재 역량 수준으로 {blend_display} 포지션 지원을 강력히 권장합니다.",
    "GOOD_FIT":      "{key_gap_ko} 역량을 보강하면 {blend_display} 포지션에서 높은 경쟁력을 갖출 수 있습니다.",
    "MODERATE_FIT":  "90일 로드맵에 따른 역량 보완 후 {blend_display} 포지션 지원을 권장합니다.",
    "LOW_FIT":       "현재 단계에서는 고유 핵심 역량({unique_score}/65) 확보가 선행되어야 합니다. 6개월 이상의 준비 기간을 권장합니다.",
}
```

---

## 8. LLM 윤색 지침

**허용:**
- 문장 자연스러움 개선
- 존댓말 통일
- 접속사 추가/변경
- 문장 분리 또는 결합 (의미 유지 시)

**금지:**
- 점수 수치 변경 (`total_score`, `unique_score`, `common_score` 등 모든 숫자)
- `profile_blend` 비율 변경 또는 누락
- 강점/갭 항목 추가 또는 제거
- `skill_group`(UNIQUE/COMMON) 분류 변경
- Evidence에 없는 경험 추가
- `fit_level` 평가 변경
- **v3 신규:** `blend_description`에서 프로필 이름이나 비율(%) 수치 변경 금지

**LLM 프롬프트 구조:**
```
System: 당신은 커리어 리포트 문장을 자연스럽게 다듬는 편집자입니다.
        내용(점수, 강점 항목, 갭 항목, 추천 행동, UNIQUE/COMMON 구분,
        profile_blend 비율)은 절대 변경하지 마세요.
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

## 9. 알려진 문제점 (§ Limitations)

| 문제 | 영향 | 비고 |
|------|------|------|
| `MIXED_3` 이상 템플릿에서 문장이 길어짐 | 가독성 저하, 특히 PDF에서 Section 2 공간 초과 가능 | significant 필터(ratio >= 0.05)로 어느 정도 완화. 3개 초과 시 `MIXED_MANY` 사용 |
| `blend_display_mode=MIXED`일 때 "혼합 프로필"이라는 표현이 일부 사용자에게 불확실하게 느껴질 수 있음 | "내 직무 정체성이 모호하다"는 인상 | `blend_description` 이후 "이 혼합 프로필은 {top1} 역량과 {top2} 역량을 동시에 갖춘 포지션에 강점을 보입니다" 같은 긍정 재프레이밍 문장 추가 권장 (V3.1) |
| 프로필 비율(%)을 `round(v * 100)`으로 정수 표시할 때, 합산이 99% 또는 101%가 될 수 있음 | 사용자가 "왜 합이 100%가 아니죠?" 라고 혼동 가능 | 표시 대상(significant, ratio >= 0.05)만 보여주므로 나머지는 "기타"로 처리하거나, 마지막 항목에서 오차 보정 |
| `priority_clause`(target_priority_text에서 유래한 강점 언급)가 없는 경우에도 문장 끝에 빈 문자열이 남아 공백이 생길 수 있음 | 마이너 UX 이슈 | `.strip()` 처리로 간단히 해결 |