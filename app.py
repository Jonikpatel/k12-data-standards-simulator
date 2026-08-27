"""
app.py
======
K-12 District Data Standards Simulator — Report Card Dashboard

Simulates the kind of governed, multi-district reporting system a state
education agency maintains: a single shared data model, with row-level
security scoping each district admin's view to their own data, plus a
state-level "KDE Analyst" role that can see everything.

Run locally:
    streamlit run app.py
"""

import sqlite3
import os
import pandas as pd
import streamlit as st
import plotly.express as px

DB_PATH = os.path.join(os.path.dirname(__file__), "k12_simulator.db")

st.set_page_config(page_title="KY District Report Card Simulator", layout="wide")


# ---------------------------------------------------------------------
# Data access layer
# ---------------------------------------------------------------------
@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data
def load_districts():
    conn = get_connection()
    return pd.read_sql("SELECT district_key, district_id, district_name FROM dim_district ORDER BY district_name", conn)


@st.cache_data
def load_schools(district_keys):
    conn = get_connection()
    placeholders = ",".join("?" * len(district_keys))
    q = f"""
        SELECT school_key, school_id, school_name, district_key, school_level, title_i_status
        FROM dim_school
        WHERE district_key IN ({placeholders})
        ORDER BY school_name
    """
    return pd.read_sql(q, conn, params=district_keys)


@st.cache_data
def load_enrollment_summary(district_keys):
    conn = get_connection()
    placeholders = ",".join("?" * len(district_keys))
    q = f"""
        SELECT s.district_key, sc.school_name, sc.school_level, st.grade_level,
               st.econ_disadvantaged, st.iep_status, st.ell_status, e.enrollment_status
        FROM fact_enrollment e
        JOIN dim_student st ON st.student_key = e.student_key
        JOIN dim_school sc ON sc.school_key = e.school_key
        WHERE e.district_key IN ({placeholders})
    """
    return pd.read_sql(q, conn, params=district_keys)


@st.cache_data
def load_attendance_summary(district_keys):
    conn = get_connection()
    placeholders = ",".join("?" * len(district_keys))
    q = f"""
        SELECT a.district_key, sc.school_name, a.attendance_status
        FROM fact_attendance a
        JOIN dim_school sc ON sc.school_key = a.school_key
        WHERE a.district_key IN ({placeholders})
    """
    return pd.read_sql(q, conn, params=district_keys)


@st.cache_data
def load_assessment_summary(district_keys):
    conn = get_connection()
    placeholders = ",".join("?" * len(district_keys))
    q = f"""
        SELECT asm.district_key, sc.school_name, asm.subject, asm.performance_level, asm.scale_score
        FROM fact_assessment asm
        JOIN dim_school sc ON sc.school_key = asm.school_key
        WHERE asm.district_key IN ({placeholders})
    """
    return pd.read_sql(q, conn, params=district_keys)


# ---------------------------------------------------------------------
# Row-Level Security simulation
# ---------------------------------------------------------------------
st.sidebar.title("🔐 Access Control")
st.sidebar.caption("Simulates row-level security: district admins only ever query their own district's rows.")

districts_df = load_districts()

role = st.sidebar.radio("Sign in as:", ["State (KDE) Analyst", "District Admin"])

if role == "District Admin":
    chosen = st.sidebar.selectbox("District", districts_df["district_name"])
    allowed_district_keys = districts_df.loc[districts_df["district_name"] == chosen, "district_key"].tolist()
    st.sidebar.success(f"Scoped to: {chosen}")
else:
    allowed_district_keys = districts_df["district_key"].tolist()
    st.sidebar.info("State-level access: all districts visible")

# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------
st.title("📊 Kentucky District Report Card Simulator")
st.caption(
    "A synthetic, fully de-identified demo modeled on state K-12 reporting systems "
    "(e.g., School Report Card, Infinite Campus extracts). No real student or district data is used."
)

enrollment_df = load_enrollment_summary(allowed_district_keys)
attendance_df = load_attendance_summary(allowed_district_keys)
assessment_df = load_assessment_summary(allowed_district_keys)

# ---------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------
total_students = len(enrollment_df)
active_rate = (enrollment_df["enrollment_status"] == "Active").mean() * 100 if total_students else 0
attendance_rate = (attendance_df["attendance_status"] == "Present").mean() * 100 if len(attendance_df) else 0
proficient_rate = assessment_df["performance_level"].isin(["Proficient", "Distinguished"]).mean() * 100 if len(assessment_df) else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Students in View", f"{total_students:,}")
k2.metric("Active Enrollment Rate", f"{active_rate:.1f}%")
k3.metric("Attendance Rate", f"{attendance_rate:.1f}%")
k4.metric("Proficient or Distinguished", f"{proficient_rate:.1f}%")

st.divider()

# ---------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Enrollment by School")
    if total_students:
        enr_by_school = enrollment_df.groupby("school_name").size().reset_index(name="students")
        fig = px.bar(enr_by_school.sort_values("students", ascending=True), x="students", y="school_name", orientation="h")
        fig.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data in view.")

with col2:
    st.subheader("Attendance Status Breakdown")
    if len(attendance_df):
        att_counts = attendance_df["attendance_status"].value_counts().reset_index()
        att_counts.columns = ["status", "count"]
        fig = px.pie(att_counts, names="status", values="count", hole=0.45)
        fig.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data in view.")

col3, col4 = st.columns(2)

with col3:
    st.subheader("Assessment Performance by Subject")
    if len(assessment_df):
        perf_order = ["Novice", "Apprentice", "Proficient", "Distinguished"]
        perf_by_subject = (
            assessment_df.groupby(["subject", "performance_level"]).size().reset_index(name="students")
        )
        fig = px.bar(
            perf_by_subject, x="subject", y="students", color="performance_level",
            category_orders={"performance_level": perf_order}, barmode="stack",
        )
        fig.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data in view.")

with col4:
    st.subheader("Enrollment by Student Subgroup")
    if total_students:
        subgroup_data = pd.DataFrame({
            "Subgroup": ["Economically Disadvantaged", "IEP / Special Education", "English Language Learner"],
            "Share (%)": [
                (enrollment_df["econ_disadvantaged"] == "Yes").mean() * 100,
                (enrollment_df["iep_status"] == "Yes").mean() * 100,
                (enrollment_df["ell_status"] == "Yes").mean() * 100,
            ],
        })
        fig = px.bar(subgroup_data, x="Subgroup", y="Share (%)")
        fig.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data in view.")

st.divider()

# ---------------------------------------------------------------------
# School-level detail table (mirrors a "Report Card" drill-down)
# ---------------------------------------------------------------------
st.subheader("School-Level Detail")
if total_students:
    detail = (
        enrollment_df.groupby("school_name")
        .agg(students=("enrollment_status", "size"))
        .reset_index()
    )
    att_by_school = (
        attendance_df.assign(present=lambda d: d["attendance_status"] == "Present")
        .groupby("school_name")["present"].mean().mul(100).round(1).reset_index(name="attendance_rate_%")
    )
    asm_by_school = (
        assessment_df.assign(proficient=lambda d: d["performance_level"].isin(["Proficient", "Distinguished"]))
        .groupby("school_name")["proficient"].mean().mul(100).round(1).reset_index(name="proficient_rate_%")
    )
    merged = detail.merge(att_by_school, on="school_name", how="left").merge(asm_by_school, on="school_name", how="left")
    st.dataframe(merged, use_container_width=True, hide_index=True)
else:
    st.info("No data in view.")

st.caption(
    "Data standards note: this simulator models one conformed dimensional layer "
    "(district → school → student) shared across enrollment, attendance, and "
    "assessment facts — the same pattern used to keep multi-source K-12 reporting "
    "consistent and auditable."
)
