-- =====================================================================
-- K-12 District Data Standards Simulator — Star Schema
-- Mirrors the structure a state education agency (e.g., Infinite Campus
-- consumers, School Report Card) would maintain: conformed dimensions
-- shared across enrollment, attendance, and assessment facts.
-- =====================================================================

-- ---------------------------------------------------------------------
-- DIMENSION TABLES
-- ---------------------------------------------------------------------

CREATE TABLE dim_district (
    district_key        INTEGER PRIMARY KEY,
    district_id         TEXT NOT NULL UNIQUE,   -- state-assigned district code
    district_name       TEXT NOT NULL,
    region              TEXT NOT NULL,          -- e.g., "Bluegrass", "Western KY"
    superintendent      TEXT
);

CREATE TABLE dim_school (
    school_key          INTEGER PRIMARY KEY,
    school_id           TEXT NOT NULL UNIQUE,   -- state-assigned school code
    school_name         TEXT NOT NULL,
    district_key        INTEGER NOT NULL REFERENCES dim_district(district_key),
    school_level        TEXT NOT NULL,          -- Elementary / Middle / High
    title_i_status      TEXT NOT NULL           -- Yes / No
);

CREATE TABLE dim_student (
    student_key         INTEGER PRIMARY KEY,
    student_id          TEXT NOT NULL UNIQUE,   -- de-identified state student ID
    grade_level         TEXT NOT NULL,
    gender               TEXT,
    ethnicity            TEXT,
    econ_disadvantaged  TEXT NOT NULL,          -- Yes / No, mirrors KDE reporting categories
    iep_status          TEXT NOT NULL,          -- Yes / No (special education)
    ell_status          TEXT NOT NULL           -- Yes / No (English language learner)
);

CREATE TABLE dim_date (
    date_key            INTEGER PRIMARY KEY,    -- YYYYMMDD
    full_date           TEXT NOT NULL,
    school_year         TEXT NOT NULL,          -- e.g., "2025-2026"
    quarter             INTEGER NOT NULL,
    month               INTEGER NOT NULL,
    day_of_week         TEXT NOT NULL,
    is_school_day       TEXT NOT NULL           -- Yes / No
);

-- ---------------------------------------------------------------------
-- FACT TABLES
-- ---------------------------------------------------------------------

-- Grain: one row per student, per school, per school year
CREATE TABLE fact_enrollment (
    enrollment_key      INTEGER PRIMARY KEY,
    student_key         INTEGER NOT NULL REFERENCES dim_student(student_key),
    school_key          INTEGER NOT NULL REFERENCES dim_school(school_key),
    district_key        INTEGER NOT NULL REFERENCES dim_district(district_key),
    school_year         TEXT NOT NULL,
    enrollment_status   TEXT NOT NULL           -- Active / Withdrawn / Transferred
);

-- Grain: one row per student, per school day
CREATE TABLE fact_attendance (
    attendance_key      INTEGER PRIMARY KEY,
    student_key         INTEGER NOT NULL REFERENCES dim_student(student_key),
    school_key          INTEGER NOT NULL REFERENCES dim_school(school_key),
    district_key        INTEGER NOT NULL REFERENCES dim_district(district_key),
    date_key            INTEGER NOT NULL REFERENCES dim_date(date_key),
    attendance_status   TEXT NOT NULL           -- Present / Absent-Excused / Absent-Unexcused
);

-- Grain: one row per student, per subject, per assessment window
CREATE TABLE fact_assessment (
    assessment_key       INTEGER PRIMARY KEY,
    student_key          INTEGER NOT NULL REFERENCES dim_student(student_key),
    school_key           INTEGER NOT NULL REFERENCES dim_school(school_key),
    district_key         INTEGER NOT NULL REFERENCES dim_district(district_key),
    school_year          TEXT NOT NULL,
    subject               TEXT NOT NULL,         -- Reading / Math / Science
    performance_level     TEXT NOT NULL,         -- Novice / Apprentice / Proficient / Distinguished
    scale_score            INTEGER NOT NULL
);

-- ---------------------------------------------------------------------
-- INDEXES to support common report filters (district, school, year)
-- ---------------------------------------------------------------------
CREATE INDEX idx_enr_district ON fact_enrollment(district_key, school_year);
CREATE INDEX idx_att_district ON fact_attendance(district_key, date_key);
CREATE INDEX idx_asm_district ON fact_assessment(district_key, school_year, subject);
