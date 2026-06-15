# 12 — Development Plan (요약)

**총 기간:** 3주 (21일)  
**개발자:** 솔로  
**에이전트:** Codex (구현), Claude (설계/문서)

> 일 단위 상세 계획은 `13_DEVELOPMENT_ROADMAP.md` 참조.  
> 이 문서는 Week 단위 목표와 산출물, 기술 스택, 금지 사항만 요약한다.

---

## 전체 요약

```
Week 1 — Architecture Week
  목표: docs 확정 + sample_input/report.json (HR, Data 손작성)
  산출물: 13개 문서 전체, Job Family 10개 weight 프로필, 정답 fixture 2종

Week 2 — Engine Week
  목표: 6개 엔진 모듈 → report.json 자동 생성
  산출물: sample_input_*.json → generated_report_*.json (HR, Data)
  검증: 결정론적 재현, 손작성 fixture와 구조 100% 일치

Week 3 — Product Week
  목표: Template → HTML → PDF → API → DB → React → Deploy
  산출물: 실제 URL에서 사용자 입력 → PDF 다운로드 전체 플로우
```

---

## Engineering Priorities (Schema-First)

`01_PRD.md` §10과 동일. 구현 순서는 항상:

```
1. 04_PAYLOAD_CONTRACT.md
2. 05_REPORT_SCHEMA.md   ← 최우선 품질 투자
3. 03_ERD.md
4. Migration
5. 06_SCORING_RULES.md
6. 07_SKILL_TAXONOMY.md
7. 08_EVIDENCE_RULES.md
8. sample_input/report.json (HR, Data)
```

---

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| DB | PostgreSQL (Supabase) |
| 백엔드 | FastAPI (Python) |
| 엔진 | Python (순수 함수 기반, `engine/` 디렉토리, DB/API 의존성 없음) |
| PDF | Jinja2 + Playwright |
| 프론트엔드 | React + TypeScript |
| 배포 | Vercel (frontend) / Render (backend) |
| 에이전트 | Codex |

---

## V1 Job Family (10개)

```
HR, Marketing, Data, Product, Operations,
Sales, Design, Finance, Engineering, Customer Success
```

각 Job Family는 `06_SCORING_RULES.md` §2의 weight 자동 배분 알고리즘에 따라  
`core_skill_keys`(4~5개, UNIQUE 65%) + `common_skill_keys`(5개, COMMON 35%)만으로 정의된다.

---

## 금지 사항 (V1)

- DB 추가 (Supabase만 사용)
- Auth 구현
- RAG 또는 벡터 DB
- 사용자 요청 경로에서 외부 채용 API 실시간 호출 (Deterministic First 위반)
- LangChain, CrewAI 등 에이전트 프레임워크
- Job Family별 매칭/점수 로직 분기 (Structure-Once, Scale-Many 위반 — `00_PROJECT_VISION.md` §5)
- 11번째 이상 Job Family 추가 (V1 검증 범위 = 10개. 구조상 가능하나 V1.1로 보류)

---

## Documentation First (.cursorrules Rule 10)

구현 중 `04_PAYLOAD_CONTRACT.md` 또는 `05_REPORT_SCHEMA.md` 변경이 필요하다고 판단되면,  
코드 작업을 멈추고 문서를 먼저 수정한 뒤 영향 범위(ERD, Scoring Rules 등)를 확인하고 진행한다.