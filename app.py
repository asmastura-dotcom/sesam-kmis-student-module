"""
SESAM KMIS - Graduate Student Lifecycle Management System (Enhanced)
Author: [Your Name]
Date: [Current Date]
Description: Full workflow-based lifecycle management with document uploads,
semester tracking, automatic GWA, adviser notifications, and step-by-step progression.
"""

import streamlit as st
import pandas as pd
import os
import json
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="SESAM Graduate Student Lifecycle Management",
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
if "selected_student" not in st.session_state:
    st.session_state.selected_student = None
if "notification_badge" not in st.session_state:
    st.session_state.notification_badge = 0

# ==================== USER AUTH (unchanged) ====================
USERS = {
    "staff1": {"password": "admin123", "role": "SESAM Staff", "display_name": "SESAM Administrator"},
    "adviser1": {"password": "adv123", "role": "Faculty Adviser", "display_name": "Dr. Eslava"},
    "adviser2": {"password": "adv456", "role": "Faculty Adviser", "display_name": "Dr. Sanchez"},
    "student1": {"password": "stu123", "role": "Student", "display_name": "Cruz, Juan M."},
    "student2": {"password": "stu456", "role": "Student", "display_name": "Santos, Maria L."}
}

# ==================== PROGRAM DEFINITIONS (unchanged) ====================
PROGRAMS = [
    "MS Environmental Science",
    "PhD Environmental Science",
    "PhD Environmental Diplomacy and Negotiations",
    "Master in Resilience Studies (M-ReS)",
    "Professional Masters in Tropical Marine Ecosystems Management (PM-TMEM)"
]

SEMESTERS = ["1st Sem", "2nd Sem", "Summer"]
current_year = date.today().year
ACADEMIC_YEARS = [f"{year}-{year+1}" for year in range(current_year-5, current_year+6)]

def is_master_program(program):
    return program.startswith("MS") or program.startswith("Master") or program.startswith("Professional Masters")

def is_phd_program(program):
    return program.startswith("PhD")

def get_thesis_limit_from_program(program):
    return 6 if is_master_program(program) else 12

def get_residency_max_from_program(program):
    return 5 if is_master_program(program) else 7

def format_ay(ay_start, semester):
    return f"A.Y. {ay_start}-{ay_start+1} ({semester})"

def get_thesis_pattern_description(program):
    if is_master_program(program):
        return "💡 MS students: thesis units (6 total) can be taken as 2-2-2 (three terms) or 3-3 (two terms)."
    else:
        return "💡 PhD students: dissertation units (12 total) can be taken as 3-3-3-3 (four terms) or 4-4-4 (three terms)."

# ==================== WORKFLOW ENGINE (NEW) ====================
WORKFLOW_STEPS = [
    "Admission",
    "Committee",
    "Coursework",
    "Exams",
    "POS",
    "Thesis",
    "Defense",
    "Graduation"
]

def get_step_completion_status(student_row):
    """Determine which steps are completed based on current data."""
    program = student_row["program"]
    completed = set()
    
    # Admission: always completed if student exists
    completed.add("Admission")
    
    # Committee: committee approved date present
    if pd.notna(student_row.get("committee_approval_date")) and student_row.get("committee_approval_date"):
        completed.add("Committee")
    
    # Coursework: total units taken >= required (or all courses completed)
    if student_row.get("total_units_taken", 0) >= student_row.get("total_units_required", 24):
        completed.add("Coursework")
    
    # Exams: For MS: general exam passed; For PhD: qualifying exam passed and comprehensive exams passed
    if is_master_program(program):
        if student_row.get("general_exam_status") == "Passed":
            completed.add("Exams")
    else:
        if (student_row.get("qualifying_exam_status") == "Passed" and
            student_row.get("written_comprehensive_status") == "Passed" and
            student_row.get("oral_comprehensive_status") == "Passed"):
            completed.add("Exams")
    
    # POS: status Approved
    if student_row.get("pos_status") == "Approved":
        completed.add("POS")
    
    # Thesis: thesis outline approved and thesis status not "Not Started"
    if (student_row.get("thesis_outline_approved") == "Yes" and
        student_row.get("thesis_status") not in ["Not Started", ""]):
        completed.add("Thesis")
    
    # Defense: final exam passed
    if student_row.get("final_exam_status") == "Passed":
        completed.add("Defense")
    
    # Graduation: graduation approved == Yes
    if student_row.get("graduation_approved") == "Yes":
        completed.add("Graduation")
    
    return completed

def get_next_required_step(student_row):
    """Return the next step that needs to be completed."""
    completed = get_step_completion_status(student_row)
    for step in WORKFLOW_STEPS:
        if step not in completed:
            return step
    return "Complete"

def is_step_locked(student_row, step_name):
    """Check if a step should be locked (previous step not completed)."""
    step_index = WORKFLOW_STEPS.index(step_name)
    if step_index == 0:
        return False
    previous_step = WORKFLOW_STEPS[step_index - 1]
    completed = get_step_completion_status(student_row)
    return previous_step not in completed

# ==================== SEMESTER TRACKING (NEW) ====================
SEMESTER_FILE = "semester_records.csv"

def load_semester_records():
    if os.path.exists(SEMESTER_FILE):
        df = pd.read_csv(SEMESTER_FILE)
        # Ensure subjects_json column exists
        if "subjects_json" not in df.columns:
            df["subjects_json"] = "[]"
        df["subjects_json"] = df["subjects_json"].fillna("[]")
        return df
    else:
        return pd.DataFrame(columns=[
            "student_number", "academic_year", "semester", 
            "subjects_json", "total_units", "gwa", "amis_file_path"
        ])

def save_semester_records(df):
    df.to_csv(SEMESTER_FILE, index=False)

def compute_gwa_from_subjects(subjects_list):
    """Calculate weighted average GWA from list of subjects with units and grades."""
    if not subjects_list:
        return 0.0
    total_units = 0
    total_grade_points = 0
    for subj in subjects_list:
        units = float(subj.get("units", 0))
        grade = float(subj.get("grade", 0))
        total_units += units
        total_grade_points += units * grade
    if total_units == 0:
        return 0.0
    return total_grade_points / total_units

def get_student_semesters(student_number):
    df = load_semester_records()
    return df[df["student_number"] == student_number].copy()

def add_semester_record(student_number, academic_year, semester, subjects_list, amis_file_path=""):
    df = load_semester_records()
    gwa = compute_gwa_from_subjects(subjects_list)
    total_units = sum(float(s.get("units", 0)) for s in subjects_list)
    new_record = pd.DataFrame([{
        "student_number": student_number,
        "academic_year": academic_year,
        "semester": semester,
        "subjects_json": json.dumps(subjects_list),
        "total_units": total_units,
        "gwa": gwa,
        "amis_file_path": amis_file_path
    }])
    df = pd.concat([df, new_record], ignore_index=True)
    save_semester_records(df)
    # Also update the student's cumulative GWA and total units in main dataframe
    update_student_academic_summary(student_number)
    return gwa

def update_student_academic_summary(student_number):
    """Recalculate cumulative GWA and total units from all semesters and update main df."""
    semesters = get_student_semesters(student_number)
    if len(semesters) == 0:
        return
    # Cumulative weighted average
    total_grade_points = 0
    total_units_all = 0
    for _, row in semesters.iterrows():
        subjects = json.loads(row["subjects_json"])
        for subj in subjects:
            units = float(subj.get("units", 0))
            grade = float(subj.get("grade", 0))
            total_units_all += units
            total_grade_points += units * grade
    if total_units_all > 0:
        cumulative_gwa = total_grade_points / total_units_all
    else:
        cumulative_gwa = 0.0
    
    # Update main dataframe
    df_main = load_data()  # We'll define load_data later, careful with circular import
    # We'll handle this inside the load_data function after loading both
    # Better to have a global ref, but for now we'll call a function
    update_main_student_gwa_and_units(student_number, cumulative_gwa, total_units_all)

def update_main_student_gwa_and_units(student_number, cumulative_gwa, total_units):
    df = load_data()
    idx = df[df["student_number"] == student_number].index
    if len(idx) > 0:
        df.loc[idx, "gwa"] = cumulative_gwa
        df.loc[idx, "total_units_taken"] = total_units
        save_data(df)

# ==================== DOCUMENT UPLOAD SYSTEM (NEW) ====================
UPLOAD_FOLDER = "student_uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

UPLOAD_CATEGORIES = [
    "admission_letter",
    "amis_screenshot",
    "committee_form",
    "plan_of_study",
    "thesis_file"
]

UPLOAD_DISPLAY_NAMES = {
    "admission_letter": "Admission Letter",
    "amis_screenshot": "AMIS Screenshot",
    "committee_form": "Committee Form",
    "plan_of_study": "Plan of Study (POS)",
    "thesis_file": "Thesis/Dissertation File"
}

UPLOAD_FILE = "uploads.csv"

def load_uploads():
    if os.path.exists(UPLOAD_FILE):
        return pd.read_csv(UPLOAD_FILE)
    else:
        return pd.DataFrame(columns=[
            "student_number", "category", "file_path", "original_filename",
            "upload_date", "status", "reviewer_comment", "reviewed_by", "review_date"
        ])

def save_uploads(df):
    df.to_csv(UPLOAD_FILE, index=False)

def save_uploaded_file(student_number, category, uploaded_file):
    if uploaded_file is None:
        return None
    # Create student subfolder
    student_folder = os.path.join(UPLOAD_FOLDER, student_number)
    if not os.path.exists(student_folder):
        os.makedirs(student_folder)
    # Generate safe filename
    ext = uploaded_file.name.split('.')[-1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{category}_{timestamp}.{ext}"
    filepath = os.path.join(student_folder, filename)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filepath

def get_upload_status(student_number, category):
    df = load_uploads()
    records = df[(df["student_number"] == student_number) & (df["category"] == category)]
    if len(records) == 0:
        return None
    latest = records.iloc[-1]
    return latest["status"]

def get_all_uploads_for_student(student_number):
    df = load_uploads()
    return df[df["student_number"] == student_number].copy()

# ==================== NOTIFICATION SYSTEM (NEW) ====================
def get_adviser_notifications(adviser_name):
    """Return list of notifications for adviser's advisees."""
    df = load_data()
    advisees = df[df["advisor"] == adviser_name].copy()
    notifications = []
    
    for _, student in advisees.iterrows():
        # GWA warning
        if student["gwa"] > 2.00:
            notifications.append({
                "student": student["name"],
                "student_number": student["student_number"],
                "type": "GWA Warning",
                "message": f"GWA {student['gwa']:.2f} exceeds 2.00",
                "severity": "error"
            })
        
        # Missing submissions (pending > 7 days)
        uploads = get_all_uploads_for_student(student["student_number"])
        for _, upload in uploads.iterrows():
            if upload["status"] == "Pending":
                upload_date = datetime.strptime(upload["upload_date"], "%Y-%m-%d %H:%M:%S")
                if (datetime.now() - upload_date).days > 7:
                    notifications.append({
                        "student": student["name"],
                        "student_number": student["student_number"],
                        "type": "Overdue Upload",
                        "message": f"{UPLOAD_DISPLAY_NAMES[upload['category']]} pending for >7 days",
                        "severity": "warning"
                    })
        
        # Overdue milestones based on residency
        next_step = get_next_required_step(student)
        residency_used = student["residency_years_used"]
        if next_step == "Exams" and residency_used >= 2:
            notifications.append({
                "student": student["name"],
                "student_number": student["student_number"],
                "type": "Milestone Overdue",
                "message": "Exams should be completed by 2nd year of residence",
                "severity": "error"
            })
        if next_step == "Thesis" and residency_used >= 3:
            notifications.append({
                "student": student["name"],
                "student_number": student["student_number"],
                "type": "Milestone Overdue",
                "message": "Thesis stage overdue - residency limit approaching",
                "severity": "error"
            })
    
    return notifications

# ==================== PROFILE PICTURE HELPER (unchanged) ====================
PIC_FOLDER = "profile_pics"
if not os.path.exists(PIC_FOLDER):
    os.makedirs(PIC_FOLDER)

def save_profile_picture(student_number, uploaded_file):
    if uploaded_file is None:
        return None
    ext = uploaded_file.name.split('.')[-1].lower()
    if ext not in ['jpg', 'jpeg', 'png', 'gif']:
        st.error("Unsupported file format. Use JPG, PNG, or GIF.")
        return None
    filename = f"{student_number}.{ext}"
    filepath = os.path.join(PIC_FOLDER, filename)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filename

def delete_profile_picture(student_number):
    for f in os.listdir(PIC_FOLDER):
        if f.startswith(str(student_number) + "."):
            os.remove(os.path.join(PIC_FOLDER, f))
            return True
    return False

def get_profile_picture_path(student_number):
    for f in os.listdir(PIC_FOLDER):
        if f.startswith(str(student_number) + "."):
            return os.path.join(PIC_FOLDER, f)
    return None

# ==================== DATA LOADING (updated with migration) ====================
DATA_FILE = "students.csv"

def create_default_data():
    return pd.DataFrame({
        "student_number": ["S001", "S002", "S003", "S004", "S005"],
        "name": ["Cruz, Juan M.", "Santos, Maria L.", "Rizal, Jose P.", "Reyes, Ana C.", "Lopez, Carlos R."],
        "last_name": ["Cruz", "Santos", "Rizal", "Reyes", "Lopez"],
        "first_name": ["Juan", "Maria", "Jose", "Ana", "Carlos"],
        "middle_name": ["M.", "L.", "P.", "C.", "R."],
        "program": [PROGRAMS[0], PROGRAMS[1], PROGRAMS[0], PROGRAMS[1], PROGRAMS[0]],
        "advisor": ["Dr. Eslava", "Dr. Sanchez", "Dr. Eslava", "Dr. Sanchez", "Dr. Eslava"],
        "ay_start": [2024, 2023, 2024, 2022, 2024],
        "semester": ["1st Sem", "1st Sem", "2nd Sem", "1st Sem", "1st Sem"],
        "profile_pic": ["", "", "", "", ""],
        "committee_members": ["Dr. Eslava, Dr. Sanchez", "Dr. Sanchez, Dr. Eslava", "Dr. Eslava", "Dr. Sanchez, Dr. Eslava", "Dr. Eslava"],
        "committee_approval_date": ["2024-02-01", "2023-07-01", "", "2022-09-15", ""],
        "pos_status": ["Approved", "Approved", "Pending", "Approved", "Pending"],
        "pos_submitted_date": ["2024-01-15", "2023-06-10", "", "2022-09-01", ""],
        "pos_approved_date": ["2024-02-01", "2023-07-01", "", "2022-09-15", ""],
        "gwa": [1.75, 1.85, 2.10, 1.95, 2.05],
        "total_units_taken": [12, 18, 9, 24, 6],
        "total_units_required": [24, 24, 24, 24, 24],
        "thesis_units_taken": [3, 8, 2, 12, 1],
        "thesis_units_limit": [6, 12, 6, 12, 6],
        "thesis_outline_approved": ["No", "Yes", "No", "Yes", "No"],
        "thesis_outline_approved_date": ["", "2024-01-10", "", "2023-11-20", ""],
        "thesis_status": ["In Progress", "Draft with Adviser", "Not Started", "Approved", "Not Started"],
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
        "residency_years_used": [1, 2, 1, 3, 1],
        "residency_max_years": [5, 7, 5, 7, 5],
        "extension_count": [0, 0, 0, 0, 0],
        "extension_end_date": ["", "", "", "", ""],
        "loa_start_date": ["", "", "", "", ""],
        "loa_end_date": ["", "", "", "", ""],
        "loa_total_terms": [0, 0, 0, 0, 0],
        "awol_status": ["No", "No", "No", "No", "No"],
        "awol_lifted_date": ["", "", "", "", ""],
        "transfer_units_approved": [0, 0, 0, 0, 0],
        "graduation_applied": ["No", "No", "No", "No", "No"],
        "graduation_approved": ["No", "No", "No", "No", "No"],
        "graduation_date": ["", "", "", "", ""],
        "re_admission_status": ["Not Applicable", "Not Applicable", "Not Applicable", "Not Applicable", "Not Applicable"],
        "re_admission_date": ["", "", "", "", ""]
    })

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = create_default_data()
    
    default_df = create_default_data()
    for col in default_df.columns:
        if col not in df.columns:
            df[col] = default_df[col]
    
    # Migrate old year_admitted column if exists
    if "year_admitted" in df.columns and "ay_start" not in df.columns:
        df["ay_start"] = df["year_admitted"]
        df["semester"] = "1st Sem"
        df = df.drop(columns=["year_admitted"])
    
    if "ay_start" not in df.columns:
        df["ay_start"] = 2024
    if "semester" not in df.columns:
        df["semester"] = "1st Sem"
    if "committee_members" not in df.columns:
        df["committee_members"] = ""
    if "committee_approval_date" not in df.columns:
        df["committee_approval_date"] = ""
    
    # Convert numeric columns
    numeric_int_cols = [
        "thesis_units_taken", "thesis_units_limit",
        "total_units_taken", "total_units_required",
        "residency_years_used", "residency_max_years",
        "extension_count", "loa_total_terms", "transfer_units_approved",
        "ay_start"
    ]
    for col in numeric_int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    
    if "gwa" in df.columns:
        df["gwa"] = pd.to_numeric(df["gwa"], errors='coerce').fillna(2.0).astype(float)
    
    for idx, row in df.iterrows():
        program = str(row["program"]).strip()
        if program not in PROGRAMS:
            if program == "MS":
                program = PROGRAMS[0]
            elif program == "PhD":
                program = PROGRAMS[1]
            else:
                program = PROGRAMS[0]
            df.at[idx, "program"] = program
        df.at[idx, "residency_max_years"] = get_residency_max_from_program(program)
        df.at[idx, "thesis_units_limit"] = get_thesis_limit_from_program(program)
        
        if row["ay_start"] >= 2025:
            df.at[idx, "total_units_taken"] = 0
            df.at[idx, "written_comprehensive_status"] = "N/A"
            df.at[idx, "oral_comprehensive_status"] = "N/A"
            df.at[idx, "qualifying_exam_status"] = "N/A"
            df.at[idx, "general_exam_status"] = "N/A"
            df.at[idx, "final_exam_status"] = "Not Taken"
    
    # Update GWA from semester records (override manual input)
    semesters_df = load_semester_records()
    for student_number in df["student_number"].unique():
        student_sems = semesters_df[semesters_df["student_number"] == student_number]
        if len(student_sems) > 0:
            total_grade = 0
            total_units = 0
            for _, sem in student_sems.iterrows():
                subjects = json.loads(sem["subjects_json"])
                for subj in subjects:
                    units = float(subj.get("units", 0))
                    grade = float(subj.get("grade", 0))
                    total_units += units
                    total_grade += units * grade
            if total_units > 0:
                computed_gwa = total_grade / total_units
                df.loc[df["student_number"] == student_number, "gwa"] = computed_gwa
                df.loc[df["student_number"] == student_number, "total_units_taken"] = total_units
    
    save_data(df)
    return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def get_thesis_limit(program):
    return get_thesis_limit_from_program(program)

def get_residency_max(program):
    return get_residency_max_from_program(program)

# ==================== WARNING FUNCTIONS (unchanged but used) ====================
def get_warning_text(program, units_taken):
    limit = get_thesis_limit(program)
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
    program = str(row.get("program", PROGRAMS[0])).strip()
    try:
        used = float(used)
    except:
        return "⚠️ Residency data error"
    max_years = get_residency_max(program)
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
        return f"⚠️ GWA {gwa:.2f} is below 2.00 – may affect exam eligibility and graduation"
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
    program = str(row.get("program", PROGRAMS[0]))
    units_taken = row.get("thesis_units_taken", 0)
    outline_approved = str(row.get("thesis_outline_approved", "No")).strip()
    try:
        units_taken = float(units_taken)
    except:
        return "⚠️ Thesis units data error"
    if is_master_program(program) and units_taken > 0:
        if units_taken >= 4 and outline_approved != "Yes":
            return "⚠️ Thesis outline approval overdue (should be approved by 2nd thesis semester)"
    elif is_phd_program(program) and units_taken > 0:
        if units_taken >= 8 and outline_approved != "Yes":
            return "⚠️ Dissertation outline approval overdue (should be approved by 3rd dissertation semester)"
    return "✅ Outline on track"

def check_qualifying_exam_deadline(row):
    program = str(row.get("program", PROGRAMS[0]))
    residency_used = row.get("residency_years_used", 0)
    exam_status = str(row.get("qualifying_exam_status", "N/A")).strip()
    try:
        residency_used = float(residency_used)
    except:
        return "⚠️ Residency data error"
    if is_phd_program(program) and residency_used >= 1:
        if exam_status not in ["Passed", "N/A"]:
            return "⚠️ Qualifying exam should be taken before 2nd semester of residence"
    return "✅ Qualifying exam on track"

def check_comprehensive_exam_deadline(row):
    program = str(row.get("program", PROGRAMS[0]))
    total_taken = row.get("total_units_taken", 0)
    total_required = row.get("total_units_required", 24)
    written_status = str(row.get("written_comprehensive_status", "N/A")).strip()
    ay_start = row.get("ay_start", 2026)
    try:
        total_taken = float(total_taken)
        total_required = float(total_required)
    except:
        return "⚠️ Units data error"
    if is_phd_program(program) and total_taken >= total_required and ay_start <= 2023:
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

def check_deadline_alerts(row):
    """Return list of deadline‑related warnings."""
    alerts = []
    program = row["program"]
    thesis_units = row["thesis_units_taken"]
    outline_approved = row["thesis_outline_approved"]
    pos_status = row["pos_status"]
    residency_used = row.get("residency_years_used", 0)
    
    if program.startswith("MS") and residency_used >= 1 and pos_status not in ["Approved", "Completed"]:
        alerts.append("⚠️ Plan of Study (POS) should be approved by 2nd semester of residence.")
    elif program.startswith("PhD") and row.get("qualifying_exam_status") == "Passed" and pos_status != "Approved":
        alerts.append("⚠️ Plan of Study (POS) pending approval after qualifying exam.")
    
    if program.startswith("MS") and thesis_units >= 4 and outline_approved != "Yes":
        alerts.append("⚠️ Thesis outline approval overdue (must be approved by 2nd thesis semester).")
    if program.startswith("PhD") and thesis_units >= 8 and outline_approved != "Yes":
        alerts.append("⚠️ Dissertation outline approval overdue (must be approved by 3rd dissertation semester).")
    
    if program.startswith("PhD") and residency_used >= 1 and row["qualifying_exam_status"] not in ["Passed", "N/A"]:
        alerts.append("⚠️ Qualifying exam should be taken before 2nd semester of residence.")
    
    if program.startswith("PhD") and row["total_units_taken"] >= row["total_units_required"] and row["written_comprehensive_status"] != "Passed":
        alerts.append("⚠️ Written comprehensive exam pending after completing all coursework.")
    
    return alerts

def compute_coursework_progress(row):
    taken = row.get("total_units_taken", 0)
    required = row.get("total_units_required", 24)
    if required <= 0:
        return 0
    return min(100, int((taken / required) * 100))

# ==================== UI HELPER FUNCTIONS ====================
def safe_index(options, value):
    try:
        return options.index(value)
    except ValueError:
        return 0

def filter_dataframe(search_term, data):
    if not search_term:
        return data
    mask = (
        data["name"].str.contains(search_term, case=False, na=False) |
        data["student_number"].str.contains(search_term, case=False, na=False)
    )
    return data[mask]

def display_workflow_progress(student_row):
    """Display a visual progress bar for workflow steps."""
    completed = get_step_completion_status(student_row)
    completed_count = len([s for s in WORKFLOW_STEPS if s in completed])
    total_steps = len(WORKFLOW_STEPS)
    progress = int((completed_count / total_steps) * 100)
    st.progress(progress, text=f"Overall Progress: {completed_count}/{total_steps} steps completed")
    
    # Next step highlight
    next_step = get_next_required_step(student_row)
    if next_step != "Complete":
        st.info(f"**Next Required Step:** {next_step}")
        # Check if locked
        if is_step_locked(student_row, next_step):
            st.warning(f"⚠️ {next_step} is locked until previous steps are completed.")
    else:
        st.success("🎉 All milestones completed! Ready for graduation.")

def display_milestone_status(student_row):
    """Show each milestone's status and lock state."""
    completed = get_step_completion_status(student_row)
    for step in WORKFLOW_STEPS:
        if step in completed:
            status = "✅ Completed"
        else:
            locked = is_step_locked(student_row, step)
            if locked:
                status = "🔒 Locked (previous step incomplete)"
            else:
                status = "⏳ Pending"
        st.metric(step, status)

# ==================== LOGIN PAGE (unchanged) ====================
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

# ==================== DATA LOADING (final call) ====================
df = load_data()

# ==================== SIDEBAR (unchanged) ====================
st.sidebar.title("🎓 KMIS Student Module")
st.sidebar.markdown("---")
st.sidebar.write(f"👤 {st.session_state.display_name}")
st.sidebar.write(f"🔑 {st.session_state.role}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.display_name = None
    st.session_state.selected_student = None
    st.rerun()
st.sidebar.markdown("---")
st.sidebar.caption("Version 3.0 | Lifecycle Management | Workflow Engine")

# ==================== MAIN ====================
st.title("🎓 SESAM Graduate Student Lifecycle Management System")
st.markdown("*Complete workflow tracking from admission to graduation with document management*")
st.markdown("---")

role = st.session_state.role

# ==================== STAFF VIEW ====================
if role == "SESAM Staff":
    st.subheader("📋 Student Directory (Click a row to edit)")
    
    # Search and filter
    search = st.text_input("🔍 Search by name or student number", placeholder="e.g., Cruz or S001")
    filtered_df = filter_dataframe(search, df)
    filtered_df["academic_year"] = filtered_df.apply(lambda row: format_ay(row["ay_start"], row["semester"]), axis=1)
    
    # Clickable rows using radio buttons (simpler than st.dataframe selection)
    display_cols = ["student_number", "name", "program", "academic_year", "advisor", "gwa", "pos_status", "final_exam_status"]
    
    # Create a selection box from filtered data
    if len(filtered_df) > 0:
        # Add "Select" column as radio
        selected_index = st.radio(
            "Select a student to edit",
            options=filtered_df.index,
            format_func=lambda idx: f"{filtered_df.loc[idx, 'student_number']} - {filtered_df.loc[idx, 'name']}",
            key="staff_student_select"
        )
        selected_student = filtered_df.loc[selected_index].copy()
        
        # Display selected student details in an expander or below
        st.markdown("---")
        st.subheader(f"✏️ Editing: {selected_student['name']} ({selected_student['student_number']})")
        
        # Show workflow progress (new)
        with st.expander("📈 Workflow Progress", expanded=True):
            display_workflow_progress(selected_student)
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Milestone Status")
                display_milestone_status(selected_student)
            with col2:
                st.subheader("Next Steps")
                next_step = get_next_required_step(selected_student)
                st.info(f"**Next Required Step:** {next_step}")
                if next_step != "Complete" and is_step_locked(selected_student, next_step):
                    st.warning(f"🔒 {next_step} is locked. Please complete previous steps first.")
        
        # Existing tabs (keep all existing functionality but add new tabs)
        tabs = st.tabs([
            "Student Info", "Coursework & Thesis", "Exams", 
            "Residency & Leave", "Graduation", "Committee", 
            "Other", "📁 Documents", "📚 Semester History"
        ])
        
        # Tab 0: Student Info (existing profile picture + basic info)
        with tabs[0]:
            # Profile picture
            col_pic1, col_pic2 = st.columns([1, 2])
            with col_pic1:
                pic_path = get_profile_picture_path(selected_student["student_number"])
                if pic_path and os.path.exists(pic_path):
                    st.image(pic_path, width=150, caption="Current Picture")
                else:
                    st.info("No profile picture uploaded.")
            with col_pic2:
                uploaded_file = st.file_uploader("Upload new profile picture (JPG, PNG, GIF)", type=["jpg", "jpeg", "png", "gif"], key=f"pic_{selected_student['student_number']}")
                if uploaded_file:
                    new_filename = save_profile_picture(selected_student["student_number"], uploaded_file)
                    if new_filename:
                        df.loc[df["student_number"] == selected_student["student_number"], "profile_pic"] = new_filename
                        save_data(df)
                        st.success("Profile picture updated!")
                        st.rerun()
                if st.button("🗑️ Delete current picture", key=f"del_pic_{selected_student['student_number']}"):
                    if delete_profile_picture(selected_student["student_number"]):
                        df.loc[df["student_number"] == selected_student["student_number"], "profile_pic"] = ""
                        save_data(df)
                        st.success("Profile picture deleted.")
                        st.rerun()
                    else:
                        st.warning("No picture to delete.")
            
            # Basic info display (read-only)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Student Number:** {selected_student['student_number']}")
                st.markdown(f"**Name:** {selected_student['name']}")
            with col2:
                st.markdown(f"**Program:** {selected_student['program']}")
                st.markdown(f"**Advisor:** {selected_student['advisor']}")
            with col3:
                limit = get_thesis_limit(selected_student["program"])
                st.markdown(f"**Thesis Units:** {selected_student['thesis_units_taken']} / {limit}")
                st.markdown(f"**Academic Year & Semester:** {format_ay(selected_student['ay_start'], selected_student['semester'])}")
        
        # Tab 1: Coursework & Thesis (existing but with lock checks)
        with tabs[1]:
            locked = is_step_locked(selected_student, "Coursework")
            if locked:
                st.warning("🔒 Coursework step is locked until Committee step is completed.")
            with st.form("coursework_form_staff"):
                st.subheader("Plan of Study (POS)")
                pos_options = ["Not Filed", "Pending", "Approved"]
                pos_status = st.selectbox("POS Status", pos_options, index=safe_index(pos_options, selected_student["pos_status"]), disabled=locked)
                pos_submitted = st.text_input("POS Submitted Date (YYYY-MM-DD)", selected_student["pos_submitted_date"], disabled=locked)
                pos_approved = st.text_input("POS Approved Date (YYYY-MM-DD)", selected_student["pos_approved_date"], disabled=locked)
                st.subheader("Coursework")
                gwa = st.number_input("GWA (manual override - but system uses computed from semesters)", min_value=1.0, max_value=5.0, step=0.01, value=float(selected_student["gwa"]), disabled=locked)
                total_units_taken = st.number_input("Total Units Taken", min_value=0, max_value=60, step=1, value=int(selected_student["total_units_taken"]), disabled=locked)
                total_units_required = st.number_input("Total Units Required", min_value=0, max_value=60, step=1, value=int(selected_student["total_units_required"]), disabled=locked)
                progress = compute_coursework_progress(selected_student)
                st.progress(progress / 100, text=f"Coursework completion: {progress}% ({selected_student['total_units_taken']} of {selected_student['total_units_required']} units)")
                st.caption(f"Remaining units: {max(0, selected_student['total_units_required'] - selected_student['total_units_taken'])}")
                st.subheader("Thesis/Dissertation")
                thesis_units_taken = st.number_input("Thesis Units Taken", min_value=0, max_value=20, step=1, value=int(selected_student["thesis_units_taken"]), disabled=locked)
                st.caption(get_thesis_pattern_description(selected_student["program"]))
                outline_options = ["Yes", "No"]
                thesis_outline_approved = st.selectbox("Thesis Outline Approved", outline_options, index=safe_index(outline_options, selected_student["thesis_outline_approved"]), disabled=locked)
                thesis_outline_date = st.text_input("Outline Approval Date", selected_student["thesis_outline_approved_date"], disabled=locked)
                status_options = ["Not Started", "In Progress", "Draft with Adviser", "For Committee Review", "Approved", "Submitted"]
                thesis_status = st.selectbox("Thesis Status", status_options, index=safe_index(status_options, selected_student["thesis_status"]), disabled=locked)
                if st.form_submit_button("Update Coursework & Thesis"):
                    if not locked:
                        df.loc[df["student_number"] == selected_student["student_number"], 
                               ["pos_status","pos_submitted_date","pos_approved_date","gwa","total_units_taken","total_units_required","thesis_units_taken","thesis_outline_approved","thesis_outline_approved_date","thesis_status"]] = \
                               [pos_status, pos_submitted, pos_approved, gwa, total_units_taken, total_units_required, thesis_units_taken, thesis_outline_approved, thesis_outline_date, thesis_status]
                        save_data(df)
                        st.success("✅ Updated!")
                        st.rerun()
                    else:
                        st.error("Cannot update: previous step not completed.")
        
        # Tab 2: Exams (existing with lock)
        with tabs[2]:
            locked = is_step_locked(selected_student, "Exams")
            if locked:
                st.warning("🔒 Exams step is locked until Coursework step is completed.")
            with st.form("exams_form_staff"):
                st.subheader("Examinations")
                qual_options = ["N/A", "Not Taken", "Passed", "Failed", "Re-exam Scheduled"]
                qualifying = st.selectbox("Qualifying Exam Status (PhD)", qual_options, index=safe_index(qual_options, selected_student["qualifying_exam_status"]), disabled=locked)
                qualifying_date = st.text_input("Qualifying Exam Passed Date", selected_student["qualifying_exam_passed_date"], disabled=locked)
                wcomp_options = ["N/A", "Not Taken", "Passed", "Failed"]
                written_comp = st.selectbox("Written Comprehensive Status", wcomp_options, index=safe_index(wcomp_options, selected_student["written_comprehensive_status"]), disabled=locked)
                written_comp_date = st.text_input("Written Comprehensive Passed Date", selected_student["written_comprehensive_passed_date"], disabled=locked)
                ocomp_options = ["N/A", "Not Taken", "Passed", "Failed"]
                oral_comp = st.selectbox("Oral Comprehensive Status", ocomp_options, index=safe_index(ocomp_options, selected_student["oral_comprehensive_status"]), disabled=locked)
                oral_comp_date = st.text_input("Oral Comprehensive Passed Date", selected_student["oral_comprehensive_passed_date"], disabled=locked)
                gen_options = ["N/A", "Not Taken", "Passed", "Failed"]
                general = st.selectbox("General Exam Status (MS)", gen_options, index=safe_index(gen_options, selected_student["general_exam_status"]), disabled=locked)
                general_date = st.text_input("General Exam Passed Date", selected_student["general_exam_passed_date"], disabled=locked)
                final_options = ["Not Taken", "Passed", "Failed", "Re-exam Scheduled"]
                final = st.selectbox("Final Exam Status", final_options, index=safe_index(final_options, selected_student["final_exam_status"]), disabled=locked)
                final_date = st.text_input("Final Exam Passed Date", selected_student["final_exam_passed_date"], disabled=locked)
                if st.form_submit_button("Update Exams"):
                    if not locked:
                        df.loc[df["student_number"] == selected_student["student_number"], 
                               ["qualifying_exam_status","qualifying_exam_passed_date","written_comprehensive_status","written_comprehensive_passed_date","oral_comprehensive_status","oral_comprehensive_passed_date","general_exam_status","general_exam_passed_date","final_exam_status","final_exam_passed_date"]] = \
                               [qualifying, qualifying_date, written_comp, written_comp_date, oral_comp, oral_comp_date, general, general_date, final, final_date]
                        save_data(df)
                        st.success("✅ Updated!")
                        st.rerun()
                    else:
                        st.error("Cannot update: previous step not completed.")
        
        # Tab 3: Residency & Leave (no lock, always allowed)
        with tabs[3]:
            with st.form("residency_form_staff"):
                st.subheader("Residency")
                residency_used = st.number_input("Years of Residence Used", min_value=0, max_value=10, step=1, value=int(selected_student["residency_years_used"]))
                max_years = get_residency_max(selected_student["program"])
                st.info(f"Maximum allowed: {max_years} years")
                extension_count = st.number_input("Number of Extensions Granted", min_value=0, max_value=3, step=1, value=int(selected_student["extension_count"]))
                extension_end = st.text_input("Extension End Date (if applicable)", selected_student["extension_end_date"])
                st.subheader("Leave of Absence (LOA)")
                loa_start = st.text_input("LOA Start Date", selected_student["loa_start_date"])
                loa_end = st.text_input("LOA End Date", selected_student["loa_end_date"])
                loa_terms = st.number_input("Total LOA Terms (each term = 0.5 year)", min_value=0, max_value=4, step=1, value=int(selected_student["loa_total_terms"]))
                st.subheader("AWOL")
                awol_options = ["No", "Yes"]
                awol = st.selectbox("AWOL Status", awol_options, index=safe_index(awol_options, selected_student["awol_status"]))
                awol_lifted = st.text_input("AWOL Lifted Date", selected_student["awol_lifted_date"])
                if st.form_submit_button("Update Residency & Leave"):
                    df.loc[df["student_number"] == selected_student["student_number"], 
                           ["residency_years_used","extension_count","extension_end_date","loa_start_date","loa_end_date","loa_total_terms","awol_status","awol_lifted_date"]] = \
                           [residency_used, extension_count, extension_end, loa_start, loa_end, loa_terms, awol, awol_lifted]
                    save_data(df)
                    st.success("✅ Updated!")
                    st.rerun()
        
        # Tab 4: Graduation (with lock - defense must be passed)
        with tabs[4]:
            defense_completed = "Defense" in get_step_completion_status(selected_student)
            if not defense_completed:
                st.warning("🔒 Graduation step is locked until Defense (Final Exam) is passed.")
            with st.form("graduation_form_staff"):
                st.subheader("Graduation")
                yn_options = ["No", "Yes"]
                grad_applied = st.selectbox("Graduation Applied", yn_options, index=safe_index(yn_options, selected_student["graduation_applied"]), disabled=not defense_completed)
                grad_approved = st.selectbox("Graduation Approved", yn_options, index=safe_index(yn_options, selected_student["graduation_approved"]), disabled=not defense_completed)
                grad_date = st.text_input("Graduation Date (YYYY-MM-DD)", selected_student["graduation_date"], disabled=not defense_completed)
                st.subheader("Transfer Credit")
                transfer_units = st.number_input("Transfer Credits Approved (max 9 units)", min_value=0, max_value=9, step=1, value=int(selected_student["transfer_units_approved"]))
                if st.form_submit_button("Update Graduation & Transfer"):
                    if defense_completed or (grad_applied == "No" and grad_approved == "No"):
                        df.loc[df["student_number"] == selected_student["student_number"], 
                               ["graduation_applied","graduation_approved","graduation_date","transfer_units_approved"]] = \
                               [grad_applied, grad_approved, grad_date, transfer_units]
                        save_data(df)
                        st.success("✅ Updated!")
                        st.rerun()
                    else:
                        st.error("Cannot approve graduation until Final Exam is passed.")
        
        # Tab 5: Committee (no lock)
        with tabs[5]:
            with st.form("committee_form_staff"):
                st.subheader("Guidance / Advisory Committee")
                committee_members = st.text_area("Committee Members (one per line)", value=selected_student.get("committee_members", ""), height=150,
                                                 help="List names of major professor/adviser and other committee members.")
                committee_approval_date = st.text_input("Committee Approval Date (YYYY-MM-DD)", selected_student.get("committee_approval_date", ""))
                if st.form_submit_button("Update Committee"):
                    df.loc[df["student_number"] == selected_student["student_number"], "committee_members"] = committee_members
                    df.loc[df["student_number"] == selected_student["student_number"], "committee_approval_date"] = committee_approval_date
                    save_data(df)
                    st.success("Committee information updated!")
                    st.rerun()
        
        # Tab 6: Other (re-admission)
        with tabs[6]:
            with st.form("other_form_staff"):
                st.subheader("Re-admission (for students who exceeded time limit)")
                readmit_options = ["Not Applicable", "Applied", "Approved", "Denied"]
                re_status = st.selectbox("Re-admission Status", readmit_options, index=safe_index(readmit_options, selected_student["re_admission_status"]))
                re_date = st.text_input("Re-admission Date", selected_student["re_admission_date"])
                if st.form_submit_button("Update Re-admission"):
                    df.loc[df["student_number"] == selected_student["student_number"], ["re_admission_status","re_admission_date"]] = [re_status, re_date]
                    save_data(df)
                    st.success("✅ Updated!")
                    st.rerun()
        
        # Tab 7: Document Management (NEW)
        with tabs[7]:
            st.subheader("📄 Student Document Submissions")
            uploads_df = get_all_uploads_for_student(selected_student["student_number"])
            if len(uploads_df) == 0:
                st.info("No documents uploaded yet.")
            else:
                st.dataframe(uploads_df[["category", "original_filename", "upload_date", "status"]], use_container_width=True)
                
                # Review pending documents
                pending = uploads_df[uploads_df["status"] == "Pending"]
                if len(pending) > 0:
                    st.subheader("Review Pending Documents")
                    for _, doc in pending.iterrows():
                        with st.expander(f"{UPLOAD_DISPLAY_NAMES[doc['category']]} - {doc['original_filename']}"):
                            st.write(f"**Uploaded:** {doc['upload_date']}")
                            # Show file preview if image/pdf?
                            file_path = doc["file_path"]
                            if os.path.exists(file_path):
                                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                                    st.image(file_path, width=300)
                                else:
                                    st.write(f"File: {os.path.basename(file_path)}")
                            comment = st.text_area("Reviewer Comment", key=f"comment_{doc['category']}_{doc['upload_date']}")
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("✅ Approve", key=f"approve_{doc['category']}_{doc['upload_date']}"):
                                    uploads_df.loc[doc.name, "status"] = "Approved"
                                    uploads_df.loc[doc.name, "reviewer_comment"] = comment
                                    uploads_df.loc[doc.name, "reviewed_by"] = st.session_state.display_name
                                    uploads_df.loc[doc.name, "review_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    save_uploads(uploads_df)
                                    st.success("Document approved!")
                                    st.rerun()
                            with col2:
                                if st.button("❌ Reject", key=f"reject_{doc['category']}_{doc['upload_date']}"):
                                    uploads_df.loc[doc.name, "status"] = "Rejected"
                                    uploads_df.loc[doc.name, "reviewer_comment"] = comment
                                    uploads_df.loc[doc.name, "reviewed_by"] = st.session_state.display_name
                                    uploads_df.loc[doc.name, "review_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    save_uploads(uploads_df)
                                    st.success("Document rejected.")
                                    st.rerun()
        
        # Tab 8: Semester History (NEW)
        with tabs[8]:
            st.subheader("📚 Academic Semester Records")
            semesters = get_student_semesters(selected_student["student_number"])
            if len(semesters) == 0:
                st.info("No semester records found. Add first semester record below.")
            else:
                for _, sem in semesters.iterrows():
                    with st.expander(f"{sem['academic_year']} - {sem['semester']} (GWA: {sem['gwa']:.2f})"):
                        subjects = json.loads(sem["subjects_json"])
                        if subjects:
                            subj_df = pd.DataFrame(subjects)
                            st.dataframe(subj_df, use_container_width=True)
                        else:
                            st.caption("No subjects entered.")
                        st.caption(f"Total Units: {sem['total_units']}")
                        if pd.notna(sem["amis_file_path"]) and sem["amis_file_path"]:
                            st.write(f"AMIS Screenshot: {os.path.basename(sem['amis_file_path'])}")
            
            # Add new semester record
            st.subheader("➕ Add New Semester Record")
            with st.form("add_semester_form"):
                col1, col2 = st.columns(2)
                with col1:
                    academic_year = st.selectbox("Academic Year", ACADEMIC_YEARS)
                with col2:
                    semester = st.selectbox("Semester", SEMESTERS)
                
                st.markdown("**Subjects (Add at least one)**")
                subjects_list = []
                num_subjects = st.number_input("Number of subjects", min_value=1, max_value=10, step=1, value=1)
                for i in range(int(num_subjects)):
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        subj_name = st.text_input(f"Subject {i+1} Name", key=f"subj_name_{i}")
                    with col_b:
                        units = st.number_input(f"Units", min_value=0.0, max_value=6.0, step=0.5, key=f"units_{i}")
                    with col_c:
                        grade = st.number_input(f"Grade", min_value=1.0, max_value=5.0, step=0.01, key=f"grade_{i}")
                    if subj_name and units > 0:
                        subjects_list.append({"name": subj_name, "units": units, "grade": grade})
                
                amis_file = st.file_uploader("Upload AMIS Screenshot (optional)", type=["png", "jpg", "jpeg", "pdf"])
                submitted = st.form_submit_button("Save Semester Record")
                if submitted and subjects_list:
                    amis_path = ""
                    if amis_file:
                        amis_path = save_uploaded_file(selected_student["student_number"], "amis_screenshot", amis_file)
                        # Also create an upload record for AMIS
                        uploads = load_uploads()
                        new_upload = pd.DataFrame([{
                            "student_number": selected_student["student_number"],
                            "category": "amis_screenshot",
                            "file_path": amis_path,
                            "original_filename": amis_file.name,
                            "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "Pending",
                            "reviewer_comment": "",
                            "reviewed_by": "",
                            "review_date": ""
                        }])
                        uploads = pd.concat([uploads, new_upload], ignore_index=True)
                        save_uploads(uploads)
                    
                    gwa = add_semester_record(selected_student["student_number"], academic_year, semester, subjects_list, amis_path)
                    st.success(f"Semester record added! Computed GWA: {gwa:.2f}")
                    st.rerun()
                elif submitted and not subjects_list:
                    st.error("Please add at least one subject.")
    
    else:
        st.info("No students match the current search. Try a different name/number or add a new student below.")
    
    # Add New Student (existing functionality, unchanged)
    st.markdown("---")
    st.subheader("➕ Add New Student")
    with st.expander("Register New Student", expanded=True):
        with st.form(key="add_student_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                last_name = st.text_input("Last Name *", placeholder="Dela Cruz")
            with col2:
                first_name = st.text_input("First Name *", placeholder="Juan")
            with col3:
                middle_name = st.text_input("Middle Name", placeholder="Santos (optional)")
            
            col4, col5 = st.columns(2)
            with col4:
                student_number = st.text_input("Student Number *", placeholder="2025-00123")
            with col5:
                program = st.selectbox("Program *", options=PROGRAMS)
            
            col6, col7 = st.columns(2)
            with col6:
                selected_ay_range = st.selectbox("Academic Year *", options=ACADEMIC_YEARS, index=ACADEMIC_YEARS.index(f"{current_year}-{current_year+1}") if f"{current_year}-{current_year+1}" in ACADEMIC_YEARS else 0)
                ay_start = int(selected_ay_range.split("-")[0])
            with col7:
                semester = st.selectbox("Semester *", options=SEMESTERS)
            st.caption(f"📅 {format_ay(ay_start, semester)}")
            
            col8, col9 = st.columns(2)
            with col8:
                advisor = st.text_input("Advisor (optional)", placeholder="Dr. Faustino-Eslava")
            with col9:
                st.empty()
            
            st.markdown("---")
            st.markdown("### Initial Milestone Status (optional)")
            col10, col11, col12 = st.columns(3)
            with col10:
                gwa = st.number_input("Initial GWA", min_value=1.0, max_value=5.0, step=0.01, value=2.0, help="1.0 best, 5.0 failing")
            with col11:
                thesis_units_taken = st.number_input("Thesis Units Taken", min_value=0, max_value=20, step=1, value=0)
                st.caption(get_thesis_pattern_description(program))
            with col12:
                pos_status = st.selectbox("POS Status", ["Not Filed", "Pending", "Approved"])
            
            col13, col14, col15 = st.columns(3)
            with col13:
                comp_exam = st.selectbox("Comprehensive Exam (PhD)", ["N/A", "Not Taken", "Passed", "Failed"])
            with col14:
                general_exam = st.selectbox("General Exam (MS)", ["N/A", "Not Taken", "Passed", "Failed"])
            with col15:
                final_exam = st.selectbox("Final Exam Status", ["Not Taken", "Passed", "Failed"])
            
            submitted = st.form_submit_button("Register Student")
            
            if submitted:
                errors = []
                if not last_name:
                    errors.append("Last Name is required.")
                if not first_name:
                    errors.append("First Name is required.")
                if not student_number:
                    errors.append("Student Number is required.")
                if student_number in df["student_number"].values:
                    errors.append("Student number already exists. Please use a unique number.")
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    middle = f" {middle_name.strip()}" if middle_name.strip() else ""
                    full_name = f"{last_name.strip()}, {first_name.strip()}{middle}"
                    new_row = create_default_data().iloc[0].to_dict()
                    new_row.update({
                        "student_number": student_number.strip(),
                        "name": full_name,
                        "last_name": last_name.strip(),
                        "first_name": first_name.strip(),
                        "middle_name": middle_name.strip(),
                        "program": program,
                        "advisor": advisor.strip() if advisor else "Not assigned",
                        "ay_start": ay_start,
                        "semester": semester,
                        "pos_status": pos_status,
                        "gwa": gwa,
                        "thesis_units_taken": thesis_units_taken,
                        "thesis_units_limit": get_thesis_limit(program),
                        "residency_max_years": get_residency_max(program),
                        "committee_members": "",
                        "committee_approval_date": "",
                        "profile_pic": "",
                        "pos_submitted_date": "",
                        "pos_approved_date": "",
                        "total_units_taken": 0,
                        "total_units_required": 24,
                        "thesis_outline_approved": "No",
                        "thesis_outline_approved_date": "",
                        "thesis_status": "Not Started",
                        "qualifying_exam_status": comp_exam if program.startswith("PhD") else "N/A",
                        "qualifying_exam_passed_date": "",
                        "written_comprehensive_status": "N/A",
                        "written_comprehensive_passed_date": "",
                        "oral_comprehensive_status": "N/A",
                        "oral_comprehensive_passed_date": "",
                        "general_exam_status": general_exam if is_master_program(program) else "N/A",
                        "general_exam_passed_date": "",
                        "final_exam_status": final_exam,
                        "final_exam_passed_date": "",
                        "residency_years_used": 0,
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
                    st.success(f"✅ Student {full_name} (Number: {student_number}) registered successfully!")
                    st.rerun()

# ==================== ADVISER VIEW (with notification panel) ====================
elif role == "Faculty Adviser":
    st.subheader(f"👨‍🏫 Your Advisees")
    all_advisors = sorted(df["advisor"].unique())
    if len(all_advisors) == 0:
        st.warning("No advisors found in the data.")
    else:
        selected_advisor = st.selectbox("Select your name", all_advisors)
        advisees = df[df["advisor"] == selected_advisor].copy()
        if len(advisees) == 0:
            st.warning("No students assigned to this advisor.")
        else:
            # Notification panel
            notifications = get_adviser_notifications(selected_advisor)
            if notifications:
                st.markdown("### 🔔 Notifications")
                for notif in notifications:
                    if notif["severity"] == "error":
                        st.error(f"{notif['student']} ({notif['student_number']}): {notif['message']}")
                    else:
                        st.warning(f"{notif['student']} ({notif['student_number']}): {notif['message']}")
                st.markdown("---")
            else:
                st.success("✅ No pending notifications.")
            
            search_adv = st.text_input("🔍 Search by name or student number", placeholder="e.g., Cruz or S001")
            filtered_advisees = filter_dataframe(search_adv, advisees)
            filtered_advisees["academic_year"] = filtered_advisees.apply(lambda row: format_ay(row["ay_start"], row["semester"]), axis=1)
            filtered_advisees["warnings"] = filtered_advisees.apply(lambda row: "\n".join(get_all_warnings(row)), axis=1)
            filtered_advisees["deadline_alerts"] = filtered_advisees.apply(lambda row: "\n".join(check_deadline_alerts(row)), axis=1)
            display_cols = ["student_number", "name", "program", "academic_year", "gwa", "thesis_units_taken", "thesis_units_limit", "pos_status", "final_exam_status", "warnings"]
            st.dataframe(filtered_advisees[display_cols], width='stretch')
            
            if len(filtered_advisees) > 0:
                st.markdown("---")
                st.subheader("📌 Detailed View")
                for _, row in filtered_advisees.iterrows():
                    with st.expander(f"{row['name']} ({row['student_number']})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Program:** {row['program']}")
                            st.markdown(f"**Academic Year:** {format_ay(row['ay_start'], row['semester'])}")
                            st.markdown(f"**GWA:** {row['gwa']}")
                            st.markdown(f"**POS Status:** {row['pos_status']}")
                            st.markdown(f"**Thesis Units:** {row['thesis_units_taken']}/{row['thesis_units_limit']}")
                        with col2:
                            st.markdown(f"**General Exam:** {row['general_exam_status']}")
                            st.markdown(f"**Comprehensive Exam (PhD):** Written: {row['written_comprehensive_status']}, Oral: {row['oral_comprehensive_status']}")
                            st.markdown(f"**Final Exam:** {row['final_exam_status']}")
                            st.markdown(f"**Residency:** {row['residency_years_used']}/{get_residency_max(row['program'])} years")
                        
                        # Workflow progress for adviser
                        display_workflow_progress(row)
                        
                        pic_path = get_profile_picture_path(row["student_number"])
                        if pic_path and os.path.exists(pic_path):
                            st.image(pic_path, width=100, caption="Profile Picture")
                        
                        alerts = check_deadline_alerts(row)
                        if alerts:
                            for alert in alerts:
                                st.error(alert)
                        warnings_text = row["warnings"]
                        if any("⚠️" in w for w in warnings_text.split("\n")):
                            for w in warnings_text.split("\n"):
                                st.error(w)
                        else:
                            st.success(warnings_text)
            else:
                st.info("No matching students.")
    st.info("📌 Read-only view. For updates, contact SESAM Staff.")

# ==================== STUDENT VIEW (enhanced with uploads and progress) ====================
elif role == "Student":
    st.subheader(f"📘 Your Academic Dashboard ({st.session_state.display_name})")
    student_record = df[df["name"] == st.session_state.display_name]
    if len(student_record) == 0:
        st.error("Your record not found. Please contact SESAM Staff.")
    else:
        student = student_record.iloc[0]
        
        # Display workflow progress prominently
        st.markdown("### 🎯 Your Milestone Progress")
        display_workflow_progress(student)
        
        # Deadline alerts and warnings
        alerts = check_deadline_alerts(student)
        if alerts:
            for alert in alerts:
                st.error(alert)
        warnings = get_all_warnings(student)
        if any("⚠️" in w for w in warnings):
            for w in warnings:
                st.error(w)
        else:
            st.success("\n".join(warnings))
        
        # Profile and basic info
        pic_path = get_profile_picture_path(student["student_number"])
        if pic_path and os.path.exists(pic_path):
            col_pic, col_info = st.columns([1, 2])
            with col_pic:
                st.image(pic_path, width=150, caption="Your Profile Picture")
            with col_info:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Student Number", student["student_number"])
                    st.metric("Program", student["program"])
                    st.metric("Academic Year", format_ay(student["ay_start"], student["semester"]))
                with col2:
                    st.metric("Advisor", student["advisor"])
                    st.metric("GWA (Official)", f"{student['gwa']:.2f}")
                    st.metric("POS Status", student["pos_status"])
                with col3:
                    limit = get_thesis_limit(student["program"])
                    st.metric("Thesis Units", f"{student['thesis_units_taken']} / {limit}")
                    st.metric("Residency", f"{student['residency_years_used']} / {get_residency_max(student['program'])} years")
                    st.metric("Final Exam", student["final_exam_status"])
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Student Number", student["student_number"])
                st.metric("Program", student["program"])
                st.metric("Academic Year", format_ay(student["ay_start"], student["semester"]))
            with col2:
                st.metric("Advisor", student["advisor"])
                st.metric("GWA (Official)", f"{student['gwa']:.2f}")
                st.metric("POS Status", student["pos_status"])
            with col3:
                limit = get_thesis_limit(student["program"])
                st.metric("Thesis Units", f"{student['thesis_units_taken']} / {limit}")
                st.metric("Residency", f"{student['residency_years_used']} / {get_residency_max(student['program'])} years")
                st.metric("Final Exam", student["final_exam_status"])
        
        # Coursework progress
        st.markdown("---")
        st.subheader("📚 Coursework Progress")
        progress = compute_coursework_progress(student)
        st.progress(progress / 100, text=f"{progress}% completed ({student['total_units_taken']} of {student['total_units_required']} units)")
        st.caption(f"Remaining units: {max(0, student['total_units_required'] - student['total_units_taken'])}")
        
        # Document upload section (new)
        st.markdown("---")
        st.subheader("📎 Submit Requirements")
        with st.expander("Upload Documents for Review", expanded=True):
            selected_category = st.selectbox("Document Type", options=UPLOAD_CATEGORIES, format_func=lambda x: UPLOAD_DISPLAY_NAMES[x])
            uploaded_file = st.file_uploader(f"Upload {UPLOAD_DISPLAY_NAMES[selected_category]}", type=["pdf", "png", "jpg", "jpeg", "doc", "docx"])
            
            if uploaded_file and st.button("Submit Document"):
                file_path = save_uploaded_file(student["student_number"], selected_category, uploaded_file)
                if file_path:
                    uploads = load_uploads()
                    new_upload = pd.DataFrame([{
                        "student_number": student["student_number"],
                        "category": selected_category,
                        "file_path": file_path,
                        "original_filename": uploaded_file.name,
                        "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "Pending",
                        "reviewer_comment": "",
                        "reviewed_by": "",
                        "review_date": ""
                    }])
                    uploads = pd.concat([uploads, new_upload], ignore_index=True)
                    save_uploads(uploads)
                    st.success(f"{UPLOAD_DISPLAY_NAMES[selected_category]} uploaded successfully! Waiting for staff review.")
                    st.rerun()
        
        # Show submission status
        st.subheader("📋 Document Submission Status")
        uploads_df = get_all_uploads_for_student(student["student_number"])
        if len(uploads_df) > 0:
            status_df = uploads_df[["category", "original_filename", "upload_date", "status", "reviewer_comment"]].copy()
            status_df["category"] = status_df["category"].map(UPLOAD_DISPLAY_NAMES)
            st.dataframe(status_df, use_container_width=True)
        else:
            st.info("No documents submitted yet.")
        
        # Semester history view (read-only)
        st.subheader("📚 Your Academic History")
        semesters = get_student_semesters(student["student_number"])
        if len(semesters) == 0:
            st.info("No semester records found. Your adviser will add your academic records.")
        else:
            for _, sem in semesters.iterrows():
                with st.expander(f"{sem['academic_year']} - {sem['semester']} (GWA: {sem['gwa']:.2f})"):
                    subjects = json.loads(sem["subjects_json"])
                    if subjects:
                        subj_df = pd.DataFrame(subjects)
                        st.dataframe(subj_df, use_container_width=True)
                    st.caption(f"Total Units: {sem['total_units']}")
        
        # Committee information (if any)
        if student.get("committee_members"):
            with st.expander("📋 Your Guidance/Advisory Committee"):
                st.text_area("Committee Members", value=student["committee_members"], height=120, disabled=True)
                if student.get("committee_approval_date"):
                    st.caption(f"Approved on: {student['committee_approval_date']}")
        
        # Milestone summary
        st.markdown("---")
        st.subheader("📌 Milestone Summary")
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
                student["general_exam_status"] if is_master_program(student["program"]) else student["qualifying_exam_status"],
                student["written_comprehensive_status"] if is_phd_program(student["program"]) else "N/A",
                student["oral_comprehensive_status"] if is_phd_program(student["program"]) else "N/A",
                student["thesis_outline_approved"],
                student["final_exam_status"]
            ]
        })
        st.dataframe(milestone_df, width='stretch', hide_index=True)
        st.info("📌 For corrections or updates, please contact your adviser or SESAM Staff.")

# ==================== FOOTER ====================
st.markdown("---")
st.caption("SESAM KMIS – Graduate Student Lifecycle Management v3.0 | Workflow Engine + Document Management")
