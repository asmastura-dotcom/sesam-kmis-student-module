"""
SESAM KMIS - Graduate Student Lifecycle Management System
Version: 40.0 | Enhanced Faculty Adviser Dashboard (analytics, filtering, milestone tracking)
Roles: Student (submit), Adviser (verify), Staff (admin & view-only)
"""

import streamlit as st
import pandas as pd
import os
import json
from datetime import date, datetime, timedelta
import smtplib
from email.message import EmailMessage
import base64
import plotly.express as px
import plotly.graph_objects as go

# ==================== EMAIL CONFIGURATION ====================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "kmis@sesam.uplb.edu.ph"
SMTP_PASSWORD = "your_app_password_here"

def send_welcome_email(student_number, personal_email, name):
    if not personal_email or personal_email.strip() == "":
        return False
    try:
        msg = EmailMessage()
        msg["Subject"] = "Welcome to SESAM KMIS – Your Account Has Been Created"
        msg["From"] = SMTP_USER
        msg["To"] = personal_email
        msg.set_content(f"Dear {name},\n\nYour SESAM KMIS account has been created.\nLogin credentials:\n    Username: {student_number}\n    Temporary Password: {student_number}\n\nPlease change your password after first login.\n\nRegards,\nSESAM KMIS Administrator")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False

# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="SESAM KMIS", page_icon="🎓", layout="wide")

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .status-badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.7rem; font-weight: 500; }
    .status-not-started { background-color: #e9ecef; color: #495057; }
    .status-pending { background-color: #fff3cd; color: #856404; }
    .status-approved { background-color: #d4edda; color: #155724; }
    .status-rejected { background-color: #f8d7da; color: #721c24; }
    .warning-banner { background-color: #ffcc00; color: #333; padding: 0.5rem; border-radius: 8px; margin: 0.5rem 0; font-weight: bold; }
    .danger-banner { background-color: #dc3545; color: white; padding: 0.5rem; border-radius: 8px; margin: 0.5rem 0; font-weight: bold; }
    div[data-testid="stExpander"] { border: 1px solid #e2e8f0; border-radius: 16px; margin-bottom: 1rem; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
    .info-card { background: #ffffff; border-radius: 16px; padding: 1rem; margin-bottom: 1rem; border: 1px solid #e9ecef; box-shadow: 0 2px 6px rgba(0,0,0,0.02); }
    .committee-card { background: white; border-radius: 24px; padding: 1.5rem; box-shadow: 0 8px 20px rgba(0,0,0,0.05); border: 1px solid #eef2ff; }
    .committee-title { font-size: 1.5rem; font-weight: 600; color: #1f3b4c; margin-bottom: 0.25rem; }
    .committee-subtitle { color: #5b6e8c; font-size: 0.9rem; margin-bottom: 1.5rem; border-left: 3px solid #2c5a6e; padding-left: 0.75rem; }
    .stButton > button { border-radius: 30px !important; font-weight: 500 !important; transition: all 0.2s ease; }
    .stButton > button:first-child { background-color: #2c5a6e !important; color: white !important; border: none !important; }
    .kpi-card {
        background: white;
        border-radius: 20px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border-left: 4px solid #2c5a6e;
    }
    .kpi-number {
        font-size: 2rem;
        font-weight: 700;
        color: #1f3b4c;
    }
    .kpi-label {
        font-size: 0.8rem;
        color: #5b6e8c;
    }
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================
for key in ["logged_in", "username", "role", "display_name", "consent_given",
            "staff_selected_student", "adviser_selected_student", "staff_show_update",
            "show_registration", "reg_success", "profile_update_success",
            "staff_dashboard_tab", "student_list_page"]:
    if key not in st.session_state:
        st.session_state[key] = 0 if key == "student_list_page" else (False if "logged_in" not in key else None if "selected" in key else False)

# ==================== DATA PRIVACY CONSENT ====================
CONSENT_LOG_FILE = "consent_log.csv"
def log_consent(username, role, display_name):
    df = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username, role, display_name, "unknown"]],
                      columns=["timestamp","username","role","display_name","ip_address"])
    if os.path.exists(CONSENT_LOG_FILE):
        df = pd.concat([pd.read_csv(CONSENT_LOG_FILE), df], ignore_index=True)
    df.to_csv(CONSENT_LOG_FILE, index=False)

def show_consent_form():
    st.markdown("### 📜 Data Privacy Consent\nIn compliance with RA 10173, SESAM KMIS collects personal data for academic monitoring.")
    if st.checkbox("I have read and agree to the Data Privacy Policy"):
        if st.button("✅ I Consent"):
            st.session_state.consent_given = True
            log_consent(st.session_state.username, st.session_state.role, st.session_state.display_name)
            st.rerun()

# ==================== USER AUTH ====================
USERS = {
    "staff1": {"password": "admin123", "role": "SESAM Staff", "display_name": "SESAM Administrator"},
    "adviser1": {"password": "adv123", "role": "Faculty Adviser", "display_name": "Dr. Jane Smith"},
    "adviser2": {"password": "adv456", "role": "Faculty Adviser", "display_name": "Dr. Maria Santos"},
}

# ==================== PROGRAM & UNIT REQUIREMENTS ====================
PROGRAMS = ["MS Environmental Science", "PhD Environmental Science", "PhD Environmental Diplomacy and Negotiations"]
SPECIALIZATIONS = ["None", "Ecosystems Management", "Environmental Chemistry", "Climate Change", "Environmental Policy"]

def get_program_type(program_name):
    if program_name == "MS Environmental Science":
        return "MS_Thesis"
    elif program_name == "PhD Environmental Science":
        return "PhD_Regular"
    elif program_name == "PhD Environmental Diplomacy and Negotiations":
        return "PhD_Research"
    return "MS_Thesis"

def is_master_program(program): return get_program_type(program).startswith("MS")
def is_phd_program(program): return get_program_type(program).startswith("PhD")

def get_required_units(program, prior_ms_graduate=False):
    if program == "MS Environmental Science":
        return 32
    elif program == "PhD Environmental Science":
        return 37 if prior_ms_graduate else 50
    elif program == "PhD Environmental Diplomacy and Negotiations":
        return 50
    else:
        return 24 if is_master_program(program) else 50

# ==================== MILESTONE DEFINITIONS ====================
MILESTONE_DEFS = {
    "MS_Thesis": [
        "Guidance Committee Members",
        "Plan of Study (POS)",
        "General / Comprehensive Examination - Passed",
        "Thesis Proposal / Outline – Approved",
        "Thesis Final Examination / Defense – Passed",
        "Final Manuscript Submission",
    ],
    "PhD_Regular": [
        "Advisory Committee Formation",
        "Qualifying Examination",
        "Plan of Study (POS)",
        "General / Comprehensive Examination - Passed",
        "Dissertation Proposal / Outline - Approved",
        "Pre‑dissertation Seminar / Colloquium – Completed",
        "Dissertation Final Defense – Passed",
        "Final Manuscript Submission",
    ],
    "PhD_Research": [
        "Supervisory Committee Formation",
        "Plan of Research",
        "Seminar Series (3 seminars)",
        "Research Progress Review",
        "Thesis Outline",
        "Publication (3 articles)",
        "Final Oral Examination",
        "Thesis Manuscript Submission",
    ]
}

# ==================== HELPER FUNCTIONS ====================
SEMESTERS = ["1st Sem", "2nd Sem", "Summer"]
current_year = date.today().year
ACADEMIC_YEARS = [f"{year}-{year+1}" for year in range(current_year-5, current_year+6)]
GRADE_OPTIONS = ["1.00","1.25","1.50","1.75","2.00","2.25","2.50","2.75","3.00","4.00","INC","DRP","5.00","P","IP"]
SEMESTER_STATUS_OPTIONS = ["Regular","Off-Sem","On Leave","Shifted Program","Transferred"]

FACULTY_CSV = "faculty.csv"

def load_faculty_list():
    if os.path.exists(FACULTY_CSV):
        df = pd.read_csv(FACULTY_CSV)
        return df["name"].dropna().tolist()
    else:
        default = [
            "Dr. Jane Smith",
            "Dr. Maria Santos",
            "Dr. Decibel V. Faustino-Eslava",
            "Dr. Jessica D. Villanueva-Peyraube",
            "Dr. Patricia Ann J. Sanchez",
            "For. Sofia A. Alaira",
            "Dr. Yusuf A. Sucol",
            "Dr. Rico C. Ancog",
            "Dr. Eduardo C. Calzeta",
            "Dr. Janice B. Sevilla Nastor",
            "Dr. Maria Theresa M. Rodriguez",
            "Dr. Roberto G. Reyes"
        ]
        df = pd.DataFrame(default, columns=["name"])
        df.to_csv(FACULTY_CSV, index=False)
        return default

FACULTY_NAMES = load_faculty_list()

def get_thesis_limit_from_program(program):
    ptype = get_program_type(program)
    return 12 if ptype in ["PhD_Regular","PhD_Research"] else (6 if ptype == "MS_Thesis" else 0)

def get_max_thesis_extension_units(program):
    return 3 if is_master_program(program) else 6

def get_residency_max_from_program(program):
    return 5 if is_master_program(program) else 7

def format_ay(ay_start, semester):
    return f"A.Y. {ay_start}-{ay_start+1} ({semester})"

def get_semester_structure(program):
    if is_master_program(program):
        return (4, 1, 5)
    else:
        return (6, 2, 8)

def generate_timeline(start_ay, start_sem, program):
    sem_order = ["1st Sem","2nd Sem","Summer"]
    total_terms = get_semester_structure(program)[2]
    timeline = []
    ay = start_ay
    start_idx = sem_order.index(start_sem)
    term_count = 0
    while term_count < total_terms:
        for i in range(start_idx, len(sem_order)):
            if term_count >= total_terms:
                break
            sem = sem_order[i]
            timeline.append((f"{ay}-{ay+1}", sem))
            term_count += 1
        start_idx = 0
        ay += 1
    return timeline

# ==================== DATA FILE PATHS ====================
DATA_FILE = "students.csv"
SEMESTER_FILE = "semester_records.csv"
MILESTONE_FILE = "milestone_tracking.csv"
UPLOAD_FOLDER = "student_uploads"
PROFILE_PIC_FOLDER = "profile_pics"
COMMITTEE_VERSIONS_FILE = "committee_versions.csv"
COMMITTEE_MEMBERS_FILE = "committee_members.csv"
POS_VERSIONS_FILE = "pos_versions.csv"

for folder in [UPLOAD_FOLDER, PROFILE_PIC_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# ==================== PDF EMBEDDING ====================
def embed_pdf(pdf_path):
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.warning("PDF file not found.")

# ==================== COMMITTEE VERSION CONTROL ====================
def init_committee_tables():
    if not os.path.exists(COMMITTEE_VERSIONS_FILE):
        pd.DataFrame(columns=["version_id","student_number","version_number","gs_pdf_path",
                              "verification_status","verification_date","verified_by","remarks","is_active","created_at"])\
          .to_csv(COMMITTEE_VERSIONS_FILE, index=False)
    if not os.path.exists(COMMITTEE_MEMBERS_FILE):
        pd.DataFrame(columns=["member_id","version_id","role","name"]).to_csv(COMMITTEE_MEMBERS_FILE, index=False)

def get_next_version_id():
    df = pd.read_csv(COMMITTEE_VERSIONS_FILE)
    return 1 if df.empty else df["version_id"].max()+1

def get_next_member_id():
    df = pd.read_csv(COMMITTEE_MEMBERS_FILE)
    return 1 if df.empty else df["member_id"].max()+1

def save_committee_version_enhanced(student_number, pdf_file, members_dict, is_phd=False):
    if not is_phd:
        if not members_dict.get('chair', '').strip():
            return False, "Missing required role: Chair"
        if not members_dict.get('member_major', '').strip():
            return False, "Missing required role: Major Member"
        if not members_dict.get('member_cognate1', '').strip():
            return False, "Missing required role: Cognate Member"
    else:
        if not members_dict.get('chair', '').strip():
            return False, "Missing required role: Chair"
        if not members_dict.get('member_major', '').strip():
            return False, "Missing required role: Major Member"
        if not members_dict.get('member_cognate1', '').strip():
            return False, "Missing required role: Cognate Member"

    df_ver = pd.read_csv(COMMITTEE_VERSIONS_FILE)
    pending = df_ver[(df_ver["student_number"]==student_number) & (df_ver["verification_status"]=="Pending")]
    if not pending.empty:
        return False, "You already have a pending committee version."

    student_versions = df_ver[df_ver["student_number"]==student_number]
    version_number = student_versions["version_number"].max()+1 if not student_versions.empty else 1

    folder = os.path.join(UPLOAD_FOLDER, student_number, "committee")
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(folder, f"committee_v{version_number}_{timestamp}.pdf")
    with open(filepath, "wb") as f:
        f.write(pdf_file.getbuffer())

    version_id = get_next_version_id()
    new_ver = pd.DataFrame([{
        "version_id": version_id,
        "student_number": student_number,
        "version_number": version_number,
        "gs_pdf_path": filepath,
        "verification_status": "Pending",
        "verification_date": "",
        "verified_by": "",
        "remarks": "",
        "is_active": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])
    df_ver = pd.concat([df_ver, new_ver], ignore_index=True)
    df_ver.to_csv(COMMITTEE_VERSIONS_FILE, index=False)

    df_mem = pd.read_csv(COMMITTEE_MEMBERS_FILE)
    for role, name in members_dict.items():
        if name and name.strip():
            new_mem = pd.DataFrame([{
                "member_id": get_next_member_id(),
                "version_id": version_id,
                "role": role.replace('_', ' ').title(),
                "name": name.strip()
            }])
            df_mem = pd.concat([df_mem, new_mem], ignore_index=True)
    df_mem.to_csv(COMMITTEE_MEMBERS_FILE, index=False)

    return True, f"Committee version {version_number} submitted for adviser verification."

def get_committee_versions(student_number):
    df = pd.read_csv(COMMITTEE_VERSIONS_FILE)
    return df[df["student_number"]==student_number].sort_values("version_number", ascending=False)

def get_committee_members_for_version(version_id):
    return pd.read_csv(COMMITTEE_MEMBERS_FILE)[pd.read_csv(COMMITTEE_MEMBERS_FILE)["version_id"]==version_id][["role","name"]]

def get_pending_committee_version(student_number):
    df = pd.read_csv(COMMITTEE_VERSIONS_FILE)
    pending = df[(df["student_number"]==student_number) & (df["verification_status"]=="Pending")]
    if pending.empty:
        return None
    return pending.iloc[0].to_dict()

def get_active_committee_version(student_number):
    df = pd.read_csv(COMMITTEE_VERSIONS_FILE)
    active = df[(df["student_number"]==student_number) & (df["is_active"]==True)]
    if active.empty:
        return None
    return active.iloc[0].to_dict()

def verify_committee_version(version_id, status, adviser_name, remarks):
    if status not in ["Verified Correct","Mismatch – Requires Correction"]:
        return False, "Invalid status."
    df_ver = pd.read_csv(COMMITTEE_VERSIONS_FILE)
    mask = df_ver["version_id"]==version_id
    if not mask.any():
        return False, "Version not found."
    row = df_ver[mask].iloc[0]
    if row["verification_status"] != "Pending":
        return False, f"Version already {row['verification_status']}."
    df_ver.loc[mask, "verification_status"] = status
    df_ver.loc[mask, "verification_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df_ver.loc[mask, "verified_by"] = adviser_name
    df_ver.loc[mask, "remarks"] = remarks
    if status == "Verified Correct":
        student_number = row["student_number"]
        df_ver.loc[df_ver["student_number"]==student_number, "is_active"] = False
        df_ver.loc[mask, "is_active"] = True
        members = get_committee_members_for_version(version_id)
        chair_row = members[members["role"]=="Chair"]
        if not chair_row.empty:
            chair_name = chair_row.iloc[0]["name"]
            df_students = load_data()
            idx = df_students[df_students["student_number"]==student_number].index
            if len(idx)>0:
                df_students.loc[idx, "advisor"] = chair_name
                save_data(df_students)
        prog_type = get_program_type(load_data().loc[load_data()["student_number"]==student_number].iloc[0]["program"])
        milestone_name = "Guidance Committee Members" if prog_type=="MS_Thesis" else ("Advisory Committee Formation" if prog_type=="PhD_Regular" else "Supervisory Committee Formation")
        update_milestone(student_number, milestone_name, "Approved", date.today().strftime("%Y-%m-%d"), "", f"Committee verified by {adviser_name}", adviser_name)
    df_ver.to_csv(COMMITTEE_VERSIONS_FILE, index=False)
    return True, f"Committee version marked as {status}."

def is_committee_approved(student_number):
    active = get_active_committee_version(student_number)
    return active is not None and active["verification_status"]=="Verified Correct"

def check_committee_approval(student_number, semester_index):
    if semester_index >= 1 and not is_committee_approved(student_number):
        return False, "Your Guidance/Advisory Committee must be approved before you can enroll in the second semester."
    return True, ""

# ==================== POS VERSION CONTROL ====================
def init_pos_tables():
    if not os.path.exists(POS_VERSIONS_FILE):
        pd.DataFrame(columns=["version_id","student_number","version_number","pdf_path","verification_status",
                              "verification_date","verified_by","remarks","is_active","created_at"])\
          .to_csv(POS_VERSIONS_FILE, index=False)

def get_next_pos_version_id():
    df = pd.read_csv(POS_VERSIONS_FILE)
    return 1 if df.empty else df["version_id"].max()+1

def save_pos_version(student_number, pdf_file):
    df = pd.read_csv(POS_VERSIONS_FILE)
    pending = df[(df["student_number"]==student_number) & (df["verification_status"]=="Pending")]
    if not pending.empty:
        return False, "You already have a pending POS version."
    student_versions = df[df["student_number"]==student_number]
    version_number = student_versions["version_number"].max()+1 if not student_versions.empty else 1
    folder = os.path.join(UPLOAD_FOLDER, student_number, "pos")
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(folder, f"pos_v{version_number}_{timestamp}.pdf")
    with open(filepath, "wb") as f:
        f.write(pdf_file.getbuffer())
    version_id = get_next_pos_version_id()
    new_row = pd.DataFrame([{
        "version_id": version_id,
        "student_number": student_number,
        "version_number": version_number,
        "pdf_path": filepath,
        "verification_status": "Pending",
        "verification_date": "",
        "verified_by": "",
        "remarks": "",
        "is_active": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(POS_VERSIONS_FILE, index=False)
    return True, f"POS version {version_number} submitted for adviser verification."

def get_pos_versions(student_number):
    df = pd.read_csv(POS_VERSIONS_FILE)
    return df[df["student_number"]==student_number].sort_values("version_number", ascending=False)

def get_pending_pos_version(student_number):
    df = pd.read_csv(POS_VERSIONS_FILE)
    pending = df[(df["student_number"]==student_number) & (df["verification_status"]=="Pending")]
    if pending.empty:
        return None
    return pending.iloc[0].to_dict()

def get_active_pos_version(student_number):
    df = pd.read_csv(POS_VERSIONS_FILE)
    active = df[(df["student_number"]==student_number) & (df["is_active"]==True)]
    if active.empty:
        return None
    return active.iloc[0].to_dict()

def verify_pos_version(version_id, status, adviser_name, remarks):
    if status not in ["Verified Correct","Mismatch – Requires Correction"]:
        return False, "Invalid status."
    df = pd.read_csv(POS_VERSIONS_FILE)
    mask = df["version_id"]==version_id
    if not mask.any():
        return False, "Version not found."
    row = df[mask].iloc[0]
    if row["verification_status"] != "Pending":
        return False, f"Version already {row['verification_status']}."
    df.loc[mask, "verification_status"] = status
    df.loc[mask, "verification_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df.loc[mask, "verified_by"] = adviser_name
    df.loc[mask, "remarks"] = remarks
    if status == "Verified Correct":
        student_number = row["student_number"]
        df.loc[df["student_number"]==student_number, "is_active"] = False
        df.loc[mask, "is_active"] = True
        df_students = load_data()
        idx = df_students[df_students["student_number"]==student_number].index
        if len(idx)>0:
            df_students.loc[idx, "pos_status"] = "Approved"
            df_students.loc[idx, "pos_approval_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_data(df_students)
        update_milestone(student_number, "Plan of Study (POS)", "Approved", date.today().strftime("%Y-%m-%d"), "", f"POS verified by {adviser_name}", adviser_name)
    df.to_csv(POS_VERSIONS_FILE, index=False)
    return True, f"POS version marked as {status}."

# ==================== CORE DATA FUNCTIONS ====================
def load_data():
    expected_columns = ["student_number","password","name","last_name","first_name","middle_name","program","specialization","advisor","ay_start","semester","gwa",
                        "total_units_taken","total_units_required","thesis_units_taken","thesis_units_limit","thesis_extension_units",
                        "residency_years_used","residency_extension_years","pos_status","pos_approval_date","qualifying_exam_status",
                        "written_comprehensive_status","oral_comprehensive_status","general_exam_status","final_exam_status","final_exam_attempts",
                        "profile_pic","committee_members_structured","committee_approval_date","thesis_outline_approved","thesis_status",
                        "prior_ms_graduate","student_status","address","phone","institutional_email","personal_email","gender","civil_status",
                        "citizenship","birthdate","religion","emergency_name","emergency_relationship","emergency_country_code","emergency_phone",
                        "special_status","residency_max_years"]
    numeric_cols = ["ay_start","gwa","total_units_taken","total_units_required","thesis_units_taken","thesis_units_limit","thesis_extension_units",
                    "residency_years_used","residency_extension_years","residency_max_years","final_exam_attempts"]
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE)==0:
        df = pd.DataFrame(columns=expected_columns)
        for col in numeric_cols:
            if col in df.columns:
                df[col] = 0
        df["student_status"] = "Active"
        save_data(df)
        return df
    df = pd.read_csv(DATA_FILE, dtype=str)
    for col in expected_columns:
        if col not in df.columns:
            df[col] = 0 if col in numeric_cols else (False if col=="prior_ms_graduate" else "")
    if "student_status" not in df.columns:
        df["student_status"] = "Active"
    if "specialization" not in df.columns:
        df["specialization"] = ""
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            if col != "gwa":
                df[col] = df[col].astype(int)
    df["prior_ms_graduate"] = df["prior_ms_graduate"].astype(bool)
    for idx, row in df.iterrows():
        prog = row["program"]
        if prog and prog!="":
            df.at[idx, "residency_max_years"] = get_residency_max_from_program(prog)
            df.at[idx, "thesis_units_limit"] = get_thesis_limit_from_program(prog)
            req = get_required_units(prog, row.get("prior_ms_graduate",False))
            if req is not None:
                df.at[idx, "total_units_required"] = req
    save_data(df)
    return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def load_semester_records():
    if not os.path.exists(SEMESTER_FILE) or os.path.getsize(SEMESTER_FILE)==0:
        return pd.DataFrame(columns=["student_number","academic_year","semester","subjects_json","total_units","gwa",
                                     "doc_path","doc_upload_time","doc_status","doc_remarks","doc_validated_by",
                                     "doc_validated_time","semester_status","pos_courses","pos_approved_status"])
    df = pd.read_csv(SEMESTER_FILE, dtype=str)
    for col in ["total_units","gwa"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    for col in ["student_number","academic_year","semester","subjects_json","doc_path","doc_upload_time",
                "doc_status","doc_remarks","doc_validated_by","doc_validated_time","semester_status","pos_courses","pos_approved_status"]:
        if col not in df.columns:
            df[col] = ""
    df["subjects_json"] = df["subjects_json"].fillna("[]")
    df["semester_status"] = df.get("semester_status","Regular").fillna("Regular")
    return df

def save_semester_records(df):
    df.to_csv(SEMESTER_FILE, index=False)

def get_student_semesters(student_number):
    df = load_semester_records()
    return df[df["student_number"]==student_number].copy()

def compute_gwa_from_subjects(subjects_list):
    total_units = total_grade = 0
    for s in subjects_list:
        grade_val = s.get("grade","")
        if grade_val in ["INC","DRP","P","IP","4.00"]:
            continue
        try:
            units = float(s.get("units",0))
            grade = float(grade_val)
            total_units += units
            total_grade += units*grade
        except:
            pass
    return total_grade/total_units if total_units>0 else 0.0

# ==================== RULE FUNCTIONS ====================
def check_pos_approval(student_number, semester_index):
    if semester_index >= 1:
        active = get_active_pos_version(student_number)
        if active is None:
            return False, "Your Plan of Study (POS) must be approved before you can enroll in the second semester."
    return True, ""

def get_semester_index(student_number, ay, sem):
    df = load_data()
    student = df[df["student_number"]==student_number]
    if student.empty:
        return -1
    timeline = generate_timeline(student.iloc[0]["ay_start"], student.iloc[0]["semester"], student.iloc[0]["program"])
    for i, (t_ay, t_sem) in enumerate(timeline):
        if t_ay==ay and t_sem==sem:
            return i
    return -1

def check_thesis_units_limit(student_number, new_thesis_units):
    student = load_data().loc[load_data()["student_number"]==student_number].iloc[0]
    current = float(student["thesis_units_taken"]) if pd.notna(student["thesis_units_taken"]) else 0
    limit = get_thesis_limit_from_program(student["program"]) + student.get("thesis_extension_units",0)
    if current+new_thesis_units > limit:
        return False, f"Thesis unit limit would be exceeded. Only {limit-current} unit(s) remaining."
    return True, ""

def check_comprehensive_exam_eligibility(student_number):
    student = load_data().loc[load_data()["student_number"]==student_number].iloc[0]
    total_taken = float(student["total_units_taken"]) if pd.notna(student["total_units_taken"]) else 0
    total_required = float(student["total_units_required"]) if pd.notna(student["total_units_required"]) else 0
    gwa = float(student["gwa"]) if pd.notna(student["gwa"]) else 0
    if total_required==0:
        return False, "Program total units not configured."
    if total_taken < 0.75*total_required:
        return False, f"Insufficient coursework: {total_taken:.0f}/{total_required:.0f} units (need ≥75%)."
    if gwa==0 or gwa>2.50:
        return False, f"GWA {gwa:.2f} must be at least 2.50."
    return True, "Eligible."

def convert_expired_grades():
    semesters = load_semester_records()
    modified = False
    for idx, row in semesters.iterrows():
        try:
            subjects = json.loads(row["subjects_json"])
        except:
            continue
        sem_date = row.get("doc_upload_time","")
        if sem_date:
            try:
                sem_end = datetime.strptime(sem_date, "%Y-%m-%d %H:%M:%S")
            except:
                sem_end = datetime.now()
        else:
            sem_end = datetime.now()
        deadline = sem_end + timedelta(days=365)
        changed = False
        for subj in subjects:
            grade = subj.get("grade","")
            if grade in ["INC","4.00"] and datetime.now() > deadline:
                subj["grade"] = "5.00"
                changed = True
                modified = True
        if changed:
            semesters.at[idx, "subjects_json"] = json.dumps(subjects)
    if modified:
        save_semester_records(semesters)
        for sn in semesters["student_number"].unique():
            update_student_academic_summary(sn)

def check_residency_enforcement(student_number):
    student = load_data().loc[load_data()["student_number"]==student_number].iloc[0]
    years_used = date.today().year - student["ay_start"]
    max_years = student.get("residency_max_years",5)
    extension = student.get("residency_extension_years",0)
    if years_used > max_years+extension:
        return False, f"Residency exceeded: {years_used} > {max_years+extension} years."
    elif years_used > max_years:
        return "warning", f"Residency warning: {years_used} out of {max_years} years (+{extension} extension)."
    return True, ""

def check_residency_alert(student):
    years_used = date.today().year - student["ay_start"]
    max_years = student.get("residency_max_years",5)
    extension = student.get("residency_extension_years",0)
    if years_used > max_years+extension:
        return "exceeded", years_used, max_years+extension
    elif years_used > max_years:
        return "warning_extension", years_used, max_years+extension
    elif years_used > max_years-1:
        return "warning", years_used, max_years
    return "ok", years_used, max_years

# ==================== SEMESTER & ACADEMIC FUNCTIONS ====================
def add_semester_record(student_number, ay, sem, subjects, doc_path="", doc_upload_time="", semester_status="Regular"):
    df = load_data()
    student = df[df["student_number"] == student_number].iloc[0]
    sems = get_student_semesters(student_number)
    semester_count = len(sems)
    
    ok, msg = check_committee_approval(student_number, semester_count)
    if not ok:
        raise ValueError(msg)
    ok, msg = check_pos_approval(student_number, semester_count)
    if not ok:
        raise ValueError(msg)
    ok, msg = check_residency_enforcement(student_number)
    if isinstance(ok, bool) and not ok:
        raise ValueError(msg)
    
    thesis_units = sum(float(s.get("units",0)) for s in subjects if "thesis" in s.get("course_code","").lower() or "dissertation" in s.get("course_code","").lower())
    
    if thesis_units > 0:
        base_limit = get_thesis_limit_from_program(student["program"])
        current_regular = float(student["thesis_units_taken"]) if pd.notna(student["thesis_units_taken"]) else 0
        current_ext = int(student.get("thesis_extension_units", 0))
        max_ext = get_max_thesis_extension_units(student["program"])
        
        if current_regular + thesis_units > base_limit:
            needed_ext = (current_regular + thesis_units) - base_limit
            if current_ext + needed_ext <= max_ext:
                new_ext = current_ext + needed_ext
                df_students = load_data()
                df_students.loc[df_students["student_number"] == student_number, "thesis_extension_units"] = new_ext
                save_data(df_students)
                raise ValueError(f"⚠️ Auto‑granted {needed_ext} extension unit(s). You now have {new_ext}/{max_ext} extension units used. Please re‑submit your subjects to save.")
            else:
                raise ValueError(f"Thesis extension quota exhausted (max {max_ext} units). You need {needed_ext} more but only {max_ext - current_ext} left.")
        else:
            ok, msg = check_thesis_units_limit(student_number, thesis_units)
            if not ok:
                raise ValueError(msg)
    
    df_sem = load_semester_records()
    gwa = compute_gwa_from_subjects(subjects)
    total_units = sum(float(s.get("units",0)) for s in subjects)
    new = pd.DataFrame([{
        "student_number": student_number,
        "academic_year": ay,
        "semester": sem,
        "subjects_json": json.dumps(subjects),
        "total_units": total_units,
        "gwa": gwa,
        "doc_path": str(doc_path),
        "doc_upload_time": str(doc_upload_time),
        "doc_status": "Pending" if doc_path else "",
        "doc_remarks": "",
        "doc_validated_by": "",
        "doc_validated_time": "",
        "semester_status": semester_status,
        "pos_courses": "",
        "pos_approved_status": ""
    }])
    df_sem = pd.concat([df_sem, new], ignore_index=True)
    save_semester_records(df_sem)
    update_student_academic_summary(student_number)
    return gwa

def update_semester_subjects(student_number, ay, sem, subjects):
    sem_index = get_semester_index(student_number, ay, sem)
    if sem_index >= 1:
        ok, msg = check_committee_approval(student_number, sem_index)
        if not ok: st.error(msg); return False
        ok, msg = check_pos_approval(student_number, sem_index)
        if not ok: st.error(msg); return False
    ok, msg = check_residency_enforcement(student_number)
    if isinstance(ok, bool) and not ok: st.error(msg); return False
    df_sem = load_semester_records()
    mask = (df_sem["student_number"]==student_number) & (df_sem["academic_year"]==ay) & (df_sem["semester"]==sem)
    if not mask.any(): return False
    idx = df_sem[mask].index[0]
    thesis_units = sum(float(s.get("units",0)) for s in subjects if "thesis" in s.get("course_code","").lower())
    if thesis_units>0:
        ok, msg = check_thesis_units_limit(student_number, thesis_units)
        if not ok: st.error(msg); return False
    gwa = compute_gwa_from_subjects(subjects)
    total_units = sum(float(s.get("units",0)) for s in subjects)
    df_sem.at[idx, "subjects_json"] = json.dumps(subjects)
    df_sem.at[idx, "total_units"] = total_units
    df_sem.at[idx, "gwa"] = gwa
    if df_sem.at[idx, "doc_status"] == "Approved":
        df_sem.at[idx, "doc_status"] = "Pending"
        df_sem.at[idx, "doc_remarks"] = "Subjects edited; re-upload required."
    save_semester_records(df_sem)
    update_student_academic_summary(student_number)
    return True

def update_semester_document(student_number, ay, sem, doc_path, doc_upload_time, status="Pending"):
    df_sem = load_semester_records()
    mask = (df_sem["student_number"]==student_number) & (df_sem["academic_year"]==ay) & (df_sem["semester"]==sem)
    if mask.any():
        idx = df_sem[mask].index[0]
        df_sem.at[idx, "doc_path"] = str(doc_path)
        df_sem.at[idx, "doc_upload_time"] = str(doc_upload_time)
        df_sem.at[idx, "doc_status"] = status
        df_sem.at[idx, "doc_remarks"] = ""
        df_sem.at[idx, "doc_validated_by"] = ""
        df_sem.at[idx, "doc_validated_time"] = ""
        save_semester_records(df_sem)
        return True
    return False

def validate_semester_document(student_number, ay, sem, status, remarks, validator_name):
    df_sem = load_semester_records()
    mask = (df_sem["student_number"]==student_number) & (df_sem["academic_year"]==ay) & (df_sem["semester"]==sem)
    if mask.any():
        idx = df_sem[mask].index[0]
        df_sem.at[idx, "doc_status"] = status
        df_sem.at[idx, "doc_remarks"] = remarks
        df_sem.at[idx, "doc_validated_by"] = validator_name
        df_sem.at[idx, "doc_validated_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_semester_records(df_sem)
        return True
    return False

def update_semester_status(student_number, ay, sem, new_status):
    df_sem = load_semester_records()
    mask = (df_sem["student_number"]==student_number) & (df_sem["academic_year"]==ay) & (df_sem["semester"]==sem)
    if mask.any():
        idx = df_sem[mask].index[0]
        df_sem.at[idx, "semester_status"] = new_status
        if new_status != "Regular":
            df_sem.at[idx, "subjects_json"] = "[]"
            df_sem.at[idx, "total_units"] = 0
            df_sem.at[idx, "gwa"] = 0.0
            df_sem.at[idx, "doc_status"] = ""
            df_sem.at[idx, "doc_path"] = ""
            df_sem.at[idx, "doc_upload_time"] = ""
            df_sem.at[idx, "doc_remarks"] = ""
            df_sem.at[idx, "doc_validated_by"] = ""
            df_sem.at[idx, "doc_validated_time"] = ""
        save_semester_records(df_sem)
        update_student_academic_summary(student_number)
        return True
    return False

def update_student_academic_summary(student_number):
    sems = get_student_semesters(student_number)
    total_grade = total_units = thesis_units = 0
    for _, row in sems.iterrows():
        if row["semester_status"] != "Regular":
            continue
        try:
            subjects = json.loads(row["subjects_json"])
        except:
            continue
        for subj in subjects:
            grade_val = subj.get("grade","")
            if grade_val in ["INC","DRP","P","IP"]:
                continue
            units = float(subj.get("units",0))
            total_units += units
            try:
                grade_num = float(grade_val)
                if grade_num != 4.00:
                    total_grade += units*grade_num
            except:
                pass
            if "thesis" in subj.get("course_code","").lower():
                try:
                    if 1.0 <= float(grade_val) <= 3.0:
                        thesis_units += units
                except:
                    pass
    df = load_data()
    idx = df[df["student_number"]==student_number].index
    if len(idx)>0:
        df.loc[idx, "total_units_taken"] = total_units
        df.loc[idx, "gwa"] = total_grade/total_units if total_units>0 else None
        df.loc[idx, "thesis_units_taken"] = thesis_units
        save_data(df)
        return True
    return False

def get_next_semester_sequence(academic_year, semester):
    sem_order = ["1st Sem","2nd Sem","Summer"]
    if semester not in sem_order:
        return academic_year, "1st Sem"
    idx = sem_order.index(semester)
    if idx < 2:
        return academic_year, sem_order[idx+1]
    start_year = int(academic_year.split("-")[0])
    return f"{start_year+1}-{start_year+2}", "1st Sem"

def create_next_semester(student_number, current_ay, current_sem):
    next_ay, next_sem = get_next_semester_sequence(current_ay, current_sem)
    df_sem = load_semester_records()
    if ((df_sem["student_number"]==student_number) & (df_sem["academic_year"]==next_ay) & (df_sem["semester"]==next_sem)).any():
        st.warning(f"Semester {next_ay} {next_sem} already exists.")
        return False
    try:
        add_semester_record(student_number, next_ay, next_sem, [], semester_status="Regular")
        st.success(f"Created new semester: {next_ay} {next_sem}")
        return True
    except ValueError as e:
        st.error(str(e))
        return False

# ==================== PROFILE PICTURE ====================
def save_profile_picture(student_number, uploaded_file):
    if uploaded_file is None: return None
    ext = uploaded_file.name.split('.')[-1].lower()
    if ext not in ['jpg','jpeg','png','gif']: return None
    filepath = os.path.join(PROFILE_PIC_FOLDER, f"{student_number}.{ext}")
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filepath

def delete_profile_picture(student_number):
    for f in os.listdir(PROFILE_PIC_FOLDER):
        if f.startswith(str(student_number)+"."):
            os.remove(os.path.join(PROFILE_PIC_FOLDER, f))
            return True
    return False

def get_profile_picture_path(student_number):
    for f in os.listdir(PROFILE_PIC_FOLDER):
        if f.startswith(str(student_number)+"."):
            return os.path.join(PROFILE_PIC_FOLDER, f)
    return None

# ==================== MILESTONE TRACKING ====================
def load_milestone_tracking():
    if not os.path.exists(MILESTONE_FILE) or os.path.getsize(MILESTONE_FILE)==0:
        return pd.DataFrame(columns=["student_number","milestone","status","date","file_path","remarks","reviewed_by","review_date"])
    df = pd.read_csv(MILESTONE_FILE, dtype=str)
    for col in ["student_number","milestone","status","date","file_path","remarks","reviewed_by","review_date"]:
        if col not in df.columns:
            df[col] = ""
        else:
            df[col] = df[col].fillna("").astype(str)
    return df

def save_milestone_tracking(df):
    df.to_csv(MILESTONE_FILE, index=False)

def get_student_milestones(student_number, program_type):
    df = load_milestone_tracking()
    student_df = df[df["student_number"]==student_number]
    milestone_names = MILESTONE_DEFS.get(program_type, MILESTONE_DEFS["MS_Thesis"])
    if student_df.empty:
        new_rows = [{"student_number":student_number, "milestone":m, "status":"Not Started", "date":"", "file_path":"", "remarks":"", "reviewed_by":"", "review_date":""} for m in milestone_names]
        new_df = pd.DataFrame(new_rows)
        df = pd.concat([df, new_df], ignore_index=True)
        save_milestone_tracking(df)
        return new_df
    else:
        existing = set(student_df["milestone"])
        new_rows = []
        for m in milestone_names:
            if m not in existing:
                new_rows.append({"student_number":student_number, "milestone":m, "status":"Not Started", "date":"", "file_path":"", "remarks":"", "reviewed_by":"", "review_date":""})
        if new_rows:
            df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
            save_milestone_tracking(df)
        return df[df["student_number"]==student_number]

def update_milestone(student_number, milestone, status, date_str, file_path, remarks, reviewer_name=None):
    df = load_milestone_tracking()
    mask = (df["student_number"]==student_number) & (df["milestone"]==milestone)
    if mask.any():
        df.loc[mask, "status"] = status
        if date_str: df.loc[mask, "date"] = str(date_str)
        if file_path: df.loc[mask, "file_path"] = str(file_path)
        if remarks: df.loc[mask, "remarks"] = str(remarks)
        if reviewer_name:
            df.loc[mask, "reviewed_by"] = str(reviewer_name)
            df.loc[mask, "review_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        new = pd.DataFrame([{"student_number":student_number, "milestone":milestone, "status":status, "date":date_str,
                             "file_path":file_path, "remarks":remarks, "reviewed_by":reviewer_name or "",
                             "review_date":datetime.now().strftime("%Y-%m-%d %H:%M:%S") if reviewer_name else ""}])
        df = pd.concat([df, new], ignore_index=True)
    save_milestone_tracking(df)
    return True, ""

def save_milestone_file(student_number, milestone_name, uploaded_file):
    if uploaded_file is None: return None
    folder = os.path.join(UPLOAD_FOLDER, student_number, "milestones")
    os.makedirs(folder, exist_ok=True)
    ext = uploaded_file.name.split('.')[-1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = milestone_name.replace(" ","_").replace("/","_")
    filepath = os.path.join(folder, f"{safe_name}_{timestamp}.{ext}")
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filepath

def get_status_badge(status):
    if status in ["Approved","Verified Correct"]:
        return '<span class="status-badge status-approved">✅ Approved</span>'
    elif status in ["Rejected","Mismatch – Requires Correction"]:
        return '<span class="status-badge status-rejected">❌ Rejected</span>'
    elif status == "Pending":
        return '<span class="status-badge status-pending">🟡 Pending</span>'
    else:
        return '<span class="status-badge status-not-started">⚪ Not Started</span>'

def filter_dataframe(search_term, data):
    if data is None or not search_term: return data
    return data[data["name"].str.contains(search_term, case=False, na=False) | data["student_number"].str.contains(search_term, case=False, na=False)]

# ==================== RENDER SEMESTER BLOCK ====================
def render_semester_block_general(student_number, semester_row, is_staff=False, is_adviser=False):
    ay = str(semester_row["academic_year"])
    sem = str(semester_row["semester"])
    semester_status = str(semester_row.get("semester_status", "Regular")).strip()
    if semester_status not in SEMESTER_STATUS_OPTIONS:
        semester_status = "Regular"
    try:
        subjects = json.loads(semester_row["subjects_json"]) if semester_row["subjects_json"] else []
    except:
        subjects = []
    total_units = float(semester_row["total_units"]) if pd.notna(semester_row["total_units"]) else 0.0
    gwa = float(semester_row["gwa"]) if pd.notna(semester_row["gwa"]) else 0.0
    doc_status = str(semester_row.get("doc_status", "")).strip()
    doc_path = str(semester_row.get("doc_path", "")).strip()
    doc_remarks = str(semester_row.get("doc_remarks", "")).strip()

    expander_key = f"expander_{student_number}_{ay}_{sem}"
    if expander_key not in st.session_state:
        st.session_state[expander_key] = False

    expander_label = f"📅 {ay} | {sem}     📊 Units: {total_units:.0f}     🏅 GWA: {gwa:.2f}"
    with st.expander(expander_label, expanded=st.session_state[expander_key]):
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%); padding: 0.5rem 0.75rem; border-radius: 12px; margin-bottom: 0.75rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                <span style="font-weight: 600; color: #1f3b4c;">📌 Semester Details</span>
                <div><span style="background: #ffffff; padding: 0.2rem 0.8rem; border-radius: 20px; font-size: 0.8rem;">Status: {semester_status}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_status, _ = st.columns([2, 1])
        with col_status:
            st.markdown('<div class="info-card" style="padding: 0.75rem;"><h4>🎓 Academic Standing (This Term)</h4>', unsafe_allow_html=True)
            new_status = st.selectbox(
                "Status",
                SEMESTER_STATUS_OPTIONS,
                index=SEMESTER_STATUS_OPTIONS.index(semester_status) if semester_status in SEMESTER_STATUS_OPTIONS else 0,
                key=f"status_{student_number}_{ay}_{sem}",
                disabled=not (is_staff or is_adviser),
                label_visibility="collapsed"
            )
            if new_status != semester_status:
                if update_semester_status(student_number, ay, sem, new_status):
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        if semester_status == "Regular":
            # ---------- STUDENT ROLE: Document upload first, then editable table ----------
            if st.session_state.role == "Student":
                # 1) Document upload section
                st.markdown('<div class="info-card" style="padding: 0.75rem;"><h4>📄 Proof of Grades (AMIS Screenshot)</h4>', unsafe_allow_html=True)
                st.markdown("**You must upload a valid screenshot of your AMIS grades before you can save your subjects.**")

                doc_uploaded = doc_path and os.path.exists(doc_path)
                if doc_uploaded:
                    st.success(f"✅ Document uploaded on {semester_row.get('doc_upload_time', 'unknown date')}")
                    if doc_status == "Pending":
                        st.info("🕒 Your document is pending adviser validation. You can still edit and save your subjects.")
                    elif doc_status == "Approved":
                        st.success("✅ Your document has been approved.")
                    elif doc_status == "Rejected":
                        st.error(f"❌ Document rejected: {doc_remarks}")
                else:
                    st.warning("⚠️ No document uploaded yet. You must upload a proof of grades to save your subjects.")

                with st.form(key=f"upload_{student_number}_{ay}_{sem}"):
                    uploaded = st.file_uploader("Choose file (PDF/JPG/PNG)", type=["pdf", "jpg", "jpeg", "png"], key=f"upload_file_{ay}_{sem}")
                    if st.form_submit_button("📎 Upload Document"):
                        if uploaded:
                            folder = os.path.join(UPLOAD_FOLDER, student_number, "semester_docs")
                            os.makedirs(folder, exist_ok=True)
                            filename = f"{ay}_{sem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{uploaded.name.split('.')[-1].lower()}"
                            filepath = os.path.join(folder, filename)
                            with open(filepath, "wb") as f:
                                f.write(uploaded.getbuffer())
                            if update_semester_document(student_number, ay, sem, filepath, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Pending"):
                                st.success("Document uploaded! You can now edit and save your subjects.")
                                st.session_state[expander_key] = True
                                st.rerun()
                            else:
                                st.error("Upload failed. Please try again.")
                        else:
                            st.error("Please select a file.")
                st.markdown('</div>', unsafe_allow_html=True)

                # 2) Editable subjects table (with session state persistence)
                st.markdown('<div class="info-card" style="padding: 0.75rem;"><h4>📚 Course Enrollment</h4>', unsafe_allow_html=True)

                # Create a session state key for this semester's editable dataframe
                df_key = f"df_edit_{student_number}_{ay}_{sem}"
                if df_key not in st.session_state:
                    # Initialize from existing subjects
                    if subjects:
                        df_init = pd.DataFrame(subjects)
                    else:
                        df_init = pd.DataFrame(columns=["course_code", "course_description", "units", "grade"])
                    for col in ["course_code", "course_description", "units", "grade"]:
                        if col not in df_init.columns:
                            if col == "units":
                                df_init[col] = 0
                            else:
                                df_init[col] = ""
                    df_init = df_init[["course_code", "course_description", "units", "grade"]]
                    df_init["units"] = pd.to_numeric(df_init["units"], errors='coerce').fillna(0).astype(int)
                    df_init["course_code"] = df_init["course_code"].astype(str)
                    df_init["course_description"] = df_init["course_description"].astype(str)
                    st.session_state[df_key] = df_init

                # Data editor bound to session state
                edited_df = st.data_editor(
                    st.session_state[df_key],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "course_code": st.column_config.TextColumn("Course Code"),
                        "course_description": st.column_config.TextColumn("Course Description"),
                        "units": st.column_config.NumberColumn("Units", step=1, min_value=0),
                        "grade": st.column_config.SelectboxColumn("Grade", options=GRADE_OPTIONS)
                    },
                    key=f"editor_{student_number}_{ay}_{sem}"
                )
                # Update session state with any direct edits (important for save button)
                st.session_state[df_key] = edited_df

                col_add, col_save = st.columns([1, 4])
                with col_add:
                    if st.button("➕ Add Row", key=f"add_{student_number}_{ay}_{sem}", use_container_width=True):
                        new_row = pd.DataFrame([{"course_code": "", "course_description": "", "units": 0, "grade": "1.00"}])
                        st.session_state[df_key] = pd.concat([st.session_state[df_key], new_row], ignore_index=True)
                        st.session_state[expander_key] = True
                        st.rerun()

                with col_save:
                    save_disabled = not doc_uploaded
                    if save_disabled:
                        st.info("📎 Please upload a proof of grades document above before saving subjects.")
                    if st.button("💾 Save Subjects", key=f"save_{student_number}_{ay}_{sem}", use_container_width=True, disabled=save_disabled):
                        sem_idx = get_semester_index(student_number, ay, sem)
                        if sem_idx >= 1:
                            ok, msg = check_committee_approval(student_number, sem_idx)
                            if not ok:
                                st.error(msg)
                                st.stop()
                            ok, msg = check_pos_approval(student_number, sem_idx)
                            if not ok:
                                st.error(msg)
                                st.stop()
                        new_subjects = st.session_state[df_key].to_dict("records")
                        for s in new_subjects:
                            s["units"] = int(s["units"]) if s["units"] else 0
                            s["course_code"] = str(s.get("course_code", ""))
                            s["course_description"] = str(s.get("course_description", ""))
                            s["grade"] = str(s.get("grade", "1.00"))
                        if update_semester_subjects(student_number, ay, sem, new_subjects):
                            st.success("Subjects saved! Refreshing totals...")
                            # Clear the temporary session state for this semester
                            if df_key in st.session_state:
                                del st.session_state[df_key]
                            st.session_state[expander_key] = True
                            st.rerun()
                        else:
                            st.error("Save failed.")
                            st.session_state[expander_key] = True
                st.markdown('</div>', unsafe_allow_html=True)

            # ---------- STAFF / ADVISER ROLE: Read‑only subjects + validation ----------
            else:
                if subjects:
                    st.dataframe(pd.DataFrame(subjects), use_container_width=True, hide_index=True)
                else:
                    st.info("No subjects entered.")

                st.markdown('<div class="info-card" style="padding: 0.75rem;"><h4>📄 Proof of Grades (AMIS Screenshot)</h4>', unsafe_allow_html=True)
                st.markdown(f"**Validation Status:** {get_status_badge(doc_status)}", unsafe_allow_html=True)
                if doc_status == "Rejected" and doc_remarks:
                    st.warning(f"Rejection reason: {doc_remarks}")
                if doc_path and os.path.exists(doc_path):
                    st.info(f"Current file: {os.path.basename(doc_path)}")
                    file_ext = os.path.splitext(doc_path)[1].lower()
                    if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                        st.image(doc_path, caption="Proof of Grades", width=300)
                    elif file_ext == '.pdf':
                        with open(doc_path, "rb") as f:
                            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="400" type="application/pdf"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)
                    else:
                        st.warning("Preview not available.")
                        with open(doc_path, "rb") as f:
                            st.download_button("Download", f, file_name=os.path.basename(doc_path))

                if is_adviser and doc_status == "Pending":
                    with st.form(key=f"validate_{student_number}_{ay}_{sem}"):
                        remarks_val = st.text_area("Remarks")
                        col1, col2 = st.columns(2)
                        if col1.form_submit_button("✅ Approve"):
                            validate_semester_document(student_number, ay, sem, "Approved", remarks_val, st.session_state.display_name)
                            st.rerun()
                        if col2.form_submit_button("❌ Reject"):
                            validate_semester_document(student_number, ay, sem, "Rejected", remarks_val, st.session_state.display_name)
                            st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        else:
            # Non-Regular semester status – no editing
            st.info(f"ℹ️ Semester marked as **{semester_status}**. Subject entry is disabled.")
            if subjects:
                st.dataframe(pd.DataFrame(subjects), use_container_width=True, hide_index=True)
            if doc_path and os.path.exists(doc_path):
                st.markdown('<div class="info-card" style="padding: 0.75rem;"><h4>📄 Proof of Grades</h4>', unsafe_allow_html=True)
                st.info(f"Uploaded file: {os.path.basename(doc_path)}")
                st.markdown('</div>', unsafe_allow_html=True)

# ==================== REGISTRATION FORM ====================
def register_new_student_form():
    if st.session_state.get("reg_success"):
        st.success("✅ Student registered!")
        st.session_state.reg_success = False
    with st.form("register_student_form"):
        st.subheader("Enroll Admitted Student")
        col1, col2 = st.columns(2)
        with col1:
            student_number = st.text_input("Student Number *")
            last_name = st.text_input("Last Name *")
            first_name = st.text_input("First Name *")
            middle_name = st.text_input("Middle Name")
            personal_email = st.text_input("Personal Email *")
        with col2:
            program = st.selectbox("Program", PROGRAMS)
            specialization = st.selectbox("Specialization (if any)", SPECIALIZATIONS)
            ay_sel = st.selectbox("Admission AY", ACADEMIC_YEARS)
            ay_start = int(ay_sel.split("-")[0])
            semester = st.selectbox("Starting Semester", SEMESTERS)
            student_status = st.selectbox("Student Status", ["Active","On Leave","Inactive","Graduated","Shifted","Transferred"])
        advisor = st.selectbox("Temporary Adviser", FACULTY_NAMES)
        prior_ms = st.checkbox("MS graduate (for PhD)") if program=="PhD Environmental Science" else False
        submitted = st.form_submit_button("Register")
        if submitted:
            errors = []
            if not student_number: errors.append("Student Number")
            if not last_name: errors.append("Last Name")
            if not first_name: errors.append("First Name")
            if not program: errors.append("Program")
            if not personal_email: errors.append("Email")
            df = load_data()
            if student_number in df["student_number"].values: errors.append("Duplicate student number")
            if errors:
                st.error(f"Missing: {', '.join(errors)}")
            else:
                full_name = f"{last_name}, {first_name} {middle_name}".strip()
                req_units = get_required_units(program, prior_ms)
                new_row = {"student_number":student_number, "password":student_number, "name":full_name,
                           "last_name":last_name, "first_name":first_name, "middle_name":middle_name,
                           "program":program, "specialization":specialization, "advisor":advisor, "ay_start":ay_start, "semester":semester,
                           "gwa":None, "total_units_taken":0, "total_units_required":req_units,
                           "thesis_units_taken":0, "thesis_units_limit":get_thesis_limit_from_program(program),
                           "thesis_extension_units":0, "residency_years_used":0, "residency_extension_years":0,
                           "residency_max_years":get_residency_max_from_program(program), "pos_status":"Not Started",
                           "pos_approval_date":"", "qualifying_exam_status":"N/A", "written_comprehensive_status":"N/A",
                           "oral_comprehensive_status":"N/A", "general_exam_status":"Not Taken", "final_exam_status":"Not Taken",
                           "final_exam_attempts":0, "profile_pic":"", "committee_members_structured":"",
                           "committee_approval_date":"", "thesis_outline_approved":"No", "thesis_status":"Not Started",
                           "prior_ms_graduate":prior_ms, "student_status":student_status, "address":"", "phone":"",
                           "institutional_email":"", "personal_email":personal_email, "gender":"", "civil_status":"",
                           "citizenship":"", "birthdate":"", "religion":"", "emergency_name":"", "emergency_relationship":"",
                           "emergency_country_code":"", "emergency_phone":"", "special_status":"Regular"}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                get_student_milestones(student_number, get_program_type(program))
                try:
                    timeline = generate_timeline(ay_start, semester, program)
                    for ay, sem in timeline:
                        add_semester_record(student_number, ay, sem, [], semester_status="Regular")
                    send_welcome_email(student_number, personal_email, full_name)
                    st.session_state.reg_success = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not create semesters: {e}")

def get_inc_alert(student_number):
    alerts = []
    for _, row in load_semester_records().iterrows():
        if row["student_number"]!=student_number: continue
        try:
            subjects = json.loads(row["subjects_json"])
        except:
            continue
        sem_date = row.get("doc_upload_time","")
        if sem_date:
            try: sem_end = datetime.strptime(sem_date, "%Y-%m-%d %H:%M:%S")
            except: sem_end = datetime.now()
        else: sem_end = datetime.now()
        deadline = sem_end + timedelta(days=365)
        for subj in subjects:
            if subj.get("grade") in ["INC","4.00"]:
                days_left = (deadline - datetime.now()).days
                alerts.append({"course":subj.get("course_code","Unknown"), "semester":f"{row['academic_year']} {row['semester']}",
                               "deadline":deadline.strftime("%Y-%m-%d"), "days_left":days_left,
                               "status":"expired" if days_left<0 else ("warning" if days_left<60 else "ok")})
    return alerts

# ==================== PROFILE RENDERER ====================
def render_compact_profile(student, is_own_profile=True):
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1f3b4c 0%, #2c5a6e 100%); border-radius: 20px; padding: 1.5rem; margin-bottom: 1.5rem; color: white;">
        <h2 style="margin: 0; font-size: 1.8rem;">{student['name']}</h2>
        <p style="margin: 0.2rem 0 0; opacity: 0.8; font-size: 1rem;">🎓 {student['student_number']}</p>
    </div>
    """, unsafe_allow_html=True)
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.markdown("""
        <div style="background: white; border-radius: 20px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #e9ecef; text-align: center;">
            <h4 style="margin-top: 0;">📸 Profile Picture</h4>
        </div>
        """, unsafe_allow_html=True)
        pic_path = get_profile_picture_path(student["student_number"])
        if pic_path and os.path.exists(pic_path):
            st.image(pic_path, width=180)
        else:
            st.info("No profile picture")
        
        if is_own_profile:
            # Picture upload form
            with st.form(key=f"pic_form_{student['student_number']}"):
                uploaded_pic = st.file_uploader("Update picture", type=["jpg", "jpeg", "png"])
                submit_pic = st.form_submit_button("Upload Picture", use_container_width=True)
                if submit_pic and uploaded_pic is not None:
                    fn = save_profile_picture(student["student_number"], uploaded_pic)
                    if fn:
                        df = load_data()
                        df.loc[df["student_number"] == student["student_number"], "profile_pic"] = fn
                        save_data(df)
                        st.success("Picture updated!")
                        st.rerun()
                    else:
                        st.error("Invalid file type. Please upload JPG, JPEG, or PNG.")
            
            # Delete picture button
            if st.button("Delete picture", key=f"del_pic_{student['student_number']}"):
                if delete_profile_picture(student["student_number"]):
                    df = load_data()
                    df.loc[df["student_number"] == student["student_number"], "profile_pic"] = ""
                    save_data(df)
                    st.success("Picture deleted.")
                    st.rerun()
    
    with col_right:
        st.markdown("""
        <div style="background: white; border-radius: 20px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #e9ecef;">
            <h3 style="margin-top: 0; color: #1f3b4c;">📚 Academic Information</h3>
        </div>
        """, unsafe_allow_html=True)
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            st.markdown(f"**🎓 Program**  \n{student['program']}")
            if student.get('specialization') and student['specialization'] != "None":
                st.markdown(f"**🔧 Specialization**  \n{student['specialization']}")
            st.markdown(f"**👨‍🏫 Adviser**  \n{student['advisor']}")
        with col_a2:
            st.markdown(f"**📅 Admitted**  \n{format_ay(student['ay_start'], student['semester'])}")
            st.markdown(f"**📊 Required Units**  \n{student['total_units_required']}")
            st.markdown(f"**📌 Status**  \n{student.get('student_status','Active')}")
        
        if student.get("pos_status") == "Approved" and student.get("pos_approval_date"):
            st.caption(f"✅ POS approved on: {student['pos_approval_date']}")
        
        st.markdown("""
        <div style="background: white; border-radius: 20px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #e9ecef;">
            <h3 style="margin-top: 0; color: #1f3b4c;">👤 Personal Information</h3>
        </div>
        """, unsafe_allow_html=True)
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown(f"**📧 Personal Email**  \n{student.get('personal_email','—')}")
            st.markdown(f"**🏠 Address**  \n{student.get('address','—')}")
            st.markdown(f"**📞 Phone**  \n{student.get('phone','—')}")
        with col_p2:
            st.markdown(f"**🏛️ Institutional Email**  \n{student.get('institutional_email','—')}")
            st.markdown(f"**⚧ Gender**  \n{student.get('gender','—')}")
            st.markdown(f"**💍 Civil Status**  \n{student.get('civil_status','—')}")
        
        st.markdown("""
        <div style="background: white; border-radius: 20px; padding: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #e9ecef;">
            <h3 style="margin-top: 0; color: #1f3b4c;">🚨 Emergency Contact</h3>
        </div>
        """, unsafe_allow_html=True)
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            st.markdown(f"**Name**  \n{student.get('emergency_name','—')}")
            st.markdown(f"**Relationship**  \n{student.get('emergency_relationship','—')}")
        with col_e2:
            st.markdown(f"**Phone**  \n{student.get('emergency_country_code','')} {student.get('emergency_phone','—')}")
                 

# ==================== STAFF DASHBOARD ====================
def staff_dashboard():
    st.markdown("## 🏢 Staff Dashboard – Administrative Control")
    tabs = st.tabs(["📋 Student Master List", "➕ Registration", "🔄 Status Update", "📊 Analytics"])
    
    df_students = load_data().copy()
    
    def get_milestone_completion(student_number, prog_type):
        milestones = get_student_milestones(student_number, prog_type)
        if milestones.empty:
            return 0
        completed = milestones[milestones["status"] == "Approved"].shape[0]
        total = milestones.shape[0]
        return completed if total == 0 else (completed / total) * 100
    
    df_students["milestone_completion"] = df_students.apply(
        lambda row: get_milestone_completion(row["student_number"], get_program_type(row["program"])), axis=1
    )
    
    with tabs[0]:
        st.subheader("📌 Student Master List")
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            program_filter = st.multiselect("Program", options=sorted(df_students["program"].unique()), default=[], key="filter_program")
        with col_f2:
            adviser_filter = st.multiselect("Adviser", options=sorted(df_students["advisor"].unique()), default=[], key="filter_adviser")
        with col_f3:
            status_filter = st.multiselect("Student Status", options=sorted(df_students["student_status"].unique()), default=[], key="filter_status")
        with col_f4:
            ay_filter = st.multiselect("Admission Year", options=sorted(df_students["ay_start"].unique()), default=[], key="filter_ay")
        
        col_f5, col_f6 = st.columns(2)
        with col_f5:
            milestone_min = st.slider("Min Milestone Completion (%)", 0, 100, 0, key="slider_milestone")
        with col_f6:
            keyword = st.text_input("Keyword Search (Name/Student No.)", key="keyword_search")
        
        filtered = df_students.copy()
        if program_filter: filtered = filtered[filtered["program"].isin(program_filter)]
        if adviser_filter: filtered = filtered[filtered["advisor"].isin(adviser_filter)]
        if status_filter: filtered = filtered[filtered["student_status"].isin(status_filter)]
        if ay_filter: filtered = filtered[filtered["ay_start"].isin(ay_filter)]
        if milestone_min > 0: filtered = filtered[filtered["milestone_completion"] >= milestone_min]
        if keyword: filtered = filtered[filtered["name"].str.contains(keyword, case=False, na=False) | 
                                   filtered["student_number"].str.contains(keyword, case=False, na=False)]
        
        st.markdown(f"**Showing {len(filtered)} of {len(df_students)} students**")
        
        display_cols = ["student_number", "name", "program", "specialization", "advisor", "ay_start", "student_status", "total_units_taken", "gwa", "milestone_completion"]
        display_df = filtered[display_cols].copy()
        display_df["milestone_completion"] = display_df["milestone_completion"].round(1).astype(str) + "%"
        display_df.rename(columns={
            "student_number": "Student No.", "name": "Name", "program": "Program", "specialization": "Specialization",
            "advisor": "Adviser", "ay_start": "Admission Year", "student_status": "Status",
            "total_units_taken": "Units Taken", "gwa": "GWA"
        }, inplace=True)
        
        page_size = 20
        total_pages = max(1, (len(display_df) + page_size - 1) // page_size)
        if "student_list_page" not in st.session_state:
            st.session_state.student_list_page = 0
        page = st.session_state.student_list_page
        start = page * page_size
        end = start + page_size
        paginated_df = display_df.iloc[start:end]
        
        col_prev, col_page_info, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("◀ Previous", disabled=page==0, key="prev_page"):
                st.session_state.student_list_page -= 1
                st.rerun()
        with col_page_info:
            st.markdown(f"Page {page+1} of {total_pages}")
        with col_next:
            if st.button("Next ▶", disabled=page>=total_pages-1, key="next_page"):
                st.session_state.student_list_page += 1
                st.rerun()
        
        st.dataframe(paginated_df, use_container_width=True, height=500)
        
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Filtered List (CSV)", data=csv, file_name=f"students_export_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", key="export_csv")
        
        st.markdown("---")
        st.markdown("#### 👤 View/Edit Individual Student")
        selected_student = st.selectbox("Select Student", options=filtered["student_number"].tolist(), 
                                        format_func=lambda x: f"{x} - {filtered[filtered['student_number']==x]['name'].values[0]}",
                                        key="select_student_master")
        if st.button("Open Student Profile", key="open_profile_master"):
            st.session_state.staff_selected_student = selected_student
            st.session_state.staff_show_update = True
            st.rerun()
    
    with tabs[1]:
        register_new_student_form()
    
    with tabs[2]:
        st.subheader("🔄 Update Student Enrollment Status")
        student_to_update = st.selectbox("Select Student", options=df_students["student_number"].tolist(), 
                                         format_func=lambda x: f"{x} - {df_students[df_students['student_number']==x]['name'].values[0]}",
                                         key="select_student_status")
        current_status = df_students[df_students["student_number"]==student_to_update]["student_status"].values[0]
        new_status = st.selectbox("New Status", options=["Active","On Leave","Inactive","Graduated","Shifted","Transferred"], 
                                  index=["Active","On Leave","Inactive","Graduated","Shifted","Transferred"].index(current_status) if current_status in ["Active","On Leave","Inactive","Graduated","Shifted","Transferred"] else 0,
                                  key="status_select")
        if st.button("Update Status", key="update_status_btn"):
            df_update = load_data()
            idx = df_update[df_update["student_number"]==student_to_update].index
            if len(idx)>0:
                df_update.at[idx[0], "student_status"] = new_status
                save_data(df_update)
                st.success(f"Status for {student_to_update} updated to {new_status}")
                st.rerun()
    
    with tabs[3]:
        st.subheader("📊 Analytics Dashboard")
        col_a1, col_a2, col_a3 = st.columns(3)
        with col_a1: st.metric("Total Students", len(df_students))
        with col_a2: st.metric("Active Students", df_students[df_students["student_status"]=="Active"].shape[0])
        with col_a3: st.metric("Programs Offered", df_students["program"].nunique())
        st.markdown("---")
        col_ch1, col_ch2 = st.columns(2)
        with col_ch1:
            prog_counts = df_students["program"].value_counts().reset_index()
            prog_counts.columns = ["Program", "Count"]
            fig1 = px.bar(prog_counts, x="Program", y="Count", title="Students per Program", color="Program")
            st.plotly_chart(fig1, use_container_width=True)
        with col_ch2:
            adviser_counts = df_students["advisor"].value_counts().head(10).reset_index()
            adviser_counts.columns = ["Adviser", "Count"]
            fig2 = px.bar(adviser_counts, x="Adviser", y="Count", title="Top 10 Advisers by Student Count", color="Adviser")
            st.plotly_chart(fig2, use_container_width=True)
        fig3 = px.histogram(df_students, x="milestone_completion", nbins=20, title="Distribution of Milestone Completion (%)")
        st.plotly_chart(fig3, use_container_width=True)
        status_counts = df_students["student_status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig4 = px.pie(status_counts, values="Count", names="Status", title="Student Status")
        st.plotly_chart(fig4, use_container_width=True)

# ==================== ADVISER DASHBOARD (NEW) ====================
def adviser_dashboard():
    st.markdown("## 👨‍🏫 Faculty Adviser Dashboard")
    st.caption(f"Welcome, {st.session_state.display_name}. You can only view and verify your assigned advisees.")
    
    df = load_data()
    advisees = df[df["advisor"] == st.session_state.display_name].copy()
    if advisees.empty:
        st.warning("You have no assigned advisees yet.")
        return
    
    # Helper to get milestone counts
    def get_milestone_status_counts(student_number, prog_type):
        milestones = get_student_milestones(student_number, prog_type)
        if milestones.empty:
            return {"Not Started": 0, "Pending": 0, "Approved": 0, "Rejected": 0}
        return milestones["status"].value_counts().to_dict()
    
    advisees["milestone_counts"] = advisees.apply(
        lambda row: get_milestone_status_counts(row["student_number"], get_program_type(row["program"])), axis=1
    )
    advisees["pending_milestones"] = advisees["milestone_counts"].apply(lambda x: x.get("Pending", 0))
    advisees["completed_milestones"] = advisees["milestone_counts"].apply(lambda x: x.get("Approved", 0))
    advisees["total_milestones"] = advisees.apply(
        lambda row: len(MILESTONE_DEFS.get(get_program_type(row["program"]), [])), axis=1
    )
    
    # Create tabs
    tab_overview, tab_advisees, tab_analytics = st.tabs(["📊 Overview", "👥 My Advisees", "📈 Analytics"])
    
    with tab_overview:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div style="background: white; border-radius: 20px; padding: 1rem; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-left: 4px solid #2c5a6e;">
                <div style="font-size: 2rem; font-weight: 700; color: #1f3b4c;">{len(advisees)}</div>
                <div style="font-size: 0.8rem; color: #5b6e8c;">Total Advisees</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            active_count = advisees[advisees["student_status"] == "Active"].shape[0]
            st.markdown(f"""
            <div style="background: white; border-radius: 20px; padding: 1rem; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-left: 4px solid #2c5a6e;">
                <div style="font-size: 2rem; font-weight: 700; color: #1f3b4c;">{active_count}</div>
                <div style="font-size: 0.8rem; color: #5b6e8c;">Active Students</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            pending_total = advisees["pending_milestones"].sum()
            st.markdown(f"""
            <div style="background: white; border-radius: 20px; padding: 1rem; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-left: 4px solid #2c5a6e;">
                <div style="font-size: 2rem; font-weight: 700; color: #1f3b4c;">{pending_total}</div>
                <div style="font-size: 0.8rem; color: #5b6e8c;">Pending Verifications</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### 📋 Recent Activity")
        # Show a simple list of advisees with pending milestones
        pending_advisees = advisees[advisees["pending_milestones"] > 0].sort_values("pending_milestones", ascending=False).head(5)
        if not pending_advisees.empty:
            for _, row in pending_advisees.iterrows():
                st.markdown(f"""
                <div style="background: #f8fafc; border-radius: 16px; padding: 0.5rem 1rem; margin-bottom: 0.5rem; border: 1px solid #e9ecef;">
                    <span style="font-weight: 600;">{row['name']}</span> ({row['student_number']}) – 
                    <span style="color: #856404;">{row['pending_milestones']} pending milestone(s)</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No pending verifications for your advisees.")
    
    with tab_advisees:
        st.subheader("📋 Your Advisees")
        # Filters
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            prog_filter = st.multiselect("Filter by Program", options=sorted(advisees["program"].unique()), default=[], key="adv_prog_filter")
        with col_f2:
            status_filter = st.multiselect("Filter by Student Status", options=sorted(advisees["student_status"].unique()), default=[], key="adv_status_filter")
        with col_f3:
            pending_filter = st.selectbox("Show only with pending milestones", ["All", "Yes", "No"], key="adv_pending_filter")
        
        keyword = st.text_input("🔍 Search (Name / Student No.)", key="adv_search")
        
        filtered = advisees.copy()
        if prog_filter: filtered = filtered[filtered["program"].isin(prog_filter)]
        if status_filter: filtered = filtered[filtered["student_status"].isin(status_filter)]
        if pending_filter == "Yes": filtered = filtered[filtered["pending_milestones"] > 0]
        elif pending_filter == "No": filtered = filtered[filtered["pending_milestones"] == 0]
        if keyword: filtered = filtered[filtered["name"].str.contains(keyword, case=False, na=False) | 
                                       filtered["student_number"].str.contains(keyword, case=False, na=False)]
        
        st.markdown(f"**Showing {len(filtered)} of {len(advisees)} advisees**")
        
        # Prepare display table
        display_df = filtered[["student_number", "name", "program", "student_status", "pending_milestones", "completed_milestones", "total_milestones"]].copy()
        display_df.columns = ["Student No.", "Name", "Program", "Status", "Pending", "Completed", "Total"]
        display_df["Progress"] = (display_df["Completed"] / display_df["Total"] * 100).round(1).astype(str) + "%"
        
        st.dataframe(display_df, use_container_width=True, height=400)
        
        st.markdown("---")
        st.markdown("#### 🔍 Select Student for Verification")
        selected_student = st.selectbox("Choose student", options=filtered["student_number"].tolist(),
                                        format_func=lambda x: f"{x} - {filtered[filtered['student_number']==x]['name'].values[0]}",
                                        key="adv_select_student")
        if st.button("Open Student Profile for Verification", key="adv_open_profile"):
            st.session_state.adviser_selected_student = selected_student
            st.rerun()
    
    with tab_analytics:
        st.subheader("📊 Advisee Analytics")
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            prog_counts = advisees["program"].value_counts().reset_index()
            prog_counts.columns = ["Program", "Count"]
            fig = px.bar(prog_counts, x="Program", y="Count", title="Advisees by Program", color="Program")
            st.plotly_chart(fig, use_container_width=True)
        with col_a2:
            status_counts = advisees["student_status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            fig2 = px.pie(status_counts, values="Count", names="Status", title="Student Status Distribution")
            st.plotly_chart(fig2, use_container_width=True)
        
        st.markdown("---")
        st.markdown("#### 🏆 Milestone Completion Overview")
        # Histogram of milestone completion percentages
        completion_pct = (advisees["completed_milestones"] / advisees["total_milestones"] * 100).fillna(0)
        fig3 = px.histogram(x=completion_pct, nbins=20, title="Milestone Completion Distribution (%)",
                            labels={"x": "Completion %", "y": "Number of Advisees"})
        st.plotly_chart(fig3, use_container_width=True)

# ==================== UNIFIED STUDENT PROFILE VIEW ====================
def view_student_profile(student_number, viewer_role):
    df = load_data()
    student = df[df["student_number"]==student_number].iloc[0].copy()
    program_type = get_program_type(student["program"])
    is_staff = (viewer_role=="SESAM Staff")
    is_adviser = (viewer_role=="Faculty Adviser" and student["advisor"]==st.session_state.display_name)
    resid_status, used, max_y = check_residency_alert(student)
    if resid_status == "exceeded":
        st.markdown(f'<div class="danger-banner">⚠️ RESIDENCY EXCEEDED: {used} years used (max {max_y}).</div>', unsafe_allow_html=True)
    elif resid_status in ["warning","warning_extension"]:
        st.markdown(f'<div class="warning-banner">⚠️ Residency warning: {used} out of {max_y} years.</div>', unsafe_allow_html=True)
    for inc in get_inc_alert(student_number):
        if inc["status"]=="expired":
            st.markdown(f'<div class="danger-banner">❌ {inc["course"]} ({inc["semester"]}) INC/4.0 expired.</div>', unsafe_allow_html=True)
        elif inc["status"]=="warning":
            st.markdown(f'<div class="warning-banner">⚠️ {inc["course"]} ({inc["semester"]}) deadline in {inc["days_left"]} days.</div>', unsafe_allow_html=True)
    st.markdown(f"## {student['name']} ({student_number})")
    if st.button("← Back"):
        if is_staff: 
            st.session_state.staff_selected_student = None
            st.session_state.staff_show_update = True
        else: 
            st.session_state.adviser_selected_student = None
        st.rerun()
    milestone_list = MILESTONE_DEFS.get(program_type, MILESTONE_DEFS["MS_Thesis"])
    tab_names = ["👤 Profile", "📚 Coursework"] + milestone_list
    if is_staff:
        tab_names.append("⚙️ Admin")
    tabs = st.tabs(tab_names)
    with tabs[0]:
        render_compact_profile(student, is_own_profile=(viewer_role=="Student"))
        if is_staff:
            with st.form("staff_edit"):
                new_addr = st.text_input("Address", student.get("address",""))
                new_phone = st.text_input("Phone", student.get("phone",""))
                new_email = st.text_input("Institutional Email", student.get("institutional_email",""))
                new_program = st.selectbox("Program", PROGRAMS, index=PROGRAMS.index(student["program"]) if student["program"] in PROGRAMS else 0)
                new_spec = st.selectbox("Specialization", SPECIALIZATIONS, index=SPECIALIZATIONS.index(student.get("specialization","None")) if student.get("specialization","None") in SPECIALIZATIONS else 0)
                new_status = st.selectbox("Student Status", ["Active","On Leave","Inactive","Graduated","Shifted","Transferred"], index=["Active","On Leave","Inactive","Graduated","Shifted","Transferred"].index(student.get("student_status","Active")))
                if st.form_submit_button("Update Information"):
                    df2 = load_data()
                    idx = df2[df2["student_number"]==student_number].index
                    if len(idx)>0:
                        df2.at[idx[0],"address"]=new_addr
                        df2.at[idx[0],"phone"]=new_phone
                        df2.at[idx[0],"institutional_email"]=new_email
                        df2.at[idx[0],"program"]=new_program
                        df2.at[idx[0],"specialization"]=new_spec if new_spec!="None" else ""
                        df2.at[idx[0],"student_status"]=new_status
                        save_data(df2)
                        st.success("Updated"); st.rerun()
    with tabs[1]:
        st.subheader("Academic Record")
        existing_sems = get_student_semesters(student_number)
        existing_dict = {(row["academic_year"], row["semester"]): row for _, row in existing_sems.iterrows()}
        timeline = generate_timeline(student["ay_start"], student["semester"], student["program"])
        for ay, sem in timeline:
            key = (ay, sem)
            if key in existing_dict:
                render_semester_block_general(student_number, existing_dict[key], is_staff, is_adviser)
            else:
                with st.expander(f"📅 {ay} | {sem} (Not yet created)", expanded=False):
                    st.warning("This semester has not been created yet.")
                    if st.button("➕ Create this semester", key=f"create_{student_number}_{ay}_{sem}"):
                        try:
                            add_semester_record(student_number, ay, sem, [], semester_status="Regular")
                            st.success(f"Created {ay} {sem}.")
                            st.rerun()
                        except Exception as e: st.error(str(e))
        st.markdown("---")
        st.subheader("➕ Extra Semesters (Beyond Standard Duration)")
        if st.button("＋ Add Extra Semester", key=f"extra_sem_{student_number}"):
            last_ay, last_sem = timeline[-1]
            next_ay, next_sem = get_next_semester_sequence(last_ay, last_sem)
            try:
                add_semester_record(student_number, next_ay, next_sem, [], semester_status="Regular")
                st.success(f"Extra semester {next_ay} {next_sem} created.")
                st.rerun()
            except Exception as e: st.error(str(e))
        cola, colb, colc, cold = st.columns(4)
        cola.metric("Units Taken", student["total_units_taken"])
        colb.metric("Required", student["total_units_required"])
        colc.metric("Remaining", max(0, student["total_units_required"]-student["total_units_taken"]))
        cold.metric("GWA", f"{student['gwa']:.2f}" if pd.notna(student['gwa']) else "—")
    milestones_df = get_student_milestones(student_number, program_type)
    for i, milestone_name in enumerate(milestone_list):
        with tabs[2+i]:
            if is_staff:
                # Staff: read-only
                st.markdown(f"### {milestone_name}")
                row = milestones_df[milestones_df["milestone"]==milestone_name].iloc[0]
                st.markdown(get_status_badge(row["status"]), unsafe_allow_html=True)
                if row["date"]: st.write(f"**Date:** {row['date']}")
                if row["file_path"] and os.path.exists(row["file_path"]):
                    with open(row["file_path"], "rb") as f: st.download_button("Download", f, file_name=os.path.basename(row["file_path"]))
                if row["remarks"]: st.info(f"Remarks: {row['remarks']}")
                continue
            # For student and adviser: full workflow
            if milestone_name == "Plan of Study (POS)":
                st.markdown("## Plan of Study (POS)")
                st.info("📌 **Reminder:** Your Plan of Study (POS) must be approved before the second semester.")
                active = get_active_pos_version(student_number)
                if active:
                    st.success(f"Active POS v{active['version_number']} verified on {active['verification_date']}")
                    embed_pdf(active['pdf_path'])
                else:
                    st.info("No active POS yet.")
                pending = get_pending_pos_version(student_number)
                if pending:
                    st.warning(f"Pending POS v{pending['version_number']} awaiting verification.")
                    embed_pdf(pending['pdf_path'])
                    if is_adviser:
                        with st.form(f"verify_pos_{pending['version_id']}"):
                            remarks = st.text_area("Remarks")
                            if st.form_submit_button("✅ Verified Correct"):
                                success, msg = verify_pos_version(pending['version_id'], "Verified Correct", st.session_state.display_name, remarks)
                                if success: st.success(msg); st.rerun()
                            if st.form_submit_button("❌ Mismatch"):
                                if not remarks: st.error("Remarks required")
                                else: verify_pos_version(pending['version_id'], "Mismatch – Requires Correction", st.session_state.display_name, remarks); st.rerun()
                    else:
                        st.info("Awaiting adviser verification.")
                elif viewer_role=="Student":
                    with st.form("upload_pos"):
                        pdf = st.file_uploader("Upload GS-approved POS PDF", type=["pdf"])
                        if st.form_submit_button("Submit for Verification"):
                            if pdf:
                                success, msg = save_pos_version(student_number, pdf)
                                st.success(msg) if success else st.error(msg)
            elif milestone_name in ["Guidance Committee Members","Advisory Committee Formation","Supervisory Committee Formation"]:
                st.markdown(f"""
                <div class="committee-card">
                    <div class="committee-title">📋 {milestone_name}</div>
                    <div class="committee-subtitle">Please select your committee members from the faculty list.<br>
                    <strong>Requirements:</strong> Master's: Chair + Major + Cognate (Co‑chair optional).<br>
                    PhD: Chair + 1‑2 Major + 1‑2 Cognate (Co‑chair optional).</div>
                </div>
                """, unsafe_allow_html=True)

                active = get_active_committee_version(student_number)
                if active:
                    st.success(f"✅ Active Committee (Version {active['version_number']}) – verified on {active['verification_date']}")
                    with st.expander("View active committee details"):
                        members = get_committee_members_for_version(active['version_id'])
                        st.dataframe(members, use_container_width=True, hide_index=True)
                        embed_pdf(active['gs_pdf_path'])
                else:
                    pending = get_pending_committee_version(student_number)
                    if pending:
                        st.info(f"🕓 Pending verification (Version {pending['version_number']}). Please wait for your adviser.")
                        with st.expander("View your submitted details"):
                            members = get_committee_members_for_version(pending['version_id'])
                            st.dataframe(members, use_container_width=True, hide_index=True)
                            embed_pdf(pending['gs_pdf_path'])
                    else:
                        is_phd = is_phd_program(student["program"])
                        with st.form("submit_comm_student_modern", clear_on_submit=False):
                            st.markdown('<div class="committee-card" style="padding: 1rem;">', unsafe_allow_html=True)
                            st.markdown("### 👥 Committee Members")
                            chair = st.selectbox("Chair *", options=FACULTY_NAMES, key="chair_select_vsp")
                            co_chair = st.selectbox("Co‑chair (optional)", options=[""] + FACULTY_NAMES, key="cochair_select_vsp")
                            if is_phd:
                                major1 = st.selectbox("Major Member 1 *", options=FACULTY_NAMES, key="major1_select_vsp")
                                major2 = st.selectbox("Major Member 2 (optional)", options=[""] + FACULTY_NAMES, key="major2_select_vsp")
                                cognate1 = st.selectbox("Cognate Member 1 *", options=FACULTY_NAMES, key="cog1_select_vsp")
                                cognate2 = st.selectbox("Cognate Member 2 (optional)", options=[""] + FACULTY_NAMES, key="cog2_select_vsp")
                            else:
                                major1 = st.selectbox("Major Member *", options=FACULTY_NAMES, key="major1_select_vsp")
                                major2 = ""
                                cognate1 = st.selectbox("Cognate Member *", options=FACULTY_NAMES, key="cog1_select_vsp")
                                cognate2 = ""
                            st.markdown("---")
                            st.markdown("### 📄 Upload GS‑approved Committee Form")
                            pdf_file = st.file_uploader("Drag & drop or click to upload (PDF only)", type=["pdf"], key="modern_committee_pdf_vsp")
                            if pdf_file: st.success(f"✅ File selected: {pdf_file.name}")
                            submitted = st.form_submit_button("📎 Submit Committee for Verification", use_container_width=True)
                            if submitted:
                                errors = []
                                if not pdf_file: errors.append("PDF file")
                                if not chair: errors.append("Chair")
                                if not major1: errors.append("Major Member")
                                if not cognate1: errors.append("Cognate Member")
                                if errors: st.error(f"Missing required fields: {', '.join(errors)}")
                                else:
                                    members_dict = {
                                        'chair': chair,
                                        'co_chair': co_chair,
                                        'member_major': major1,
                                        'member_cognate1': cognate1,
                                        'member_cognate2': cognate2 if cognate2 else ""
                                    }
                                    if is_phd and major2: members_dict['member_major2'] = major2
                                    if is_phd and cognate2: members_dict['member_cognate2'] = cognate2
                                    success, msg = save_committee_version_enhanced(student_number, pdf_file, members_dict, is_phd)
                                    if success:
                                        st.success(msg)
                                        st.balloons()
                                        st.rerun()
                                    else:
                                        st.error(msg)
                            st.markdown('</div>', unsafe_allow_html=True)
                versions = get_committee_versions(student_number)
                if not versions.empty:
                    with st.expander("Committee Version History"):
                        for _, ver in versions.iterrows():
                            st.markdown(f"**Version {ver['version_number']}** – {ver['verification_status']} – {ver['created_at']}")
                            if ver['verification_status'] == "Verified Correct" and ver['is_active']: st.markdown("(Active)")
                            if ver['remarks']: st.caption(f"Remarks: {ver['remarks']}")
                            st.markdown("---")
            else:
                row = milestones_df[milestones_df["milestone"]==milestone_name].iloc[0]
                status = row["status"]
                st.markdown(get_status_badge(status), unsafe_allow_html=True)
                if row["date"]: st.write(f"**Date:** {row['date']}")
                if row["file_path"] and os.path.exists(row["file_path"]):
                    with open(row["file_path"], "rb") as f: st.download_button("Download", f, file_name=os.path.basename(row["file_path"]))
                if status in ["Not Started","Rejected"] and viewer_role=="Student":
                    with st.form(f"submit_{milestone_name}"):
                        file = st.file_uploader("Upload document", type=["pdf","jpg","jpeg","png"])
                        date_comp = st.date_input("Date of completion")
                        if st.form_submit_button("Submit for Approval") and file:
                            path = save_milestone_file(student_number, milestone_name, file)
                            update_milestone(student_number, milestone_name, "Pending", date_comp.strftime("%Y-%m-%d"), path, "", None)
                            st.success("Submitted"); st.rerun()
                elif status=="Pending" and is_adviser:
                    if milestone_name in ["General / Comprehensive Examination - Passed", "Final Oral Examination"]:
                        eligible, msg = check_comprehensive_exam_eligibility(student_number)
                        if not eligible: st.error(f"Cannot approve: {msg}")
                        else:
                            with st.form(f"review_{milestone_name}"):
                                remarks = st.text_area("Remarks")
                                if st.form_submit_button("✅ Approve"):
                                    update_milestone(student_number, milestone_name, "Approved", None, None, remarks, st.session_state.display_name)
                                    st.success("Approved"); st.rerun()
                                if st.form_submit_button("❌ Reject"):
                                    update_milestone(student_number, milestone_name, "Rejected", None, None, remarks, st.session_state.display_name)
                                    st.rerun()
                    else:
                        with st.form(f"review_{milestone_name}"):
                            remarks = st.text_area("Remarks")
                            if st.form_submit_button("✅ Approve"):
                                update_milestone(student_number, milestone_name, "Approved", None, None, remarks, st.session_state.display_name)
                                st.success("Approved"); st.rerun()
                            if st.form_submit_button("❌ Reject"):
                                update_milestone(student_number, milestone_name, "Rejected", None, None, remarks, st.session_state.display_name)
                                st.rerun()
                elif status=="Pending": st.info("Pending review")
                elif status=="Approved": st.success("Approved")
    if is_staff and len(tabs) > len(milestone_list)+2:
        with tabs[-1]:
            st.subheader("Administrative Tools")
            ext = student.get("thesis_extension_units",0)
            max_ext = get_max_thesis_extension_units(student["program"])
            st.write(f"Thesis extension units: {ext}/{max_ext}")
            if ext < max_ext:
                if st.button("➕ Grant 1 Thesis Extension Unit"):
                    df2 = load_data()
                    df2.loc[df2["student_number"]==student_number, "thesis_extension_units"] = ext+1
                    save_data(df2); st.rerun()
            res_ext = student.get("residency_extension_years",0)
            if res_ext < 2:
                if st.button("➕ Grant 1 Residency Extension Year"):
                    df2 = load_data()
                    df2.loc[df2["student_number"]==student_number, "residency_extension_years"] = res_ext+1
                    save_data(df2); st.rerun()
            if st.button("📥 Download All Students CSV"):
                csv = load_data().to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                st.markdown(f'<a href="data:file/csv;base64,{b64}" download="sesam_students.csv">Download CSV</a>', unsafe_allow_html=True)

# ==================== STUDENT DASHBOARD ====================
def student_dashboard():
    # Load data and define student
    df = load_data()
    student_records = df[df["student_number"] == st.session_state.username]
    if student_records.empty:
        st.error("Student record not found.")
        st.stop()
    student = student_records.iloc[0].copy()
    program_type = get_program_type(student["program"])
    
    # Show success message if profile was updated
    if st.session_state.get("profile_update_success", False):
        st.success("✅ Profile successfully updated!")
        st.session_state.profile_update_success = False
    
    st.subheader(f"📘 Your Dashboard – {student['name']}")
    st.info("📢 **Gentle Reminder:** Please ensure your contact details (Address, Phone Number, and Institutional Email) are always up‑to‑date. This helps us send you important announcements and updates promptly. You can edit your profile in the '👤 Profile' tab.")
    
    # Check missing required fields
    missing = [f for f in ["address","phone","institutional_email"] if not student.get(f)]
    if missing:
        st.warning(f"Please complete your profile: {', '.join(missing)}")
    
    # Load milestones
    milestones_df = get_student_milestones(student["student_number"], program_type)
    milestone_list = MILESTONE_DEFS.get(program_type, MILESTONE_DEFS["MS_Thesis"])
    tab_names = ["👤 Profile", "📚 Coursework"] + milestone_list
    tabs = st.tabs(tab_names)
    
    # --- Profile Tab ---
    with tabs[0]:
        render_compact_profile(student, is_own_profile=True)
        st.markdown("---")
        with st.expander("✏️ Edit Profile", expanded=False):
            with st.form(key="edit_profile_form"):
                addr = st.text_input("Address", value=student.get("address", ""))
                phone = st.text_input("Phone Number", value=student.get("phone", ""))
                email = st.text_input("Institutional Email (UP mail)", value=student.get("institutional_email", ""))
                submitted = st.form_submit_button("Save Changes", width='stretch')
                if submitted:
                    if not addr or not phone or not email:
                        st.error("All fields are required.")
                    else:
                        # Load fresh data and update
                        df2 = load_data()
                        idx = df2[df2["student_number"] == student["student_number"]].index
                        if len(idx) > 0:
                            df2.at[idx[0], "address"] = addr
                            df2.at[idx[0], "phone"] = phone
                            df2.at[idx[0], "institutional_email"] = email
                            save_data(df2)
                            st.session_state.profile_update_success = True
                            st.success("Profile updated! Refreshing...")
                            import time
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Student record not found.")
    
    # --- Coursework Tab ---
    with tabs[1]:
        st.subheader("Your Coursework")
        existing_sems = get_student_semesters(student["student_number"])
        existing_dict = {(row["academic_year"], row["semester"]): row for _, row in existing_sems.iterrows()}
        timeline = generate_timeline(student["ay_start"], student["semester"], student["program"])
        for ay, sem in timeline:
            key = (ay, sem)
            if key in existing_dict:
                render_semester_block_general(student["student_number"], existing_dict[key], False, False)
            else:
                with st.expander(f"📅 {ay} | {sem} (Not yet created)", expanded=False):
                    st.warning("This semester has not been created yet.")
                    if st.button("➕ Create this semester", key=f"create_{student['student_number']}_{ay}_{sem}"):
                        try:
                            add_semester_record(student["student_number"], ay, sem, [], semester_status="Regular")
                            st.success(f"Created {ay} {sem}.")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
        st.markdown("---")
        st.subheader("➕ Extra Semesters (Beyond Standard Duration)")
        if st.button("＋ Add Extra Semester", key=f"extra_sem_{student['student_number']}"):
            last_ay, last_sem = timeline[-1]
            next_ay, next_sem = get_next_semester_sequence(last_ay, last_sem)
            try:
                add_semester_record(student["student_number"], next_ay, next_sem, [], semester_status="Regular")
                st.success(f"Extra semester {next_ay} {next_sem} created.")
                st.rerun()
            except Exception as e:
                st.error(str(e))
        cola, colb, colc, cold = st.columns(4)
        cola.metric("Units Taken", student["total_units_taken"])
        colb.metric("Required", student["total_units_required"])
        colc.metric("Remaining", max(0, student["total_units_required"] - student["total_units_taken"]))
        cold.metric("GWA", f"{student['gwa']:.2f}" if pd.notna(student['gwa']) else "—")
    
    # --- Milestone Tabs ---
    for i, milestone_name in enumerate(milestone_list):
        with tabs[2 + i]:
            if milestone_name == "Plan of Study (POS)":
                st.markdown("## Plan of Study (POS)")
                st.info("📌 **Reminder:** Your Plan of Study (POS) must be approved before the second semester.")
                active = get_active_pos_version(student["student_number"])
                if active:
                    st.success(f"Active POS v{active['version_number']} verified on {active['verification_date']}")
                    embed_pdf(active['pdf_path'])
                else:
                    st.info("No active POS yet.")
                pending = get_pending_pos_version(student["student_number"])
                if pending:
                    st.info("You have a pending POS submission awaiting verification.")
                    embed_pdf(pending['pdf_path'])
                else:
                    with st.form("upload_pos_student"):
                        pdf = st.file_uploader("Upload GS-approved POS PDF", type=["pdf"])
                        if st.form_submit_button("Submit for Verification"):
                            if pdf:
                                success, msg = save_pos_version(student["student_number"], pdf)
                                st.success(msg) if success else st.error(msg)
            elif milestone_name in ["Guidance Committee Members", "Advisory Committee Formation", "Supervisory Committee Formation"]:
                st.markdown(f"""
                <div class="committee-card">
                    <div class="committee-title">📋 {milestone_name}</div>
                    <div class="committee-subtitle">Please select your committee members from the faculty list.<br>
                    <strong>Requirements:</strong> Master's: Chair + Major + Cognate (Co‑chair optional).<br>
                    PhD: Chair + 1‑2 Major + 1‑2 Cognate (Co‑chair optional).</div>
                </div>
                """, unsafe_allow_html=True)
                
                active = get_active_committee_version(student["student_number"])
                if active:
                    st.success(f"✅ Active Committee (Version {active['version_number']}) – verified on {active['verification_date']}")
                    with st.expander("View active committee details"):
                        members = get_committee_members_for_version(active['version_id'])
                        st.dataframe(members, use_container_width=True, hide_index=True)
                        embed_pdf(active['gs_pdf_path'])
                else:
                    pending = get_pending_committee_version(student["student_number"])
                    if pending:
                        st.info(f"🕓 Pending verification (Version {pending['version_number']}). Please wait for your adviser.")
                        with st.expander("View your submitted details"):
                            members = get_committee_members_for_version(pending['version_id'])
                            st.dataframe(members, use_container_width=True, hide_index=True)
                            embed_pdf(pending['gs_pdf_path'])
                    else:
                        is_phd = is_phd_program(student["program"])
                        with st.form("submit_comm_student_modern", clear_on_submit=False):
                            st.markdown('<div class="committee-card" style="padding: 1rem;">', unsafe_allow_html=True)
                            st.markdown("### 👥 Committee Members")
                            chair = st.selectbox("Chair *", options=FACULTY_NAMES, key="chair_select_sd")
                            co_chair = st.selectbox("Co‑chair (optional)", options=[""] + FACULTY_NAMES, key="cochair_select_sd")
                            if is_phd:
                                major1 = st.selectbox("Major Member 1 *", options=FACULTY_NAMES, key="major1_select_sd")
                                major2 = st.selectbox("Major Member 2 (optional)", options=[""] + FACULTY_NAMES, key="major2_select_sd")
                                cognate1 = st.selectbox("Cognate Member 1 *", options=FACULTY_NAMES, key="cog1_select_sd")
                                cognate2 = st.selectbox("Cognate Member 2 (optional)", options=[""] + FACULTY_NAMES, key="cog2_select_sd")
                            else:
                                major1 = st.selectbox("Major Member *", options=FACULTY_NAMES, key="major1_select_sd")
                                major2 = ""
                                cognate1 = st.selectbox("Cognate Member *", options=FACULTY_NAMES, key="cog1_select_sd")
                                cognate2 = ""
                            st.markdown("---")
                            st.markdown("### 📄 Upload GS‑approved Committee Form")
                            pdf_file = st.file_uploader("Drag & drop or click to upload (PDF only)", type=["pdf"], key="modern_committee_pdf_sd")
                            if pdf_file:
                                st.success(f"✅ File selected: {pdf_file.name}")
                            submitted = st.form_submit_button("📎 Submit Committee for Verification", use_container_width=True)
                            if submitted:
                                errors = []
                                if not pdf_file:
                                    errors.append("PDF file")
                                if not chair:
                                    errors.append("Chair")
                                if not major1:
                                    errors.append("Major Member")
                                if not cognate1:
                                    errors.append("Cognate Member")
                                if errors:
                                    st.error(f"Missing required fields: {', '.join(errors)}")
                                else:
                                    members_dict = {
                                        'chair': chair,
                                        'co_chair': co_chair,
                                        'member_major': major1,
                                        'member_cognate1': cognate1,
                                        'member_cognate2': cognate2 if cognate2 else ""
                                    }
                                    if is_phd and major2:
                                        members_dict['member_major2'] = major2
                                    if is_phd and cognate2:
                                        members_dict['member_cognate2'] = cognate2
                                    success, msg = save_committee_version_enhanced(student["student_number"], pdf_file, members_dict, is_phd)
                                    if success:
                                        st.success(msg)
                                        st.balloons()
                                        st.rerun()
                                    else:
                                        st.error(msg)
                            st.markdown('</div>', unsafe_allow_html=True)
                versions = get_committee_versions(student["student_number"])
                if not versions.empty:
                    with st.expander("Committee Version History"):
                        for _, ver in versions.iterrows():
                            st.markdown(f"**Version {ver['version_number']}** – {ver['verification_status']} – {ver['created_at']}")
                            if ver['verification_status'] == "Verified Correct" and ver['is_active']:
                                st.markdown("(Active)")
                            if ver['remarks']:
                                st.caption(f"Remarks: {ver['remarks']}")
                            st.markdown("---")
            else:
                # Other milestones
                row = milestones_df[milestones_df["milestone"] == milestone_name].iloc[0]
                status = row["status"]
                st.markdown(get_status_badge(status), unsafe_allow_html=True)
                if row["date"]:
                    st.write(f"**Date:** {row['date']}")
                if row["file_path"] and os.path.exists(row["file_path"]):
                    with open(row["file_path"], "rb") as f:
                        st.download_button("Download", f, file_name=os.path.basename(row["file_path"]))
                if status in ["Not Started", "Rejected"]:
                    with st.form(f"submit_{milestone_name}_student"):
                        file = st.file_uploader("Upload document", type=["pdf","jpg","jpeg","png"])
                        date_comp = st.date_input("Date of completion")
                        if st.form_submit_button("Submit for Approval") and file:
                            path = save_milestone_file(student["student_number"], milestone_name, file)
                            update_milestone(student["student_number"], milestone_name, "Pending", date_comp.strftime("%Y-%m-%d"), path, "", None)
                            st.success("Submitted")
                            st.rerun()
                elif status == "Pending":
                    st.info("Awaiting adviser review.")
                elif status == "Approved":
                    st.success("Approved")
    
    st.caption("For corrections, contact your adviser or SESAM Staff.")

# ==================== MAIN APP ====================
# ==================== MAIN APP ====================
if not st.session_state.logged_in:
    # Modern login UI – Green theme
    st.markdown("""
    <style>
        .login-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 80vh;
            background: linear-gradient(135deg, #f5f7fa 0%, #e8f0e8 100%);
            padding: 1rem;
        }
        .login-card {
            background: white;
            border-radius: 32px;
            box-shadow: 0 20px 35px -10px rgba(0,0,0,0.1);
            padding: 2rem 2rem 2.5rem;
            max-width: 450px;
            width: 100%;
            transition: transform 0.2s ease;
        }
        .login-card:hover {
            transform: translateY(-5px);
        }
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .login-header h1 {
            font-size: 2.2rem;
            color: #1b5e20;
            margin: 0;
            font-weight: 600;
        }
        .login-header p {
            color: #5b6e8c;
            margin-top: 0.5rem;
            font-size: 0.9rem;
        }
        .login-icon {
            font-size: 3rem;
            margin-bottom: 0.5rem;
        }
        .stTextInput > div > div > input {
            border-radius: 40px !important;
            padding: 0.6rem 1rem !important;
            border: 1px solid #cbd5e1 !important;
            font-size: 1rem !important;
            transition: all 0.2s ease;
        }
        .stTextInput > div > div > input:focus {
            border-color: #2e7d32 !important;
            box-shadow: 0 0 0 2px rgba(46,125,50,0.2) !important;
        }
        .stButton > button {
            background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%) !important;
            border: none !important;
            border-radius: 40px !important;
            padding: 0.6rem !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            color: white !important;
            width: 100%;
            transition: all 0.2s ease;
            margin-top: 0.5rem;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(46,125,50,0.3);
        }
        .demo-credentials {
            text-align: center;
            margin-top: 1.5rem;
            font-size: 0.8rem;
            color: #5b6e8c;
            background: #f8fafc;
            padding: 0.8rem;
            border-radius: 20px;
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="login-card">
            <div class="login-header">
                <div class="login-icon">🎓</div>
                <h1>SESAM KMIS</h1>
                <p>Graduate Student Lifecycle Management</p>
            </div>
        """, unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter your username or student number", key="login_username")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                try:
                    # Check staff/adviser users first
                    if username in USERS and USERS[username]["password"] == password:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.role = USERS[username]["role"]
                        st.session_state.display_name = USERS[username]["display_name"]
                        st.session_state.consent_given = False
                        st.rerun()
                    else:
                        # Check student records
                        df = load_data()
                        student_row = df[df["student_number"] == username]
                        if not student_row.empty and student_row.iloc[0].get("password") == password:
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.role = "Student"
                            st.session_state.display_name = student_row.iloc[0]["name"]
                            st.session_state.consent_given = False
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password. Please try again.")
                except Exception as e:
                    st.error(f"Login error: {e}")

        st.markdown("""
        <div class="demo-credentials">
            <strong>Demo accounts:</strong><br>
            Staff: staff1 / admin123 &nbsp;|&nbsp;
            Adviser: adviser1 / adv123 &nbsp;|&nbsp;
            Student: use registered student number as password
        </div>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# ==================== AFTER LOGIN ====================
if st.session_state.logged_in and not st.session_state.consent_given:
    show_consent_form()
    st.stop()

init_committee_tables()
init_pos_tables()
convert_expired_grades()
df = load_data()

with st.sidebar:
    st.markdown(f"**{st.session_state.display_name}**  \n{st.session_state.role}  \n✅ Consent given")
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.consent_given = False
        st.rerun()
    st.caption("SESAM KMIS v40.0 | Enhanced Adviser Dashboard")

st.title("🎓 SESAM Graduate Student Lifecycle Management")

role = st.session_state.role
if role == "SESAM Staff":
    staff_dashboard()
elif role == "Faculty Adviser":
    adviser_dashboard()
    if st.session_state.adviser_selected_student:
        view_student_profile(st.session_state.adviser_selected_student, "Faculty Adviser")
elif role == "Student":
    student_dashboard()
