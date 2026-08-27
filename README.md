# K-12 District Data Standards Simulator

A synthetic, fully de-identified demo of the kind of multi-district
reporting system a state education agency maintains — built to show
how a governed data model, standardized reporting, and role-based
access can work together, not just to show a dashboard.

**No real student, school, or district data is used anywhere in this
project.** All records are randomly generated (see `data/generate_data.py`).

---

## Why this project exists

Most portfolio dashboards show a chart. This one is built around a
different question: **if a state agency needed to combine reporting
from many independent districts into one trustworthy system, what
would that actually require?**

That's a data-standards problem before it's a dashboard problem —
which is the same framing behind systems like Kentucky's School Report
Card and Infinite Campus extracts. So this project treats the data
model, the documentation, and the access controls as first-class
deliverables, alongside the dashboard itself.

## What it demonstrates

| Capability | Where it shows up |
|---|---|
| Business requirements → data model | `sql/schema.sql` — a conformed star schema shared across enrollment, attendance, and assessment reporting |
| Data standards & documentation | `data_dictionary.md` — every field, valid values, and grain defined |
| Data governance / access control | `app.py` — a working row-level security simulation: a "District Admin" login only ever sees their own district's rows |
| Stakeholder-ready reporting | The dashboard's KPI and drill-down layout mirrors a School Report Card: enrollment, attendance, and assessment performance by school |
| Realistic synthetic data at scale | `data/generate_data.py` — ~6,700 students across 5 districts and 25 schools, with correlated (not random-looking) attendance and assessment patterns |

## The scenario, in plain terms

Imagine five independent school districts all need to report into one
state-level system. Each district admin should only ever see their own
district's data. A state-level analyst needs to see everything, across
all districts, to spot patterns and support policy decisions.

This project builds that system end-to-end:

1. **One shared data model** (`sql/schema.sql`) that every district's
   data loads into consistently — so a "Proficient" score or an
   "Absent-Excused" day means the same thing everywhere.
2. **Synthetic but realistic data** (`data/generate_data.py`) standing
   in for what would normally come from each district's student
   information system.
3. **A reporting layer** (`app.py`) with two roles:
   - **District Admin** — sees only their district, exactly as row-level
     security would enforce in a real multi-tenant reporting system.
   - **State (KDE) Analyst** — sees all districts, for state-level
     reporting and oversight.

## Try it yourself

```bash
pip install -r requirements.txt
python data/generate_data.py     # builds k12_simulator.db from scratch
streamlit run app.py             # launches the dashboard
```

Then, in the sidebar, switch between **"District Admin"** (pick a
district) and **"State (KDE) Analyst"** to see the row-level security
in action — the same student, school, and district-level KPIs reflow
to only the rows that role is allowed to see.

## Project structure

```
k12-data-standards-simulator/
├── app.py                  # Streamlit dashboard + row-level security logic
├── data/
│   └── generate_data.py    # Synthetic data generator
├── sql/
│   └── schema.sql          # Star-schema DDL with documentation comments
├── data_dictionary.md       # Full field-level data dictionary + governance notes
├── requirements.txt
└── README.md
```

## Design decisions worth calling out

- **Star schema over a single flat table.** Enrollment, attendance,
  and assessment are separate fact tables at different grains (per
  year, per school day, per subject) sharing conformed dimensions —
  the same pattern that keeps multi-source K-12 reporting internally
  consistent as new fact types get added later.
- **`district_key` denormalized onto every fact table.** This keeps
  the row-level security check a single, simple filter on each fact
  table, instead of requiring a join back through `dim_school` before
  security can be enforced — simpler to audit and harder to
  accidentally bypass.
- **No direct identifiers in `dim_student`.** Name, date of birth, and
  address are intentionally absent rather than masked — reflecting how
  a real system would keep identity data in a separate,
  access-controlled table joined only when explicitly authorized.

## What I'd build next

- A "data quality exceptions" view — flagging rows that fail the
  fixed-value checks described in the data dictionary, so bad loads
  get caught before they reach a report.
- A year-over-year comparison view, once multiple `school_year`
  values exist in the data.
