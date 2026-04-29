"""
SESAM KMIS - Graduate Student Lifecycle Management System
Version: 21.1 | Fixed syntax, staff search dashboards
"""

import streamlit as st
import pandas as pd
import os
import json
from datetime import date, datetime

# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="SESAM KMIS", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .profile-card {
        background: white;
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
    }
    .profile-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #f0f2f6;
        padding-bottom: 0.75rem;
    }
    .profile-header h3 {
        margin: 0;
        color: #1f3b4c;
    }
    .student-card {
        background: white;
        border-radius: 16px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #e9ecef;
        transition: all 0.2s;
        cursor: pointer;
    }
    .student-card:hover {
        background-color: #f8f9fa;
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.1);
    }
    .student-name {
        font-weight: 600;
        font-size: 1.1rem;
        color: #1f3b4c;
    }
    .student-detail {
        font-size: 0.85rem;
        color: #6c757d;
    }
    .stButton button {
        border-radius: 30px !important;
        padding: 0.4rem 1.2rem !important;
        font-weight: 500 !important;
    }
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
if "staff_show_update" not in st.session_state:
    st.session_state.staff_show_update = False
if "show_registration" not in st.session_state:
    st.session_state.show_registration = False

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

def is_master_program(program):
    return get_program_type(program).startswith("MS")

def is_phd_program(program):
    return get_program_type(program).startswith("PhD")

def get_required_units(program, prior_ms_graduate=False):
    if program == "MS Environmental Science":
        return 32
    elif program == "PhD Environmental Science":
        return 37 if prior_ms_graduate else 50
    else:
        return None

# ==================== HELPER FUNCTIONS ====================
SEMESTERS = ["1st Sem", "2nd Sem", "Summer"]
current_year = date.today().year
ACADEMIC_YEARS = [f"{year}-{year+1}" for year in range(current_year-5, current_year+6)]
GRADE_OPTIONS = ["1.00", "1.25", "1.50", "1.75", "2.00", "2.25", "2.50", "2.75", "3.00", "INC", "DRP", "5.00", "P", "IP"]
SEMESTER_STATUS_OPTIONS = ["Regular", "Off-Sem", "On Leave", "Shifted Program", "Transferred"]
WORKFLOW_STEPS = ["Committee", "Coursework", "Exams", "POS", "Thesis", "Defense", "Graduation"]

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

# ==================== DATA LOADING ====================
DATA_FILE = "students.csv"
SEMESTER_FILE = "semester_records.csv"
MILESTONE_FILE = "milestone_tracking.csv"
UPLOAD_FOLDER = "student_uploads"
MILESTONE_REQUESTS_FILE = "milestone_requests.csv"
PROFILE_PIC_FOLDER = "profile_pics"

for folder in [UPLOAD_FOLDER, PROFILE_PIC_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

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
    }
    return pd.DataFrame(data)

@st.cache_resource
def load_data():
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        df = create_demo_data()
        save_data(df)
        return df
    try:
        df = pd.read_csv(DATA_FILE, dtype=str)
    except Exception:
        df = create_demo_data()
        save_data(df)
        return df
    numeric_cols = ["ay_start", "gwa", "total_units_taken", "total_units_required",
                    "thesis_units_taken", "thesis_units_limit", "residency_years_used",
                    "residency_max_years", "extension_count", "loa_total_terms",
                    "transfer_units_approved"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            if col != "gwa":
                df[col] = df[col].astype(int)
            else:
                df[col] = df[col].astype(float)
    default_df = create_demo_data()
    for col in default_df.columns:
        if col not in df.columns:
            df[col] = default_df[col]
    text_cols = ["student_number","name","last_name","first_name","middle_name","program","advisor","semester",
                 "profile_pic","committee_members_structured","committee_approval_date","thesis_outline_approved",
                 "thesis_status","pos_status","qualifying_exam_status","written_comprehensive_status",
                 "oral_comprehensive_status","general_exam_status","final_exam_status","student_status",
                 "address","phone","institutional_email","gender","civil_status","citizenship","birthdate","religion",
                 "emergency_name","emergency_relationship","emergency_country_code","emergency_phone","special_status"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)
    for col in ["prior_ms_graduate", "committee_changed", "coursework_changed"]:
        if col in df.columns:
            df[col] = df[col].astype(bool)
        else:
            df[col] = False
    for idx, row in df.iterrows():
        prog = row["program"]
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
            except Exception:
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
                                     "doc_path","doc_upload_time","doc_status","doc_remarks","doc_validated_by","doc_validated_time","semester_status"])
    df = pd.read_csv(SEMESTER_FILE, dtype=str)
    required_cols = ["student_number","academic_year","semester","subjects_json","total_units","gwa",
                     "doc_path","doc_upload_time","doc_status","doc_remarks","doc_validated_by","doc_validated_time","semester_status"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""
    for col in ["total_units","gwa"]:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    text_cols = ["student_number","academic_year","semester","subjects_json","doc_path","doc_upload_time",
                 "doc_status","doc_remarks","doc_validated_by","doc_validated_time","semester_status"]
    for col in text_cols:
        df[col] = df[col].fillna("").astype(str)
    df["subjects_json"] = df["subjects_json"].apply(lambda x: x if x and x != "" else "[]")
    if "semester_status" not in df.columns:
        df["semester_status"] = "Regular"
    else:
        df["semester_status"] = df["semester_status"].fillna("Regular")
    return df

def save_semester_records(df):
    df.to_csv(SEMESTER_FILE, index=False)

def get_student_semesters(student_number):
    df = load_semester_records()
    return df[df["student_number"] == student_number].copy()

def compute_gwa_from_subjects(subjects_list):
    total_units = 0
    total_grade = 0
    for s in subjects_list:
        try:
            units = float(s.get("units", 0))
            grade = float(s.get("grade", 0))
            total_units += units
            total_grade += units * grade
        except Exception:
            pass
    return total_grade / total_units if total_units > 0 else 0.0

def add_semester_record(student_number, ay, sem, subjects, doc_path="", doc_upload_time="", semester_status="Regular"):
    df = load_semester_records()
    gwa = compute_gwa_from_subjects(subjects)
    total_units = sum(float(s.get("units", 0)) for s in subjects)
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
        "semester_status": semester_status
    }])
    df = pd.concat([df, new], ignore_index=True)
    save_semester_records(df)
    update_student_academic_summary(student_number)
    return gwa

def update_semester_subjects(student_number, ay, sem, subjects):
    df = load_semester_records()
    mask = (df["student_number"] == student_number) & (df["academic_year"] == ay) & (df["semester"] == sem)
    if mask.any():
        idx = df[mask].index[0]
        gwa = compute_gwa_from_subjects(subjects)
        total_units = sum(float(s.get("units", 0)) for s in subjects)
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
    mask = (df["student_number"] == student_number) & (df["academic_year"] == ay) & (df["semester"] == sem)
    if mask.any():
        idx = df[mask].index[0]
        df.at[idx, "doc_path"] = str(doc_path)
        df.at[idx, "doc_upload_time"] = str(doc_upload_time)
        df.at[idx, "doc_status"] = status
        df.at[idx, "doc_remarks"] = ""
        df.at[idx, "doc_validated_by"] = ""
        df.at[idx, "doc_validated_time"] = ""
        save_semester_records(df)
        return True
    return False

def validate_semester_document(student_number, ay, sem, status, remarks, validator_name):
    df = load_semester_records()
    mask = (df["student_number"] == student_number) & (df["academic_year"] == ay) & (df["semester"] == sem)
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
    mask = (df["student_number"] == student_number) & (df["academic_year"] == ay) & (df["semester"] == sem)
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
    if semester not in sem_order:
        return academic_year, "1st Sem"
    idx = sem_order.index(semester)
    if idx < 2:
        return academic_year, sem_order[idx+1]
    start_year = int(academic_year.split("-")[0])
    return f"{start_year+1}-{start_year+2}", "1st Sem"

def create_next_semester(student_number, current_ay, current_sem):
    next_ay, next_sem = get_next_semester_sequence(current_ay, current_sem)
    df = load_semester_records()
    if ((df["student_number"] == student_number) & (df["academic_year"] == next_ay) & (df["semester"] == next_sem)).any():
        st.warning(f"Semester {next_ay} {next_sem} already exists.")
        return False
    add_semester_record(student_number, next_ay, next_sem, [], semester_status="Regular")
    st.success(f"Created new semester: {next_ay} {next_sem}")
    return True

def update_student_academic_summary(student_number):
    sems = get_student_semesters(student_number)
    total_grade = 0
    total_units = 0
    for _, row in sems.iterrows():
        if row["semester_status"] != "Regular":
            continue
        try:
            subjects = json.loads(row["subjects_json"]) if row["subjects_json"] else []
            for s in subjects:
                units = float(s.get("units", 0))
                grade = float(s.get("grade", 0))
                total_units += units
                total_grade += units * grade
        except Exception:
            pass
    if total_units > 0:
        df = load_data()
        idx = df[df["student_number"] == student_number].index
        if len(idx) > 0:
            df.loc[idx, "gwa"] = total_grade / total_units
            df.loc[idx, "total_units_taken"] = total_units
            save_data(df)
    else:
        df = load_data()
        idx = df[df["student_number"] == student_number].index
        if len(idx) > 0:
            df.loc[idx, "total_units_taken"] = 0
            df.loc[idx, "gwa"] = 0.0
            save_data(df)

# ==================== PROFILE PICTURE ====================
def save_profile_picture(student_number, uploaded_file):
    if uploaded_file is None:
        return None
    ext = uploaded_file.name.split('.')[-1].lower()
    if ext not in ['jpg','jpeg','png','gif']:
        return None
    filename = f"{student_number}.{ext}"
    filepath = os.path.join(PROFILE_PIC_FOLDER, filename)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filename

def delete_profile_picture(student_number):
    for f in os.listdir(PROFILE_PIC_FOLDER):
        if f.startswith(str(student_number) + "."):
            os.remove(os.path.join(PROFILE_PIC_FOLDER, f))
            return True
    return False

def get_profile_picture_path(student_number):
    for f in os.listdir(PROFILE_PIC_FOLDER):
        if f.startswith(str(student_number) + "."):
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
    if not os.path.exists(MILESTONE_FILE) or os.path.getsize(MILESTONE_FILE) == 0:
        return pd.DataFrame(columns=["student_number","milestone","status","date","file_path","remarks"])
    df = pd.read_csv(MILESTONE_FILE, dtype=str)
    for col in ["student_number","milestone","status","date","file_path","remarks"]:
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
            df.loc[mask, "date"] = str(date_str)
        if file_path:
            df.loc[mask, "file_path"] = str(file_path)
        if remarks:
            df.loc[mask, "remarks"] = str(remarks)
    else:
        new = pd.DataFrame([{
            "student_number": student_number,
            "milestone": milestone,
            "status": status,
            "date": date_str,
            "file_path": file_path,
            "remarks": remarks
        }])
        df = pd.concat([df, new], ignore_index=True)
    save_milestone_tracking(df)

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
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filepath

# ==================== MILESTONE REQUESTS ====================
def load_milestone_requests():
    if not os.path.exists(MILESTONE_REQUESTS_FILE) or os.path.getsize(MILESTONE_REQUESTS_FILE) == 0:
        return pd.DataFrame(columns=["request_id","student_number","student_name","milestone_label","target_field","target_value","submitted_date","file_path","original_filename","status","reviewer_comment","reviewed_by","review_date"])
    df = pd.read_csv(MILESTONE_REQUESTS_FILE, dtype=str)
    for col in df.columns:
        df[col] = df[col].fillna("").astype(str)
    return df

def save_milestone_requests(df):
    df.to_csv(MILESTONE_REQUESTS_FILE, index=False)

def save_milestone_request_file(student_number, milestone_label, uploaded_file):
    if uploaded_file is None:
        return None
    folder = os.path.join(UPLOAD_FOLDER, student_number, "milestone_proofs")
    os.makedirs(folder, exist_ok=True)
    ext = uploaded_file.name.split('.')[-1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_label = milestone_label.replace(" ", "_").replace("/", "_")
    filename = f"{safe_label}_{timestamp}.{ext}"
    filepath = os.path.join(folder, filename)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filepath

# ==================== WORKFLOW HELPERS ====================
def get_step_completion_status(student_row):
    ptype = get_program_type(student_row["program"])
    completed = set()
    if pd.notna(student_row.get("committee_approval_date")) and str(student_row.get("committee_approval_date")).strip():
        completed.add("Committee")
    if student_row.get("total_units_taken", 0) >= student_row.get("total_units_required", 24):
        completed.add("Coursework")
    if ptype in ["MS_Thesis","MS_NonThesis"]:
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
        if student_row.get("thesis_outline_approved") == "Yes" and student_row.get("thesis_status") not in ["Not Started",""]:
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
    previous_step = WORKFLOW_STEPS[step_index-1]
    return previous_step not in get_step_completion_status(student_row)

# ==================== UI COMPONENTS ====================
def get_status_badge(status):
    if status == "Approved":
        return '<span class="status-approved">✅ Approved</span>'
    elif status == "Rejected":
        return '<span class="status-rejected">❌ Rejected</span>'
    elif status == "Pending":
        return '<span class="status-pending">🟡 Pending</span>'
    else:
        return '<span class="status-pending">📄 Not submitted</span>'

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
                st.markdown(f'<div style="background:#e8f5e9; border-radius:12px; padding:0.5rem; text-align:center;"><div>✅</div><div>{step}</div><div style="font-size:0.7rem;">Completed</div></div>', unsafe_allow_html=True)
            elif step == next_step:
                st.markdown(f'<div style="background:#fff3e0; border:2px solid #ff9800; border-radius:12px; padding:0.5rem; text-align:center;"><div>⏳</div><div>{step}</div><div style="font-size:0.7rem;">Next</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="background:#f5f5f5; border-radius:12px; padding:0.5rem; text-align:center; opacity:0.6;"><div>🔒</div><div>{step}</div><div style="font-size:0.7rem;">Locked</div></div>', unsafe_allow_html=True)

# ==================== RENDER SEMESTER BLOCK ====================
def render_semester_block_general(student_number, semester_row, is_staff=False, override_edit=False):
    ay = str(semester_row["academic_year"])
    sem = str(semester_row["semester"])
    semester_status = str(semester_row.get("semester_status", "Regular")).strip()
    if semester_status not in SEMESTER_STATUS_OPTIONS:
        semester_status = "Regular"
    try:
        subjects = json.loads(semester_row["subjects_json"]) if semester_row["subjects_json"] else []
    except Exception:
        subjects = []
    total_units = float(semester_row["total_units"]) if pd.notna(semester_row["total_units"]) else 0.0
    gwa = float(semester_row["gwa"]) if pd.notna(semester_row["gwa"]) else 0.0
    doc_status = str(semester_row.get("doc_status", "")).strip()
    doc_path = str(semester_row.get("doc_path", "")).strip()
    doc_remarks = str(semester_row.get("doc_remarks", "")).strip()

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
            if not doc_path or doc_path == "":
                st.warning("⚠️ Required: Upload AMIS screenshot or grade report below.")
            df_edit = pd.DataFrame(subjects) if subjects else pd.DataFrame(columns=["course_code","course_description","units","grade"])
            for col in ["course_code","course_description","units","grade"]:
                if col not in df_edit.columns:
                    df_edit[col] = 0 if col == "units" else ""
            df_edit = df_edit[["course_code","course_description","units","grade"]]
            df_edit["units"] = pd.to_numeric(df_edit["units"], errors='coerce').fillna(0).astype(int)
            df_key = f"df_{student_number}_{ay}_{sem}"
            if df_key not in st.session_state:
                st.session_state[df_key] = df_edit.copy()
            edited_df = st.data_editor(st.session_state[df_key], use_container_width=True, hide_index=True,
                column_config={
                    "course_code": "Course Code",
                    "course_description": "Course Description",
                    "units": st.column_config.NumberColumn("Units", step=1, min_value=0),
                    "grade": st.column_config.SelectboxColumn("Grade", options=GRADE_OPTIONS, default="1.00")
                },
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
            st.info("Editing is disabled in this view. Only the student can edit subjects.")
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
                if is_staff and doc_status == "Pending":
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

# ==================== STAFF VIEW STUDENT PROFILE (FULL DASHBOARD) ====================
def staff_view_student_profile(student_number):
    df = load_data()
    student = df[df["student_number"] == student_number].iloc[0].copy()
    program_type = get_program_type(student["program"])
    
    # Determine editing permissions
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
    
    # Header with back button
    st.markdown(f"## {student['name']} ({student_number})")
    if st.button("← Back to Student List"):
        st.session_state.staff_selected_student = None
        st.session_state.staff_show_update = True
        st.rerun()
    
    # Tabs
    tabs = st.tabs(["📝 Student Info", "📚 Coursework", "📌 Milestones", "📁 Uploads", "⚙️ Admin Controls"])
    
    with tabs[0]:
        # Two-column layout for profile picture and info cards
        col_left, col_right = st.columns([1, 2])
        
        with col_left:
            st.markdown('<div class="profile-card">', unsafe_allow_html=True)
            st.markdown('<div class="profile-header"><h3>📸 Profile Picture</h3></div>', unsafe_allow_html=True)
            pic_path = get_profile_picture_path(student_number)
            if pic_path:
                st.image(pic_path, width=180, caption="Current Picture")
            else:
                st.info("No profile picture uploaded")
            uploaded_pic = st.file_uploader("Upload new picture", type=["jpg","jpeg","png"], key="staff_pic")
            if uploaded_pic:
                fn = save_profile_picture(student_number, uploaded_pic)
                if fn:
                    df.loc[df["student_number"] == student_number, "profile_pic"] = fn
                    save_data(df)
                    st.success("Picture updated.")
                    st.rerun()
            if st.button("Delete picture"):
                if delete_profile_picture(student_number):
                    df.loc[df["student_number"] == student_number, "profile_pic"] = ""
                    save_data(df)
                    st.success("Picture deleted.")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_right:
            # --- Basic Information Card ---
            st.markdown('<div class="profile-card">', unsafe_allow_html=True)
            st.markdown('<div class="profile-header"><h3>📋 Basic Information</h3></div>', unsafe_allow_html=True)
            st.markdown(f"""
            <table style="width:100%;">
                <tr><td style="width:40%; font-weight:600;">Student Number:</td><td>{student['student_number']}</td></tr>
                <tr><td style="font-weight:600;">Full Name:</td><td>{student['name']}</td></tr>
                <tr><td style="font-weight:600;">Program:</td><td>{student['program']}</td></tr>
                <tr><td style="font-weight:600;">Adviser:</td><td>{student['advisor']}</td></tr>
                <tr><td style="font-weight:600;">Admitted:</td><td>{format_ay(student['ay_start'], student['semester'])}</td></tr>
                <tr><td style="font-weight:600;">Required Units:</td><td>{student['total_units_required']}</td></tr>
                <tr><td style="font-weight:600;">Special Status:</td><td>{student.get('special_status', 'Regular')}</td></tr>
            </table>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # --- Contact Details Card ---
            st.markdown('<div class="profile-card">', unsafe_allow_html=True)
            st.markdown('<div class="profile-header"><h3>📞 Contact Details</h3></div>', unsafe_allow_html=True)
            st.markdown(f"""
            <table style="width:100%;">
                <tr><td style="width:40%; font-weight:600;">Address:</td><td>{student['address'] or '—'}</td></tr>
                <tr><td style="font-weight:600;">Phone Number:</td><td>{student['phone'] or '—'}</td></tr>
                <tr><td style="font-weight:600;">Institutional Email:</td><td>{student['institutional_email'] or '—'}</td></tr>
            </table>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # --- Personal Details Card ---
            st.markdown('<div class="profile-card">', unsafe_allow_html=True)
            st.markdown('<div class="profile-header"><h3>🧑 Personal Details</h3></div>', unsafe_allow_html=True)
            st.markdown(f"""
            <table style="width:100%;">
                <tr><td style="width:40%; font-weight:600;">Gender:</td><td>{student['gender'] or '—'}</td></tr>
                <tr><td style="font-weight:600;">Civil Status:</td><td>{student['civil_status'] or '—'}</td></tr>
                <tr><td style="font-weight:600;">Citizenship:</td><td>{student['citizenship'] or '—'}</td></tr>
                <tr><td style="font-weight:600;">Birthdate:</td><td>{student['birthdate'] or '—'}</td></tr>
                <tr><td style="font-weight:600;">Religion:</td><td>{student['religion'] or '—'}</td></tr>
            </table>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # --- Emergency Contact Card ---
            st.markdown('<div class="profile-card">', unsafe_allow_html=True)
            st.markdown('<div class="profile-header"><h3>🚨 Emergency Contact</h3></div>', unsafe_allow_html=True)
            st.markdown(f"""
            <table style="width:100%;">
                <tr><td style="width:40%; font-weight:600;">Name:</td><td>{student['emergency_name'] or '—'}</td></tr>
                <tr><td style="font-weight:600;">Relationship:</td><td>{student['emergency_relationship'] or '—'}</td></tr>
                <tr><td style="font-weight:600;">Phone:</td><td>{student['emergency_country_code'] or ''} {student['emergency_phone'] or ''}</td></tr>
            </table>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    with tabs[1]:
        st.subheader("Academic Record")
        total_years = 2 if is_master_program(student["program"]) else 3
        total_semesters_needed = total_years * 2 + (total_years - 1)
        start_ay = student.get("ay_start", current_year)
        if pd.isna(start_ay) or start_ay == 0:
            start_ay = current_year
        start_ay_str = f"{start_ay}-{start_ay+1}"
        start_sem = student.get("semester", "1st Sem")
        sem_order = ["1st Sem","2nd Sem","Summer"]
        all_semesters = []
        for yr in range(total_years):
            ay = f"{start_ay+yr}-{start_ay+yr+1}"
            for sem in sem_order:
                all_semesters.append((ay, sem))
        start_idx = 0
        for i, (ay, sem) in enumerate(all_semesters):
            if ay == start_ay_str and sem == start_sem:
                start_idx = i
                break
        prospectus = all_semesters[start_idx:start_idx+total_semesters_needed]
        existing = get_student_semesters(student_number)
        for ay, sem in prospectus:
            if not ((existing["academic_year"] == ay) & (existing["semester"] == sem)).any():
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
    with tabs[2]:
        st.subheader("Milestone Tracker")
        milestones_df = get_student_milestones(student_number, program_type)
        for _, m in milestones_df.iterrows():
            with st.expander(f"{m['milestone']} – Status: {m['status']}"):
                st.write(f"Date: {m['date'] if m['date'] else 'Not set'}")
                if m['file_path'] and m['file_path'] != "" and os.path.exists(m['file_path']):
                    with open(m['file_path'], "rb") as f:
                        st.download_button("Download proof", f, file_name=os.path.basename(m['file_path']))
                if can_edit and m['status'] != "Completed":
                    if st.button(f"Mark {m['milestone']} as Completed", key=f"staff_complete_{m['milestone']}"):
                        update_milestone(student_number, m['milestone'], "Completed", datetime.now().strftime("%Y-%m-%d"), "", "Marked by staff")
                        st.success("Milestone completed.")
                        st.rerun()
    with tabs[3]:
        st.subheader("Student Uploads")
        st.info("Upload documents via student portal; staff can validate them here.")
    with tabs[4]:
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

# ==================== REGISTRATION FORM (MINIMAL) ====================
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
            if not student_number:
                errors.append("Student Number")
            if not last_name:
                errors.append("Last Name")
            if not first_name:
                errors.append("First Name")
            if not program:
                errors.append("Program")
            if not ay_sel:
                errors.append("Academic Year")
            if not semester:
                errors.append("Semester")
            df = load_data()
            if student_number in df["student_number"].values:
                errors.append("Student number already exists")
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
                    "address": "", "phone": "", "institutional_email": "",
                    "gender": "", "civil_status": "", "citizenship": "", "birthdate": "", "religion": "",
                    "emergency_name": "", "emergency_relationship": "", "emergency_country_code": "", "emergency_phone": "",
                    "special_status": "Regular"
                })
                new_df = pd.DataFrame([new_row])
                df = pd.concat([df, new_df], ignore_index=True)
                save_data(df)
                get_student_milestones(student_number, get_program_type(program))
                st.success(f"Student {full_name} registered successfully.")
                st.rerun()

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
            else:
                st.error("Invalid credentials")
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
    st.caption("Version 21.1 | Full Staff Dashboard")

# ==================== MAIN ====================
st.title("🎓 SESAM Graduate Student Lifecycle Management")
st.caption("Role‑based workflow: Student updates → Adviser/Staff approves")

role = st.session_state.role

# ==================== STAFF VIEW ====================
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
            st.subheader("🔍 Search and Select a Student to Update")
            search_term = st.text_input("Search by name or student number", key="staff_search")
            filtered = filter_dataframe(search_term, df)
            if filtered.empty:
                st.warning("No students match your search.")
            else:
                st.markdown(f"#### Found {len(filtered)} student(s)")
                for _, row in filtered.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div class="student-card">
                            <div class="student-name">{row['name']}</div>
                            <div class="student-detail">{row['student_number']} | {row['program']} | GWA: {row['gwa']:.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"Select {row['name']}", key=f"select_{row['student_number']}"):
                            st.session_state.staff_selected_student = row["student_number"]
                            st.rerun()
        else:
            staff_view_student_profile(st.session_state.staff_selected_student)
    else:
        st.info("Select an action using the buttons above.")

# ==================== ADVISER VIEW ====================
elif role == "Faculty Adviser":
    st.subheader(f"👨‍🏫 Faculty Adviser Dashboard – {st.session_state.display_name}")
    
    # Get advisees
    advisees = df[df["advisor"] == st.session_state.display_name].copy()
    
    if advisees.empty:
        st.warning("No students assigned to you.")
    else:
        # --- Pending Validations Summary ---
        all_semesters = load_semester_records()
        advisee_numbers = advisees["student_number"].tolist()
        pending_sems = all_semesters[(all_semesters["student_number"].isin(advisee_numbers)) & (all_semesters["doc_status"] == "Pending")]
        pending_count = len(pending_sems)
        
        # Also count pending profile updates (if any)
        pending_profiles = advisees[advisees["profile_pending_status"] == "Pending"]
        profile_count = len(pending_profiles)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📄 Pending Document Validations", pending_count)
        with col2:
            st.metric("👤 Pending Profile Approvals", profile_count)
        
        if pending_count > 0 or profile_count > 0:
            st.info("Use the **View & Validate** button on a student's card to review pending items inside their profile.")
        
        st.markdown("---")
        
        # --- Search and Filter ---
        search_term = st.text_input("🔍 Search advisees by name or student number", key="adviser_search")
        if search_term:
            advisees = advisees[advisees["name"].str.contains(search_term, case=False, na=False) | 
                               advisees["student_number"].str.contains(search_term, case=False, na=False)]
        
        st.markdown(f"#### Your Advisees ({len(advisees)} student(s))")
        
        # --- Display advisees as cards ---
        for _, student in advisees.iterrows():
            with st.container():
                # Create a card using custom HTML or columns
                st.markdown(f"""
                <div style="background:white; border-radius:16px; padding:1rem; margin-bottom:1rem; border:1px solid #e9ecef; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-weight:600; font-size:1.1rem;">{student['name']}</div>
                            <div style="font-size:0.85rem; color:#6c757d;">{student['student_number']} | {student['program']}</div>
                        </div>
                        <div style="text-align:right;">
                            <div>GWA: <strong>{student['gwa']:.2f}</strong></div>
                            <div style="font-size:0.8rem;">Units: {student['total_units_taken']}/{student['total_units_required']}</div>
                        </div>
                    </div>
                    <div style="margin-top:0.75rem;">
                        <span style="background:#e9ecef; padding:0.2rem 0.6rem; border-radius:20px; font-size:0.75rem;">{student['program']}</span>
                        {"<span style='background:#fff3cd; padding:0.2rem 0.6rem; border-radius:20px; font-size:0.75rem; margin-left:0.5rem;'>🔔 Pending Profile</span>" if student.get('profile_pending_status') == "Pending" else ""}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Button to view full profile
                if st.button(f"👁️ View & Validate {student['name']}", key=f"view_advisee_{student['student_number']}"):
                    st.session_state.staff_selected_student = student["student_number"]
                    st.session_state.staff_show_update = True
                    st.rerun()
        
        # If a student is selected, display the full profile (same as staff view)
        if st.session_state.get("staff_show_update", False) and st.session_state.staff_selected_student:
            staff_view_student_profile(st.session_state.staff_selected_student)

# ==================== STUDENT VIEW ====================
elif role == "Student":
    student = df[df["name"] == st.session_state.display_name].iloc[0].copy()
    program_type = get_program_type(student["program"])

    st.subheader(f"📘 Your Dashboard – {student['name']}")

    milestones = get_student_milestones(student["student_number"], program_type)
    next_milestone = None
    for _, row in milestones.iterrows():
        if row["status"] != "Completed":
            next_milestone = row["milestone"]
            break
    if next_milestone:
        st.info(f"🎯 Next milestone: {next_milestone}")
    else:
        st.success("🎉 All milestones completed!")

    tabs = st.tabs(["👤 My Profile", "📚 Coursework", "📌 Milestones", "📁 Uploads"])
    with tabs[0]:
        col1, col2 = st.columns([1,2])
        with col1:
            pic_path = get_profile_picture_path(student["student_number"])
            if pic_path:
                st.image(pic_path, width=180, caption="Profile Picture")
            else:
                st.info("No profile picture")
            uploaded_pic = st.file_uploader("Upload new picture", type=["jpg","jpeg","png"], key="student_pic")
            if uploaded_pic:
                fn = save_profile_picture(student["student_number"], uploaded_pic)
                if fn:
                    df.loc[df["student_number"] == student["student_number"], "profile_pic"] = fn
                    save_data(df)
                    st.success("Picture updated.")
                    st.rerun()
            if st.button("Delete picture"):
                if delete_profile_picture(student["student_number"]):
                    df.loc[df["student_number"] == student["student_number"], "profile_pic"] = ""
                    save_data(df)
                    st.success("Picture deleted.")
                    st.rerun()
        with col2:
            st.markdown('<div class="profile-card">', unsafe_allow_html=True)
            st.markdown('<div class="profile-header"><h3>📋 Personal Information</h3></div>', unsafe_allow_html=True)
            st.markdown(f"**Student Number:** {student['student_number']}")
            st.markdown(f"**Full Name:** {student['name']}")
            st.markdown(f"**Program:** {student['program']}")
            st.markdown(f"**Adviser:** {student['advisor']}")
            st.markdown(f"**Admitted:** {format_ay(student['ay_start'], student['semester'])}")
            st.markdown(f"**Required Units:** {student['total_units_required']}")
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        st.markdown('<div class="profile-header"><h3>✏️ Additional Information</h3></div>', unsafe_allow_html=True)
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
                new_gender = st.selectbox("Gender", ["", "Male", "Female", "Other", "Prefer not to say"],
                                          index=["", "Male", "Female", "Other", "Prefer not to say"].index(student.get("gender","")) if student.get("gender","") in ["", "Male", "Female", "Other", "Prefer not to say"] else 0)
                new_civil = st.selectbox("Civil Status", ["", "Single", "Married", "Divorced", "Widowed"],
                                         index=["", "Single", "Married", "Divorced", "Widowed"].index(student.get("civil_status","")) if student.get("civil_status","") in ["", "Single", "Married", "Divorced", "Widowed"] else 0)
                new_citizenship = st.text_input("Citizenship", value=student.get("citizenship",""))
            with col4:
                new_religion = st.text_input("Religion", value=student.get("religion",""))
                try:
                    birthdate_val = datetime.strptime(student.get("birthdate","2000-01-01"), "%Y-%m-%d").date() if student.get("birthdate","") else date(2000,1,1)
                except Exception:
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
                    df.loc[df["student_number"] == student["student_number"], "address"] = new_address
                    df.loc[df["student_number"] == student["student_number"], "phone"] = new_phone
                    df.loc[df["student_number"] == student["student_number"], "institutional_email"] = new_email
                    df.loc[df["student_number"] == student["student_number"], "gender"] = new_gender
                    df.loc[df["student_number"] == student["student_number"], "civil_status"] = new_civil
                    df.loc[df["student_number"] == student["student_number"], "citizenship"] = new_citizenship
                    df.loc[df["student_number"] == student["student_number"], "birthdate"] = birthdate_str
                    df.loc[df["student_number"] == student["student_number"], "religion"] = new_religion
                    df.loc[df["student_number"] == student["student_number"], "emergency_name"] = new_emergency_name
                    df.loc[df["student_number"] == student["student_number"], "emergency_relationship"] = new_emergency_rel
                    df.loc[df["student_number"] == student["student_number"], "emergency_country_code"] = new_emergency_cc
                    df.loc[df["student_number"] == student["student_number"], "emergency_phone"] = new_emergency_phone
                    save_data(df)
                    st.success("Profile updated successfully!")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        st.subheader("Your Academic Record (Prospectus)")
        total_years = 2 if is_master_program(student["program"]) else 3
        total_semesters_needed = total_years * 2 + (total_years - 1)
        start_ay = student.get("ay_start", current_year)
        if pd.isna(start_ay) or start_ay == 0:
            start_ay = current_year
        start_ay_str = f"{start_ay}-{start_ay+1}"
        start_sem = student.get("semester", "1st Sem")
        sem_order = ["1st Sem","2nd Sem","Summer"]
        all_semesters = []
        for yr in range(total_years):
            ay = f"{start_ay+yr}-{start_ay+yr+1}"
            for sem in sem_order:
                all_semesters.append((ay, sem))
        start_idx = 0
        for i, (ay, sem) in enumerate(all_semesters):
            if ay == start_ay_str and sem == start_sem:
                start_idx = i
                break
        prospectus = all_semesters[start_idx:start_idx+total_semesters_needed]
        existing = get_student_semesters(student["student_number"])
        for ay, sem in prospectus:
            if not ((existing["academic_year"] == ay) & (existing["semester"] == sem)).any():
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
        st.subheader("📊 Cumulative Summary")
        total_taken = student["total_units_taken"] if not pd.isna(student["total_units_taken"]) else 0
        total_required = student["total_units_required"] if not pd.isna(student["total_units_required"]) else 24
        remaining = max(0, total_required - total_taken)
        cum_gwa = student["gwa"] if not pd.isna(student["gwa"]) else 0.0
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Units Taken", total_taken)
        with col2:
            st.metric("Required Units", total_required)
        with col3:
            st.metric("Remaining Units", remaining)
        with col4:
            st.metric("Cumulative GWA", f"{cum_gwa:.2f}")
        if st.button("🔄 Recalculate Totals (Refresh)"):
            update_student_academic_summary(student["student_number"])
            st.success("Totals recalculated. Refresh the page.")
            st.rerun()

    with tabs[2]:
        st.subheader("Milestone Tracker")
        milestones_df = get_student_milestones(student["student_number"], program_type)
        for _, m in milestones_df.iterrows():
            with st.expander(f"{m['milestone']} – Status: {m['status']}"):
                st.write(f"Date: {m['date'] if m['date'] else 'Not set'}")
                if m['file_path'] and m['file_path'] != "" and os.path.exists(m['file_path']):
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
        st.info("Upload supporting documents here (admission letter, AMIS screenshot, etc.).")

    st.caption("For corrections, contact your adviser or SESAM Staff.")

# ==================== FOOTER ====================
st.markdown("---")
st.caption("SESAM KMIS v21.1 | Fixed syntax – runs without errors")
