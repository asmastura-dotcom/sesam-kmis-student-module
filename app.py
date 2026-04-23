"""
SESAM KMIS - Student Module V1.2 (Add Student with Auto-Clear Form)
Author: [Your Name]
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

# ==================== SESSION STATE INIT ====================
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
}

# ==================== LOGIN ====================
if not st.session_state.logged_in:
    st.title("🔐 SESAM KMIS Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = USERS[username]["role"]
            st.session_state.display_name = USERS[username]["display_name"]
            st.success("✅ Login successful")
            st.rerun()
        else:
            st.error("❌ Invalid credentials")

    st.stop()

# ==================== DATA ====================
DATA_FILE = "students.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame({
            "student_id": ["S001"],
            "name": ["Sample Student"],
            "program": ["MS"],
            "advisor_username": ["adviser1"],
            "year_admitted": [2024],
            "pos_filed": ["Pending"],
            "comp_exam": ["Pending"],
            "proposal_defense": ["Pending"],
            "thesis_submitted": ["No"],
            "thesis_units_taken": [0]
        })
        df.to_csv(DATA_FILE, index=False)
        return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()

def get_limit(program):
    return 6 if program == "MS" else 12

def warning(program, units):
    limit = get_limit(program)
    return f"⚠️ {units}/{limit}" if units > limit else f"✅ {units}/{limit}"

# ==================== SIDEBAR ====================
st.sidebar.title("KMIS")
st.sidebar.write(st.session_state.display_name)
st.sidebar.write(st.session_state.role)

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

role = st.session_state.role

# ==================== STAFF VIEW ====================
if role == "SESAM Staff":

    st.title("🎓 Student Management")

    st.dataframe(df, use_container_width=True)

    # ================= UPDATE =================
    st.subheader("✏️ Update Student")

    if len(df) > 0:
        sid = st.selectbox("Select Student", df["student_id"])
        student = df[df["student_id"] == sid].iloc[0]

        st.write(f"Name: {student['name']}")

        with st.form("update_form"):
            field = st.selectbox(
                "Field",
                ["pos_filed", "comp_exam", "proposal_defense", "thesis_submitted", "thesis_units_taken"]
            )

            if field == "thesis_units_taken":
                value = st.number_input("Units", 0, 20, int(student["thesis_units_taken"]))
            else:
                value = st.text_input("Value", student[field])

            if st.form_submit_button("Update"):
                df.loc[df["student_id"] == sid, field] = value
                save_data(df)
                st.success("Updated!")
                st.rerun()

    # ================= ADD STUDENT =================
    st.markdown("---")
    st.subheader("➕ Add Student")

    with st.expander("Add New Student"):

        with st.form("add_student"):

            col1, col2 = st.columns(2)

            with col1:
                new_id = st.text_input("Student ID", key="new_id")
                new_name = st.text_input("Name", key="new_name")
                new_program = st.selectbox("Program", ["MS", "PhD"], key="new_program")
                new_adv = st.selectbox("Advisor", ["adviser1", "adviser2"], key="new_adv")
                new_year = st.number_input("Year", 2000, 2030, 2024, key="new_year")

            with col2:
                new_pos = st.selectbox("POS", ["Pending", "Completed"], key="new_pos")
                new_comp = st.selectbox("Comprehensive", ["Pending", "Passed", "Failed"], key="new_comp")
                new_prop = st.selectbox("Proposal", ["Pending", "Completed"], key="new_prop")
                new_thesis = st.selectbox("Thesis Submitted", ["No", "Yes"], key="new_thesis")
                new_units = st.number_input("Units", 0, 20, 0, key="new_units")

            submit = st.form_submit_button("➕ Add")

            if submit:

                if new_id in df["student_id"].values:
                    st.error("Student ID exists")
                elif not new_id or not new_name:
                    st.error("Required fields missing")
                else:

                    new_row = pd.DataFrame([{
                        "student_id": new_id,
                        "name": new_name,
                        "program": new_program,
                        "advisor_username": new_adv,
                        "year_admitted": new_year,
                        "pos_filed": new_pos,
                        "comp_exam": new_comp,
                        "proposal_defense": new_prop,
                        "thesis_submitted": new_thesis,
                        "thesis_units_taken": new_units
                    }])

                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)

                    st.toast("🎉 Student added successfully!", icon="✅")
                    st.balloons()

                    # ================= RESET FORM =================
                    st.session_state.new_id = ""
                    st.session_state.new_name = ""
                    st.session_state.new_program = "MS"
                    st.session_state.new_adv = "adviser1"
                    st.session_state.new_year = 2024
                    st.session_state.new_pos = "Pending"
                    st.session_state.new_comp = "Pending"
                    st.session_state.new_prop = "Pending"
                    st.session_state.new_thesis = "No"
                    st.session_state.new_units = 0

                    st.rerun()

# ==================== ADVISER VIEW ====================
elif role == "Faculty Adviser":

    st.title("👨‍🏫 Adviser View")

    my_students = df[df["advisor_username"] == st.session_state.username]

    st.dataframe(my_students, use_container_width=True)

# ==================== FOOTER ====================
st.markdown("---")
st.caption("SESAM KMIS V1.2 - Streamlit Prototype")
