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
  완료: 00~13 문서 전체 (v3.1 primary_profile 체계 반영)
        data/skill_taxonomy.json, data/job_requirements_*.json 10개 (Day 6 산출물)
  잔여: sample_input/report.json (primary_profile 기준 fixture/report)

Week 2 — Engine Week
  목표: profile_selector.py + 5개 엔진 모듈 → report.json 자동 생성
  산출물:
    - scripts/profile_selector.py (select_primary_profile, fallback_profile, confidence_level)
    - engine/evidence_extractor.py (career_histories + target_priority_text 듀얼 소스)
    - engine/requirement_matcher.py (selected_requirements 기준 매칭)
    - engine/scoring_engine.py (primary_profile 65/35 기반 점수)
    - engine/gap_analyzer.py, engine/strength_selector.py
    - engine/report_builder.py (primary_profile, confidence_level, warning_message 포함)
  검증: 결정론적 재현, 손작성 fixture와 구조 100% 일치

Week 3 — Product Week
  목표: Template → HTML → PDF → API → DB → React → Deploy
  산출물: 실제 URL에서 사용자 입력 → PDF 다운로드 전체 플로우
          (Primary Profile Selection, LOW warning, source_profiles 보조 배지 포함)
```

---

## Engineering Priorities (Schema-First, v3)

```
1. 04_PAYLOAD_CONTRACT.md  ← 확정 (target_priority_text, primary_profile 응답)
2. 05_REPORT_SCHEMA.md     ← 확정 (meta.primary_profile, confidence_level, warning_message)
3. 03_ERD.md               ← 확정 (job_requirement_profiles 테이블, primary_profile 저장)
4. Migration               ← ERD 확정 후 실행
5. 06_SCORING_RULES.md     ← 확정 (select_primary_profile, fallback_profile 추가)
6. 07_SKILL_TAXONOMY.md    ← 확정 (79개 풀, living document)
7. 08_EVIDENCE_RULES.md    ← 확정 (듀얼 소스 추출)
8. sample_input/report.json ← Day 7 잔여 (dominant + mixed + LOW)
```

---

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| DB | PostgreSQL (Supabase) |
| 백엔드 | FastAPI (Python) |
| 엔진 | Python (순수 함수, DB/API 의존성 없음) |
| **프로필 선택 모듈 (v3.1 신규)** | `scripts/profile_selector.py` (primary_profile/fallback 선택, 외부 ML 모델 없음) |
| PDF | Jinja2 + Playwright |
| 프론트엔드 | React + TypeScript |
| 배포 | Vercel (frontend) / Render (backend) |
| 에이전트 | Codex |

---

## V1 좌표축 (N=10)

```
hr, marketing, data, product, operations,
sales, design, finance, engineering, customer_success

(data/job_requirements_*.json 10개 — Day 6 산출물, primary_profile registry로 재사용)
```

---

## 금지 사항 (V1)

- 신경망 임베딩 모델 (sentence-transformers 등) — cosine_similarity는 순수 산술
- `target_job_family` ENUM select UI — `target_priority_text` 자유 입력으로 대체
- 사용자-facing Blend 중심 설계 금지 — V1은 primary_profile 중심
- 사용자 요청 경로에서 실시간 외부 API 호출
- LangChain, CrewAI 등 에이전트 프레임워크
- 좌표축별 별도 매칭/점수 로직 분기 (Structure-Once, Scale-Many 위반)
- N>10 profile 추가 (V1 검증 범위. 운영 데이터 없이 추가 금지)
- `synthesize_requirements()` (즉석 합성) — 검증 불가 코드 경로 제거
- 분석 차단 상태 enum 또는 차단형 422 구현

---

## Documentation First (.cursorrules Rule 10)

구현 중 `04_PAYLOAD_CONTRACT.md` 또는 `05_REPORT_SCHEMA.md` 변경이 필요하다고 판단되면,  
코드 작업을 멈추고 문서를 먼저 수정한 뒤 영향 범위를 확인하고 진행한다.

---

## 알려진 문제점 (§ Limitations)

| 문제 | 영향 | 비고 |
|------|------|------|
| fallback `operations`가 LOW 입력에서 과대표현될 수 있음 | 사용자 의도와 불일치 가능 | LOW warning과 추가 입력 권장 필수 |
| secondary_profiles 표시가 혼란을 줄 수 있음 | 대표 판단이 흐려질 수 있음 | 사용자-facing 핵심은 primary_profile로 제한 |
| Week 2 엔진 작업은 profile selector가 선행 조건 | Day 8에서 막히면 Day 9~13이 지연 | profile_selector.py를 Day 8에 먼저 완성하고 나머지 모듈이 이를 임포트 |
