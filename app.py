"""
SESAM KMIS - Graduate Student Lifecycle Management System
Version: 32.0 | Enhanced committee workflow: version control, adviser verification, GS PDF upload
Roles: Student (submit), Adviser (verify), Staff (read-only)
"""

import streamlit as st
import pandas as pd
import os
import json
from datetime import date, datetime, timedelta
import smtplib
from email.message import EmailMessage
import base64
import shutil

# ==================== EMAIL CONFIGURATION (placeholder) ====================
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
        msg.set_content(f"""
Dear {name},

Your SESAM KMIS account has been created based on your Notice of Admission (NOA).

Login credentials:
    Username: {student_number}
    Temporary Password: {student_number}

Please log in at: [Insert KMIS URL here]

After your first login, we strongly recommend that you change your password and update your institutional email address (UP mail) once it becomes active.

For any issues, please contact the SESAM ICT Coordination Unit.

Regards,
SESAM KMIS Administrator
""")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Email sending failed for {personal_email}: {e}")
        return False

# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="SESAM KMIS", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .profile-card { background: white; border-radius: 20px; padding: 1.2rem; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #e9ecef; }
    .profile-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; border-bottom: 2px solid #f0f2f6; padding-bottom: 0.5rem; }
    .profile-header h3 { margin: 0; color: #1f3b4c; font-size: 1.2rem; }
    .status-badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.7rem; font-weight: 500; }
    .status-not-started { background-color: #e9ecef; color: #495057; }
    .status-pending { background-color: #fff3cd; color: #856404; }
    .status-approved { background-color: #d4edda; color: #155724; }
    .status-rejected { background-color: #f8d7da; color: #721c24; }
    .warning-banner { background-color: #ffcc00; color: #333; padding: 0.5rem; border-radius: 8px; margin: 0.5rem 0; font-weight: bold; }
    .danger-banner { background-color: #dc3545; color: white; padding: 0.5rem; border-radius: 8px; margin: 0.5rem 0; font-weight: bold; }
    .next-step-card { background-color: #e3f2fd; border-left: 5px solid #1e88e5; padding: 1rem; border-radius: 12px; margin: 1rem 0; }
    .stButton button { border-radius: 30px !important; padding: 0.4rem 1.2rem !important; font-weight: 500 !important; }
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None
if "display_name" not in st.session_state:
    st.session_state.display_name = None
if "consent_given" not in st.session_state:
    st.session_state.consent_given = False
if "staff_selected_student" not in st.session_state:
    st.session_state.staff_selected_student = None
if "adviser_selected_student" not in st.session_state:
    st.session_state.adviser_selected_student = None
if "staff_show_update" not in st.session_state:
    st.session_state.staff_show_update = False
if "show_registration" not in st.session_state:
    st.session_state.show_registration = False
if "reg_success" not in st.session_state:
    st.session_state.reg_success = False
if "profile_update_success" not in st.session_state:
    st.session_state.profile_update_success = False

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
            In compliance with the Data Privacy Act of 2012 (Republic Act No. 10173), SESAM KMIS collects and processes personal and academic information solely for academic monitoring.
            <br><br><strong>Your Rights:</strong> You may access, correct, and request deletion of your data.
            <br><br>By clicking "I Consent", you agree to the processing as described.
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
}

# ==================== PROGRAM & UNIT REQUIREMENTS ====================
PROGRAMS = [
    "MS Environmental Science",
    "PhD Environmental Science",
    "PhD Environmental Diplomacy and Negotiations",
    "Master in Resilience Studies (M-ReS)",
    "Professional Masters in Tropical Marine Ecosystems Management (PM-TMEM)",
    "PhD by Research Environmental Science"
]

def get_program_type(program_name):
    if program_name.startswith("MS") or program_name.startswith("Master") or program_name == "Professional Masters in Tropical Marine Ecosystems Management (PM-TMEM)":
        return "MS_Thesis"
    elif program_name.startswith("PhD by Research"):
        return "PhD_Research"
    elif program_name.startswith("PhD"):
        return "PhD_Regular"
    else:
        return "MS_Thesis"

def is_master_program(program): return get_program_type(program).startswith("MS")
def is_phd_program(program): return get_program_type(program).startswith("PhD")

def get_required_units(program, prior_ms_graduate=False):
    if program == "MS Environmental Science":
        return 32
    elif program == "PhD Environmental Science":
        return 37 if prior_ms_graduate else 50
    elif program == "Master in Resilience Studies (M-ReS)":
        return 36
    elif program == "Professional Masters in Tropical Marine Ecosystems Management (PM-TMEM)":
        return 30
    elif program == "PhD by Research Environmental Science":
        return 0
    else:
        if is_master_program(program):
            return 24
        else:
            return 50

# ==================== MILESTONE DEFINITIONS ====================
MILESTONE_DEFS = {
    "MS_Thesis": [
        "Guidance Committee Members",
        "Plan of Study (POS)",
        "General Examination",
        "Thesis Work",
        "External Review",
        "Publishable Article",
        "Final Examination",
        "Final Submission",
        "Graduation Clearance"
    ],
    "MS_NonThesis": [
        "Guidance Committee Formation",
        "Plan of Study (POS)",
        "General Examination",
        "Final Examination",
        "Graduation Clearance"
    ],
    "PhD_Regular": [
        "Advisory Committee Formation",
        "Qualifying Exam",
        "Plan of Study",
        "Comprehensive Exam",
        "Dissertation",
        "External Review",
        "Publication",
        "Final Defense",
        "Submission",
        "Graduation"
    ],
    "PhD_Straight": [
        "Advisory Committee Formation",
        "Qualifying Exam",
        "Plan of Study",
        "Comprehensive Exam",
        "Dissertation",
        "External Review",
        "Publication (2 papers)",
        "Final Defense",
        "Submission",
        "Graduation"
    ],
    "PhD_Research": [
        "Supervisory Committee Formation",
        "Plan of Research",
        "Seminar Series (3 seminars)",
        "Research Progress Review",
        "Thesis Draft",
        "Publication (3 articles)",
        "Final Oral Examination",
        "Thesis Submission",
        "Graduation"
    ]
}

# ==================== HELPER FUNCTIONS ====================
SEMESTERS = ["1st Sem", "2nd Sem", "Summer"]
current_year = date.today().year
ACADEMIC_YEARS = [f"{year}-{year+1}" for year in range(current_year-5, current_year+6)]
GRADE_OPTIONS = ["1.00", "1.25", "1.50", "1.75", "2.00", "2.25", "2.50", "2.75", "3.00", "4.00", "INC", "DRP", "5.00", "P", "IP"]
SEMESTER_STATUS_OPTIONS = ["Regular", "Off-Sem", "On Leave", "Shifted Program", "Transferred"]

def get_thesis_limit_from_program(program):
    ptype = get_program_type(program)
    return 12 if ptype in ["PhD_Regular", "PhD_Straight", "PhD_Research"] else (6 if ptype == "MS_Thesis" else 0)

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
    sem_order = ["1st Sem", "2nd Sem", "Summer"]
    total_sem, total_summer, total_terms = get_semester_structure(program)
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

# ==================== DATA FILES ====================
DATA_FILE = "students.csv"
SEMESTER_FILE = "semester_records.csv"
MILESTONE_FILE = "milestone_tracking.csv"
POS_SUBMISSIONS_FILE = "pos_submissions.csv"
UPLOAD_FOLDER = "student_uploads"
PROFILE_PIC_FOLDER = "profile_pics"
COMMITTEE_VERSIONS_FILE = "committee_versions.csv"
COMMITTEE_MEMBERS_FILE = "committee_members.csv"

for folder in [UPLOAD_FOLDER, PROFILE_PIC_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# ==================== COMMITTEE VERSION CONTROL ====================
def init_committee_tables():
    """Create CSV files if they don't exist."""
    if not os.path.exists(COMMITTEE_VERSIONS_FILE):
        df_ver = pd.DataFrame(columns=[
            "version_id", "student_number", "version_number", "gs_pdf_path",
            "verification_status", "verification_date", "verified_by", "remarks", "is_active", "created_at"
        ])
        df_ver.to_csv(COMMITTEE_VERSIONS_FILE, index=False)
    if not os.path.exists(COMMITTEE_MEMBERS_FILE):
        df_mem = pd.DataFrame(columns=[
            "member_id", "version_id", "role", "name"
        ])
        df_mem.to_csv(COMMITTEE_MEMBERS_FILE, index=False)

def get_next_version_id():
    df = pd.read_csv(COMMITTEE_VERSIONS_FILE)
    if df.empty:
        return 1
    return df["version_id"].max() + 1

def get_next_member_id():
    df = pd.read_csv(COMMITTEE_MEMBERS_FILE)
    if df.empty:
        return 1
    return df["member_id"].max() + 1

def save_committee_version(student_number, pdf_file, program_type, chair, co_chair, major_members, cognate_members):
    """
    program_type: 'MS' or 'PhD'
    major_members: list of strings (1-2)
    cognate_members: list of strings (1-2 for PhD, exactly 1 for MS)
    """
    # Basic validation
    if not chair.strip():
        return False, "Chair is required."
    if not major_members or len(major_members) == 0:
        return False, "At least one major member is required."
    if program_type == "MS":
        if len(major_members) > 1:
            return False, "Master's programs require exactly 1 major member."
        if len(cognate_members) != 1:
            return False, "Master's programs require exactly 1 minor/cognate member."
        total_members = 1 + (1 if co_chair.strip() else 0) + len(major_members) + len(cognate_members)
        if total_members < 3 or total_members > 4:
            return False, f"Master's committee must have 3-4 members (currently {total_members})."
    else:  # PhD
        if len(major_members) > 2:
            return False, "PhD programs allow at most 2 major members."
        if len(cognate_members) < 1 or len(cognate_members) > 2:
            return False, "PhD programs require 1-2 cognate members."
        total_members = 1 + (1 if co_chair.strip() else 0) + len(major_members) + len(cognate_members)
        if total_members < 4 or total_members > 5:
            return False, f"PhD committee must have 4-5 members (currently {total_members})."

    # Check for pending version (unchanged)
    df_ver = pd.read_csv(COMMITTEE_VERSIONS_FILE)
    pending = df_ver[(df_ver["student_number"] == student_number) & (df_ver["verification_status"] == "Pending")]
    if not pending.empty:
        return False, "You already have a pending committee version."

    # Determine version number
    student_versions = df_ver[df_ver["student_number"] == student_number]
    version_number = student_versions["version_number"].max() + 1 if not student_versions.empty else 1

    # Save PDF
    folder = os.path.join(UPLOAD_FOLDER, student_number, "committee")
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"committee_v{version_number}_{timestamp}.pdf"
    filepath = os.path.join(folder, filename)
    with open(filepath, "wb") as f:
        f.write(pdf_file.getbuffer())

    # Insert version record
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

    # Insert members
    df_mem = pd.read_csv(COMMITTEE_MEMBERS_FILE)
    # Chair
    new_mem = pd.DataFrame([{"member_id": get_next_member_id(), "version_id": version_id, "role": "Chair", "name": chair.strip()}])
    df_mem = pd.concat([df_mem, new_mem], ignore_index=True)
    # Co-chair (optional)
    if co_chair.strip():
        new_mem = pd.DataFrame([{"member_id": get_next_member_id(), "version_id": version_id, "role": "Co-chair", "name": co_chair.strip()}])
        df_mem = pd.concat([df_mem, new_mem], ignore_index=True)
    # Major members
    for i, name in enumerate(major_members):
        if name.strip():
            role = f"Member (Major {i+1})" if len(major_members) > 1 else "Member (Major)"
            new_mem = pd.DataFrame([{"member_id": get_next_member_id(), "version_id": version_id, "role": role, "name": name.strip()}])
            df_mem = pd.concat([df_mem, new_mem], ignore_index=True)
    # Cognate members
    for i, name in enumerate(cognate_members):
        if name.strip():
            role = f"Member (Cognate {i+1})" if program_type == "PhD" and len(cognate_members) > 1 else "Member (Cognate)"
            new_mem = pd.DataFrame([{"member_id": get_next_member_id(), "version_id": version_id, "role": role, "name": name.strip()}])
            df_mem = pd.concat([df_mem, new_mem], ignore_index=True)

    df_mem.to_csv(COMMITTEE_MEMBERS_FILE, index=False)
    return True, f"Committee version {version_number} submitted for adviser verification."

def get_committee_versions(student_number):
    df_ver = pd.read_csv(COMMITTEE_VERSIONS_FILE)
    df_ver = df_ver[df_ver["student_number"] == student_number].sort_values("version_number", ascending=False)
    return df_ver

def get_committee_members_for_version(version_id):
    df_mem = pd.read_csv(COMMITTEE_MEMBERS_FILE)
    return df_mem[df_mem["version_id"] == version_id][["role", "name"]]

def get_pending_committee_version(student_number):
    df_ver = pd.read_csv(COMMITTEE_VERSIONS_FILE)
    pending = df_ver[(df_ver["student_number"] == student_number) & (df_ver["verification_status"] == "Pending")]
    if pending.empty:
        return None
    return pending.iloc[0]

def get_active_committee_version(student_number):
    df_ver = pd.read_csv(COMMITTEE_VERSIONS_FILE)
    active = df_ver[(df_ver["student_number"] == student_number) & (df_ver["is_active"] == True)]
    if active.empty:
        return None
    return active.iloc[0]

def verify_committee_version(version_id, status, adviser_name, remarks):
    """
    status: 'Verified Correct' or 'Mismatch – Requires Correction'
    """
    if status not in ["Verified Correct", "Mismatch – Requires Correction"]:
        return False, "Invalid status."
    
    df_ver = pd.read_csv(COMMITTEE_VERSIONS_FILE)
    mask = df_ver["version_id"] == version_id
    if not mask.any():
        return False, "Version not found."
    
    row = df_ver[mask].iloc[0]
    if row["verification_status"] != "Pending":
        return False, f"Version is already {row['verification_status']}."
    
    df_ver.loc[mask, "verification_status"] = status
    df_ver.loc[mask, "verification_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df_ver.loc[mask, "verified_by"] = adviser_name
    df_ver.loc[mask, "remarks"] = remarks
    
    if status == "Verified Correct":
        # Set this version as active, deactivate all others for this student
        student_number = row["student_number"]
        df_ver.loc[df_ver["student_number"] == student_number, "is_active"] = False
        df_ver.loc[mask, "is_active"] = True
        
        # Update adviser to Chair of this version
        members = get_committee_members_for_version(version_id)
        chair_row = members[members["role"] == "Chair"]
        if not chair_row.empty:
            chair_name = chair_row.iloc[0]["name"]
            # Update students.csv
            df_students = load_data()
            idx = df_students[df_students["student_number"] == student_number].index
            if len(idx) > 0:
                df_students.loc[idx, "advisor"] = chair_name
                save_data(df_students)
        
        # Update milestone tracking
        df_students = load_data()
        student = df_students[df_students["student_number"] == student_number].iloc[0]
        prog_type = get_program_type(student["program"])
        milestone_name = None
        if prog_type == "MS_Thesis":
            milestone_name = "Guidance Committee Members"
        elif prog_type == "PhD_Regular" or prog_type == "PhD_Straight":
            milestone_name = "Advisory Committee Formation"
        elif prog_type == "PhD_Research":
            milestone_name = "Supervisory Committee Formation"
        else:
            milestone_name = "Guidance Committee Formation"  # fallback
        update_milestone(student_number, milestone_name, "Approved", date.today().strftime("%Y-%m-%d"), "", f"Committee verified by {adviser_name}", adviser_name)
    
    df_ver.to_csv(COMMITTEE_VERSIONS_FILE, index=False)
    return True, f"Committee version marked as {status}."

# ==================== OLD COMMITTEE HELPER (for backward compatibility, not used) ====================
def get_committee_members_old(student_number):
    # Kept for any legacy calls; not used in new UI
    return []

def set_committee_members_old(student_number, members):
    return False, "Deprecated. Use committee version control."

def get_committee_chair_old(student_number):
    active = get_active_committee_version(student_number)
    if active is not None:
        members = get_committee_members_for_version(active["version_id"])
        chair = members[members["role"] == "Chair"]
        if not chair.empty:
            return chair.iloc[0]["name"]
    return None

def is_committee_approved(student_number):
    active = get_active_committee_version(student_number)
    return active is not None and active["verification_status"] == "Verified Correct"

def check_committee_approval(student_number, semester_index):
    """Require committee approval before second semester."""
    if semester_index >= 1:  # second semester or later
        if not is_committee_approved(student_number):
            return False, "Your Guidance/Advisory Committee must be approved before you can enroll in the second semester. Please submit the Committee Nomination Form to the Graduate School."
    return True, ""

# ==================== POS SUBMISSIONS FUNCTIONS ====================
def load_pos_submissions():
    if not os.path.exists(POS_SUBMISSIONS_FILE) or os.path.getsize(POS_SUBMISSIONS_FILE) == 0:
        return pd.DataFrame(columns=["submission_id", "student_number", "file_path", "upload_date", "version", 
                                     "status", "approval_date", "approved_by", "remarks", "submission_type",
                                     "adviser_approved", "gs_approved"])
    df = pd.read_csv(POS_SUBMISSIONS_FILE, dtype=str)
    required_cols = ["submission_id", "student_number", "file_path", "upload_date", "version", "status", 
                     "approval_date", "approved_by", "remarks", "submission_type", "adviser_approved", "gs_approved"]
    for col in required_cols:
        if col not in df.columns:
            if col in ["adviser_approved", "gs_approved"]:
                df[col] = False
            else:
                df[col] = ""
    df["submission_id"] = pd.to_numeric(df["submission_id"], errors='coerce').fillna(0).astype(int)
    df["version"] = pd.to_numeric(df["version"], errors='coerce').fillna(0).astype(int)
    for bool_col in ["adviser_approved", "gs_approved"]:
        if bool_col in df.columns:
            df[bool_col] = df[bool_col].apply(lambda x: str(x).strip().lower() in ["true", "1", "yes"])
    if "submission_type" not in df.columns:
        df["submission_type"] = ""
    return df

def save_pos_submissions(df):
    df.to_csv(POS_SUBMISSIONS_FILE, index=False)

def get_pos_submissions(student_number):
    df = load_pos_submissions()
    return df[df["student_number"] == student_number].sort_values("submission_id", ascending=False)

def get_original_pos(student_number):
    df = load_pos_submissions()
    original = df[(df["student_number"] == student_number) & (df["version"] == 1) & (df["status"] == "Approved")]
    if original.empty:
        return None
    return original.iloc[0]

def get_revisions(student_number):
    df = load_pos_submissions()
    revisions = df[(df["student_number"] == student_number) & (df["version"] >= 2)]
    return revisions.sort_values("version", ascending=False)

def submit_pos_document(student_number, uploaded_file, submission_type="revision"):
    if uploaded_file is None:
        return False, "No file provided"
    df = load_pos_submissions()
    student_submissions = df[df["student_number"] == student_number]
    if student_submissions.empty:
        new_id = 1
        version = 1
        submission_type = "original"
    else:
        new_id = student_submissions["submission_id"].max() + 1
        version = len(student_submissions) + 1
    folder = os.path.join(UPLOAD_FOLDER, student_number, "pos_submissions")
    os.makedirs(folder, exist_ok=True)
    ext = uploaded_file.name.split('.')[-1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"POS_v{version}_{timestamp}.{ext}"
    filepath = os.path.join(folder, filename)
    try:
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
    except Exception as e:
        return False, f"Error saving file: {e}"
    new_row = pd.DataFrame([{
        "submission_id": new_id,
        "student_number": student_number,
        "file_path": filepath,
        "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": version,
        "status": "Pending",
        "approval_date": "",
        "approved_by": "",
        "remarks": "",
        "submission_type": submission_type,
        "adviser_approved": False,
        "gs_approved": False
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    save_pos_submissions(df)
    update_pos_milestone_status(student_number)
    return True, "Success"

def approve_pos_revision(submission_id, reviewer_name, remarks, role):
    df = load_pos_submissions()
    mask = df["submission_id"] == submission_id
    if not mask.any():
        return False, "Submission not found."
    row = df[mask].iloc[0]
    if role == "adviser":
        df.loc[mask, "adviser_approved"] = True
        df.loc[mask, "status"] = "Adviser Approved"
        df.loc[mask, "approved_by"] = reviewer_name
        df.loc[mask, "approval_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if remarks:
            df.loc[mask, "remarks"] = remarks
        save_pos_submissions(df)
        return True, "Revision approved by adviser. The student must now upload the GS-approved document to complete the process."
    else:
        return False, "Invalid role. Only adviser can approve the revision step."

def finalize_gs_approval(student_number, submission_id, remarks):
    df = load_pos_submissions()
    mask = df["submission_id"] == submission_id
    if not mask.any():
        return False, "Submission not found."
    if df.loc[mask, "adviser_approved"].iloc[0] != True:
        return False, "This revision has not been approved by the adviser yet."
    if df.loc[mask, "gs_approved"].iloc[0] == True:
        return False, "This revision is already GS approved."
    df.loc[mask, "gs_approved"] = True
    df.loc[mask, "status"] = "GS Approved"
    if remarks:
        df.loc[mask, "remarks"] = remarks
    save_pos_submissions(df)
    update_pos_milestone_status(student_number)
    return True, "GS approval recorded."

def reject_pos_submission(submission_id, reviewer_name, remarks):
    df = load_pos_submissions()
    mask = df["submission_id"] == submission_id
    if not mask.any():
        return False
    df.loc[mask, "status"] = "Rejected"
    df.loc[mask, "approval_date"] = ""
    df.loc[mask, "approved_by"] = reviewer_name
    if remarks:
        df.loc[mask, "remarks"] = remarks
    save_pos_submissions(df)
    student_number = df.loc[mask, "student_number"].iloc[0]
    update_pos_milestone_status(student_number)
    return True

def update_pos_milestone_status(student_number):
    submissions = get_pos_submissions(student_number)
    if submissions.empty:
        update_milestone_status_from_pos(student_number, "Not Started", "")
        return
    approved = submissions[submissions["status"] == "GS Approved"]
    if not approved.empty:
        latest_approved = approved.sort_values("submission_id", ascending=False).iloc[0]
        approval_date = latest_approved.get("approval_date", "")
        update_milestone_status_from_pos(student_number, "Approved", approval_date)
        df_students = load_data()
        idx = df_students[df_students["student_number"] == student_number].index
        if len(idx) > 0:
            df_students.at[idx[0], "pos_status"] = "Approved"
            df_students.at[idx[0], "pos_approval_date"] = approval_date
            save_data(df_students)
    elif any(submissions["status"] == "Pending"):
        update_milestone_status_from_pos(student_number, "Pending", "")
        df_students = load_data()
        idx = df_students[df_students["student_number"] == student_number].index
        if len(idx) > 0 and df_students.at[idx[0], "pos_status"] == "Approved":
            df_students.at[idx[0], "pos_status"] = "Pending"
            save_data(df_students)
    else:
        update_milestone_status_from_pos(student_number, "Not Started", "")

def update_milestone_status_from_pos(student_number, status, approval_date):
    df_milestone = load_milestone_tracking()
    mask = (df_milestone["student_number"] == student_number) & (df_milestone["milestone"] == "Plan of Study (POS)")
    if mask.any():
        idx = df_milestone[mask].index[0]
        df_milestone.loc[idx, "status"] = status
        if status == "Approved" and approval_date:
            df_milestone.loc[idx, "date"] = approval_date.split()[0] if approval_date else ""
        save_milestone_tracking(df_milestone)
    else:
        new_row = pd.DataFrame([{
            "student_number": student_number,
            "milestone": "Plan of Study (POS)",
            "status": status,
            "date": approval_date.split()[0] if approval_date else "",
            "file_path": "",
            "remarks": "",
            "reviewed_by": "",
            "review_date": ""
        }])
        df_milestone = pd.concat([df_milestone, new_row], ignore_index=True)
        save_milestone_tracking(df_milestone)

# ==================== CORE DATA FUNCTIONS ====================
def load_data():
    expected_columns = [
        "student_number", "password", "name", "last_name", "first_name", "middle_name",
        "program", "advisor", "ay_start", "semester", "gwa", "total_units_taken",
        "total_units_required", "thesis_units_taken", "thesis_units_limit",
        "thesis_extension_units", "residency_years_used", "residency_extension_years",
        "pos_status", "pos_approval_date", "qualifying_exam_status", "written_comprehensive_status",
        "oral_comprehensive_status", "general_exam_status", "final_exam_status",
        "final_exam_attempts", "profile_pic", "committee_members_structured", "committee_approval_date",
        "thesis_outline_approved", "thesis_status", "prior_ms_graduate", "student_status", "address",
        "phone", "institutional_email", "personal_email", "gender", "civil_status", "citizenship", "birthdate", "religion",
        "emergency_name", "emergency_relationship", "emergency_country_code", "emergency_phone",
        "special_status", "residency_max_years"
    ]
    numeric_cols = ["ay_start","gwa","total_units_taken","total_units_required",
                    "thesis_units_taken","thesis_units_limit","thesis_extension_units",
                    "residency_years_used","residency_extension_years","residency_max_years",
                    "final_exam_attempts"]
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        empty_df = pd.DataFrame(columns=expected_columns)
        for col in numeric_cols:
            if col in empty_df.columns:
                empty_df[col] = pd.to_numeric(empty_df[col], errors='coerce').fillna(0)
        save_data(empty_df)
        return empty_df
    try:
        df = pd.read_csv(DATA_FILE, dtype=str)
    except Exception:
        empty_df = pd.DataFrame(columns=expected_columns)
        for col in numeric_cols:
            if col in empty_df.columns:
                empty_df[col] = 0
        save_data(empty_df)
        return empty_df

    for col in expected_columns:
        if col not in df.columns:
            if col in numeric_cols:
                df[col] = 0
            elif col == "prior_ms_graduate":
                df[col] = False
            else:
                df[col] = ""

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            if col != "gwa":
                df[col] = df[col].astype(int)

    for col in df.columns:
        if col not in numeric_cols and col != "prior_ms_graduate":
            df[col] = df[col].fillna("").astype(str)

    df["prior_ms_graduate"] = df["prior_ms_graduate"].apply(lambda x: str(x).strip().lower() in ["true", "1", "yes"])

    for idx, row in df.iterrows():
        prog = row["program"]
        if prog and prog != "":
            df.at[idx, "residency_max_years"] = get_residency_max_from_program(prog)
            df.at[idx, "thesis_units_limit"] = get_thesis_limit_from_program(prog)
            req = get_required_units(prog, row.get("prior_ms_graduate", False))
            if req is not None:
                df.at[idx, "total_units_required"] = req

    save_data(df)
    return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# ==================== SEMESTER RECORDS ====================
def load_semester_records():
    if not os.path.exists(SEMESTER_FILE) or os.path.getsize(SEMESTER_FILE) == 0:
        return pd.DataFrame(columns=["student_number","academic_year","semester","subjects_json","total_units","gwa",
                                     "doc_path","doc_upload_time","doc_status","doc_remarks","doc_validated_by","doc_validated_time",
                                     "semester_status","pos_courses","pos_approved_status"])
    df = pd.read_csv(SEMESTER_FILE, dtype=str)
    required_cols = ["student_number","academic_year","semester","subjects_json","total_units","gwa",
                     "doc_path","doc_upload_time","doc_status","doc_remarks","doc_validated_by","doc_validated_time",
                     "semester_status","pos_courses","pos_approved_status"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""
    for col in ["total_units","gwa"]:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    text_cols = ["student_number","academic_year","semester","subjects_json","doc_path","doc_upload_time",
                 "doc_status","doc_remarks","doc_validated_by","doc_validated_time","semester_status","pos_courses","pos_approved_status"]
    for col in text_cols:
        df[col] = df[col].fillna("").astype(str)
    df["subjects_json"] = df["subjects_json"].apply(lambda x: x if x and x != "" else "[]")
    if "semester_status" not in df.columns:
        df["semester_status"] = "Regular"
    else:
        df["semester_status"] = df["semester_status"].fillna("Regular")
    if "pos_courses" not in df.columns:
        df["pos_courses"] = ""
    if "pos_approved_status" not in df.columns:
        df["pos_approved_status"] = ""
    return df

def save_semester_records(df):
    df.to_csv(SEMESTER_FILE, index=False)

def get_student_semesters(student_number):
    df = load_semester_records()
    return df[df["student_number"] == student_number].copy()

def compute_gwa_from_subjects(subjects_list):
    total_units = total_grade = 0
    for s in subjects_list:
        grade_val = s.get("grade", "")
        if grade_val in ["INC", "DRP", "P", "IP", "4.00"]:
            continue
        try:
            units = float(s.get("units",0))
            grade = float(grade_val)
            total_units += units
            total_grade += units * grade
        except:
            pass
    return total_grade/total_units if total_units>0 else 0.0

# ==================== POS CONSISTENCY FUNCTIONS ====================
def get_pos_for_semester(student_number, ay, sem):
    sems = load_semester_records()
    mask = (sems["student_number"] == student_number) & (sems["academic_year"] == ay) & (sems["semester"] == sem)
    if mask.any():
        row = sems[mask].iloc[0]
        pos_courses_str = row.get("pos_courses", "")
        if pos_courses_str and pos_courses_str.strip():
            try:
                return json.loads(pos_courses_str)
            except:
                return []
    return []

def set_pos_for_semester(student_number, ay, sem, course_codes_list, status, approver_name):
    sems = load_semester_records()
    mask = (sems["student_number"] == student_number) & (sems["academic_year"] == ay) & (sems["semester"] == sem)
    pos_json = json.dumps(course_codes_list) if course_codes_list else ""
    if mask.any():
        idx = sems[mask].index[0]
        sems.at[idx, "pos_courses"] = pos_json
        sems.at[idx, "pos_approved_status"] = status
    else:
        new_row = {
            "student_number": student_number,
            "academic_year": ay,
            "semester": sem,
            "subjects_json": "[]",
            "total_units": 0,
            "gwa": 0,
            "doc_path": "",
            "doc_upload_time": "",
            "doc_status": "",
            "doc_remarks": "",
            "doc_validated_by": "",
            "doc_validated_time": "",
            "semester_status": "Regular",
            "pos_courses": pos_json,
            "pos_approved_status": status
        }
        sems = pd.concat([sems, pd.DataFrame([new_row])], ignore_index=True)
    save_semester_records(sems)

def check_coursework_consistency(student_number, ay, sem):
    enrolled = []
    sems = load_semester_records()
    mask = (sems["student_number"] == student_number) & (sems["academic_year"] == ay) & (sems["semester"] == sem)
    if mask.any():
        row = sems[mask].iloc[0]
        try:
            subjects = json.loads(row["subjects_json"]) if row["subjects_json"] else []
            enrolled = [s.get("course_code", "").strip() for s in subjects if s.get("course_code")]
        except:
            enrolled = []
    approved = get_pos_for_semester(student_number, ay, sem)
    if not approved:
        return True, []
    mismatches = [code for code in enrolled if code not in approved]
    return len(mismatches) == 0, mismatches

# ==================== RULE FUNCTIONS (STRICT ENFORCEMENT) ====================
def check_pos_approval(student_number, semester_index):
    if semester_index >= 1:
        df = load_data()
        student = df[df["student_number"] == student_number]
        if student.empty:
            return False, "Student not found."
        pos_status = student.iloc[0].get("pos_status", "Pending")
        if pos_status != "Approved":
            return False, "Your Plan of Study (POS) must be approved before you can enroll in the second semester. Please work with your adviser to complete and approve your POS."
    return True, ""

def get_semester_index(student_number, ay, sem):
    df = load_data()
    student = df[df["student_number"] == student_number]
    if student.empty:
        return -1
    timeline = generate_timeline(student.iloc[0]["ay_start"], student.iloc[0]["semester"], student.iloc[0]["program"])
    for i, (t_ay, t_sem) in enumerate(timeline):
        if t_ay == ay and t_sem == sem:
            return i
    return -1

def check_thesis_units_limit(student_number, new_thesis_units):
    df = load_data()
    student = df[df["student_number"] == student_number].iloc[0]
    current = float(student["thesis_units_taken"]) if pd.notna(student["thesis_units_taken"]) else 0
    base_limit = get_thesis_limit_from_program(student["program"])
    extension = student.get("thesis_extension_units", 0)
    limit = base_limit + extension
    if current + new_thesis_units > limit:
        remaining = limit - current
        return False, f"Thesis unit limit would be exceeded: {current} + {new_thesis_units} > {limit}. Only {remaining} unit(s) remaining."
    return True, ""

def convert_expired_grades():
    semesters = load_semester_records()
    modified = False
    for idx, row in semesters.iterrows():
        try:
            subjects = json.loads(row["subjects_json"]) if row["subjects_json"] else []
        except:
            continue
        sem_date = row.get("doc_upload_time", "")
        if sem_date and sem_date != "":
            try:
                sem_end = datetime.strptime(sem_date, "%Y-%m-%d %H:%M:%S")
            except:
                sem_end = datetime.now()
        else:
            sem_end = datetime.now()
        deadline = sem_end + timedelta(days=365)
        changed = False
        for subj in subjects:
            grade = subj.get("grade", "")
            if grade in ["INC", "4.00"] and datetime.now() > deadline:
                subj["grade"] = "5.00"
                subj["remarks"] = f"Auto-converted from {grade} after 1 year"
                changed = True
                modified = True
        if changed:
            semesters.at[idx, "subjects_json"] = json.dumps(subjects)
    if modified:
        save_semester_records(semesters)
        for sn in semesters["student_number"].unique():
            update_student_academic_summary(sn)

def check_residency_enforcement(student_number):
    df = load_data()
    student = df[df["student_number"] == student_number].iloc[0]
    years_used = date.today().year - student["ay_start"]
    max_years = student.get("residency_max_years", 5)
    extension = student.get("residency_extension_years", 0)
    max_with_extension = max_years + extension
    if years_used > max_with_extension:
        return False, f"Residency exceeded: {years_used} > {max_with_extension} years. This student is no longer eligible to enroll."
    elif years_used > max_years and years_used <= max_with_extension:
        return "warning", f"Residency warning: {years_used} out of {max_years} years (extension granted: +{extension} years)."
    return True, ""

def check_residency_alert(student):
    years_used = date.today().year - student["ay_start"]
    max_years = student.get("residency_max_years", 5)
    extension = student.get("residency_extension_years", 0)
    max_with_extension = max_years + extension
    if years_used > max_with_extension:
        return "exceeded", years_used, max_with_extension
    elif years_used > max_years:
        return "warning_extension", years_used, max_with_extension
    elif years_used > max_years - 1:
        return "warning", years_used, max_years
    return "ok", years_used, max_years

def check_probationary_status(student_number):
    students = load_data()
    student = students[students["student_number"] == student_number].iloc[0]
    if student.get("student_status") != "Probationary":
        return
    sems = load_semester_records()
    sems = sems[(sems["student_number"] == student_number) & (sems["semester_status"] == "Regular")]
    if len(sems) == 0:
        return
    first_sem = sems.iloc[0]
    try:
        subjects = json.loads(first_sem["subjects_json"]) if first_sem["subjects_json"] else []
    except:
        subjects = []
    grades = [float(s["grade"]) for s in subjects if s.get("grade") and s["grade"] not in ["INC","DRP","P","IP","4.00"]]
    if not grades:
        return
    gwa = sum(grades) / len(grades)
    if gwa < 2.0:
        students.loc[students["student_number"] == student_number, "student_status"] = "Disqualified (Probation Failed)"
        students.loc[students["student_number"] == student_number, "special_status"] = "Inactive"
        save_data(students)
        return f"Student {student['name']} failed probation (GWA {gwa:.2f} < 2.0). Status set to Disqualified."

# ==================== SEMESTER & ACADEMIC FUNCTIONS (STRICT) ====================
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
    check_probationary_status(student_number)
    return gwa

def update_semester_subjects(student_number, ay, sem, subjects):
    sem_index = get_semester_index(student_number, ay, sem)
    if sem_index >= 1:
        ok, msg = check_committee_approval(student_number, sem_index)
        if not ok:
            st.error(msg)
            return False
        ok, msg = check_pos_approval(student_number, sem_index)
        if not ok:
            st.error(msg)
            return False
    ok, msg = check_residency_enforcement(student_number)
    if isinstance(ok, bool) and not ok:
        st.error(msg)
        return False

    df_sem = load_semester_records()
    mask = (df_sem["student_number"]==student_number) & (df_sem["academic_year"]==ay) & (df_sem["semester"]==sem)
    if not mask.any():
        return False
    idx = df_sem[mask].index[0]
    thesis_units = sum(float(s.get("units",0)) for s in subjects if "thesis" in s.get("course_code","").lower() or "dissertation" in s.get("course_code","").lower())
    if thesis_units > 0:
        ok, msg = check_thesis_units_limit(student_number, thesis_units)
        if not ok:
            st.error(msg)
            return False
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
    check_probationary_status(student_number)
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
    total_grade = 0.0
    total_units = 0
    thesis_units = 0
    error_occurred = False

    for _, row in sems.iterrows():
        if row["semester_status"] != "Regular":
            continue
        try:
            subjects = json.loads(row["subjects_json"]) if row["subjects_json"] else []
        except Exception as e:
            st.error(f"Error parsing subjects for {row['academic_year']} {row['semester']}: {e}")
            error_occurred = True
            continue

        for subj in subjects:
            grade_val = subj.get("grade", "")
            if grade_val in ["INC", "DRP", "P", "IP"]:
                continue
            try:
                units = float(subj.get("units", 0))
                total_units += units
            except Exception as e:
                st.error(f"Invalid units in {subj.get('course_code', '?')}: {e}")
                error_occurred = True
                continue
            try:
                grade_num = float(grade_val)
                if grade_num != 4.00:
                    total_grade += units * grade_num
            except ValueError:
                pass
            if "thesis" in subj.get("course_code", "").lower() or "dissertation" in subj.get("course_code", "").lower():
                try:
                    grade_num = float(grade_val)
                    if 1.0 <= grade_num <= 3.0:
                        thesis_units += units
                except:
                    pass

    df = load_data()
    idx = df[df["student_number"] == student_number].index
    if len(idx) > 0:
        if total_units > 0:
            new_gwa = total_grade / total_units
        else:
            new_gwa = None
        df.loc[idx, "total_units_taken"] = total_units
        df.loc[idx, "gwa"] = new_gwa
        df.loc[idx, "thesis_units_taken"] = thesis_units
        save_data(df)
        if error_occurred:
            st.warning("Totals recalculated with some errors. Please check semester subject data.")
        return True
    else:
        st.error(f"Student {student_number} not found.")
        return False

def get_next_semester_sequence(academic_year, semester):
    sem_order = ["1st Sem", "2nd Sem", "Summer"]
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
    if uploaded_file is None:
        return None
    ext = uploaded_file.name.split('.')[-1].lower()
    if ext not in ['jpg','jpeg','png','gif']:
        return None
    filename = f"{student_number}.{ext}"
    filepath = os.path.join(PROFILE_PIC_FOLDER, filename)
    try:
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
    except:
        return None
    return filename

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
    if not os.path.exists(MILESTONE_FILE) or os.path.getsize(MILESTONE_FILE) == 0:
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
                "remarks": "",
                "reviewed_by": "",
                "review_date": ""
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
                    "remarks": "",
                    "reviewed_by": "",
                    "review_date": ""
                })
        if new_rows:
            df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
            save_milestone_tracking(df)
        return df[df["student_number"] == student_number]

def update_milestone(student_number, milestone, status, date_str, file_path, remarks, reviewer_name=None):
    # This function is called by committee verification and other workflows
    df = load_milestone_tracking()
    mask = (df["student_number"] == student_number) & (df["milestone"] == milestone)
    if mask.any():
        df.loc[mask, "status"] = status
        if date_str:
            df.loc[mask, "date"] = str(date_str)
        if file_path:
            df.loc[mask, "file_path"] = str(file_path)
        if remarks:
            df.loc[mask, "remarks"] = str(remarks)
        if reviewer_name:
            df.loc[mask, "reviewed_by"] = str(reviewer_name)
            df.loc[mask, "review_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        new = pd.DataFrame([{
            "student_number": student_number,
            "milestone": milestone,
            "status": status,
            "date": date_str,
            "file_path": file_path,
            "remarks": remarks,
            "reviewed_by": reviewer_name if reviewer_name else "",
            "review_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S") if reviewer_name else ""
        }])
        df = pd.concat([df, new], ignore_index=True)
    save_milestone_tracking(df)
    return True, ""

def save_milestone_file(student_number, milestone_name, uploaded_file):
    if uploaded_file is None:
        return None
    folder = os.path.join(UPLOAD_FOLDER, student_number, "milestones")
    os.makedirs(folder, exist_ok=True)
    ext = uploaded_file.name.split('.')[-1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = milestone_name.replace(" ", "_").replace("/", "_")
    filename = f"{safe_name}_{timestamp}.{ext}"
    filepath = os.path.join(folder, filename)
    try:
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
    except Exception as e:
        st.error(f"Failed to save file: {e}")
        return None
    return filepath

# ==================== UI HELPERS ====================
def get_status_badge(status):
    if status == "Approved":
        return '<span class="status-badge status-approved">✅ Approved</span>'
    elif status == "Rejected":
        return '<span class="status-badge status-rejected">❌ Rejected</span>'
    elif status == "Pending":
        return '<span class="status-badge status-pending">🟡 Pending</span>'
    elif status == "Revision Requested":
        return '<span class="status-badge status-pending">📝 Revision Requested</span>'
    elif status == "Verified Correct":
        return '<span class="status-badge status-approved">✅ Verified Correct</span>'
    elif status == "Mismatch – Requires Correction":
        return '<span class="status-badge status-rejected">❌ Mismatch</span>'
    else:
        return '<span class="status-badge status-not-started">⚪ Not Started</span>'

def filter_dataframe(search_term, data):
    if data is None:
        return pd.DataFrame()
    if not search_term:
        return data
    mask = data["name"].str.contains(search_term, case=False, na=False) | data["student_number"].str.contains(search_term, case=False, na=False)
    return data[mask]

# ==================== RENDER SEMESTER BLOCK ====================
def render_semester_block_general(student_number, semester_row, is_staff=False, is_adviser=False):
    ay = str(semester_row["academic_year"])
    sem = str(semester_row["semester"])
    semester_status = str(semester_row.get("semester_status","Regular")).strip()
    if semester_status not in SEMESTER_STATUS_OPTIONS:
        semester_status = "Regular"
    try:
        subjects = json.loads(semester_row["subjects_json"]) if semester_row["subjects_json"] else []
    except:
        subjects = []
    total_units = float(semester_row["total_units"]) if pd.notna(semester_row["total_units"]) else 0.0
    gwa = float(semester_row["gwa"]) if pd.notna(semester_row["gwa"]) else 0.0
    doc_status = str(semester_row.get("doc_status","")).strip()
    doc_path = str(semester_row.get("doc_path","")).strip()
    doc_remarks = str(semester_row.get("doc_remarks","")).strip()
    
    pos_approved = semester_row.get("pos_approved_status", "") == "Approved"
    pos_courses_str = semester_row.get("pos_courses", "")
    pos_courses = []
    if pos_courses_str:
        try:
            pos_courses = json.loads(pos_courses_str)
        except:
            pass
    has_pos = len(pos_courses) > 0 and pos_approved
    
    if has_pos and semester_status == "Regular":
        consistent, mismatches = check_coursework_consistency(student_number, ay, sem)
        if not consistent:
            st.markdown('<div class="danger-banner">⚠️ Enrolled subjects do not match the approved Plan of Study (POS). Please consult your adviser.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="pos-match">✅ Enrolled subjects match the approved POS for this semester.</div>', unsafe_allow_html=True)
    elif semester_status == "Regular" and not pos_approved and semester_row.get("pos_courses", "") and semester_row.get("pos_courses", "") != "":
        st.info("📋 Plan of Study (POS) for this semester is pending approval. Courses will be validated after approval.")
    
    with st.expander(f"📅 {ay} | {sem} (Units: {total_units:.0f} | GWA: {gwa:.2f})", expanded=False):
        new_status = st.selectbox("Semester Status", SEMESTER_STATUS_OPTIONS,
                                  index=SEMESTER_STATUS_OPTIONS.index(semester_status) if semester_status in SEMESTER_STATUS_OPTIONS else 0,
                                  key=f"status_{student_number}_{ay}_{sem}",
                                  disabled=not (is_staff or is_adviser))
        if new_status != semester_status:
            if update_semester_status(student_number, ay, sem, new_status):
                st.success(f"Status updated to {new_status}.")
                st.rerun()
        
        st.markdown(f"**Document Validation:** {get_status_badge(doc_status)}", unsafe_allow_html=True)
        if doc_status == "Rejected" and doc_remarks:
            st.warning(f"Rejection reason: {doc_remarks}")
        
        if semester_status == "Regular":
            if st.session_state.role == "Student":
                df_edit = pd.DataFrame(subjects) if subjects else pd.DataFrame(columns=["course_code","course_description","units","grade"])
                for col in ["course_code","course_description","units","grade"]:
                    if col not in df_edit.columns:
                        df_edit[col] = 0 if col == "units" else ""
                df_edit = df_edit[["course_code","course_description","units","grade"]]
                df_edit["units"] = pd.to_numeric(df_edit["units"], errors='coerce').fillna(0).astype(int)
                
                df_key = f"df_{student_number}_{ay}_{sem}"
                if df_key not in st.session_state:
                    st.session_state[df_key] = df_edit.copy()
                
                edited_df = st.data_editor(
                    st.session_state[df_key],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "course_code": "Course Code",
                        "course_description": "Course Description",
                        "units": st.column_config.NumberColumn("Units", step=1, min_value=0),
                        "grade": st.column_config.SelectboxColumn("Grade", options=GRADE_OPTIONS, default="1.00")
                    },
                    key=f"editor_{student_number}_{ay}_{sem}"
                )
                st.session_state[df_key] = edited_df
                
                col_add, col_save = st.columns([1, 4])
                with col_add:
                    if st.button("➕ Add Row", key=f"add_{student_number}_{ay}_{sem}"):
                        new_row = pd.DataFrame([{"course_code": "", "course_description": "", "units": 0, "grade": "1.00"}])
                        st.session_state[df_key] = pd.concat([st.session_state[df_key], new_row], ignore_index=True)
                        st.rerun()
                with col_save:
                    if st.button("💾 Save Subjects", key=f"save_{student_number}_{ay}_{sem}"):
                        if not doc_path or doc_path == "":
                            st.error("❌ Cannot save subjects: Proof of grades (AMIS screenshot) is required. Please upload a file first.")
                        else:
                            sem_index = get_semester_index(student_number, ay, sem)
                            if sem_index >= 1:
                                ok, msg = check_committee_approval(student_number, sem_index)
                                if not ok:
                                    st.error(msg)
                                    st.stop()
                                ok, msg = check_pos_approval(student_number, sem_index)
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
                                update_student_academic_summary(student_number)
                                if df_key in st.session_state:
                                    del st.session_state[df_key]
                                st.rerun()
                            else:
                                st.error("Save failed.")
            else:
                if subjects:
                    df_subjects = pd.DataFrame(subjects)
                    display_cols = {}
                    if "course_code" in df_subjects.columns:
                        display_cols["course_code"] = "Course Code"
                    if "course_description" in df_subjects.columns:
                        display_cols["course_description"] = "Course Description"
                    if "units" in df_subjects.columns:
                        display_cols["units"] = "Units"
                    if "grade" in df_subjects.columns:
                        display_cols["grade"] = "Grade"
                    st.dataframe(df_subjects[list(display_cols.keys())].rename(columns=display_cols),
                                 use_container_width=True, hide_index=True)
                else:
                    st.info("No subjects have been entered for this semester.")
        elif semester_status != "Regular":
            st.info(f"Semester marked as **{semester_status}**. Subject input disabled.")
            if subjects:
                st.dataframe(pd.DataFrame(subjects), use_container_width=True, hide_index=True)
        else:
            st.info("Editing is disabled because you do not have permission.")
        
        st.markdown("---")
        st.markdown("**Upload Proof of Grades (AMIS Screenshot)**")
        if semester_status == "Regular":
            if doc_path and doc_path != "" and os.path.exists(doc_path):
                st.info(f"Current file: {os.path.basename(doc_path)}")
                if is_staff or is_adviser:
                    file_ext = os.path.splitext(doc_path)[1].lower()
                    if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                        st.image(doc_path, caption="Proof of Grades", width=400)
                    elif file_ext == '.pdf':
                        with open(doc_path, "rb") as f:
                            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="400" type="application/pdf"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)
                    else:
                        st.warning("Preview not available for this file type.")
                        with open(doc_path, "rb") as f:
                            st.download_button("Open file", f, file_name=os.path.basename(doc_path), key=f"fallback_{student_number}_{ay}_{sem}")
            if st.session_state.role == "Student":
                with st.form(key=f"upload_{student_number}_{ay}_{sem}"):
                    uploaded = st.file_uploader("Choose file (PDF/JPG/PNG)", type=["pdf","jpg","jpeg","png"], key=f"upload_file_{ay}_{sem}")
                    if st.form_submit_button("📎 Upload Document") and uploaded:
                        folder = os.path.join(UPLOAD_FOLDER, student_number, "semester_docs")
                        os.makedirs(folder, exist_ok=True)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{ay}_{sem}_{timestamp}.{uploaded.name.split('.')[-1].lower()}"
                        filepath = os.path.join(folder, filename)
                        try:
                            with open(filepath, "wb") as f:
                                f.write(uploaded.getbuffer())
                            if update_semester_document(student_number, ay, sem, filepath, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Pending"):
                                st.success("Document uploaded! Pending validation.")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Upload failed: {e}")
            elif is_adviser and doc_status == "Pending":
                with st.form(key=f"validate_{student_number}_{ay}_{sem}"):
                    remarks_val = st.text_area("Remarks", key=f"val_remarks_{student_number}_{ay}_{sem}")
                    col1, col2 = st.columns(2)
                    if col1.form_submit_button("✅ Approve"):
                        validate_semester_document(student_number, ay, sem, "Approved", remarks_val, st.session_state.display_name)
                        st.success("Approved.")
                        st.rerun()
                    if col2.form_submit_button("❌ Reject"):
                        validate_semester_document(student_number, ay, sem, "Rejected", remarks_val, st.session_state.display_name)
                        st.warning("Rejected.")
                        st.rerun()
        else:
            st.info(f"Semester status **{semester_status}** – no upload required.")
        
        if st.session_state.role == "SESAM Staff":
            st.markdown("---")
            st.markdown("#### 📋 Plan of Study (POS) for this Semester")
            pos_status = semester_row.get("pos_approved_status", "")
            if pos_status == "Approved":
                st.success("✅ This semester's POS is approved.")
                if pos_courses:
                    st.write("**Approved courses:**", ", ".join(pos_courses))
                else:
                    st.info("No specific courses listed in POS (free elective semester).")
            else:
                if pos_status == "Pending":
                    st.warning("POS Pending approval.")
                else:
                    st.info("No POS submitted for this semester yet.")
            with st.expander("✏️ Edit POS (Administrative Only)"):
                current_codes = pos_courses if pos_courses else []
                pos_codes_input = st.text_input("Course codes (comma-separated)", value=", ".join(current_codes), key=f"pos_edit_{student_number}_{ay}_{sem}")
                new_approval_status = st.selectbox("Approval Status", ["Pending", "Approved", "Rejected"], index=["Pending","Approved","Rejected"].index(pos_status) if pos_status in ["Pending","Approved","Rejected"] else 0, key=f"pos_status_{student_number}_{ay}_{sem}")
                if st.button("Save POS Changes", key=f"save_pos_{student_number}_{ay}_{sem}"):
                    new_codes = [c.strip() for c in pos_codes_input.split(",") if c.strip()]
                    set_pos_for_semester(student_number, ay, sem, new_codes, new_approval_status, st.session_state.display_name)
                    st.success("POS updated.")
                    st.rerun()

# ==================== REGISTRATION FORM ====================
def register_new_student_form():
    if st.session_state.get("reg_success", False):
        st.success("✅ Student successfully registered!")
        st.session_state.reg_success = False

    with st.form("register_student_form"):
        st.subheader("➕ Enroll an Admitted Student")
        st.info("ℹ️ **For Staff Use Only:** This function is used to create a record for an officially admitted student. Please verify the student's Notice of Admission (NOA) and complete the details below.")
        
        col1, col2 = st.columns(2)
        with col1:
            student_number = st.text_input("Student Number *")
            last_name = st.text_input("Last Name *")
            first_name = st.text_input("First Name *")
            middle_name = st.text_input("Middle Name (optional)")
            personal_email = st.text_input("Personal Email Address (from NOA) *")
        with col2:
            program = st.selectbox("Program *", PROGRAMS)
            ay_sel = st.selectbox("Admission Academic Year *", ACADEMIC_YEARS)
            ay_start = int(ay_sel.split("-")[0])
            semester = st.selectbox("Starting Semester *", SEMESTERS)
            student_status = st.selectbox("Student Status", ["Regular", "Probationary", "Conditional"])
        advisor = st.selectbox("Temporary Adviser", ["Dr. Uno", "Dr. Dos", "Dr. Eslava", "Dr. Sanchez"])
        prior_ms = False
        if program == "PhD Environmental Science":
            prior_ms = st.checkbox("Student is an MS Environmental Science graduate")
        
        submitted = st.form_submit_button("Register Student", use_container_width=True)
        
        if submitted:
            errors = []
            if not student_number: errors.append("Student Number")
            if not last_name: errors.append("Last Name")
            if not first_name: errors.append("First Name")
            if not program: errors.append("Program")
            if not ay_sel: errors.append("Academic Year")
            if not semester: errors.append("Semester")
            if not personal_email: errors.append("Personal Email Address")
            df = load_data()
            if student_number in df["student_number"].values: errors.append("Student number already exists")
            if errors:
                st.error(f"Missing or invalid: {', '.join(errors)}")
            else:
                full_name = f"{last_name}, {first_name} {middle_name}".strip()
                req_units = get_required_units(program, prior_ms)
                new_row = {
                    "student_number": student_number,
                    "password": student_number,
                    "name": full_name,
                    "last_name": last_name,
                    "first_name": first_name,
                    "middle_name": middle_name,
                    "program": program,
                    "advisor": advisor,
                    "ay_start": ay_start,
                    "semester": semester,
                    "gwa": None,
                    "total_units_taken": 0,
                    "total_units_required": req_units if req_units else 24,
                    "thesis_units_taken": 0,
                    "thesis_units_limit": get_thesis_limit_from_program(program),
                    "thesis_extension_units": 0,
                    "residency_years_used": 0,
                    "residency_extension_years": 0,
                    "residency_max_years": get_residency_max_from_program(program),
                    "pos_status": "Not Started",
                    "pos_approval_date": "",
                    "qualifying_exam_status": "N/A",
                    "written_comprehensive_status": "N/A",
                    "oral_comprehensive_status": "N/A",
                    "general_exam_status": "Not Taken",
                    "final_exam_status": "Not Taken",
                    "final_exam_attempts": 0,
                    "profile_pic": "",
                    "committee_members_structured": "",
                    "committee_approval_date": "",
                    "thesis_outline_approved": "No",
                    "thesis_status": "Not Started",
                    "prior_ms_graduate": prior_ms,
                    "student_status": student_status,
                    "address": "",
                    "phone": "",
                    "institutional_email": "",
                    "personal_email": personal_email,
                    "gender": "",
                    "civil_status": "",
                    "citizenship": "",
                    "birthdate": "",
                    "religion": "",
                    "emergency_name": "",
                    "emergency_relationship": "",
                    "emergency_country_code": "",
                    "emergency_phone": "",
                    "special_status": "Regular"
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                get_student_milestones(student_number, get_program_type(program))
                try:
                    add_semester_record(student_number, f"{ay_start}-{ay_start+1}", semester, [], semester_status="Regular")
                    send_welcome_email(student_number, personal_email, full_name)
                    st.session_state.reg_success = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not create initial semester: {e}")

# ==================== GET INC/4.0 ALERTS ====================
def get_inc_alert(student_number):
    sems = load_semester_records()
    sems = sems[sems["student_number"] == student_number]
    alerts = []
    for _, row in sems.iterrows():
        try:
            subjects = json.loads(row["subjects_json"]) if row["subjects_json"] else []
        except:
            continue
        sem_date = row.get("doc_upload_time", "")
        if sem_date and sem_date != "":
            try:
                sem_end = datetime.strptime(sem_date, "%Y-%m-%d %H:%M:%S")
            except:
                sem_end = datetime.now()
        else:
            sem_end = datetime.now()
        deadline = sem_end + timedelta(days=365)
        for subj in subjects:
            grade = subj.get("grade", "")
            if grade in ["INC","4.00"]:
                days_left = (deadline - datetime.now()).days
                alerts.append({
                    "course": subj.get("course_code", "Unknown"),
                    "semester": f"{row['academic_year']} {row['semester']}",
                    "deadline": deadline.strftime("%Y-%m-%d"),
                    "days_left": days_left,
                    "status": "expired" if days_left < 0 else "warning" if days_left < 60 else "ok"
                })
    return alerts

# ==================== PROFILE CONTENT RENDERER ====================
def render_compact_profile(student, is_own_profile=True):
    col_left, col_right = st.columns([1, 3])
    with col_left:
        pic_path = get_profile_picture_path(student["student_number"])
        if pic_path:
            st.image(pic_path, width=150)
        else:
            st.info("No profile picture")
        if is_own_profile:
            uploaded_pic = st.file_uploader("Update picture", type=["jpg","jpeg","png"], key=f"pic_{student['student_number']}")
            if uploaded_pic:
                fn = save_profile_picture(student["student_number"], uploaded_pic)
                if fn:
                    df = load_data()
                    df.loc[df["student_number"]==student["student_number"], "profile_pic"] = fn
                    save_data(df)
                    st.success("Picture updated.")
                    st.rerun()
            if st.button("Delete picture", key=f"del_pic_{student['student_number']}"):
                if delete_profile_picture(student["student_number"]):
                    df = load_data()
                    df.loc[df["student_number"]==student["student_number"], "profile_pic"] = ""
                    save_data(df)
                    st.success("Picture deleted.")
                    st.rerun()
    with col_right:
        st.markdown(f"### {student['name']}")
        st.caption(f"**Student Number:** {student['student_number']}")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**Program:** {student['program']}")
            st.markdown(f"**Temporary Adviser (assigned upon admission):** {student['advisor']}")
            st.markdown(f"**Admitted:** {format_ay(student['ay_start'], student['semester'])}")
        with col_b:
            st.markdown(f"**Required Units:** {student['total_units_required']}")
            st.markdown(f"**Special Status:** {student.get('special_status','Regular')}")
        
        if student.get("pos_status") == "Approved" and student.get("pos_approval_date"):
            st.caption(f"✅ POS approved on: {student['pos_approval_date']}")
    
    st.markdown("---")
    st.markdown("#### 📞 Contact & Personal Information")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Address:** {student['address'] or '—'}")
        st.markdown(f"**Phone:** {student['phone'] or '—'}")
        st.markdown(f"**Personal Email:** {student['personal_email'] or '—'}")
        st.markdown(f"**Institutional Email (UP mail):** {student['institutional_email'] or '—'}")
    with col2:
        st.markdown(f"**Gender:** {student['gender'] or '—'}")
        st.markdown(f"**Civil Status:** {student['civil_status'] or '—'}")
        st.markdown(f"**Citizenship:** {student['citizenship'] or '—'}")
    with col3:
        st.markdown(f"**Birthdate:** {student['birthdate'] or '—'}")
        st.markdown(f"**Religion:** {student['religion'] or '—'}")
    
    st.markdown("---")
    st.markdown("#### 🚨 Emergency Contact")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.markdown(f"**Name:** {student['emergency_name'] or '—'}")
        st.markdown(f"**Relationship:** {student['emergency_relationship'] or '—'}")
    with col_e2:
        st.markdown(f"**Phone:** {student['emergency_country_code'] or ''} {student['emergency_phone'] or ''}")

# ==================== POS MILESTONE RENDERER ====================
def render_pos_milestone(student_number, viewer_role, is_own_view=False):
    if "_pos_form_counter" not in st.session_state:
        st.session_state._pos_form_counter = 0
    st.session_state._pos_form_counter += 1
    form_suffix = st.session_state._pos_form_counter

    original = get_original_pos(student_number)
    revisions = get_revisions(student_number)
    
    can_submit = (is_own_view or st.session_state.role == "SESAM Staff")
    is_adviser = (viewer_role == "Faculty Adviser")
    is_staff = (viewer_role == "SESAM Staff")
    
    st.markdown("## Plan of Study (POS) – Version Control")
    
    col_left, col_right = st.columns(2, gap="large")
    
    with col_left:
        st.markdown("### 🏛️ Original Approved POS (Graduate School Baseline)")
        st.caption("Official GS‑approved document – read only for adviser")
        
        if original is None:
            if can_submit:
                st.warning("No original POS has been submitted yet. Please upload the initial POS for GS approval.")
                with st.form(key=f"submit_original_{student_number}_{form_suffix}"):
                    uploaded_file = st.file_uploader("Upload initial POS (PDF/JPG/PNG) - Max 5MB", type=["pdf","jpg","jpeg","png"], key=f"original_pos_{student_number}_{form_suffix}")
                    if st.form_submit_button("Submit Initial POS for GS Approval", use_container_width=True):
                        if uploaded_file:
                            if uploaded_file.size > 5 * 1024 * 1024:
                                st.error("File size exceeds 5MB.")
                            else:
                                success, msg = submit_pos_document(student_number, uploaded_file, submission_type="original")
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                        else:
                            st.error("Please select a file.")
            else:
                st.info("No original POS document has been approved by the Graduate School yet.")
        else:
            st.success(f"✅ GS Approved on: {original['approval_date']}")
            if original["file_path"] and os.path.exists(original["file_path"]):
                with open(original["file_path"], "rb") as f:
                    st.download_button("📎 Download Original POS", f, file_name=os.path.basename(original["file_path"]))
            else:
                st.info("Document file not available.")
            
            if is_adviser and not is_own_view:
                st.markdown("---")
                st.markdown("#### Verification")
                if "original_verified" not in st.session_state:
                    st.session_state.original_verified = False
                if not st.session_state.original_verified:
                    if st.button("✅ Mark as Verified (I have reviewed the original POS)"):
                        st.session_state.original_verified = True
                        st.success("You have verified the original POS. Thank you.")
                else:
                    st.info("You have already verified this original POS.")
    
    with col_right:
        st.markdown("### 📝 Revised POS (Updated Versions)")
        st.caption("Student proposes changes → Adviser approves → Student uploads GS-approved document")
        
        if revisions.empty:
            st.info("No revised POS submissions yet.")
        else:
            for _, rev in revisions.iterrows():
                with st.container():
                    st.markdown(f"**Version {rev['version']}** – Uploaded: {rev['upload_date']}")
                    status = rev["status"]
                    if status == "Pending":
                        st.warning("🟡 Status: Pending (Awaiting Adviser Review)")
                    elif status == "Adviser Approved":
                        st.info("🔵 Status: Adviser Approved – Student must upload the GS-approved document")
                    elif status == "GS Approved":
                        st.success("✅ Status: GS Approved")
                    elif status == "Rejected":
                        st.error("❌ Status: Rejected")
                    else:
                        st.write(f"Status: {status}")
                    
                    if rev["remarks"]:
                        st.caption(f"Remarks: {rev['remarks']}")
                    if rev["file_path"] and os.path.exists(rev["file_path"]):
                        with open(rev["file_path"], "rb") as f:
                            st.download_button("📎 Download", f, file_name=os.path.basename(rev["file_path"]), key=f"download_rev_{rev['submission_id']}_{form_suffix}")
                    
                    if is_adviser and status == "Pending":
                        with st.form(key=f"adviser_rev_{rev['submission_id']}_{form_suffix}"):
                            remarks = st.text_area("Remarks (optional)", key=f"rev_remarks_{rev['submission_id']}_{form_suffix}")
                            if st.form_submit_button("✅ Approve Revision", use_container_width=True):
                                success, msg = approve_pos_revision(rev['submission_id'], st.session_state.display_name, remarks, "adviser")
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                            if st.form_submit_button("❌ Reject", use_container_width=True):
                                if reject_pos_submission(rev['submission_id'], st.session_state.display_name, remarks):
                                    st.warning("Revision rejected.")
                                    st.rerun()
                                else:
                                    st.error("Rejection failed.")
                    
                    if is_own_view and status == "Adviser Approved" and rev.get("gs_approved") == False:
                        with st.form(key=f"student_gs_upload_{rev['submission_id']}_{form_suffix}"):
                            st.info("Your adviser has approved the revision. Please upload the official GS-approved POS document to complete the process.")
                            uploaded_file = st.file_uploader("Upload GS-approved POS (PDF/JPG/PNG)", type=["pdf","jpg","jpeg","png"], key=f"gs_upload_{rev['submission_id']}_{form_suffix}")
                            if st.form_submit_button("Submit GS-Approved Document", use_container_width=True):
                                if uploaded_file:
                                    folder = os.path.join(UPLOAD_FOLDER, student_number, "pos_submissions")
                                    os.makedirs(folder, exist_ok=True)
                                    ext = uploaded_file.name.split('.')[-1].lower()
                                    filename = f"POS_v{rev['version']}_GSApproved_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
                                    filepath = os.path.join(folder, filename)
                                    with open(filepath, "wb") as f:
                                        f.write(uploaded_file.getbuffer())
                                    success, msg = finalize_gs_approval(student_number, rev['submission_id'], "Student uploaded GS-approved document")
                                    if success:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                                else:
                                    st.error("Please select a file.")
        
        if can_submit:
            st.markdown("---")
            st.markdown("### 📤 Submit Revised POS")
            with st.form(key=f"submit_revision_{student_number}_{form_suffix}"):
                uploaded_file = st.file_uploader("Upload proposed revised POS (PDF/JPG/PNG) - Max 5MB", type=["pdf","jpg","jpeg","png"], key=f"revised_pos_{student_number}_{form_suffix}")
                if st.form_submit_button("Submit Revised Version for Adviser Approval", use_container_width=True):
                    if uploaded_file:
                        if uploaded_file.size > 5 * 1024 * 1024:
                            st.error("File size exceeds 5MB.")
                        else:
                            success, msg = submit_pos_document(student_number, uploaded_file, submission_type="revision")
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        st.error("Please select a file.")
    
    st.markdown("---")
    st.caption("Note: The original POS is the first version approved by GS. Revisions go through Adviser approval, then student uploads the GS-approved document.")

# ==================== UNIFIED STUDENT PROFILE VIEW ====================
def view_student_profile(student_number, viewer_role):
    df = load_data()
    student = df[df["student_number"] == student_number].iloc[0].copy()
    program_type = get_program_type(student["program"])
    
    is_staff = (viewer_role == "SESAM Staff")
    is_adviser = (viewer_role == "Faculty Adviser" and student["advisor"] == st.session_state.display_name)
    
    resid_status, used, max_y = check_residency_alert(student)
    if resid_status == "exceeded":
        st.markdown(f'<div class="danger-banner">⚠️ RESIDENCY EXCEEDED: {used} years used (max {max_y}). Student is no longer eligible to enroll.</div>', unsafe_allow_html=True)
    elif resid_status == "warning":
        st.markdown(f'<div class="warning-banner">⚠️ Residency warning: {used} out of {max_y} years used. Only one year remaining.</div>', unsafe_allow_html=True)
    elif resid_status == "warning_extension":
        st.markdown(f'<div class="warning-banner">⚠️ Residency extended: {used} out of {max_y} years. Extension active.</div>', unsafe_allow_html=True)
    
    inc_items = get_inc_alert(student_number)
    for inc in inc_items:
        if inc["status"] == "expired":
            st.markdown(f'<div class="danger-banner">❌ {inc["course"]} ({inc["semester"]}) INC/4.0 expired on {inc["deadline"]}. Auto-converted to 5.00.</div>', unsafe_allow_html=True)
        elif inc["status"] == "warning":
            st.markdown(f'<div class="warning-banner">⚠️ {inc["course"]} ({inc["semester"]}) INC/4.0 deadline in {inc["days_left"]} days ({inc["deadline"]}).</div>', unsafe_allow_html=True)
    
    st.markdown(f"## {student['name']} ({student_number})")
    back_button_text = "← Back to Student List" if is_staff else "← Back to Advisee List"
    if st.button(back_button_text):
        if is_staff:
            st.session_state.staff_selected_student = None
            st.session_state.staff_show_update = True
        else:
            st.session_state.adviser_selected_student = None
        st.rerun()
    
    milestone_list = MILESTONE_DEFS.get(program_type, MILESTONE_DEFS["MS_Thesis"])
    tab_names = ["👤 My Profile", "📚 Coursework"] + milestone_list
    if is_staff:
        tab_names.append("⚙️ Admin & Extensions")
    tabs = st.tabs(tab_names)
    
    with tabs[0]:
        render_compact_profile(student, is_own_profile=(viewer_role == "Student"))
        if is_staff:
            st.markdown("---")
            st.markdown("#### 📝 Edit Personal Information (Staff Only)")
            with st.form("staff_edit_profile"):
                new_address = st.text_input("Address", value=student.get("address",""))
                new_phone = st.text_input("Phone", value=student.get("phone",""))
                new_institutional_email = st.text_input("Institutional Email (UP mail)", value=student.get("institutional_email",""))
                new_gender = st.selectbox("Gender", ["", "Male", "Female", "Other"], index=["", "Male", "Female", "Other"].index(student.get("gender","")) if student.get("gender","") in ["", "Male", "Female", "Other"] else 0)
                new_civil = st.selectbox("Civil Status", ["", "Single", "Married", "Divorced", "Widowed"], index=["", "Single", "Married", "Divorced", "Widowed"].index(student.get("civil_status","")) if student.get("civil_status","") in ["", "Single", "Married", "Divorced", "Widowed"] else 0)
                if st.form_submit_button("Update Personal Information"):
                    df = load_data()
                    idx = df[df["student_number"] == student_number].index
                    if len(idx) > 0:
                        df.at[idx[0], "address"] = new_address
                        df.at[idx[0], "phone"] = new_phone
                        df.at[idx[0], "institutional_email"] = new_institutional_email
                        df.at[idx[0], "gender"] = new_gender
                        df.at[idx[0], "civil_status"] = new_civil
                        save_data(df)
                        st.success("Information updated.")
                        st.rerun()
    
    with tabs[1]:
        st.subheader("Academic Record")
        
        timeline = generate_timeline(student["ay_start"], student["semester"], student["program"])
        total_terms = len(timeline)
        existing_sems = get_student_semesters(student_number)
        
        semesters = get_student_semesters(student_number)
        if not semesters.empty:
            sem_order = {"1st Sem": 0, "2nd Sem": 1, "Summer": 2}
            semesters["order"] = semesters["semester"].map(sem_order)
            semesters["ay_num"] = semesters["academic_year"].apply(lambda x: int(x.split("-")[0]))
            semesters = semesters.sort_values(["ay_num", "order"]).reset_index(drop=True)
        
        for _, row in semesters.iterrows():
            render_semester_block_general(student_number, row, is_staff=is_staff, is_adviser=is_adviser)
        
        can_add_semester = (st.session_state.role == "Student") or is_staff
        if can_add_semester and len(semesters) < total_terms:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("➕ Add Next Semester"):
                    if st.session_state.role == "Student":
                        sem_index = len(semesters)
                        ok, msg = check_committee_approval(student_number, sem_index)
                        if not ok:
                            st.error(msg)
                        else:
                            ok, msg = check_pos_approval(student_number, sem_index)
                            if not ok:
                                st.error(msg)
                            else:
                                last_sem = semesters.iloc[-1] if not semesters.empty else None
                                if last_sem is not None:
                                    create_next_semester(student_number, last_sem["academic_year"], last_sem["semester"])
                                else:
                                    create_next_semester(student_number, timeline[0][0], timeline[0][1])
                                st.rerun()
                    else:
                        sem_index = len(semesters)
                        ok, msg = check_committee_approval(student_number, sem_index)
                        if not ok:
                            st.error(msg)
                        else:
                            ok, msg = check_pos_approval(student_number, sem_index)
                            if not ok:
                                st.error(msg)
                            else:
                                last_sem = semesters.iloc[-1] if not semesters.empty else None
                                if last_sem is not None:
                                    create_next_semester(student_number, last_sem["academic_year"], last_sem["semester"])
                                else:
                                    create_next_semester(student_number, timeline[0][0], timeline[0][1])
                                st.rerun()
            with col2:
                if st.button("📅 Create All Missing Semesters (Bulk)") and is_staff:
                    for ay, sem in timeline:
                        if not ((existing_sems["academic_year"] == ay) & (existing_sems["semester"] == sem)).any():
                            try:
                                add_semester_record(student_number, ay, sem, [], semester_status="Regular")
                            except ValueError as e:
                                st.error(f"Could not create {ay} {sem}: {e}")
                                break
                    st.success("All missing semesters created (where allowed by policy).")
                    st.rerun()
        elif can_add_semester:
            st.success("✅ All required semesters have been created. Student may still need to enroll in subjects.")
        
        st.markdown("---")
        cola, colb, colc, cold = st.columns(4)
        cola.metric("Units Taken", student["total_units_taken"])
        colb.metric("Required Units", student["total_units_required"])
        colc.metric("Remaining", max(0, student["total_units_required"] - student["total_units_taken"]))
        gwa_val = student["gwa"] if pd.notna(student["gwa"]) else None
        cold.metric("Cumulative GWA", f"{gwa_val:.2f}" if gwa_val is not None else "—")
    
    # Milestone Tabs
    milestones_df = get_student_milestones(student_number, program_type)
    for i, milestone_name in enumerate(milestone_list):
        with tabs[2 + i]:
            if milestone_name == "Plan of Study (POS)":
                render_pos_milestone(student_number, viewer_role, is_own_view=(viewer_role == "Student"))
            else:
                # Replace committee milestone with new version-controlled UI
                if milestone_name in ["Guidance Committee Members", "Guidance Committee Formation", "Advisory Committee Formation", "Supervisory Committee Formation"]:
                    st.markdown(f"### {milestone_name}")
                    
                    # Determine the appropriate committee milestone name for display
                    committee_milestone_display = milestone_name
                    
                    # Show current active committee if any
                    active = get_active_committee_version(student_number)
                    if active is not None:
                        st.success(f"**Active Committee (Version {active['version_number']})** – Verified on {active['verification_date']} by {active['verified_by']}")
                        with st.expander("View Active Committee Details"):
                            members = get_committee_members_for_version(active['version_id'])
                            st.dataframe(members)
                            st.markdown(f"[View GS PDF]({active['gs_pdf_path']})")
                    else:
                        st.info("No active committee approved yet.")
                    
                    # Show pending version for adviser verification
                    pending = get_pending_committee_version(student_number)
                    if pending is not None:
                        st.warning(f"**Pending Committee Version {pending['version_number']}** – Submitted on {pending['created_at']}")
                        with st.expander("Review Pending Committee"):
                            members = get_committee_members_for_version(pending['version_id'])
                            st.dataframe(members)
                            st.markdown(f"[View GS PDF]({pending['gs_pdf_path']})")
                            if is_adviser:
                                with st.form(key=f"verify_committee_{pending['version_id']}"):
                                    remarks = st.text_area("Remarks (required if mismatch)")
                                    col1, col2 = st.columns(2)
                                    if col1.form_submit_button("✅ Verified Correct"):
                                        success, msg = verify_committee_version(pending['version_id'], "Verified Correct", st.session_state.display_name, remarks)
                                        if success:
                                            st.success(msg)
                                            st.rerun()
                                        else:
                                            st.error(msg)
                                    if col2.form_submit_button("❌ Mismatch – Requires Correction"):
                                        if not remarks:
                                            st.error("Please provide remarks explaining the mismatch.")
                                        else:
                                            success, msg = verify_committee_version(pending['version_id'], "Mismatch – Requires Correction", st.session_state.display_name, remarks)
                                            if success:
                                                st.warning(msg)
                                                st.rerun()
                                            else:
                                                st.error(msg)
                            else:
                                st.info("Awaiting adviser verification.")
                    
                    # Student submission form (only if no pending version)
                    if viewer_role == "Student" and pending is None:
                        with st.form(key="submit_committee_version"):
                            st.markdown("#### Submit New Committee (GS-Approved)")
                            uploaded_pdf = st.file_uploader("GS‑approved Committee Form (PDF)", type=["pdf"])
                            st.markdown("**Committee Members**")
                            chair = st.text_input("Chair (required)")
                            co_chair = st.text_input("Co‑chair (optional)")
                            major_member = st.text_input("Member (Major) – required")
                            cognate1 = st.text_input("Member (Cognate 1) – required")
                            cognate2 = st.text_input("Member (Cognate 2) – required")
                            if st.form_submit_button("Submit Committee for Verification"):
                                if not uploaded_pdf or not chair or not major_member or not cognate1 or not cognate2:
                                    st.error("Please fill all required fields and upload the GS‑approved PDF.")
                                else:
                                    members_dict = {
                                        'chair': chair,
                                        'co_chair': co_chair,
                                        'member_major': major_member,
                                        'member_cognate1': cognate1,
                                        'member_cognate2': cognate2
                                    }
                                    success, msg = save_committee_version(student_number, uploaded_pdf, members_dict)
                                    if success:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                    
                    # Show version history
                    versions = get_committee_versions(student_number)
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
                    # Non-committee milestone (unchanged from previous version)
                    milestone_filtered = milestones_df[milestones_df["milestone"] == milestone_name]
                    if milestone_filtered.empty:
                        st.error(f"Milestone '{milestone_name}' not found in records.")
                        continue
                    milestone_row = milestone_filtered.iloc[0]
                    status = milestone_row["status"]
                    date_val = milestone_row["date"]
                    file_path = milestone_row["file_path"]
                    remarks = milestone_row["remarks"]
                    reviewed_by = milestone_row.get("reviewed_by", "")
                    review_date = milestone_row.get("review_date", "")
                    
                    st.markdown(f"### {milestone_name}")
                    st.markdown(get_status_badge(status), unsafe_allow_html=True)
                    if date_val:
                        st.write(f"**Date of approval:** {date_val}")
                    if reviewed_by and status == "Approved":
                        st.caption(f"Approved by: {reviewed_by} on {review_date}")
                    
                    if file_path and file_path != "" and os.path.exists(file_path):
                        with st.expander("📎 View document"):
                            if file_path.lower().endswith(('.png','.jpg','.jpeg','.gif')):
                                st.image(file_path, width=300)
                            else:
                                with open(file_path, "rb") as f:
                                    st.download_button("Download", f, file_name=os.path.basename(file_path))
                    
                    if status == "Rejected" and remarks:
                        st.error(f"**Rejection reason:** {remarks}")
                    
                    if status == "Not Started" and viewer_role == "Student":
                        st.warning("⚠️ **Requirement not yet submitted.** Please upload the required document and submit for approval.")
                    
                    if status in ["Not Started", "Rejected"] and viewer_role == "Student":
                        with st.form(key=f"student_submit_{milestone_name}_{student_number}"):
                            st.markdown("**Required document:** Please upload the official form or certificate for this milestone.")
                            uploaded_file = st.file_uploader("Upload document (PDF/JPG/PNG) - Max 5MB", type=["pdf","jpg","jpeg","png"], key=f"upload_student_{milestone_name}_{student_number}")
                            date_completed = st.date_input("Date of completion/event", value=date.today())
                            if st.form_submit_button("Submit for Approval", use_container_width=True):
                                if not uploaded_file:
                                    st.error("Please upload a document.")
                                elif uploaded_file.size > 5 * 1024 * 1024:
                                    st.error("File size exceeds 5MB.")
                                else:
                                    filepath = save_milestone_file(student_number, milestone_name, uploaded_file)
                                    success, msg = update_milestone(student_number, milestone_name, "Pending", date_completed.strftime("%Y-%m-%d"), filepath, "", None)
                                    if success:
                                        if msg:
                                            st.success(msg)
                                        else:
                                            st.success(f"{milestone_name} submitted for approval.")
                                        st.rerun()
                                    else:
                                        st.error(msg)
                    elif status == "Pending" and is_adviser:
                        st.markdown("---")
                        st.markdown("**Review this milestone**")
                        with st.form(key=f"review_{milestone_name}_{student_number}"):
                            review_remarks = st.text_area("Remarks (optional)", key=f"review_remarks_{milestone_name}_{student_number}")
                            col_app, col_rej = st.columns(2)
                            if col_app.form_submit_button("✅ Approve", use_container_width=True):
                                success, msg = update_milestone(student_number, milestone_name, "Approved", None, None, review_remarks, st.session_state.display_name)
                                if success:
                                    if msg:
                                        st.success(msg)
                                    else:
                                        st.success("Milestone approved.")
                                    st.rerun()
                                else:
                                    st.error(msg)
                            if col_rej.form_submit_button("❌ Reject", use_container_width=True):
                                success, msg = update_milestone(student_number, milestone_name, "Rejected", None, None, review_remarks, st.session_state.display_name)
                                if success:
                                    st.warning("Milestone rejected.")
                                    st.rerun()
                                else:
                                    st.error(msg)
                    elif status == "Pending" and not is_adviser:
                        st.info("⏳ Your submission is pending review.")
                    elif status == "Approved":
                        st.success("✅ This milestone has been approved.")
                        if milestone_name == milestone_list[-1]:
                            st.markdown("""
                            <div class="next-step-card">
                                <strong>🎉 Congratulations!</strong><br>
                                You have completed all milestones. Contact the Graduate School for graduation.
                            </div>
                            """, unsafe_allow_html=True)
    
    # Admin & Extensions Tab (Staff only)
    if is_staff:
        with tabs[-1]:
            st.subheader("Administrative Data Entry & Extensions")
            
            st.markdown("**Update Student Program**")
            new_program = st.selectbox("New Program", PROGRAMS, index=PROGRAMS.index(student["program"]) if student["program"] in PROGRAMS else 0)
            if st.button("Update Program"):
                prior = student.get("prior_ms_graduate", False)
                new_req = get_required_units(new_program, prior)
                df = load_data()
                df.loc[df["student_number"] == student_number, "program"] = new_program
                if new_req is not None:
                    df.loc[df["student_number"] == student_number, "total_units_required"] = new_req
                save_data(df)
                st.success("Program updated.")
                st.rerun()
            
            st.markdown("**Update Special Status**")
            status_options = ["Regular", "Transferred", "Shifted", "On Leave", "Inactive", "Deleted"]
            current_special = student.get("special_status", "Regular")
            new_special = st.selectbox("Status", status_options, index=status_options.index(current_special) if current_special in status_options else 0)
            if st.button("Update Special Status"):
                df = load_data()
                df.loc[df["student_number"] == student_number, "special_status"] = new_special
                save_data(df)
                st.success("Special status updated.")
                st.rerun()
            
            st.markdown("---")
            st.markdown("### 📜 Extension Grants (UPLB GS Rules)")
            
            st.markdown("**Thesis/Dissertation Extension Units**")
            current_thesis_ext = student.get("thesis_extension_units", 0)
            max_thesis_ext = 6
            st.write(f"Current thesis extension units granted: **{current_thesis_ext} / {max_thesis_ext}**")
            if current_thesis_ext < max_thesis_ext:
                if st.button("➕ Grant 1 Thesis Extension Unit", key=f"grant_thesis_ext_{student_number}"):
                    df = load_data()
                    df.loc[df["student_number"] == student_number, "thesis_extension_units"] = current_thesis_ext + 1
                    save_data(df)
                    st.success(f"Thesis extension unit granted. New total: {current_thesis_ext + 1}")
                    st.rerun()
            else:
                st.info("Maximum thesis extension units (6) already granted.")
            
            st.markdown("**Residency Extension Years**")
            current_res_ext = student.get("residency_extension_years", 0)
            max_res_ext = 2
            st.write(f"Current residency extension years granted: **{current_res_ext}**")
            if current_res_ext < max_res_ext:
                if st.button("➕ Grant 1 Residency Extension Year", key=f"grant_res_ext_{student_number}"):
                    df = load_data()
                    df.loc[df["student_number"] == student_number, "residency_extension_years"] = current_res_ext + 1
                    new_max = get_residency_max_from_program(student["program"]) + (current_res_ext + 1)
                    df.loc[df["student_number"] == student_number, "residency_max_years"] = new_max
                    save_data(df)
                    st.success(f"Residency extended by 1 year. New max residency: {new_max} years")
                    st.rerun()
            else:
                st.info("Maximum residency extension (2 years) already granted.")
            
            st.markdown("---")
            st.markdown("**Export Student Data**")
            if st.button("📥 Download All Students CSV"):
                df_export = load_data()
                csv = df_export.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="sesam_students.csv">Download CSV</a>'
                st.markdown(href, unsafe_allow_html=True)

# ==================== STUDENT DASHBOARD ====================
def student_dashboard():
    df = load_data()
    student_records = df[df["student_number"] == st.session_state.username]
    if student_records.empty:
        st.error(f"❌ Student record not found for username: {st.session_state.username}. Please contact the administrator or register first.")
        st.stop()
    student = student_records.iloc[0].copy()
    program_type = get_program_type(student["program"])
    
    if st.session_state.get("profile_update_success", False):
        st.success("✅ Profile successfully updated!")
        st.session_state.profile_update_success = False
    
    st.subheader(f"📘 Your Dashboard – {student['name']}")
    st.info("ℹ️ **Note:** The adviser shown above is a **temporary adviser** assigned upon admission. Once your Guidance/Advisory Committee is formed and approved, the Chair will automatically become your official adviser.")
    
    required_fields_missing = False
    missing_fields = []
    if not student.get("address") or student.get("address") == "":
        missing_fields.append("Address")
    if not student.get("phone") or student.get("phone") == "":
        missing_fields.append("Phone Number")
    if not student.get("institutional_email") or student.get("institutional_email") == "":
        missing_fields.append("Institutional Email (UP mail)")
    if missing_fields:
        required_fields_missing = True
        st.warning(f"⚠️ **Required Information Missing**\n\nPlease complete the following fields in your Profile before accessing your coursework: {', '.join(missing_fields)}")
    
    existing_sems = get_student_semesters(student["student_number"])
    if len(existing_sems) == 1 and student.get("pos_status", "Pending") != "Approved":
        st.warning("⚠️ **Action Required:** You are in your first semester. Your Plan of Study (POS) must be approved by your adviser before the end of this semester to allow enrollment in the second semester. Please work with your adviser to complete and approve your POS.")
    
    resid_status, used, max_y = check_residency_alert(student)
    if resid_status == "exceeded":
        st.markdown(f'<div class="danger-banner">⚠️ RESIDENCY EXCEEDED: {used} years used (max {max_y}). You are no longer eligible to enroll.</div>', unsafe_allow_html=True)
    elif resid_status == "warning":
        st.markdown(f'<div class="warning-banner">⚠️ Residency warning: {used} out of {max_y} years used. Only one year remaining.</div>', unsafe_allow_html=True)
    elif resid_status == "warning_extension":
        st.markdown(f'<div class="warning-banner">⚠️ Residency extended: {used} out of {max_y} years. Extension granted.</div>', unsafe_allow_html=True)
    
    inc_items = get_inc_alert(student["student_number"])
    for inc in inc_items:
        if inc["status"] == "expired":
            st.markdown(f'<div class="danger-banner">❌ {inc["course"]} ({inc["semester"]}) INC/4.0 expired on {inc["deadline"]}. Converted to 5.00. Please retake.</div>', unsafe_allow_html=True)
        elif inc["status"] == "warning":
            st.markdown(f'<div class="warning-banner">⚠️ {inc["course"]} ({inc["semester"]}) INC/4.0 deadline in {inc["days_left"]} days ({inc["deadline"]}).</div>', unsafe_allow_html=True)
    
    semester_count = len(get_student_semesters(student["student_number"]))
    if semester_count >= 2 and is_master_program(student["program"]) and student.get("pos_status","Pending") != "Approved":
        st.markdown('<div class="danger-banner">⚠️ Your Plan of Study (POS) is not yet approved. You will not be able to register for the next semester until it is approved. Please contact your adviser.</div>', unsafe_allow_html=True)
    
    # Committee formation reminder (using new committee system)
    if not is_committee_approved(student["student_number"]):
        if len(existing_sems) >= 2:
            st.warning("""
            ⚠️ **Committee Formation Required**  
            Your Guidance/Advisory Committee should have been nominated during your first semester.  
            Please contact your temporary adviser immediately to form your committee and submit the Nomination Form to the Graduate School.  
            You will not be able to proceed to further semesters until this is approved.
            """)
        else:
            st.info("""
            ℹ️ **Reminder:** Your Guidance/Advisory Committee must be nominated by the end of this (first) semester.  
            Please consult with your temporary adviser to form your committee and submit the required form to the Graduate School.
            """)
    
    milestones_df = get_student_milestones(student["student_number"], program_type)
    milestone_list = MILESTONE_DEFS.get(program_type, MILESTONE_DEFS["MS_Thesis"])
    
    tab_names = ["👤 My Profile", "📚 Coursework"] + milestone_list
    main_tabs = st.tabs(tab_names)
    
    # Profile Tab
    with main_tabs[0]:
        render_compact_profile(student, is_own_profile=True)
        st.markdown("---")
        with st.expander("✏️ Edit Your Profile", expanded=False):
            with st.form("student_edit_profile"):
                st.markdown("#### Required Information")
                col1, col2 = st.columns(2)
                with col1:
                    new_address = st.text_input("Address *", value=student.get("address",""))
                with col2:
                    new_phone = st.text_input("Phone Number *", value=student.get("phone",""))
                new_email = st.text_input("Institutional Email (UP mail) *", value=student.get("institutional_email",""))
                st.caption("Your personal email (from NOA) cannot be changed here. Contact staff if needed.")
                st.markdown("#### Optional Information")
                col3, col4 = st.columns(2)
                with col3:
                    new_gender = st.selectbox("Gender", ["", "Male", "Female", "Other", "Prefer not to say"], index=["", "Male", "Female", "Other", "Prefer not to say"].index(student.get("gender","")) if student.get("gender","") in ["", "Male", "Female", "Other", "Prefer not to say"] else 0)
                    new_civil = st.selectbox("Civil Status", ["", "Single", "Married", "Divorced", "Widowed"], index=["", "Single", "Married", "Divorced", "Widowed"].index(student.get("civil_status","")) if student.get("civil_status","") in ["", "Single", "Married", "Divorced", "Widowed"] else 0)
                    new_citizenship = st.text_input("Citizenship", value=student.get("citizenship",""))
                with col4:
                    new_religion = st.text_input("Religion", value=student.get("religion",""))
                    try:
                        birthdate_val = datetime.strptime(student.get("birthdate","2000-01-01"), "%Y-%m-%d").date() if student.get("birthdate","") else date(2000,1,1)
                    except:
                        birthdate_val = date(2000,1,1)
                    new_birthdate = st.date_input("Birthdate", value=birthdate_val)
                st.markdown("#### Emergency Contact")
                col5, col6 = st.columns(2)
                with col5:
                    new_emergency_name = st.text_input("Name", value=student.get("emergency_name",""))
                    new_emergency_rel = st.text_input("Relationship", value=student.get("emergency_relationship",""))
                with col6:
                    new_emergency_cc = st.text_input("Country Code (e.g., +63)", value=student.get("emergency_country_code",""))
                    new_emergency_phone = st.text_input("Phone Number", value=student.get("emergency_phone",""))
                submitted = st.form_submit_button("Save Changes", use_container_width=True)
                if submitted:
                    if not new_address or not new_phone or not new_email:
                        st.error("Address, Phone Number, and Institutional Email are required.")
                    else:
                        birthdate_str = new_birthdate.strftime("%Y-%m-%d")
                        df = load_data()
                        idx = df[df["student_number"] == student["student_number"]].index
                        if len(idx) > 0:
                            df.at[idx[0], "address"] = new_address
                            df.at[idx[0], "phone"] = new_phone
                            df.at[idx[0], "institutional_email"] = new_email
                            df.at[idx[0], "gender"] = new_gender
                            df.at[idx[0], "civil_status"] = new_civil
                            df.at[idx[0], "citizenship"] = new_citizenship
                            df.at[idx[0], "birthdate"] = birthdate_str
                            df.at[idx[0], "religion"] = new_religion
                            df.at[idx[0], "emergency_name"] = new_emergency_name
                            df.at[idx[0], "emergency_relationship"] = new_emergency_rel
                            df.at[idx[0], "emergency_country_code"] = new_emergency_cc
                            df.at[idx[0], "emergency_phone"] = new_emergency_phone
                            save_data(df)
                            st.session_state.profile_update_success = True
                            st.rerun()
                        else:
                            st.error("Student record not found.")
    
    # Coursework Tab
    with main_tabs[1]:
        if required_fields_missing:
            st.error("❌ **Cannot access Coursework**\n\nPlease complete your profile information (Address, Phone Number, and Institutional Email) before proceeding to your coursework.")
            st.stop()
        
        st.subheader("Your Academic Record (Coursework)")
        
        timeline = generate_timeline(student["ay_start"], student["semester"], student["program"])
        total_terms = len(timeline)
        
        semesters = get_student_semesters(student["student_number"])
        if not semesters.empty:
            sem_order = {"1st Sem": 0, "2nd Sem": 1, "Summer": 2}
            semesters["order"] = semesters["semester"].map(sem_order)
            semesters["ay_num"] = semesters["academic_year"].apply(lambda x: int(x.split("-")[0]))
            semesters = semesters.sort_values(["ay_num", "order"]).reset_index(drop=True)
        
        for _, row in semesters.iterrows():
            render_semester_block_general(student["student_number"], row, is_staff=False, is_adviser=False)
        
        if len(semesters) < total_terms:
            pos_ok = True
            committee_ok = True
            if len(semesters) >= 1:
                if student.get("pos_status") != "Approved":
                    pos_ok = False
                    st.warning("⚠️ Your Plan of Study (POS) must be approved before you can add the next semester. Please work with your adviser.")
                if not is_committee_approved(student["student_number"]):
                    committee_ok = False
                    st.warning("⚠️ Your Guidance/Advisory Committee must be approved before you can add the next semester. Please submit the Committee Nomination Form to the Graduate School.")
            
            if pos_ok and committee_ok:
                if st.button("➕ Add Next Semester"):
                    if not semesters.empty:
                        last_sem = semesters.iloc[-1]
                        success = create_next_semester(student["student_number"], last_sem["academic_year"], last_sem["semester"])
                    else:
                        success = create_next_semester(student["student_number"], f"{student['ay_start']}-{student['ay_start']+1}", student["semester"])
                    if success:
                        st.rerun()
        else:
            total_taken = student["total_units_taken"] if not pd.isna(student["total_units_taken"]) else 0
            total_required = student["total_units_required"] if not pd.isna(student["total_units_required"]) else 24
            if total_taken >= total_required:
                st.success("✅ You have earned the required number of units. Please request your adviser to approve the **Graduation Clearance** milestone to complete your coursework.")
            else:
                st.info(f"📚 You have created all {total_terms} semester(s). Continue enrolling in subjects to meet the required {total_required} units (currently {total_taken}).")
        
        st.markdown("---")
        st.subheader("📊 Cumulative Summary")
        total_taken = student["total_units_taken"] if not pd.isna(student["total_units_taken"]) else 0
        total_required = student["total_units_required"] if not pd.isna(student["total_units_required"]) else 24
        remaining = max(0, total_required - total_taken)
        gwa_val = student["gwa"] if pd.notna(student["gwa"]) else None
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Total Units Taken", total_taken)
        with col2: st.metric("Required Units", total_required)
        with col3: st.metric("Remaining Units", remaining)
        with col4: st.metric("Cumulative GWA", f"{gwa_val:.2f}" if gwa_val is not None else "—")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🔄 Refresh GWA & Units"):
                with st.spinner("Recalculating from saved records..."):
                    success = update_student_academic_summary(student["student_number"])
                    if success:
                        st.success("Totals recalculated successfully. Refreshing page...")
                        st.rerun()
                    else:
                        st.error("Recalculation failed. See errors above.")
        with col_btn2:
            st.caption("⚠️ Only **saved subjects** are included. Use 'Save Subjects' before refreshing.")
    
    # Milestone Tabs (student view)
    for i, milestone_name in enumerate(milestone_list):
        with main_tabs[2 + i]:
            if milestone_name == "Plan of Study (POS)":
                render_pos_milestone(student["student_number"], "Student", is_own_view=True)
            else:
                # Committee milestone (new version-controlled UI)
                if milestone_name in ["Guidance Committee Members", "Guidance Committee Formation", "Advisory Committee Formation", "Supervisory Committee Formation"]:
                    st.markdown(f"### {milestone_name}")
                    
                    active = get_active_committee_version(student["student_number"])
                    if active is not None:
                        st.success(f"**Active Committee (Version {active['version_number']})** – Verified on {active['verification_date']}")
                        with st.expander("View Active Committee Details"):
                            members = get_committee_members_for_version(active['version_id'])
                            st.dataframe(members)
                            st.markdown(f"[View GS PDF]({active['gs_pdf_path']})")
                    else:
                        st.info("No active committee approved yet.")
                    
                    pending = get_pending_committee_version(student["student_number"])
                    if pending is None:
                        # Student submission form (only if no pending version exists)
                        prog_type = get_program_type(student["program"])
                        is_phd = prog_type.startswith("PhD")
                        extra_major_key = f"extra_major_{student['student_number']}"
                        extra_cognate_key = f"extra_cognate_{student['student_number']}"
                        if extra_major_key not in st.session_state:
                            st.session_state[extra_major_key] = 0
                        if extra_cognate_key not in st.session_state:
                            st.session_state[extra_cognate_key] = 0

                        with st.form(key="submit_committee_version"):
                            st.markdown("#### Submit New Committee (GS-Approved)")
                            uploaded_pdf = st.file_uploader("GS‑approved Committee Form (PDF)", type=["pdf"])
                            chair = st.text_input("Chair (required)")
                            co_chair = st.text_input("Co‑chair (optional)")

                            major_members = []
                            st.markdown("##### Major Field Members")
                            major1 = st.text_input("Major member 1 (required)")
                            if major1.strip():
                                major_members.append(major1)

                            if is_phd:
                                for i in range(st.session_state[extra_major_key]):
                                    extra = st.text_input(f"Major member {i+2} (optional)", key=f"major_extra_{student['student_number']}_{i}")
                                    if extra.strip():
                                        major_members.append(extra)
                                if st.session_state[extra_major_key] < 1:
                                    if st.form_submit_button("➕ Add additional major member"):
                                        st.session_state[extra_major_key] += 1
                                        st.rerun()

                            cognate_members = []
                            if is_phd:
                                st.markdown("##### Cognate Field Members")
                                cog1 = st.text_input("Cognate member 1 (required)")
                                if cog1.strip():
                                    cognate_members.append(cog1)
                                for i in range(st.session_state[extra_cognate_key]):
                                    extra = st.text_input(f"Cognate member {i+2} (optional)", key=f"cog_extra_{student['student_number']}_{i}")
                                    if extra.strip():
                                        cognate_members.append(extra)
                                if st.session_state[extra_cognate_key] < 1:
                                    if st.form_submit_button("➕ Add additional cognate member"):
                                        st.session_state[extra_cognate_key] += 1
                                        st.rerun()
                            else:
                                st.markdown("##### Minor Field Member")
                                minor = st.text_input("Minor member (required)")
                                if minor.strip():
                                    cognate_members.append(minor)

                            submitted = st.form_submit_button("Submit Committee for Verification")
                            if submitted:
                                errors = []
                                if not uploaded_pdf:
                                    errors.append("PDF file is required")
                                if not chair.strip():
                                    errors.append("Chair is required")
                                if len(major_members) == 0:
                                    errors.append("At least one major member is required")
                                if is_phd and len(cognate_members) == 0:
                                    errors.append("At least one cognate member is required")
                                if not is_phd and len(cognate_members) != 1:
                                    errors.append("Exactly one minor member is required for Master's programs")
                                total = 1 + (1 if co_chair.strip() else 0) + len(major_members) + len(cognate_members)
                                if is_phd and (total < 4 or total > 5):
                                    errors.append(f"PhD committee must have 4–5 members (currently {total})")
                                if not is_phd and (total < 3 or total > 4):
                                    errors.append(f"Master's committee must have 3–4 members (currently {total})")

                                if errors:
                                    for err in errors:
                                        st.error(err)
                                else:
                                    success, msg = save_committee_version(
                                        student["student_number"], uploaded_pdf,
                                        "PhD" if is_phd else "MS",
                                        chair, co_chair, major_members, cognate_members
                                    )
                                    if success:
                                        st.session_state[extra_major_key] = 0
                                        st.session_state[extra_cognate_key] = 0
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                    else:
                        st.warning(f"**Pending Committee Version {pending['version_number']}** – Submitted on {pending['created_at']} – Awaiting verification")
                        with st.expander("View Pending Committee"):
                            members = get_committee_members_for_version(pending['version_id'])
                            st.dataframe(members)
                            st.markdown(f"[View GS PDF]({pending['gs_pdf_path']})")

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
                    milestone_filtered = milestones_df[milestones_df["milestone"] == milestone_name]
                    if milestone_filtered.empty:
                        st.error(f"Milestone '{milestone_name}' not found in records.")
                        continue
                    milestone_row = milestone_filtered.iloc[0]
                    status = milestone_row["status"]
                    date_val = milestone_row["date"]
                    file_path = milestone_row["file_path"]
                    remarks = milestone_row["remarks"]
                    reviewed_by = milestone_row.get("reviewed_by", "")
                    review_date = milestone_row.get("review_date", "")

                    st.markdown(f"### {milestone_name}")
                    st.markdown(get_status_badge(status), unsafe_allow_html=True)
                    if date_val:
                        st.write(f"**Date of approval:** {date_val}")
                    if reviewed_by and status == "Approved":
                        st.caption(f"Approved by: {reviewed_by} on {review_date}")

                    if file_path and file_path != "" and os.path.exists(file_path):
                        with st.expander("📎 View submitted document"):
                            if file_path.lower().endswith(('.png','.jpg','.jpeg','.gif')):
                                st.image(file_path, width=300)
                            else:
                                with open(file_path, "rb") as f:
                                    st.download_button("Download", f, file_name=os.path.basename(file_path))

                    if status == "Rejected" and remarks:
                        st.error(f"**Rejection reason:** {remarks}")
                    
                    if status == "Not Started":
                        st.warning("⚠️ **Requirement not yet submitted.** Please upload the required document and submit for approval.")
                    
                    if status in ["Not Started", "Rejected"]:
                        with st.form(key=f"student_submit_noncomm_{milestone_name}_{student['student_number']}"):
                            st.markdown("**Required document:** Please upload the official form or certificate for this milestone.")
                            uploaded_file = st.file_uploader("Upload document (PDF/JPG/PNG) - Max 5MB", type=["pdf","jpg","jpeg","png"], key=f"upload_student_noncomm_{milestone_name}_{student['student_number']}")
                            date_completed = st.date_input("Date of completion/event", value=date.today())
                            if st.form_submit_button("Submit for Approval", use_container_width=True):
                                if not uploaded_file:
                                    st.error("Please upload a document.")
                                elif uploaded_file.size > 5 * 1024 * 1024:
                                    st.error("File size exceeds 5MB.")
                                else:
                                    filepath = save_milestone_file(student["student_number"], milestone_name, uploaded_file)
                                    success, msg = update_milestone(student["student_number"], milestone_name, "Pending", date_completed.strftime("%Y-%m-%d"), filepath, "", None)
                                    if success:
                                        if msg:
                                            st.success(msg)
                                        else:
                                            st.success(f"{milestone_name} submitted for approval.")
                                        st.rerun()
                                    else:
                                        st.error(msg)
                    elif status == "Pending":
                        st.info("⏳ Your submission is pending review.")
                    elif status == "Approved":
                        st.success("✅ This milestone has been approved.")
                        if milestone_name == milestone_list[-1]:
                            st.markdown("""
                            <div class="next-step-card">
                                <strong>🎉 Congratulations!</strong><br>
                                You have completed all milestones. Contact the Graduate School for graduation.
                            </div>
                            """, unsafe_allow_html=True)
    
    st.caption("For corrections, contact your adviser or SESAM Staff.")

# ==================== MAIN APP ====================
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center'>🎓 SESAM KMIS</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
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
                    st.error("Invalid credentials")
        st.caption("Demo (staff): staff1/admin123 | adviser1/adv123 | For students, use your registered student number as both username and password.")
    st.stop()

if st.session_state.logged_in and not st.session_state.consent_given:
    show_consent_form()
    st.stop()

# Initialize committee tables
init_committee_tables()

convert_expired_grades()
df = load_data()
if df is None or df.empty:
    st.error("❌ Could not load student data. Please check the data file.")
    st.stop()

with st.sidebar:
    st.markdown(f"<div style='text-align:center'><h3>👤 {st.session_state.display_name}</h3><div>{st.session_state.role}</div><div>✅ Consent given</div></div>", unsafe_allow_html=True)
    
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.consent_given = False
        st.rerun()
    st.markdown("---")
    st.caption("Version 32.0 | Enhanced committee workflow: version control, adviser verification, GS PDF upload")

st.title("🎓 SESAM Graduate Student Lifecycle Management")
st.caption("Strict rule enforcement + enhanced committee workflow: version control, adviser verification, GS PDF upload")

role = st.session_state.role

if role == "SESAM Staff":
    st.subheader("📋 Student Directory")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Register New Student", use_container_width=True):
            st.session_state.show_registration = True
            st.session_state.staff_show_update = False
            st.session_state.staff_selected_student = None
    with col2:
        if st.button("✏️ Update Student Information", use_container_width=True):
            st.session_state.show_registration = False
            st.session_state.staff_show_update = True
            st.session_state.staff_selected_student = None
    if st.session_state.get("show_registration", False):
        register_new_student_form()
    elif st.session_state.get("staff_show_update", False):
        if st.session_state.staff_selected_student is None:
            st.subheader("🔍 Search and Select a Student")
            search_term = st.text_input("Search by name or student number", key="staff_search")
            filtered = filter_dataframe(search_term, df)
            if filtered is None:
                filtered = pd.DataFrame()
            if filtered.empty:
                st.warning("No students match your search.")
            else:
                st.markdown(f"#### Found {len(filtered)} student(s)")
                for _, row in filtered.iterrows():
                    col_name, col_prog, col_gwa = st.columns([3,2,1])
                    with col_name:
                        if st.button(f"📌 {row['name']}", key=f"select_{row['student_number']}", help="Click to open profile"):
                            st.session_state.staff_selected_student = row["student_number"]
                            st.rerun()
                    with col_prog:
                        st.write(row['program'])
                    with col_gwa:
                        gwa_disp = f"{row['gwa']:.2f}" if pd.notna(row['gwa']) else "—"
                        st.write(f"GWA: {gwa_disp}")
        else:
            view_student_profile(st.session_state.staff_selected_student, viewer_role="SESAM Staff")
    else:
        st.info("Select an action using the buttons above.")

elif role == "Faculty Adviser":
    st.subheader(f"👨‍🏫 Faculty Adviser Dashboard – {st.session_state.display_name}")
    
    advisees = df[df["advisor"] == st.session_state.display_name].copy()
    if advisees.empty:
        st.warning("No students assigned to you.")
    else:
        all_semesters = load_semester_records()
        advisee_numbers = advisees["student_number"].tolist()
        pending_sems = all_semesters[(all_semesters["student_number"].isin(advisee_numbers)) & (all_semesters["doc_status"] == "Pending")]
        pending_count = len(pending_sems)
        col1, col2 = st.columns(2)
        with col1: st.metric("Total Advisees", len(advisees))
        with col2: st.metric("📄 Pending Documents", pending_count)
        st.markdown("---")
        search_term = st.text_input("🔍 Search advisees", key="adviser_search")
        if search_term:
            advisees = advisees[advisees["name"].str.contains(search_term, case=False, na=False) | 
                               advisees["student_number"].str.contains(search_term, case=False, na=False)]
        st.markdown(f"#### Your Advisees ({len(advisees)} student(s))")
        for _, student in advisees.iterrows():
            col_name, col_prog, col_gwa = st.columns([3,2,1])
            with col_name:
                if st.button(f"📌 {student['name']}", key=f"advisee_{student['student_number']}", help="Click to open profile"):
                    st.session_state.adviser_selected_student = student["student_number"]
                    st.rerun()
            with col_prog:
                st.write(student['program'])
            with col_gwa:
                gwa_disp = f"{student['gwa']:.2f}" if pd.notna(student['gwa']) else "—"
                st.write(f"GWA: {gwa_disp}")
        if st.session_state.get("adviser_selected_student"):
            view_student_profile(st.session_state.adviser_selected_student, viewer_role="Faculty Adviser")

elif role == "Student":
    student_dashboard()

st.markdown("---")
st.caption("SESAM KMIS v32.0 | Enhanced committee workflow: version control, adviser verification, GS PDF upload")
