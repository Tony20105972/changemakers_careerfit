# 03 — Entity Relationship Diagram (ERD)

**DB:** PostgreSQL
**Extensions:** `uuid-ossp`

> **v3.1 핵심 변경:** `reports.target_job_family`(ENUM) → `reports.primary_profile`(TEXT).  
> `job_requirement_stats`의 `job_family` ENUM 컬럼을 `profile_key`(TEXT, N개 좌표축 식별자)로  
> 변경 — N은 더 이상 ENUM으로 고정되지 않으며, `job_requirement_profiles` 테이블의  
> row 추가로 확장 가능.
>
> **Schema-First 원칙:** 이 ERD는 `05_REPORT_SCHEMA.md`에서 정의한 Report JSON 구조를  
> 저장하기 위해 역방향으로 도출되었다.

---

## 0. Report JSON → 테이블 도출 매핑 (v3 갱신)

| Report JSON 섹션 | 저장 위치 |
|-------------------|-----------|
| 전체 Report JSON | `reports.report_json` (JSONB, 완성본 그대로) |
| **`meta.primary_profile`** | **`reports.primary_profile` (TEXT, v3.1 신규)** |
| **`meta.secondary_profiles`** | **`reports.secondary_profiles` (TEXT[], v3.1 신규, optional)** |
| `meta.weight_source`, `meta.confidence_level` | `reports` 컬럼 (v3 신규) |
| `meta`, `summary` (기타) | `reports` 테이블 컬럼 일부 + `report_scores` |
| `careerProfile` (extracted_skills 제외) | `career_histories` |
| `evidenceMapping` | `career_evidences` |
| **`targetJobAnalysis.unique_requirements`/`common_requirements`** | **`requirement_matches`** (primary_profile 기준 결과, `source_profiles` 포함) |
| **N개 좌표축 자체 (`profile_pool`)** | **`job_requirement_profiles`** (v3 신규 테이블, ENUM 대체) |
| `skillMapping`, `scores.breakdown` | `requirement_matches` |
| `scores.total`, `unique_total`, `common_total`, `core_penalty` | `report_scores` |
| `gaps` | `report_gaps` |
| `strengths`, `recommendations`, `roadmap` | `reports.report_json`에만 저장 |

---

## 1. ER Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                  CareerFit V3.1 ERD (Primary Profile)                     │
└──────────────────────────────────────────────────────────────────────────┘

 ┌──────────────┐         ┌──────────────────────────┐
 │    users     │         │  job_requirement_profiles │  ← v3 신규 (ENUM 대체)
 │──────────────│         │───────────────────────────│
 │ id (PK)      │         │ id (PK)                   │
 │ session_id   │         │ profile_key  (TEXT, UNIQUE)│ ◄──────────────┐
 │ created_at   │         │ label_ko                   │                │
 └──────┬───────┘         │ requirement_key            │                │
        │ 1               │ skill_group  (UNIQUE|COMMON)│                │
        │                 │ weight                      │                │
        │ N               │ is_core                     │                │
 ┌──────▼───────────────┐ │ description                 │                │
 │       reports        │ │ status (ACTIVE|DEPRECATED)  │                │
 │──────────────────────│ └─────────────────────────────┘                │
 │ id (PK, UUID)        │                                                  │
 │ user_id (FK→users)   │                                                  │
 │ primary_profile TEXT │──────────────────────────────────────────────────┘
 │ secondary_profiles TEXT[]
 │ weight_source        │
 │ confidence_level     │
 │ status               │
 │ report_json (JSONB)  │
 │ pdf_url               │
 │ error_message         │
 │ created_at            │
 │ completed_at          │
 │ expires_at            │
 └──────┬───────────────┘
        │ 1
        │
        ├─────────────────────────────────────────────┐
        │ N                                           │ 1
 ┌──────▼──────────────────┐             ┌────────────▼────────────┐
 │    career_histories      │             │     report_scores       │
 │──────────────────────────│             │─────────────────────────│
 │ id (PK)                  │             │ id (PK)                 │
 │ report_id (FK→reports)   │             │ report_id (FK→reports)  │
 │ company_name             │             │ total_score              │
 │ title                     │             │ unique_total             │
 │ start_date                │             │ common_total             │
 │ end_date                  │             │ core_penalty             │
 │ is_current                │             │ score_breakdown (JSONB)  │
 │ responsibilities (TEXT)   │             │ calculated_at            │
 │ achievements (TEXT)       │             └─────────────────────────┘
 │ sort_order                │
 └──────┬────────────────────┘
        │ 1
        │ N
 ┌──────▼──────────────────┐
 │   career_evidences        │
 │───────────────────────────│
 │ id (PK)                   │
 │ career_history_id (FK)    │ ── nullable (v3: target_priority_text 유래 시 NULL)
 │ report_id (FK→reports)    │
 │ skill_key                  │
 │ original_text (TEXT)       │
 │ evidence_type               │
 │ confidence_score            │
 │ source (career_history|target_priority_text)  ← v3 신규
 │ created_at                  │
 └─────────────────────────────┘

 ┌────────────────────────────────────────────────────┐
 │              requirement_matches                    │
 │──────────────────────────────────────────────────--│
 │ id (PK)                                            │
 │ report_id (FK→reports)                             │
 │ requirement_key                                    │
 │ skill_group        (UNIQUE|COMMON)                  │
 │ weight             (primary_profile requirement)       │
 │ source_profiles    (TEXT[], v3 신규)                │
 │ match_level  (FULL/STRONG/PARTIAL/WEAK/NONE)        │
 │ match_score                                        │
 │ confidence_total                                   │
 │ matched_evidence_ids (UUID[])                      │
 │ reasoning (TEXT)                                   │
 └─────────────────────────────────────────────────--┘

 ┌─────────────────────────────────────────────────┐
 │                 report_gaps                      │
 │─────────────────────────────────────────────────│
 │ id (PK)                                          │
 │ report_id (FK→reports)                           │
 │ requirement_key                                  │
 │ skill_group       (UNIQUE|COMMON)                 │
 │ gap_severity   (CRITICAL/MAJOR/MINOR)            │
 │ gap_reason (TEXT)                                │
 │ recommendation (TEXT)                            │
 │ priority_order (INT)                             │
 └─────────────────────────────────────────────────┘
```

---

## 2. 테이블 상세 정의

### 2.1 `users`

익명 사용자 추적용. (변경 없음)

```sql
CREATE TABLE users (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id  TEXT        NOT NULL UNIQUE,
    ip_hash     TEXT,
    user_agent  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_session_id ON users(session_id);
```

---

### 2.2 `reports` (v3 변경)

```sql
CREATE TYPE report_status AS ENUM (
    'CREATED',
    'ANALYZING',
    'PDF_GENERATING',
    'READY',
    'FAILED'
);

-- v3: job_family ENUM 삭제. weight_source, confidence_level ENUM 신규.
CREATE TYPE weight_source_type AS ENUM (
    'MANUAL_V1'
    -- 향후: 'CRAWLED_2026Q3' 등은 TEXT로 유연하게 관리하기 위해
    -- 실제로는 ENUM이 아닌 TEXT + CHECK 제약을 권장 (아래 DDL 참조)
);

CREATE TYPE confidence_level_type AS ENUM ('HIGH', 'MEDIUM', 'LOW');

CREATE TABLE reports (
    id                UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id           UUID            REFERENCES users(id) ON DELETE SET NULL,
    -- target_job_family job_family NOT NULL,  -- v3: 제거
    primary_profile   TEXT,           -- v3.1 신규. 예: 'hr'. ANALYZING 완료 후 채워짐
    secondary_profiles TEXT[]         NOT NULL DEFAULT '{}',
    weight_source     TEXT            NOT NULL DEFAULT 'MANUAL_V1'
                       CHECK (weight_source ~ '^(MANUAL_V1|CRAWLED_\d{4}Q[1-4])$'),
    confidence_level  confidence_level_type,  -- ANALYZING 완료 후 채워짐
    status            report_status   NOT NULL DEFAULT 'CREATED',
    report_json       JSONB,
    pdf_url           TEXT,
    error_message     TEXT,
    retry_count       INT             NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    completed_at      TIMESTAMPTZ,
    expires_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW() + INTERVAL '30 days'
);

CREATE INDEX idx_reports_user_id    ON reports(user_id);
CREATE INDEX idx_reports_status     ON reports(status);
CREATE INDEX idx_reports_expires_at ON reports(expires_at);
CREATE INDEX idx_reports_json       ON reports USING GIN (report_json);
CREATE INDEX idx_reports_primary_profile ON reports(primary_profile);  -- v3.1 신규
```

> `weight_source`를 ENUM이 아닌 `TEXT + CHECK`로 둔 이유: 트랙 2(공고 기반 weight)가  
> 분기별로 새 값(`CRAWLED_2026Q1`, `CRAWLED_2026Q2`, ...)을 추가하는데, ENUM 값 추가보다  
> TEXT+CHECK가 마이그레이션 부담이 적다.

**상태 전이:** (변경 없음)
```
CREATED → ANALYZING → PDF_GENERATING → READY
                ↘                   ↘
                FAILED             FAILED
```

---

### 2.3 `career_histories`

(변경 없음 — v2와 동일)

```sql
CREATE TABLE career_histories (
    id                UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id         UUID        NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    company_name      TEXT        NOT NULL,
    title             TEXT        NOT NULL,
    start_date        DATE        NOT NULL,
    end_date          DATE,
    is_current        BOOLEAN     NOT NULL DEFAULT FALSE,
    responsibilities  TEXT        NOT NULL,
    achievements      TEXT,
    sort_order        INT         NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_career_histories_report_id ON career_histories(report_id);
```

---

### 2.4 `career_evidences` (v3 변경)

```sql
CREATE TYPE evidence_type AS ENUM (
    'EXPLICIT',
    'INFERRED',
    'ACHIEVED'
);

CREATE TYPE evidence_source AS ENUM (
    'career_history',
    'target_priority_text'  -- v3 신규
);

CREATE TABLE career_evidences (
    id                  UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id           UUID            NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    career_history_id   UUID            REFERENCES career_histories(id) ON DELETE CASCADE,
        -- v3: NULL 허용. target_priority_text 유래 evidence는 특정 career_history에
        -- 속하지 않으므로 NULL.
    skill_key           TEXT            NOT NULL,
    original_text       TEXT            NOT NULL,
    evidence_type       evidence_type   NOT NULL,
    source              evidence_source NOT NULL DEFAULT 'career_history',  -- v3 신규
    confidence_score    NUMERIC(3,2)    NOT NULL CHECK (confidence_score BETWEEN 0 AND 1),
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_career_history_required
        CHECK (
            (source = 'career_history' AND career_history_id IS NOT NULL)
            OR (source = 'target_priority_text' AND career_history_id IS NULL)
        )
);

CREATE INDEX idx_career_evidences_report_id ON career_evidences(report_id);
CREATE INDEX idx_career_evidences_skill_key ON career_evidences(skill_key);
```

---

### 2.5 `job_requirement_profiles` (v3 신규 — ENUM 기반 `job_requirement_stats` 대체)

각 profile의 requirement 정의. **이 테이블의 row가 곧 primary_profile 선택 후 scoring 기준이다.**

```sql
CREATE TYPE skill_group AS ENUM ('UNIQUE', 'COMMON');
CREATE TYPE profile_status AS ENUM ('ACTIVE', 'DEPRECATED');

CREATE TABLE job_requirement_profiles (
    id              SERIAL          PRIMARY KEY,
    profile_key     TEXT            NOT NULL,   -- 'hr', 'marketing', 'data', ... (ENUM 아님, TEXT)
    requirement_key TEXT            NOT NULL,
    skill_group     skill_group     NOT NULL,
    label_ko        TEXT            NOT NULL,
    weight          NUMERIC(5,4)    NOT NULL CHECK (weight BETWEEN 0 AND 1),
    is_core         BOOLEAN         NOT NULL DEFAULT FALSE,
    description     TEXT,
    status          profile_status  NOT NULL DEFAULT 'ACTIVE',  -- v3: N 확장 시 후보를 ACTIVE 전환
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    UNIQUE (profile_key, requirement_key)
);

CREATE INDEX idx_job_req_profiles_profile_key ON job_requirement_profiles(profile_key);
CREATE INDEX idx_job_req_profiles_status ON job_requirement_profiles(profile_key, status);
```

**weight 규칙 (06_SCORING_RULES.md §2 — 변경 없음, 좌표축 생성 시 적용):**

```sql
-- status='ACTIVE'인 각 profile_key에 대해:
--   SUM(weight) WHERE skill_group='UNIQUE' = 0.65  (±0.001 허용)
--   SUM(weight) WHERE skill_group='COMMON' = 0.35  (±0.001 허용)

SELECT profile_key, skill_group, ROUND(SUM(weight), 4) AS weight_sum
FROM job_requirement_profiles
WHERE status = 'ACTIVE'
GROUP BY profile_key, skill_group
ORDER BY profile_key, skill_group;
```

**v2 → v3 마이그레이션:**

```sql
-- v2의 job_requirement_stats (job_family ENUM 기반)를
-- job_requirement_profiles (profile_key TEXT 기반)로 옮긴다.
-- ENUM 값(예: 'HR')을 소문자 TEXT('hr')로 변환.

INSERT INTO job_requirement_profiles
  (profile_key, requirement_key, skill_group, label_ko, weight, is_core, description, status)
SELECT
  LOWER(job_family::TEXT), requirement_key, skill_group, label_ko, weight, is_core, description, 'ACTIVE'
FROM job_requirement_stats;

-- 기존 job_requirement_stats, job_family ENUM 타입은 보존하거나 폐기 가능
-- (profile selection/scoring 코드는 job_requirement_profiles만 참조)
```

> `data/job_requirements_*.json` 10개 (`13_Development_Roadmap.md` Day 6 산출물)는  
> 그대로 이 테이블의 시딩 데이터로 사용된다 — 파일 → row 변환 외 추가 작업 없음.

---

### 2.6 `report_scores`

(변경 없음 — v2와 동일. `score_breakdown`은 primary_profile 결과 반영)

```sql
CREATE TABLE report_scores (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id       UUID        NOT NULL UNIQUE REFERENCES reports(id) ON DELETE CASCADE,
    total_score     NUMERIC(5,2) NOT NULL CHECK (total_score BETWEEN 0 AND 100),
    unique_total    NUMERIC(5,2) NOT NULL CHECK (unique_total BETWEEN 0 AND 65),
    common_total    NUMERIC(5,2) NOT NULL CHECK (common_total BETWEEN 0 AND 35),
    core_penalty    NUMERIC(5,2) NOT NULL DEFAULT 0,
    score_breakdown JSONB       NOT NULL,
    calculated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_total_matches_parts
        CHECK (total_score = ROUND(unique_total + common_total, 1))
);
```

---

### 2.7 `requirement_matches` (v3 변경)

```sql
CREATE TYPE match_level AS ENUM ('FULL', 'STRONG', 'PARTIAL', 'WEAK', 'NONE');

CREATE TABLE requirement_matches (
    id                      UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id               UUID        NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    requirement_key         TEXT        NOT NULL,
    skill_group             skill_group NOT NULL,
    weight                  NUMERIC(5,4) NOT NULL,  -- v3.1: primary_profile requirement
    source_profiles         TEXT[]      NOT NULL DEFAULT '{}',  -- v3 신규
    match_level             match_level NOT NULL,
    match_score             NUMERIC(3,2) NOT NULL,
    confidence_total        NUMERIC(4,2) NOT NULL DEFAULT 0,
    matched_evidence_ids    UUID[]      NOT NULL DEFAULT '{}',
    reasoning               TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (report_id, requirement_key)
);

CREATE INDEX idx_req_matches_report_id ON requirement_matches(report_id);
```

> `requirement_matches.weight`는 v2에서 `job_requirement_stats.weight`를 그대로 참조하던 것과 달리,  
> v3.1에서는 `primary_profile`의 requirement weight를 계산 결과와 함께 저장한다.  
> profile registry 변경 후에도 과거 리포트 점수가 재현되도록 weight를 컬럼으로 직접 저장한다.

---

### 2.8 `report_gaps`

(변경 없음 — v2와 동일)

```sql
CREATE TYPE gap_severity AS ENUM ('CRITICAL', 'MAJOR', 'MINOR');

CREATE TABLE report_gaps (
    id                  UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id           UUID            NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    requirement_key     TEXT            NOT NULL,
    skill_group         skill_group     NOT NULL,
    gap_severity        gap_severity    NOT NULL,
    gap_reason          TEXT            NOT NULL,
    recommendation      TEXT            NOT NULL,
    priority_order      INT             NOT NULL,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    UNIQUE (report_id, requirement_key)
);

CREATE INDEX idx_report_gaps_report_id ON report_gaps(report_id);
```

---

## 3. 관계 요약

```
users                    1 ──── N   reports
reports                  1 ──── N   career_histories
reports                  1 ──── N   career_evidences
reports                  1 ──── 1   report_scores
reports                  1 ──── N   requirement_matches
reports                  1 ──── N   report_gaps
career_histories         1 ──── N   career_evidences (nullable FK, v3)
job_requirement_profiles N ─── (참조, FK 아님) ─── requirement_matches.requirement_key
job_requirement_profiles N ─── (profile 선택 입력) ─── reports.primary_profile (profile_key 매칭)
```

> `reports.primary_profile`은 `job_requirement_profiles.profile_key`를 가리키지만,  
> profile registry가 데이터 시딩으로 관리되므로 애플리케이션 레벨에서 존재를 검증한다.

---

## 4. 데이터 흐름 (v3)

```
[사용자 입력]
    │  career_histories + target_priority_text
    ▼
career_histories (원문 저장) + career_evidences (target_priority_text 유래분, career_history_id=NULL)
    │
    ▼ Evidence 추출 엔진 (08_EVIDENCE_RULES.md, 입력 소스 2개)
    │
career_evidences (skill_key 매핑, confidence_score, source)
    │
    ▼ user_vector = {skill_key: confidence_total} 집계
    │
    ▼ job_requirement_profiles 전체(status='ACTIVE') 조회 → N개 좌표축 벡터
    │
    ▼ profile selector (06_SCORING_RULES.md §2.5)
    │   target_priority_text hint + profile별 evidence signal
    │   → primary_profile, secondary_profiles
    │   → selected_requirements (primary_profile 65/35)
    │
    ├──► reports.primary_profile / secondary_profiles 저장
    │
    ▼ 매칭 엔진 (selected_requirements 기준)
    │
requirement_matches (match_level, weight=primary_profile requirement, source_profiles, confidence_total)
    │
    ├──► report_scores (unique_total/common_total/core_penalty 집계)
    │
    └──► report_gaps (severity 분류)
              │
              ▼
        report_json (05_REPORT_SCHEMA.md 구조로 직렬화, meta.primary_profile 포함)
              │
              ▼
        reports.report_json (JSONB 저장, status=READY)
```

---

## 5. Migration 순서 (v3)

```sql
1.  CREATE TYPE report_status
2.  CREATE TYPE evidence_type
3.  CREATE TYPE evidence_source        -- v3 신규
4.  CREATE TYPE skill_group
5.  CREATE TYPE profile_status         -- v3 신규
6.  CREATE TYPE match_level
7.  CREATE TYPE gap_severity
8.  CREATE TYPE confidence_level_type  -- v3 신규
9.  CREATE TABLE users
10. CREATE TABLE reports               -- v3.1: primary_profile, secondary_profiles, weight_source, confidence_level
11. CREATE TABLE career_histories
12. CREATE TABLE career_evidences      -- v3: source 컬럼, career_history_id nullable
13. CREATE TABLE job_requirement_profiles  -- v3 신규 (job_requirement_stats + job_family ENUM 대체)
14. CREATE TABLE report_scores
15. CREATE TABLE requirement_matches   -- v3: weight, source_profiles 컬럼
16. CREATE TABLE report_gaps
```

> `job_family` ENUM(10개 값)은 더 이상 생성하지 않는다. `profile_key`는 TEXT로,  
> N=10이 `job_requirement_profiles`의 row 10×9=90개로 시딩된다 (Day 6 산출물 재사용).

---

## 6. 인덱스 전략 (v3 갱신)

| 인덱스 | 목적 |
|--------|------|
| `reports.status` | 폴링 쿼리 |
| `reports.expires_at` | 만료 정리 배치 |
| `reports.report_json` (GIN) | JSONB 내부 검색 |
| **`reports.primary_profile` (v3.1 신규)** | 대표 프로필별 리포트 분포 분석 |
| `career_evidences.skill_key` | 스킬별 Evidence 집계 |
| `requirement_matches.report_id` | 리포트별 매칭 결과 조회 |
| `job_requirement_profiles(profile_key, status)` | weight 합계 검증 쿼리, profile selection 시 ACTIVE 프로필만 로드 |

---

## 7. 알려진 문제점 (§ Limitations)

| 문제 | 영향 | 비고 |
|------|------|------|
| `requirement_matches.weight`를 매 리포트마다 저장 (v2는 FK 참조로 충분) | 저장 공간 소폭 증가 (리포트당 4~6 UNIQUE + 5 COMMON ≈ 9~11 row) | N=10, 사용자 월 20~30명 규모에서는 무시할 수준 |
| `reports.primary_profile`이 `job_requirement_profiles.profile_key`를 참조하지만 FK 미적용 | `profile_key`가 오타/누락되어도 DB 레벨에서 감지 안 됨 | 애플리케이션 레벨 검증 필수 |
| `job_requirement_profiles.status`(ACTIVE/DEPRECATED)는 있으나 `CANDIDATE`(검토 대기) 상태가 없음 | N 확장 시 "검토 중" 좌표축을 표현할 방법이 ERD에 없음 | V1에서는 N=10 고정이므로 미해당. N 확장 논의 시 `profile_status` ENUM에 `CANDIDATE` 추가 필요 (`01_PRD.md` §4.3) |
| `career_evidences.career_history_id` nullable화로 기존 NOT NULL 가정 코드가 있다면 깨질 수 있음 | v2 → v3 마이그레이션 시 애플리케이션 코드 점검 필요 | `chk_career_history_required` CHECK 제약으로 DB 레벨 방어는 되어 있음 |
