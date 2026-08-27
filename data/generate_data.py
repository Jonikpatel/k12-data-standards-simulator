"""
generate_data.py
================
Generates realistic, fully synthetic K-12 district/school/student data
and loads it into a star-schema SQLite database (see sql/schema.sql).

No real student or district data is used anywhere in this project.
All names, IDs, and records are randomly generated for demonstration
purposes only.

Usage:
    python data/generate_data.py
"""

import sqlite3
import random
import os
from datetime import date, timedelta
from faker import Faker

random.seed(42)
fake = Faker()
Faker.seed(42)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "k12_simulator.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "sql", "schema.sql")

SCHOOL_YEAR = "2025-2026"
SCHOOL_YEAR_START = date(2025, 8, 4)
SCHOOL_YEAR_END = date(2026, 5, 22)

REGIONS = ["Bluegrass", "Western Kentucky", "Eastern Kentucky", "Northern Kentucky", "South Central"]
SCHOOL_LEVELS = ["Elementary", "Middle", "High"]
ETHNICITIES = ["White", "Black or African American", "Hispanic or Latino", "Asian", "Two or More Races", "American Indian/Alaska Native"]
GENDERS = ["Male", "Female"]
GRADE_LEVELS_BY_LEVEL = {
    "Elementary": ["K", "1", "2", "3", "4", "5"],
    "Middle": ["6", "7", "8"],
    "High": ["9", "10", "11", "12"],
}
SUBJECTS = ["Reading", "Math", "Science"]
PERFORMANCE_LEVELS = ["Novice", "Apprentice", "Proficient", "Distinguished"]

N_DISTRICTS = 5
SCHOOLS_PER_DISTRICT = (3, 6)      # random range
STUDENTS_PER_SCHOOL = (150, 400)   # random range


def build_schema(conn):
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())


def weighted_choice(options, weights):
    return random.choices(options, weights=weights, k=1)[0]


def generate_districts(conn):
    rows = []
    for i in range(1, N_DISTRICTS + 1):
        rows.append((
            i,
            f"KY-{100 + i}",
            f"{fake.city()} Independent Schools",
            random.choice(REGIONS),
            fake.name(),
        ))
    conn.executemany(
        "INSERT INTO dim_district (district_key, district_id, district_name, region, superintendent) VALUES (?,?,?,?,?)",
        rows,
    )
    return rows


def generate_schools(conn, districts):
    rows = []
    school_key = 1
    school_map = []  # (school_key, district_key, school_level)
    for district_key, *_ in [(d[0],) for d in districts]:
        n_schools = random.randint(*SCHOOLS_PER_DISTRICT)
        for _ in range(n_schools):
            level = random.choice(SCHOOL_LEVELS)
            rows.append((
                school_key,
                f"SCH-{district_key:02d}{school_key:03d}",
                f"{fake.last_name()} {level} School",
                district_key,
                level,
                random.choices(["Yes", "No"], weights=[35, 65])[0],
            ))
            school_map.append((school_key, district_key, level))
            school_key += 1
    conn.executemany(
        "INSERT INTO dim_school (school_key, school_id, school_name, district_key, school_level, title_i_status) VALUES (?,?,?,?,?,?)",
        rows,
    )
    return school_map


def generate_students_and_enrollment(conn, school_map):
    student_rows = []
    enrollment_rows = []
    student_key = 1
    enrollment_key = 1
    student_school_map = []  # (student_key, school_key, district_key, grade_level)

    for school_key, district_key, level in school_map:
        n_students = random.randint(*STUDENTS_PER_SCHOOL)
        for _ in range(n_students):
            grade = random.choice(GRADE_LEVELS_BY_LEVEL[level])
            econ = weighted_choice(["Yes", "No"], [45, 55])
            iep = weighted_choice(["Yes", "No"], [15, 85])
            ell = weighted_choice(["Yes", "No"], [8, 92])

            student_rows.append((
                student_key,
                f"STU-{student_key:07d}",
                grade,
                random.choice(GENDERS),
                random.choice(ETHNICITIES),
                econ, iep, ell,
            ))

            status = weighted_choice(["Active", "Withdrawn", "Transferred"], [92, 4, 4])
            enrollment_rows.append((
                enrollment_key, student_key, school_key, district_key, SCHOOL_YEAR, status,
            ))

            student_school_map.append((student_key, school_key, district_key, grade))
            student_key += 1
            enrollment_key += 1

    conn.executemany(
        "INSERT INTO dim_student (student_key, student_id, grade_level, gender, ethnicity, econ_disadvantaged, iep_status, ell_status) VALUES (?,?,?,?,?,?,?,?)",
        student_rows,
    )
    conn.executemany(
        "INSERT INTO fact_enrollment (enrollment_key, student_key, school_key, district_key, school_year, enrollment_status) VALUES (?,?,?,?,?,?)",
        enrollment_rows,
    )
    return student_school_map


def generate_dates(conn):
    rows = []
    d = SCHOOL_YEAR_START
    while d <= SCHOOL_YEAR_END:
        is_school_day = "Yes" if d.weekday() < 5 else "No"
        quarter = 1 if d.month in (8, 9, 10) else 2 if d.month in (11, 12, 1) else 3 if d.month in (2, 3) else 4
        rows.append((
            int(d.strftime("%Y%m%d")),
            d.isoformat(),
            SCHOOL_YEAR,
            quarter,
            d.month,
            d.strftime("%A"),
            is_school_day,
        ))
        d += timedelta(days=1)
    conn.executemany(
        "INSERT INTO dim_date (date_key, full_date, school_year, quarter, month, day_of_week, is_school_day) VALUES (?,?,?,?,?,?,?)",
        rows,
    )
    return [r[0] for r in rows if r[6] == "Yes"]


def generate_attendance(conn, student_school_map, school_day_keys):
    # Sample a manageable number of school days per student (not every single day)
    # to keep the demo dataset a reasonable size while still showing real patterns.
    rows = []
    attendance_key = 1
    sample_days = random.sample(school_day_keys, k=min(40, len(school_day_keys)))

    for student_key, school_key, district_key, _grade in student_school_map:
        # Each student gets an individual "attendance risk" profile
        absence_rate = random.betavariate(2, 20)  # most students cluster low, some tail off high
        for date_key in sample_days:
            if random.random() < absence_rate:
                status = weighted_choice(["Absent-Excused", "Absent-Unexcused"], [60, 40])
            else:
                status = "Present"
            rows.append((attendance_key, student_key, school_key, district_key, date_key, status))
            attendance_key += 1

    conn.executemany(
        "INSERT INTO fact_attendance (attendance_key, student_key, school_key, district_key, date_key, attendance_status) VALUES (?,?,?,?,?,?)",
        rows,
    )


def generate_assessments(conn, student_school_map):
    rows = []
    assessment_key = 1
    for student_key, school_key, district_key, grade in student_school_map:
        if grade == "K":
            continue  # kindergarten typically not state-assessed
        # Each student gets a baseline ability that correlates across subjects
        baseline = random.gauss(0, 1)
        for subject in SUBJECTS:
            score = baseline + random.gauss(0, 0.6)
            scale_score = int(max(1, min(100, 50 + score * 15)))
            if scale_score < 40:
                level = "Novice"
            elif scale_score < 55:
                level = "Apprentice"
            elif scale_score < 75:
                level = "Proficient"
            else:
                level = "Distinguished"
            rows.append((
                assessment_key, student_key, school_key, district_key,
                SCHOOL_YEAR, subject, level, scale_score,
            ))
            assessment_key += 1

    conn.executemany(
        "INSERT INTO fact_assessment (assessment_key, student_key, school_key, district_key, school_year, subject, performance_level, scale_score) VALUES (?,?,?,?,?,?,?,?)",
        rows,
    )


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    build_schema(conn)

    print("Generating districts...")
    districts = generate_districts(conn)

    print("Generating schools...")
    school_map = generate_schools(conn, districts)

    print("Generating students and enrollment...")
    student_school_map = generate_students_and_enrollment(conn, school_map)

    print("Generating calendar dimension...")
    school_day_keys = generate_dates(conn)

    print("Generating attendance records (sampled school days)...")
    generate_attendance(conn, student_school_map, school_day_keys)

    print("Generating assessment records...")
    generate_assessments(conn, student_school_map)

    conn.commit()

    counts = {}
    for table in ["dim_district", "dim_school", "dim_student", "dim_date",
                  "fact_enrollment", "fact_attendance", "fact_assessment"]:
        counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    conn.close()

    print("\nDone. Row counts:")
    for table, count in counts.items():
        print(f"  {table:<20} {count:,}")
    print(f"\nDatabase written to: {os.path.abspath(DB_PATH)}")


if __name__ == "__main__":
    main()
