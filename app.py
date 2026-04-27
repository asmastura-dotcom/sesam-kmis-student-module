"""
SESAM KMIS - Graduate Student Lifecycle Management System
Version: 15.0 | Clean Admin Dashboard | Tab‑based Validation | Role‑Controlled Editing
"""

import streamlit as st
import pandas as pd
import os
import json
from datetime import date, datetime

# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="SESAM KMIS", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

# ==================== CSS ====================
st.markdown("""
<style>
    .block-container { padding-top: 1rem !important; }
    .stButton button { padding: 0.2rem 0.8rem !important; font-size: 0.8rem !important; }
    .status-pending { background-color: #fff3cd; color: #856404; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.7rem; display: inline-block; }
    .status-approved { background-color: #d4edda; color: #155724; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.7rem; display: inline-block; }
    .status-rejected { background-color: #f8d7da; color: #721c24; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.7rem; display: inline-block; }
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
    st.session_state.staff_selected_student = None   # student number when staff is updating
if "staff_show_update" not in st.session_state:
    st.session_state.staff_show_update = False

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
    if program_name.startswith("MS") or program_name.startswith("Master"):
        return "MS_Thesis" if "Resilience" not in program_name or "Environmental Science" in program_name else "MS_NonThesis"
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

# ==================== HELPER FUNCTIONS ====================
SEMESTERS = ["1st Sem", "2nd Sem", "Summer"]
current_year = date.today().year
ACADEMIC_YEARS = [f"{year}-{year+1}" for year in range(current_year-5, current_year+6)]
GRADE_OPTIONS = ["1.00", "1.25", "1.50", "1.75", "2.00", "2.25", "2.50", "2.75", "3.00", "INC", "DRP", "5.00", "P", "IP"]
SEMESTER_STATUS_OPTIONS = ["Regular", "Off-Sem", "On Leave", "Shifted Program", "Transferred"]
WORKFLOW_STEPS = ["Committee", "Coursework", "Exams", "POS", "Thesis", "Defense", "Graduation"]

def get_thesis_limit_from_program(program):
    ptype = get_program_type(program)
    return 12 if ptype in ["PhD_Regular", "PhD_Straight", "PhD_Research"] else (6 if ptype == "MS_Thesis" else 0)

def get_residency_max_from_program(program): return 5 if is_master_program(program) else 7
def format_ay(ay_start, semester): return f"A.Y. {ay_start}-{ay_start+1} ({semester})"

# ==================== DATA LOADING ====================
DATA_FILE = "students.csv"
SEMESTER_FILE = "semester_records.csv"
MILESTONE_FILE = "milestone_tracking.csv"
UPLOAD_FOLDER = "student_uploads"
MILESTONE_REQUESTS_FILE = "milestone_requests.csv"
PROFILE_PIC_FOLDER = "profile_pics"

for folder in [UPLOAD_FOLDER, PROFILE_PIC_FOLDER]:
    if not os.path.exists(folder): os.makedirs(folder)

def create_demo_data():
    data = {
        "student_number": [f"S00{i}" for i in range(1,14)],
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
        "residency_years_used": [3,1,3,3,3,1,2,2,3,3,3,3,3],
        "pos_status": ["Approved","Pending","Approved","Approved","Approved","Approved","Pending","Approved","Approved","Approved","Approved","Approved","Approved"],
        "qualifying_exam_status": ["N/A","N/A","Passed","N/A","N/A","N/A","N/A","N/A","Passed","N/A","N/A","N/A","N/A"],
        "written_comprehensive_status": ["N/A","N/A","Failed","N/A","N/A","N/A","N/A","N/A","Passed","N/A","N/A","N/A","N/A"],
        "oral_comprehensive_status": ["N/A","N/A","Not Taken","N/A","N/A","N/A","N/A","N/A","Failed","N/A","N/A","N/A","N/A"],
        "general_exam_status": ["Passed","Passed","N/A","Passed","Passed","Not Taken","Not Taken","Not Taken","N/A","Passed","Passed","Passed","Passed"],
        "final_exam_status": ["Passed","Not Taken","Not Taken","Not Taken","Not Taken","Not Taken","Not Taken","Not Taken","Not Taken","Not Taken","Not Taken","Passed","Not Taken"],
        "profile_pic": [""]*13,
        "committee_members_structured": [""]*13,
        "committee_approval_date": [""]*13,
        "thesis_outline_approved": ["Yes"]*13,
        "thesis_status": ["Approved"]*13,
        "prior_ms_graduate": [False]*13,
        "student_status": ["Regular"]*13,
        "address": [""]*13,
        "phone": [""]*13,
        "emergency_contact": [""]*13,
        "profile_pending_address": [""]*13,
        "profile_pending_phone": [""]*13,
        "profile_pending_emergency": [""]*13,
        "profile_pending_status": [""]*13,
        "profile_pending_remarks": [""]*13,
        "special_status": ["Regular"]*13,   # transferred, shifted, on leave, inactive, deceased
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

    required_cols = ["prior_ms_graduate", "student_status", "address", "phone", "emergency_contact",
                     "profile_pending_address", "profile_pending_phone", "profile_pending_emergency",
                     "profile_pending_status", "profile_pending_remarks", "advisor_assigned_date", "special_status"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = "" if col != "prior_ms_graduate" else False

    numeric_cols = ["total_units_taken", "total_units_required", "thesis_units_taken", "thesis_units_limit",
                    "residency_years_used", "ay_start", "gwa"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            if col != "gwa":
                df[col] = df[col].astype(int)

    for idx, row in df.iterrows():
        prog = row["program"]
        if prog not in PROGRAMS:
            df.at[idx, "program"] = PROGRAMS[0]
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
            if sem["semester_status"] != "Regular": continue
            try:
                subjects = json.loads(sem["subjects_json"]) if sem["subjects_json"] else []
                for subj in subjects:
                    units = float(subj.get("units", 0))
                    grade = float(subj.get("grade", 0))
                    total_units += units
                    total_grade += units * grade
            except: pass
        if total_units > 0:
            df.loc[df["student_number"] == sn, "gwa"] = total_grade / total_units
            df.loc[df["student_number"] == sn, "total_units_taken"] = total_units
    save_data(df)
    return df

def save_data(df): df.to_csv(DATA_FILE, index=False)

# ==================== SEMESTER RECORDS ====================
def load_semester_records():
    if os.path.exists(SEMESTER_FILE):
        df = pd.read_csv(SEMESTER_FILE)
        text_cols = ["student_number","academic_year","semester","subjects_json","doc_path","doc_upload_time",
                     "doc_status","doc_remarks","doc_validated_by","doc_validated_time","semester_status"]
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).replace(['nan','None',''], '')
        for col in ["total_units","gwa"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        if "subjects_json" in df.columns:
            df["subjects_json"] = df["subjects_json"].apply(lambda x: x if x and x!='' else '[]')
        if "semester_status" not in df.columns:
            df["semester_status"] = "Regular"
        return df
    else:
        return pd.DataFrame(columns=["student_number","academic_year","semester","subjects_json","total_units","gwa",
                                     "doc_path","doc_upload_time","doc_status","doc_remarks","doc_validated_by","doc_validated_time","semester_status"])

def save_semester_records(df): df.to_csv(SEMESTER_FILE, index=False)

def get_student_semesters(student_number):
    df = load_semester_records()
    return df[df["student_number"] == student_number].copy()

def compute_gwa_from_subjects(subjects_list):
    total_units = total_grade = 0
    for s in subjects_list:
        try:
            units = float(s.get("units",0))
            grade = float(s.get("grade",0))
            total_units += units
            total_grade += units * grade
        except: pass
    return total_grade/total_units if total_units>0 else 0.0

def add_semester_record(student_number, ay, sem, subjects, doc_path="", doc_upload_time="", semester_status="Regular"):
    df = load_semester_records()
    gwa = compute_gwa_from_subjects(subjects)
    total_units = sum(float(s.get("units",0)) for s in subjects)
    new = pd.DataFrame([{
        "student_number": student_number, "academic_year": ay, "semester": sem,
        "subjects_json": json.dumps(subjects), "total_units": total_units, "gwa": gwa,
        "doc_path": str(doc_path), "doc_upload_time": doc_upload_time,
        "doc_status": "Pending" if doc_path else "", "doc_remarks": "", "doc_validated_by": "", "doc_validated_time": "",
        "semester_status": semester_status
    }])
    df = pd.concat([df, new], ignore_index=True)
    save_semester_records(df)
    update_student_academic_summary(student_number)
    return gwa

def update_semester_subjects(student_number, ay, sem, subjects):
    df = load_semester_records()
    mask = (df["student_number"]==student_number) & (df["academic_year"]==ay) & (df["semester"]==sem)
    if mask.any():
        idx = df[mask].index[0]
        gwa = compute_gwa_from_subjects(subjects)
        total_units = sum(float(s.get("units",0)) for s in subjects)
        df.at[idx, "subjects_json"] = json.dumps(subjects)
        df.at[idx, "total_units"] = total_units
        df.at[idx, "gwa"] = gwa
        if df.at[idx, "doc_status"] == "Approved":
            df.at[idx, "doc_status"] = "Pending"
            df.at[idx, "doc_remarks"] = "Subjects edited; re-upload required."
        save_semester_records(df)
        update_student_academic_summary(student_number)
        return True
    return False

def update_semester_document(student_number, ay, sem, doc_path, doc_upload_time, status="Pending"):
    df = load_semester_records()
    mask = (df["student_number"]==student_number) & (df["academic_year"]==ay) & (df["semester"]==sem)
    if mask.any():
        idx = df[mask].index[0]
        df.at[idx, "doc_path"] = str(doc_path)
        df.at[idx, "doc_upload_time"] = doc_upload_time
        df.at[idx, "doc_status"] = status
        df.at[idx, "doc_remarks"] = ""
        df.at[idx, "doc_validated_by"] = ""
        df.at[idx, "doc_validated_time"] = ""
        save_semester_records(df)
        return True
    return False

def validate_semester_document(student_number, ay, sem, status, remarks, validator_name):
    df = load_semester_records()
    mask = (df["student_number"]==student_number) & (df["academic_year"]==ay) & (df["semester"]==sem)
    if mask.any():
        idx = df[mask].index[0]
        df.at[idx, "doc_status"] = status
        df.at[idx, "doc_remarks"] = remarks
        df.at[idx, "doc_validated_by"] = validator_name
        df.at[idx, "doc_validated_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_semester_records(df)
        return True
    return False

def update_semester_status(student_number, ay, sem, new_status):
    df = load_semester_records()
    mask = (df["student_number"]==student_number) & (df["academic_year"]==ay) & (df["semester"]==sem)
    if mask.any():
        idx = df[mask].index[0]
        df.at[idx, "semester_status"] = new_status
        if new_status != "Regular":
            df.at[idx, "subjects_json"] = "[]"
            df.at[idx, "total_units"] = 0
            df.at[idx, "gwa"] = 0.0
            df.at[idx, "doc_status"] = ""
            df.at[idx, "doc_path"] = ""
            df.at[idx, "doc_upload_time"] = ""
            df.at[idx, "doc_remarks"] = ""
            df.at[idx, "doc_validated_by"] = ""
            df.at[idx, "doc_validated_time"] = ""
        save_semester_records(df)
        update_student_academic_summary(student_number)
        return True
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
    df = load_semester_records()
    if ((df["student_number"]==student_number) & (df["academic_year"]==next_ay) & (df["semester"]==next_sem)).any():
        st.warning(f"Semester {next_ay} {next_sem} already exists.")
        return False
    add_semester_record(student_number, next_ay, next_sem, [], semester_status="Regular")
    st.success(f"Created new semester: {next_ay} {next_sem}")
    return True

def update_student_academic_summary(student_number):
    sems = get_student_semesters(student_number)
    total_grade = total_units = 0
    for _, row in sems.iterrows():
        if row["semester_status"] != "Regular": continue
        try:
            subjects = json.loads(row["subjects_json"]) if row["subjects_json"] else []
            for s in subjects:
                units = float(s.get("units",0))
                grade = float(s.get("grade",0))
                total_units += units
                total_grade += units * grade
        except: pass
    if total_units > 0:
        df = load_data()
        idx = df[df["student_number"]==student_number].index
        if len(idx) > 0:
            df.loc[idx, "gwa"] = total_grade / total_units
            df.loc[idx, "total_units_taken"] = total_units
            save_data(df)

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
MILESTONE_DEFS = {
    "MS_Thesis": ["Admission","Registration","Guidance Committee Formation","Plan of Study (POS)","Coursework Completion","General Examination","Thesis Work","External Review","Publishable Article","Final Examination","Final Submission","Graduation Clearance"],
    "MS_NonThesis": ["Admission","Registration","Guidance Committee Formation","Plan of Study (POS)","Coursework Completion","General Examination","External Review","Graduation Clearance"],
    "PhD_Regular": ["Admission","Registration","Advisory Committee Formation","Qualifying Exam","Plan of Study","Coursework","Comprehensive Exam","Dissertation","External Review","Publication","Final Defense","Submission","Graduation"],
    "PhD_Straight": ["Admission","Registration","Advisory Committee Formation","Plan of Study","Coursework","Comprehensive Exam","Dissertation","External Review","Publication (2 papers)","Final Defense","Submission","Graduation"],
    "PhD_Research": ["Admission","Registration","Supervisory Committee Formation","Plan of Research","Seminar Series (4 seminars)","Research Progress Review","Thesis Draft","Publication (min 2 papers)","Final Oral Examination","Thesis Submission","Graduation"]
}

def load_milestone_tracking():
    if os.path.exists(MILESTONE_FILE):
        df = pd.read_csv(MILESTONE_FILE)
        for col in ["student_number","milestone","status","date","file_path","remarks"]:
            if col not in df.columns: df[col] = ""
        return df
    return pd.DataFrame(columns=["student_number","milestone","status","date","file_path","remarks"])

def save_milestone_tracking(df): df.to_csv(MILESTONE_FILE, index=False)

def get_student_milestones(student_number, program_type):
    df = load_milestone_tracking()
    student_df = df[df["student_number"]==student_number]
    milestone_names = MILESTONE_DEFS.get(program_type, MILESTONE_DEFS["MS_Thesis"])
    if len(student_df) == 0:
        new_rows = [{"student_number":student_number, "milestone":m, "status":"Not Started","date":"","file_path":"","remarks":""} for m in milestone_names]
        new_df = pd.DataFrame(new_rows)
        df = pd.concat([df, new_df], ignore_index=True)
        save_milestone_tracking(df)
        return new_df
    else:
        existing = set(student_df["milestone"])
        new_rows = [{"student_number":student_number, "milestone":m, "status":"Not Started","date":"","file_path":"","remarks":""} for m in milestone_names if m not in existing]
        if new_rows:
            df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
            save_milestone_tracking(df)
        return df[df["student_number"]==student_number]

def update_milestone(student_number, milestone, status, date_str, file_path, remarks):
    df = load_milestone_tracking()
    mask = (df["student_number"]==student_number) & (df["milestone"]==milestone)
    if mask.any():
        df.loc[mask, "status"] = status
        if date_str: df.loc[mask, "date"] = date_str
        if file_path: df.loc[mask, "file_path"] = file_path
        if remarks: df.loc[mask, "remarks"] = remarks
    else:
        new = pd.DataFrame([{"student_number":student_number, "milestone":milestone, "status":status, "date":date_str, "file_path":file_path, "remarks":remarks}])
        df = pd.concat([df, new], ignore_index=True)
    save_milestone_tracking(df)

def save_milestone_file(student_number, milestone_name, uploaded_file):
    if uploaded_file is None: return None
    folder = os.path.join(UPLOAD_FOLDER, student_number, "milestones")
    os.makedirs(folder, exist_ok=True)
    ext = uploaded_file.name.split('.')[-1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = milestone_name.replace(" ", "_").replace("/", "_")
    filename = f"{safe_name}_{timestamp}.{ext}"
    filepath = os.path.join(folder, filename)
    with open(filepath, "wb") as f: f.write(uploaded_file.getbuffer())
    return filepath

# ==================== MILESTONE REQUESTS (for approval) ====================
def load_milestone_requests():
    if os.path.exists(MILESTONE_REQUESTS_FILE):
        return pd.read_csv(MILESTONE_REQUESTS_FILE)
    return pd.DataFrame(columns=["request_id","student_number","student_name","milestone_label","target_field","target_value","submitted_date","file_path","original_filename","status","reviewer_comment","reviewed_by","review_date"])

def save_milestone_requests(df): df.to_csv(MILESTONE_REQUESTS_FILE, index=False)

def save_milestone_request_file(student_number, milestone_label, uploaded_file):
    if uploaded_file is None: return None
    folder = os.path.join(UPLOAD_FOLDER, student_number, "milestone_proofs")
    os.makedirs(folder, exist_ok=True)
    ext = uploaded_file.name.split('.')[-1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_label = milestone_label.replace(" ", "_").replace("/", "_")
    filename = f"{safe_label}_{timestamp}.{ext}"
    filepath = os.path.join(folder, filename)
    with open(filepath, "wb") as f: f.write(uploaded_file.getbuffer())
    return filepath

# ==================== WORKFLOW HELPERS ====================
def get_step_completion_status(student_row):
    ptype = get_program_type(student_row["program"])
    completed = set()
    if pd.notna(student_row.get("committee_approval_date")) and str(student_row.get("committee_approval_date")).strip():
        completed.add("Committee")
    if student_row.get("total_units_taken",0) >= student_row.get("total_units_required",24):
        completed.add("Coursework")
    if ptype in ["MS_Thesis","MS_NonThesis"]:
        if student_row.get("general_exam_status") == "Passed": completed.add("Exams")
    else:
        if (student_row.get("qualifying_exam_status")=="Passed" and
            student_row.get("written_comprehensive_status")=="Passed" and
            student_row.get("oral_comprehensive_status")=="Passed"): completed.add("Exams")
    if student_row.get("pos_status") == "Approved": completed.add("POS")
    if ptype != "MS_NonThesis":
        if student_row.get("thesis_outline_approved")=="Yes" and student_row.get("thesis_status") not in ["Not Started",""]:
            completed.add("Thesis")
    else: completed.add("Thesis")
    if student_row.get("final_exam_status") == "Passed": completed.add("Defense")
    if student_row.get("graduation_approved") == "Yes": completed.add("Graduation")
    return completed

def get_next_required_step(student_row):
    completed = get_step_completion_status(student_row)
    for step in WORKFLOW_STEPS:
        if step not in completed: return step
    return "Complete"

def is_step_locked(student_row, step_name):
    step_index = WORKFLOW_STEPS.index(step_name)
    if step_index == 0: return False
    previous_step = WORKFLOW_STEPS[step_index-1]
    return previous_step not in get_step_completion_status(student_row)

# ==================== UI COMPONENTS ====================
def get_status_badge(status):
    if status == "Approved": return '<span class="status-approved">✅ Approved</span>'
    elif status == "Rejected": return '<span class="status-rejected">❌ Rejected</span>'
    elif status == "Pending": return '<span class="status-pending">🟡 Pending</span>'
    else: return '<span class="status-pending">📄 Not submitted</span>'

def filter_dataframe(search_term, data):
    if not search_term: return data
    mask = data["name"].str.contains(search_term, case=False, na=False) | data["student_number"].str.contains(search_term, case=False, na=False)
    return data[mask]

def display_workflow_grid(completed_steps, next_step):
    cols = st.columns(4)
    for i, step in enumerate(WORKFLOW_STEPS):
        with cols[i%4]:
            if step in completed_steps:
                st.markdown(f'<div style="background:#e8f5e9; border-radius:12px; padding:0.5rem; text-align:center;"><div>✅</div><div>{step}</div><div style="font-size:0.7rem;">Completed</div></div>', unsafe_allow_html=True)
            elif step == next_step:
                st.markdown(f'<div style="background:#fff3e0; border:2px solid #ff9800; border-radius:12px; padding:0.5rem; text-align:center;"><div>⏳</div><div>{step}</div><div style="font-size:0.7rem;">Next</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="background:#f5f5f5; border-radius:12px; padding:0.5rem; text-align:center; opacity:0.6;"><div>🔒</div><div>{step}</div><div style="font-size:0.7rem;">Locked</div></div>', unsafe_allow_html=True)

# ==================== RENDER SEMESTER BLOCK (STUDENT / STAFF VIEW) ====================
def render_semester_block_general(student_number, semester_row, is_staff=False, override_edit=False):
    """Display semester block. If is_staff and override_edit, staff can edit subjects."""
    ay = str(semester_row["academic_year"])
    sem = str(semester_row["semester"])
    semester_status = str(semester_row.get("semester_status","Regular")).strip()
    if semester_status not in SEMESTER_STATUS_OPTIONS: semester_status = "Regular"
    try:
        subjects = json.loads(semester_row["subjects_json"]) if semester_row["subjects_json"] else []
    except: subjects = []
    total_units = float(semester_row["total_units"]) if pd.notna(semester_row["total_units"]) else 0.0
    gwa = float(semester_row["gwa"]) if pd.notna(semester_row["gwa"]) else 0.0
    doc_status = str(semester_row.get("doc_status","")).strip()
    doc_path = str(semester_row.get("doc_path","")).strip()
    doc_remarks = str(semester_row.get("doc_remarks","")).strip()

    with st.expander(f"📅 {ay} | {sem} (Units: {total_units:.0f} | GWA: {gwa:.2f})", expanded=False):
        # Semester status dropdown (only editable if staff with override or student)
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
        if doc_status == "Rejected" and doc_remarks: st.warning(f"Rejection reason: {doc_remarks}")

        # Show edit table only if (student) OR (staff with override)
        if semester_status == "Regular" and (not is_staff or (is_staff and override_edit)):
            if not doc_path or doc_path == "nan": st.warning("⚠️ Required: Upload AMIS screenshot or grade report below.")
            # Editable subjects table
            df_edit = pd.DataFrame(subjects) if subjects else pd.DataFrame(columns=["course_code","course_description","units","grade"])
            for col in ["course_code","course_description","units","grade"]:
                if col not in df_edit.columns:
                    df_edit[col] = 0 if col=="units" else ""
            df_edit = df_edit[["course_code","course_description","units","grade"]]
            df_edit["units"] = pd.to_numeric(df_edit["units"], errors='coerce').fillna(0).astype(int)

            df_key = f"df_{student_number}_{ay}_{sem}"
            if df_key not in st.session_state:
                st.session_state[df_key] = df_edit.copy()
            edited_df = st.data_editor(st.session_state[df_key], use_container_width=True, hide_index=True,
                column_config={"course_code":"Code","course_description":"Description",
                               "units":st.column_config.NumberColumn("Units", step=1, min_value=0),
                               "grade":st.column_config.SelectboxColumn("Grade", options=GRADE_OPTIONS, default="1.00")},
                key=f"editor_{student_number}_{ay}_{sem}")
            st.session_state[df_key] = edited_df

            col_add, col_save = st.columns([1,4])
            with col_add:
                if st.button("➕ Add Row", key=f"add_{student_number}_{ay}_{sem}"):
                    new_row = pd.DataFrame([{"course_code":"","course_description":"","units":0,"grade":"1.00"}])
                    st.session_state[df_key] = pd.concat([st.session_state[df_key], new_row], ignore_index=True)
                    st.rerun()
            with col_save:
                if st.button("💾 Save Subjects", key=f"save_{student_number}_{ay}_{sem}"):
                    new_subjects = st.session_state[df_key].to_dict("records")
                    for s in new_subjects:
                        s["units"] = int(s["units"]) if s["units"] else 0
                        s["course_code"] = str(s.get("course_code",""))
                        s["course_description"] = str(s.get("course_description",""))
                        s["grade"] = str(s.get("grade","1.00"))
                    if update_semester_subjects(student_number, ay, sem, new_subjects):
                        st.success("Subjects saved! Waiting for validation.")
                        if df_key in st.session_state: del st.session_state[df_key]
                        st.rerun()
                    else: st.error("Save failed.")
        elif semester_status != "Regular":
            st.info(f"Semester marked as **{semester_status}**. Subject input disabled.")
            if subjects: st.dataframe(pd.DataFrame(subjects), use_container_width=True, hide_index=True)
        else:
            st.info("Editing is disabled in this view. Only the student can edit subjects.")

        # Document upload (only for student)
        st.markdown("---")
        st.markdown("**Upload Proof of Grades (AMIS Screenshot)**")
        if semester_status == "Regular":
            if doc_path and doc_path not in ["","nan"] and os.path.exists(doc_path):
                st.info(f"Current file: {os.path.basename(doc_path)}")
            # Upload only if not staff or staff in override view? We'll allow staff to upload on behalf? Keep simple: only student can upload.
            if not is_staff:
                with st.form(key=f"upload_{student_number}_{ay}_{sem}"):
                    uploaded = st.file_uploader("Choose file (PDF/JPG/PNG)", type=["pdf","jpg","jpeg","png"], key=f"upload_file_{ay}_{sem}")
                    if st.form_submit_button("📎 Upload Document") and uploaded:
                        folder = os.path.join(UPLOAD_FOLDER, student_number, "semester_docs")
                        os.makedirs(folder, exist_ok=True)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{ay}_{sem}_{timestamp}.{uploaded.name.split('.')[-1].lower()}"
                        filepath = os.path.join(folder, filename)
                        with open(filepath,"wb") as f: f.write(uploaded.getbuffer())
                        if update_semester_document(student_number, ay, sem, filepath, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Pending"):
                            st.success("Document uploaded! Pending validation.")
                            st.rerun()
            else:
                # Staff can see document but cannot upload (or they could, but we omit for simplicity)
                if doc_path and doc_path != "nan" and os.path.exists(doc_path):
                    st.caption("Document uploaded by student.")
        else: st.info(f"Semester status **{semester_status}** – no upload required.")

        # Validation buttons for staff (if document pending)
        if is_staff and doc_status == "Pending":
            st.markdown("---")
            st.markdown("**Staff Validation**")
            remarks_val = st.text_area("Remarks", key=f"val_remarks_{student_number}_{ay}_{sem}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve Document", key=f"approve_doc_{student_number}_{ay}_{sem}"):
                    validate_semester_document(student_number, ay, sem, "Approved", remarks_val, st.session_state.display_name)
                    st.success("Approved.")
                    st.rerun()
            with col2:
                if st.button("❌ Reject Document", key=f"reject_doc_{student_number}_{ay}_{sem}"):
                    validate_semester_document(student_number, ay, sem, "Rejected", remarks_val, st.session_state.display_name)
                    st.warning("Rejected.")
                    st.rerun()

# ==================== PROFILE APPROVAL PANEL INSIDE STUDENT PROFILE ====================
def render_profile_approval_section(student, is_staff=False):
    """Show pending profile updates and approval buttons (only for staff)."""
    if student.get("profile_pending_status") == "Pending" and is_staff:
        st.markdown("#### Pending Profile Update")
        st.write(f"**New Address:** {student['profile_pending_address']}")
        st.write(f"**New Phone:** {student['profile_pending_phone']}")
        st.write(f"**New Emergency Contact:** {student['profile_pending_emergency']}")
        remarks = st.text_area("Remarks", key="prof_remarks")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve Profile Update"):
                df = load_data()
                df.loc[df["student_number"]==student["student_number"], "address"] = student["profile_pending_address"]
                df.loc[df["student_number"]==student["student_number"], "phone"] = student["profile_pending_phone"]
                df.loc[df["student_number"]==student["student_number"], "emergency_contact"] = student["profile_pending_emergency"]
                df.loc[df["student_number"]==student["student_number"], "profile_pending_status"] = "Approved"
                df.loc[df["student_number"]==student["student_number"], "profile_pending_remarks"] = remarks
                save_data(df)
                st.success("Profile approved.")
                st.rerun()
        with col2:
            if st.button("❌ Reject Profile Update"):
                df = load_data()
                df.loc[df["student_number"]==student["student_number"], "profile_pending_status"] = "Rejected"
                df.loc[df["student_number"]==student["student_number"], "profile_pending_remarks"] = remarks
                save_data(df)
                st.warning("Profile rejected.")
                st.rerun()
    elif student.get("profile_pending_status") == "Rejected":
        st.error(f"Profile update rejected: {student.get('profile_pending_remarks','')}")

# ==================== STAFF UPDATE STUDENT PROFILE (FULL DASHBOARD) ====================
def staff_view_student_profile(student_number):
    """Display full student dashboard for staff, with validation buttons inside tabs and limited editing."""
    df = load_data()
    student = df[df["student_number"] == student_number].iloc[0].copy()
    program_type = get_program_type(student["program"])

    # Determine if staff can edit academic records (override mode)
    can_edit = False
    if student["advisor"] == "Not assigned":
        can_edit = True
        st.info("ℹ️ No adviser assigned. You can edit this student's records directly.")
    else:
        st.warning(f"⚠️ Adviser assigned: {student['advisor']}. Editing is restricted.")
        override = st.checkbox("🔓 Override restrictions (admin override)")
        if override:
            can_edit = True
            st.info("Override active – you can now edit this student's records.")

    st.markdown(f"## {student['name']} ({student_number})")
    if st.button("← Back to Student List"):
        st.session_state.staff_selected_student = None
        st.session_state.staff_show_update = False
        st.rerun()

    tabs = st.tabs(["📝 Student Info", "📚 Coursework", "📌 Milestones", "📁 Uploads", "⚙️ Admin Controls"])
    with tabs[0]:
        col1, col2 = st.columns([1,2])
        with col1:
            pic_path = get_profile_picture_path(student_number)
            if pic_path: st.image(pic_path, width=150)
            else: st.info("No profile picture")
            # Staff can upload/delete picture
            uploaded_pic = st.file_uploader("Update picture", type=["jpg","jpeg","png"], key="staff_pic")
            if uploaded_pic:
                fn = save_profile_picture(student_number, uploaded_pic)
                if fn:
                    df.loc[df["student_number"]==student_number, "profile_pic"] = fn
                    save_data(df)
                    st.success("Picture updated.")
                    st.rerun()
            if st.button("Delete picture"):
                if delete_profile_picture(student_number):
                    df.loc[df["student_number"]==student_number, "profile_pic"] = ""
                    save_data(df)
                    st.rerun()
        with col2:
            st.markdown(f"**Student Number:** {student_number}")
            st.markdown(f"**Name:** {student['name']}")
            st.markdown(f"**Program:** {student['program']}")
            st.markdown(f"**Adviser:** {student['advisor']}")
            st.markdown(f"**Admitted:** {format_ay(student['ay_start'], student['semester'])}")
            st.markdown(f"**Required Units:** {student['total_units_required']}")
            st.markdown(f"**Special Status:** {student.get('special_status','Regular')}")
            # Show contact details
            if student.get("profile_pending_status") == "Pending":
                st.info("Profile update pending approval")
                st.write(f"Current approved address: {student['address']}")
                st.write(f"Pending address: {student['profile_pending_address']}")
            else:
                st.markdown(f"**Address:** {student['address'] or '—'}")
                st.markdown(f"**Phone:** {student['phone'] or '—'}")
                st.markdown(f"**Emergency Contact:** {student['emergency_contact'] or '—'}")
        # Profile approval section
        render_profile_approval_section(student, is_staff=True)

    with tabs[1]:  # Coursework
        st.subheader("Academic Record")
        # Generate semesters automatically (same as student dashboard)
        total_years = 2 if is_master_program(student["program"]) else 3
        total_semesters_needed = total_years * 2 + (total_years - 1)
        start_ay = student.get("ay_start", current_year)
        if pd.isna(start_ay) or start_ay == 0: start_ay = current_year
        start_ay_str = f"{start_ay}-{start_ay+1}"
        start_sem = student.get("semester", "1st Sem")
        sem_order = ["1st Sem","2nd Sem","Summer"]
        all_semesters = []
        for yr in range(total_years):
            ay = f"{start_ay+yr}-{start_ay+yr+1}"
            for sem in sem_order:
                all_semesters.append((ay,sem))
        start_idx = 0
        for i, (ay,sem) in enumerate(all_semesters):
            if ay == start_ay_str and sem == start_sem:
                start_idx = i
                break
        prospectus = all_semesters[start_idx:start_idx+total_semesters_needed]
        existing = get_student_semesters(student_number)
        for ay,sem in prospectus:
            if not ((existing["academic_year"]==ay) & (existing["semester"]==sem)).any():
                add_semester_record(student_number, ay, sem, [], semester_status="Regular")
        semesters = get_student_semesters(student_number)
        semesters["order"] = semesters["semester"].map({"1st Sem":0,"2nd Sem":1,"Summer":2})
        semesters["ay_num"] = semesters["academic_year"].apply(lambda x: int(x.split("-")[0]))
        semesters = semesters.sort_values(["ay_num","order"]).reset_index(drop=True)
        for _, row in semesters.iterrows():
            render_semester_block_general(student_number, row, is_staff=True, override_edit=can_edit)
        if can_edit and st.button("➕ Add Next Semester (Staff)"):
            last_sem = semesters.iloc[-1] if not semesters.empty else None
            if last_sem:
                create_next_semester(student_number, last_sem["academic_year"], last_sem["semester"])
                st.rerun()
        st.markdown("---")
        cola, colb, colc, cold = st.columns(4)
        cola.metric("Units Taken", student["total_units_taken"])
        colb.metric("Required Units", student["total_units_required"])
        colc.metric("Remaining", max(0, student["total_units_required"] - student["total_units_taken"]))
        cold.metric("Cumulative GWA", f"{student['gwa']:.2f}")

    with tabs[2]:  # Milestones
        st.subheader("Milestone Tracker")
        milestones_df = get_student_milestones(student_number, program_type)
        for _, m in milestones_df.iterrows():
            with st.expander(f"{m['milestone']} – Status: {m['status']}"):
                st.write(f"Date: {m['date'] if m['date'] else 'Not set'}")
                if m['file_path'] and m['file_path'] != 'nan' and os.path.exists(m['file_path']):
                    with open(m['file_path'], "rb") as f:
                        st.download_button("Download proof", f, file_name=os.path.basename(m['file_path']))
                if can_edit and m['status'] != "Completed":
                    # Staff can manually mark as completed (override)
                    if st.button(f"Mark {m['milestone']} as Completed", key=f"staff_complete_{m['milestone']}"):
                        update_milestone(student_number, m['milestone'], "Completed", datetime.now().strftime("%Y-%m-%d"), "", "Marked by staff")
                        st.success("Milestone completed.")
                        st.rerun()
                # Validation of pending milestone requests? We'll keep simple.

    with tabs[3]:  # Uploads (general documents)
        st.subheader("Student Uploads")
        # Show uploads associated with this student
        uploads_df = load_uploads()
        student_uploads = uploads_df[uploads_df["student_number"] == student_number]
        if student_uploads.empty:
            st.info("No documents uploaded.")
        else:
            for _, up in student_uploads.iterrows():
                st.write(f"**{UPLOAD_DISPLAY_NAMES.get(up['category'], up['category'])}** – Status: {up['status']}")
                if up["status"] == "Pending" and can_edit:
                    # Staff can approve/reject uploads
                    remarks_up = st.text_area("Remarks", key=f"upload_remarks_{up['category']}_{student_number}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ Approve", key=f"approve_upload_{student_number}_{up['category']}"):
                            # Update upload status
                            df_up = load_uploads()
                            df_up.loc[df_up.index[up.name], "status"] = "Approved"
                            df_up.loc[df_up.index[up.name], "reviewer_comment"] = remarks_up
                            df_up.loc[df_up.index[up.name], "reviewed_by"] = st.session_state.display_name
                            df_up.loc[df_up.index[up.name], "review_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            save_uploads(df_up)
                            st.success("Approved.")
                            st.rerun()
                    with col2:
                        if st.button(f"❌ Reject", key=f"reject_upload_{student_number}_{up['category']}"):
                            df_up = load_uploads()
                            df_up.loc[df_up.index[up.name], "status"] = "Rejected"
                            df_up.loc[df_up.index[up.name], "reviewer_comment"] = remarks_up
                            df_up.loc[df_up.index[up.name], "reviewed_by"] = st.session_state.display_name
                            df_up.loc[df_up.index[up.name], "review_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            save_uploads(df_up)
                            st.warning("Rejected.")
                            st.rerun()

    with tabs[4]:  # Admin Controls
        st.subheader("Administrative Controls")
        st.markdown("**Change Adviser**")
        adviser_options = ["Not assigned", "Dr. Eslava", "Dr. Sanchez"]
        new_advisor = st.selectbox("Select adviser", adviser_options, index=adviser_options.index(student["advisor"]) if student["advisor"] in adviser_options else 0)
        if st.button("Update Adviser"):
            df.loc[df["student_number"] == student_number, "advisor"] = new_advisor
            save_data(df)
            st.success(f"Adviser updated to {new_advisor}")
            st.rerun()

        st.markdown("**Change Program**")
        new_program = st.selectbox("New Program", PROGRAMS, index=PROGRAMS.index(student["program"]) if student["program"] in PROGRAMS else 0)
        if st.button("Update Program"):
            # Recalculate required units
            prior = student.get("prior_ms_graduate", False)
            new_req = get_required_units(new_program, prior)
            df.loc[df["student_number"] == student_number, "program"] = new_program
            if new_req is not None:
                df.loc[df["student_number"] == student_number, "total_units_required"] = new_req
            save_data(df)
            st.success("Program updated.")
            st.rerun()

        st.markdown("**Special Student Status**")
        status_options = ["Regular", "Transferred", "Shifted", "On Leave", "Inactive", "Deceased"]
        current_special = student.get("special_status", "Regular")
        new_special = st.selectbox("Status", status_options, index=status_options.index(current_special) if current_special in status_options else 0)
        if st.button("Update Special Status"):
            df.loc[df["student_number"] == student_number, "special_status"] = new_special
            save_data(df)
            st.success("Special status updated.")
            st.rerun()

        st.markdown("**Override Coursework Editing**")
        st.info("If you need to manually edit subjects or grades, use the 'Override' checkbox at the top of this page.")

# ==================== REGISTRATION FORM ====================
def register_new_student_form():
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
        advisor = st.selectbox("Adviser (optional)", ["Not assigned", "Dr. Eslava", "Dr. Sanchez"])
        prior_ms = False
        if program == "PhD Environmental Science":
            prior_ms = st.checkbox("Student is an MS Environmental Science graduate")
        submitted = st.form_submit_button("Register Student")
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
                st.error(f"Missing: {', '.join(errors)}")
            else:
                full_name = f"{last_name}, {first_name} {middle_name}".strip()
                new_row = create_demo_data().iloc[0].to_dict()
                req_units = get_required_units(program, prior_ms)
                new_row.update({
                    "student_number": student_number,
                    "name": full_name,
                    "last_name": last_name,
                    "first_name": first_name,
                    "middle_name": middle_name,
                    "program": program,
                    "advisor": advisor,
                    "ay_start": ay_start,
                    "semester": semester,
                    "student_status": student_status,
                    "prior_ms_graduate": prior_ms,
                    "total_units_required": req_units if req_units else 24,
                    "thesis_units_limit": get_thesis_limit_from_program(program),
                    "residency_max_years": get_residency_max_from_program(program),
                    "address": "", "phone": "", "emergency_contact": "",
                    "profile_pending_address": "", "profile_pending_phone": "", "profile_pending_emergency": "",
                    "profile_pending_status": "", "profile_pending_remarks": "",
                    "special_status": "Regular"
                })
                new_df = pd.DataFrame([new_row])
                df = pd.concat([df, new_df], ignore_index=True)
                save_data(df)
                get_student_milestones(student_number, get_program_type(program))
                st.success(f"Student {full_name} registered successfully.")
                st.rerun()

# ==================== UPLOAD HELPERS ====================
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

def save_uploads(df): df.to_csv(UPLOAD_FILE, index=False)

def save_uploaded_file(student_number, category, uploaded_file):
    if uploaded_file is None: return None
    student_folder = os.path.join(UPLOAD_FOLDER, student_number)
    os.makedirs(student_folder, exist_ok=True)
    ext = uploaded_file.name.split('.')[-1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{category}_{timestamp}.{ext}"
    filepath = os.path.join(student_folder, filename)
    with open(filepath, "wb") as f: f.write(uploaded_file.getbuffer())
    # Also add entry to uploads.csv
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

# ==================== LOGIN & CONSENT ====================
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
            else: st.error("Invalid credentials")
        st.caption("Demo: staff1/admin123 | adviser1/adv123 | student numbers S001-S013 with password = student number")
    st.stop()

if st.session_state.logged_in and not st.session_state.consent_given:
    show_consent_form()
    st.stop()

# ==================== LOAD DATA ====================
df = load_data()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown(f"<div style='text-align:center'><h3>👤 {st.session_state.display_name}</h3><div>{st.session_state.role}</div><div>✅ Consent given</div></div>", unsafe_allow_html=True)
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.consent_given = False
        st.rerun()
    st.markdown("---")
    st.caption("Version 15.0 | Clean Admin Dashboard | Tab Validation")

# ==================== MAIN ====================
st.title("🎓 SESAM Graduate Student Lifecycle Management")
st.caption("Role‑based workflow: Student updates → Adviser/Staff approves")

role = st.session_state.role

# ==================== STAFF VIEW ====================
if role == "SESAM Staff":
    # Show only two buttons at the top
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Register New Student", use_container_width=True):
            st.session_state.staff_show_update = False
            st.session_state.staff_selected_student = None
            st.session_state.show_registration = True
        else:
            if "show_registration" not in st.session_state:
                st.session_state.show_registration = False
    with col2:
        if st.button("✏️ Update Student Information", use_container_width=True):
            st.session_state.show_registration = False
            st.session_state.staff_show_update = True
            st.session_state.staff_selected_student = None

    if st.session_state.get("show_registration", False):
        register_new_student_form()
    elif st.session_state.get("staff_show_update", False):
        if st.session_state.staff_selected_student is None:
            st.subheader("Select a student to update")
            search = st.text_input("Search by name or student number")
            filtered = filter_dataframe(search, df)
            # Display as a simple table with select button
            for _, row in filtered.iterrows():
                col1, col2, col3 = st.columns([3,2,1])
                with col1:
                    st.write(f"{row['name']} ({row['student_number']})")
                with col2:
                    st.write(f"Program: {row['program']}")
                with col3:
                    if st.button("Select", key=f"select_{row['student_number']}"):
                        st.session_state.staff_selected_student = row["student_number"]
                        st.rerun()
            if st.button("← Back"):
                st.session_state.staff_show_update = False
                st.rerun()
        else:
            staff_view_student_profile(st.session_state.staff_selected_student)
    else:
        # If no button pressed, show welcome message
        st.info("Use the buttons above to register a new student or update existing student information.")

# ==================== ADVISER VIEW ====================
elif role == "Faculty Adviser":
    st.subheader(f"👨‍🏫 Your Advisees – {st.session_state.display_name}")
    advisees = df[df["advisor"] == st.session_state.display_name].copy()
    if advisees.empty:
        st.warning("No students assigned to you.")
    else:
        # Show advisee list with details
        for _, student in advisees.iterrows():
            with st.expander(f"{student['name']} ({student['student_number']}) – {student['program']}"):
                st.write(f"GWA: {student['gwa']:.2f}, Units: {student['total_units_taken']}/{student['total_units_required']}")
                # Show pending profile update if any
                if student.get("profile_pending_status") == "Pending":
                    st.warning("Profile update pending approval")
                # Quick validation button? But we'll redirect to full profile view
                if st.button(f"View & Validate", key=f"view_{student['student_number']}"):
                    st.session_state.staff_selected_student = student["student_number"]
                    st.session_state.staff_show_update = True
                    st.rerun()
        # Show pending validations in a unified way? The user wants inside profile.
        if st.session_state.get("staff_show_update", False) and st.session_state.staff_selected_student:
            staff_view_student_profile(st.session_state.staff_selected_student)

# ==================== STUDENT VIEW ====================
elif role == "Student":
    student = df[df["name"] == st.session_state.display_name].iloc[0].copy()
    program_type = get_program_type(student["program"])
    # Student dashboard (same as before, simplified for brevity – reuse existing code)
    # We'll keep the existing student dashboard structure (already implemented in previous versions).
    # For space, we'll assume the existing student dashboard code is copied here.
    # But to avoid duplication, we rely on that the student view remains unchanged from the previous working version.
    # Since this is a complete replacement, we include a minimal student dashboard that works.
    st.subheader(f"📘 Your Dashboard – {student['name']}")
    # Show pending profile status
    if student.get("profile_pending_status") == "Pending":
        st.warning("Your profile update is pending approval.")
    elif student.get("profile_pending_status") == "Rejected":
        st.error(f"Profile update rejected: {student.get('profile_pending_remarks','')}")

    # Milestone next action (as before)
    milestones = get_student_milestones(student["student_number"], program_type)
    next_milestone = None
    for _, row in milestones.iterrows():
        if row["status"] != "Completed":
            next_milestone = row["milestone"]
            break
    if next_milestone:
        st.info(f"🎯 Next milestone: {next_milestone}")
    else:
        st.success("All milestones completed!")

    tabs = st.tabs(["👤 My Profile", "📚 Coursework", "📌 Milestones", "📁 Uploads"])
    with tabs[0]:
        col1, col2 = st.columns([1,2])
        with col1:
            pic_path = get_profile_picture_path(student["student_number"])
            if pic_path: st.image(pic_path, width=150)
            else: st.info("No profile picture")
            uploaded_pic = st.file_uploader("Upload picture", type=["jpg","jpeg","png"], key="student_pic")
            if uploaded_pic:
                fn = save_profile_picture(student["student_number"], uploaded_pic)
                if fn:
                    df.loc[df["student_number"]==student["student_number"], "profile_pic"] = fn
                    save_data(df)
                    st.success("Picture updated.")
                    st.rerun()
        with col2:
            st.markdown(f"**Student Number:** {student['student_number']}")
            st.markdown(f"**Name:** {student['name']}")
            st.markdown(f"**Program:** {student['program']}")
            st.markdown(f"**Adviser:** {student['advisor']}")
            st.markdown(f"**Admitted:** {format_ay(student['ay_start'], student['semester'])}")
            st.markdown(f"**Required Units:** {student['total_units_required']}")
            if student.get("profile_pending_status") == "Pending":
                st.info("Your contact details are pending approval.")
                # Show pending values
                st.write(f"Proposed Address: {student['profile_pending_address']}")
                st.write(f"Proposed Phone: {student['profile_pending_phone']}")
                st.write(f"Proposed Emergency Contact: {student['profile_pending_emergency']}")
            else:
                st.markdown(f"**Address:** {student['address'] or '—'}")
                st.markdown(f"**Phone:** {student['phone'] or '—'}")
                st.markdown(f"**Emergency Contact:** {student['emergency_contact'] or '—'}")
        st.markdown("---")
        with st.form("student_edit_profile"):
            current_address = student.get("profile_pending_address") if student.get("profile_pending_status") == "Pending" else student.get("address","")
            current_phone = student.get("profile_pending_phone") if student.get("profile_pending_status") == "Pending" else student.get("phone","")
            current_emergency = student.get("profile_pending_emergency") if student.get("profile_pending_status") == "Pending" else student.get("emergency_contact","")
            new_address = st.text_input("Address", value=current_address)
            new_phone = st.text_input("Phone", value=current_phone)
            new_emergency = st.text_input("Emergency Contact", value=current_emergency)
            if st.form_submit_button("Submit for Approval"):
                df.loc[df["student_number"]==student["student_number"], "profile_pending_address"] = new_address
                df.loc[df["student_number"]==student["student_number"], "profile_pending_phone"] = new_phone
                df.loc[df["student_number"]==student["student_number"], "profile_pending_emergency"] = new_emergency
                df.loc[df["student_number"]==student["student_number"], "profile_pending_status"] = "Pending"
                save_data(df)
                st.success("Changes submitted. Waiting for approval.")
                st.rerun()

    with tabs[1]:
        st.subheader("Your Academic Record")
        # Generate semesters automatically (same as staff view)
        total_years = 2 if is_master_program(student["program"]) else 3
        total_semesters_needed = total_years * 2 + (total_years - 1)
        start_ay = student.get("ay_start", current_year)
        if pd.isna(start_ay) or start_ay == 0: start_ay = current_year
        start_ay_str = f"{start_ay}-{start_ay+1}"
        start_sem = student.get("semester", "1st Sem")
        sem_order = ["1st Sem","2nd Sem","Summer"]
        all_semesters = []
        for yr in range(total_years):
            ay = f"{start_ay+yr}-{start_ay+yr+1}"
            for sem in sem_order:
                all_semesters.append((ay,sem))
        start_idx = 0
        for i, (ay,sem) in enumerate(all_semesters):
            if ay == start_ay_str and sem == start_sem:
                start_idx = i
                break
        prospectus = all_semesters[start_idx:start_idx+total_semesters_needed]
        existing = get_student_semesters(student["student_number"])
        for ay,sem in prospectus:
            if not ((existing["academic_year"]==ay) & (existing["semester"]==sem)).any():
                add_semester_record(student["student_number"], ay, sem, [], semester_status="Regular")
        semesters = get_student_semesters(student["student_number"])
        semesters["order"] = semesters["semester"].map({"1st Sem":0,"2nd Sem":1,"Summer":2})
        semesters["ay_num"] = semesters["academic_year"].apply(lambda x: int(x.split("-")[0]))
        semesters = semesters.sort_values(["ay_num","order"]).reset_index(drop=True)
        for _, row in semesters.iterrows():
            render_semester_block_general(student["student_number"], row, is_staff=False, override_edit=False)
        if st.button("➕ Add Next Semester"):
            last_sem = semesters.iloc[-1] if not semesters.empty else None
            if last_sem:
                create_next_semester(student["student_number"], last_sem["academic_year"], last_sem["semester"])
                st.rerun()
        st.markdown("---")
        cola, colb, colc, cold = st.columns(4)
        cola.metric("Units Taken", student["total_units_taken"])
        colb.metric("Required Units", student["total_units_required"])
        colc.metric("Remaining", max(0, student["total_units_required"] - student["total_units_taken"]))
        cold.metric("Cumulative GWA", f"{student['gwa']:.2f}")

    with tabs[2]:
        st.subheader("Milestone Tracker")
        milestones_df = get_student_milestones(student["student_number"], program_type)
        for _, m in milestones_df.iterrows():
            with st.expander(f"{m['milestone']} – Status: {m['status']}"):
                st.write(f"Date: {m['date'] if m['date'] else 'Not set'}")
                if m['file_path'] and m['file_path'] != 'nan' and os.path.exists(m['file_path']):
                    with open(m['file_path'], "rb") as f:
                        st.download_button("Download proof", f, file_name=os.path.basename(m['file_path']))
                if m['status'] != "Completed":
                    uploaded = st.file_uploader("Upload proof", type=["pdf","jpg","png"], key=f"milestone_{m['milestone']}")
                    if st.button(f"Submit {m['milestone']}", key=f"submit_{m['milestone']}"):
                        if uploaded:
                            filepath = save_milestone_file(student["student_number"], m['milestone'], uploaded)
                            update_milestone(student["student_number"], m['milestone'], "Pending", datetime.now().strftime("%Y-%m-%d"), filepath, "")
                            st.success("Submitted for approval.")
                            st.rerun()
                        else:
                            st.error("Please upload a file.")

    with tabs[3]:
        st.subheader("Upload Supporting Documents")
        category = st.selectbox("Document Type", UPLOAD_CATEGORIES, format_func=lambda x: UPLOAD_DISPLAY_NAMES.get(x,x))
        file = st.file_uploader("Choose file", type=["pdf","jpg","jpeg","png"])
        if st.button("Upload") and file:
            path = save_uploaded_file(student["student_number"], category, file)
            if path:
                st.success("Uploaded. Waiting for validation.")
                st.rerun()

    st.caption("For corrections, contact your adviser or SESAM Staff.")
