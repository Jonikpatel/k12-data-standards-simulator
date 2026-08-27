# Data Dictionary — K-12 District Data Standards Simulator

This document outlines the table schemas, field definitions, and data modeling design for the star-schema warehouse. It is structured to mirror state reporting standards, ensuring consistent metric definitions and join integrity across district reporting dashboards.

> **Note:** All data in this repository is synthetic and randomly generated. No personally identifiable information (PII) or real student records are used.

---

### Modeling Conventions

* **Surrogate Keys (`*_key`):** Auto-incrementing integer keys used strictly for internal warehouse joins and indexing.
* **Natural / Business Keys (`*_id`):** Formatted identifier strings simulating state agency and SIS codes (e.g., Infinite Campus / PowerSchool mappings).
* **Controlled Vocabularies:** Fields with predefined value lists (e.g., status flags, performance bands) must adhere to the exact accepted values below during ingestion.

---

### Dimension Tables

#### `dim_district`
One record per school district.

| Field | Type | Description |
| :--- | :--- | :--- |
| `district_key` | INTEGER (PK) | Warehouse surrogate primary key |
| `district_id` | TEXT | State-assigned unique district identifier |
| `district_name` | TEXT | District display name |
| `region` | TEXT | Geographic reporting region / cooperative |
| `superintendent` | TEXT | Assigned district lead (synthetic) |

#### `dim_school`
One record per individual school facility.

| Field | Type | Description |
| :--- | :--- | :--- |
| `school_key` | INTEGER (PK) | Warehouse surrogate primary key |
| `school_id` | TEXT | State-assigned school building code |
| `school_name` | TEXT | School facility display name |
| `district_key` | INTEGER (FK) | References `dim_district.district_key` |
| `school_level` | TEXT | `Elementary`, `Middle`, `High` |
| `title_i_status` | TEXT | `Yes`, `No` |

#### `dim_student`
De-identified student profile records.

| Field | Type | Description |
| :--- | :--- | :--- |
| `student_key` | INTEGER (PK) | Warehouse surrogate primary key |
| `student_id` | TEXT | Anonymized state-level student identifier |
| `grade_level` | TEXT | Grade placement (`K`, `1`–`12`) |
| `gender` | TEXT | Demographic reporting category |
| `ethnicity` | TEXT | Federal race/ethnicity reporting band |
| `econ_disadvantaged` | TEXT | Economic status indicator (`Yes`, `No`) |
| `iep_status` | TEXT | Special education / IEP flag (`Yes`, `No`) |
| `ell_status` | TEXT | English Language Learner flag (`Yes`, `No`) |

#### `dim_date`
Standard date spine covering the academic calendar year.

| Field | Type | Description |
| :--- | :--- | :--- |
| `date_key` | INTEGER (PK) | Integer date representation (`YYYYMMDD`) |
| `full_date` | TEXT | ISO calendar date (`YYYY-MM-DD`) |
| `school_year` | TEXT | Academic year label (e.g., `2025-2026`) |
| `quarter` | INTEGER | Academic/calendar quarter (`1`–`4`) |
| `month` | INTEGER | Calendar month number (`1`–`12`) |
| `day_of_week` | TEXT | Day name (`Monday`, `Tuesday`, etc.) |
| `is_school_day` | TEXT | Instructional day flag (`Yes`, `No`) |

---

### Fact Tables

#### `fact_enrollment`
*Grain: One row per student, per enrolled school, per school year.*

| Field | Type | Description |
| :--- | :--- | :--- |
| `enrollment_key` | INTEGER (PK) | Unique surrogate transaction key |
| `student_key` | INTEGER (FK) | References `dim_student.student_key` |
| `school_key` | INTEGER (FK) | References `dim_school.school_key` |
| `district_key` | INTEGER (FK) | Denormalized district key for RLS filtering |
| `school_year` | TEXT | Academic enrollment year |
| `enrollment_status` | TEXT | `Active`, `Withdrawn`, `Transferred` |

#### `fact_attendance`
*Grain: One row per student per sampled instructional day.*

| Field | Type | Description |
| :--- | :--- | :--- |
| `attendance_key` | INTEGER (PK) | Unique surrogate event key |
| `student_key` | INTEGER (FK) | References `dim_student.student_key` |
| `school_key` | INTEGER (FK) | References `dim_school.school_key` |
| `district_key` | INTEGER (FK) | Denormalized district key for RLS filtering |
| `date_key` | INTEGER (FK) | References `dim_date.date_key` |
| `attendance_status` | TEXT | `Present`, `Absent-Excused`, `Absent-Unexcused` |

#### `fact_assessment`
*Grain: One row per student, per tested subject, per school year.*

| Field | Type | Description |
| :--- | :--- | :--- |
| `assessment_key` | INTEGER (PK) | Unique surrogate test record key |
| `student_key` | INTEGER (FK) | References `dim_student.student_key` |
| `school_key` | INTEGER (FK) | References `dim_school.school_key` |
| `district_key` | INTEGER (FK) | Denormalized district key for RLS filtering |
| `school_year` | TEXT | Testing year |
| `subject` | TEXT | `Reading`, `Math`, `Science` |
| `performance_level` | TEXT | `Novice`, `Apprentice`, `Proficient`, `Distinguished` |
| `scale_score` | INTEGER | Scaled assessment score (`1`–`100`) |

---

### Architecture & Governance Notes

* **Direct RLS Partitioning:** `district_key` is intentionally maintained directly across all fact tables. This allows multi-tenant row-level security (RLS) predicates (`WHERE district_key = @user_district`) to execute directly against fact partitions without joining `dim_school` first.
* **De-identification by Design:** `dim_student` strips direct identifiers (first/last names, birth dates, home addresses, SSNs). In a live enterprise architecture, identity mapping resides in an isolated, encrypted master index.
* **ETL Quality Constraints:** Upstream staging pipelines reject or isolate non-conforming rows failing standard value sets before loading into reporting tables.
