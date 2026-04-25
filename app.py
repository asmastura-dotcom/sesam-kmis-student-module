"""
SESAM KMIS - Graduate Student Lifecycle Management System (Enhanced UI)
Author: [Your Name]
Date: [Current Date]
Description: Full workflow-based lifecycle management, now with student milestone submission + staff validation.
"""

import streamlit as st
import pandas as pd
import os
import json
from datetime import date, datetime
import shutil

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="SESAM Graduate Lifecycle Manager",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS FOR MODERN UI ====================
st.markdown("""
<style>
    .main > div { padding: 0 1rem; }
    .css-1r6slb0, .element-container, .stExpander {
        background: white;
        border-radius: 12px;
        padding: 0.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
    }
    .stExpander:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    [data-testid="stMetric"] {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    h1, h2, h3 { font-weight: 600 !important; letter-spacing: -0.01em; }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-right: 0.5rem;
    }
    .badge-success { background: #d4edda; color: #155724; }
    .badge-warning { background: #fff3cd; color: #856404; }
    .badge-danger { background: #f8d7da; color: #721c24; }
    .badge-info { background: #d1ecf1; color: #0c5460; }
    .stProgress > div > div { background-color: #2c7da0; border-radius: 10px; }
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .dataframe th { background-color: #2c3e50 !important; color: white !important; }
    .dataframe tr:hover { background-color: #f1f9ff !important; }
    .stButton button {
        border-radius: 20px;
        font-weight: 500;
        transition: 0.2s;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    button[data-testid="baseButton-secondary"] {
        padding: 0.25rem 0.75rem !important;
        font-size: 0.8rem !important;
        min-height: 32px !important;
    }
    .stButton button[kind="secondary"] {
        padding: 0.2rem 0.6rem !important;
        font-size: 0.75rem !important;
    }
    div[data-testid="column"]:has(> div > button) button {
        padding: 0.2rem 0.8rem !important;
        font-size: 0.75rem !important;
        min-height: 30px !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background: #f8f9fa;
        border-radius: 12px;
        padding: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 20px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2c7da0;
        color: white;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(135deg, #f8fafc 0%, #eef2f5 100%);
        border-right: 1px solid rgba(0,0,0,0.05);
    }
    section[data-testid="stSidebar"] .css-1d391kg {
        background: transparent;
    }
    .sidebar-profile {
        background: white;
        border-radius: 20px;
        padding: 1.2rem 1rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        text-align: center;
    }
    .sidebar-profile h3 {
        margin: 0 0 0.25rem 0;
        font-size: 1.2rem;
        font-weight: 600;
        color: #1e293b;
    }
    .sidebar-role {
        font-size: 0.8rem;
        color: #2c7da0;
        background: #e6f4f5;
        display: inline-block;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        margin-top: 0.25rem;
    }
    .sidebar-logout button {
        background: white !important;
        border: 1px solid #e2e8f0 !important;
        color: #475569 !important;
        border-radius: 40px !important;
        padding: 0.4rem 1rem !important;
        font-weight: 500 !important;
        transition: all 0.2s;
    }
    .sidebar-logout button:hover {
        background: #f1f5f9 !important;
        border-color: #cbd5e1 !important;
        transform: none !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    hr.sidebar-divider {
        margin: 1rem 0;
        border: 0;
        height: 1px;
        background: linear-gradient(to right, #cbd5e1, transparent);
    }
    .sidebar-footer {
        font-size: 0.7rem;
        color: #94a3b8;
        text-align: center;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

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

# ==================== USER AUTH ====================
USERS = {
    "staff1": {"password": "admin123", "role": "SESAM Staff", "display_name": "SESAM Administrator"},
    "adviser1": {"password": "adv123", "role": "Faculty Adviser", "display_name": "Dr. Eslava"},
    "adviser2": {"password": "adv456", "role": "Faculty Adviser", "display_name": "Dr. Sanchez"},
    "student1": {"password": "stu123", "role": "Student", "display_name": "Cruz, Juan M."},
    "student2": {"password": "stu456", "role": "Student", "display_name": "Santos, Maria L."}
}

# ==================== PROGRAM DEFINITIONS ====================
PROGRAMS = [
    "MS Environmental Science",
    "PhD Environmental Science",
    "PhD Environmental Diplomacy and Negotiations",
    "Master in Resilience Studies (M-ReS)",
    "Professional Masters in Tropical Marine Ecosystems Management (PM-TMEM)",
    "PhD by Research Environmental Science"
]

SEMESTERS = ["1st Sem", "2nd Sem", "Summer"]
current_year = date.today().year
ACADEMIC_YEARS = [f"{year}-{year+1}" for year in range(current_year-5, current_year+6)]

def is_master_program(program):
    return program.startswith("MS") or program.startswith("Master") or program.startswith("Professional Masters")

def is_phd_program(program):
    return program.startswith("PhD") and "by Research" not in program

def is_phd_by_research(program):
    return "PhD by Research" in program

def get_thesis_limit_from_program(program):
    return 6 if is_master_program(program) else 12

def get_residency_max_from_program(program):
    return 5 if is_master_program(program) else 7

def format_ay(ay_start, semester):
    return f"A.Y. {ay_start}-{ay_start+1} ({semester})"

def get_thesis_pattern_description(program):
    if is_master_program(program):
        return "💡 MS: 6 thesis units (2-2-2 or 3-3)"
    else:
        return "💡 PhD: 12 dissertation units (3-3-3-3 or 4-4-4)"

# ==================== WORKFLOW ENGINE ====================
WORKFLOW_STEPS = ["Committee", "Coursework", "Exams", "POS", "Thesis", "Defense", "Graduation"]

def get_step_completion_status(student_row):
    program = student_row["program"]
    completed = set()
    if pd.notna(student_row.get("committee_approval_date")) and student_row.get("committee_approval_date"):
        completed.add("Committee")
    if student_row.get("total_units_taken", 0) >= student_row.get("total_units_required", 24):
        completed.add("Coursework")
    if is_master_program(program):
        if student_row.get("general_exam_status") == "Passed":
            completed.add("Exams")
    else:
        if (student_row.get("qualifying_exam_status") == "Passed" and
            student_row.get("written_comprehensive_status") == "Passed" and
            student_row.get("oral_comprehensive_status") == "Passed"):
            completed.add("Exams")
    if student_row.get("pos_status") == "Approved":
        completed.add("POS")
    if (student_row.get("thesis_outline_approved") == "Yes" and
        student_row.get("thesis_status") not in ["Not Started", ""]):
        completed.add("Thesis")
    if student_row.get("final_exam_status") == "Passed":
        completed.add("Defense")
    if student_row.get("graduation_approved") == "Yes":
        completed.add("Graduation")
    return completed

def get_next_required_step(student_row):
    completed = get_step_completion_status(student_row)
    for step in WORKFLOW_STEPS:
        if step not in completed:
            return step
    return "Complete"

def is_step_locked(student_row, step_name):
    step_index = WORKFLOW_STEPS.index(step_name)
    if step_index == 0:
        return False
    previous_step = WORKFLOW_STEPS[step_index - 1]
    completed = get_step_completion_status(student_row)
    return previous_step not in completed

# ==================== SEMESTER TRACKING ====================
SEMESTER_FILE = "semester_records.csv"

def load_semester_records():
    if os.path.exists(SEMESTER_FILE):
        df = pd.read_csv(SEMESTER_FILE)
        if "subjects_json" not in df.columns:
            df["subjects_json"] = "[]"
        df["subjects_json"] = df["subjects_json"].fillna("[]")
        return df
    else:
        return pd.DataFrame(columns=["student_number", "academic_year", "semester", "subjects_json", "total_units", "gwa", "amis_file_path"])

def save_semester_records(df):
    df.to_csv(SEMESTER_FILE, index=False)

def compute_gwa_from_subjects(subjects_list):
    if not subjects_list:
        return 0.0
    total_units = 0
    total_grade_points = 0
    for subj in subjects_list:
        units = float(subj.get("units", 0))
        grade = float(subj.get("grade", 0))
        total_units += units
        total_grade_points += units * grade
    return total_grade_points / total_units if total_units > 0 else 0.0

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
    update_student_academic_summary(student_number)
    return gwa

def update_student_academic_summary(student_number):
    semesters = get_student_semesters(student_number)
    if len(semesters) == 0:
        return
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
        update_main_student_gwa_and_units(student_number, cumulative_gwa, total_units_all)

def update_main_student_gwa_and_units(student_number, cumulative_gwa, total_units):
    df = load_data()
    idx = df[df["student_number"] == student_number].index
    if len(idx) > 0:
        df.loc[idx, "gwa"] = cumulative_gwa
        df.loc[idx, "total_units_taken"] = total_units
        save_data(df)

# ==================== DOCUMENT UPLOAD SYSTEM (General) ====================
UPLOAD_FOLDER = "student_uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

UPLOAD_CATEGORIES = ["admission_letter", "amis_screenshot", "committee_form", "plan_of_study", "thesis_file"]
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
        return pd.DataFrame(columns=["student_number", "category", "file_path", "original_filename", "upload_date", "status", "reviewer_comment", "reviewed_by", "review_date"])

def save_uploads(df):
    df.to_csv(UPLOAD_FILE, index=False)

def save_uploaded_file(student_number, category, uploaded_file):
    if uploaded_file is None:
        return None
    student_folder = os.path.join(UPLOAD_FOLDER, student_number)
    if not os.path.exists(student_folder):
        os.makedirs(student_folder)
    ext = uploaded_file.name.split('.')[-1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{category}_{timestamp}.{ext}"
    filepath = os.path.join(student_folder, filename)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filepath

def get_all_uploads_for_student(student_number):
    df = load_uploads()
    return df[df["student_number"] == student_number].copy()

# ==================== MILESTONE SUBMISSION & VALIDATION ====================
MILESTONE_REQUESTS_FILE = "milestone_requests.csv"

# Define milestone types student can submit, and the corresponding field to update in student record
MILESTONE_TYPES = [
    {"label": "General Exam (MS) - Passed", "field": "general_exam_status", "value": "Passed"},
    {"label": "Qualifying Exam (PhD) - Passed", "field": "qualifying_exam_status", "value": "Passed"},
    {"label": "Written Comprehensive Exam (PhD) - Passed", "field": "written_comprehensive_status", "value": "Passed"},
    {"label": "Oral Comprehensive Exam (PhD) - Passed", "field": "oral_comprehensive_status", "value": "Passed"},
    {"label": "Plan of Study (POS) - Approved", "field": "pos_status", "value": "Approved"},
    {"label": "Thesis Outline - Approved", "field": "thesis_outline_approved", "value": "Yes"},
    {"label": "Final Exam - Passed", "field": "final_exam_status", "value": "Passed"},
    {"label": "Graduation - Applied", "field": "graduation_applied", "value": "Yes"}
]

def load_milestone_requests():
    if os.path.exists(MILESTONE_REQUESTS_FILE):
        return pd.read_csv(MILESTONE_REQUESTS_FILE)
    else:
        return pd.DataFrame(columns=[
            "request_id", "student_number", "student_name", "milestone_label", "target_field", "target_value",
            "submitted_date", "file_path", "original_filename", "status", "reviewer_comment", "reviewed_by", "review_date"
        ])

def save_milestone_requests(df):
    df.to_csv(MILESTONE_REQUESTS_FILE, index=False)

def save_milestone_file(student_number, milestone_label, uploaded_file):
    if uploaded_file is None:
        return None
    milestone_folder = os.path.join(UPLOAD_FOLDER, student_number, "milestone_proofs")
    if not os.path.exists(milestone_folder):
        os.makedirs(milestone_folder)
    ext = uploaded_file.name.split('.')[-1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_label = milestone_label.replace(" ", "_").replace("/", "_")
    filename = f"{safe_label}_{timestamp}.{ext}"
    filepath = os.path.join(milestone_folder, filename)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filepath

# ==================== NOTIFICATION SYSTEM ====================
def get_adviser_notifications(adviser_name):
    df = load_data()
    advisees = df[df["advisor"] == adviser_name].copy()
    notifications = []
    for _, student in advisees.iterrows():
        if student["gwa"] > 2.00:
            notifications.append({"student": student["name"], "student_number": student["student_number"], "type": "GWA Warning", "message": f"GWA {student['gwa']:.2f} exceeds 2.00", "severity": "error"})
        uploads = get_all_uploads_for_student(student["student_number"])
        for _, upload in uploads.iterrows():
            if upload["status"] == "Pending":
                upload_date = datetime.strptime(upload["upload_date"], "%Y-%m-%d %H:%M:%S")
                if (datetime.now() - upload_date).days > 7:
                    notifications.append({"student": student["name"], "student_number": student["student_number"], "type": "Overdue Upload", "message": f"{UPLOAD_DISPLAY_NAMES[upload['category']]} pending >7 days", "severity": "warning"})
        next_step = get_next_required_step(student)
        residency_used = student["residency_years_used"]
        if next_step == "Exams" and residency_used >= 2:
            notifications.append({"student": student["name"], "student_number": student["student_number"], "type": "Milestone Overdue", "message": "Exams due by 2nd year", "severity": "error"})
    return notifications

# ==================== PROFILE PICTURE ====================
PIC_FOLDER = "profile_pics"
if not os.path.exists(PIC_FOLDER):
    os.makedirs(PIC_FOLDER)

def save_profile_picture(student_number, uploaded_file):
    if uploaded_file is None:
        return None
    ext = uploaded_file.name.split('.')[-1].lower()
    if ext not in ['jpg', 'jpeg', 'png', 'gif']:
        st.error("Unsupported file format.")
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

# ==================== COMMITTEE HELPERS ====================
def get_committee_title(program):
    if is_phd_program(program) or is_phd_by_research(program):
        return "Advisory Committee"
    else:
        return "Guidance Committee"

def parse_committee_members(members_str):
    if not members_str or pd.isna(members_str):
        return []
    members = []
    for line in members_str.strip().split('\n'):
        if '|' in line:
            name, role = line.split('|', 1)
            members.append({"name": name.strip(), "role": role.strip()})
        else:
            members.append({"name": line.strip(), "role": "Member"})
    return members

def format_committee_members(members_list):
    return "\n".join([f"{m['name']}|{m['role']}" for m in members_list])

# ==================== DATA LOADING ====================
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
        "committee_members_structured": ["Dr. Eslava|Chair (Major Professor)\nDr. Sanchez|Member", "Dr. Sanchez|Chair (Adviser)\nDr. Eslava|Member\nDr. Reyes|Member", "Dr. Eslava|Chair", "Dr. Sanchez|Chair\nDr. Eslava|Member\nDr. Cruz|Member", "Dr. Eslava|Chair"],
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
    if "committee_members_structured" not in df.columns:
        df["committee_members_structured"] = ""
    if "committee_approval_date" not in df.columns:
        df["committee_approval_date"] = ""
    if "year_admitted" in df.columns and "ay_start" not in df.columns:
        df["ay_start"] = df["year_admitted"]
        df["semester"] = "1st Sem"
        df = df.drop(columns=["year_admitted"])
    if "ay_start" not in df.columns:
        df["ay_start"] = 2024
    if "semester" not in df.columns:
        df["semester"] = "1st Sem"
    numeric_int_cols = ["thesis_units_taken", "thesis_units_limit", "total_units_taken", "total_units_required", "residency_years_used", "residency_max_years", "extension_count", "loa_total_terms", "transfer_units_approved", "ay_start"]
    for col in numeric_int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    if "gwa" in df.columns:
        df["gwa"] = pd.to_numeric(df["gwa"], errors='coerce').fillna(2.0).astype(float)
    for idx, row in df.iterrows():
        program = str(row["program"]).strip()
        if program not in PROGRAMS:
            program = PROGRAMS[0] if program == "MS" else PROGRAMS[1] if program == "PhD" else PROGRAMS[0]
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
    # Override GWA with computed from semesters
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

# ==================== WARNING FUNCTIONS ====================
def get_warning_text(program, units_taken):
    limit = get_thesis_limit(program)
    try:
        units_taken = float(units_taken)
    except:
        return "⚠️ Thesis units error"
    if units_taken > limit:
        return f"⚠️ Units exceeded: {units_taken}/{limit}"
    return f"✅ Thesis units: {units_taken}/{limit}"

def check_residency_warning(row):
    used = row.get("residency_years_used", 0)
    max_years = get_residency_max(row["program"])
    if used >= max_years:
        return f"⚠️ Residency limit reached ({used}/{max_years})"
    elif used >= max_years - 1:
        return f"⚠️ Approaching limit ({used}/{max_years})"
    return f"✅ Residency: {used}/{max_years}"

def check_gwa_warning(gwa):
    if gwa > 2.00:
        return f"⚠️ GWA {gwa:.2f} > 2.00"
    return f"✅ GWA {gwa:.2f}"

def check_awol_warning(row):
    return "⚠️ AWOL" if row.get("awol_status") == "Yes" else "✅ No AWOL"

def check_loa_warning(row):
    terms = row.get("loa_total_terms", 0)
    if terms > 2:
        return f"⚠️ LOA exceeds 2 years ({terms} terms)"
    elif terms > 0:
        return f"ℹ️ LOA: {terms} term(s)"
    return "✅ No LOA"

def check_thesis_outline_deadline(row):
    program = row["program"]
    units = row["thesis_units_taken"]
    approved = row["thesis_outline_approved"]
    if is_master_program(program) and units >= 4 and approved != "Yes":
        return "⚠️ Outline overdue (by 2nd thesis sem)"
    if is_phd_program(program) and units >= 8 and approved != "Yes":
        return "⚠️ Outline overdue (by 3rd diss sem)"
    return "✅ Outline on track"

def check_qualifying_exam_deadline(row):
    if is_phd_program(row["program"]) and row["residency_years_used"] >= 1 and row["qualifying_exam_status"] not in ["Passed", "N/A"]:
        return "⚠️ Qualifying exam due before 2nd sem"
    return "✅ Qualifying exam on track"

def check_comprehensive_exam_deadline(row):
    if (is_phd_program(row["program"]) and row["total_units_taken"] >= row["total_units_required"] and row["written_comprehensive_status"] != "Passed"):
        return "⚠️ Written comprehensive pending"
    return "✅ Comprehensive on track"

def get_all_warnings(row):
    warnings = []
    for check in [get_warning_text, check_residency_warning, check_gwa_warning, check_awol_warning, check_loa_warning, check_thesis_outline_deadline, check_qualifying_exam_deadline, check_comprehensive_exam_deadline]:
        msg = check(row) if "row" in check.__code__.co_varnames else check(row["program"], row["thesis_units_taken"]) if check.__name__ == "get_warning_text" else check(row["gwa"])
        if "⚠️" in msg:
            warnings.append(msg)
    return warnings if warnings else ["✅ All rules satisfied"]

def check_deadline_alerts(row):
    alerts = []
    program = row["program"]
    thesis_units = row["thesis_units_taken"]
    outline_approved = row["thesis_outline_approved"]
    pos_status = row["pos_status"]
    residency_used = row.get("residency_years_used", 0)
    if program.startswith("MS") and residency_used >= 1 and pos_status not in ["Approved", "Completed"]:
        alerts.append("⚠️ POS should be approved by 2nd semester")
    elif program.startswith("PhD") and row.get("qualifying_exam_status") == "Passed" and pos_status != "Approved":
        alerts.append("⚠️ POS pending after qualifying exam")
    if program.startswith("MS") and thesis_units >= 4 and outline_approved != "Yes":
        alerts.append("⚠️ Thesis outline overdue")
    if program.startswith("PhD") and thesis_units >= 8 and outline_approved != "Yes":
        alerts.append("⚠️ Dissertation outline overdue")
    if program.startswith("PhD") and residency_used >= 1 and row["qualifying_exam_status"] not in ["Passed", "N/A"]:
        alerts.append("⚠️ Qualifying exam should be taken before 2nd semester")
    if program.startswith("PhD") and row["total_units_taken"] >= row["total_units_required"] and row["written_comprehensive_status"] != "Passed":
        alerts.append("⚠️ Written comprehensive exam pending")
    return alerts

def compute_coursework_progress(row):
    taken = row.get("total_units_taken", 0)
    required = row.get("total_units_required", 24)
    return min(100, int((taken / required) * 100)) if required > 0 else 0

# ==================== UI HELPER FUNCTIONS ====================
def safe_index(options, value):
    try:
        return options.index(value)
    except ValueError:
        return 0

def filter_dataframe(search_term, data):
    if not search_term:
        return data
    mask = data["name"].str.contains(search_term, case=False, na=False) | data["student_number"].str.contains(search_term, case=False, na=False)
    return data[mask]

def display_workflow_grid(completed_steps, next_step):
    cols = st.columns(4)
    for i, step in enumerate(WORKFLOW_STEPS):
        with cols[i % 4]:
            if step in completed_steps:
                st.markdown(f'<div style="background:#e8f5e9; border-radius:12px; padding:0.75rem; text-align:center; margin:0.25rem;"><div style="font-size:1.2rem;">✅</div><div style="font-weight:500;">{step}</div><div style="font-size:0.7rem; color:#2e7d32;">Completed</div></div>', unsafe_allow_html=True)
            elif step == next_step:
                st.markdown(f'<div style="background:#fff3e0; border:2px solid #ff9800; border-radius:12px; padding:0.75rem; text-align:center; margin:0.25rem;"><div style="font-size:1.2rem;">⏳</div><div style="font-weight:500;">{step}</div><div style="font-size:0.7rem; color:#e65100;">Next Required</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="background:#f5f5f5; border-radius:12px; padding:0.75rem; text-align:center; margin:0.25rem; opacity:0.6;"><div style="font-size:1.2rem;">🔒</div><div style="font-weight:500;">{step}</div><div style="font-size:0.7rem; color:#757575;">Locked</div></div>', unsafe_allow_html=True)

# ==================== LOGIN PAGE ====================
if not st.session_state.logged_in:
    st.markdown('<div style="text-align:center; margin-bottom:2rem;"><h1>🎓 SESAM KMIS</h1><p style="color:#6c757d;">Graduate Student Lifecycle Management System</p></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container():
            st.markdown("#### 🔐 Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login", use_container_width=True):
                if username in USERS and USERS[username]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = USERS[username]["role"]
                    st.session_state.display_name = USERS[username]["display_name"]
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            st.caption("Demo: staff1/admin123 | adviser1/adv123 | student1/stu123")
    st.stop()

# ==================== DATA LOAD ====================
df = load_data()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-profile">
        <h3>👤 {st.session_state.display_name}</h3>
        <div class="sidebar-role">{st.session_state.role}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-logout">', unsafe_allow_html=True)
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        for key in ["username", "role", "display_name", "selected_student"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="sidebar-footer">
        Version 3.0 | Lifecycle Management<br>
        © SESAM 2026
    </div>
    """, unsafe_allow_html=True)

# ==================== MAIN ====================
st.title("🎓 SESAM Graduate Student Lifecycle Management")
st.caption("Complete workflow tracking from admission to graduation")

role = st.session_state.role

# ==================== STAFF VIEW ====================
if role == "SESAM Staff":
    st.subheader("📋 Student Directory")
    
    search = st.text_input("🔍 Search by name or student number", placeholder="e.g., Cruz or S001", key="staff_search")
    filtered_df = filter_dataframe(search, df)
    filtered_df["academic_year"] = filtered_df.apply(lambda row: format_ay(row["ay_start"], row["semester"]), axis=1)
    
    if len(filtered_df) > 0:
        st.dataframe(
            filtered_df[["student_number", "name", "program", "academic_year", "advisor", "gwa", "pos_status", "final_exam_status"]],
            use_container_width=True,
            height=400
        )
    else:
        st.info("No students match the current search.")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1,1,2])
    with col1:
        btn_update = st.button("✏️ Update Student", use_container_width=True, key="staff_btn_update")
    with col2:
        btn_add = st.button("➕ Add New Student", use_container_width=True, key="staff_btn_add")
    
    if "staff_show_update" not in st.session_state:
        st.session_state.staff_show_update = False
    if "staff_show_add" not in st.session_state:
        st.session_state.staff_show_add = False
    
    if btn_update:
        st.session_state.staff_show_update = not st.session_state.staff_show_update
        st.session_state.staff_show_add = False
        st.rerun()
    if btn_add:
        st.session_state.staff_show_add = not st.session_state.staff_show_add
        st.session_state.staff_show_update = False
        st.rerun()
    
    # ==================== UPDATE STUDENT FORM (unchanged from previous, but we keep it) ====================
    if st.session_state.staff_show_update:
        st.subheader("✏️ Update Student Record")
        if len(filtered_df) == 0:
            st.warning("No students available to edit.")
        else:
            selected_student_name = st.selectbox(
                "Select a student to edit",
                options=filtered_df["name"].tolist(),
                key="staff_update_select"
            )
            student = filtered_df[filtered_df["name"] == selected_student_name].iloc[0].copy()
            
            if st.button("❌ Cancel", key="cancel_update"):
                st.session_state.staff_show_update = False
                st.rerun()
            
            st.markdown(f"### Editing: {student['name']} ({student['student_number']})")
            
            completed_steps = get_step_completion_status(student)
            next_step = get_next_required_step(student)
            st.markdown("#### 🚀 Milestone Workflow")
            display_workflow_grid(completed_steps, next_step)
            if next_step != "Complete":
                if is_step_locked(student, next_step):
                    st.warning(f"🔒 **{next_step} is locked** – complete previous steps first.")
                else:
                    st.info(f"🎯 **Next Required Step:** {next_step}")
            else:
                st.success("🎉 All milestones completed! Ready for graduation.")
            
            # We reuse the same 8 tabs as before, but we add a new tab for Milestone Requests review at the end?
            # Instead, we keep the existing 8 tabs and add a new tab "Milestone Requests" at position 8.
            # However, to avoid breaking existing layout, we'll insert a new tab after "Semester History".
            # But we must keep all original tabs. Let's make a list of tabs.
            tab_labels = ["📝 Student Info", "📚 Coursework & Thesis", "📝 Exams", "🏠 Residency", "🎓 Graduation", "👥 Committee", "📁 Documents", "📖 Semester History", "✅ Milestone Requests"]
            tabs = st.tabs(tab_labels)
            
            # Tab 0: Student Info (same as before)
            with tabs[0]:
                col1, col2 = st.columns([1,2])
                with col1:
                    pic_path = get_profile_picture_path(student["student_number"])
                    if pic_path and os.path.exists(pic_path):
                        st.image(pic_path, width=180)
                    else:
                        st.info("No profile picture")
                    uploaded_file = st.file_uploader("Upload new picture", type=["jpg","jpeg","png"], key="staff_pic")
                    if uploaded_file:
                        fn = save_profile_picture(student["student_number"], uploaded_file)
                        if fn:
                            df.loc[df["student_number"]==student["student_number"], "profile_pic"] = fn
                            save_data(df)
                            st.rerun()
                    if st.button("🗑️ Delete picture"):
                        if delete_profile_picture(student["student_number"]):
                            df.loc[df["student_number"]==student["student_number"], "profile_pic"] = ""
                            save_data(df)
                            st.rerun()
                with col2:
                    st.markdown(f"**Student Number:** {student['student_number']}")
                    st.markdown(f"**Full Name:** {student['name']}")
                    st.markdown(f"**Program:** {student['program']}")
                    st.markdown(f"**Advisor:** {student['advisor']}")
                    st.markdown(f"**Academic Year:** {format_ay(student['ay_start'], student['semester'])}")
                    st.markdown(f"**GWA (Official):** {student['gwa']:.2f}")
            
            # Tab 1: Coursework & Thesis (same as before)
            with tabs[1]:
                locked = is_step_locked(student, "Coursework")
                if locked:
                    st.warning("🔒 Coursework step locked until Committee approved.")
                with st.form("staff_coursework"):
                    st.subheader("Plan of Study")
                    pos_status = st.selectbox("POS Status", ["Not Filed","Pending","Approved"], index=safe_index(["Not Filed","Pending","Approved"], student["pos_status"]), disabled=locked)
                    pos_submitted = st.text_input("Submitted Date", student["pos_submitted_date"], disabled=locked)
                    pos_approved = st.text_input("Approved Date", student["pos_approved_date"], disabled=locked)
                    st.subheader("Coursework")
                    gwa_manual = st.number_input("GWA (manual fallback)", min_value=1.0, max_value=5.0, value=float(student["gwa"]), disabled=locked)
                    total_units_taken = st.number_input("Total Units Taken", min_value=0, value=int(student["total_units_taken"]), disabled=locked)
                    total_units_required = st.number_input("Required Units", min_value=0, value=int(student["total_units_required"]), disabled=locked)
                    progress = compute_coursework_progress(student)
                    st.progress(progress/100, text=f"Coursework completion: {progress}% ({student['total_units_taken']} / {student['total_units_required']} units)")
                    st.subheader("Thesis/Dissertation")
                    thesis_units = st.number_input("Thesis Units Taken", min_value=0, value=int(student["thesis_units_taken"]), disabled=locked)
                    st.caption(get_thesis_pattern_description(student["program"]))
                    outline_approved = st.selectbox("Outline Approved", ["Yes","No"], index=safe_index(["Yes","No"], student["thesis_outline_approved"]), disabled=locked)
                    outline_date = st.text_input("Outline Approval Date", student["thesis_outline_approved_date"], disabled=locked)
                    thesis_status = st.selectbox("Thesis Status", ["Not Started","In Progress","Draft with Adviser","For Committee Review","Approved","Submitted"], index=safe_index(["Not Started","In Progress","Draft with Adviser","For Committee Review","Approved","Submitted"], student["thesis_status"]), disabled=locked)
                    if st.form_submit_button("Update"):
                        if not locked:
                            df.loc[df["student_number"]==student["student_number"], ["pos_status","pos_submitted_date","pos_approved_date","gwa","total_units_taken","total_units_required","thesis_units_taken","thesis_outline_approved","thesis_outline_approved_date","thesis_status"]] = [pos_status, pos_submitted, pos_approved, gwa_manual, total_units_taken, total_units_required, thesis_units, outline_approved, outline_date, thesis_status]
                            save_data(df)
                            st.success("Updated")
                            st.rerun()
                        else:
                            st.error("Locked step cannot be edited")
            
            # Tab 2: Exams (same)
            with tabs[2]:
                locked = is_step_locked(student, "Exams")
                if locked:
                    st.warning("🔒 Exams step locked until Coursework completed.")
                with st.form("staff_exams"):
                    st.subheader("Examinations")
                    qual = st.selectbox("Qualifying Exam (PhD)", ["N/A","Not Taken","Passed","Failed","Re-exam Scheduled"], index=safe_index(["N/A","Not Taken","Passed","Failed","Re-exam Scheduled"], student["qualifying_exam_status"]), disabled=locked)
                    qual_date = st.text_input("Qualifying Passed Date", student["qualifying_exam_passed_date"], disabled=locked)
                    written = st.selectbox("Written Comprehensive", ["N/A","Not Taken","Passed","Failed"], index=safe_index(["N/A","Not Taken","Passed","Failed"], student["written_comprehensive_status"]), disabled=locked)
                    written_date = st.text_input("Written Passed Date", student["written_comprehensive_passed_date"], disabled=locked)
                    oral = st.selectbox("Oral Comprehensive", ["N/A","Not Taken","Passed","Failed"], index=safe_index(["N/A","Not Taken","Passed","Failed"], student["oral_comprehensive_status"]), disabled=locked)
                    oral_date = st.text_input("Oral Passed Date", student["oral_comprehensive_passed_date"], disabled=locked)
                    general = st.selectbox("General Exam (MS)", ["N/A","Not Taken","Passed","Failed"], index=safe_index(["N/A","Not Taken","Passed","Failed"], student["general_exam_status"]), disabled=locked)
                    general_date = st.text_input("General Passed Date", student["general_exam_passed_date"], disabled=locked)
                    final = st.selectbox("Final Exam", ["Not Taken","Passed","Failed","Re-exam Scheduled"], index=safe_index(["Not Taken","Passed","Failed","Re-exam Scheduled"], student["final_exam_status"]), disabled=locked)
                    final_date = st.text_input("Final Passed Date", student["final_exam_passed_date"], disabled=locked)
                    if st.form_submit_button("Update Exams"):
                        if not locked:
                            df.loc[df["student_number"]==student["student_number"], ["qualifying_exam_status","qualifying_exam_passed_date","written_comprehensive_status","written_comprehensive_passed_date","oral_comprehensive_status","oral_comprehensive_passed_date","general_exam_status","general_exam_passed_date","final_exam_status","final_exam_passed_date"]] = [qual, qual_date, written, written_date, oral, oral_date, general, general_date, final, final_date]
                            save_data(df)
                            st.success("Updated")
                            st.rerun()
                        else:
                            st.error("Locked step cannot be edited")
            
            # Tab 3: Residency (same)
            with tabs[3]:
                with st.form("staff_residency"):
                    residency_used = st.number_input("Years of Residence Used", min_value=0, value=int(student["residency_years_used"]))
                    max_years = get_residency_max(student["program"])
                    st.info(f"Maximum allowed: {max_years} years")
                    extension_count = st.number_input("Extensions Granted", min_value=0, value=int(student["extension_count"]))
                    extension_end = st.text_input("Extension End Date", student["extension_end_date"])
                    loa_start = st.text_input("LOA Start Date", student["loa_start_date"])
                    loa_end = st.text_input("LOA End Date", student["loa_end_date"])
                    loa_terms = st.number_input("Total LOA Terms", min_value=0, value=int(student["loa_total_terms"]))
                    awol = st.selectbox("AWOL Status", ["No","Yes"], index=safe_index(["No","Yes"], student["awol_status"]))
                    awol_lifted = st.text_input("AWOL Lifted Date", student["awol_lifted_date"])
                    if st.form_submit_button("Update Residency & Leave"):
                        df.loc[df["student_number"]==student["student_number"], ["residency_years_used","extension_count","extension_end_date","loa_start_date","loa_end_date","loa_total_terms","awol_status","awol_lifted_date"]] = [residency_used, extension_count, extension_end, loa_start, loa_end, loa_terms, awol, awol_lifted]
                        save_data(df)
                        st.success("Updated")
                        st.rerun()
            
            # Tab 4: Graduation (same)
            with tabs[4]:
                defense_done = "Defense" in get_step_completion_status(student)
                if not defense_done:
                    st.warning("🔒 Graduation locked until Final Exam passed.")
                with st.form("staff_graduation"):
                    grad_applied = st.selectbox("Graduation Applied", ["No","Yes"], index=safe_index(["No","Yes"], student["graduation_applied"]), disabled=not defense_done)
                    grad_approved = st.selectbox("Graduation Approved", ["No","Yes"], index=safe_index(["No","Yes"], student["graduation_approved"]), disabled=not defense_done)
                    grad_date = st.text_input("Graduation Date", student["graduation_date"], disabled=not defense_done)
                    transfer_units = st.number_input("Transfer Credits Approved (max 9)", min_value=0, max_value=9, value=int(student["transfer_units_approved"]))
                    if st.form_submit_button("Update Graduation"):
                        if defense_done or (grad_applied=="No" and grad_approved=="No"):
                            df.loc[df["student_number"]==student["student_number"], ["graduation_applied","graduation_approved","graduation_date","transfer_units_approved"]] = [grad_applied, grad_approved, grad_date, transfer_units]
                            save_data(df)
                            st.success("Updated")
                            st.rerun()
                        else:
                            st.error("Cannot approve graduation before Final Exam")
            
            # Tab 5: Committee (structured members, same as previous)
            with tabs[5]:
                committee_title = get_committee_title(student["program"])
                st.subheader(f"👥 {committee_title}")
                existing_members = parse_committee_members(student.get("committee_members_structured", ""))
                if f"committee_members_{student['student_number']}" not in st.session_state:
                    st.session_state[f"committee_members_{student['student_number']}"] = existing_members
                members = st.session_state[f"committee_members_{student['student_number']}"]
                st.write("**Current Committee Members:**")
                for idx, member in enumerate(members):
                    col1, col2, col3 = st.columns([3, 3, 1])
                    with col1:
                        name = st.text_input(f"Name", value=member["name"], key=f"name_{student['student_number']}_{idx}")
                    with col2:
                        role_options = ["Chair (Major Professor)", "Chair (Adviser)", "Member", "Co-Chair", "Secretary", "External Member"]
                        if committee_title == "Guidance Committee":
                            default_role = "Chair (Major Professor)" if idx == 0 else "Member"
                        else:
                            default_role = "Chair (Adviser)" if idx == 0 else "Member"
                        role = st.selectbox(f"Role", options=role_options, index=role_options.index(member["role"]) if member["role"] in role_options else role_options.index(default_role), key=f"role_{student['student_number']}_{idx}")
                    with col3:
                        if st.button("❌", key=f"remove_{student['student_number']}_{idx}"):
                            members.pop(idx)
                            st.rerun()
                    members[idx] = {"name": name, "role": role}
                if st.button("➕ Add Member", key=f"add_member_{student['student_number']}"):
                    members.append({"name": "", "role": "Member"})
                    st.rerun()
                committee_approval_date = st.text_input("Committee Approval Date (YYYY-MM-DD)", student.get("committee_approval_date", ""))
                if st.button("💾 Save Committee", key=f"save_committee_{student['student_number']}"):
                    valid_members = [m for m in members if m["name"].strip()]
                    if not valid_members:
                        st.error("At least one committee member is required.")
                    else:
                        structured_str = format_committee_members(valid_members)
                        df.loc[df["student_number"] == student["student_number"], "committee_members_structured"] = structured_str
                        df.loc[df["student_number"] == student["student_number"], "committee_approval_date"] = committee_approval_date
                        save_data(df)
                        st.success("Committee saved successfully!")
                        st.rerun()
                st.markdown("---")
                st.write("**Preview (as will appear in student profile):**")
                if members:
                    for m in members:
                        if m["name"].strip():
                            st.write(f"• {m['name']} – {m['role']}")
                else:
                    st.caption("No members added yet.")
            
            # Tab 6: Documents (same)
            with tabs[6]:
                st.subheader("📎 Document Submissions")
                uploads = get_all_uploads_for_student(student["student_number"])
                if len(uploads)==0:
                    st.info("No documents uploaded.")
                else:
                    for _, doc in uploads.iterrows():
                        with st.expander(f"{UPLOAD_DISPLAY_NAMES[doc['category']]} – {doc['original_filename']} (Status: {doc['status']})"):
                            st.write(f"Uploaded: {doc['upload_date']}")
                            if doc['status']=="Pending":
                                comment = st.text_area("Reviewer Comment", key=f"comm_{doc['category']}_{doc['upload_date']}")
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    if st.button("✅ Approve", key=f"app_{doc['category']}_{doc['upload_date']}"):
                                        uploads.loc[doc.name, "status"] = "Approved"
                                        uploads.loc[doc.name, "reviewer_comment"] = comment
                                        uploads.loc[doc.name, "reviewed_by"] = st.session_state.display_name
                                        uploads.loc[doc.name, "review_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        save_uploads(uploads)
                                        st.rerun()
                                with col_b:
                                    if st.button("❌ Reject", key=f"rej_{doc['category']}_{doc['upload_date']}"):
                                        uploads.loc[doc.name, "status"] = "Rejected"
                                        uploads.loc[doc.name, "reviewer_comment"] = comment
                                        uploads.loc[doc.name, "reviewed_by"] = st.session_state.display_name
                                        uploads.loc[doc.name, "review_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        save_uploads(uploads)
                                        st.rerun()
                            else:
                                st.write(f"Reviewer: {doc['reviewed_by']} on {doc['review_date']}")
                                st.write(f"Comment: {doc['reviewer_comment']}")
            
            # Tab 7: Semester History (same)
            with tabs[7]:
                st.subheader("📚 Academic Semester Records")
                semesters = get_student_semesters(student["student_number"])
                if len(semesters)==0:
                    st.info("No semester records. Add below.")
                else:
                    for _, sem in semesters.iterrows():
                        with st.expander(f"📅 {sem['academic_year']} | {sem['semester']} | GWA: {sem['gwa']:.2f}"):
                            subjects = json.loads(sem["subjects_json"])
                            if subjects:
                                st.table(pd.DataFrame(subjects))
                            st.caption(f"Total Units: {sem['total_units']}")
                            if sem['amis_file_path']:
                                st.write(f"📎 AMIS: {os.path.basename(sem['amis_file_path'])}")
                st.subheader("➕ Add New Semester")
                with st.form("add_semester_staff"):
                    col_ay, col_sem = st.columns(2)
                    with col_ay:
                        academic_year = st.selectbox("Academic Year", ACADEMIC_YEARS)
                    with col_sem:
                        semester = st.selectbox("Semester", SEMESTERS)
                    num_subjects = st.number_input("Number of Subjects", min_value=1, max_value=10, value=1)
                    subjects = []
                    for i in range(num_subjects):
                        cols = st.columns(3)
                        with cols[0]:
                            name = st.text_input(f"Subject {i+1} Name", key=f"subj_name_{i}")
                        with cols[1]:
                            units = st.number_input(f"Units", min_value=0.0, step=0.5, key=f"subj_units_{i}")
                        with cols[2]:
                            grade = st.number_input(f"Grade (1.0-5.0)", min_value=1.0, max_value=5.0, step=0.01, key=f"subj_grade_{i}")
                        if name and units>0:
                            subjects.append({"name": name, "units": units, "grade": grade})
                    amis_file = st.file_uploader("AMIS Screenshot (optional)", type=["png","jpg","jpeg","pdf"])
                    if st.form_submit_button("Save Semester"):
                        if subjects:
                            amis_path = save_uploaded_file(student["student_number"], "amis_screenshot", amis_file) if amis_file else ""
                            add_semester_record(student["student_number"], academic_year, semester, subjects, amis_path)
                            st.success("Semester added and GWA recalculated")
                            st.rerun()
                        else:
                            st.error("Add at least one subject")
            
            # Tab 8: Milestone Requests (new) - Staff can review pending submissions for this student
            with tabs[8]:
                st.subheader("📌 Pending Milestone Validations")
                requests_df = load_milestone_requests()
                student_requests = requests_df[requests_df["student_number"] == student["student_number"]].copy()
                pending = student_requests[student_requests["status"] == "Pending"]
                if len(pending) == 0:
                    st.info("No pending milestone requests for this student.")
                else:
                    for idx, req in pending.iterrows():
                        with st.expander(f"{req['milestone_label']} - Submitted on {req['submitted_date']}"):
                            st.write(f"**Student:** {req['student_name']}")
                            st.write(f"**Submitted:** {req['submitted_date']}")
                            st.write(f"**File:** {os.path.basename(req['file_path'])}")
                            # Show file preview if image
                            file_path = req['file_path']
                            if os.path.exists(file_path):
                                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                                    st.image(file_path, width=300)
                                else:
                                    st.write(f"📎 [Download]({file_path})")
                            else:
                                st.warning("File not found.")
                            comment = st.text_area("Reviewer Remarks", key=f"review_comment_{req['request_id']}")
                            col_a, col_b = st.columns(2)
                            with col_a:
                                if st.button("✅ Approve", key=f"approve_{req['request_id']}"):
                                    # Update the student's official record
                                    target_field = req['target_field']
                                    target_value = req['target_value']
                                    df.loc[df["student_number"] == student["student_number"], target_field] = target_value
                                    # If it's a date field, also set date
                                    if target_field == "pos_status":
                                        df.loc[df["student_number"] == student["student_number"], "pos_approved_date"] = datetime.now().strftime("%Y-%m-%d")
                                    elif target_field == "thesis_outline_approved":
                                        df.loc[df["student_number"] == student["student_number"], "thesis_outline_approved_date"] = datetime.now().strftime("%Y-%m-%d")
                                    elif target_field == "graduation_applied":
                                        df.loc[df["student_number"] == student["student_number"], "graduation_date"] = datetime.now().strftime("%Y-%m-%d")
                                    # Update request status
                                    requests_df.loc[req.name, "status"] = "Approved"
                                    requests_df.loc[req.name, "reviewer_comment"] = comment
                                    requests_df.loc[req.name, "reviewed_by"] = st.session_state.display_name
                                    requests_df.loc[req.name, "review_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    save_milestone_requests(requests_df)
                                    save_data(df)
                                    st.success("Milestone approved and student record updated!")
                                    st.rerun()
                            with col_b:
                                if st.button("❌ Reject", key=f"reject_{req['request_id']}"):
                                    requests_df.loc[req.name, "status"] = "Rejected"
                                    requests_df.loc[req.name, "reviewer_comment"] = comment
                                    requests_df.loc[req.name, "reviewed_by"] = st.session_state.display_name
                                    requests_df.loc[req.name, "review_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    save_milestone_requests(requests_df)
                                    st.warning("Milestone rejected. Student can resubmit.")
                                    st.rerun()
    
    # ==================== ADD NEW STUDENT FORM (unchanged) ====================
    if st.session_state.staff_show_add:
        st.subheader("➕ Register New Student")
        if st.button("❌ Cancel", key="cancel_add"):
            st.session_state.staff_show_add = False
            st.rerun()
        
        with st.form(key="add_student_form_staff"):
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
            
            col8, col9 = st.columns(2)
            with col8:
                advisor = st.text_input("Advisor (optional)", placeholder="Dr. Faustino-Eslava")
            with col9:
                st.empty()
            
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
                        "pos_status": "Not Filed",
                        "gwa": 2.0,
                        "thesis_units_taken": 0,
                        "thesis_units_limit": get_thesis_limit(program),
                        "residency_max_years": get_residency_max(program),
                        "committee_members_structured": "",
                        "committee_approval_date": "",
                        "profile_pic": "",
                        "pos_submitted_date": "",
                        "pos_approved_date": "",
                        "total_units_taken": 0,
                        "total_units_required": 24,
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
                    st.session_state.staff_show_add = False
                    st.rerun()

# ==================== ADVISER VIEW (with milestone validation too) ====================
elif role == "Faculty Adviser":
    st.subheader(f"👨‍🏫 Your Advisees – {st.session_state.display_name}")
    advisees = df[df["advisor"] == st.session_state.display_name].copy()
    if len(advisees)==0:
        st.warning("No students assigned.")
    else:
        notifications = get_adviser_notifications(st.session_state.display_name)
        if notifications:
            st.markdown("#### 🔔 Notifications")
            for n in notifications:
                if n["severity"]=="error":
                    st.error(f"**{n['student']}** ({n['student_number']}): {n['message']}")
                else:
                    st.warning(f"**{n['student']}** ({n['student_number']}): {n['message']}")
            st.markdown("---")
        # Also show pending milestone requests for advisees
        requests_df = load_milestone_requests()
        pending_requests = requests_df[requests_df["status"] == "Pending"]
        if len(pending_requests) > 0:
            st.markdown("#### ⏳ Pending Milestone Submissions")
            for _, req in pending_requests.iterrows():
                if req["student_number"] in advisees["student_number"].values:
                    with st.expander(f"{req['student_name']} - {req['milestone_label']} ({req['submitted_date']})"):
                        st.write(f"**Submitted:** {req['submitted_date']}")
                        file_path = req['file_path']
                        if os.path.exists(file_path):
                            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                                st.image(file_path, width=300)
                            else:
                                st.write(f"📎 [Download]({file_path})")
                        else:
                            st.warning("File not found.")
                        comment = st.text_area("Remarks", key=f"adv_comment_{req['request_id']}")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(f"✅ Approve", key=f"adv_approve_{req['request_id']}"):
                                # Update student record
                                target_field = req['target_field']
                                target_value = req['target_value']
                                df.loc[df["student_number"] == req["student_number"], target_field] = target_value
                                if target_field == "pos_status":
                                    df.loc[df["student_number"] == req["student_number"], "pos_approved_date"] = datetime.now().strftime("%Y-%m-%d")
                                elif target_field == "thesis_outline_approved":
                                    df.loc[df["student_number"] == req["student_number"], "thesis_outline_approved_date"] = datetime.now().strftime("%Y-%m-%d")
                                elif target_field == "graduation_applied":
                                    df.loc[df["student_number"] == req["student_number"], "graduation_date"] = datetime.now().strftime("%Y-%m-%d")
                                # Update request
                                requests_df.loc[req.name, "status"] = "Approved"
                                requests_df.loc[req.name, "reviewer_comment"] = comment
                                requests_df.loc[req.name, "reviewed_by"] = st.session_state.display_name
                                requests_df.loc[req.name, "review_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                save_milestone_requests(requests_df)
                                save_data(df)
                                st.success("Approved and updated!")
                                st.rerun()
                        with col_b:
                            if st.button(f"❌ Reject", key=f"adv_reject_{req['request_id']}"):
                                requests_df.loc[req.name, "status"] = "Rejected"
                                requests_df.loc[req.name, "reviewer_comment"] = comment
                                requests_df.loc[req.name, "reviewed_by"] = st.session_state.display_name
                                requests_df.loc[req.name, "review_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                save_milestone_requests(requests_df)
                                st.warning("Rejected.")
                                st.rerun()
            st.markdown("---")
        
        search_adv = st.text_input("🔍 Filter advisees")
        filtered = filter_dataframe(search_adv, advisees)
        filtered["academic_year"] = filtered.apply(lambda row: format_ay(row["ay_start"], row["semester"]), axis=1)
        st.dataframe(filtered[["student_number","name","program","academic_year","gwa","thesis_units_taken","pos_status","final_exam_status"]], use_container_width=True)
        for _, row in filtered.iterrows():
            with st.expander(f"📌 {row['name']} ({row['student_number']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Program", row["program"])
                    st.metric("GWA", f"{row['gwa']:.2f}")
                    st.metric("Thesis Units", f"{row['thesis_units_taken']}/{get_thesis_limit(row['program'])}")
                with col2:
                    st.metric("Residency", f"{row['residency_years_used']}/{get_residency_max(row['program'])}")
                    st.metric("POS Status", row["pos_status"])
                    st.metric("Final Exam", row["final_exam_status"])
                display_workflow_grid(get_step_completion_status(row), get_next_required_step(row))
                pic = get_profile_picture_path(row["student_number"])
                if pic:
                    st.image(pic, width=100)
                for alert in check_deadline_alerts(row):
                    st.error(alert)
                for w in get_all_warnings(row):
                    if "⚠️" in w:
                        st.warning(w)
                    else:
                        st.success(w)
        st.info("For updates, contact SESAM Staff.")

# ==================== STUDENT VIEW (with new submission tab) ====================
elif role == "Student":
    st.subheader(f"📘 Your Dashboard – {st.session_state.display_name}")
    student = df[df["name"] == st.session_state.display_name].iloc[0]
    
    completed = get_step_completion_status(student)
    next_step = get_next_required_step(student)
    st.markdown("#### 🚀 Your Milestone Journey")
    display_workflow_grid(completed, next_step)
    
    for alert in check_deadline_alerts(student):
        st.error(alert)
    for w in get_all_warnings(student):
        if "⚠️" in w:
            st.warning(w)
        else:
            st.success(w)
    
    colp1, colp2 = st.columns([1,3])
    with colp1:
        pic = get_profile_picture_path(student["student_number"])
        if pic:
            st.image(pic, width=150)
        else:
            st.info("No profile picture")
    with colp2:
        metrics = st.columns(4)
        metrics[0].metric("Student Number", student["student_number"])
        metrics[1].metric("Program", student["program"])
        metrics[2].metric("GWA (Official)", f"{student['gwa']:.2f}")
        metrics[3].metric("Advisor", student["advisor"])
        metrics2 = st.columns(4)
        metrics2[0].metric("Thesis Units", f"{student['thesis_units_taken']}/{get_thesis_limit(student['program'])}")
        metrics2[1].metric("Residency", f"{student['residency_years_used']}/{get_residency_max(student['program'])}")
        metrics2[2].metric("POS Status", student["pos_status"])
        metrics2[3].metric("Final Exam", student["final_exam_status"])
    
    prog = compute_coursework_progress(student)
    st.progress(prog/100, text=f"Coursework completion: {prog}% ({student['total_units_taken']}/{student['total_units_required']} units)")
    
    # ==================== MILESTONE SUBMISSION SECTION ====================
    st.markdown("#### 📌 Submit Milestone Update")
    with st.expander("Request a milestone update (with supporting document)", expanded=False):
        # Filter milestone types that are not already achieved or not locked?
        # We'll show all, but student can't submit if already approved (we'll check later)
        milestone_options = [m["label"] for m in MILESTONE_TYPES]
        selected_milestone_label = st.selectbox("Select Milestone", milestone_options)
        selected_milestone = next(m for m in MILESTONE_TYPES if m["label"] == selected_milestone_label)
        # Check current status
        current_value = student[selected_milestone["field"]]
        if current_value == selected_milestone["value"]:
            st.success(f"✅ This milestone is already marked as {current_value}. No need to submit.")
        else:
            uploaded_file = st.file_uploader("Upload Proof (screenshot, PDF, etc.)", type=["png","jpg","jpeg","pdf"])
            if uploaded_file and st.button("Submit for Validation"):
                # Save file
                file_path = save_milestone_file(student["student_number"], selected_milestone_label, uploaded_file)
                if file_path:
                    # Create request
                    requests_df = load_milestone_requests()
                    new_id = len(requests_df) + 1
                    new_request = pd.DataFrame([{
                        "request_id": new_id,
                        "student_number": student["student_number"],
                        "student_name": student["name"],
                        "milestone_label": selected_milestone_label,
                        "target_field": selected_milestone["field"],
                        "target_value": selected_milestone["value"],
                        "submitted_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "file_path": file_path,
                        "original_filename": uploaded_file.name,
                        "status": "Pending",
                        "reviewer_comment": "",
                        "reviewed_by": "",
                        "review_date": ""
                    }])
                    requests_df = pd.concat([requests_df, new_request], ignore_index=True)
                    save_milestone_requests(requests_df)
                    st.success("Milestone update submitted! Staff/Adviser will validate.")
                    st.rerun()
    
    # Show submission history
    st.markdown("#### 📋 Your Milestone Submission History")
    requests_df = load_milestone_requests()
    my_requests = requests_df[requests_df["student_number"] == student["student_number"]].copy()
    if len(my_requests) == 0:
        st.info("No milestone submissions yet.")
    else:
        for _, req in my_requests.iterrows():
            status_color = "🟡" if req["status"] == "Pending" else ("✅" if req["status"] == "Approved" else "❌")
            with st.expander(f"{status_color} {req['milestone_label']} - {req['status']} (Submitted: {req['submitted_date']})"):
                st.write(f"**Status:** {req['status']}")
                if req["status"] == "Pending":
                    st.info("Your request is pending review.")
                elif req["status"] == "Approved":
                    st.success(f"Approved on {req['review_date']} by {req['reviewed_by']}.")
                    if req["reviewer_comment"]:
                        st.write(f"**Remarks:** {req['reviewer_comment']}")
                else:
                    st.error(f"Rejected on {req['review_date']} by {req['reviewed_by']}.")
                    if req["reviewer_comment"]:
                        st.write(f"**Reason:** {req['reviewer_comment']}")
                    st.write("You may resubmit using the form above.")
                st.write(f"**Proof:** {os.path.basename(req['file_path'])}")
                if os.path.exists(req['file_path']) and req['file_path'].lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    st.image(req['file_path'], width=200)
    
    # Existing document uploads (general)
    st.markdown("#### 📎 Submit General Documents")
    with st.expander("Upload other documents (admission letter, AMIS, etc.)"):
        category = st.selectbox("Document Type", UPLOAD_CATEGORIES, format_func=lambda x: UPLOAD_DISPLAY_NAMES[x])
        file = st.file_uploader("Choose file", type=["pdf","png","jpg","jpeg","doc","docx"], key="gen_doc")
        if file and st.button("Upload Document"):
            path = save_uploaded_file(student["student_number"], category, file)
            if path:
                uploads = load_uploads()
                new = pd.DataFrame([{"student_number": student["student_number"], "category": category, "file_path": path, "original_filename": file.name, "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "Pending", "reviewer_comment": "", "reviewed_by": "", "review_date": ""}])
                uploads = pd.concat([uploads, new], ignore_index=True)
                save_uploads(uploads)
                st.success("Uploaded successfully. Staff will review.")
                st.rerun()
    
    st.markdown("#### 📋 Document Status")
    uploads_student = get_all_uploads_for_student(student["student_number"])
    if len(uploads_student)>0:
        status_df = uploads_student[["category","original_filename","upload_date","status"]].copy()
        status_df["category"] = status_df["category"].map(UPLOAD_DISPLAY_NAMES)
        st.dataframe(status_df, use_container_width=True)
    else:
        st.info("No documents submitted.")
    
    st.markdown("#### 📚 Academic History")
    semesters = get_student_semesters(student["student_number"])
    if len(semesters)==0:
        st.info("No semester records yet. Your adviser will add them.")
    else:
        for _, sem in semesters.iterrows():
            with st.expander(f"📅 {sem['academic_year']} – {sem['semester']} (GWA: {sem['gwa']:.2f})"):
                subjects = json.loads(sem["subjects_json"])
                if subjects:
                    st.table(pd.DataFrame(subjects))
                st.caption(f"Total units: {sem['total_units']}")
    
    # Committee display
    committee_title = get_committee_title(student["program"])
    members = parse_committee_members(student.get("committee_members_structured", ""))
    if members:
        with st.expander(f"👥 {committee_title}"):
            for m in members:
                st.write(f"• {m['name']} – {m['role']}")
            if student.get("committee_approval_date"):
                st.caption(f"Approved on: {student['committee_approval_date']}")
    else:
        with st.expander(f"👥 {committee_title}"):
            st.info("No committee members assigned yet.")
    
    st.caption("For corrections, contact your adviser or SESAM Staff.")

# ==================== FOOTER ====================
st.markdown("---")
st.caption("SESAM Graduate Student Lifecycle Management v3.0 | Workflow + Document Management + Milestone Validation")
