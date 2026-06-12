# 12 — Development Plan

**총 기간:** 3주  
**개발자:** 솔로  
**에이전트:** Codex (구현), Claude (설계/문서)

---

## Week 1: 기반 구축

### 목표
문서 확정 → 스키마 확정 → 엔진 CLI 시작

### 일별 계획

| Day | 작업 |
|-----|------|
| 1 | /docs 전체 확정, Codex용 프롬프트 최종화 |
| 2 | PostgreSQL 마이그레이션 작성 (03_ERD.md 기반) |
| 3 | 마스터 데이터 시딩 (job_requirement_stats 5개 Job Family) |
| 4 | Evidence 추출 엔진 CLI 구현 (08_EVIDENCE_RULES.md 기반) |
| 5 | Evidence 추출 단위 테스트 (Job Family별 5개 이상 케이스) |

### 완료 기준
- [ ] 마이그레이션 정상 실행
- [ ] `python engine.py --input sample.json` 실행 시 Evidence 추출 결과 출력

---

## Week 2: 핵심 파이프라인

### 목표
점수화 → 리포트 JSON 생성 → PDF 생성

### 일별 계획

| Day | 작업 |
|-----|------|
| 6 | requirement_matches 계산 엔진 (06_SCORING_RULES.md 기반) |
| 7 | report_scores 집계, report_gaps 분류 |
| 8 | Report JSON 직렬화 (05_REPORT_SCHEMA.md 전체 구조) |
| 9 | Text Template 엔진 (09_TEXT_TEMPLATE_RULES.md 기반) |
| 10 | PDF 생성 (WeasyPrint, 10_PDF_TEMPLATE_SPEC.md 기반) |

### 완료 기준
- [ ] `python engine.py --input sample.json --output report.json` 정상 실행
- [ ] `python pdf_gen.py --input report.json --output report.pdf` PDF 생성 성공
- [ ] 동일 입력 3회 실행 → 동일 점수 확인 (결정론적 검증)

---

## Week 3: 서비스 레이어

### 목표
FastAPI → React → Supabase → 배포

### 일별 계획

| Day | 작업 |
|-----|------|
| 11 | FastAPI 앱 구조, POST /reports, GET /reports/{id} |
| 12 | GET /reports/{id}/pdf, 비동기 엔진 연동 (BackgroundTasks) |
| 13 | React 입력 폼 (/report/new), Generating 화면 |
| 14 | React 결과 페이지 (/report/:id), PDF 다운로드 |
| 15 | Supabase 연동, 환경 변수 정리, Render/Railway 배포 |

### 완료 기준
- [ ] `POST /reports` → 리포트 생성 성공 (end-to-end)
- [ ] 결과 페이지 정상 렌더링
- [ ] PDF 다운로드 성공
- [ ] 배포 URL 접근 가능

---

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| DB | PostgreSQL (Supabase) |
| 백엔드 | FastAPI (Python) |
| 엔진 | Python (순수 함수 기반) |
| PDF | WeasyPrint |
| 프론트엔드 | React + TypeScript |
| 배포 | Render 또는 Railway |
| 에이전트 | Codex |

---

## 금지 사항 (V1)

- DB 추가 (Supabase만 사용)
- Auth 구현
- RAG 또는 벡터 DB
- 외부 채용 API 연동
- LangChain, CrewAI 등 에이전트 프레임워크

---

---

# .cursorrules — CareerFit V1

이 파일은 Codex(또는 Cursor AI)가 CareerFit 코드베이스에서 작업할 때 반드시 따라야 하는 규칙이다.  
규칙을 어기는 코드는 생성하지 않는다.

---

## 1. 프로젝트 컨텍스트

- **프로젝트명:** CareerFit V1
- **목적:** 커리어 경험 → 직무 적합도 분석 → PDF 리포트 생성
- **문서 기준:** `/docs` 폴더의 `.md` 파일이 단일 진실 공급원
- **개발자:** 솔로 개발, 에이전트 보조

---

## 2. 아키텍처 규칙

### 절대 금지
```
❌ Auth / 로그인 구현 추가
❌ Supabase 외 DB 추가 (Redis, MongoDB 등)
❌ RAG, 벡터 DB (pgvector는 V2)
❌ LangChain, CrewAI, AutoGPT 등 에이전트 프레임워크
❌ 외부 채용 공고 API 연동
❌ ORM 없이 raw SQL 직접 작성 (SQLAlchemy 또는 Supabase client 사용)
```

### 레이어 분리 원칙
```
engine/         ← 순수 함수만. DB 접근 금지. FastAPI import 금지.
api/            ← FastAPI 라우터. 비즈니스 로직 금지.
services/       ← 비즈니스 로직. engine 호출 + DB 저장.
models/         ← DB 스키마 (SQLAlchemy 또는 Pydantic 모델).
```

---

## 3. 엔진 규칙 (engine/)

### 결정론적 보장
```python
# ✅ 올바른 패턴 — 순수 함수
def calculate_score(matches: list[RequirementMatch], requirements: list[Requirement]) -> float:
    ...

# ❌ 금지 — 엔진 내부에서 LLM 직접 호출
def calculate_score(...):
    response = openai.chat(...)  # 금지
```

### Evidence 추출 규칙
- `original_text`는 **절대 수정하지 않는다**
- 사용자 입력 문장을 요약하거나 재작성하는 코드를 작성하지 않는다
- `confidence_score < 0.5`인 Evidence는 생성하지 않는다

### 점수 계산 규칙
- `docs/06_SCORING_RULES.md`의 공식을 그대로 구현한다
- matchLevel → match_score 매핑은 상수로 정의한다

```python
MATCH_SCORE = {
    "FULL":    1.00,
    "STRONG":  0.75,
    "PARTIAL": 0.50,
    "WEAK":    0.25,
    "NONE":    0.00,
}
```

---

## 4. DB 규칙

### 스키마 기준
- `docs/03_ERD.md`의 테이블 정의가 유일한 기준
- 마이그레이션 없이 테이블을 추가하지 않는다
- ENUM 타입은 반드시 PostgreSQL ENUM으로 정의한다

### 데이터 무결성
```python
# ✅ report_json은 READY 상태에서만 저장
if report.status == "READY":
    report.report_json = generated_json

# ❌ 중간 상태에서 report_json 저장 금지
if report.status == "ANALYZING":
    report.report_json = partial_json  # 금지
```

### 원문 보존
```python
# ✅ 원문 그대로 저장
career_history.responsibilities = user_input["responsibilities"]

# ❌ 저장 전 가공 금지
career_history.responsibilities = clean_text(user_input["responsibilities"])  # 금지
```

---

## 5. API 규칙

### 엔드포인트 기준
`docs/11_API_SPEC.md`에 정의된 3개 엔드포인트만 구현한다.

```
POST /reports
GET  /reports/{report_id}
GET  /reports/{report_id}/pdf
```

임의로 엔드포인트를 추가하지 않는다.

### 응답 형식
- 모든 에러는 `docs/04_PAYLOAD_CONTRACT.md`의 Error Format을 따른다
- 성공 응답도 동일 문서의 Response 구조를 따른다

### 상태 관리
```python
# 상태 전이는 이 순서만 허용
VALID_TRANSITIONS = {
    "CREATED":        ["ANALYZING", "FAILED"],
    "ANALYZING":      ["PDF_GENERATING", "FAILED"],
    "PDF_GENERATING": ["READY", "FAILED"],
    "READY":          [],
    "FAILED":         [],
}
```

---

## 6. Report JSON 규칙

- `docs/05_REPORT_SCHEMA.md`의 구조와 100% 일치해야 한다
- 섹션을 임의로 추가하거나 삭제하지 않는다
- LLM 폴백 실패 시에도 모든 섹션이 채워진 Report JSON이 생성되어야 한다

```python
# LLM 실패 시 템플릿 기반 폴백 필수
try:
    text = llm_polish(template_text)
except Exception:
    text = template_text  # 폴백, 리포트 생성은 계속
```

---

## 7. 코드 스타일

### Python
- Type hints 필수 (모든 함수 인자 및 반환값)
- Pydantic 모델로 데이터 검증
- 함수 단위: 단일 책임 원칙 (함수 하나 = 역할 하나)
- 파일당 300줄 초과 시 모듈 분리

### 파일 구조
```
careerfit/
├── engine/
│   ├── evidence.py       # Evidence 추출
│   ├── matching.py       # requirement_matches 계산
│   ├── scoring.py        # 점수 계산
│   ├── report_builder.py # Report JSON 조립
│   └── text_template.py  # 텍스트 템플릿 생성
├── api/
│   └── routes/
│       └── reports.py
├── services/
│   └── report_service.py
├── models/
│   ├── db.py             # SQLAlchemy 모델
│   └── schemas.py        # Pydantic 스키마
├── pdf/
│   └── generator.py
└── main.py
```

### React (TypeScript)
- 컴포넌트당 파일 1개
- Props 타입은 interface로 명시
- API 호출은 `/src/api/` 모듈에서만

---

## 8. 테스트 규칙

- 엔진 함수는 반드시 단위 테스트 작성
- 동일 입력 → 동일 출력 테스트 필수 (결정론적 검증)
- DB 연동 테스트는 별도 테스트 DB 사용

```python
# 결정론적 검증 테스트 패턴
def test_score_determinism():
    input_data = load_fixture("hr_sample.json")
    score_1 = calculate_total_score(input_data)
    score_2 = calculate_total_score(input_data)
    assert score_1 == score_2
```

---

## 9. 커밋 규칙

```
feat: 새 기능
fix: 버그 수정
docs: 문서 변경
refactor: 리팩토링 (기능 변경 없음)
test: 테스트 추가/수정
chore: 빌드, 설정 변경
```

예시: `feat: evidence 추출 엔진 EXPLICIT 규칙 구현`