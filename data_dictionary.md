# Data Dictionary — K-12 District Data Standards Simulator

This document describes every table and field in the star-schema data
model, along with governance notes. It mirrors the kind of data
dictionary a state education agency would maintain alongside its
reporting systems, so that any analyst — not just the person who built
it — can trust and reuse the data correctly.

All data in this project is synthetic and randomly generated. No real
student, school, or district records are used at any point.

---

## Conventions

- All surrogate keys (`*_key` fields) are integers used only for joins
  within this database; they are not meaningful outside it.
- All natural/business identifiers (`*_id` fields) mimic state-assigned
  codes and are the fields you would map to an external system of
  record (e.g., Infinite Campus) in a real deployment.
- Fields with a fixed set of values ("Yes"/"No", performance levels,
  etc.) are called out explicitly below — any values outside this list
  in production data would indicate a data quality issue.

---

## Dimension Tables

### `dim_district`
One row per school district.

| Field | Type | Description |
|---|---|---|
| `district_key` | INTEGER (PK) | Surrogate key |
| `district_id` | TEXT | State-assigned district code |
| `district_name` | TEXT | District display name |
| `region` | TEXT | Reporting region |
| `superintendent` | TEXT | District superintendent name (synthetic) |

### `dim_school`
One row per school. A district has many schools.

| Field | Type | Description |
|---|---|---|
| `school_key` | INTEGER (PK) | Surrogate key |
| `school_id` | TEXT | State-assigned school code |
| `school_name` | TEXT | School display name |
| `district_key` | INTEGER (FK → dim_district) | Owning district |
| `school_level` | TEXT | One of: Elementary, Middle, High |
| `title_i_status` | TEXT | One of: Yes, No |

### `dim_student`
One row per student. Fully de-identified; no PII fields exist in this
model by design (see Governance Notes below).

| Field | Type | Description |
|---|---|---|
| `student_key` | INTEGER (PK) | Surrogate key |
| `student_id` | TEXT | De-identified state student ID |
| `grade_level` | TEXT | K, 1–12 |
| `gender` | TEXT | Reporting category |
| `ethnicity` | TEXT | Reporting category |
| `econ_disadvantaged` | TEXT | One of: Yes, No |
| `iep_status` | TEXT | One of: Yes, No — special education status |
| `ell_status` | TEXT | One of: Yes, No — English language learner status |

### `dim_date`
One row per calendar day across the school year, used to support
attendance and trend reporting.

| Field | Type | Description |
|---|---|---|
| `date_key` | INTEGER (PK) | YYYYMMDD integer key |
| `full_date` | TEXT | ISO date |
| `school_year` | TEXT | e.g., "2025-2026" |
| `quarter` | INTEGER | 1–4 |
| `month` | INTEGER | 1–12 |
| `day_of_week` | TEXT | Day name |
| `is_school_day` | TEXT | One of: Yes, No |

---

## Fact Tables

### `fact_enrollment`
Grain: **one row per student, per school, per school year.**

| Field | Type | Description |
|---|---|---|
| `enrollment_key` | INTEGER (PK) | Surrogate key |
| `student_key` | INTEGER (FK) | |
| `school_key` | INTEGER (FK) | |
| `district_key` | INTEGER (FK) | Denormalized for query performance and RLS filtering |
| `school_year` | TEXT | |
| `enrollment_status` | TEXT | One of: Active, Withdrawn, Transferred |

### `fact_attendance`
Grain: **one row per student, per school day** (sampled to a
representative subset of school days for this demo, rather than every
single day, to keep the dataset a reasonable size).

| Field | Type | Description |
|---|---|---|
| `attendance_key` | INTEGER (PK) | Surrogate key |
| `student_key` | INTEGER (FK) | |
| `school_key` | INTEGER (FK) | |
| `district_key` | INTEGER (FK) | Denormalized for RLS filtering |
| `date_key` | INTEGER (FK → dim_date) | |
| `attendance_status` | TEXT | One of: Present, Absent-Excused, Absent-Unexcused |

### `fact_assessment`
Grain: **one row per student, per subject, per school year.**

| Field | Type | Description |
|---|---|---|
| `assessment_key` | INTEGER (PK) | Surrogate key |
| `student_key` | INTEGER (FK) | |
| `school_key` | INTEGER (FK) | |
| `district_key` | INTEGER (FK) | Denormalized for RLS filtering |
| `school_year` | TEXT | |
| `subject` | TEXT | One of: Reading, Math, Science |
| `performance_level` | TEXT | One of: Novice, Apprentice, Proficient, Distinguished |
| `scale_score` | INTEGER | 1–100 synthetic scale score |

---

## Governance Notes

- **Denormalized `district_key` on fact tables.** Every fact table
  carries `district_key` directly, even though it's derivable through
  `school_key`. This is intentional: it lets row-level security be
  enforced with a single, simple predicate (`WHERE district_key IN
  (...)`) on every fact table, rather than requiring a join back
  through `dim_school` before a security filter can apply.
- **No direct identifiers.** `dim_student` intentionally excludes
  name, date of birth, and address fields. A production system would
  keep those in a separate, access-controlled identity table joined
  only when explicitly authorized — this model reflects that
  separation by simply not including them at all.
- **Fixed-value fields should be validated on load.** Any ETL process
  populating this model from a source system (e.g., Infinite Campus
  extracts) should validate incoming values against the fixed lists
  above and reject or quarantine rows that don't conform, rather than
  silently loading bad values into downstream reports.
