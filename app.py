"""
SESAM KMIS - Graduate Student Lifecycle Management System (Enhanced)
Author: [Your Name]
Date: [Current Date]
Description: Full academic record system with per-semester blocks, editable subjects, and document validation.
"""

import streamlit as st
import pandas as pd
import os
import json
from datetime import date, datetime

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="SESAM Graduate Lifecycle Manager",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== COMPACT CSS ====================
st.markdown("""
<style>
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    .element-container { margin-bottom: 0.25rem !important; }
    .stMarkdown { margin-bottom: 0.25rem !important; }
    .stButton button { padding: 0.2rem 0.8rem !important; font-size: 0.8rem !important; min-height: 32px !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 0.5rem !important; background: transparent !important; padding: 0 !important; }
    .stTabs [data-baseweb="tab"] { padding: 0.25rem 0.8rem !important; font-size: 0.8rem !important; }
    .streamlit-expanderHeader { font-size: 0.9rem !important; padding: 0.3rem !important; }
    .row-widget.stSelectbox, .row-widget.stTextInput, .row-widget.stNumberInput { margin-bottom: 0.2rem !important; }
    .stHorizontalBlock { gap: 0.5rem !important; }
    hr { margin: 0.5rem 0 !important; }
    section[data-testid="stSidebar"] .css-1d391kg { padding-top: 1rem; }
    .status-pending { background-color: #fff3cd; color: #856404; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.7rem; display: inline-block; }
    .status-approved { background-color: #d4edda; color: #155724; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.7rem; display: inline-block; }
    .status-rejected { background-color: #f8d7da; color: #721c24; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.7rem; display: inline-block; }
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
if "consent_given" not in st.session_state:
    st.session_state.consent_given = False

# ==================== DATA PRIVACY CONSENT ====================
CONSENT_LOG_FILE = "consent_log.csv"

def log_consent(username, role, display_name):
    if not os.path.exists(CONSENT_LOG_FILE):
        df = pd.DataFrame(columns=["timestamp", "username", "role", "display_name", "ip_address"])
    else:
        df = pd.read_csv(CONSENT_LOG_FILE)
    new_entry = pd.DataFrame([{
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "username": username,
        "role": role,
        "display_name": display_name,
        "ip_address": "unknown"
    }])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(CONSENT_LOG_FILE, index=False)

def show_consent_form():
    st.markdown("""
    <div style="background:white; border-radius:24px; padding:2rem; max-width:800px; margin:2rem auto; box-shadow:0 20px 35px rgba(0,0,0,0.1); border:1px solid #e2e8f0;">
        <div style="text-align:center; margin-bottom:1.5rem;">
            <h2>📜 Data Privacy Consent</h2>
            <p>Please read and accept our Data Privacy Policy</p>
        </div>
        <div style="background:#f8fafc; padding:1.5rem; border-radius:16px; margin:1rem 0; max-height:300px; overflow-y:auto; font-size:0.9rem; line-height:1.5; color:#334155;">
            <strong>Data Privacy Notice</strong><br><br>
            In compliance with the Data Privacy Act of 2012 (Republic Act No. 10173), SESAM KMIS collects and processes the following personal and academic information:
            <ul>
                <li>Full name, student number, program, adviser</li>
                <li>Academic records (GWA, units taken, exam results, thesis progress)</li>
                <li>Uploaded documents (profile pictures, proof of milestones, AMIS screenshots)</li>
                <li>Committee membership details</li>
            </ul>
            <strong>Purpose of Collection</strong><br>
            Your data is used solely for academic monitoring, degree progress tracking, and reporting as required by the Graduate School. We do not share your data with third parties without your explicit consent, except as required by law.<br><br>
            <strong>Your Rights</strong><br>
            You have the right to access, correct, and request deletion of your personal data. You may withdraw consent at any time by contacting the SESAM Data Protection Officer.<br><br>
            <strong>Consent</strong><br>
            By clicking "I Consent", you acknowledge that you have read and understood this notice and agree to the processing of your personal data as described.
        </div>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        agree = st.checkbox("I have read and agree to the Data Privacy Policy")
        if st.button("✅ I Consent", use_container_width=True, disabled=not agree):
            st.session_state.consent_given = True
            log_consent(st.session_state.username, st.session_state.role, st.session_state.display_name)
            st.rerun()

# ==================== USER AUTH ====================
USERS = {
    "staff1": {"password": "admin123", "role": "SESAM Staff", "display_name": "SESAM Administrator"},
    "adviser1": {"password": "adv123", "role": "Faculty Adviser", "display_name": "Dr. Eslava"},
    "adviser2": {"password": "adv456", "role": "Faculty Adviser", "display_name": "Dr. Sanchez"},
    # Demo students (password = student number)
    "S001": {"password": "S001", "role": "Student", "display_name": "Santos, Maria Concepcion R."},
    "S002": {"password": "S002", "role": "Student", "display_name": "Dela Cruz, Jose Mari P."},
    "S003": {"password": "S003", "role": "Student", "display_name": "Fernandez, Kristoffer Ivan M."},
    "S004": {"password": "S004", "role": "Student", "display_name": "Lopez, Maria Isabella T."},
    "S005": {"password": "S005", "role": "Student", "display_name": "Villanueva, Gabriel Angelo S."},
    "S006": {"password": "S006", "role": "Student", "display_name": "Reyes, Patricia Anne G."},
    "S007": {"password": "S007", "role": "Student", "display_name": "Gomez, Emmanuel D."},
    "S008": {"password": "S008", "role": "Student", "display_name": "Mendoza, Catherine Joy L."},
    "S009": {"password": "S009", "role": "Student", "display_name": "Santiago, Rommel C."},
    "S010": {"password": "S010", "role": "Student", "display_name": "Ramirez, Maria Lourdes E."},
    "S011": {"password": "S011", "role": "Student", "display_name": "Torres, Victor Emmanuel A."},
    "S012": {"password": "S012", "role": "Student", "display_name": "Bautista, Anna Patricia F."},
    "S013": {"password": "S013", "role": "Student", "display_name": "Aquino, Francis Joseph T."}
}

# ==================== PROGRAM CLASSIFICATION ====================
PROGRAMS = [
    "MS Environmental Science",
    "PhD Environmental Science",
    "PhD Environmental Diplomacy and Negotiations",
    "Master in Resilience Studies (M-ReS)",
    "Professional Masters in Tropical Marine Ecosystems Management (PM-TMEM)",
    "PhD by Research Environmental Science"
]

def get_program_type(program_name):
    if program_name.startswith("MS") or program_name.startswith("Master"):
        return "MS_Thesis" if "Resilience" not in program_name or "Environmental Science" in program_name else "MS_NonThesis"
    elif program_name.startswith("PhD by Research"):
        return "PhD_Research"
    elif program_name.startswith("PhD"):
        return "PhD_Regular"
    else:
        return "MS_Thesis"

# ==================== MILESTONE DEFINITIONS ====================
MILESTONE_DEFS = {
    "MS_Thesis": [
        "Admission", "Registration", "Guidance Committee Formation", "Plan of Study (POS)",
        "Coursework Completion", "General Examination", "Thesis Work", "External Review",
        "Publishable Article", "Final Examination", "Final Submission", "Graduation Clearance"
    ],
    "MS_NonThesis": [
        "Admission", "Registration", "Guidance Committee Formation", "Plan of Study (POS)",
        "Coursework Completion", "General Examination", "External Review", "Graduation Clearance"
    ],
    "PhD_Regular": [
        "Admission", "Registration", "Advisory Committee Formation", "Qualifying Exam",
        "Plan of Study", "Coursework", "Comprehensive Exam", "Dissertation", "External Review",
        "Publication", "Final Defense", "Submission", "Graduation"
    ],
    "PhD_Straight": [
        "Admission", "Registration", "Advisory Committee Formation", "Plan of Study",
        "Coursework", "Comprehensive Exam", "Dissertation", "External Review",
        "Publication (2 papers)", "Final Defense", "Submission", "Graduation"
    ],
    "PhD_Research": [
        "Admission", "Registration", "Supervisory Committee Formation", "Plan of Research",
        "Seminar Series (4 seminars)", "Research Progress Review", "Thesis Draft",
        "Publication (min 2 papers)", "Final Oral Examination", "Thesis Submission", "Graduation"
    ]
}

# ==================== MILESTONE TRACKING ====================
MILESTONE_FILE = "milestone_tracking.csv"

def load_milestone_tracking():
    if os.path.exists(MILESTONE_FILE):
        df = pd.read_csv(MILESTONE_FILE)
        required = ["student_number", "milestone", "status", "date", "file_path", "remarks"]
        for col in required:
            if col not in df.columns:
                df[col] = ""
        return df
    else:
        return pd.DataFrame(columns=["student_number", "milestone", "status", "date", "file_path", "remarks"])

def save_milestone_tracking(df):
    df.to_csv(MILESTONE_FILE, index=False)

def get_student_milestones(student_number, program_type):
    df = load_milestone_tracking()
    student_df = df[df["student_number"] == student_number]
    milestone_names = MILESTONE_DEFS.get(program_type, MILESTONE_DEFS["MS_Thesis"])
    if len(student_df) == 0:
        new_rows = []
        for m in milestone_names:
            new_rows.append({
                "student_number": student_number,
                "milestone": m,
                "status": "Not Started",
                "date": "",
                "file_path": "",
                "remarks": ""
            })
        new_df = pd.DataFrame(new_rows)
        df = pd.concat([df, new_df], ignore_index=True)
        save_milestone_tracking(df)
        return new_df
    else:
        existing = set(student_df["milestone"])
        new_rows = []
        for m in milestone_names:
            if m not in existing:
                new_rows.append({
                    "student_number": student_number,
                    "milestone": m,
                    "status": "Not Started",
                    "date": "",
                    "file_path": "",
                    "remarks": ""
                })
        if new_rows:
            df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
            save_milestone_tracking(df)
        return df[df["student_number"] == student_number]

def update_milestone(student_number, milestone, status, date_str, file_path, remarks):
    df = load_milestone_tracking()
    mask = (df["student_number"] == student_number) & (df["milestone"] == milestone)
    if mask.any():
        df.loc[mask, "status"] = status
        if date_str:
            df.loc[mask, "date"] = date_str
        if file_path:
            df.loc[mask, "file_path"] = file_path
        if remarks:
            df.loc[mask, "remarks"] = remarks
    else:
        new_row = pd.DataFrame([{
            "student_number": student_number,
            "milestone": milestone,
            "status": status,
            "date": date_str,
            "file_path": file_path,
            "remarks": remarks
        }])
        df = pd.concat([df, new_row], ignore_index=True)
    save_milestone_tracking(df)

def save_milestone_file(student_number, milestone_name, uploaded_file):
    if uploaded_file is None:
        return None
    milestone_folder = os.path.join("student_files", student_number, "milestones")
    if not os.path.exists(milestone_folder):
        os.makedirs(milestone_folder)
    ext = uploaded_file.name.split('.')[-1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = milestone_name.replace(" ", "_").replace("/", "_")
    filename = f"{safe_name}_{timestamp}.{ext}"
    filepath = os.path.join(milestone_folder, filename)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filepath

# ==================== HELPER FUNCTIONS ====================
SEMESTERS = ["1st Sem", "2nd Sem", "Summer"]
current_year = date.today().year
ACADEMIC_YEARS = [f"{year}-{year+1}" for year in range(current_year-5, current_year+6)]

def is_master_program(program):
    return get_program_type(program).startswith("MS")

def is_phd_program(program):
    return get_program_type(program).startswith("PhD")

def is_phd_by_research(program):
    return get_program_type(program) == "PhD_Research"

def get_thesis_limit_from_program(program):
    ptype = get_program_type(program)
    if ptype in ["PhD_Regular", "PhD_Straight", "PhD_Research"]:
        return 12
    elif ptype == "MS_Thesis":
        return 6
    else:
        return 0

def get_residency_max_from_program(program):
    return 5 if is_master_program(program) else 7

def format_ay(ay_start, semester):
    return f"A.Y. {ay_start}-{ay_start+1} ({semester})"

def get_thesis_pattern_description(program):
    if is_master_program(program):
        return "💡 MS: 6 thesis units (2-2-2 or 3-3) if thesis track."
    else:
        return "💡 PhD: 12 dissertation units (3-3-3-3 or 4-4-4)."

# ==================== WORKFLOW ENGINE ====================
WORKFLOW_STEPS = ["Committee", "Coursework", "Exams", "POS", "Thesis", "Defense", "Graduation"]

def get_step_completion_status(student_row):
    program = student_row["program"]
    ptype = get_program_type(program)
    completed = set()
    if pd.notna(student_row.get("committee_approval_date")) and str(student_row.get("committee_approval_date")).strip():
        completed.add("Committee")
    if student_row.get("total_units_taken", 0) >= student_row.get("total_units_required", 24):
        completed.add("Coursework")
    if ptype in ["MS_Thesis", "MS_NonThesis"]:
        if student_row.get("general_exam_status") == "Passed":
            completed.add("Exams")
    else:
        if (student_row.get("qualifying_exam_status") == "Passed" and
            student_row.get("written_comprehensive_status") == "Passed" and
            student_row.get("oral_comprehensive_status") == "Passed"):
            completed.add("Exams")
    if student_row.get("pos_status") == "Approved":
        completed.add("POS")
    if ptype != "MS_NonThesis":
        if (student_row.get("thesis_outline_approved") == "Yes" and
            student_row.get("thesis_status") not in ["Not Started", ""]):
            completed.add("Thesis")
    else:
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
        for col in ["doc_path", "doc_upload_time", "doc_status", "doc_remarks", "doc_validated_by", "doc_validated_time"]:
            if col not in df.columns:
                df[col] = ""
        return df
    else:
        return pd.DataFrame(columns=["student_number", "academic_year", "semester", "subjects_json", "total_units", "gwa", "amis_file_path",
                                     "doc_path", "doc_upload_time", "doc_status", "doc_remarks", "doc_validated_by", "doc_validated_time"])

def save_semester_records(df):
    df.to_csv(SEMESTER_FILE, index=False)

def compute_gwa_from_subjects(subjects_list):
    total_units = 0
    total_grade_points = 0
    for subj in subjects_list:
        try:
            grade = float(subj["grade"])
            units = float(subj["units"])
            total_units += units
            total_grade_points += units * grade
        except (ValueError, TypeError):
            continue
    return total_grade_points / total_units if total_units > 0 else 0.0

def get_student_semesters(student_number):
    df = load_semester_records()
    return df[df["student_number"] == student_number].copy()

def add_semester_record(student_number, academic_year, semester, subjects_list, doc_path="", doc_upload_time=""):
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
        "amis_file_path": "",
        "doc_path": doc_path,
        "doc_upload_time": doc_upload_time,
        "doc_status": "Pending" if doc_path else "",
        "doc_remarks": "",
        "doc_validated_by": "",
        "doc_validated_time": ""
    }])
    df = pd.concat([df, new_record], ignore_index=True)
    save_semester_records(df)
    update_student_academic_summary(student_number)
    return gwa

def update_semester_subjects(student_number, academic_year, semester, subjects_list):
    """Replace the subjects list of an existing semester and recalc GWA/units."""
    df = load_semester_records()
    mask = (df["student_number"] == student_number) & (df["academic_year"] == academic_year) & (df["semester"] == semester)
    if mask.any():
        idx = df[mask].index[0]
        gwa = compute_gwa_from_subjects(subjects_list)
        total_units = sum(float(s.get("units", 0)) for s in subjects_list)
        df.at[idx, "subjects_json"] = json.dumps(subjects_list)
        df.at[idx, "total_units"] = total_units
        df.at[idx, "gwa"] = gwa
        # If document already approved and subjects changed, reset status to Pending
        if df.at[idx, "doc_status"] == "Approved":
            df.at[idx, "doc_status"] = "Pending"
            df.at[idx, "doc_remarks"] = "Subjects edited; re-upload required."
        save_semester_records(df)
        update_student_academic_summary(student_number)
        return True
    return False

def add_subject_to_semester(student_number, academic_year, semester, new_subject):
    df = load_semester_records()
    mask = (df["student_number"] == student_number) & (df["academic_year"] == academic_year) & (df["semester"] == semester)
    if not mask.any():
        st.error("Semester not found. Create semester first.")
        return False
    idx = df[mask].index[0]
    subjects = json.loads(df.at[idx, "subjects_json"])
    subjects.append(new_subject)
    return update_semester_subjects(student_number, academic_year, semester, subjects)

def update_semester_document(student_number, academic_year, semester, doc_path, doc_upload_time, status="Pending"):
    df = load_semester_records()
    mask = (df["student_number"] == student_number) & (df["academic_year"] == academic_year) & (df["semester"] == semester)
    if mask.any():
        idx = df[mask].index[0]
        df.at[idx, "doc_path"] = doc_path
        df.at[idx, "doc_upload_time"] = doc_upload_time
        df.at[idx, "doc_status"] = status
        df.at[idx, "doc_remarks"] = ""
        df.at[idx, "doc_validated_by"] = ""
        df.at[idx, "doc_validated_time"] = ""
        save_semester_records(df)
        return True
    return False

def validate_semester_document(student_number, academic_year, semester, status, remarks, validator_name):
    df = load_semester_records()
    mask = (df["student_number"] == student_number) & (df["academic_year"] == academic_year) & (df["semester"] == semester)
    if mask.any():
        idx = df[mask].index[0]
        df.at[idx, "doc_status"] = status
        df.at[idx, "doc_remarks"] = remarks
        df.at[idx, "doc_validated_by"] = validator_name
        df.at[idx, "doc_validated_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_semester_records(df)
        return True
    return False

def get_next_semester_sequence(academic_year, semester):
    sem_order = ["1st Sem", "2nd Sem", "Summer"]
    if semester not in sem_order:
        return academic_year, "1st Sem"
    idx = sem_order.index(semester)
    if idx < 2:
        return academic_year, sem_order[idx+1]
    else:
        start_year = int(academic_year.split("-")[0])
        next_ay = f"{start_year+1}-{start_year+2}"
        return next_ay, "1st Sem"

def create_next_semester(student_number, current_ay, current_sem):
    next_ay, next_sem = get_next_semester_sequence(current_ay, current_sem)
    df = load_semester_records()
    mask = (df["student_number"] == student_number) & (df["academic_year"] == next_ay) & (df["semester"] == next_sem)
    if mask.any():
        st.warning(f"Semester {next_ay} {next_sem} already exists.")
        return False
    add_semester_record(student_number, next_ay, next_sem, [])
    st.success(f"Created new semester: {next_ay} {next_sem}")
    return True

def update_student_academic_summary(student_number):
    semesters = get_student_semesters(student_number)
    if len(semesters) == 0:
        return
    total_grade_points = 0
    total_units_all = 0
    for _, row in semesters.iterrows():
        subjects = json.loads(row["subjects_json"])
        for subj in subjects:
            try:
                units = float(subj.get("units", 0))
                grade = float(subj.get("grade", 0))
                total_units_all += units
                total_grade_points += units * grade
            except (ValueError, TypeError):
                continue
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

# ==================== DOCUMENT UPLOAD SYSTEM ====================
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

# ==================== MILESTONE SUBMISSION ====================
MILESTONE_REQUESTS_FILE = "milestone_requests.csv"

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

def save_milestone_request_file(student_number, milestone_label, uploaded_file):
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
    if is_phd_program(program):
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

def create_demo_data():
    data = {
        "student_number": ["S001", "S002", "S003", "S004", "S005", "S006", "S007", "S008", "S009", "S010", "S011", "S012", "S013"],
        "name": [
            "Santos, Maria Concepcion R.",
            "Dela Cruz, Jose Mari P.",
            "Fernandez, Kristoffer Ivan M.",
            "Lopez, Maria Isabella T.",
            "Villanueva, Gabriel Angelo S.",
            "Reyes, Patricia Anne G.",
            "Gomez, Emmanuel D.",
            "Mendoza, Catherine Joy L.",
            "Santiago, Rommel C.",
            "Ramirez, Maria Lourdes E.",
            "Torres, Victor Emmanuel A.",
            "Bautista, Anna Patricia F.",
            "Aquino, Francis Joseph T."
        ],
        "last_name": ["Santos", "Dela Cruz", "Fernandez", "Lopez", "Villanueva", "Reyes", "Gomez", "Mendoza", "Santiago", "Ramirez", "Torres", "Bautista", "Aquino"],
        "first_name": ["Maria Concepcion", "Jose Mari", "Kristoffer Ivan", "Maria Isabella", "Gabriel Angelo", "Patricia Anne", "Emmanuel", "Catherine Joy", "Rommel", "Maria Lourdes", "Victor Emmanuel", "Anna Patricia", "Francis Joseph"],
        "middle_name": ["R.", "P.", "M.", "T.", "S.", "G.", "D.", "L.", "C.", "E.", "A.", "F.", "T."],
        "program": [
            PROGRAMS[0], PROGRAMS[0], PROGRAMS[1], PROGRAMS[0], PROGRAMS[0], PROGRAMS[0],
            PROGRAMS[0], PROGRAMS[0], PROGRAMS[1], PROGRAMS[0], PROGRAMS[0], PROGRAMS[0], PROGRAMS[0]
        ],
        "advisor": ["Dr. Eslava", "Dr. Sanchez", "Dr. Eslava", "Dr. Sanchez", "Dr. Eslava", "Dr. Sanchez",
                    "Dr. Eslava", "Dr. Sanchez", "Dr. Eslava", "Dr. Sanchez", "Dr. Eslava", "Dr. Sanchez", "Dr. Eslava"],
        "ay_start": [2022, 2023, 2022, 2022, 2022, 2023, 2022, 2022, 2022, 2022, 2022, 2022, 2022],
        "semester": ["1st Sem"] * 13,
        "profile_pic": [""] * 13,
        "committee_members_structured": [
            "Dr. Eslava|Chair (Major Professor)\nDr. Sanchez|Member",
            "Dr. Sanchez|Chair (Adviser)\nDr. Eslava|Member",
            "Dr. Eslava|Chair (Major Professor)\nDr. Sanchez|Member",
            "Dr. Sanchez|Chair\nDr. Eslava|Member",
            "Dr. Eslava|Chair",
            "Dr. Sanchez|Chair",
            "",
            "Dr. Eslava|Chair\nDr. Sanchez|Member",
            "Dr. Sanchez|Chair (Adviser)\nDr. Eslava|Member\nDr. Cruz|Member",
            "Dr. Eslava|Chair (Major Professor)\nDr. Sanchez|Member",
            "Dr. Sanchez|Chair\nDr. Eslava|Member",
            "Dr. Eslava|Chair",
            "Dr. Sanchez|Chair\nDr. Eslava|Member"
        ],
        "committee_approval_date": [
            "2022-06-01", "2023-08-15", "2022-07-10", "2022-07-10", "2022-06-20",
            "2023-09-10", "", "2022-08-01", "2022-08-01", "2022-06-01", "2022-06-01",
            "2022-08-01", "2022-06-20"
        ],
        "pos_status": [
            "Approved", "Pending", "Approved", "Approved", "Approved", "Approved", "Pending",
            "Approved", "Approved", "Approved", "Approved", "Approved", "Approved"
        ],
        "pos_submitted_date": [
            "2022-05-15", "", "2022-06-05", "2022-06-05", "2022-05-20", "2023-08-20", "",
            "2022-07-15", "2022-07-15", "2022-05-10", "2022-05-10", "2022-07-15", "2022-05-20"
        ],
        "pos_approved_date": [
            "2022-06-01", "", "2022-07-10", "2022-07-10", "2022-06-20", "2023-09-10", "",
            "2022-08-01", "2022-08-01", "2022-06-01", "2022-06-01", "2022-08-01", "2022-06-20"
        ],
        "pos_file": [""] * 13,
        "gwa": [1.80, 1.95, 1.85, 2.30, 1.90, 1.88, 1.75, 1.85, 1.80, 1.80, 1.80, 1.85, 1.90],
        "total_units_taken": [24, 12, 24, 24, 24, 15, 24, 18, 24, 24, 24, 24, 24],
        "total_units_required": [24] * 13,
        "thesis_units_taken": [6, 2, 6, 6, 4, 2, 3, 2, 8, 3, 6, 6, 6],
        "thesis_units_limit": [6, 6, 12, 6, 6, 6, 6, 6, 12, 6, 6, 6, 6],
        "thesis_outline_approved": [
            "Yes", "Yes", "Yes", "Yes", "No", "Yes", "No", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes"
        ],
        "thesis_outline_approved_date": [
            "2023-11-01", "2023-12-01", "2023-06-01", "2023-09-20", "", "2023-12-01", "",
            "2023-11-10", "2023-11-10", "2023-11-01", "2023-11-01", "2023-11-10", "2023-06-20"
        ],
        "thesis_outline_file": [""] * 13,
        "thesis_draft_file": [""] * 13,
        "thesis_manuscript_file": [""] * 13,
        "thesis_status": [
            "Approved", "In Progress", "Approved", "Approved", "In Progress", "In Progress",
            "Not Started", "In Progress", "In Progress", "Approved", "Approved", "Approved", "Approved"
        ],
        "qualifying_exam_status": ["N/A", "N/A", "Passed", "N/A", "N/A", "N/A", "N/A", "N/A", "Passed", "N/A", "N/A", "N/A", "N/A"],
        "qualifying_exam_passed_date": ["", "", "2023-12-01", "", "", "", "", "", "2023-11-01", "", "", "", ""],
        "qualifying_exam_file": [""] * 13,
        "written_comprehensive_status": ["N/A", "N/A", "Failed", "N/A", "N/A", "N/A", "N/A", "N/A", "Passed", "N/A", "N/A", "N/A", "N/A"],
        "written_comprehensive_passed_date": ["", "", "", "", "", "", "", "", "2023-11-15", "", "", "", ""],
        "written_comprehensive_file": [""] * 13,
        "oral_comprehensive_status": ["N/A", "N/A", "Not Taken", "N/A", "N/A", "N/A", "N/A", "N/A", "Failed", "N/A", "N/A", "N/A", "N/A"],
        "oral_comprehensive_passed_date": [""] * 13,
        "oral_comprehensive_file": [""] * 13,
        "general_exam_status": [
            "Passed", "Passed", "N/A", "Passed", "Passed", "Not Taken", "Not Taken", "Not Taken", "N/A",
            "Passed", "Passed", "Passed", "Passed"
        ],
        "general_exam_passed_date": [
            "2023-12-10", "2023-11-05", "", "2023-10-15", "2023-11-20", "", "", "", "",
            "2023-10-01", "2023-10-01", "2023-10-01", "2023-10-01"
        ],
        "general_exam_file": [""] * 13,
        "final_exam_status": [
            "Passed", "Not Taken", "Not Taken", "Not Taken", "Not Taken", "Not Taken", "Not Taken",
            "Not Taken", "Not Taken", "Not Taken", "Not Taken", "Passed", "Not Taken"
        ],
        "final_exam_passed_date": [
            "2024-02-15", "", "", "", "", "", "", "", "", "", "", "2024-02-01", ""
        ],
        "final_exam_file": [""] * 13,
        "residency_years_used": [3, 1, 3, 3, 3, 1, 2, 2, 3, 3, 3, 3, 3],
        "residency_max_years": [5, 5, 7, 5, 5, 5, 5, 5, 7, 5, 5, 5, 5],
        "extension_count": [0] * 13,
        "extension_end_date": [""] * 13,
        "loa_start_date": [""] * 13,
        "loa_end_date": [""] * 13,
        "loa_total_terms": [0] * 13,
        "awol_status": ["No"] * 13,
        "awol_lifted_date": [""] * 13,
        "transfer_units_approved": [0] * 13,
        "graduation_applied": [
            "Yes", "No", "No", "No", "No", "No", "No", "No", "No", "No", "No", "Yes", "Yes"
        ],
        "graduation_approved": [
            "Yes", "No", "No", "No", "No", "No", "No", "No", "No", "No", "No", "Pending", "Pending"
        ],
        "graduation_date": ["2024-06-15", "", "", "", "", "", "", "", "", "", "", "", ""],
        "re_admission_status": ["Not Applicable"] * 13,
        "re_admission_date": [""] * 13,
        "committee_changed": [False, False, False, False, False, False, False, False, False, True, False, False, False],
        "coursework_changed": [False, False, False, False, False, False, False, False, False, False, True, False, False]
    }
    return pd.DataFrame(data)

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if len(df) < 13:
            df = create_demo_data()
            save_data(df)
    else:
        df = create_demo_data()
        save_data(df)

    default_df = create_demo_data()
    for col in default_df.columns:
        if col not in df.columns:
            df[col] = default_df[col]

    new_file_cols = ["pos_file", "thesis_outline_file", "thesis_draft_file", "thesis_manuscript_file",
                     "qualifying_exam_file", "written_comprehensive_file", "oral_comprehensive_file",
                     "general_exam_file", "final_exam_file", "committee_changed", "coursework_changed"]
    for col in new_file_cols:
        if col not in df.columns:
            df[col] = False if col in ["committee_changed", "coursework_changed"] else ""
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

    numeric_int_cols = ["thesis_units_taken", "thesis_units_limit", "total_units_taken", "total_units_required",
                        "residency_years_used", "residency_max_years", "extension_count", "loa_total_terms",
                        "transfer_units_approved", "ay_start"]
    for col in numeric_int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    if "gwa" in df.columns:
        df["gwa"] = pd.to_numeric(df["gwa"], errors='coerce').fillna(2.0).astype(float)

    for idx, row in df.iterrows():
        program = str(row["program"]).strip()
        if program not in PROGRAMS:
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
                    try:
                        units = float(subj.get("units", 0))
                        grade = float(subj.get("grade", 0))
                        total_units += units
                        total_grade += units * grade
                    except (ValueError, TypeError):
                        continue
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

# ==================== VALIDATION FUNCTIONS ====================
def validate_student_data(student):
    warnings = []
    if student["pos_status"] == "Approved" and (pd.isna(student["pos_approved_date"]) or not student["pos_approved_date"]):
        warnings.append("POS is Approved but no approval date.")
    if student["thesis_outline_approved"] == "Yes" and (pd.isna(student["thesis_outline_approved_date"]) or not student["thesis_outline_approved_date"]):
        warnings.append("Thesis outline is approved but no approval date.")
    if student["committee_approval_date"] and student["committee_approval_date"] != "":
        pass
    elif student.get("committee_members_structured") and student.get("committee_members_structured") != "":
        warnings.append("Committee members are listed but committee approval date is missing.")
    if student["qualifying_exam_status"] == "Passed" and (pd.isna(student["qualifying_exam_passed_date"]) or not student["qualifying_exam_passed_date"]):
        warnings.append("Qualifying Exam is Passed but no date.")
    if student["written_comprehensive_status"] == "Passed" and (pd.isna(student["written_comprehensive_passed_date"]) or not student["written_comprehensive_passed_date"]):
        warnings.append("Written Comprehensive Exam is Passed but no date.")
    if student["oral_comprehensive_status"] == "Passed" and (pd.isna(student["oral_comprehensive_passed_date"]) or not student["oral_comprehensive_passed_date"]):
        warnings.append("Oral Comprehensive Exam is Passed but no date.")
    if student["general_exam_status"] == "Passed" and (pd.isna(student["general_exam_passed_date"]) or not student["general_exam_passed_date"]):
        warnings.append("General Exam is Passed but no date.")
    if student["final_exam_status"] == "Passed" and (pd.isna(student["final_exam_passed_date"]) or not student["final_exam_passed_date"]):
        warnings.append("Final Exam is Passed but no date.")
    if student["graduation_approved"] == "Yes" and (pd.isna(student["graduation_date"]) or not student["graduation_date"]):
        warnings.append("Graduation is approved but no graduation date.")
    return warnings

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

def get_committee_deadline_warning(row):
    if not row.get("committee_approval_date") and row.get("residency_years_used") >= 1:
        return "⚠️ Committee not yet approved. Required within first year."
    return "✅ Committee on track"

def get_publication_requirement_warning(row):
    ptype = get_program_type(row["program"])
    if ptype in ["PhD_Regular", "PhD_Straight", "PhD_Research"]:
        milestones = get_student_milestones(row["student_number"], ptype)
        pub_row = milestones[milestones["milestone"].str.contains("Publication", case=False)]
        if len(pub_row) > 0:
            pub_status = pub_row.iloc[0]["status"]
            if pub_status != "Completed" and row["graduation_applied"] == "Yes":
                return "⚠️ Publication requirement not met before graduation."
    return "✅ Publication requirement satisfied."

def get_all_warnings(row):
    warnings = []
    for check in [get_warning_text, check_residency_warning, check_gwa_warning, check_awol_warning, check_loa_warning,
                  check_thesis_outline_deadline, check_qualifying_exam_deadline, check_comprehensive_exam_deadline,
                  get_committee_deadline_warning, get_publication_requirement_warning]:
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
                st.markdown(f'<div style="background:#e8f5e9; border-radius:12px; padding:0.5rem; text-align:center; margin:0.2rem;"><div style="font-size:1rem;">✅</div><div style="font-weight:500;">{step}</div><div style="font-size:0.7rem; color:#2e7d32;">Completed</div></div>', unsafe_allow_html=True)
            elif step == next_step:
                st.markdown(f'<div style="background:#fff3e0; border:2px solid #ff9800; border-radius:12px; padding:0.5rem; text-align:center; margin:0.2rem;"><div style="font-size:1rem;">⏳</div><div style="font-weight:500;">{step}</div><div style="font-size:0.7rem; color:#e65100;">Next Required</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="background:#f5f5f5; border-radius:12px; padding:0.5rem; text-align:center; margin:0.2rem; opacity:0.6;"><div style="font-size:1rem;">🔒</div><div style="font-weight:500;">{step}</div><div style="font-size:0.7rem; color:#757575;">Locked</div></div>', unsafe_allow_html=True)

# ==================== COURSEWORK DISPLAY FUNCTIONS ====================
GRADE_OPTIONS = ["1.00", "1.25", "1.50", "1.75", "2.00", "2.25", "2.50", "2.75", "3.00", "INC", "DRP", "5.00", "P", "IP"]

def get_status_badge(status):
    if status == "Approved":
        return '<span class="status-approved">✅ Approved</span>'
    elif status == "Rejected":
        return '<span class="status-rejected">❌ Rejected</span>'
    elif status == "Pending":
        return '<span class="status-pending">🟡 Pending</span>'
    else:
        return '<span class="status-pending">📄 No document uploaded</span>'

def render_semester_block_student(student_number, semester_row):
    """Render a single semester block with editable subjects, Add Subject button, and document upload."""
    ay = semester_row["academic_year"]
    sem = semester_row["semester"]
    subjects = json.loads(semester_row["subjects_json"])
    total_units = semester_row["total_units"]
    gwa = semester_row["gwa"]
    doc_status = semester_row.get("doc_status", "")
    doc_path = semester_row.get("doc_path", "")
    doc_remarks = semester_row.get("doc_remarks", "")

    status_badge = get_status_badge(doc_status)
    with st.container():
        st.markdown(f"### 📅 {ay} | {sem}")
        st.markdown(f"**Validation Status:** {status_badge}", unsafe_allow_html=True)
        if doc_status == "Rejected" and doc_remarks:
            st.warning(f"**Rejection reason:** {doc_remarks}")

        # Editable subjects table
        if subjects:
            df_edit = pd.DataFrame(subjects)
            for col in ["course_code", "course_description", "units", "grade"]:
                if col not in df_edit.columns:
                    if col == "course_description":
                        df_edit["course_description"] = df_edit.get("name", "")
                    else:
                        df_edit[col] = ""
            df_edit = df_edit[["course_code", "course_description", "units", "grade"]]

            edited_df = st.data_editor(
                df_edit,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "course_code": "Course Code",
                    "course_description": "Course Description",
                    "units": st.column_config.NumberColumn("Units", step=1, min_value=0),
                    "grade": st.column_config.SelectColumn("Grade", options=GRADE_OPTIONS)
                },
                key=f"editor_{student_number}_{ay}_{sem}"
            )
            if st.button("💾 Save Subjects", key=f"save_subjects_{student_number}_{ay}_{sem}"):
                new_subjects = edited_df.to_dict("records")
                for s in new_subjects:
                    s["units"] = int(s["units"])
                if update_semester_subjects(student_number, ay, sem, new_subjects):
                    st.success("Subjects updated!")
                    st.rerun()
                else:
                    st.error("Failed to update subjects.")
        else:
            st.caption("No subjects yet. Use 'Add Subject' below.")

        st.markdown(f"**Semester Total Units:** {total_units}  **Semester GWA:** {gwa:.2f}")

        st.markdown("---")
        st.markdown("**Add a new subject**")
        with st.form(key=f"add_subject_{student_number}_{ay}_{sem}"):
            col1, col2 = st.columns(2)
            with col1:
                code = st.text_input("Course Code", key=f"code_{ay}_{sem}")
                units = st.number_input("Units", min_value=0, max_value=12, step=1, value=3, key=f"units_{ay}_{sem}")
            with col2:
                desc = st.text_input("Course Description", key=f"desc_{ay}_{sem}")
                grade = st.selectbox("Grade", options=GRADE_OPTIONS, index=0, key=f"grade_{ay}_{sem}")
            add_submitted = st.form_submit_button("➕ Add Subject")
            if add_submitted:
                if not code.strip() and not desc.strip():
                    st.error("Please enter at least a course code or description.")
                else:
                    new_subject = {
                        "course_code": code.strip(),
                        "course_description": desc.strip(),
                        "units": int(units),
                        "grade": grade
                    }
                    success = add_subject_to_semester(student_number, ay, sem, new_subject)
                    if success:
                        st.success(f"Subject added!")
                        st.rerun()
                    else:
                        st.error("Failed to add subject.")

        st.markdown("---")
        st.markdown("**Upload Supporting Document (AMIS Screenshot or Grade Report)**")
        if doc_path and os.path.exists(doc_path):
            st.info(f"Currently uploaded: {os.path.basename(doc_path)} (uploaded on {semester_row.get('doc_upload_time', 'unknown')})")
            if doc_status == "Rejected":
                st.warning("Your document was rejected. Please upload a corrected version.")
        with st.form(key=f"upload_doc_{student_number}_{ay}_{sem}"):
            uploaded_file = st.file_uploader("Choose file (PDF, JPG, PNG)", type=["pdf", "jpg", "jpeg", "png"], key=f"upload_{ay}_{sem}")
            submit_upload = st.form_submit_button("📎 Upload Document")
            if submit_upload and uploaded_file:
                student_folder = os.path.join(UPLOAD_FOLDER, student_number, "semester_docs")
                os.makedirs(student_folder, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{ay}_{sem}_{timestamp}.{uploaded_file.name.split('.')[-1].lower()}"
                filepath = os.path.join(student_folder, filename)
                with open(filepath, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                success = update_semester_document(student_number, ay, sem, filepath, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Pending")
                if success:
                    st.success("Document uploaded! Waiting for validation.")
                    st.rerun()
                else:
                    st.error("Failed to update record.")

def render_semester_section_staff(student_number, semester_row):
    """Staff view: read-only subjects and document preview."""
    ay = semester_row["academic_year"]
    sem = semester_row["semester"]
    subjects = json.loads(semester_row["subjects_json"])
    total_units = semester_row["total_units"]
    gwa = semester_row["gwa"]
    doc_status = semester_row.get("doc_status", "")
    doc_path = semester_row.get("doc_path", "")
    doc_upload_time = semester_row.get("doc_upload_time", "")
    doc_remarks = semester_row.get("doc_remarks", "")

    status_badge = get_status_badge(doc_status)
    with st.container():
        st.markdown(f"### 📅 {ay} | {sem}")
        st.markdown(f"**Validation Status:** {status_badge}", unsafe_allow_html=True)
        if subjects:
            df_display = pd.DataFrame([
                {"Course Code": s.get("course_code", ""), "Course Description": s.get("course_description", s.get("name", "")),
                 "Units": s["units"], "Grade": s["grade"]} for s in subjects
            ])
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        st.markdown(f"**Semester Total Units:** {total_units}  **Semester GWA:** {gwa:.2f}")

        if doc_path and os.path.exists(doc_path):
            st.markdown("**Uploaded Document:**")
            if doc_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                st.image(doc_path, width=300)
            else:
                with open(doc_path, "rb") as f:
                    st.download_button("Download Document", f, file_name=os.path.basename(doc_path))
            st.caption(f"Uploaded on: {doc_upload_time}")
            if doc_remarks:
                st.write(f"**Remarks:** {doc_remarks}")
        else:
            st.info("No document uploaded for this semester.")

def render_validation_panel(records_df, students_df, role):
    """Display all pending documents grouped by student for Staff/Adviser to approve/reject."""
    if records_df.empty:
        st.info("No semester records found.")
        return

    status_filter = st.radio("Show records with status:", ["All", "Pending", "Approved", "Rejected"], horizontal=True)
    if status_filter != "All":
        records_df = records_df[records_df["doc_status"] == status_filter]

    if records_df.empty:
        st.info(f"No {status_filter} documents.")
        return

    for idx, row in records_df.iterrows():
        student_number = row["student_number"]
        student_name = students_df.loc[students_df["student_number"] == student_number, "name"].values
        student_name = student_name[0] if len(student_name) > 0 else student_number
        ay = row["academic_year"]
        sem = row["semester"]
        doc_status = row.get("doc_status", "")
        doc_path = row.get("doc_path", "")
        subjects = json.loads(row["subjects_json"])
        total_units = row["total_units"]
        gwa = row["gwa"]

        with st.expander(f"📌 {student_name} ({student_number}) – {ay} {sem} – Status: {doc_status}"):
            st.write(f"**Total Units:** {total_units} **GWA:** {gwa:.2f}")
            if subjects:
                df_subj = pd.DataFrame([
                    {"Code": s.get("course_code", ""), "Description": s.get("course_description", ""), "Units": s["units"], "Grade": s["grade"]}
                    for s in subjects
                ])
                st.dataframe(df_subj, use_container_width=True, hide_index=True)

            if doc_path and os.path.exists(doc_path):
                if doc_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    st.image(doc_path, width=300)
                else:
                    with open(doc_path, "rb") as f:
                        st.download_button("Download Document", f, file_name=os.path.basename(doc_path))

            if doc_status == "Pending":
                remarks = st.text_area("Remarks (optional)", key=f"remarks_{student_number}_{ay}_{sem}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Approve", key=f"approve_{student_number}_{ay}_{sem}"):
                        validate_semester_document(student_number, ay, sem, "Approved", remarks, st.session_state.display_name)
                        st.success("Document approved.")
                        st.rerun()
                with col2:
                    if st.button("❌ Reject", key=f"reject_{student_number}_{ay}_{sem}"):
                        validate_semester_document(student_number, ay, sem, "Rejected", remarks, st.session_state.display_name)
                        st.warning("Document rejected.")
                        st.rerun()
            else:
                st.info(f"Status: {doc_status}")
                if row.get("doc_remarks"):
                    st.write(f"**Remarks:** {row['doc_remarks']}")
                if row.get("doc_validated_by"):
                    st.caption(f"Validated by: {row['doc_validated_by']} on {row['doc_validated_time']}")

# ==================== LOGIN PAGE ====================
if not st.session_state.logged_in:
    st.markdown('<div style="text-align:center; margin-bottom:1rem;"><h1>🎓 SESAM KMIS</h1><p style="color:#6c757d;">Graduate Student Lifecycle Management System</p></div>', unsafe_allow_html=True)
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
                    st.session_state.consent_given = False
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            st.caption("Demo: staff1/admin123 | adviser1/adv123 | student numbers S001-S013 with password = student number")
    st.stop()

# ==================== DATA PRIVACY CONSENT CHECK ====================
if st.session_state.logged_in and not st.session_state.consent_given:
    show_consent_form()
    st.stop()

# ==================== DATA LOAD ====================
df = load_data()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown(f"""
    <div style="background:white; border-radius:20px; padding:0.8rem; margin-bottom:1rem; text-align:center; box-shadow:0 2px 6px rgba(0,0,0,0.05);">
        <h3 style="margin:0 0 0.2rem; font-size:1.1rem;">👤 {st.session_state.display_name}</h3>
        <div style="font-size:0.75rem; color:#2c7da0; background:#e6f4f5; display:inline-block; padding:0.2rem 0.6rem; border-radius:20px;">{st.session_state.role}</div>
        <div style="font-size:0.65rem; margin-top:0.3rem; color:#22c55e;">✅ Consent given</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.consent_given = False
        for key in ["username", "role", "display_name", "selected_student"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    st.markdown("---")
    st.caption("Version 9.0 | Per-Semester Blocks | Editable Subjects | Document Validation")
    st.caption("© SESAM 2026")

# ==================== MAIN ====================
st.title("🎓 SESAM Graduate Student Lifecycle Management")
st.caption("Complete workflow tracking from admission to graduation")

role = st.session_state.role

# ==================== STAFF VIEW ====================
if role == "SESAM Staff":
    st.subheader("📋 Student Directory")
    search = st.text_input("🔍 Search by name or student number", placeholder="e.g., S001 or Santos", key="staff_search")
    filtered_df = filter_dataframe(search, df)
    filtered_df["admitted_year"] = filtered_df.apply(lambda row: format_ay(row["ay_start"], row["semester"]), axis=1)
    if len(filtered_df) > 0:
        display_df = filtered_df[["student_number", "name", "program", "admitted_year", "advisor", "gwa", "pos_status", "final_exam_status"]].copy()
        display_df.rename(columns={"admitted_year": "Admitted Year", "gwa": "Cumulative GWA"}, inplace=True)
        st.dataframe(display_df, use_container_width=True, height=350)
    else:
        st.info("No students match the current search.")

    with st.expander("⚠️ Data Consistency Warnings (Admin View)", expanded=False):
        for idx, row in filtered_df.iterrows():
            warnings = validate_student_data(row)
            if warnings:
                st.warning(f"**{row['name']} ({row['student_number']})**")
                for w in warnings:
                    st.write(f"- {w}")
        st.info("These warnings indicate missing dates for approved/passed milestones.")

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        btn_validate = st.button("📄 Document Validation Panel", use_container_width=True, key="staff_validate_btn")
    with col2:
        btn_update = st.button("✏️ Update Student", use_container_width=True, key="staff_btn_update")
    with col3:
        btn_add = st.button("➕ Add New Student", use_container_width=True, key="staff_btn_add")

    if "staff_show_validate" not in st.session_state:
        st.session_state.staff_show_validate = False
    if "staff_show_update" not in st.session_state:
        st.session_state.staff_show_update = False
    if "staff_show_add" not in st.session_state:
        st.session_state.staff_show_add = False

    if btn_validate:
        st.session_state.staff_show_validate = not st.session_state.staff_show_validate
        st.session_state.staff_show_update = False
        st.session_state.staff_show_add = False
        st.rerun()
    if btn_update:
        st.session_state.staff_show_update = not st.session_state.staff_show_update
        st.session_state.staff_show_validate = False
        st.session_state.staff_show_add = False
        st.rerun()
    if btn_add:
        st.session_state.staff_show_add = not st.session_state.staff_show_add
        st.session_state.staff_show_validate = False
        st.session_state.staff_show_update = False
        st.rerun()

    # Validation Panel
    if st.session_state.staff_show_validate:
        st.subheader("📄 Document Validation Panel")
        semesters_all = load_semester_records()
        if semesters_all.empty:
            st.info("No semester records found.")
        else:
            render_validation_panel(semesters_all, df, role)

    # Update Student Form
    if st.session_state.staff_show_update:
        st.subheader("✏️ Update Student Record")
        if len(filtered_df) == 0:
            st.warning("No students available to edit.")
        else:
            selected_student_name = st.selectbox("Select a student to edit", options=filtered_df["name"].tolist(), key="staff_update_select")
            student = filtered_df[filtered_df["name"] == selected_student_name].iloc[0].copy()
            if st.button("❌ Cancel", key="cancel_update"):
                st.session_state.staff_show_update = False
                st.rerun()
            st.markdown(f"### Editing: {student['name']} ({student['student_number']}) | Program: {student['program']}")

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

            tab_labels = ["📝 Info", "📚 Coursework", "📝 Exams", "🏠 Residency", "🎓 Graduation", "👥 Committee", "📁 Docs", "✅ Requests"]
            tabs = st.tabs(tab_labels)

            with tabs[0]:  # Info
                col1, col2 = st.columns([1,2])
                with col1:
                    pic_path = get_profile_picture_path(student["student_number"])
                    if pic_path and os.path.exists(pic_path):
                        st.image(pic_path, width=150)
                    else:
                        st.info("No profile picture")
                with col2:
                    st.markdown(f"**Student Number:** {student['student_number']}")
                    st.markdown(f"**Full Name:** {student['name']}")
                    st.markdown(f"**Program:** {student['program']}")
                    st.markdown(f"**Advisor:** {student['advisor']}")
                    st.markdown(f"**Admitted Year:** {format_ay(student['ay_start'], student['semester'])}")
                    st.markdown(f"**Cumulative GWA:** {student['gwa']:.2f}")

            with tabs[1]:  # Coursework (Staff view: read-only semester blocks)
                st.subheader("Student's Academic Record")
                semesters = get_student_semesters(student["student_number"])
                if semesters.empty:
                    st.info("No semesters yet.")
                else:
                    for _, sem_row in semesters.iterrows():
                        render_semester_section_staff(student["student_number"], sem_row)
                st.markdown("---")
                st.subheader("➕ Add Next Semester (Staff)")
                if st.button("➕ Add Next Semester", key=f"staff_next_sem_{student['student_number']}"):
                    semesters = get_student_semesters(student["student_number"])
                    last_sem = semesters.iloc[-1] if not semesters.empty else None
                    if last_sem is None:
                        default_ay = f"{current_year}-{current_year+1}"
                        default_sem = "1st Sem"
                        success = add_semester_record(student["student_number"], default_ay, default_sem, [])
                        if success is not None:
                            st.success(f"Created first semester: {default_ay} {default_sem}")
                            st.rerun()
                    else:
                        next_ay, next_sem = get_next_semester_sequence(last_sem["academic_year"], last_sem["semester"])
                        success = create_next_semester(student["student_number"], last_sem["academic_year"], last_sem["semester"])
                        if success:
                            st.rerun()
                st.markdown("---")
                st.subheader("Manual Override (GWA / Units)")
                with st.form("staff_coursework_override"):
                    gwa_manual = st.number_input("GWA (override)", min_value=1.0, max_value=5.0, value=float(student["gwa"]))
                    total_units_taken = st.number_input("Total Units Taken (override)", min_value=0, value=int(student["total_units_taken"]))
                    if st.form_submit_button("Update Totals"):
                        df.loc[df["student_number"]==student["student_number"], ["gwa","total_units_taken"]] = [gwa_manual, total_units_taken]
                        save_data(df)
                        st.success("Totals updated manually.")
                        st.rerun()

            with tabs[2]:  # Exams
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
                            df.loc[df["student_number"]==student["student_number"],
                                   ["qualifying_exam_status","qualifying_exam_passed_date","written_comprehensive_status","written_comprehensive_passed_date","oral_comprehensive_status","oral_comprehensive_passed_date","general_exam_status","general_exam_passed_date","final_exam_status","final_exam_passed_date"]] = \
                                   [qual, qual_date, written, written_date, oral, oral_date, general, general_date, final, final_date]
                            save_data(df)
                            st.success("Updated")
                            st.rerun()
                        else:
                            st.error("Locked step cannot be edited")

            with tabs[3]:  # Residency
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
                        df.loc[df["student_number"]==student["student_number"],
                               ["residency_years_used","extension_count","extension_end_date","loa_start_date","loa_end_date","loa_total_terms","awol_status","awol_lifted_date"]] = \
                               [residency_used, extension_count, extension_end, loa_start, loa_end, loa_terms, awol, awol_lifted]
                        save_data(df)
                        st.success("Updated")
                        st.rerun()

            with tabs[4]:  # Graduation
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
                            df.loc[df["student_number"]==student["student_number"],
                                   ["graduation_applied","graduation_approved","graduation_date","transfer_units_approved"]] = \
                                   [grad_applied, grad_approved, grad_date, transfer_units]
                            save_data(df)
                            st.success("Updated")
                            st.rerun()
                        else:
                            st.error("Cannot approve graduation before Final Exam")

            with tabs[5]:  # Committee
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
                        try:
                            role_idx = role_options.index(member["role"])
                        except ValueError:
                            role_idx = role_options.index(default_role)
                        role = st.selectbox(f"Role", options=role_options, index=role_idx, key=f"role_{student['student_number']}_{idx}")
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
                        st.success("Committee saved!")
                        st.rerun()

            with tabs[6]:  # Docs
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

            with tabs[7]:  # Requests
                st.subheader("📌 Pending Milestone Validations")
                requests_df = load_milestone_requests()
                student_requests = requests_df[requests_df["student_number"] == student["student_number"]].copy()
                pending = student_requests[student_requests["status"] == "Pending"]
                if len(pending) == 0:
                    st.info("No pending milestone requests for this student.")
                else:
                    for _, req in pending.iterrows():
                        with st.expander(f"{req['milestone_label']} - Submitted on {req['submitted_date']}"):
                            st.write(f"**Submitted:** {req['submitted_date']}")
                            file_path = req['file_path']
                            if pd.notna(file_path) and os.path.exists(file_path):
                                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                                    st.image(file_path, width=200)
                                else:
                                    st.write(f"📎 {os.path.basename(file_path)}")
                            else:
                                st.warning("File not found.")
                            comment = st.text_area("Reviewer Remarks", key=f"review_comment_{req['request_id']}")
                            col_a, col_b = st.columns(2)
                            with col_a:
                                if st.button("✅ Approve", key=f"approve_{req['request_id']}"):
                                    target_field = req['target_field']
                                    target_value = req['target_value']
                                    df.loc[df["student_number"] == student["student_number"], target_field] = target_value
                                    if target_field == "pos_status":
                                        df.loc[df["student_number"] == student["student_number"], "pos_approved_date"] = datetime.now().strftime("%Y-%m-%d")
                                    elif target_field == "thesis_outline_approved":
                                        df.loc[df["student_number"] == student["student_number"], "thesis_outline_approved_date"] = datetime.now().strftime("%Y-%m-%d")
                                    elif target_field == "graduation_applied":
                                        df.loc[df["student_number"] == student["student_number"], "graduation_date"] = datetime.now().strftime("%Y-%m-%d")
                                    requests_df.loc[req.name, "status"] = "Approved"
                                    requests_df.loc[req.name, "reviewer_comment"] = comment
                                    requests_df.loc[req.name, "reviewed_by"] = st.session_state.display_name
                                    requests_df.loc[req.name, "review_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    save_milestone_requests(requests_df)
                                    save_data(df)
                                    st.success("Approved!")
                                    st.rerun()
                            with col_b:
                                if st.button("❌ Reject", key=f"reject_{req['request_id']}"):
                                    requests_df.loc[req.name, "status"] = "Rejected"
                                    requests_df.loc[req.name, "reviewer_comment"] = comment
                                    requests_df.loc[req.name, "reviewed_by"] = st.session_state.display_name
                                    requests_df.loc[req.name, "review_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    save_milestone_requests(requests_df)
                                    st.warning("Rejected.")
                                    st.rerun()

    # Add New Student Form
    if st.session_state.staff_show_add:
        st.subheader("➕ Register New Student")
        if st.button("❌ Cancel", key="cancel_add"):
            st.session_state.staff_show_add = False
            st.rerun()
        with st.form(key="add_student_form_staff"):
            col1, col2 = st.columns(2)
            with col1:
                last_name = st.text_input("Last Name *", placeholder="Dela Cruz")
                first_name = st.text_input("First Name *", placeholder="Juan")
                student_number = st.text_input("Student Number *", placeholder="2025-00123")
                selected_ay_range = st.selectbox("Academic Year *", options=ACADEMIC_YEARS, index=ACADEMIC_YEARS.index(f"{current_year}-{current_year+1}") if f"{current_year}-{current_year+1}" in ACADEMIC_YEARS else 0)
                ay_start = int(selected_ay_range.split("-")[0])
            with col2:
                middle_name = st.text_input("Middle Name", placeholder="Santos (optional)")
                program = st.selectbox("Program *", options=PROGRAMS)
                semester = st.selectbox("Semester *", options=SEMESTERS)
                advisor = st.text_input("Advisor (optional)", placeholder="Dr. Faustino-Eslava")
            submitted = st.form_submit_button("Register Student", use_container_width=True)
            if submitted:
                errors = []
                if not last_name: errors.append("Last Name is required.")
                if not first_name: errors.append("First Name is required.")
                if not student_number: errors.append("Student Number is required.")
                if student_number in df["student_number"].values: errors.append("Student number already exists.")
                if errors:
                    for err in errors: st.error(err)
                else:
                    middle = f" {middle_name.strip()}" if middle_name.strip() else ""
                    full_name = f"{last_name.strip()}, {first_name.strip()}{middle}"
                    new_row = create_demo_data().iloc[0].to_dict()
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
                        "re_admission_date": "",
                        "committee_changed": False,
                        "coursework_changed": False
                    })
                    new_df = pd.DataFrame([new_row])
                    df = pd.concat([df, new_df], ignore_index=True)
                    save_data(df)
                    get_student_milestones(student_number.strip(), get_program_type(program))
                    st.success(f"✅ Student {full_name} registered successfully!")
                    st.session_state.staff_show_add = False
                    st.rerun()

# ==================== ADVISER VIEW ====================
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

        st.markdown("### 📄 Document Validation for Your Advisees")
        all_semesters = load_semester_records()
        advisee_numbers = advisees["student_number"].tolist()
        advisee_semesters = all_semesters[all_semesters["student_number"].isin(advisee_numbers)]
        render_validation_panel(advisee_semesters, df, role)

        st.markdown("---")
        st.subheader("📋 Advisee List")
        search_adv = st.text_input("🔍 Filter advisees")
        filtered = filter_dataframe(search_adv, advisees)
        filtered["admitted_year"] = filtered.apply(lambda row: format_ay(row["ay_start"], row["semester"]), axis=1)
        display_adv = filtered[["student_number","name","program","admitted_year","gwa","thesis_units_taken","pos_status","final_exam_status"]].copy()
        display_adv.rename(columns={"admitted_year": "Admitted Year", "gwa": "Cumulative GWA"}, inplace=True)
        st.dataframe(display_adv, use_container_width=True)
        for _, row in filtered.iterrows():
            with st.expander(f"📌 {row['name']} ({row['student_number']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Program", row["program"])
                    st.metric("Cumulative GWA", f"{row['gwa']:.2f}")
                    st.metric("Thesis Units", f"{row['thesis_units_taken']}/{get_thesis_limit(row['program'])}")
                with col2:
                    st.metric("Residency", f"{row['residency_years_used']}/{get_residency_max(row['program'])}")
                    st.metric("POS Status", row["pos_status"])
                    st.metric("Final Exam", row["final_exam_status"])
                display_workflow_grid(get_step_completion_status(row), get_next_required_step(row))
                pic = get_profile_picture_path(row["student_number"])
                if pic:
                    st.image(pic, width=80)
                for alert in check_deadline_alerts(row):
                    st.error(alert)
                for w in get_all_warnings(row):
                    st.warning(w) if "⚠️" in w else st.success(w)
        st.info("For updates, contact SESAM Staff.")

# ==================== STUDENT VIEW (ENHANCED) ====================
elif role == "Student":
    st.subheader(f"📘 Your Dashboard – {st.session_state.display_name}")
    student = df[df["name"] == st.session_state.display_name].iloc[0].copy()
    program_type = get_program_type(student["program"])

    def save_student_milestone_file(student_number, milestone_name, uploaded_file):
        if uploaded_file is None:
            return None
        milestone_folder = os.path.join("student_files", student_number, "milestones")
        if not os.path.exists(milestone_folder):
            os.makedirs(milestone_folder)
        ext = uploaded_file.name.split('.')[-1].lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = milestone_name.replace(" ", "_").replace("/", "_")
        filename = f"{safe_name}_{timestamp}.{ext}"
        filepath = os.path.join(milestone_folder, filename)
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return filepath

    def get_program_specific_alerts(student):
        alerts = []
        ptype = get_program_type(student["program"])
        if not student.get("committee_approval_date") and student["residency_years_used"] >= 1:
            alerts.append("⚠️ Committee not yet approved. Required within first year of residency.")
        if ptype in ["PhD_Regular", "PhD_Straight", "PhD_Research"]:
            milestones_df = get_student_milestones(student["student_number"], ptype)
            pub_rows = milestones_df[milestones_df["milestone"].str.contains("Publication", case=False)]
            if len(pub_rows) > 0:
                pub_status = pub_rows.iloc[0]["status"]
                if pub_status != "Completed" and student["graduation_applied"] == "Yes":
                    alerts.append("⚠️ Publication requirement not yet met. Please upload your publication(s).")
        if ptype == "PhD_Research":
            milestones_df = get_student_milestones(student["student_number"], ptype)
            seminars = milestones_df[milestones_df["milestone"] == "Seminar Series (4 seminars)"]
            if len(seminars) > 0:
                sem_status = seminars.iloc[0]["status"]
                if sem_status != "Completed" and student["residency_years_used"] >= 3:
                    alerts.append("⚠️ Seminar series requirement not yet completed. Please schedule your seminars.")
        return alerts

    def get_student_alerts_and_next_action(student):
        alerts = []
        alerts.extend(get_all_warnings(student))
        alerts.extend(get_program_specific_alerts(student))
        milestones = get_student_milestones(student["student_number"], program_type)
        next_milestone = None
        for _, row in milestones.iterrows():
            if row["status"] != "Completed":
                next_milestone = row["milestone"]
                break
        if next_milestone:
            next_action = f"🎯 Your next required milestone: **{next_milestone}**"
        else:
            next_action = "🎉 All milestones completed! You are ready for graduation."
        return alerts, next_action

    alerts, next_action = get_student_alerts_and_next_action(student)
    if next_action:
        st.info(next_action)
    if alerts:
        for alert in alerts:
            if "✅" not in alert:
                st.error(alert)
    else:
        st.success("✅ All requirements are satisfied. No pending actions.")

    st.markdown("---")

    tab_labels = ["👤 Student Info", "📚 Coursework", "📄 Plan of Study", "👥 Committee", "📌 Milestone Tracker"]
    if program_type in ["MS_Thesis", "MS_NonThesis", "PhD_Regular", "PhD_Straight"]:
        tab_labels.append("📝 Examinations")
    if program_type == "PhD_Research":
        tab_labels.append("🎤 Seminars & Publications")

    tabs = st.tabs(tab_labels)
    tab_index = 0

    with tabs[tab_index]:  # Student Info
        tab_index += 1
        col1, col2 = st.columns([1,2])
        with col1:
            pic_path = get_profile_picture_path(student["student_number"])
            if pic_path and os.path.exists(pic_path):
                st.image(pic_path, width=160, caption="Your Profile Picture")
            else:
                st.info("No profile picture")
            uploaded_pic = st.file_uploader("Upload/Update profile picture", type=["jpg","jpeg","png"], key="student_pic_tab1")
            if uploaded_pic:
                fn = save_profile_picture(student["student_number"], uploaded_pic)
                if fn:
                    df.loc[df["student_number"]==student["student_number"], "profile_pic"] = fn
                    save_data(df)
                    st.success("Profile picture updated!")
                    st.rerun()
            if st.button("🗑️ Delete picture", key="del_pic_tab1"):
                if delete_profile_picture(student["student_number"]):
                    df.loc[df["student_number"]==student["student_number"], "profile_pic"] = ""
                    save_data(df)
                    st.success("Picture deleted.")
                    st.rerun()
        with col2:
            st.markdown(f"**Student Number:** {student['student_number']}")
            st.markdown(f"**Full Name:** {student['name']}")
            st.markdown(f"**Program:** {student['program']}")
            st.markdown(f"**Adviser:** {student['advisor']}")
            st.markdown(f"**Admitted Year:** {format_ay(student['ay_start'], student['semester'])}")

    with tabs[tab_index]:  # Coursework (new top-level AY/Semester selection + Add Semester button)
        tab_index += 1
        st.subheader("📚 Your Academic Record")

        # Top-level selection for AY and Semester (horizontal layout)
        st.markdown("### Add a New Semester")
        col_top1, col_top2, col_top3 = st.columns([2, 2, 1])
        with col_top1:
            new_ay = st.selectbox("Academic Year", ACADEMIC_YEARS, key="new_sem_ay")
        with col_top2:
            new_semester = st.selectbox("Semester", SEMESTERS, key="new_sem_sem")
        with col_top3:
            st.write("")  # vertical alignment
            add_sem_btn = st.button("📌 Add Semester", use_container_width=True)
        if add_sem_btn:
            # Check if semester already exists
            semesters_df = get_student_semesters(student["student_number"])
            if ((semesters_df["academic_year"] == new_ay) & (semesters_df["semester"] == new_semester)).any():
                st.warning(f"Semester {new_ay} {new_semester} already exists.")
            else:
                add_semester_record(student["student_number"], new_ay, new_semester, [])
                st.success(f"Created new semester: {new_ay} {new_semester}")
                st.rerun()

        st.markdown("---")
        st.subheader("Existing Semesters")
        semesters = get_student_semesters(student["student_number"])
        if semesters.empty:
            st.info("No semesters yet. Use the form above to add your first semester.")
        else:
            for _, sem_row in semesters.iterrows():
                render_semester_block_student(student["student_number"], sem_row)

        st.markdown("---")
        st.subheader("📊 Cumulative Summary")
        total_taken = student["total_units_taken"]
        total_required = student["total_units_required"]
        remaining = max(0, total_required - total_taken)
        cum_gwa = student["gwa"]
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Units Taken", total_taken)
        with col2:
            st.metric("Required Units", total_required)
        with col3:
            st.metric("Remaining Units", remaining)
        with col4:
            st.metric("Cumulative GWA", f"{cum_gwa:.2f}")

    # Rest of the tabs (Plan of Study, Committee, Milestone Tracker, etc.) unchanged
    with tabs[tab_index]:  # Plan of Study
        tab_index += 1
        st.subheader("📄 Plan of Study (POS)")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Status:** {student['pos_status']}")
            if student["pos_submitted_date"]:
                st.markdown(f"**Submitted:** {student['pos_submitted_date']}")
            if student["pos_approved_date"]:
                st.markdown(f"**Approved:** {student['pos_approved_date']}")
        with col2:
            pos_file = student["pos_file"]
            if pd.notna(pos_file) and os.path.exists(pos_file):
                st.markdown("**Current POS File:**")
                if pos_file.lower().endswith(('.png','.jpg','.jpeg','.gif')):
                    st.image(pos_file, width=200)
                else:
                    st.write(f"📎 {os.path.basename(pos_file)}")
            uploaded_pos = st.file_uploader("Upload or update Plan of Study (PDF/image)", type=["pdf","png","jpg","jpeg"])
            if uploaded_pos:
                def save_pos_file(sn, col, uf):
                    student_folder = os.path.join(UPLOAD_FOLDER, sn)
                    if not os.path.exists(student_folder):
                        os.makedirs(student_folder)
                    ext = uf.name.split('.')[-1].lower()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{col}_{timestamp}.{ext}"
                    filepath = os.path.join(student_folder, filename)
                    with open(filepath, "wb") as f:
                        f.write(uf.getbuffer())
                    return filepath
                filepath = save_pos_file(student["student_number"], "pos_file", uploaded_pos)
                if filepath:
                    if not student["pos_submitted_date"]:
                        df.loc[df["student_number"] == student["student_number"], "pos_submitted_date"] = datetime.now().strftime("%Y-%m-%d")
                        save_data(df)
                    df.loc[df["student_number"] == student["student_number"], "pos_file"] = filepath
                    save_data(df)
                    st.success("POS file uploaded. Staff will review.")
                    st.rerun()

    with tabs[tab_index]:  # Committee
        tab_index += 1
        committee_title = get_committee_title(student["program"])
        st.subheader(f"👥 {committee_title} (Read-only)")
        members = parse_committee_members(student.get("committee_members_structured", ""))
        if members:
            for m in members:
                st.markdown(f"• **{m['name']}** – *{m['role']}*")
            if student.get("committee_approval_date"):
                st.caption(f"Approved on: {student['committee_approval_date']}")
        else:
            st.info("No committee members assigned yet.")

    with tabs[tab_index]:  # Milestone Tracker
        tab_index += 1
        st.subheader("🎯 Milestone Tracker")
        milestones_df = get_student_milestones(student["student_number"], program_type)
        for idx, row in milestones_df.iterrows():
            with st.container():
                cols = st.columns([2, 1.5, 1.5, 2])
                with cols[0]:
                    st.markdown(f"**{row['milestone']}**")
                with cols[1]:
                    status = st.selectbox(
                        "Status",
                        options=["Not Started", "In Progress", "Completed"],
                        index=["Not Started", "In Progress", "Completed"].index(row["status"]),
                        key=f"status_{student['student_number']}_{idx}"
                    )
                with cols[2]:
                    date_val = st.text_input("Date (YYYY-MM-DD)", value=row["date"] if pd.notna(row["date"]) else "", key=f"date_{student['student_number']}_{idx}")
                with cols[3]:
                    uploaded_file = st.file_uploader("Upload Proof", type=["pdf","png","jpg","jpeg","doc","docx"], key=f"file_{student['student_number']}_{idx}")
                    if uploaded_file:
                        file_path = save_student_milestone_file(student["student_number"], row["milestone"], uploaded_file)
                        if file_path:
                            update_milestone(student["student_number"], row["milestone"], status, date_val, file_path, "")
                            st.success("File uploaded!")
                            st.rerun()
                if st.button("Update", key=f"update_{student['student_number']}_{idx}"):
                    update_milestone(student["student_number"], row["milestone"], status, date_val, None, "")
                    st.success(f"Milestone '{row['milestone']}' updated!")
                    st.rerun()
                st.markdown("---")

    # Thesis/Dissertation tab (if applicable)
    if program_type in ["MS_Thesis", "PhD_Regular", "PhD_Straight", "PhD_Research"] and tab_index < len(tabs):
        with tabs[tab_index]:
            tab_index += 1
            st.subheader("📖 Thesis / Dissertation Progress")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Status:** {student['thesis_status']}")
                st.markdown(f"**Units taken:** {student['thesis_units_taken']} / {student['thesis_units_limit']}")
                st.markdown(f"**Outline approval:** {student['thesis_outline_approved']}")
                if student["thesis_outline_approved_date"]:
                    st.markdown(f"**Outline approved:** {student['thesis_outline_approved_date']}")
            with col2:
                outline_file = student["thesis_outline_file"]
                if pd.notna(outline_file) and os.path.exists(outline_file):
                    st.markdown("**Outline:**")
                    if outline_file.lower().endswith(('.png','.jpg','.jpeg','.gif')):
                        st.image(outline_file, width=150)
                    else:
                        st.write(f"📎 {os.path.basename(outline_file)}")
                uploaded_outline = st.file_uploader("Upload outline", type=["pdf","png","jpg","jpeg","doc","docx"], key="outline_file")
                if uploaded_outline:
                    student_folder = os.path.join(UPLOAD_FOLDER, student["student_number"])
                    if not os.path.exists(student_folder):
                        os.makedirs(student_folder)
                    ext = uploaded_outline.name.split('.')[-1].lower()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"thesis_outline_file_{timestamp}.{ext}"
                    filepath = os.path.join(student_folder, filename)
                    with open(filepath, "wb") as f:
                        f.write(uploaded_outline.getbuffer())
                    df.loc[df["student_number"] == student["student_number"], "thesis_outline_file"] = filepath
                    save_data(df)
                    st.success("Outline uploaded.")
                    st.rerun()
                draft_file = student["thesis_draft_file"]
                if pd.notna(draft_file) and os.path.exists(draft_file):
                    st.markdown("**Draft:**")
                    st.write(f"📎 {os.path.basename(draft_file)}")
                uploaded_draft = st.file_uploader("Upload draft", type=["pdf","doc","docx"], key="draft_file")
                if uploaded_draft:
                    student_folder = os.path.join(UPLOAD_FOLDER, student["student_number"])
                    ext = uploaded_draft.name.split('.')[-1].lower()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"thesis_draft_file_{timestamp}.{ext}"
                    filepath = os.path.join(student_folder, filename)
                    with open(filepath, "wb") as f:
                        f.write(uploaded_draft.getbuffer())
                    df.loc[df["student_number"] == student["student_number"], "thesis_draft_file"] = filepath
                    save_data(df)
                    st.success("Draft uploaded.")
                    st.rerun()
                manuscript_file = student["thesis_manuscript_file"]
                if pd.notna(manuscript_file) and os.path.exists(manuscript_file):
                    st.markdown("**Final manuscript:**")
                    st.write(f"📎 {os.path.basename(manuscript_file)}")
                uploaded_manuscript = st.file_uploader("Upload final manuscript", type=["pdf"], key="manuscript_file")
                if uploaded_manuscript:
                    student_folder = os.path.join(UPLOAD_FOLDER, student["student_number"])
                    filename = f"thesis_manuscript_file_{timestamp}.{ext}"
                    filepath = os.path.join(student_folder, filename)
                    with open(filepath, "wb") as f:
                        f.write(uploaded_manuscript.getbuffer())
                    df.loc[df["student_number"] == student["student_number"], "thesis_manuscript_file"] = filepath
                    save_data(df)
                    st.success("Manuscript uploaded.")
                    st.rerun()
            st.caption(get_thesis_pattern_description(student["program"]))

    # Examinations tab
    if program_type in ["MS_Thesis", "MS_NonThesis", "PhD_Regular", "PhD_Straight"] and tab_index < len(tabs):
        with tabs[tab_index]:
            tab_index += 1
            st.subheader("📝 Examination Status")
            if program_type.startswith("MS"):
                st.markdown("##### General Exam")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Status:** {student['general_exam_status']}")
                    if student["general_exam_passed_date"]:
                        st.markdown(f"**Date passed:** {student['general_exam_passed_date']}")
                with col2:
                    g_file = student["general_exam_file"]
                    if pd.notna(g_file) and os.path.exists(g_file):
                        if g_file.lower().endswith(('.png','.jpg','.jpeg','.gif')):
                            st.image(g_file, width=150)
                        else:
                            st.write(f"📎 {os.path.basename(g_file)}")
                    uploaded = st.file_uploader("Upload proof (result slip)", type=["pdf","png","jpg","jpeg"], key="gen_file")
                    if uploaded:
                        student_folder = os.path.join(UPLOAD_FOLDER, student["student_number"])
                        if not os.path.exists(student_folder):
                            os.makedirs(student_folder)
                        ext = uploaded.name.split('.')[-1].lower()
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"general_exam_file_{timestamp}.{ext}"
                        filepath = os.path.join(student_folder, filename)
                        with open(filepath, "wb") as f:
                            f.write(uploaded.getbuffer())
                        df.loc[df["student_number"] == student["student_number"], "general_exam_file"] = filepath
                        save_data(df)
                        st.success("File uploaded.")
                        st.rerun()
            else:
                st.markdown("##### Qualifying Exam")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Status:** {student['qualifying_exam_status']}")
                    if student["qualifying_exam_passed_date"]:
                        st.markdown(f"**Date passed:** {student['qualifying_exam_passed_date']}")
                with col2:
                    q_file = student["qualifying_exam_file"]
                    if pd.notna(q_file) and os.path.exists(q_file):
                        if q_file.lower().endswith(('.png','.jpg','.jpeg','.gif')):
                            st.image(q_file, width=150)
                        else:
                            st.write(f"📎 {os.path.basename(q_file)}")
                    uploaded = st.file_uploader("Upload proof (result slip)", type=["pdf","png","jpg","jpeg"], key="qual_file")
                    if uploaded:
                        student_folder = os.path.join(UPLOAD_FOLDER, student["student_number"])
                        if not os.path.exists(student_folder):
                            os.makedirs(student_folder)
                        ext = uploaded.name.split('.')[-1].lower()
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"qualifying_exam_file_{timestamp}.{ext}"
                        filepath = os.path.join(student_folder, filename)
                        with open(filepath, "wb") as f:
                            f.write(uploaded.getbuffer())
                        df.loc[df["student_number"] == student["student_number"], "qualifying_exam_file"] = filepath
                        save_data(df)
                        st.success("File uploaded.")
                        st.rerun()
                st.markdown("---")
                st.markdown("##### Written Comprehensive Exam")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Status:** {student['written_comprehensive_status']}")
                    if student["written_comprehensive_passed_date"]:
                        st.markdown(f"**Date passed:** {student['written_comprehensive_passed_date']}")
                with col2:
                    w_file = student["written_comprehensive_file"]
                    if pd.notna(w_file) and os.path.exists(w_file):
                        if w_file.lower().endswith(('.png','.jpg','.jpeg','.gif')):
                            st.image(w_file, width=150)
                        else:
                            st.write(f"📎 {os.path.basename(w_file)}")
                    uploaded = st.file_uploader("Upload proof", type=["pdf","png","jpg","jpeg"], key="written_file")
                    if uploaded:
                        student_folder = os.path.join(UPLOAD_FOLDER, student["student_number"])
                        ext = uploaded.name.split('.')[-1].lower()
                        filename = f"written_comprehensive_file_{timestamp}.{ext}"
                        filepath = os.path.join(student_folder, filename)
                        with open(filepath, "wb") as f:
                            f.write(uploaded.getbuffer())
                        df.loc[df["student_number"] == student["student_number"], "written_comprehensive_file"] = filepath
                        save_data(df)
                        st.success("File uploaded.")
                        st.rerun()
                st.markdown("---")
                st.markdown("##### Oral Comprehensive Exam")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Status:** {student['oral_comprehensive_status']}")
                    if student["oral_comprehensive_passed_date"]:
                        st.markdown(f"**Date passed:** {student['oral_comprehensive_passed_date']}")
                with col2:
                    o_file = student["oral_comprehensive_file"]
                    if pd.notna(o_file) and os.path.exists(o_file):
                        if o_file.lower().endswith(('.png','.jpg','.jpeg','.gif')):
                            st.image(o_file, width=150)
                        else:
                            st.write(f"📎 {os.path.basename(o_file)}")
                    uploaded = st.file_uploader("Upload proof", type=["pdf","png","jpg","jpeg"], key="oral_file")
                    if uploaded:
                        student_folder = os.path.join(UPLOAD_FOLDER, student["student_number"])
                        ext = uploaded.name.split('.')[-1].lower()
                        filename = f"oral_comprehensive_file_{timestamp}.{ext}"
                        filepath = os.path.join(student_folder, filename)
                        with open(filepath, "wb") as f:
                            f.write(uploaded.getbuffer())
                        df.loc[df["student_number"] == student["student_number"], "oral_comprehensive_file"] = filepath
                        save_data(df)
                        st.success("File uploaded.")
                        st.rerun()

    # PhD Research additional tab
    if program_type == "PhD_Research" and tab_index < len(tabs):
        with tabs[tab_index]:
            st.subheader("🎤 Seminars & Publications")
            st.info("This section tracks your seminar series and publication requirements.")
            milestones_df = get_student_milestones(student["student_number"], program_type)
            for _, row in milestones_df.iterrows():
                if "Seminar" in row["milestone"] or "Publication" in row["milestone"]:
                    st.markdown(f"**{row['milestone']}** – Status: **{row['status']}**")
                    if pd.notna(row["date"]) and row["date"]:
                        st.caption(f"Date: {row['date']}")
                    if pd.notna(row["file_path"]) and row["file_path"]:
                        st.write(f"📎 Proof: {os.path.basename(row['file_path'])}")
                    st.markdown("---")

    st.caption("For corrections, contact your adviser or SESAM Staff.")

# ==================== FOOTER ====================
st.markdown("---")
st.caption("SESAM Graduate Lifecycle Management v9.0 | Per-Semester Blocks | Editable Subjects | Document Validation")
