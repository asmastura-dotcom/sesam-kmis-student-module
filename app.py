"""
SESAM KMIS - Student Module V2 (Graduate School Rules Integration)
Author: [Your Name]
Date: [Current Date]
Description: Tracks graduate student milestones, thesis units, exams, residency, LOA/AWOL, etc.
Based on UPLB Graduate School Policies, Rules and Regulations (2009).
"""

import streamlit as st
import pandas as pd
import os
from datetime import date

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

# ==================== DATA LOADING ====================
DATA_FILE = "students.csv"

def create_default_data():
    """Create sample data with all required fields."""
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
        # Thesis
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
    """Load or create student data with proper schema and numeric conversion."""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = create_default_data()
    
    # Ensure all required columns exist
    default_df = create_default_data()
    for col in default_df.columns:
        if col not in df.columns:
            df[col] = default_df[col]
    
    # Convert numeric columns
    numeric_int_cols = [
        "thesis_units_taken", "thesis_units_limit",
        "total_units_taken", "total_units_required",
        "residency_years_used", "residency_max_years",
        "extension_count", "loa_total_terms", "transfer_units_approved"
    ]
    for col in numeric_int_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    
    df["gwa"] = pd.to_numeric(df["gwa"], errors='coerce').fillna(2.0).astype(float)
    df["year_admitted"] = pd.to_numeric(df["year_admitted"], errors='coerce').fillna(2024).astype(int)
    
    # Fix residency max based on program and reset new students' progress
    for idx, row in df.iterrows():
        program = str(row["program"]).strip()
        df.at[idx, "residency_max_years"] = 5 if program == "MS" else 7
        
        # Reset total_units_taken and exam statuses for students admitted in 2025 or later
        if row["year_admitted"] >= 2025:
            df.at[idx, "total_units_taken"] = 0
            df.at[idx, "written_comprehensive_status"] = "N/A"
            df.at[idx, "oral_comprehensive_status"] = "N/A"
            df.at[idx, "qualifying_exam_status"] = "N/A"
            df.at[idx, "general_exam_status"] = "N/A"
            df.at[idx, "final_exam_status"] = "Not Taken"
    
    df.to_csv(DATA_FILE, index=False)
    return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def get_thesis_limit(program):
    return 6 if program == "MS" else 12

def get_residency_max(program):
    return 5 if program == "MS" else 7

# ==================== WARNING FUNCTIONS ====================
def get_warning_text(program, units_taken):
    limit = 6 if program == "MS" else 12
    try:
        units_taken = float(units_taken)
        limit = float(limit)
    except:
        return "⚠️ Thesis units data error"
    if units_taken > limit:
        return f"⚠️ Thesis units exceeded: {units_taken}/{limit} (exceeded by {units_taken - limit})"
    return f"✅ Thesis units: {units_taken}/{limit}"

def check_residency_warning(row):
    used = row.get("residency_years_used", 0)
    program = str(row.get("program", "MS")).strip()
    try:
        used = float(used)
    except:
        return "⚠️ Residency data error"
    max_years = 5 if program == "MS" else 7
    if used >= max_years:
        return f"⚠️ Residency limit reached ({used}/{max_years} years). Extension required."
    elif used >= max_years - 1:
        return f"⚠️ Approaching residency limit ({used}/{max_years} years)."
    return f"✅ Residency: {used}/{max_years} years used"

def check_gwa_warning(gwa):
    try:
        gwa = float(gwa)
    except:
        return "⚠️ GWA data error"
    if gwa > 2.00:
        return f"⚠️ GWA {gwa:.2f} is above 2.00 – may affect exam eligibility and graduation"
    return f"✅ GWA {gwa:.2f} – good standing"

def check_awol_warning(row):
    status = str(row.get("awol_status", "No")).strip()
    if status == "Yes":
        return "⚠️ AWOL – registration privileges curtailed"
    return "✅ No AWOL"

def check_loa_warning(row):
    total_terms = row.get("loa_total_terms", 0)
    try:
        total_terms = float(total_terms)
    except:
        return "⚠️ LOA data error"
    if total_terms > 2:
        return f"⚠️ LOA total exceeds 2 years ({total_terms} terms). Not allowed."
    elif total_terms > 0:
        return f"ℹ️ LOA total: {total_terms} term(s)"
    return "✅ No LOA"

def check_thesis_outline_deadline(row):
    program = str(row.get("program", "MS"))
    units_taken = row.get("thesis_units_taken", 0)
    outline_approved = str(row.get("thesis_outline_approved", "No")).strip()
    try:
        units_taken = float(units_taken)
    except:
        return "⚠️ Thesis units data error"
    if program == "MS" and units_taken > 0:
        if units_taken >= 4 and outline_approved != "Yes":
            return "⚠️ Thesis outline approval overdue (should be approved by 2nd thesis semester)"
    elif program == "PhD" and units_taken > 0:
        if units_taken >= 8 and outline_approved != "Yes":
            return "⚠️ Dissertation outline approval overdue (should be approved by 3rd dissertation semester)"
    return "✅ Outline on track"

def check_qualifying_exam_deadline(row):
    program = str(row.get("program", "MS"))
    residency_used = row.get("residency_years_used", 0)
    exam_status = str(row.get("qualifying_exam_status", "N/A")).strip()
    try:
        residency_used = float(residency_used)
    except:
        return "⚠️ Residency data error"
    if program == "PhD" and residency_used >= 1:
        if exam_status not in ["Passed", "N/A"]:
            return "⚠️ Qualifying exam should be taken before 2nd semester of residence"
    return "✅ Qualifying exam on track"

def check_comprehensive_exam_deadline(row):
    program = str(row.get("program", "MS"))
    total_taken = row.get("total_units_taken", 0)
    total_required = row.get("total_units_required", 24)
    written_status = str(row.get("written_comprehensive_status", "N/A")).strip()
    year_admitted = row.get("year_admitted", 2026)
    try:
        total_taken = float(total_taken)
        total_required = float(total_required)
    except:
        return "⚠️ Units data error"
    # Only warn if coursework is complete AND student is not brand‑new (admitted 2025 or later)
    if program == "PhD" and total_taken >= total_required and year_admitted <= 2023:
        if written_status != "Passed":
            return "⚠️ Written comprehensive exam pending after completing coursework"
    return "✅ Comprehensive exam on track"

def get_all_warnings(row):
    warnings = []
    thesis_warn = get_warning_text(row["program"], row["thesis_units_taken"])
    if "⚠️" in thesis_warn:
        warnings.append(thesis_warn)
    res_warn = check_residency_warning(row)
    if "⚠️" in res_warn:
        warnings.append(res_warn)
    gwa_warn = check_gwa_warning(row["gwa"])
    if "⚠️" in gwa_warn:
        warnings.append(gwa_warn)
    awol_warn = check_awol_warning(row)
    if "⚠️" in awol_warn:
        warnings.append(awol_warn)
    loa_warn = check_loa_warning(row)
    if "⚠️" in loa_warn:
        warnings.append(loa_warn)
    outline_warn = check_thesis_outline_deadline(row)
    if "⚠️" in outline_warn:
        warnings.append(outline_warn)
    qual_warn = check_qualifying_exam_deadline(row)
    if "⚠️" in qual_warn:
        warnings.append(qual_warn)
    comp_warn = check_comprehensive_exam_deadline(row)
    if "⚠️" in comp_warn:
        warnings.append(comp_warn)
    if not warnings:
        return ["✅ All rules satisfied"]
    return warnings

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

def safe_index(options, value):
    try:
        return options.index(value)
    except ValueError:
        return 0

# ==================== STAFF VIEW ====================
if role == "SESAM Staff":
    st.subheader("📋 All Students")
    st.dataframe(df, width='stretch', height=400)

    st.markdown("---")
    st.subheader("✏️ Update Student Record")

    if len(df) > 0:
        student_id = st.selectbox("Select Student", df["student_id"])
        student = df[df["student_id"] == student_id].iloc[0].copy()

        warnings = get_all_warnings(student)
        if any("⚠️" in w for w in warnings):
            st.warning("\n".join(warnings))
        else:
            st.success("\n".join(warnings))

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

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Coursework & Thesis", "Exams", "Residency & Leave", "Graduation", "Other"])

        with tab1:
            with st.form("coursework_form"):
                st.subheader("Plan of Study (POS)")
                pos_options = ["Not Filed", "Pending", "Approved"]
                pos_status = st.selectbox("POS Status", pos_options, index=safe_index(pos_options, student["pos_status"]))
                pos_submitted = st.text_input("POS Submitted Date (YYYY-MM-DD)", student["pos_submitted_date"])
                pos_approved = st.text_input("POS Approved Date (YYYY-MM-DD)", student["pos_approved_date"])

                st.subheader("Coursework")
                gwa = st.number_input("GWA", min_value=1.0, max_value=5.0, step=0.01, value=float(student["gwa"]))
                total_units_taken = st.number_input("Total Units Taken", min_value=0, max_value=60, step=1, value=int(student["total_units_taken"]))
                total_units_required = st.number_input("Total Units Required", min_value=0, max_value=60, step=1, value=int(student["total_units_required"]))

                st.subheader("Thesis/Dissertation")
                thesis_units_taken = st.number_input("Thesis Units Taken", min_value=0, max_value=20, step=1, value=int(student["thesis_units_taken"]))
                outline_options = ["Yes", "No"]
                thesis_outline_approved = st.selectbox("Thesis Outline Approved", outline_options, index=safe_index(outline_options, student["thesis_outline_approved"]))
                thesis_outline_date = st.text_input("Outline Approval Date", student["thesis_outline_approved_date"])
                status_options = ["Not Started", "In Progress", "Draft with Adviser", "For Committee Review", "Approved", "Submitted"]
                thesis_status = st.selectbox("Thesis Status", status_options, index=safe_index(status_options, student["thesis_status"]))

                if st.form_submit_button("Update Coursework & Thesis"):
                    df.loc[df["student_id"] == student_id, ["pos_status","pos_submitted_date","pos_approved_date","gwa","total_units_taken","total_units_required","thesis_units_taken","thesis_outline_approved","thesis_outline_approved_date","thesis_status"]] = [pos_status, pos_submitted, pos_approved, gwa, total_units_taken, total_units_required, thesis_units_taken, thesis_outline_approved, thesis_outline_date, thesis_status]
                    save_data(df)
                    st.success("✅ Updated!")
                    st.rerun()

        with tab2:
            with st.form("exams_form"):
                st.subheader("Examinations")
                qual_options = ["N/A", "Not Taken", "Passed", "Failed", "Re-exam Scheduled"]
                qualifying = st.selectbox("Qualifying Exam Status (PhD)", qual_options, index=safe_index(qual_options, student["qualifying_exam_status"]))
                qualifying_date = st.text_input("Qualifying Exam Passed Date", student["qualifying_exam_passed_date"])
                wcomp_options = ["N/A", "Not Taken", "Passed", "Failed"]
                written_comp = st.selectbox("Written Comprehensive Status", wcomp_options, index=safe_index(wcomp_options, student["written_comprehensive_status"]))
                written_comp_date = st.text_input("Written Comprehensive Passed Date", student["written_comprehensive_passed_date"])
                ocomp_options = ["N/A", "Not Taken", "Passed", "Failed"]
                oral_comp = st.selectbox("Oral Comprehensive Status", ocomp_options, index=safe_index(ocomp_options, student["oral_comprehensive_status"]))
                oral_comp_date = st.text_input("Oral Comprehensive Passed Date", student["oral_comprehensive_passed_date"])
                gen_options = ["N/A", "Not Taken", "Passed", "Failed"]
                general = st.selectbox("General Exam Status (MS)", gen_options, index=safe_index(gen_options, student["general_exam_status"]))
                general_date = st.text_input("General Exam Passed Date", student["general_exam_passed_date"])
                final_options = ["Not Taken", "Passed", "Failed", "Re-exam Scheduled"]
                final = st.selectbox("Final Exam Status", final_options, index=safe_index(final_options, student["final_exam_status"]))
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
                awol_options = ["No", "Yes"]
                awol = st.selectbox("AWOL Status", awol_options, index=safe_index(awol_options, student["awol_status"]))
                awol_lifted = st.text_input("AWOL Lifted Date", student["awol_lifted_date"])

                if st.form_submit_button("Update Residency & Leave"):
                    df.loc[df["student_id"] == student_id, ["residency_years_used","extension_count","extension_end_date","loa_start_date","loa_end_date","loa_total_terms","awol_status","awol_lifted_date"]] = [residency_used, extension_count, extension_end, loa_start, loa_end, loa_terms, awol, awol_lifted]
                    save_data(df)
                    st.success("✅ Updated!")
                    st.rerun()

        with tab4:
            with st.form("graduation_form"):
                st.subheader("Graduation")
                yn_options = ["No", "Yes"]
                grad_applied = st.selectbox("Graduation Applied", yn_options, index=safe_index(yn_options, student["graduation_applied"]))
                grad_approved = st.selectbox("Graduation Approved", yn_options, index=safe_index(yn_options, student["graduation_approved"]))
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
                readmit_options = ["Not Applicable", "Applied", "Approved", "Denied"]
                re_status = st.selectbox("Re-admission Status", readmit_options, index=safe_index(readmit_options, student["re_admission_status"]))
                re_date = st.text_input("Re-admission Date", student["re_admission_date"])

                if st.form_submit_button("Update Re-admission"):
                    df.loc[df["student_id"] == student_id, ["re_admission_status","re_admission_date"]] = [re_status, re_date]
                    save_data(df)
                    st.success("✅ Updated!")
                    st.rerun()

    else:
        st.info("No students found. Use the Add Student feature below.")

    # ----- ADD NEW STUDENT (properly reset all progress) -----
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
                    new_row = create_default_data().iloc[0].to_dict()
                    new_row.update({
                        "student_id": new_id,
                        "name": new_name,
                        "program": new_program,
                        "advisor_username": new_advisor,
                        "year_admitted": new_year,
                        "pos_status": new_pos,
                        "pos_submitted_date": "",
                        "pos_approved_date": "",
                        "gwa": new_gwa,
                        "total_units_taken": 0,
                        "total_units_required": 24,
                        "thesis_units_taken": new_units_taken,
                        "thesis_units_limit": 6 if new_program == "MS" else 12,
                        "thesis_outline_approved": "No",
                        "thesis_outline_approved_date": "",
                        "thesis_status": "Not Started",
                        "qualifying_exam_status": "N/A",
                        "qualifying_exam_passed_date": "",
                        "written_comprehensive_status": "N/A",
                        "written_comprehensive_passed_date": "",
                        "oral_comprehensive_status": "N/A",
                        "oral_comprehensive_passed_date": "",
                        "general_exam_status": "N/A",
                        "general_exam_passed_date": "",
                        "final_exam_status": "Not Taken",
                        "final_exam_passed_date": "",
                        "residency_years_used": 0,
                        "residency_max_years": 5 if new_program == "MS" else 7,
                        "extension_count": 0,
                        "extension_end_date": "",
                        "loa_start_date": "",
                        "loa_end_date": "",
                        "loa_total_terms": 0,
                        "awol_status": "No",
                        "awol_lifted_date": "",
                        "transfer_units_approved": 0,
                        "graduation_applied": "No",
                        "graduation_approved": "No",
                        "graduation_date": "",
                        "re_admission_status": "Not Applicable",
                        "re_admission_date": ""
                    })
                    new_df = pd.DataFrame([new_row])
                    df = pd.concat([df, new_df], ignore_index=True)
                    save_data(df)
                    st.success(f"✅ Student '{new_name}' added!")
                    st.rerun()

# ==================== ADVISER VIEW ====================
elif role == "Faculty Adviser":
    st.subheader(f"👨‍🏫 Your Advisees ({st.session_state.display_name})")
    advisees = df[df["advisor_username"] == st.session_state.username].copy()
    if len(advisees) == 0:
        st.warning("No students assigned to you.")
    else:
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
                    st.write(f"**Residency:** {row['residency_years_used']}/{5 if row['program']=='MS' else 7} years")
                warnings_text = row["warnings"]
                if any("⚠️" in w for w in warnings_text.split("\n")):
                    st.warning(warnings_text)
                else:
                    st.success(warnings_text)
    st.info("📌 Read-only view. For updates, contact SESAM Staff.")

# ==================== STUDENT VIEW ====================
elif role == "Student":
    st.subheader(f"📘 Your Academic Progress ({st.session_state.display_name})")
    student_record = df[df["name"] == st.session_state.display_name]
    if len(student_record) == 0:
        st.error("Your record not found. Please contact SESAM Staff.")
    else:
        student = student_record.iloc[0]
        warnings = get_all_warnings(student)
        if any("⚠️" in w for w in warnings):
            st.warning("\n".join(warnings))
        else:
            st.success("\n".join(warnings))

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
            st.metric("Residency", f"{student['residency_years_used']} / {5 if student['program']=='MS' else 7} years")
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
                student["general_exam_status"] if student["program"] == "MS" else student["qualifying_exam_status"],
                student["written_comprehensive_status"] if student["program"] == "PhD" else "N/A",
                student["oral_comprehensive_status"] if student["program"] == "PhD" else "N/A",
                student["thesis_outline_approved"],
                student["final_exam_status"]
            ]
        })
        st.dataframe(milestone_df, width='stretch', hide_index=True)
        st.info("📌 Read-only view. For updates, contact your adviser or SESAM Staff.")

# ==================== FOOTER ====================
st.markdown("---")
st.caption("SESAM KMIS – Student Module V2 | Based on UPLB Graduate School Rules (2009)")
