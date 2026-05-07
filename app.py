"""
SESAM KMIS - Graduate Student Lifecycle Management System
Version: 28.17 | Two‑panel committee interface + transfer workflow
"""

import streamlit as st
import pandas as pd
import os
import json
from datetime import date, datetime, timedelta

# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="SESAM KMIS", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .profile-card {
        background: white;
        border-radius: 20px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
    }
    .profile-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
        border-bottom: 2px solid #f0f2f6;
        padding-bottom: 0.5rem;
    }
    .profile-header h3 {
        margin: 0;
        color: #1f3b4c;
        font-size: 1.2rem;
    }
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 500;
    }
    .status-not-started { background-color: #e9ecef; color: #495057; }
    .status-pending { background-color: #fff3cd; color: #856404; }
    .status-approved { background-color: #d4edda; color: #155724; }
    .status-rejected { background-color: #f8d7da; color: #721c24; }
    .warning-banner { background-color: #ffcc00; color: #333; padding: 0.5rem; border-radius: 8px; margin: 0.5rem 0; font-weight: bold; }
    .danger-banner { background-color: #dc3545; color: white; padding: 0.5rem; border-radius: 8px; margin: 0.5rem 0; font-weight: bold; }
    .next-step-card {
        background-color: #e3f2fd;
        border-left: 5px solid #1e88e5;
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    .stButton button {
        border-radius: 30px !important;
        padding: 0.4rem 1.2rem !important;
        font-weight: 500 !important;
    }
    .pos-match { color: green; font-weight: bold; }
    .pos-mismatch { color: red; font-weight: bold; }
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
    # Student credentials will be validated from students.csv
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
    if program == "MS Environmental Science": return 32
    elif program == "PhD Environmental Science": return 37 if prior_ms_graduate else 50
    else: return None

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
def get_residency_max_from_program(program): return 5 if is_master_program(program) else 7
def format_ay(ay_start, semester): return f"A.Y. {ay_start}-{ay_start+1} ({semester})"

def get_semester_structure(program):
    if is_master_program(program):
        return (4, 1, 5)   # 4 semesters, 1 summer, 5 terms
    else:
        return (6, 2, 8)   # 6 semesters, 2 summers, 8 terms

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
UPLOAD_FILE = "uploads.csv"
DATA_REQUEST_FILE = "data_requests.csv"
FINAL_EXAM_VOTES_FILE = "final_exam_votes.csv"
ADVISER_TRANSFER_REQUESTS_FILE = "adviser_transfer_requests.csv"

for folder in [UPLOAD_FOLDER, PROFILE_PIC_FOLDER]:
    if not os.path.exists(folder): os.makedirs(folder)

# ==================== COMMITTEE MEMBERS HELPERS ====================
def get_committee_members(student_number):
    df = load_data()
    student = df[df["student_number"] == student_number]
    if student.empty:
        return []
    committee_json = student.iloc[0].get("committee_members_structured", "")
    if committee_json and committee_json.strip():
        try:
            members = json.loads(committee_json)
            if isinstance(members, list):
                return members
        except:
            pass
    return []

def set_committee_members(student_number, members):
    # Validate exactly one Chair
    chairs = [m for m in members if m.get("role") == "Chair"]
    if len(chairs) != 1:
        return False, "Committee must have exactly one Chair."
    df = load_data()
    idx = df[df["student_number"] == student_number].index
    if len(idx) > 0:
        df.at[idx[0], "committee_members_structured"] = json.dumps(members)
        save_data(df)
        return True, "Committee members saved."
    return False, "Student not found."

def get_committee_chair(student_number):
    members = get_committee_members(student_number)
    for member in members:
        if member.get("role") == "Chair":
            return member.get("name", "").strip()
    return None

# ==================== ADVISER TRANSFER REQUESTS ====================
def load_transfer_requests():
    if not os.path.exists(ADVISER_TRANSFER_REQUESTS_FILE) or os.path.getsize(ADVISER_TRANSFER_REQUESTS_FILE) == 0:
        return pd.DataFrame(columns=["request_id", "student_number", "current_advisor", "requested_advisor", "status", "request_date", "milestone_name"])
    df = pd.read_csv(ADVISER_TRANSFER_REQUESTS_FILE, dtype=str)
    for col in ["request_id", "student_number", "current_advisor", "requested_advisor", "status", "request_date", "milestone_name"]:
        if col not in df.columns:
            df[col] = ""
    df["request_id"] = pd.to_numeric(df["request_id"], errors='coerce').fillna(0).astype(int)
    return df

def save_transfer_requests(df):
    df.to_csv(ADVISER_TRANSFER_REQUESTS_FILE, index=False)

def create_transfer_request(student_number, current_advisor, requested_advisor, milestone_name):
    df = load_transfer_requests()
    new_id = df["request_id"].max() + 1 if not df.empty else 1
    new = pd.DataFrame([{
        "request_id": new_id,
        "student_number": student_number,
        "current_advisor": current_advisor,
        "requested_advisor": requested_advisor,
        "status": "Pending",
        "request_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "milestone_name": milestone_name
    }])
    df = pd.concat([df, new], ignore_index=True)
    save_transfer_requests(df)
    return new_id

def accept_transfer_request(request_id):
    df = load_transfer_requests()
    mask = df["request_id"] == request_id
    if not mask.any():
        return False, "Request not found."
    row = df[mask].iloc[0]
    student_number = row["student_number"]
    requested_advisor = row["requested_advisor"]
    students_df = load_data()
    idx = students_df[students_df["student_number"] == student_number].index
    if len(idx) == 0:
        return False, "Student not found."
    students_df.at[idx[0], "advisor"] = requested_advisor
    save_data(students_df)
    df = df[~mask]
    save_transfer_requests(df)
    return True, f"Student transferred to {requested_advisor}."

def reject_transfer_request(request_id):
    df = load_transfer_requests()
    mask = df["request_id"] == request_id
    if not mask.any():
        return False, "Request not found."
    df = df[~mask]
    save_transfer_requests(df)
    return True, "Transfer request rejected."

# ==================== POS SUBMISSIONS FUNCTIONS ====================
def load_pos_submissions():
    if not os.path.exists(POS_SUBMISSIONS_FILE) or os.path.getsize(POS_SUBMISSIONS_FILE) == 0:
        return pd.DataFrame(columns=["submission_id", "student_number", "file_path", "upload_date", "version", "status", "approval_date", "approved_by", "remarks"])
    df = pd.read_csv(POS_SUBMISSIONS_FILE, dtype=str)
    for col in ["submission_id", "student_number", "file_path", "upload_date", "version", "status", "approval_date", "approved_by", "remarks"]:
        if col not in df.columns:
            df[col] = ""
    df["submission_id"] = pd.to_numeric(df["submission_id"], errors='coerce').fillna(0).astype(int)
    df["version"] = pd.to_numeric(df["version"], errors='coerce').fillna(0).astype(int)
    return df

def save_pos_submissions(df):
    df.to_csv(POS_SUBMISSIONS_FILE, index=False)

def get_pos_submissions(student_number):
    df = load_pos_submissions()
    return df[df["student_number"] == student_number].sort_values("submission_id", ascending=False)

def get_latest_approved_pos(student_number):
    df = load_pos_submissions()
    approved = df[(df["student_number"] == student_number) & (df["status"] == "Approved")]
    if approved.empty:
        return None
    return approved.sort_values("submission_id", ascending=False).iloc[0]

def submit_pos_document(student_number, uploaded_file):
    if uploaded_file is None:
        return False
    df = load_pos_submissions()
    student_submissions = df[df["student_number"] == student_number]
    if student_submissions.empty:
        new_id = 1
        version = 1
    else:
        new_id = student_submissions["submission_id"].max() + 1
        version = len(student_submissions) + 1
    folder = os.path.join(UPLOAD_FOLDER, student_number, "pos_submissions")
    os.makedirs(folder, exist_ok=True)
    ext = uploaded_file.name.split('.')[-1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"POS_v{version}_{timestamp}.{ext}"
    filepath = os.path.join(folder, filename)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    new_row = pd.DataFrame([{
        "submission_id": new_id,
        "student_number": student_number,
        "file_path": filepath,
        "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": version,
        "status": "Pending",
        "approval_date": "",
        "approved_by": "",
        "remarks": ""
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    save_pos_submissions(df)
    update_pos_milestone_status(student_number)
    return True

def approve_pos_submission(submission_id, reviewer_name, remarks):
    df = load_pos_submissions()
    mask = df["submission_id"] == submission_id
    if not mask.any():
        return False
    df.loc[mask, "status"] = "Approved"
    df.loc[mask, "approval_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df.loc[mask, "approved_by"] = reviewer_name
    if remarks:
        df.loc[mask, "remarks"] = remarks
    save_pos_submissions(df)
    student_number = df.loc[mask, "student_number"].iloc[0]
    update_pos_milestone_status(student_number)
    return True

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
    approved = submissions[submissions["status"] == "Approved"]
    if not approved.empty:
        latest_approved = approved.sort_values("submission_id", ascending=False).iloc[0]
        approval_date = latest_approved.get("approval_date", "")
        update_milestone_status_from_pos(student_number, "Approved", approval_date)
    elif any(submissions["status"] == "Pending"):
        update_milestone_status_from_pos(student_number, "Pending", "")
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
def create_demo_students():
    # Demo data - not auto-called
    data = {
        "student_number": [f"S00{i}" for i in range(1,14)],
        "password": [""]*13,
        "name": ["Santos, Maria Concepcion R.", "Dela Cruz, Jose Mari P.", "Fernandez, Kristoffer Ivan M.", "Lopez, Maria Isabella T.", "Villanueva, Gabriel Angelo S.", "Reyes, Patricia Anne G.", "Gomez, Emmanuel D.", "Mendoza, Catherine Joy L.", "Santiago, Rommel C.", "Ramirez, Maria Lourdes E.", "Torres, Victor Emmanuel A.", "Bautista, Anna Patricia F.", "Aquino, Francis Joseph T."],
        "last_name": ["Santos","Dela Cruz","Fernandez","Lopez","Villanueva","Reyes","Gomez","Mendoza","Santiago","Ramirez","Torres","Bautista","Aquino"],
        "first_name": ["Maria Concepcion","Jose Mari","Kristoffer Ivan","Maria Isabella","Gabriel Angelo","Patricia Anne","Emmanuel","Catherine Joy","Rommel","Maria Lourdes","Victor Emmanuel","Anna Patricia","Francis Joseph"],
        "middle_name": ["R.","P.","M.","T.","S.","G.","D.","L.","C.","E.","A.","F.","T."],
        "program": [PROGRAMS[0]]*3 + [PROGRAMS[1]] + [PROGRAMS[0]]*9,
        "advisor": ["Dr. Eslava","Dr. Sanchez","Dr. Eslava","Dr. Sanchez","Dr. Eslava","Dr. Sanchez","Dr. Eslava","Dr. Sanchez","Dr. Eslava","Dr. Sanchez","Dr. Eslava","Dr. Sanchez","Dr. Eslava"],
        "ay_start": [2022,2023,2022,2022,2022,2023,2022,2022,2022,2022,2022,2022,2022],
        "semester": ["1st Sem"]*13,
        "gwa": [1.80,1.95,1.85,2.30,1.90,1.88,1.75,1.85,1.80,1.80,1.80,1.85,1.90],
        "total_units_taken": [24,12,24,24,24,15,24,18,24,24,24,24,24],
        "total_units_required": [24]*13,
        "thesis_units_taken": [6,2,6,6,4,2,3,2,8,3,6,6,6],
        "thesis_units_limit": [6,6,12,6,6,6,6,6,12,6,6,6,6],
        "thesis_extension_units": [0]*13,
        "residency_years_used": [3,1,3,3,3,1,2,2,3,3,3,3,3],
        "residency_extension_years": [0]*13,
        "pos_status": ["Approved","Pending","Approved","Approved","Approved","Approved","Pending","Approved","Approved","Approved","Approved","Approved","Approved"],
        "pos_approval_date": [""]*13,
        "qualifying_exam_status": ["N/A","N/A","Passed","N/A","N/A","N/A","N/A","N/A","Passed","N/A","N/A","N/A","N/A"],
        "written_comprehensive_status": ["N/A","N/A","Failed","N/A","N/A","N/A","N/A","N/A","Passed","N/A","N/A","N/A","N/A"],
        "oral_comprehensive_status": ["N/A","N/A","Not Taken","N/A","N/A","N/A","N/A","N/A","Failed","N/A","N/A","N/A","N/A"],
        "general_exam_status": ["Passed","Passed","N/A","Passed","Passed","Not Taken","Not Taken","Not Taken","N/A","Passed","Passed","Passed","Passed"],
        "final_exam_status": ["Passed","Not Taken","Not Taken","Not Taken","Not Taken","Not Taken","Not Taken","Not Taken","Not Taken","Not Taken","Not Taken","Passed","Not Taken"],
        "external_reviewer": [""]*13,
        "final_exam_attempts": [0]*13,
        "profile_pic": [""]*13,
        "committee_members_structured": [""]*13,
        "committee_approval_date": [""]*13,
        "thesis_outline_approved": ["Yes"]*13,
        "thesis_status": ["Approved"]*13,
        "prior_ms_graduate": [False]*13,
        "student_status": ["Regular"]*13,
        "address": [""]*13,
        "phone": [""]*13,
        "institutional_email": [""]*13,
        "gender": [""]*13,
        "civil_status": [""]*13,
        "citizenship": [""]*13,
        "birthdate": [""]*13,
        "religion": [""]*13,
        "emergency_name": [""]*13,
        "emergency_relationship": [""]*13,
        "emergency_country_code": [""]*13,
        "emergency_phone": [""]*13,
        "special_status": ["Regular"]*13,
        "residency_max_years": [5,5,7,5,5,5,5,5,7,5,5,5,5],
        "profile_pending_status": [""]*13,
        "profile_pending_remarks": [""]*13,
        "profile_pending_address": [""]*13,
        "profile_pending_phone": [""]*13,
        "profile_pending_email": [""]*13,
        "profile_pending_gender": [""]*13,
        "profile_pending_civil_status": [""]*13,
        "profile_pending_citizenship": [""]*13,
        "profile_pending_birthdate": [""]*13,
        "profile_pending_religion": [""]*13,
        "profile_pending_emergency_name": [""]*13,
        "profile_pending_emergency_relationship": [""]*13,
        "profile_pending_emergency_country_code": [""]*13,
        "profile_pending_emergency_phone": [""]*13,
    }
    df = pd.DataFrame(data)
    numeric_cols = ["ay_start","gwa","total_units_taken","total_units_required",
                    "thesis_units_taken","thesis_units_limit","thesis_extension_units",
                    "residency_years_used","residency_extension_years","residency_max_years",
                    "final_exam_attempts"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    for col in df.columns:
        if col not in numeric_cols and col != "prior_ms_graduate":
            df[col] = df[col].astype(str).replace("nan", "").replace("None", "")
    df["prior_ms_graduate"] = df["prior_ms_graduate"].astype(bool)
    return df

def load_data():
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        empty_df = pd.DataFrame(columns=create_demo_students().columns)
        save_data(empty_df)
        return empty_df
    try:
        df = pd.read_csv(DATA_FILE, dtype=str)
    except Exception:
        empty_df = pd.DataFrame(columns=create_demo_students().columns)
        save_data(empty_df)
        return empty_df

    if "password" not in df.columns:
        df["password"] = ""
    if "pos_approval_date" not in df.columns:
        df["pos_approval_date"] = ""

    numeric_cols = ["ay_start","gwa","total_units_taken","total_units_required",
                    "thesis_units_taken","thesis_units_limit","thesis_extension_units",
                    "residency_years_used","residency_extension_years","residency_max_years",
                    "final_exam_attempts"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            if col != "gwa":
                df[col] = df[col].astype(int)

    default_columns = create_demo_students().columns
    for col in default_columns:
        if col not in df.columns:
            df[col] = "" if col not in numeric_cols else 0
            if col == "prior_ms_graduate":
                df[col] = False

    text_cols = [c for c in df.columns if c not in numeric_cols and c != "prior_ms_graduate"]
    for col in text_cols:
        df[col] = df[col].fillna("").astype(str)

    if "prior_ms_graduate" in df.columns:
        df["prior_ms_graduate"] = df["prior_ms_graduate"].astype(bool)
    else:
        df["prior_ms_graduate"] = False

    for idx, row in df.iterrows():
        prog = row["program"]
        if prog and prog != "":
            df.at[idx, "residency_max_years"] = get_residency_max_from_program(prog)
            df.at[idx, "thesis_units_limit"] = get_thesis_limit_from_program(prog)
            req = get_required_units(prog, row.get("prior_ms_graduate", False))
            if req is not None:
                df.at[idx, "total_units_required"] = req

    semesters_df = load_semester_records()
    for sn in df["student_number"].unique():
        sems = semesters_df[semesters_df["student_number"] == sn]
        total_grade = 0
        total_units = 0
        for _, sem in sems.iterrows():
            if sem["semester_status"] != "Regular":
                continue
            try:
                subjects = json.loads(sem["subjects_json"]) if sem["subjects_json"] else []
                for subj in subjects:
                    units = float(subj.get("units", 0))
                    grade = float(subj.get("grade", 0))
                    total_units += units
                    total_grade += units * grade
            except:
                pass
        if total_units > 0:
            df.loc[df["student_number"] == sn, "gwa"] = total_grade / total_units
            df.loc[df["student_number"] == sn, "total_units_taken"] = total_units

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
        except: pass
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

# ==================== RULE FUNCTIONS ====================
def check_pos_approval(student_number, semester_index):
    if semester_index >= 1:
        df = load_data()
        student = df[df["student_number"] == student_number]
        if student.empty:
            return False, "Student not found."
        pos_status = student.iloc[0].get("pos_status", "Pending")
        if pos_status != "Approved":
            return False, "Your Plan of Study (POS) must be approved by your adviser before you can enroll in the second semester. Please contact your Guidance Committee."
    return True, ""

def check_thesis_units_limit(student_number, new_thesis_units):
    df = load_data()
    student = df[df["student_number"] == student_number].iloc[0]
    current = float(student["thesis_units_taken"]) if pd.notna(student["thesis_units_taken"]) else 0
    base_limit = get_thesis_limit_from_program(student["program"])
    extension = student.get("thesis_extension_units", 0)
    limit = base_limit + extension
    if current + new_thesis_units > limit:
        remaining = limit - current
        return False, f"Thesis unit limit would be exceeded: {current} + {new_thesis_units} > {limit}. Only {remaining} unit(s) remaining. If you need extension, request staff approval."
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
        return False, f"Residency exceeded: {years_used} > {max_with_extension} years. Please request extension from Graduate School."
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

def check_external_reviewer_required(student_number):
    students = load_data()
    student = students[students["student_number"] == student_number].iloc[0]
    if is_phd_program(student["program"]):
        reviewer = student.get("external_reviewer", "")
        if not reviewer or reviewer == "":
            return False, "Cannot complete Final Examination/Defense: No external reviewer assigned. Please contact your adviser."
    return True, ""

def load_final_exam_votes():
    if not os.path.exists(FINAL_EXAM_VOTES_FILE) or os.path.getsize(FINAL_EXAM_VOTES_FILE) == 0:
        return pd.DataFrame(columns=["student_number", "milestone", "voter_name", "vote", "voter_role", "vote_date"])
    return pd.read_csv(FINAL_EXAM_VOTES_FILE)

def save_final_exam_votes(df):
    df.to_csv(FINAL_EXAM_VOTES_FILE, index=False)

def record_final_exam_vote(student_number, voter_name, vote, voter_role="Committee"):
    df = load_final_exam_votes()
    new_row = pd.DataFrame([{
        "student_number": student_number,
        "milestone": "Final Examination",
        "voter_name": voter_name,
        "vote": vote,
        "voter_role": voter_role,
        "vote_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    save_final_exam_votes(df)
    votes_df = load_final_exam_votes()
    student_votes = votes_df[votes_df["student_number"] == student_number]
    negative_count = len(student_votes[student_votes["vote"] == "Negative"])
    if negative_count > 1:
        students = load_data()
        students.loc[students["student_number"] == student_number, "final_exam_status"] = "Failed"
        save_data(students)
        return False, f"Final Examination failed: {negative_count} negative votes. Re-examination may be allowed."
    return True, ""

# ==================== SEMESTER & ACADEMIC FUNCTIONS ====================
def add_semester_record(student_number, ay, sem, subjects, doc_path="", doc_upload_time="", semester_status="Regular"):
    df = load_data()
    student = df[df["student_number"] == student_number].iloc[0]
    sems = get_student_semesters(student_number)
    semester_count = len(sems)
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
    if semester not in sem_order: return academic_year, "1st Sem"
    idx = sem_order.index(semester)
    if idx < 2: return academic_year, sem_order[idx+1]
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
    filename = f"{student_number}.{ext}"
    filepath = os.path.join(PROFILE_PIC_FOLDER, filename)
    with open(filepath, "wb") as f: f.write(uploaded_file.getbuffer())
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
    committee_milestones = ["Guidance Committee Members", "Guidance Committee Formation", "Advisory Committee Formation", "Supervisory Committee Formation"]
    if milestone in committee_milestones and status == "Approved":
        chair_name = get_committee_chair(student_number)
        if not chair_name:
            return False, "No committee chair found. Cannot approve."
        if chair_name not in USERS or USERS[chair_name]["role"] != "Faculty Adviser":
            return False, f"Committee Chair '{chair_name}' is not a valid faculty adviser in the system. Please contact staff to add them."
        df_students = load_data()
        student_row = df_students[df_students["student_number"] == student_number]
        if student_row.empty:
            return False, "Student not found."
        current_advisor = student_row.iloc[0]["advisor"]
        create_transfer_request(student_number, current_advisor, chair_name, milestone)
        st.success(f"Committee approved. A transfer request has been sent to {chair_name}. The student will remain under {current_advisor} until {chair_name} accepts the transfer.")
    
    if milestone == "Plan of Study (POS)" and status == "Approved":
        df_students = load_data()
        idx = df_students[df_students["student_number"] == student_number].index
        if len(idx) > 0:
            if df_students.at[idx[0], "pos_status"] != "Approved":
                df_students.at[idx[0], "pos_status"] = "Approved"
                df_students.at[idx[0], "pos_approval_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_data(df_students)
                st.success("✅ POS has been approved. Student can now enroll in the second semester.")
        else:
            return False, "Student record not found."
    
    if milestone in ["Final Examination", "Final Defense"] and status == "Approved":
        ok, msg = check_external_reviewer_required(student_number)
        if not ok:
            return False, msg
        ok, msg = check_residency_enforcement(student_number)
        if isinstance(ok, bool) and not ok:
            return False, msg
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
    if uploaded_file is None: return None
    folder = os.path.join(UPLOAD_FOLDER, student_number, "milestones")
    os.makedirs(folder, exist_ok=True)
    ext = uploaded_file.name.split('.')[-1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = milestone_name.replace(" ", "_").replace("/", "_")
    filename = f"{safe_name}_{timestamp}.{ext}"
    filepath = os.path.join(folder, filename)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filepath

# ==================== DATA REQUESTS ====================
def load_data_requests():
    if not os.path.exists(DATA_REQUEST_FILE) or os.path.getsize(DATA_REQUEST_FILE) == 0:
        return pd.DataFrame(columns=["request_id","student_number","request_type","details","status","submitted_date","reviewer_comment","reviewed_by","review_date"])
    df = pd.read_csv(DATA_REQUEST_FILE, dtype=str)
    for col in df.columns:
        df[col] = df[col].fillna("").astype(str)
    return df

def save_data_requests(df):
    df.to_csv(DATA_REQUEST_FILE, index=False)

def submit_data_request(student_number, request_type, details):
    df = load_data_requests()
    req_id = len(df) + 1 if not df.empty else 1
    new = pd.DataFrame([{
        "request_id": req_id,
        "student_number": student_number,
        "request_type": request_type,
        "details": details,
        "status": "Pending",
        "submitted_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reviewer_comment": "",
        "reviewed_by": "",
        "review_date": ""
    }])
    df = pd.concat([df, new], ignore_index=True)
    save_data_requests(df)

# ==================== UPLOADS HANDLING ====================
UPLOAD_CATEGORIES = ["admission_letter", "amis_screenshot", "committee_form", "plan_of_study", "thesis_file"]
UPLOAD_DISPLAY_NAMES = {
    "admission_letter": "Admission Letter",
    "amis_screenshot": "AMIS Screenshot",
    "committee_form": "Committee Form",
    "plan_of_study": "Plan of Study (POS)",
    "thesis_file": "Thesis/Dissertation File"
}

def load_uploads():
    if not os.path.exists(UPLOAD_FILE) or os.path.getsize(UPLOAD_FILE) == 0:
        return pd.DataFrame(columns=["student_number", "category", "file_path", "original_filename", "upload_date", "status", "reviewer_comment", "reviewed_by", "review_date"])
    df = pd.read_csv(UPLOAD_FILE, dtype=str)
    for col in df.columns:
        df[col] = df[col].fillna("").astype(str)
    return df

def save_uploads(df):
    df.to_csv(UPLOAD_FILE, index=False)

def save_uploaded_file(student_number, category, uploaded_file):
    if uploaded_file is None: return None
    student_folder = os.path.join(UPLOAD_FOLDER, student_number)
    os.makedirs(student_folder, exist_ok=True)
    ext = uploaded_file.name.split('.')[-1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{category}_{timestamp}.{ext}"
    filepath = os.path.join(student_folder, filename)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    up_df = load_uploads()
    new_up = pd.DataFrame([{
        "student_number": student_number,
        "category": category,
        "file_path": filepath,
        "original_filename": uploaded_file.name,
        "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Pending",
        "reviewer_comment": "",
        "reviewed_by": "",
        "review_date": ""
    }])
    up_df = pd.concat([up_df, new_up], ignore_index=True)
    save_uploads(up_df)
    return filepath

# ==================== UI HELPERS ====================
def get_status_badge(status):
    if status == "Approved":
        return '<span class="status-badge status-approved">✅ Approved</span>'
    elif status == "Rejected":
        return '<span class="status-badge status-rejected">❌ Rejected</span>'
    elif status == "Pending":
        return '<span class="status-badge status-pending">🟡 Pending</span>'
    else:
        return '<span class="status-badge status-not-started">⚪ Not Started</span>'

def filter_dataframe(search_term, data):
    if not search_term: return data
    mask = data["name"].str.contains(search_term, case=False, na=False) | data["student_number"].str.contains(search_term, case=False, na=False)
    return data[mask]

# ==================== RENDER SEMESTER BLOCK ====================
def render_semester_block_general(student_number, semester_row, is_staff=False, override_edit=False):
    ay = str(semester_row["academic_year"])
    sem = str(semester_row["semester"])
    semester_status = str(semester_row.get("semester_status","Regular")).strip()
    if semester_status not in SEMESTER_STATUS_OPTIONS: semester_status = "Regular"
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
        can_edit_status = (is_staff and override_edit) or (not is_staff)
        if can_edit_status:
            new_status = st.selectbox("Semester Status", SEMESTER_STATUS_OPTIONS,
                                      index=SEMESTER_STATUS_OPTIONS.index(semester_status) if semester_status in SEMESTER_STATUS_OPTIONS else 0,
                                      key=f"status_{student_number}_{ay}_{sem}")
            if new_status != semester_status:
                if update_semester_status(student_number, ay, sem, new_status):
                    st.success(f"Status updated to {new_status}.")
                    st.rerun()
        else:
            st.markdown(f"**Semester Status:** {semester_status}")
        
        st.markdown(f"**Document Validation:** {get_status_badge(doc_status)}", unsafe_allow_html=True)
        if doc_status == "Rejected" and doc_remarks:
            st.warning(f"Rejection reason: {doc_remarks}")
        
        if semester_status == "Regular" and (not is_staff or (is_staff and override_edit)):
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
        elif semester_status != "Regular":
            st.info(f"Semester marked as **{semester_status}**. Subject input disabled.")
            if subjects:
                st.dataframe(pd.DataFrame(subjects), use_container_width=True, hide_index=True)
        else:
            st.info("Editing is disabled because you do not have permission.")
        
        # ---- Document upload and validation ----
        st.markdown("---")
        st.markdown("**Upload Proof of Grades (AMIS Screenshot)**")
        if semester_status == "Regular":
            if doc_path and doc_path != "" and os.path.exists(doc_path):
                st.info(f"Current file: {os.path.basename(doc_path)}")
            if not is_staff:
                with st.form(key=f"upload_{student_number}_{ay}_{sem}"):
                    uploaded = st.file_uploader("Choose file (PDF/JPG/PNG)", type=["pdf","jpg","jpeg","png"], key=f"upload_file_{ay}_{sem}")
                    if st.form_submit_button("📎 Upload Document") and uploaded:
                        folder = os.path.join(UPLOAD_FOLDER, student_number, "semester_docs")
                        os.makedirs(folder, exist_ok=True)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{ay}_{sem}_{timestamp}.{uploaded.name.split('.')[-1].lower()}"
                        filepath = os.path.join(folder, filename)
                        with open(filepath, "wb") as f:
                            f.write(uploaded.getbuffer())
                        if update_semester_document(student_number, ay, sem, filepath, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Pending"):
                            st.success("Document uploaded! Pending validation.")
                            st.rerun()
            else:
                if doc_path and doc_path != "" and os.path.exists(doc_path):
                    st.caption("Document uploaded by student.")
                if doc_status == "Pending":
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
        
        # ---- POS Management Section (Staff/Adviser only) ----
        if is_staff and (override_edit or st.session_state.role in ["SESAM Staff", "Faculty Adviser"]):
            st.markdown("---")
            st.markdown("#### 📋 Plan of Study (POS) for this Semester")
            pos_status = semester_row.get("pos_approved_status", "")
            if pos_status == "Approved":
                st.success("✅ This semester's POS is approved.")
                if pos_courses:
                    st.write("**Approved courses:**", ", ".join(pos_courses))
                else:
                    st.info("No specific courses listed in POS (free elective semester).")
                if st.button("✏️ Edit/Update POS", key=f"edit_pos_{student_number}_{ay}_{sem}"):
                    st.session_state[f"edit_pos_{student_number}_{ay}_{sem}"] = True
            else:
                if pos_status == "Pending":
                    st.warning("POS Pending approval.")
                else:
                    st.info("No POS submitted for this semester yet.")
                if st.button("📝 Manage POS", key=f"manage_pos_{student_number}_{ay}_{sem}"):
                    st.session_state[f"edit_pos_{student_number}_{ay}_{sem}"] = True
            
            if st.session_state.get(f"edit_pos_{student_number}_{ay}_{sem}", False):
                with st.form(key=f"pos_form_{student_number}_{ay}_{sem}"):
                    current_codes = pos_courses if pos_courses else []
                    pos_codes_input = st.text_input("Course codes (comma-separated)", value=", ".join(current_codes))
                    new_approval_status = st.selectbox("Approval Status", ["Pending", "Approved", "Rejected"], index=["Pending","Approved","Rejected"].index(pos_status) if pos_status in ["Pending","Approved","Rejected"] else 0)
                    if st.form_submit_button("Save POS"):
                        new_codes = [c.strip() for c in pos_codes_input.split(",") if c.strip()]
                        set_pos_for_semester(student_number, ay, sem, new_codes, new_approval_status, st.session_state.display_name)
                        st.success("POS updated.")
                        st.session_state[f"edit_pos_{student_number}_{ay}_{sem}"] = False
                        st.rerun()

def render_profile_approval_section(student, is_staff=False):
    if student.get("profile_pending_status") == "Pending" and is_staff:
        st.markdown("#### Pending Profile Update")
        pending_fields = []
        if student.get("profile_pending_address"): pending_fields.append(("Address", student["profile_pending_address"]))
        if student.get("profile_pending_phone"): pending_fields.append(("Phone", student["profile_pending_phone"]))
        if student.get("profile_pending_email"): pending_fields.append(("Institutional Email", student["profile_pending_email"]))
        if student.get("profile_pending_gender"): pending_fields.append(("Gender", student["profile_pending_gender"]))
        if student.get("profile_pending_civil_status"): pending_fields.append(("Civil Status", student["profile_pending_civil_status"]))
        if student.get("profile_pending_citizenship"): pending_fields.append(("Citizenship", student["profile_pending_citizenship"]))
        if student.get("profile_pending_birthdate"): pending_fields.append(("Birthdate", student["profile_pending_birthdate"]))
        if student.get("profile_pending_religion"): pending_fields.append(("Religion", student["profile_pending_religion"]))
        if student.get("profile_pending_emergency_name"): pending_fields.append(("Emergency Name", student["profile_pending_emergency_name"]))
        if student.get("profile_pending_emergency_relationship"): pending_fields.append(("Emergency Relationship", student["profile_pending_emergency_relationship"]))
        if student.get("profile_pending_emergency_country_code"): pending_fields.append(("Emergency Country Code", student["profile_pending_emergency_country_code"]))
        if student.get("profile_pending_emergency_phone"): pending_fields.append(("Emergency Phone", student["profile_pending_emergency_phone"]))
        for label, value in pending_fields:
            st.write(f"**{label}:** {value}")
        remarks = st.text_area("Remarks", key="prof_remarks")
        col1, col2 = st.columns(2)
        if col1.button("✅ Approve Profile Update"):
            df = load_data()
            for field in ["address","phone","institutional_email","gender","civil_status","citizenship","birthdate","religion",
                          "emergency_name","emergency_relationship","emergency_country_code","emergency_phone"]:
                pending_field = f"profile_pending_{field}"
                if pending_field in student and student[pending_field]:
                    df.loc[df["student_number"]==student["student_number"], field] = student[pending_field]
            df.loc[df["student_number"]==student["student_number"], "profile_pending_status"] = "Approved"
            df.loc[df["student_number"]==student["student_number"], "profile_pending_remarks"] = remarks
            save_data(df)
            st.success("Profile approved.")
            st.rerun()
        if col2.button("❌ Reject Profile Update"):
            df = load_data()
            df.loc[df["student_number"]==student["student_number"], "profile_pending_status"] = "Rejected"
            df.loc[df["student_number"]==student["student_number"], "profile_pending_remarks"] = remarks
            save_data(df)
            st.warning("Profile rejected.")
            st.rerun()
    elif student.get("profile_pending_status") == "Rejected":
        st.error(f"Profile update rejected: {student.get('profile_pending_remarks','')}")

# ==================== REGISTRATION FORM ====================
def register_new_student_form():
    if st.session_state.get("reg_success", False):
        st.success("✅ Student successfully registered!")
        st.session_state.reg_success = False

    with st.form("register_student_form"):
        st.subheader("Register New Student")
        col1, col2 = st.columns(2)
        with col1:
            student_number = st.text_input("Student Number *")
            last_name = st.text_input("Last Name *")
            first_name = st.text_input("First Name *")
            middle_name = st.text_input("Middle Name (optional)")
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
                    "external_reviewer": "",
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
                    "gender": "",
                    "civil_status": "",
                    "citizenship": "",
                    "birthdate": "",
                    "religion": "",
                    "emergency_name": "",
                    "emergency_relationship": "",
                    "emergency_country_code": "",
                    "emergency_phone": "",
                    "special_status": "Regular",
                    "profile_pending_status": "",
                    "profile_pending_remarks": "",
                    "profile_pending_address": "",
                    "profile_pending_phone": "",
                    "profile_pending_email": "",
                    "profile_pending_gender": "",
                    "profile_pending_civil_status": "",
                    "profile_pending_citizenship": "",
                    "profile_pending_birthdate": "",
                    "profile_pending_religion": "",
                    "profile_pending_emergency_name": "",
                    "profile_pending_emergency_relationship": "",
                    "profile_pending_emergency_country_code": "",
                    "profile_pending_emergency_phone": "",
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                get_student_milestones(student_number, get_program_type(program))
                
                # Create only the first (admission) semester
                try:
                    add_semester_record(student_number, f"{ay_start}-{ay_start+1}", semester, [], semester_status="Regular")
                except Exception as e:
                    st.error(f"Could not create initial semester: {e}")
                else:
                    st.session_state.reg_success = True
                    st.rerun()

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

# ==================== PROFILE CONTENT RENDERER (COMPACT) ====================
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
            if not is_own_profile:
                st.markdown(f"**External Reviewer:** {student.get('external_reviewer','Not assigned')}")
        
        if student.get("pos_status") == "Approved" and student.get("pos_approval_date"):
            st.caption(f"✅ POS approved on: {student['pos_approval_date']}")
    
    st.markdown("---")
    st.markdown("#### 📞 Contact & Personal Information")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Address:** {student['address'] or '—'}")
        st.markdown(f"**Phone:** {student['phone'] or '—'}")
        st.markdown(f"**Email:** {student['institutional_email'] or '—'}")
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
# ==================== POS SUBMISSIONS FUNCTIONS (UPDATED) ====================

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
            df[col] = ""
    df["submission_id"] = pd.to_numeric(df["submission_id"], errors='coerce').fillna(0).astype(int)
    df["version"] = pd.to_numeric(df["version"], errors='coerce').fillna(0).astype(int)
    df["adviser_approved"] = df["adviser_approved"].astype(bool) if "adviser_approved" in df.columns else False
    df["gs_approved"] = df["gs_approved"].astype(bool) if "gs_approved" in df.columns else False
    if "submission_type" not in df.columns:
        df["submission_type"] = ""
    return df

def save_pos_submissions(df):
    df.to_csv(POS_SUBMISSIONS_FILE, index=False)

def get_pos_submissions(student_number):
    df = load_pos_submissions()
    return df[df["student_number"] == student_number].sort_values("submission_id", ascending=False)

def get_original_pos(student_number):
    """Return the first approved submission (version 1, status Approved) as the Original POS."""
    df = load_pos_submissions()
    original = df[(df["student_number"] == student_number) & 
                  (df["version"] == 1) & 
                  (df["status"] == "Approved")]
    if original.empty:
        return None
    return original.iloc[0]

def get_revisions(student_number):
    """Return all submissions with version >= 2, sorted by version descending."""
    df = load_pos_submissions()
    revisions = df[(df["student_number"] == student_number) & (df["version"] >= 2)]
    return revisions.sort_values("version", ascending=False)

def submit_pos_document(student_number, uploaded_file, submission_type="revision"):
    """Submit a new POS document. For original, use submission_type='original' (first submission)."""
    if uploaded_file is None:
        return False
    df = load_pos_submissions()
    student_submissions = df[df["student_number"] == student_number]
    if student_submissions.empty:
        new_id = 1
        version = 1
        # First submission is always original
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
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
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
    return True

def approve_pos_revision(submission_id, reviewer_name, remarks, role):
    """
    Approve a revision. Role can be 'adviser' or 'gs'.
    Adviser approval sets adviser_approved = True.
    GS approval sets gs_approved = True and status = 'GS Approved'.
    """
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
        return True, "Revision approved by adviser. Awaiting GS approval."
    elif role == "gs":
        df.loc[mask, "gs_approved"] = True
        df.loc[mask, "status"] = "GS Approved"
        df.loc[mask, "approved_by"] = reviewer_name
        df.loc[mask, "approval_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if remarks:
            df.loc[mask, "remarks"] = remarks
        save_pos_submissions(df)
        # Update milestone status
        student_number = row["student_number"]
        update_pos_milestone_status(student_number)
        return True, "Revision approved by Graduate School."
    else:
        return False, "Invalid role."

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

# ==================== RENDER POS MILESTONE (SIDE-BY-SIDE) ====================
# ==================== RENDER POS MILESTONE (SIDE-BY-SIDE, SWAPPED, WITH UNIQUE KEYS) ====================

def render_pos_milestone(student_number, viewer_role, is_own_view=False):
    # Generate a unique suffix for this function call to avoid duplicate form keys
    if "_pos_form_counter" not in st.session_state:
        st.session_state._pos_form_counter = 0
    st.session_state._pos_form_counter += 1
    form_suffix = st.session_state._pos_form_counter

    original = get_original_pos(student_number)
    revisions = get_revisions(student_number)
    
    can_submit = (is_own_view or viewer_role == "SESAM Staff")
    is_adviser = (viewer_role == "Faculty Adviser")
    is_staff = (viewer_role == "SESAM Staff")
    
    st.markdown("## Plan of Study (POS) – Version Control")
    
    # Two columns: LEFT = ORIGINAL, RIGHT = REVISIONS
    col_left, col_right = st.columns(2, gap="large")
    
    # ==================== LEFT COLUMN: ORIGINAL POS (GS baseline) ====================
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
                                if submit_pos_document(student_number, uploaded_file, submission_type="original"):
                                    st.success("Initial POS submitted. Awaiting GS approval.")
                                    st.rerun()
                                else:
                                    st.error("Submission failed.")
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
            
            # Adviser verification (only for advisers, not for students)
            if is_adviser and not is_own_view:
                st.markdown("---")
                st.markdown("#### 🔍 Adviser Verification")
                if "original_verified" not in st.session_state:
                    st.session_state.original_verified = False
                if not st.session_state.original_verified:
                    if st.button("✅ Mark as Verified (I have reviewed the original POS)"):
                        st.session_state.original_verified = True
                        st.success("You have verified the original POS. Thank you.")
                else:
                    st.info("You have already verified this original POS.")
    
    # ==================== RIGHT COLUMN: REVISED POS ====================
    with col_right:
        st.markdown("### 📝 Revised POS (Updated Versions)")
        st.caption("Student proposes changes → Adviser reviews → GS approves")
        
        if revisions.empty:
            st.info("No revised POS submissions yet.")
        else:
            for _, rev in revisions.iterrows():
                with st.container(border=True):
                    st.markdown(f"**Version {rev['version']}** – Uploaded: {rev['upload_date']}")
                    status = rev["status"]
                    if status == "Pending":
                        st.warning("🟡 Status: Pending (Awaiting Adviser Review)")
                    elif status == "Adviser Approved":
                        st.info("🔵 Status: Adviser Approved – Awaiting GS Approval")
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
                    
                    # Approval actions based on role and current status
                    if is_adviser and status == "Pending":
                        with st.form(key=f"adviser_rev_{rev['submission_id']}_{form_suffix}"):
                            remarks = st.text_area("Remarks (optional)", key=f"rev_remarks_{rev['submission_id']}_{form_suffix}")
                            if st.form_submit_button("✅ Approve as Adviser", use_container_width=True):
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
                    elif is_staff and status == "Adviser Approved":
                        with st.form(key=f"gs_rev_{rev['submission_id']}_{form_suffix}"):
                            remarks = st.text_area("Remarks (optional)", key=f"gs_rev_remarks_{rev['submission_id']}_{form_suffix}")
                            if st.form_submit_button("🏛️ Approve as Graduate School", use_container_width=True):
                                success, msg = approve_pos_revision(rev['submission_id'], st.session_state.display_name, remarks, "gs")
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
        
        # Submit new revision
        if can_submit:
            st.markdown("---")
            st.markdown("### 📤 Submit Revised POS")
            with st.form(key=f"submit_revision_{student_number}_{form_suffix}"):
                uploaded_file = st.file_uploader("Upload revised POS (PDF/JPG/PNG) - Max 5MB", type=["pdf","jpg","jpeg","png"], key=f"revised_pos_{student_number}_{form_suffix}")
                if st.form_submit_button("Submit Revised Version", use_container_width=True):
                    if uploaded_file:
                        if uploaded_file.size > 5 * 1024 * 1024:
                            st.error("File size exceeds 5MB.")
                        else:
                            if submit_pos_document(student_number, uploaded_file, submission_type="revision"):
                                st.success("Revised POS submitted for review.")
                                st.rerun()
                            else:
                                st.error("Submission failed.")
                    else:
                        st.error("Please select a file.")
    
    st.markdown("---")
    st.caption("Note: The original POS is the first version approved by GS. Revisions go through Adviser → GS approval.")

# ==================== UNIFIED STUDENT PROFILE VIEW ====================
def view_student_profile(student_number, viewer_role):
    df = load_data()
    student = df[df["student_number"] == student_number].iloc[0].copy()
    program_type = get_program_type(student["program"])
    
    is_staff = (viewer_role == "SESAM Staff")
    
    can_edit_subjects = False
    if is_staff:
        if student["advisor"] == "Not assigned":
            can_edit_subjects = True
            st.info("ℹ️ No adviser assigned. You can edit this student's records directly.")
        else:
            st.warning(f"⚠️ Adviser assigned: {student['advisor']}. Editing is restricted.")
            override = st.checkbox("🔓 Override restrictions (admin override)")
            if override:
                can_edit_subjects = True
                st.info("Override active – you can now edit this student's subjects and add semesters.")
    
    resid_status, used, max_y = check_residency_alert(student)
    if resid_status == "exceeded":
        st.markdown(f'<div class="danger-banner">⚠️ RESIDENCY EXCEEDED: {used} years used (max {max_y}). Action required.</div>', unsafe_allow_html=True)
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
        tab_names.append("⚙️ Admin Controls")
    tabs = st.tabs(tab_names)
    
    with tabs[0]:
        render_compact_profile(student, is_own_profile=False)
        if is_staff:
            render_profile_approval_section(student, is_staff=True)
        if is_staff:
            st.markdown("---")
            st.markdown("#### ℹ️ Staff Note")
            st.info("Profile editing is not allowed. To change temporary adviser or external reviewer, use the **Admin Controls** tab.")
        else:
            st.markdown(f"**External Reviewer:** {student.get('external_reviewer','Not assigned')}")
    
    # ---- Coursework Tab (with POS warnings and on‑demand semester creation) ----
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
            render_semester_block_general(student_number, row, is_staff=True, override_edit=can_edit_subjects)
        
        if can_edit_subjects and len(semesters) < total_terms:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("➕ Add Next Semester (Staff Only)"):
                    last_sem = semesters.iloc[-1] if not semesters.empty else None
                    if last_sem is not None:
                        create_next_semester(student_number, last_sem["academic_year"], last_sem["semester"])
                    else:
                        create_next_semester(student_number, timeline[0][0], timeline[0][1])
                    st.rerun()
            with col2:
                if st.button("📅 Create All Missing Semesters (Bulk)") and can_edit_subjects:
                    for ay, sem in timeline:
                        if not ((existing_sems["academic_year"] == ay) & (existing_sems["semester"] == sem)).any():
                            try:
                                add_semester_record(student_number, ay, sem, [], semester_status="Regular")
                            except ValueError as e:
                                st.error(f"Could not create {ay} {sem}: {e}")
                                break
                    st.success("All missing semesters created (where allowed by policy).")
                    st.rerun()
        elif can_edit_subjects:
            st.success("✅ All required semesters have been created. Student may still need to enroll in subjects.")
        
        st.markdown("---")
        cola, colb, colc, cold = st.columns(4)
        cola.metric("Units Taken", student["total_units_taken"])
        colb.metric("Required Units", student["total_units_required"])
        colc.metric("Remaining", max(0, student["total_units_required"] - student["total_units_taken"]))
        gwa_val = student["gwa"] if pd.notna(student["gwa"]) else None
        cold.metric("Cumulative GWA", f"{gwa_val:.2f}" if gwa_val is not None else "—")
    
    # ---- Milestone Tabs ----
    milestones_df = get_student_milestones(student_number, program_type)
    for i, milestone_name in enumerate(milestone_list):
        with tabs[2 + i]:
            if milestone_name == "Plan of Study (POS)":
                render_pos_milestone(student_number, viewer_role, is_own_view=False)
            else:
                milestone_row = milestones_df[milestones_df["milestone"] == milestone_name].iloc[0]
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
                
                # Committee milestone with two‑panel layout
                if milestone_name in ["Guidance Committee Members", "Guidance Committee Formation", "Advisory Committee Formation", "Supervisory Committee Formation"]:
                    committee_members = get_committee_members(student_number)
                    
                    # Two-column layout: left = member list, right = management
                    col_left, col_right = st.columns([1, 1])
                    
                    with col_left:
                        st.markdown("#### 📋 Committee Members")
                        if committee_members:
                            for member in committee_members:
                                st.write(f"- **{member.get('name', '')}** ({member.get('role', 'Member')})")
                        else:
                            st.info("No committee members added yet.")
                    
                    with col_right:
                        st.markdown("#### ✏️ Manage Committee")
                        if status != "Approved":
                            edit_key = f"committee_edit_{student_number}"
                            if edit_key not in st.session_state:
                                st.session_state[edit_key] = committee_members.copy() if committee_members else []
                            
                            remove_indices = []
                            for idx, member in enumerate(st.session_state[edit_key]):
                                with st.container():
                                    col_name, col_role, col_del = st.columns([2, 1.5, 0.5])
                                    with col_name:
                                        new_name = st.text_input("Name", value=member.get("name", ""), key=f"name_{idx}_{student_number}", placeholder="Firstname Lastname")
                                    with col_role:
                                        new_role = st.selectbox("Role", ["Chair", "Co-chair", "Member"], index=["Chair","Co-chair","Member"].index(member.get("role", "Member")), key=f"role_{idx}_{student_number}")
                                    with col_del:
                                        if st.button("🗑️", key=f"remove_{idx}_{student_number}"):
                                            remove_indices.append(idx)
                                    st.session_state[edit_key][idx] = {"name": new_name, "role": new_role}
                            
                            for idx in sorted(remove_indices, reverse=True):
                                st.session_state[edit_key].pop(idx)
                                st.rerun()
                            
                            if st.button("➕ Add Committee Member"):
                                st.session_state[edit_key].append({"name": "", "role": "Member"})
                                st.rerun()
                            
                            if st.button("💾 Save Committee Members"):
                                chairs = [m for m in st.session_state[edit_key] if m.get("role") == "Chair"]
                                if len(chairs) != 1:
                                    st.error("Committee must have exactly one Chair.")
                                elif any(not m.get("name", "").strip() for m in st.session_state[edit_key]):
                                    st.error("All members must have a name (Firstname Lastname).")
                                else:
                                    valid, msg = set_committee_members(student_number, st.session_state[edit_key])
                                    if valid:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                        else:
                            st.info("Committee already approved. No further changes allowed.")
                    
                    st.markdown("---")
                    
                    if status == "Not Started":
                        st.warning("⚠️ **Requirement not yet submitted.** Please upload the required document and submit for approval.")
                    
                    if status != "Approved":
                        with st.form(key=f"submit_{milestone_name}_{student_number}"):
                            st.markdown("**Required document:** Please upload the official form or certificate for this milestone.")
                            uploaded_file = st.file_uploader(
                                "Upload document (PDF/JPG/PNG) - Max 5MB",
                                type=["pdf", "jpg", "jpeg", "png"],
                                key=f"upload_{milestone_name}_{student_number}"
                            )
                            date_completed = st.date_input("Date of completion/event", value=date.today())
                            if st.form_submit_button("Submit for Approval", use_container_width=True):
                                if not uploaded_file:
                                    st.error("Please upload a document.")
                                elif uploaded_file.size > 5 * 1024 * 1024:
                                    st.error("File size exceeds 5MB. Please compress or choose a smaller file.")
                                else:
                                    filepath = save_milestone_file(student_number, milestone_name, uploaded_file)
                                    success, msg = update_milestone(student_number, milestone_name, "Pending", date_completed.strftime("%Y-%m-%d"), filepath, "", None)
                                    if success:
                                        st.success(f"{milestone_name} submitted for approval.")
                                        st.rerun()
                                    else:
                                        st.error(msg)
                    else:
                        st.success("✅ This milestone has been approved.")
                
                # Non‑committee milestones (unchanged)
                else:
                    if status == "Not Started":
                        st.warning("⚠️ **Requirement not yet submitted.** Please upload the required document and submit for approval.")
                    
                    if status != "Approved":
                        if viewer_role == "Student" or (viewer_role == "SESAM Staff"):
                            with st.form(key=f"submit_{milestone_name}_{student_number}"):
                                st.markdown("**Required document:** Please upload the official form or certificate for this milestone.")
                                uploaded_file = st.file_uploader("Upload document (PDF/JPG/PNG) - Max 5MB", type=["pdf","jpg","jpeg","png"], key=f"upload_{milestone_name}_{student_number}")
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
                                            st.success(f"{milestone_name} submitted for approval.")
                                            st.rerun()
                                        else:
                                            st.error(msg)
                        else:
                            st.info("Only the student or staff can submit milestone requirements.")
                    
                    if status == "Pending" and viewer_role == "Faculty Adviser":
                        st.markdown("---")
                        st.markdown("**Review this milestone**")
                        with st.form(key=f"review_{milestone_name}_{student_number}"):
                            review_remarks = st.text_area("Remarks (optional)", key=f"review_remarks_{milestone_name}_{student_number}")
                            col_app, col_rej = st.columns(2)
                            if col_app.form_submit_button("✅ Approve", use_container_width=True):
                                success, msg = update_milestone(student_number, milestone_name, "Approved", None, None, review_remarks, st.session_state.display_name)
                                if success:
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
    
    # ---- Admin Controls Tab (Staff only) ----
    if is_staff:
        with tabs[-1]:
            st.subheader("Administrative Controls")
            st.markdown("**Change Temporary Adviser**")
            adviser_options = ["Not assigned", "Dr. Eslava", "Dr. Sanchez"]
            new_advisor = st.selectbox("Select adviser", adviser_options, index=adviser_options.index(student["advisor"]) if student["advisor"] in adviser_options else 0)
            if st.button("Update Temporary Adviser"):
                df = load_data()
                df.loc[df["student_number"] == student_number, "advisor"] = new_advisor
                save_data(df)
                st.success(f"Temporary adviser updated to {new_advisor}")
                st.rerun()
            st.markdown("**Change Program**")
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
            st.markdown("**Special Student Status**")
            status_options = ["Regular", "Transferred", "Shifted", "On Leave", "Inactive", "Deleted"]
            current_special = student.get("special_status", "Regular")
            new_special = st.selectbox("Status", status_options, index=status_options.index(current_special) if current_special in status_options else 0)
            if st.button("Update Special Status"):
                df = load_data()
                df.loc[df["student_number"] == student_number, "special_status"] = new_special
                save_data(df)
                st.success("Special status updated.")
                st.rerun()
            st.markdown("**POS Status Override**")
            pos_status = st.selectbox("POS Status", ["Approved", "Pending", "Rejected", "Not Started"], index=["Approved","Pending","Rejected","Not Started"].index(student.get("pos_status","Pending")))
            if st.button("Update POS Status"):
                df = load_data()
                df.loc[df["student_number"] == student_number, "pos_status"] = pos_status
                save_data(df)
                st.success(f"POS status updated to {pos_status}")
                st.rerun()
            st.markdown("**Thesis & Residency Extensions**")
            current_ext = student.get("thesis_extension_units", 0)
            st.write(f"Thesis extension units: {current_ext} / 6")
            if st.button("➕ Grant 1 Thesis Extension Unit"):
                if current_ext < 6:
                    df = load_data()
                    df.loc[df["student_number"] == student_number, "thesis_extension_units"] = current_ext + 1
                    save_data(df)
                    st.success("Thesis extension unit granted.")
                    st.rerun()
                else:
                    st.error("Maximum reached.")
            current_res_ext = student.get("residency_extension_years", 0)
            st.write(f"Residency extension years: {current_res_ext}")
            if st.button("➕ Grant 1 Residency Extension Year"):
                df = load_data()
                df.loc[df["student_number"] == student_number, "residency_extension_years"] = current_res_ext + 1
                save_data(df)
                st.success("Residency extended by 1 year.")
                st.rerun()

# ==================== STUDENT DASHBOARD (self view) ====================
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
    st.info("ℹ️ **Note:** The adviser shown above is a **temporary adviser** assigned upon admission. Once your Guidance/Advisory Committee is formed and approved, a transfer request will be sent to the Chair. You will be officially transferred only when the Chair accepts.")
    
    required_fields_missing = False
    missing_fields = []
    if not student.get("address") or student.get("address") == "":
        missing_fields.append("Address")
    if not student.get("phone") or student.get("phone") == "":
        missing_fields.append("Phone Number")
    if not student.get("institutional_email") or student.get("institutional_email") == "":
        missing_fields.append("Institutional Email")
    if missing_fields:
        required_fields_missing = True
        st.warning(f"⚠️ **Required Information Missing**\n\nPlease complete the following fields in your Profile before accessing your coursework: {', '.join(missing_fields)}")
    
    existing_sems = get_student_semesters(student["student_number"])
    if len(existing_sems) == 1 and student.get("pos_status", "Pending") != "Approved":
        st.warning("⚠️ **Action Required:** You are in your first semester. Your Plan of Study (POS) must be approved by your adviser before the end of this semester to allow enrollment in the second semester. Please work with your adviser to complete and approve your POS.")
    
    resid_status, used, max_y = check_residency_alert(student)
    if resid_status == "exceeded":
        st.markdown(f'<div class="danger-banner">⚠️ RESIDENCY EXCEEDED: {used} years used (max {max_y}). Please consult your adviser.</div>', unsafe_allow_html=True)
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
    
    milestones_df = get_student_milestones(student["student_number"], program_type)
    milestone_list = MILESTONE_DEFS.get(program_type, MILESTONE_DEFS["MS_Thesis"])
    
    tab_names = ["👤 My Profile", "📚 Coursework"] + milestone_list
    main_tabs = st.tabs(tab_names)
    
    # ---- Profile Tab ----
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
                new_email = st.text_input("Institutional Email *", value=student.get("institutional_email",""))
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
    
    # ---- Coursework Tab (with on‑demand semester creation) ----
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
            render_semester_block_general(student["student_number"], row, is_staff=False, override_edit=False)
        
        if len(semesters) < total_terms:
            pos_ok = True
            if len(semesters) >= 1 and student.get("pos_status") != "Approved":
                pos_ok = False
                st.warning("⚠️ Your Plan of Study (POS) must be approved before you can add the next semester. Please work with your adviser.")
            
            if pos_ok:
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
    
    # ---- Milestone Tabs (student view, with two‑panel committee interface) ----
    for i, milestone_name in enumerate(milestone_list):
        with main_tabs[2 + i]:
            if milestone_name == "Plan of Study (POS)":
                render_pos_milestone(student["student_number"], "Student", is_own_view=True)
            else:
                milestone_row = milestones_df[milestones_df["milestone"] == milestone_name].iloc[0]
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
                
                # Committee milestone with two‑panel layout
                if milestone_name in ["Guidance Committee Members", "Guidance Committee Formation", "Advisory Committee Formation", "Supervisory Committee Formation"]:
                    committee_members = get_committee_members(student["student_number"])
                    
                    col_left, col_right = st.columns([1, 1])
                    
                    with col_left:
                        st.markdown("#### 📋 Committee Members")
                        if committee_members:
                            for member in committee_members:
                                st.write(f"- **{member.get('name', '')}** ({member.get('role', 'Member')})")
                        else:
                            st.info("No committee members added yet.")
                    
                    with col_right:
                        st.markdown("#### ✏️ Manage Committee")
                        if status != "Approved":
                            edit_key = f"committee_edit_{student['student_number']}"
                            if edit_key not in st.session_state:
                                st.session_state[edit_key] = committee_members.copy() if committee_members else []
                            
                            remove_indices = []
                            for idx, member in enumerate(st.session_state[edit_key]):
                                with st.container():
                                    col_name, col_role, col_del = st.columns([2, 1.5, 0.5])
                                    with col_name:
                                        new_name = st.text_input("Name", value=member.get("name", ""), key=f"name_{idx}_{student['student_number']}", placeholder="Firstname Lastname")
                                    with col_role:
                                        new_role = st.selectbox("Role", ["Chair", "Co-chair", "Member"], index=["Chair","Co-chair","Member"].index(member.get("role", "Member")), key=f"role_{idx}_{student['student_number']}")
                                    with col_del:
                                        if st.button("🗑️", key=f"remove_{idx}_{student['student_number']}"):
                                            remove_indices.append(idx)
                                    st.session_state[edit_key][idx] = {"name": new_name, "role": new_role}
                            
                            for idx in sorted(remove_indices, reverse=True):
                                st.session_state[edit_key].pop(idx)
                                st.rerun()
                            
                            if st.button("➕ Add Committee Member"):
                                st.session_state[edit_key].append({"name": "", "role": "Member"})
                                st.rerun()
                            
                            if st.button("💾 Save Committee Members"):
                                chairs = [m for m in st.session_state[edit_key] if m.get("role") == "Chair"]
                                if len(chairs) != 1:
                                    st.error("Committee must have exactly one Chair.")
                                elif any(not m.get("name", "").strip() for m in st.session_state[edit_key]):
                                    st.error("All members must have a name (Firstname Lastname).")
                                else:
                                    valid, msg = set_committee_members(student["student_number"], st.session_state[edit_key])
                                    if valid:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                        else:
                            st.info("Committee already approved. No further changes allowed.")
                    
                    st.markdown("---")
                    
                    if status == "Not Started":
                        st.warning("⚠️ **Requirement not yet submitted.** Please upload the required document and submit for approval.")
                    
                    if status != "Approved":
                        with st.form(key=f"student_submit_{milestone_name}_{student['student_number']}"):
                            st.markdown("**Required document:** Please upload the official form or certificate for this milestone.")
                            uploaded_file = st.file_uploader(
                                "Upload document (PDF/JPG/PNG) - Max 5MB",
                                type=["pdf", "jpg", "jpeg", "png"],
                                key=f"upload_student_{milestone_name}_{student['student_number']}"
                            )
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
                                        st.success(f"{milestone_name} submitted for approval.")
                                        st.rerun()
                                    else:
                                        st.error(msg)
                    else:
                        st.success("✅ This milestone has been approved.")
                
                # Non‑committee milestones
                else:
                    if status == "Not Started":
                        st.warning("⚠️ **Requirement not yet submitted.** Please upload the required document and submit for approval.")
                    
                    if status != "Approved":
                        with st.form(key=f"student_submit_{milestone_name}_{student['student_number']}"):
                            st.markdown("**Required document:** Please upload the official form or certificate for this milestone.")
                            uploaded_file = st.file_uploader("Upload document (PDF/JPG/PNG) - Max 5MB", type=["pdf","jpg","jpeg","png"], key=f"upload_student_{milestone_name}_{student['student_number']}")
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
                                        st.success(f"{milestone_name} submitted for approval.")
                                        st.rerun()
                                    else:
                                        st.error(msg)
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

convert_expired_grades()
df = load_data()

with st.sidebar:
    st.markdown(f"<div style='text-align:center'><h3>👤 {st.session_state.display_name}</h3><div>{st.session_state.role}</div><div>✅ Consent given</div></div>", unsafe_allow_html=True)
    
    if st.session_state.role == "Faculty Adviser":
        transfer_df = load_transfer_requests()
        pending_for_me = transfer_df[transfer_df["requested_advisor"] == st.session_state.display_name]
        pending_count = len(pending_for_me)
        if pending_count > 0:
            st.info(f"📬 **{pending_count} pending transfer request(s)** – see below")
    
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.consent_given = False
        st.rerun()
    st.markdown("---")
    st.caption("Version 28.17 | Two‑panel committee interface + transfer workflow")

st.title("🎓 SESAM Graduate Student Lifecycle Management")
st.caption("Fully compliant with UPLB Graduate School policies. Coursework handled in its own tab; milestones can be submitted anytime.")

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
    
    transfer_df = load_transfer_requests()
    pending_for_me = transfer_df[transfer_df["requested_advisor"] == st.session_state.display_name]
    if not pending_for_me.empty:
        st.markdown("### 📬 Pending Transfer Requests")
        for _, req in pending_for_me.iterrows():
            with st.container(border=True):
                st.write(f"**Student:** {req['student_number']}")
                st.write(f"**Current Adviser:** {req['current_advisor']}")
                st.write(f"**Requested Adviser (You):** {req['requested_advisor']}")
                st.write(f"**Milestone:** {req['milestone_name']}")
                st.write(f"**Date:** {req['request_date']}")
                col_acc, col_rej = st.columns(2)
                if col_acc.button("✅ Accept", key=f"accept_{req['request_id']}"):
                    success, msg = accept_transfer_request(req['request_id'])
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                if col_rej.button("❌ Reject", key=f"reject_{req['request_id']}"):
                    success, msg = reject_transfer_request(req['request_id'])
                    if success:
                        st.warning(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        st.markdown("---")
    
    advisees = df[df["advisor"] == st.session_state.display_name].copy()
    if advisees.empty:
        st.warning("No students assigned to you.")
    else:
        all_semesters = load_semester_records()
        advisee_numbers = advisees["student_number"].tolist()
        pending_sems = all_semesters[(all_semesters["student_number"].isin(advisee_numbers)) & (all_semesters["doc_status"] == "Pending")]
        pending_count = len(pending_sems)
        profile_count = 0
        if "profile_pending_status" in advisees.columns:
            profile_count = len(advisees[advisees["profile_pending_status"] == "Pending"])
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Total Advisees", len(advisees))
        with col2: st.metric("📄 Pending Documents", pending_count)
        with col3: st.metric("👤 Pending Profiles", profile_count)
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
st.caption("SESAM KMIS v28.17 | Two‑panel committee interface + transfer workflow")
