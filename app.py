"""
SESAM KMIS - Student Module V1 (with Login)
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

# ==================== USER AUTH ====================
USERS = {
    "staff1": {"password": "admin123", "role": "SESAM Staff"},
    "adviser1": {"password": "adv123", "role": "Faculty Adviser"},
    "adviser2": {"password": "adv456", "role": "Faculty Adviser"}
}

# ==================== LOGIN ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 SESAM KMIS Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = USERS[username]["role"]
            st.success("✅ Login successful")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

    st.stop()

# ==================== DATA LOADING ====================
DATA_FILE = "students.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame({
            "student_id": [],
            "name": [],
            "program": [],
            "advisor": [],
            "year_admitted": [],
            "pos_filed": [],
            "comp_exam": [],
            "proposal_defense": [],
            "thesis_submitted": [],
            "thesis_units_taken": []
        })
        df.to_csv(DATA_FILE, index=False)
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

role = st.session_state.role
username = st.session_state.username

st.sidebar.write(f"👤 {username}")
st.sidebar.write(f"🔑 {role}")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Version 1.1 | ISSP 2026-2031")

# ==================== MAIN ====================
st.title("🎓 SESAM Graduate Student Milestone Tracker")
st.markdown("*Centralized tracking system*")
st.markdown("---")

# ==================== STAFF VIEW ====================
if role == "SESAM Staff":

    st.subheader("📋 All Students")
    st.dataframe(df, use_container_width=True, height=400)

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
            st.metric("Advisor", student["advisor"])
            st.metric("Year Admitted", student["year_admitted"])
        with col3:
            limit = get_thesis_limit(student["program"])
            st.metric("Thesis Units", f"{student['thesis_units_taken']} / {limit}")
            if student["thesis_units_taken"] > limit:
                st.error("⚠️ Units exceeded!")

        with st.form("update_form"):
            milestone = st.selectbox(
                "Select Milestone",
                ["pos_filed", "comp_exam", "proposal_defense", "thesis_submitted", "thesis_units_taken"]
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

                new_status = st.selectbox("Status", options, index=options.index(current))
                if st.form_submit_button("Update"):
                    df.loc[df["student_id"] == student_id, milestone] = new_status
                    save_data(df)
                    st.success("Updated!")
                    st.rerun()

    # Stats
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
else:
    st.subheader(f"👨‍🏫 Your Advisees ({username})")

    advisees = df[df["advisor"] == username].copy()

    if len(advisees) == 0:
        st.warning("No assigned students.")
    else:
        advisees["units_status"] = advisees.apply(
            lambda row: get_warning_text(row["program"], row["thesis_units_taken"]),
            axis=1
        )

        st.dataframe(advisees, use_container_width=True)

        st.markdown("---")
        for _, row in advisees.iterrows():
            with st.expander(f"{row['name']} ({row['student_id']})"):
                st.write(f"Program: {row['program']}")
                st.write(f"Compre: {row['comp_exam']}")
                st.write(f"Proposal: {row['proposal_defense']}")
                st.write(f"Units: {get_warning_text(row['program'], row['thesis_units_taken'])}")

    st.info("Read-only access")

# ==================== FOOTER ====================
st.markdown("---")
st.caption("SESAM KMIS – Student Module V1 with Authentication")