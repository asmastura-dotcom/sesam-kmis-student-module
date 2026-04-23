"""
SESAM KMIS - Student Module V2 (Graduate School Rules Integration)
Author: Alyssa Fatmah S. Mastura
Date: April 23, 2026
Description: Tracks graduate student milestones, thesis units, exams, residency, LOA/AWOL, etc.
Based on UPLB Graduate School Policies, Rules and Regulations (2009).
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime, date

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="SESAM Graduate Student Tracker",
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

# ==================== DATA LOADING WITH ENHANCED SCHEMA ====================
DATA_FILE = "students.csv"

def create_default_data():
    """Create sample data with all required fields."""
    current_year = date.today().year
    return pd.DataFrame({
        "student_id": ["S001", "S002", "S003", "S004", "S005"],
        "name": ["Juan Cruz", "Maria Santos", "Jose Rizal", "Ana Reyes", "Carlos Lopez"],
        "program": ["MS", "PhD", "MS", "PhD", "MS"],
        "advisor_username": ["adviser1", "adviser2", "adviser1", "adviser2", "adviser1"],
        "year_admitted": [2024, 2023, 2024, 2022, 2024],
        # Plan of Study
        "pos_status": ["Approved", "Approved", "Pending", "Approved", "Pending"],
        "pos_submitted_date": ["2024-01-15", "2023-06-10", "", "2022-09-01", ""],
        "pos_approved_date": ["2024-02-01", "2023-07-01", "", "2022-09-15", ""],
        # Coursework
        "gwa": [1.75, 1.85, 2.10, 1.95, 2.05],
        "total_units_taken": [12, 18, 9, 24, 6],
        "total_units_required": [24, 24, 24, 24, 24],
        # Thesis / Dissertation
        "thesis_units_taken": [3, 8, 2, 12, 1],
        "thesis_units_limit": [6, 12, 6, 12, 6],
        "thesis_outline_approved": ["No", "Yes", "No", "Yes", "No"],
        "thesis_outline_approved_date": ["", "2024-01-10", "", "2023-11-20", ""],
        "thesis_status": ["In Progress", "Draft with Adviser", "Not Started", "Approved", "Not Started"],
        # Exams
        "qualifying_exam_status": ["N/A", "Passed", "N/A", "Passed", "N/A"],
        "qualifying_exam_passed_date": ["", "2023-12-01", "", "2023-10-15", ""],
        "written_comprehensive_status": ["N/A", "Passed", "N/A", "Passed", "N/A"],
        "written_comprehensive_passed_date": ["", "2024-02-10", "", "2024-01-20", ""],
        "oral_comprehensive_status": ["N/A", "Pending", "N/A", "Pending", "N/A"],
        "oral_comprehensive_passed_date": ["", "", "", "", ""],
        "general_exam_status": ["Pending", "N/A", "Pending", "N/A", "Pending"],
        "general_exam_passed_date": ["", "", "", "", ""],
        "final_exam_status": ["Pending", "Pending", "Pending", "Pending", "Pending"],
        "final_exam_passed_date": ["", "", "", "", ""],
        # Residency
        "residency_years_used": [1, 2, 1, 3, 1],
        "residency_max_years": [5, 7, 5, 7, 5],
        "extension_count": [0, 0, 0, 0, 0],
        "extension_end_date": ["", "", "", "", ""],
        # Leave
        "loa_start_date": ["", "", "", "", ""],
        "loa_end_date": ["", "", "", "", ""],
        "loa_total_terms": [0, 0, 0, 0, 0],
        "awol_status": ["No", "No", "No", "No", "No"],
        "awol_lifted_date": ["", "", "", "", ""],
        # Transfer credit
        "transfer_units_approved": [0, 0, 0, 0, 0],
        # Graduation
        "graduation_applied": ["No", "No", "No", "No", "No"],
        "graduation_approved": ["No", "No", "No", "No", "No"],
        "graduation_date": ["", "", "", "", ""],
        # Re-admission
        "re_admission_status": ["Not Applicable", "Not Applicable", "Not Applicable", "Not Applicable", "Not Applicable"],
        "re_admission_date": ["", "", "", "", ""]
    })

def load_data():
    """Load or create student data with proper schema."""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # Ensure all required columns exist; add missing with defaults
        default_df = create_default_data()
        for col in default_df.columns:
            if col not in df.columns:
                df[col] = default_df[col]
        # Save back to ensure consistency
        df.to_csv(DATA_FILE, index=False)
    else:
        df = create_default_data()
    return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def get_thesis_limit(program):
    return 6 if program == "MS" else 12

def get_residency_max(program):
    return 5 if program == "MS" else 7

# ==================== WARNING FUNCTIONS ====================
def get_warning_text(program, units_taken):
    limit = get_thesis_limit(program)
    if units_taken > limit:
        return f"⚠️ WARNING: {units_taken}/{limit} units (exceeded by {units_taken - limit})"
    return f"✅ {units_taken}/{limit} units"

def check_residency_warning(row):
    used = row["residency_years_used"]
    max_years = row["residency_max_years"]
    if used >= max_years:
        return f"⚠️ Residency limit reached ({used}/{max_years} years). Extension required."
    elif used >= max_years - 1:
        return f"⚠️ Approaching residency limit ({used}/{max_years} years)."
    return f"✅ {used}/{max_years} years used"

def check_gwa_warning(gwa):
    if gwa >= 2.0:
        return "✅ Good standing"
    else:
        return "⚠️ GWA below 2.00 – may affect exam eligibility and graduation"

def check_awol_warning(row):
    if row["awol_status"] == "Yes":
        return "⚠️ AWOL – registration privileges curtailed"
    return "✅ No AWOL"

def check_loa_warning(row):
    total_terms = row["loa_total_terms"]
    if total_terms > 2:
        return f"⚠️ LOA total exceeds 2 years ({total_terms} terms). Not allowed."
    elif total_terms > 0:
        return f"ℹ️ LOA total: {total_terms} term(s)"
    return "✅ No LOA"

def check_thesis_outline_deadline(row):
    if row["program"] == "MS" and row["thesis_units_taken"] > 0:
        # MS: outline must be approved not later than second semester of thesis enrollment
        # Simplified: if thesis units taken >= 4 and not approved, warn
        if row["thesis_units_taken"] >= 4 and row["thesis_outline_approved"] != "Yes":
            return "⚠️ Thesis outline approval overdue (should be approved by 2nd thesis semester)"
    elif row["program"] == "PhD" and row["thesis_units_taken"] > 0:
        # PhD: outline must be approved not later than third semester of dissertation enrollment
        if row["thesis_units_taken"] >= 8 and row["thesis_outline_approved"] != "Yes":
            return "⚠️ Dissertation outline approval overdue (should be approved by 3rd dissertation semester)"
    return "✅ Outline on track"

def check_qualifying_exam_deadline(row):
    if row["program"] == "PhD" and row["residency_years_used"] >= 1:
        # Qualifying exam should be taken before registration for second semester of residence
        if row["qualifying_exam_status"] not in ["Passed", "N/A"]:
            return "⚠️ Qualifying exam should be taken before 2nd semester of residence"
    return "✅ Qualifying exam on track"

def check_comprehensive_exam_deadline(row):
    if row["program"] == "PhD" and row["total_units_taken"] >= row["total_units_required"]:
        if row["written_comprehensive_status"] != "Passed":
            return "⚠️ Written comprehensive exam pending after completing coursework"
    return "✅ Comprehensive exam on track"

def get_all_warnings(row):
    warnings = []
    warnings.append(get_warning_text(row["program"], row["thesis_units_taken"]))
    warnings.append(check_residency_warning(row))
    warnings.append(check_gwa_warning(row["gwa"]))
    warnings.append(check_awol_warning(row))
    warnings.append(check_loa_warning(row))
    warnings.append(check_thesis_outline_deadline(row))
    warnings.append(check_qualifying_exam_deadline(row))
    warnings.append(check_comprehensive_exam_deadline(row))
    # Filter out duplicates and empty
    return [w for w in warnings if w and "✅" not in w] or ["✅ All rules satisfied"]

# Load data
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
st.sidebar.caption("Version 2.0 | ISSP 2026-2031 | Graduate School Rules")

# ==================== MAIN ====================
st.title("🎓 SESAM Graduate Student Milestone Tracker")
st.markdown("*Centralized tracking for MS/PhD students based on UPLB Graduate School Policies*")
st.markdown("---")

role = st.session_state.role

# ==================== STAFF VIEW (Full Edit) ====================
if role == "SESAM Staff":
    st.subheader("📋 All Students")
    st.dataframe(df, width='stretch', height=400)

    st.markdown("---")
    st.subheader("✏️ Update Student Record")

    if len(df) > 0:
        student_id = st.selectbox("Select Student", df["student_id"])
        student = df[df["student_id"] == student_id].iloc[0].copy()

        # Display warnings
        warnings = get_all_warnings(student)
        st.warning("\n".join(warnings)) if any("⚠️" in w for w in warnings) else st.success("\n".join(warnings))

        # Basic info display
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Student", student["name"])
            st.metric("Program", student["program"])
        with col2:
            advisor_display = USERS.get(student["advisor_username"], {}).get("display_name", student["advisor_username"])
            st.metric("Advisor", advisor_display)
            st.metric("Year Admitted", student["year_admitted"])
        with col3:
            limit = get_thesis_limit(student["program"])
            st.metric("Thesis Units", f"{student['thesis_units_taken']} / {limit}")
            if student["thesis_units_taken"] > limit:
                st.error("⚠️ Units exceeded!")

        # Editable fields organized in tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Coursework & Thesis", "Exams", "Residency & Leave", "Graduation", "Other"])

        with tab1:
            with st.form("coursework_form"):
                st.subheader("Plan of Study (POS)")
                pos_status = st.selectbox("POS Status", ["Not Filed", "Pending", "Approved"], index=["Not Filed","Pending","Approved"].index(student["pos_status"]))
                pos_submitted = st.text_input("POS Submitted Date (YYYY-MM-DD)", student["pos_submitted_date"])
                pos_approved = st.text_input("POS Approved Date (YYYY-MM-DD)", student["pos_approved_date"])

                st.subheader("Coursework")
                gwa = st.number_input("GWA", min_value=1.0, max_value=5.0, step=0.01, value=float(student["gwa"]))
                total_units_taken = st.number_input("Total Units Taken", min_value=0, max_value=60, step=1, value=int(student["total_units_taken"]))
                total_units_required = st.number_input("Total Units Required", min_value=0, max_value=60, step=1, value=int(student["total_units_required"]))

                st.subheader("Thesis/Dissertation")
                thesis_units_taken = st.number_input("Thesis Units Taken", min_value=0, max_value=20, step=1, value=int(student["thesis_units_taken"]))
                thesis_outline_approved = st.selectbox("Thesis Outline Approved", ["Yes","No"], index=0 if student["thesis_outline_approved"]=="Yes" else 1)
                thesis_outline_date = st.text_input("Outline Approval Date", student["thesis_outline_approved_date"])
                thesis_status = st.selectbox("Thesis Status", ["Not Started","In Progress","Draft with Adviser","For Committee Review","Approved","Submitted"], index=["Not Started","In Progress","Draft with Adviser","For Committee Review","Approved","Submitted"].index(student["thesis_status"]))

                if st.form_submit_button("Update Coursework & Thesis"):
                    df.loc[df["student_id"] == student_id, ["pos_status","pos_submitted_date","pos_approved_date","gwa","total_units_taken","total_units_required","thesis_units_taken","thesis_outline_approved","thesis_outline_approved_date","thesis_status"]] = [pos_status, pos_submitted, pos_approved, gwa, total_units_taken, total_units_required, thesis_units_taken, thesis_outline_approved, thesis_outline_date, thesis_status]
                    save_data(df)
                    st.success("✅ Updated!")
                    st.rerun()

        with tab2:
            with st.form("exams_form"):
                st.subheader("Examinations")
                # PhD exams
                qualifying = st.selectbox("Qualifying Exam Status (PhD)", ["N/A","Not Taken","Passed","Failed","Re-exam Scheduled"], index=["N/A","Not Taken","Passed","Failed","Re-exam Scheduled"].index(student["qualifying_exam_status"]))
                qualifying_date = st.text_input("Qualifying Exam Passed Date", student["qualifying_exam_passed_date"])
                written_comp = st.selectbox("Written Comprehensive Status", ["N/A","Not Taken","Passed","Failed"], index=["N/A","Not Taken","Passed","Failed"].index(student["written_comprehensive_status"]))
                written_comp_date = st.text_input("Written Comprehensive Passed Date", student["written_comprehensive_passed_date"])
                oral_comp = st.selectbox("Oral Comprehensive Status", ["N/A","Not Taken","Passed","Failed"], index=["N/A","Not Taken","Passed","Failed"].index(student["oral_comprehensive_status"]))
                oral_comp_date = st.text_input("Oral Comprehensive Passed Date", student["oral_comprehensive_passed_date"])
                # MS general exam
                general = st.selectbox("General Exam Status (MS)", ["N/A","Not Taken","Passed","Failed"], index=["N/A","Not Taken","Passed","Failed"].index(student["general_exam_status"]))
                general_date = st.text_input("General Exam Passed Date", student["general_exam_passed_date"])
                # Final exam
                final = st.selectbox("Final Exam Status", ["Not Taken","Passed","Failed","Re-exam Scheduled"], index=["Not Taken","Passed","Failed","Re-exam Scheduled"].index(student["final_exam_status"]))
                final_date = st.text_input("Final Exam Passed Date", student["final_exam_passed_date"])

                if st.form_submit_button("Update Exams"):
                    df.loc[df["student_id"] == student_id, ["qualifying_exam_status","qualifying_exam_passed_date","written_comprehensive_status","written_comprehensive_passed_date","oral_comprehensive_status","oral_comprehensive_passed_date","general_exam_status","general_exam_passed_date","final_exam_status","final_exam_passed_date"]] = [qualifying, qualifying_date, written_comp, written_comp_date, oral_comp, oral_comp_date, general, general_date, final, final_date]
                    save_data(df)
                    st.success("✅ Updated!")
                    st.rerun()

        with tab3:
            with st.form("residency_form"):
                st.subheader("Residency")
                residency_used = st.number_input("Years of Residence Used", min_value=0, max_value=10, step=1, value=int(student["residency_years_used"]))
                max_years = get_residency_max(student["program"])
                st.info(f"Maximum allowed: {max_years} years")
                extension_count = st.number_input("Number of Extensions Granted", min_value=0, max_value=3, step=1, value=int(student["extension_count"]))
                extension_end = st.text_input("Extension End Date (if applicable)", student["extension_end_date"])

                st.subheader("Leave of Absence (LOA)")
                loa_start = st.text_input("LOA Start Date", student["loa_start_date"])
                loa_end = st.text_input("LOA End Date", student["loa_end_date"])
                loa_terms = st.number_input("Total LOA Terms (each term = 0.5 year)", min_value=0, max_value=4, step=1, value=int(student["loa_total_terms"]))

                st.subheader("AWOL")
                awol = st.selectbox("AWOL Status", ["No","Yes"], index=0 if student["awol_status"]=="No" else 1)
                awol_lifted = st.text_input("AWOL Lifted Date", student["awol_lifted_date"])

                if st.form_submit_button("Update Residency & Leave"):
                    df.loc[df["student_id"] == student_id, ["residency_years_used","extension_count","extension_end_date","loa_start_date","loa_end_date","loa_total_terms","awol_status","awol_lifted_date"]] = [residency_used, extension_count, extension_end, loa_start, loa_end, loa_terms, awol, awol_lifted]
                    save_data(df)
                    st.success("✅ Updated!")
                    st.rerun()

        with tab4:
            with st.form("graduation_form"):
                st.subheader("Graduation")
                grad_applied = st.selectbox("Graduation Applied", ["No","Yes"], index=0 if student["graduation_applied"]=="No" else 1)
                grad_approved = st.selectbox("Graduation Approved", ["No","Yes"], index=0 if student["graduation_approved"]=="No" else 1)
                grad_date = st.text_input("Graduation Date (YYYY-MM-DD)", student["graduation_date"])

                st.subheader("Transfer Credit")
                transfer_units = st.number_input("Transfer Credits Approved (max 9 units)", min_value=0, max_value=9, step=1, value=int(student["transfer_units_approved"]))

                if st.form_submit_button("Update Graduation & Transfer"):
                    df.loc[df["student_id"] == student_id, ["graduation_applied","graduation_approved","graduation_date","transfer_units_approved"]] = [grad_applied, grad_approved, grad_date, transfer_units]
                    save_data(df)
                    st.success("✅ Updated!")
                    st.rerun()

        with tab5:
            with st.form("other_form"):
                st.subheader("Re-admission (for students who exceeded time limit)")
                re_status = st.selectbox("Re-admission Status", ["Not Applicable","Applied","Approved","Denied"], index=["Not Applicable","Applied","Approved","Denied"].index(student["re_admission_status"]))
                re_date = st.text_input("Re-admission Date", student["re_admission_date"])

                if st.form_submit_button("Update Re-admission"):
                    df.loc[df["student_id"] == student_id, ["re_admission_status","re_admission_date"]] = [re_status, re_date]
                    save_data(df)
                    st.success("✅ Updated!")
                    st.rerun()

    else:
        st.info("No students found. Use the Add Student feature below.")

    # ----- ADD NEW STUDENT (simplified but includes essential fields) -----
    st.markdown("---")
    st.subheader("➕ Add New Student")
    with st.expander("Click to expand and add a new student record"):
        with st.form("add_student_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_id = st.text_input("Student ID (unique)", max_chars=10)
                new_name = st.text_input("Full Name", max_chars=50)
                new_program = st.selectbox("Program", ["MS", "PhD"])
                new_advisor = st.selectbox("Advisor Username", ["adviser1", "adviser2"])
                new_year = st.number_input("Year Admitted", min_value=2000, max_value=2030, step=1, value=2025)
            with col2:
                st.markdown("**Initial Status**")
                new_pos = st.selectbox("POS Status", ["Not Filed", "Pending", "Approved"])
                new_gwa = st.number_input("Initial GWA", min_value=1.0, max_value=5.0, step=0.01, value=2.0)
                new_units_taken = st.number_input("Thesis Units Taken", min_value=0, max_value=20, step=1, value=0)

            submitted = st.form_submit_button("➕ Add Student")
            if submitted:
                if not new_id or not new_name:
                    st.error("❌ Student ID and Name are required.")
                elif new_id in df["student_id"].values:
                    st.error(f"❌ Student ID '{new_id}' already exists.")
                else:
                    # Create a new row with defaults from create_default_data, then override
                    new_row = create_default_data().iloc[0].to_dict()
                    new_row.update({
                        "student_id": new_id,
                        "name": new_name,
                        "program": new_program,
                        "advisor_username": new_advisor,
                        "year_admitted": new_year,
                        "pos_status": new_pos,
                        "gwa": new_gwa,
                        "thesis_units_taken": new_units_taken,
                        "thesis_units_limit": 6 if new_program == "MS" else 12,
                        "residency_max_years": 5 if new_program == "MS" else 7
                    })
                    new_df = pd.DataFrame([new_row])
                    df = pd.concat([df, new_df], ignore_index=True)
                    save_data(df)
                    st.success(f"✅ Student '{new_name}' added!")
                    st.rerun()

# ==================== ADVISER VIEW (Read-only) ====================
elif role == "Faculty Adviser":
    st.subheader(f"👨‍🏫 Your Advisees ({st.session_state.display_name})")
    advisees = df[df["advisor_username"] == st.session_state.username].copy()

    if len(advisees) == 0:
        st.warning("No students assigned to you.")
    else:
        # Add warning column
        advisees["warnings"] = advisees.apply(lambda row: "\n".join(get_all_warnings(row)), axis=1)
        display_cols = ["student_id", "name", "program", "year_admitted", "gwa", "thesis_units_taken", "thesis_units_limit", "pos_status", "final_exam_status", "warnings"]
        st.dataframe(advisees[display_cols], width='stretch')

        st.markdown("---")
        st.subheader("📌 Detailed View")
        for _, row in advisees.iterrows():
            with st.expander(f"{row['name']} ({row['student_id']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Program:** {row['program']}")
                    st.write(f"**Admitted:** {row['year_admitted']}")
                    st.write(f"**GWA:** {row['gwa']}")
                    st.write(f"**POS Status:** {row['pos_status']}")
                    st.write(f"**Thesis Units:** {row['thesis_units_taken']}/{row['thesis_units_limit']}")
                with col2:
                    st.write(f"**General Exam:** {row['general_exam_status']}")
                    st.write(f"**Comprehensive Exam (PhD):** Written: {row['written_comprehensive_status']}, Oral: {row['oral_comprehensive_status']}")
                    st.write(f"**Final Exam:** {row['final_exam_status']}")
                    st.write(f"**Residency:** {row['residency_years_used']}/{row['residency_max_years']} years")
                st.warning(row["warnings"]) if any("⚠️" in row["warnings"] for _ in [1]) else st.success(row["warnings"])
    st.info("📌 Read-only view. For updates, contact SESAM Staff.")

# ==================== STUDENT VIEW (Read-only) ====================
elif role == "Student":
    st.subheader(f"📘 Your Academic Progress ({st.session_state.display_name})")
    student_record = df[df["name"] == st.session_state.display_name]
    if len(student_record) == 0:
        st.error("Your record not found. Please contact SESAM Staff.")
    else:
        student = student_record.iloc[0]
        warnings = get_all_warnings(student)
        st.warning("\n".join(warnings)) if any("⚠️" in w for w in warnings) else st.success("\n".join(warnings))

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Student ID", student["student_id"])
            st.metric("Program", student["program"])
            st.metric("Year Admitted", student["year_admitted"])
        with col2:
            advisor_display = USERS.get(student["advisor_username"], {}).get("display_name", student["advisor_username"])
            st.metric("Advisor", advisor_display)
            st.metric("GWA", f"{student['gwa']:.2f}")
            st.metric("POS Status", student["pos_status"])
        with col3:
            limit = get_thesis_limit(student["program"])
            st.metric("Thesis Units", f"{student['thesis_units_taken']} / {limit}")
            st.metric("Residency", f"{student['residency_years_used']} / {student['residency_max_years']} years")
            st.metric("Final Exam", student["final_exam_status"])

        st.markdown("---")
        st.subheader("📌 Milestone Status")
        milestone_df = pd.DataFrame({
            "Milestone": [
                "Plan of Study (POS)",
                "General Exam (MS) / Qualifying Exam (PhD)",
                "Written Comprehensive (PhD)",
                "Oral Comprehensive (PhD)",
                "Thesis/Dissertation Outline",
                "Final Examination"
            ],
            "Status": [
                student["pos_status"],
                student["general_exam_status"] if student["program"]=="MS" else student["qualifying_exam_status"],
                student["written_comprehensive_status"] if student["program"]=="PhD" else "N/A",
                student["oral_comprehensive_status"] if student["program"]=="PhD" else "N/A",
                student["thesis_outline_approved"],
                student["final_exam_status"]
            ]
        })
        st.dataframe(milestone_df, width='stretch', hide_index=True)

        st.info("📌 Read-only view. For updates, contact your adviser or SESAM Staff.")

# ==================== FOOTER ====================
st.markdown("---")
st.caption("SESAM KMIS – Student Module V2 | Based on UPLB Graduate School Rules (2009)")
