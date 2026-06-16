# 12 — Development Plan (요약)

**Version:** 3.0  
**총 기간:** 3주 (21일)  
**개발자:** 솔로  
**에이전트:** Codex (구현), Claude (설계/문서)

> 일 단위 상세 계획은 `13_Development_Roadmap.md` 참조.  
> 이 문서는 Week 단위 목표와 산출물, 기술 스택, 금지 사항만 요약한다.

---

## 전체 요약

```
Week 1 — Architecture Week  (Day 1~5 완료, Day 6~7 잔여)
  완료: 00~13 문서 전체 (v3 블렌딩 체계 반영)
        data/skill_taxonomy.json, data/job_requirements_*.json 10개 (Day 6 산출물)
  잔여: sample_input/report.json (HR dominant, MIXED 두 케이스 손작성)

Week 2 — Engine Week
  목표: blend_profiles.py + 5개 엔진 모듈 → report.json 자동 생성
  산출물:
    - scripts/blend_profiles.py (cosine_similarity, blend_requirements, renormalize_to_65_35)
    - engine/evidence_extractor.py (career_histories + target_priority_text 듀얼 소스)
    - engine/requirement_matcher.py (blended_requirements 기준 매칭)
    - engine/scoring_engine.py (블렌딩 후 65/35 기반 점수)
    - engine/gap_analyzer.py, engine/strength_selector.py
    - engine/report_builder.py (profile_blend, weight_source 포함)
  검증: 결정론적 재현, 손작성 fixture와 구조 100% 일치

Week 3 — Product Week
  목표: Template → HTML → PDF → API → DB → React → Deploy
  산출물: 실제 URL에서 사용자 입력 → PDF 다운로드 전체 플로우
          (블렌딩 Explanation, source_profiles 배지 포함)
```

---

## Engineering Priorities (Schema-First, v3)

```
1. 04_PAYLOAD_CONTRACT.md  ← 확정 (target_priority_text, profile_blend 응답)
2. 05_REPORT_SCHEMA.md     ← 확정 (meta.profile_blend, blend_description, source_profiles)
3. 03_ERD.md               ← 확정 (job_requirement_profiles 테이블, profile_blend JSONB)
4. Migration               ← ERD 확정 후 실행
5. 06_SCORING_RULES.md     ← 확정 (blend_requirements, renormalize_to_65_35 추가)
6. 07_SKILL_TAXONOMY.md    ← 확정 (79개 풀, living document)
7. 08_EVIDENCE_RULES.md    ← 확정 (듀얼 소스 추출)
8. sample_input/report.json ← Day 7 잔여 (HR dominant + MIXED 2종)
```

---

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| DB | PostgreSQL (Supabase) |
| 백엔드 | FastAPI (Python) |
| 엔진 | Python (순수 함수, DB/API 의존성 없음) |
| **블렌딩 모듈 (v3 신규)** | `scripts/blend_profiles.py` (cosine_similarity: 순수 산술, 외부 ML 모델 없음) |
| PDF | Jinja2 + Playwright |
| 프론트엔드 | React + TypeScript |
| 배포 | Vercel (frontend) / Render (backend) |
| 에이전트 | Codex |

---

## V1 좌표축 (N=10)

```
hr, marketing, data, product, operations,
sales, design, finance, engineering, customer_success

(data/job_requirements_*.json 10개 — Day 6 산출물, 블렌딩 기저 벡터로 재사용)
```

---

## 금지 사항 (V1)

- 신경망 임베딩 모델 (sentence-transformers 등) — cosine_similarity는 순수 산술
- `target_job_family` ENUM select UI — `target_priority_text` 자유 입력으로 대체
- 사용자 요청 경로에서 실시간 외부 API 호출
- LangChain, CrewAI 등 에이전트 프레임워크
- 좌표축별 별도 매칭/점수 로직 분기 (Structure-Once, Scale-Many 위반)
- N>10 좌표축 추가 (V1 검증 범위. `meta.profile_blend` 분포 데이터 없이 추가 금지)
- `synthesize_requirements()` (즉석 합성) — 블렌딩으로 대체, 검증 불가 코드 경로 제거
- `BLOCKED` 상태에서 `blend_requirements()` 호출 (§10 불변규칙 12)

---

## Documentation First (.cursorrules Rule 10)

구현 중 `04_PAYLOAD_CONTRACT.md` 또는 `05_REPORT_SCHEMA.md` 변경이 필요하다고 판단되면,  
코드 작업을 멈추고 문서를 먼저 수정한 뒤 영향 범위를 확인하고 진행한다.

---

## 알려진 문제점 (§ Limitations)

| 문제 | 영향 | 비고 |
|------|------|------|
| `blend_profiles.py`의 `POWER=2` 값이 경험 데이터 없이 설정됨 | 블렌딩 비율의 "쏠림 정도"가 실제 사용자 경험에 최적화되지 않을 수 있음 | V1 운영 후 `profile_blend` 분포 데이터로 보정 |
| `SINGLE_IDENTITY_THRESHOLD=0.7` 임계값이 임의로 설정됨 | 단일/혼합 표현 분기 기준이 사용자 기대와 불일치할 수 있음 | 동일하게 V1 운영 후 보정 |
| Week 2 엔진 작업이 블렌딩 모듈(신규)을 포함하므로 v2보다 복잡도 증가 | Day 8~14 작업량이 v2 대비 약 1.5배 추정 | blend_profiles.py를 Day 8에 먼저 완성하고 나머지 엔진 모듈이 이를 임포트하는 순서로 진행 |