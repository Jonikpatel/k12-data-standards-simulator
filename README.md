# K-12 District Data Standards Simulator

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://k12-data-standards-simulator-jonikpatel.streamlit.app/)

An end-to-end multi-district reporting system demonstration modeling state-level education agency reporting. Focuses on governed data modeling, conformed star schemas, standardized metric definitions, and simulated row-level security (RLS) across district and state roles.

> **Note:** All student, school, and district records are synthetic and generated via `data/generate_data.py`. No real or personally identifiable information (PII) is used.

---

### Key Deliverables & Implementation

| Area | Component | Description |
| :--- | :--- | :--- |
| **Data Warehouse** | `sql/schema.sql` | Conformed star schema spanning enrollment, daily attendance, and annual assessment reporting grains. |
| **Data Standards** | `data_dictionary.md` | Field definitions, primary/foreign key mappings, and accepted value sets for all dimensions and facts. |
| **Access Control & RLS** | `app.py` | Role-based data access simulation enforcing tenant boundaries (District Admin vs. State Analyst). |
| **Stakeholder Reporting** | `app.py` | State report card layout visualizing performance, demographic breakdowns, and school-level drill-downs. |
| **Data Generation** | `data/generate_data.py` | Generates ~6,700 students across 5 districts and 25 schools with realistic demographic and attendance correlations. |

---

### System Architecture & Roles

1. **Shared Conformed Schema:** Fact tables (`fact_enrollment`, `fact_attendance`, `fact_assessment`) share conformed dimensions (`dim_district`, `dim_school`, `dim_student`, `dim_date`) ensuring standardized metric calculations across independent districts.
2. **Role-Based Access Control:**
   * **District Admin:** Scoped strictly to records matching their assigned district via partitioned filters.
   * **State (KDE) Analyst:** Full access across all districts for cross-district comparisons, statewide aggregate trends, and policy reporting.

---

### Project Structure

```text
k12-data-standards-simulator/
├── app.py                  # Streamlit reporting UI & role-based filter logic
├── data/
│   └── generate_data.py    # Synthetic dataset generator (~6,700 students)
├── sql/
│   └── schema.sql          # Star-schema DDL and foreign key definitions
├── data_dictionary.md       # Grain definitions, schema docs, and governance rules
├── requirements.txt        # Project dependencies
└── README.md
```
---

### Getting Started

1.**Clone the repository**

Bash
git clone [https://github.com/Jonikpatel/k12-data-standards-simulator.git](https://github.com/Jonikpatel/k12-data-standards-simulator.git)
cd k12-data-standards-simulator

2.**Set up a virtual environment**

Bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3.**Install dependencies**

Bash
pip install -r requirements.txt

4.**Generate the database**

Bash
python data/generate_data.py

5.**Run the application**

Bash
streamlit run app.py


### Architecture & Design Decisions

**Conformed Star Schema:** Distinct fact tables separate daily operational events (attendance), annual enrollment snapshots, and standardized assessment scoring while maintaining uniform dimensional joins.

**Denormalized district_key on Fact Tables:** Placing district_key directly on all fact records allows row-level security predicates (WHERE district_key = @user_district) to execute immediately without joining dimension tables.

**De-Identified Entity Modeling:** Direct identifiers (names, dates of birth, street addresses) are excluded from dim_student, mirroring state warehouse architectures where student identities are managed in separate, restricted credential stores.
