# 03 — Entity Relationship Diagram (ERD)

**DB:** PostgreSQL  
**Extensions:** `uuid-ossp`, `pgvector` (optional, V2)

---

## 1. ER Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CareerFit V1 ERD                               │
└─────────────────────────────────────────────────────────────────────────┘

 ┌──────────────┐         ┌──────────────────────┐
 │    users     │         │  job_requirement_stats│
 │──────────────│         │──────────────────────│
 │ id (PK)      │         │ id (PK)              │
 │ session_id   │         │ job_family           │◄──────────────────┐
 │ created_at   │         │ requirement_key      │                   │
 └──────┬───────┘         │ label_ko             │                   │
        │ 1               │ weight               │                   │
        │                 │ is_core              │                   │
        │ N               │ description          │                   │
 ┌──────▼───────────────┐ └──────────────────────┘                   │
 │       reports        │                                             │
 │──────────────────────│                                             │
 │ id (PK, UUID)        │                                             │
 │ user_id (FK→users)   │                                             │
 │ target_job_family    │─────────────────────────────────────────────┘
 │ status               │
 │ report_json (JSONB)  │
 │ pdf_url              │
 │ error_message        │
 │ created_at           │
 │ completed_at         │
 │ expires_at           │
 └──────┬───────────────┘
        │ 1
        │
        ├─────────────────────────────────────────────┐
        │ N                                           │ N
 ┌──────▼──────────────────┐             ┌────────────▼────────────┐
 │    career_histories     │             │     report_scores       │
 │─────────────────────────│             │─────────────────────────│
 │ id (PK)                 │             │ id (PK)                 │
 │ report_id (FK→reports)  │             │ report_id (FK→reports)  │
 │ company_name            │             │ total_score             │
 │ title                   │             │ score_breakdown (JSONB) │
 │ start_date              │             │ percentile              │
 │ end_date                │             │ calculated_at           │
 │ is_current              │             └─────────────────────────┘
 │ responsibilities (TEXT) │
 │ achievements (TEXT)     │
 │ sort_order              │
 └──────┬──────────────────┘
        │ 1
        │ N
 ┌──────▼──────────────────┐
 │   career_evidences      │
 │─────────────────────────│
 │ id (PK)                 │
 │ career_history_id (FK)  │─────────────┐
 │ report_id (FK→reports)  │             │
 │ skill_key               │             │
 │ original_text (TEXT)    │             │
 │ evidence_type           │             │
 │ confidence_score        │             │
 │ created_at              │             │
 └─────────────────────────┘             │
                                         │
 ┌───────────────────────────────────────▼──────────┐
 │              requirement_matches                  │
 │──────────────────────────────────────────────────│
 │ id (PK)                                          │
 │ report_id (FK→reports)                           │
 │ requirement_key (FK→job_requirement_stats)       │
 │ match_level  (FULL/STRONG/PARTIAL/WEAK/NONE)     │
 │ matched_evidence_ids (UUID[])                    │
 │ match_score                                      │
 │ reasoning (TEXT)                                 │
 └──────────────────────────────────────────────────┘

 ┌─────────────────────────────────────────────────┐
 │                 report_gaps                      │
 │─────────────────────────────────────────────────│
 │ id (PK)                                          │
 │ report_id (FK→reports)                           │
 │ requirement_key                                  │
 │ gap_severity   (CRITICAL/MAJOR/MINOR)            │
 │ gap_reason (TEXT)                                │
 │ recommendation (TEXT)                            │
 │ priority_order (INT)                             │
 └─────────────────────────────────────────────────┘
```

---

## 2. 테이블 상세 정의

### 2.1 `users`

익명 사용자 추적용. V1은 세션 기반.

```sql
CREATE TABLE users (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id  TEXT        NOT NULL UNIQUE,   -- 브라우저 세션 식별자
    ip_hash     TEXT,                          -- 해시된 IP (로그 목적)
    user_agent  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_session_id ON users(session_id);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| session_id | TEXT | 브라우저 로컬 스토리지 기반 익명 ID |
| ip_hash | TEXT | SHA-256 해시된 IP (분석용, 개인정보 아님) |
| created_at | TIMESTAMPTZ | 최초 방문 시각 |

---

### 2.2 `reports`

리포트의 중심 테이블. 모든 생성 결과의 루트.

```sql
CREATE TYPE report_status AS ENUM (
    'CREATED',
    'ANALYZING',
    'PDF_GENERATING',
    'READY',
    'FAILED'
);

CREATE TYPE job_family AS ENUM (
    'HR',
    'MARKETING',
    'DATA',
    'PRODUCT',
    'OPERATIONS'
);

CREATE TABLE reports (
    id                UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id           UUID            REFERENCES users(id) ON DELETE SET NULL,
    target_job_family job_family      NOT NULL,
    status            report_status   NOT NULL DEFAULT 'CREATED',
    report_json       JSONB,          -- 완성된 Report JSON (READY 상태에서만 채워짐)
    pdf_url           TEXT,           -- S3 또는 로컬 경로
    error_message     TEXT,           -- FAILED 상태일 때만 사용
    retry_count       INT             NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    completed_at      TIMESTAMPTZ,
    expires_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW() + INTERVAL '30 days'
);

CREATE INDEX idx_reports_user_id    ON reports(user_id);
CREATE INDEX idx_reports_status     ON reports(status);
CREATE INDEX idx_reports_expires_at ON reports(expires_at);
CREATE INDEX idx_reports_json       ON reports USING GIN (report_json);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK, URL에 노출되는 리포트 식별자 |
| user_id | UUID | FK → users, nullable (세션 만료 시) |
| target_job_family | ENUM | 분석 대상 Job Family |
| status | ENUM | 생성 파이프라인 상태 |
| report_json | JSONB | 단일 진실 공급원. 05_REPORT_SCHEMA.md 구조 따름 |
| pdf_url | TEXT | PDF 저장 위치 |
| error_message | TEXT | 실패 원인 로그 |
| retry_count | INT | 자동 재시도 횟수 |
| expires_at | TIMESTAMPTZ | 30일 후 만료 |

**상태 전이:**
```
CREATED → ANALYZING → PDF_GENERATING → READY
                ↘                   ↘
                FAILED             FAILED
```

---

### 2.3 `career_histories`

사용자가 입력한 개별 경력 항목.

```sql
CREATE TABLE career_histories (
    id                UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id         UUID        NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    company_name      TEXT        NOT NULL,
    title             TEXT        NOT NULL,
    start_date        DATE        NOT NULL,
    end_date          DATE,                   -- NULL이면 현재 재직 중
    is_current        BOOLEAN     NOT NULL DEFAULT FALSE,
    responsibilities  TEXT        NOT NULL,   -- 자유 텍스트, 원문 보존
    achievements      TEXT,                   -- 자유 텍스트, 원문 보존
    sort_order        INT         NOT NULL DEFAULT 0,  -- 최신 순 정렬
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_career_histories_report_id ON career_histories(report_id);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| responsibilities | TEXT | 담당 업무 자유 텍스트. Evidence 추출 원본. **절대 가공하지 않음** |
| achievements | TEXT | 성과 자유 텍스트. Evidence 추출 원본. **절대 가공하지 않음** |
| sort_order | INT | 0 = 가장 최근 직장 |

---

### 2.4 `career_evidences`

`career_histories`에서 추출된 스킬 증거 단위.  
Evidence는 원문 텍스트의 특정 구간과 skill_key의 매핑이다.

```sql
CREATE TYPE evidence_type AS ENUM (
    'EXPLICIT',     -- 스킬명이 직접 언급됨 (e.g. "SQL 쿼리 작성")
    'INFERRED',     -- 업무 맥락에서 추론됨 (e.g. "데이터 취합 → data_analysis")
    'ACHIEVED'      -- 성과 기반 (e.g. "효율 30% 향상 → process_improvement")
);

CREATE TABLE career_evidences (
    id                  UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id           UUID            NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    career_history_id   UUID            NOT NULL REFERENCES career_histories(id) ON DELETE CASCADE,
    skill_key           TEXT            NOT NULL,  -- FK→ skill_taxonomy
    original_text       TEXT            NOT NULL,  -- 원문 구간 (절대 수정 금지)
    evidence_type       evidence_type   NOT NULL,
    confidence_score    NUMERIC(3,2)    NOT NULL CHECK (confidence_score BETWEEN 0 AND 1),
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_career_evidences_report_id ON career_evidences(report_id);
CREATE INDEX idx_career_evidences_skill_key ON career_evidences(skill_key);
```

| 컬럼 | 타입 | 설명 |
|------|------|------|
| original_text | TEXT | 원문 그대로. 절대 수정하지 않음 |
| confidence_score | NUMERIC | 0.0–1.0. EXPLICIT=1.0, INFERRED=0.7, ACHIEVED=0.8 |

**Evidence 유형 정의:**
- `EXPLICIT`: 사용자가 스킬명을 직접 언급
- `INFERRED`: 업무 맥락에서 스킬 존재를 추론 (규칙 기반, `08_EVIDENCE_RULES.md` 참조)
- `ACHIEVED`: 성과/결과로부터 스킬 역산

---

### 2.5 `job_requirement_stats`

각 Job Family별 요구 역량 정의. 관리자가 사전 세팅하는 마스터 데이터.

```sql
CREATE TABLE job_requirement_stats (
    id              SERIAL      PRIMARY KEY,
    job_family      job_family  NOT NULL,
    requirement_key TEXT        NOT NULL,   -- skill_taxonomy의 key
    label_ko        TEXT        NOT NULL,   -- 화면 표시명 (한국어)
    weight          NUMERIC(3,2) NOT NULL CHECK (weight BETWEEN 0 AND 1),
    is_core         BOOLEAN     NOT NULL DEFAULT FALSE,  -- 핵심 요구사항 여부
    description     TEXT,                   -- 이 요구사항의 설명
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (job_family, requirement_key)
);

CREATE INDEX idx_job_req_stats_job_family ON job_requirement_stats(job_family);
```

**weight 규칙:**
- 각 Job Family의 전체 weight 합계 = 1.0 (100%)
- `is_core = TRUE`인 항목: weight ≥ 0.10
- 단일 항목 최대 weight: 0.25

**예시 데이터 (HR):**

| requirement_key | label_ko | weight | is_core |
|-----------------|----------|--------|---------|
| recruiting | 채용 관리 | 0.20 | TRUE |
| training_and_onboarding | 교육/온보딩 | 0.15 | TRUE |
| performance_management | 성과 관리 | 0.15 | TRUE |
| hr_policy | HR 정책 수립 | 0.12 | FALSE |
| payroll | 급여/복리후생 | 0.10 | FALSE |
| labor_law | 노동법 | 0.10 | FALSE |
| stakeholder_management | 이해관계자 관리 | 0.08 | FALSE |
| documentation | 문서화 | 0.05 | FALSE |
| data_analysis | 데이터 분석 | 0.05 | FALSE |

---

### 2.6 `report_scores`

결정론적 알고리즘이 계산한 점수 결과.

```sql
CREATE TABLE report_scores (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id       UUID        NOT NULL UNIQUE REFERENCES reports(id) ON DELETE CASCADE,
    total_score     NUMERIC(5,2) NOT NULL CHECK (total_score BETWEEN 0 AND 100),
    score_breakdown JSONB       NOT NULL,  -- requirement별 점수 상세
    percentile      NUMERIC(5,2),          -- 동일 Job Family 내 백분위 (V2)
    calculated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**score_breakdown JSONB 구조:**
```json
{
  "recruiting": {
    "weight": 0.20,
    "match_level": "FULL",
    "match_score": 1.0,
    "weighted_score": 20.0,
    "evidence_count": 3
  },
  "training_and_onboarding": {
    "weight": 0.15,
    "match_level": "PARTIAL",
    "match_score": 0.5,
    "weighted_score": 7.5,
    "evidence_count": 1
  }
}
```

---

### 2.7 `requirement_matches`

요구사항별 매칭 결과 상세. `report_scores`의 breakdown을 정규화한 것.

```sql
CREATE TYPE match_level AS ENUM ('FULL', 'STRONG', 'PARTIAL', 'WEAK', 'NONE');

CREATE TABLE requirement_matches (
    id                      UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id               UUID        NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    requirement_key         TEXT        NOT NULL,
    match_level             match_level NOT NULL,
    matched_evidence_ids    UUID[]      NOT NULL DEFAULT '{}',  -- career_evidences.id 참조
    match_score             NUMERIC(3,2) NOT NULL,  -- 0.0–1.0
    reasoning               TEXT,       -- 매칭 판단 근거 (로그용)
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (report_id, requirement_key)
);

CREATE INDEX idx_req_matches_report_id ON requirement_matches(report_id);
```

| match_level | match_score | 의미 |
|-------------|-------------|------|
| FULL | 1.00 | 요구사항을 완전히 충족하는 Evidence 존재 |
| STRONG | 0.75 | 핵심 요소 충족, 일부 심화 부족 |
| PARTIAL | 0.50 | 일부 충족, 상당한 갭 존재 |
| WEAK | 0.25 | 간접적 연관성만 있음 |
| NONE | 0.00 | 관련 Evidence 없음 |

---

### 2.8 `report_gaps`

미충족 요구사항 및 갭 분석 결과.

```sql
CREATE TYPE gap_severity AS ENUM ('CRITICAL', 'MAJOR', 'MINOR');

CREATE TABLE report_gaps (
    id                  UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id           UUID            NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    requirement_key     TEXT            NOT NULL,
    gap_severity        gap_severity    NOT NULL,
    gap_reason          TEXT            NOT NULL,    -- 갭 발생 이유
    recommendation      TEXT            NOT NULL,    -- 채우기 위한 구체적 행동
    priority_order      INT             NOT NULL,    -- 1이 최우선
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    UNIQUE (report_id, requirement_key)
);

CREATE INDEX idx_report_gaps_report_id ON report_gaps(report_id);
```

**gap_severity 분류 기준:**

| severity | 기준 |
|----------|------|
| CRITICAL | is_core = TRUE이고 match_level = NONE 또는 WEAK |
| MAJOR | weight ≥ 0.10이고 match_level ≤ PARTIAL |
| MINOR | weight < 0.10이고 match_level ≤ PARTIAL |

---

## 3. 관계 요약

```
users           1 ──── N    reports
reports         1 ──── N    career_histories
reports         1 ──── N    career_evidences
reports         1 ──── 1    report_scores
reports         1 ──── N    requirement_matches
reports         1 ──── N    report_gaps
career_histories 1 ──── N   career_evidences
job_requirement_stats N ─── (참조) ─── requirement_matches
job_requirement_stats N ─── (참조) ─── report_gaps
```

---

## 4. 데이터 흐름

```
[사용자 입력]
    │
    ▼
career_histories (원문 저장)
    │
    ▼ Evidence 추출 엔진 (08_EVIDENCE_RULES.md)
    │
career_evidences (skill_key 매핑)
    │
    ▼ 매칭 엔진 (job_requirement_stats 조회)
    │
requirement_matches (match_level 계산)
    │
    ├──► report_scores (06_SCORING_RULES.md 기반 집계)
    │
    └──► report_gaps (미충족 요구사항 분류)
              │
              ▼
        report_json (05_REPORT_SCHEMA.md 구조로 직렬화)
              │
              ▼
        reports.report_json (JSONB 저장)
```

---

## 5. Migration 순서

```sql
-- 의존성 순서대로 생성
1. CREATE TYPE report_status
2. CREATE TYPE job_family
3. CREATE TYPE evidence_type
4. CREATE TYPE match_level
5. CREATE TYPE gap_severity
6. CREATE TABLE users
7. CREATE TABLE reports
8. CREATE TABLE career_histories
9. CREATE TABLE career_evidences
10. CREATE TABLE job_requirement_stats
11. CREATE TABLE report_scores
12. CREATE TABLE requirement_matches
13. CREATE TABLE report_gaps
```

---

## 6. 인덱스 전략

| 인덱스 | 목적 |
|--------|------|
| `reports.status` | 폴링 쿼리 (status = ANALYZING인 리포트 조회) |
| `reports.expires_at` | 만료 정리 배치 |
| `reports.report_json` (GIN) | JSONB 내부 검색 (V2 분석 기능) |
| `career_evidences.skill_key` | 스킬별 Evidence 집계 |
| `requirement_matches.report_id` | 리포트별 매칭 결과 조회 |
# 05 — Report JSON Schema

Report JSON은 CareerFit의 **단일 진실 공급원(Single Source of Truth)**이다.  
PDF, 화면, API 응답은 모두 이 구조를 파싱해 렌더링한다.

---

## 전체 구조

```json
{
  "meta": { ... },
  "summary": { ... },
  "careerProfile": { ... },
  "targetJobAnalysis": { ... },
  "marketAnalysis": { ... },
  "skillMapping": { ... },
  "evidenceMapping": { ... },
  "scores": { ... },
  "strengths": { ... },
  "gaps": { ... },
  "recommendations": { ... },
  "roadmap": { ... },
  "reportSections": { ... }
}
```

---

## 섹션별 상세

### `meta`
```json
{
  "meta": {
    "report_id": "550e8400-e29b-41d4-a716-446655440000",
    "generated_at": "2025-06-01T12:03:45Z",
    "target_job_family": "HR",
    "target_job_family_ko": "인사(HR)",
    "engine_version": "1.0.0",
    "llm_used": true
  }
}
```

---

### `summary`
```json
{
  "summary": {
    "total_score": 78.5,
    "score_label": "우수",
    "one_line": "채용과 온보딩 역량은 시장 기준을 충족하나, 노동법과 급여 관리 보강이 필요합니다.",
    "fit_level": "GOOD_FIT",
    "key_strengths": ["recruiting", "training_and_onboarding", "stakeholder_management"],
    "key_gaps": ["labor_law", "payroll"]
  }
}
```

**fit_level 기준:**

| fit_level | score 범위 |
|-----------|-----------|
| EXCELLENT_FIT | 90–100 |
| GOOD_FIT | 75–89 |
| MODERATE_FIT | 55–74 |
| LOW_FIT | 0–54 |

---

### `careerProfile`
```json
{
  "careerProfile": {
    "total_experience_months": 36,
    "total_experience_label": "3년",
    "career_count": 2,
    "most_recent_title": "HR 매니저",
    "most_recent_company": "주식회사 예시",
    "extracted_skills": [
      {
        "skill_key": "recruiting",
        "label_ko": "채용 관리",
        "evidence_count": 3,
        "confidence": "HIGH"
      }
    ]
  }
}
```

---

### `targetJobAnalysis`
```json
{
  "targetJobAnalysis": {
    "job_family": "HR",
    "job_family_ko": "인사(HR)",
    "market_demand_label": "높음",
    "core_requirements": [
      {
        "requirement_key": "recruiting",
        "label_ko": "채용 관리",
        "weight": 0.20,
        "is_core": true,
        "match_level": "FULL"
      }
    ],
    "requirement_overview": "HR 직무는 채용, 온보딩, 성과관리의 트리플 역량을 핵심으로 요구합니다."
  }
}
```

---

### `skillMapping`
```json
{
  "skillMapping": {
    "matched": [
      {
        "skill_key": "recruiting",
        "label_ko": "채용 관리",
        "match_level": "FULL",
        "weight": 0.20,
        "weighted_score": 20.0
      }
    ],
    "unmatched": [
      {
        "skill_key": "labor_law",
        "label_ko": "노동법",
        "match_level": "NONE",
        "weight": 0.10,
        "weighted_score": 0.0
      }
    ]
  }
}
```

---

### `evidenceMapping`
```json
{
  "evidenceMapping": [
    {
      "skill_key": "recruiting",
      "label_ko": "채용 관리",
      "evidences": [
        {
          "career_history_id": "ch-uuid-001",
          "company_name": "주식회사 예시",
          "original_text": "신입사원 채용 전 과정 담당. JD 작성, 서류 검토, 면접 진행",
          "evidence_type": "EXPLICIT"
        }
      ]
    }
  ]
}
```

---

### `scores`
```json
{
  "scores": {
    "total": 78.5,
    "breakdown": {
      "recruiting": {
        "weight": 0.20,
        "match_level": "FULL",
        "match_score": 1.0,
        "weighted_score": 20.0,
        "evidence_count": 2
      }
    }
  }
}
```

---

### `strengths`
```json
{
  "strengths": [
    {
      "rank": 1,
      "skill_key": "recruiting",
      "label_ko": "채용 관리",
      "match_level": "FULL",
      "headline": "채용 전 과정을 직접 운영한 검증된 경험",
      "detail": "JD 작성부터 온보딩까지 채용 사이클 전반을 직접 담당했으며, 연간 목표 120% 달성의 성과를 보유합니다.",
      "supporting_evidence": ["ch-uuid-001"]
    }
  ]
}
```

---

### `gaps`
```json
{
  "gaps": [
    {
      "rank": 1,
      "skill_key": "labor_law",
      "label_ko": "노동법",
      "gap_severity": "MAJOR",
      "headline": "노동법 전문성 보강 필요",
      "detail": "현재 경력에서 노동법 관련 직접 경험이 확인되지 않습니다.",
      "recommendation": "노무사 시험 준비 또는 노동법 관련 사내 프로젝트 참여를 권장합니다.",
      "priority_order": 1
    }
  ]
}
```

---

### `recommendations`
```json
{
  "recommendations": {
    "short_term": [
      {
        "action": "노동법 온라인 강의 수강 (40시간)",
        "rationale": "MAJOR 갭인 노동법 역량 보완",
        "timeframe": "1–2개월"
      }
    ],
    "mid_term": [
      {
        "action": "HR 제너럴리스트 포지션 지원",
        "rationale": "현재 점수 78.5점으로 중견기업 HR 제너럴리스트 지원 가능",
        "timeframe": "3–6개월"
      }
    ]
  }
}
```

---

### `roadmap`
```json
{
  "roadmap": {
    "period": "90일",
    "phases": [
      {
        "phase": 1,
        "label": "1–30일: 갭 보완",
        "actions": [
          "노동법 기초 강의 수강",
          "급여 관련 사내 프로세스 학습"
        ]
      },
      {
        "phase": 2,
        "label": "31–60일: 역량 심화",
        "actions": [
          "HR 데이터 분석 포트폴리오 작성",
          "채용 KPI 대시보드 구축 경험"
        ]
      },
      {
        "phase": 3,
        "label": "61–90일: 지원 준비",
        "actions": [
          "목표 직무 이력서 최종 수정",
          "타겟 기업 3–5개 선정 및 지원"
        ]
      }
    ]
  }
}
```

---

### `reportSections`

PDF 렌더링 순서 제어용. 각 섹션은 활성화 여부와 순서를 가진다.

```json
{
  "reportSections": [
    { "section_id": "cover",           "order": 1,  "enabled": true },
    { "section_id": "executive_summary","order": 2, "enabled": true },
    { "section_id": "career_profile",  "order": 3,  "enabled": true },
    { "section_id": "target_job",      "order": 4,  "enabled": true },
    { "section_id": "market_intel",    "order": 5,  "enabled": true },
    { "section_id": "skill_mapping",   "order": 6,  "enabled": true },
    { "section_id": "evidence_mapping","order": 7,  "enabled": true },
    { "section_id": "fit_score",       "order": 8,  "enabled": true },
    { "section_id": "strength_analysis","order": 9, "enabled": true },
    { "section_id": "gap_analysis",    "order": 10, "enabled": true },
    { "section_id": "recommendation",  "order": 11, "enabled": true },
    { "section_id": "roadmap",         "order": 12, "enabled": true },
    { "section_id": "final_assessment","order": 13, "enabled": true }
  ]
}
```