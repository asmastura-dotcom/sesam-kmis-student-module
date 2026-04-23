"""
SESAM KMIS - Student Module V1 (with Login and Sample Data)
Fixed for Streamlit Cloud deployment
Author: [Your Name]
Date: [Current Date]
"""

import streamlit as st
import pandas as pd
import os

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="SESAM Student Milestone Tracker",
    page_icon="🎓",
    layout="wide"
)

# ==================== INITIALIZE SESSION STATE ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None
if "display_name" not in st.session_state:
    st.session_state.display_name = None

# ==================== USER AUTH ====================
USERS = {
    "staff1": {"password": "admin123", "role": "SESAM Staff", "display_name": "SESAM Administrator"},
    "adviser1": {"password": "adv123", "role": "Faculty Adviser", "display_name": "Dr. Eslava"},
    "adviser2": {"password": "adv456", "role": "Faculty Adviser", "display_name": "Dr. Sanchez"},
    "student1": {"password": "stu123", "role": "Student", "display_name": "Juan Cruz"},
    "student2": {"password": "stu456", "role": "Student", "display_name": "Maria Santos"}
}

# ==================== LOGIN PAGE ====================
if not st.session_state.logged_in:
    st.title("🔐 SESAM KMIS Login")
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
    with col2:
        st.caption("Demo accounts:")
        st.caption("staff1 / admin123")
        st.caption("adviser1 / adv123")
        st.caption("student1 / stu123")

    if st.button("Login"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = USERS[username]["role"]
            st.session_state.display_name = USERS[username]["display_name"]
            st.success("✅ Login successful")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")
    st.stop()

# ==================== DATA LOADING WITH MIGRATION ====================
DATA_FILE = "students.csv"

def load_data():
    """Load or create student data with proper column names."""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # Check if required column 'advisor_username' exists; if not, try to migrate from old 'advisor' column
        if "advisor_username" not in df.columns:
            if "advisor" in df.columns:
                df["advisor_username"] = df["advisor"]
                df.drop(columns=["advisor"], inplace=True)
                save_data(df)
            else:
                # Fallback: create default data
                df = create_default_data()
    else:
        df = create_default_data()
    return df

def create_default_data():
    """Create sample data with advisor_username matching USERS keys."""
    df = pd.DataFrame({
        "student_id": ["S001", "S002", "S003", "S004", "S005"],
        "name": ["Juan Cruz", "Maria Santos", "Jose Rizal", "Ana Reyes", "Carlos Lopez"],
        "program": ["MS", "PhD", "MS", "PhD", "MS"],
        "advisor_username": ["adviser1", "adviser2", "adviser1", "adviser2", "adviser1"],
        "year_admitted": [2024, 2023, 2024, 2022, 2024],
        "pos_filed": ["Completed", "Completed", "Pending", "Completed", "Pending"],
        "comp_exam": ["Pending", "Passed", "Pending", "Passed", "Pending"],
        "proposal_defense": ["Pending", "Completed", "Pending", "Completed", "Pending"],
        "thesis_submitted": ["No", "No", "No", "Yes", "No"],
        "thesis_units_taken": [3, 8, 2, 12, 1]
    })
    return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def get_thesis_limit(program):
    return 6 if program == "MS" else 12

def get_warning_text(program, units):
    limit = get_thesis_limit(program)
    if units > limit:
        return f"⚠️ WARNING: {units}/{limit} units (exceeded by {units - limit})"
    return f"✅ {units}/{limit} units"

df = load_data()

# ==================== SIDEBAR ====================
st.sidebar.title("🎓 KMIS Student Module")
st.sidebar.markdown("---")
st.sidebar.write(f"👤 {st.session_state.display_name}")
st.sidebar.write(f"🔑 {st.session_state.role}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.display_name = None
    st.rerun()
st.sidebar.markdown("---")
st.sidebar.caption("Version 1.2 | ISSP 2026-2031")

# ==================== MAIN CONTENT ====================
st.title("🎓 SESAM Graduate Student Milestone Tracker")
st.markdown("*Centralized tracking for MS/PhD students*")
st.markdown("---")

role = st.session_state.role

# ==================== STAFF VIEW ====================
if role == "SESAM Staff":
    st.subheader("📋 All Students")
    # Use width='stretch' instead of deprecated use_container_width
    st.dataframe(df, width='stretch', height=400)

    st.markdown("---")
    st.subheader("✏️ Update Student Milestone")

    if len(df) > 0:
        student_id = st.selectbox("Select Student", df["student_id"])
        student = df[df["student_id"] == student_id].iloc[0]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Student", student["name"])
            st.metric("Program", student["program"])
        with col2:
            # Use advisor_username; map to display name if needed
            advisor_display = USERS.get(student["advisor_username"], {}).get("display_name", student["advisor_username"])
            st.metric("Advisor", advisor_display)
            st.metric("Year Admitted", student["year_admitted"])
        with col3:
            limit = get_thesis_limit(student["program"])
            st.metric("Thesis Units", f"{student['thesis_units_taken']} / {limit}")
            if student["thesis_units_taken"] > limit:
                st.error("⚠️ Units exceeded!")

        with st.form("update_form"):
            milestone = st.selectbox(
                "Select Milestone",
                ["pos_filed", "comp_exam", "proposal_defense", "thesis_submitted", "thesis_units_taken"],
                format_func=lambda x: {
                    "pos_filed": "Plan of Study (POS)",
                    "comp_exam": "Comprehensive Exam",
                    "proposal_defense": "Proposal Defense",
                    "thesis_submitted": "Thesis Submitted",
                    "thesis_units_taken": "Thesis Units Taken"
                }[x]
            )

            if milestone == "thesis_units_taken":
                new_units = st.number_input(
                    "New Units", min_value=0, max_value=20,
                    value=int(student["thesis_units_taken"]), step=1
                )
                if st.form_submit_button("Update"):
                    df.loc[df["student_id"] == student_id, "thesis_units_taken"] = new_units
                    save_data(df)
                    st.success("Updated!")
                    st.rerun()
            else:
                options_map = {
                    "pos_filed": ["Pending", "Completed"],
                    "comp_exam": ["Pending", "Passed", "Failed"],
                    "proposal_defense": ["Pending", "Completed", "Revisions Required"],
                    "thesis_submitted": ["No", "Yes"]
                }
                options = options_map[milestone]
                current = student[milestone]
                # Ensure current value is in options, else default to first
                index = options.index(current) if current in options else 0
                new_status = st.selectbox("Status", options, index=index)
                if st.form_submit_button("Update"):
                    df.loc[df["student_id"] == student_id, milestone] = new_status
                    save_data(df)
                    st.success("Updated!")
                    st.rerun()
    else:
        st.info("No students found. Add students via CSV or use the Add Student feature.")

    st.markdown("---")
    st.subheader("📊 Quick Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Students", len(df))
    with col2:
        st.metric("MS", len(df[df["program"] == "MS"]))
    with col3:
        st.metric("PhD", len(df[df["program"] == "PhD"]))

# ==================== ADVISER VIEW ====================
elif role == "Faculty Adviser":
    st.subheader(f"👨‍🏫 Your Advisees ({st.session_state.display_name})")
    advisees = df[df["advisor_username"] == st.session_state.username].copy()

    if len(advisees) == 0:
        st.warning("No students assigned to you.")
    else:
        advisees["units_status"] = advisees.apply(
            lambda row: get_warning_text(row["program"], row["thesis_units_taken"]),
            axis=1
        )
        display_cols = ["student_id", "name", "program", "year_admitted",
                        "pos_filed", "comp_exam", "proposal_defense",
                        "thesis_submitted", "thesis_units_taken", "units_status"]
        st.dataframe(advisees[display_cols], width='stretch')

        st.markdown("---")
        st.subheader("📌 Student Details")
        for _, row in advisees.iterrows():
            with st.expander(f"{row['name']} ({row['student_id']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Program:** {row['program']}")
                    st.write(f"**Year Admitted:** {row['year_admitted']}")
                    st.write(f"**POS Filed:** {row['pos_filed']}")
                with col2:
                    st.write(f"**Comprehensive Exam:** {row['comp_exam']}")
                    st.write(f"**Proposal Defense:** {row['proposal_defense']}")
                    st.write(f"**Thesis Submitted:** {row['thesis_submitted']}")
                st.write(f"**Thesis Units:** {get_warning_text(row['program'], row['thesis_units_taken'])}")
    st.info("📌 Read-only access. For updates, contact SESAM Staff.")

# ==================== STUDENT VIEW ====================
elif role == "Student":
    st.subheader(f"📘 Your Academic Progress ({st.session_state.display_name})")
    student_record = df[df["name"] == st.session_state.display_name]
    if len(student_record) == 0:
        st.error("Your record not found. Please contact SESAM Staff.")
    else:
        student = student_record.iloc[0]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Student ID", student["student_id"])
            st.metric("Program", student["program"])
        with col2:
            advisor_display = USERS.get(student["advisor_username"], {}).get("display_name", student["advisor_username"])
            st.metric("Advisor", advisor_display)
            st.metric("Year Admitted", student["year_admitted"])
        with col3:
            limit = get_thesis_limit(student["program"])
            st.metric("Thesis Units", f"{student['thesis_units_taken']} / {limit}")
            if student["thesis_units_taken"] > limit:
                st.error("⚠️ You have exceeded the allowed thesis units. Please consult your adviser.")

        st.markdown("---")
        st.subheader("📌 Your Milestone Status")
        milestone_df = pd.DataFrame({
            "Milestone": ["Plan of Study (POS)", "Comprehensive Exam", "Proposal Defense", "Thesis Submission"],
            "Status": [
                student["pos_filed"],
                student["comp_exam"],
                student["proposal_defense"],
                student["thesis_submitted"]
            ]
        })
        st.dataframe(milestone_df, width='stretch', hide_index=True)
        st.info("📌 Read-only view. For updates, contact your adviser or SESAM Staff.")

# ==================== FOOTER ====================
st.markdown("---")
st.caption("SESAM KMIS – Student Module V1 | Based on ISSP 2026-2031")