"""
SESAM KMIS - Graduate Student Lifecycle Management System
Version: 17.0 | Full UPLB Policy Compliance
"""

import streamlit as st
import pandas as pd
import os
import json
from datetime import date, datetime, timedelta

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
    .warning-banner { background-color: #ffcc00; color: #333; padding: 0.5rem; border-radius: 8px; margin: 0.5rem 0; font-weight: bold; }
    .danger-banner { background-color: #dc3545; color: white; padding: 0.5rem; border-radius: 8px; margin: 0.5rem 0; font-weight: bold; }
    .info-banner { background-color: #17a2b8; color: white; padding: 0.5rem; border-radius: 8px; margin: 0.5rem 0; }
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
            <br><br><strong>Your Rights:</strong> You may access, correct, and request deletion of your data. Requests can be submitted via the "Data Rights" tab in your dashboard.
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
def load_faculty():
    faculty_file = "faculty.csv"
    if os.path.exists(faculty_file):
        return pd.read_csv(faculty_file)
    else:
        default_faculty = pd.DataFrame([
            {"username": "adviser1", "password": "adv123", "role": "Faculty Adviser", "display_name": "Dr. Eslava", "email": "eslava@up.edu.ph"},
            {"username": "adviser2", "password": "adv456", "role": "Faculty Adviser", "display_name": "Dr. Sanchez", "email": "sanchez@up.edu.ph"}
        ])
        default_faculty.to_csv(faculty_file, index=False)
        return default_faculty

def load_users():
    faculty_df = load_faculty()
    users = {}
    for _, row in faculty_df.iterrows():
        users[row["username"]] = {
            "password": row["password"],
            "role": row["role"],
            "display_name": row["display_name"],
            "email": row.get("email", "")
        }
    users["staff1"] = {"password": "admin123", "role": "SESAM Staff", "display_name": "SESAM Administrator", "email": "admin@sesam.uplb.edu.ph"}
    for i in range(1, 14):
        sn = f"S00{i}" if i < 10 else f"S0{i}"
        users[sn] = {"password": sn, "role": "Student", "display_name": f"Student {sn}", "email": f"{sn}@up.edu.ph"}
    return users

USERS = load_users()

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
# Added "4.00" to GRADE_OPTIONS
GRADE_OPTIONS = ["1.00", "1.25", "1.50", "1.75", "2.00", "2.25", "2.50", "2.75", "3.00", "4.00", "INC", "DRP", "5.00", "P", "IP"]
SEMESTER_STATUS_OPTIONS = ["Regular", "Off-Sem", "On Leave", "Shifted Program", "Transferred"]
WORKFLOW_STEPS = ["Committee", "Coursework", "Exams", "POS", "Thesis", "Defense", "Graduation"]

def get_thesis_limit_from_program(program):
    ptype = get_program_type(program)
    return 12 if ptype in ["PhD_Regular", "PhD_Straight", "PhD_Research"] else (6 if ptype == "MS_Thesis" else 0)

def get_residency_max_from_program(program): return 5 if is_master_program(program) else 7
def format_ay(ay_start, semester): return f"A.Y. {ay_start}-{ay_start+1} ({semester})"

# ==================== DATA FILES ====================
DATA_FILE = "students.csv"
SEMESTER_FILE = "semester_records.csv"
MILESTONE_FILE = "milestone_tracking.csv"
UPLOAD_FOLDER = "student_uploads"
PROFILE_PIC_FOLDER = "profile_pics"
UPLOAD_FILE = "uploads.csv"
DATA_REQUEST_FILE = "data_requests.csv"  # for deletion/correction requests

for folder in [UPLOAD_FOLDER, PROFILE_PIC_FOLDER]:
    if not os.path.exists(folder): os.makedirs(folder)

# ==================== RULE ENFORCEMENT: GRADE CONVERSION (INC/4.0) ====================
def convert_expired_grades():
    """Automatically convert INC and 4.0 grades that are older than 1 year to 5.00 or Failed."""
    semesters_df = pd.read_csv(SEMESTER_FILE) if os.path.exists(SEMESTER_FILE) else None
    if semesters_df is None or semesters_df.empty:
        return
    modified = False
    for idx, row in semesters_df.iterrows():
        try:
            subjects = json.loads(row["subjects_json"]) if row["subjects_json"] else []
        except:
            continue
        sem_date_str = row.get("doc_upload_time", "")
        if sem_date_str and sem_date_str != "nan":
            try:
                sem_end = datetime.strptime(sem_date_str, "%Y-%m-%d %H:%M:%S")
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
                subj["remarks"] = f"Auto-converted from {grade} after deadline"
                changed = True
                modified = True
        if changed:
            semesters_df.at[idx, "subjects_json"] = json.dumps(subjects)
    if modified:
        semesters_df.to_csv(SEMESTER_FILE, index=False)
        # Update student academic summaries
        for sn in semesters_df["student_number"].unique():
            update_student_academic_summary(sn)

# ==================== RESIDENCY ENFORCEMENT ====================
def check_residency_enforcement(student_row, action_description="perform this action"):
    """Returns (allowed, message). If exceeded, blocks action unless overridden."""
    exceeded, years_used, max_years = check_residency_alert(student_row)
    if exceeded:
        return False, f"❌ Residency exceeded ({years_used} > {max_years} years). {action_description} is blocked. Please contact SESAM staff for extension."
    return True, ""

def check_residency_alert(student_row):
    admission_year = student_row["ay_start"]
    current_year = date.today().year
    years_used = current_year - admission_year
    max_years = student_row.get("residency_max_years", 5)
    if years_used > max_years:
        return True, years_used, max_years
    elif years_used > max_years - 1:
        return "warning", years_used, max_years
    return False, years_used, max_years

# ==================== PROBATIONARY CONDITION CHECK ====================
def check_probationary_status(student_number):
    """Checks if a probationary student met GWA >=2.0 after first semester."""
    df = load_students_data()
    student = df[df["student_number"] == student_number].iloc[0]
    if student.get("student_status") != "Probationary":
        return
    # Get first regular semester
    semesters = load_semester_records()
    sems = semesters[(semesters["student_number"] == student_number) & (semesters["semester_status"] == "Regular")]
    if len(sems) == 0:
        return
    first_sem = sems.sort_values(["ay_num", "order"]).iloc[0] if "order" in sems.columns else sems.iloc[0]
    try:
        subjects = json.loads(first_sem["subjects_json"]) if first_sem["subjects_json"] else []
    except:
        subjects = []
    grades = [float(s.get("grade", 0)) for s in subjects if s.get("grade") and s.get("grade") not in ["INC", "DRP", "P", "IP", "4.00"]]
    if len(grades) == 0:
        return
    gwa = sum(grades) / len(grades)
    if gwa < 2.0:
        df.loc[df["student_number"] == student_number, "student_status"] = "Disqualified (Probation Failed)"
        df.loc[df["student_number"] == student_number, "special_status"] = "Inactive"
        save_data(df)
        # Notify via sidebar (will show next login)
        st.warning(f"Student {student['name']} failed probation (GWA {gwa:.2f} < 2.0). Status set to Disqualified.")
    else:
        df.loc[df["student_number"] == student_number, "student_status"] = "Regular"
        save_data(df)

# ==================== CACHED DATA LOADING ====================
@st.cache_data(ttl=60)
def load_students_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = create_demo_data()
        save_data(df)
    default_df = create_demo_data()
    for col in default_df.columns:
        if col not in df.columns:
            df[col] = default_df[col]
    required_cols = ["prior_ms_graduate", "student_status", "address", "phone", "emergency_contact",
                     "profile_pending_address", "profile_pending_phone", "profile_pending_emergency",
                     "profile_pending_status", "profile_pending_remarks", "advisor_assigned_date", "special_status",
                     "external_reviewer", "data_request_type", "data_request_details", "data_request_status"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = "" if col not in ["prior_ms_graduate"] else False
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
    # Run grade conversion on load
    convert_expired_grades()
    return df

@st.cache_data(ttl=60)
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
        if "order" not in df.columns:
            df["order"] = df["semester"].map({"1st Sem":0,"2nd Sem":1,"Summer":2})
        if "ay_num" not in df.columns:
            df["ay_num"] = df["academic_year"].apply(lambda x: int(x.split("-")[0]) if "-" in str(x) else current_year)
        return df
    else:
        return pd.DataFrame(columns=["student_number","academic_year","semester","subjects_json","total_units","gwa",
                                     "doc_path","doc_upload_time","doc_status","doc_remarks","doc_validated_by","doc_validated_time","semester_status","order","ay_num"])

@st.cache_data(ttl=60)
def load_milestone_tracking():
    if os.path.exists(MILESTONE_FILE):
        df = pd.read_csv(MILESTONE_FILE)
        for col in ["student_number","milestone","status","date","file_path","remarks"]:
            if col not in df.columns: df[col] = ""
        return df
    return pd.DataFrame(columns=["student_number","milestone","status","date","file_path","remarks"])

def save_data(df): df.to_csv(DATA_FILE, index=False)
def save_semester_records(df): df.to_csv(SEMESTER_FILE, index=False)
def save_milestone_tracking(df): df.to_csv(MILESTONE_FILE, index=False)

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
        "special_status": ["Regular"]*13,
        "external_reviewer": [""]*13,
        "data_request_type": [""]*13,
        "data_request_details": [""]*13,
        "data_request_status": [""]*13,
    }
    return pd.DataFrame(data)

# ==================== SEMESTER & MILESTONE FUNCTIONS ====================
def update_student_academic_summary(student_number):
    sems = load_semester_records()
    sems = sems[sems["student_number"]==student_number]
    total_grade = total_units = 0
    thesis_units = 0
    for _, row in sems.iterrows():
        if row["semester_status"] != "Regular": continue
        try:
            subjects = json.loads(row["subjects_json"]) if row["subjects_json"] else []
            for s in subjects:
                grade_val = s.get("grade", "")
                if grade_val in ["INC", "DRP", "P", "IP", "4.00"]:
                    continue
                units = float(s.get("units",0))
                total_units += units
                try:
                    grade_num = float(grade_val)
                    total_grade += units * grade_num
                except:
                    pass
                if "thesis" in s.get("course_code","").lower() or "dissertation" in s.get("course_code","").lower():
                    if grade_val not in ["INC","DRP","4.00"]:
                        try:
                            g = float(grade_val)
                            if 1.0 <= g <= 3.0:
                                thesis_units += units
                        except:
                            pass
        except: pass
    df = load_students_data()
    idx = df[df["student_number"]==student_number].index
    if len(idx) > 0:
        if total_units > 0:
            df.loc[idx, "gwa"] = total_grade / total_units
            df.loc[idx, "total_units_taken"] = total_units
        df.loc[idx, "thesis_units_taken"] = thesis_units
        save_data(df)

def compute_gwa_from_subjects(subjects_list):
    total_units = total_grade = 0
    for s in subjects_list:
        grade_val = s.get("grade","")
        if grade_val in ["INC", "DRP", "P", "IP", "4.00"]:
            continue
        try:
            units = float(s.get("units",0))
            grade = float(grade_val)
            total_units += units
            total_grade += units * grade
        except: pass
    return total_grade/total_units if total_units>0 else 0.0

def add_semester_record(student_number, ay, sem, subjects, doc_path="", doc_upload_time="", semester_status="Regular"):
    # Residency enforcement
    df_students = load_students_data()
    student = df_students[df_students["student_number"]==student_number].iloc[0]
    allowed, msg = check_residency_enforcement(student, "add a new semester")
    if not allowed:
        raise ValueError(msg)
    df = load_semester_records()
    thesis_units_in_subjects = sum(float(s.get("units",0)) for s in subjects if "thesis" in s.get("course_code","").lower() or "dissertation" in s.get("course_code","").lower())
    if thesis_units_in_subjects > 0:
        allowed_units, current, limit = check_thesis_unit_limit(student_number, thesis_units_in_subjects, student["program"])
        if not allowed_units:
            raise ValueError(f"Thesis unit limit exceeded: {current} + {thesis_units_in_subjects} > {limit}")
    gwa = compute_gwa_from_subjects(subjects)
    total_units = sum(float(s.get("units",0)) for s in subjects)
    new = pd.DataFrame([{
        "student_number": student_number, "academic_year": ay, "semester": sem,
        "subjects_json": json.dumps(subjects), "total_units": total_units, "gwa": gwa,
        "doc_path": str(doc_path), "doc_upload_time": doc_upload_time,
        "doc_status": "Pending" if doc_path else "", "doc_remarks": "", "doc_validated_by": "", "doc_validated_time": "",
        "semester_status": semester_status, "order": {"1st Sem":0,"2nd Sem":1,"Summer":2}.get(sem,0),
        "ay_num": int(ay.split("-")[0])
    }])
    df = pd.concat([df, new], ignore_index=True)
    save_semester_records(df)
    update_student_academic_summary(student_number)
    # Check probation after first semester
    check_probationary_status(student_number)
    return gwa

def update_semester_subjects(student_number, ay, sem, subjects):
    df = load_semester_records()
    mask = (df["student_number"]==student_number) & (df["academic_year"]==ay) & (df["semester"]==sem)
    if mask.any():
        idx = df[mask].index[0]
        df_students = load_students_data()
        student = df_students[df_students["student_number"]==student_number].iloc[0]
        thesis_units_in_subjects = sum(float(s.get("units",0)) for s in subjects if "thesis" in s.get("course_code","").lower() or "dissertation" in s.get("course_code","").lower())
        if thesis_units_in_subjects > 0:
            allowed, current, limit = check_thesis_unit_limit(student_number, thesis_units_in_subjects, student["program"])
            if not allowed:
                st.error(f"Cannot save: Thesis unit limit exceeded. Current: {current}, Adding: {thesis_units_in_subjects}, Limit: {limit}")
                return False
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
        check_probationary_status(student_number)
        return True
    return False

def check_thesis_unit_limit(student_number, new_units, program):
    df = load_students_data()
    student = df[df["student_number"] == student_number].iloc[0]
    current = float(student["thesis_units_taken"]) if pd.notna(student["thesis_units_taken"]) else 0
    limit = get_thesis_limit_from_program(program)
    if current + new_units > limit:
        return False, current, limit
    return True, current, limit

def get_inc_grades_with_deadline(student_number):
    semesters_df = load_semester_records()
    student_sems = semesters_df[semesters_df["student_number"] == student_number]
    inc_items = []
    for _, row in student_sems.iterrows():
        try:
            subjects = json.loads(row["subjects_json"]) if row["subjects_json"] else []
        except:
            continue
        sem_date_str = row.get("doc_upload_time", "")
        if sem_date_str and sem_date_str != "nan":
            try:
                sem_end = datetime.strptime(sem_date_str, "%Y-%m-%d %H:%M:%S")
            except:
                sem_end = datetime.now()
        else:
            sem_end = datetime.now()
        deadline = sem_end + timedelta(days=365)
        for subj in subjects:
            grade = subj.get("grade", "")
            if grade in ["INC", "4.00"]:
                days_left = (deadline - datetime.now()).days
                inc_items.append({
                    "course": subj.get("course_code", "Unknown"),
                    "semester": f"{row['academic_year']} {row['semester']}",
                    "deadline": deadline.strftime("%Y-%m-%d"),
                    "days_left": days_left,
                    "status": "expired" if days_left < 0 else "warning" if days_left < 60 else "ok"
                })
    return inc_items

# ==================== MILESTONE DEFINITIONS ====================
MILESTONE_DEFS = {
    "MS_Thesis": ["Admission","Registration","Guidance Committee Formation","Plan of Study (POS)","Coursework Completion","General Examination","Thesis Work","External Review","Publishable Article","Final Examination","Final Submission","Graduation Clearance"],
    "MS_NonThesis": ["Admission","Registration","Guidance Committee Formation","Plan of Study (POS)","Coursework Completion","General Examination","External Review","Graduation Clearance"],
    "PhD_Regular": ["Admission","Registration","Advisory Committee Formation","Qualifying Exam","Plan of Study","Coursework","Comprehensive Exam","Dissertation","External Review","Publication","Final Defense","Submission","Graduation"],
    "PhD_Straight": ["Admission","Registration","Advisory Committee Formation","Plan of Study","Coursework","Comprehensive Exam","Dissertation","External Review","Publication (2 papers)","Final Defense","Submission","Graduation"],
    "PhD_Research": ["Admission","Registration","Supervisory Committee Formation","Plan of Research","Seminar Series (4 seminars)","Research Progress Review","Thesis Draft","Publication (min 2 papers)","Final Oral Examination","Thesis Submission","Graduation"]
}

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

def check_milestone_prerequisite(student_number, program_type, milestone_name, milestones_df):
    milestone_order = MILESTONE_DEFS.get(program_type, MILESTONE_DEFS["MS_Thesis"])
    if milestone_name not in milestone_order:
        return True, ""
    idx = milestone_order.index(milestone_name)
    if idx == 0:
        return True, ""
    previous = milestone_order[idx-1]
    prev_status = milestones_df[milestones_df["milestone"] == previous]["status"].values
    if len(prev_status) == 0 or prev_status[0] != "Completed":
        return False, f"❌ Cannot mark '{milestone_name}' as Completed because previous milestone '{previous}' is not yet Completed."
    # Residency enforcement for final milestones
    if milestone_name in ["Final Examination", "Final Defense", "Graduation Clearance", "Graduation"]:
        df_students = load_students_data()
        student = df_students[df_students["student_number"]==student_number].iloc[0]
        allowed, msg = check_residency_enforcement(student, "complete this milestone")
        if not allowed:
            return False, msg
    return True, ""

# ==================== DATA REQUEST (DELETION/CORRECTION) ====================
def load_data_requests():
    if os.path.exists(DATA_REQUEST_FILE):
        return pd.read_csv(DATA_REQUEST_FILE)
    else:
        return pd.DataFrame(columns=["request_id", "student_number", "request_type", "details", "status", "submitted_date", "reviewer_comment", "reviewed_by", "review_date"])

def save_data_requests(df):
    df.to_csv(DATA_REQUEST_FILE, index=False)

def submit_data_request(student_number, request_type, details):
    df = load_data_requests()
    new_id = len(df) + 1 if not df.empty else 1
    new = pd.DataFrame([{
        "request_id": new_id,
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

# ==================== HELPER UI FUNCTIONS ====================
def get_status_badge(status):
    if status == "Approved": return '<span class="status-approved">✅ Approved</span>'
    elif status == "Rejected": return '<span class="status-rejected">❌ Rejected</span>'
    elif status == "Pending": return '<span class="status-pending">🟡 Pending</span>'
    else: return '<span class="status-pending">📄 Not submitted</span>'

def filter_dataframe(search_term, data):
    if not search_term: return data
    mask = data["name"].str.contains(search_term, case=False, na=False) | data["student_number"].str.contains(search_term, case=False, na=False)
    return data[mask]

# ==================== PROFILE PICTURE & FILE FUNCTIONS ====================
def get_profile_picture_path(student_number):
    for f in os.listdir(PROFILE_PIC_FOLDER):
        if f.startswith(str(student_number)+"."):
            return os.path.join(PROFILE_PIC_FOLDER, f)
    return None

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

def save_uploaded_file(student_number, category, uploaded_file):
    if uploaded_file is None: return None
    student_folder = os.path.join(UPLOAD_FOLDER, student_number)
    os.makedirs(student_folder, exist_ok=True)
    ext = uploaded_file.name.split('.')[-1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{category}_{timestamp}.{ext}"
    filepath = os.path.join(student_folder, filename)
    with open(filepath, "wb") as f: f.write(uploaded_file.getbuffer())
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

def load_uploads():
    if os.path.exists(UPLOAD_FILE):
        return pd.read_csv(UPLOAD_FILE)
    else:
        return pd.DataFrame(columns=["student_number", "category", "file_path", "original_filename", "upload_date", "status", "reviewer_comment", "reviewed_by", "review_date"])

def save_uploads(df): df.to_csv(UPLOAD_FILE, index=False)

UPLOAD_CATEGORIES = ["admission_letter", "amis_screenshot", "committee_form", "plan_of_study", "thesis_file"]
UPLOAD_DISPLAY_NAMES = {
    "admission_letter": "Admission Letter",
    "amis_screenshot": "AMIS Screenshot",
    "committee_form": "Committee Form",
    "plan_of_study": "Plan of Study (POS)",
    "thesis_file": "Thesis/Dissertation File"
}

# ==================== RENDER SEMESTER BLOCK ====================
def render_semester_block_general(student_number, semester_row, is_staff=False, override_edit=False):
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
        can_edit_status = (is_staff and override_edit) or (not is_staff)
        if can_edit_status:
            new_status = st.selectbox("Semester Status", SEMESTER_STATUS_OPTIONS,
                                      index=SEMESTER_STATUS_OPTIONS.index(semester_status) if semester_status in SEMESTER_STATUS_OPTIONS else 0,
                                      key=f"status_{student_number}_{ay}_{sem}")
            if new_status != semester_status:
                update_semester_status(student_number, ay, sem, new_status)
                st.rerun()
        else:
            st.markdown(f"**Semester Status:** {semester_status}")
        st.markdown(f"**Document Validation:** {get_status_badge(doc_status)}", unsafe_allow_html=True)
        if doc_status == "Rejected" and doc_remarks: st.warning(f"Rejection reason: {doc_remarks}")
        if semester_status == "Regular" and (not is_staff or (is_staff and override_edit)):
            if not doc_path or doc_path == "nan": st.warning("⚠️ Required: Upload AMIS screenshot or grade report below.")
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
        st.markdown("---")
        st.markdown("**Upload Proof of Grades (AMIS Screenshot)**")
        if semester_status == "Regular":
            if doc_path and doc_path not in ["","nan"] and os.path.exists(doc_path):
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
                        with open(filepath,"wb") as f: f.write(uploaded.getbuffer())
                        update_semester_document(student_number, ay, sem, filepath, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Pending")
                        st.rerun()
            else:
                if doc_path and doc_path != "nan" and os.path.exists(doc_path):
                    st.caption("Document uploaded by student.")
        else: st.info(f"Semester status **{semester_status}** – no upload required.")
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

def create_next_semester(student_number, current_ay, current_sem):
    def get_next_semester_sequence(academic_year, semester):
        sem_order = ["1st Sem", "2nd Sem", "Summer"]
        if semester not in sem_order: return academic_year, "1st Sem"
        idx = sem_order.index(semester)
        if idx < 2: return academic_year, sem_order[idx+1]
        start_year = int(academic_year.split("-")[0])
        return f"{start_year+1}-{start_year+2}", "1st Sem"
    next_ay, next_sem = get_next_semester_sequence(current_ay, current_sem)
    df = load_semester_records()
    if ((df["student_number"]==student_number) & (df["academic_year"]==next_ay) & (df["semester"]==next_sem)).any():
        st.warning(f"Semester {next_ay} {next_sem} already exists.")
        return False
    try:
        add_semester_record(student_number, next_ay, next_sem, [], semester_status="Regular")
    except ValueError as e:
        st.error(str(e))
        return False
    st.success(f"Created new semester: {next_ay} {next_sem}")
    return True

# ==================== STAFF & STUDENT VIEW FUNCTIONS ====================
def render_profile_approval_section(student, is_staff=False):
    if student.get("profile_pending_status") == "Pending" and is_staff:
        st.markdown("#### Pending Profile Update")
        st.write(f"**New Address:** {student['profile_pending_address']}")
        st.write(f"**New Phone:** {student['profile_pending_phone']}")
        st.write(f"**New Emergency Contact:** {student['profile_pending_emergency']}")
        remarks = st.text_area("Remarks", key="prof_remarks")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve Profile Update"):
                df = load_students_data()
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
                df = load_students_data()
                df.loc[df["student_number"]==student["student_number"], "profile_pending_status"] = "Rejected"
                df.loc[df["student_number"]==student["student_number"], "profile_pending_remarks"] = remarks
                save_data(df)
                st.warning("Profile rejected.")
                st.rerun()
    elif student.get("profile_pending_status") == "Rejected":
        st.error(f"Profile update rejected: {student.get('profile_pending_remarks','')}")

def get_external_reviewer(student_number):
    df = load_students_data()
    student = df[df["student_number"] == student_number]
    if not student.empty and "external_reviewer" in student.columns:
        return student.iloc[0]["external_reviewer"]
    return ""

def set_external_reviewer(student_number, reviewer_name):
    df = load_students_data()
    if "external_reviewer" not in df.columns:
        df["external_reviewer"] = ""
    df.loc[df["student_number"] == student_number, "external_reviewer"] = reviewer_name
    save_data(df)

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
        faculty_df = load_faculty()
        adviser_options = ["Not assigned"] + faculty_df["display_name"].tolist()
        advisor = st.selectbox("Adviser", adviser_options)
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
            df = load_students_data()
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
                    "special_status": "Regular",
                    "external_reviewer": "",
                    "data_request_type": "", "data_request_details": "", "data_request_status": ""
                })
                new_df = pd.DataFrame([new_row])
                df = pd.concat([df, new_df], ignore_index=True)
                save_data(df)
                get_student_milestones(student_number, get_program_type(program))
                st.success(f"Student {full_name} registered successfully.")
                st.rerun()

def staff_view_student_profile(student_number):
    df = load_students_data()
    student = df[df["student_number"] == student_number].iloc[0].copy()
    program_type = get_program_type(student["program"])
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
    exceeded, years_used, max_years = check_residency_alert(student)
    if exceeded:
        st.markdown(f'<div class="danger-banner">⚠️ RESIDENCY EXCEEDED! This student has used {years_used} years out of max {max_years} years. Action required.</div>', unsafe_allow_html=True)
    elif exceeded == "warning":
        st.markdown(f'<div class="warning-banner">⚠️ Residency warning: {years_used} out of {max_years} years used. Only one year remaining.</div>', unsafe_allow_html=True)
    inc_items = get_inc_grades_with_deadline(student_number)
    for inc in inc_items:
        if inc["status"] == "expired":
            st.markdown(f'<div class="danger-banner">❌ INC/4.0 in {inc["course"]} ({inc["semester"]}) expired on {inc["deadline"]}. Automatically converted to 5.00.</div>', unsafe_allow_html=True)
        elif inc["status"] == "warning":
            st.markdown(f'<div class="warning-banner">⚠️ INC/4.0 in {inc["course"]} ({inc["semester"]}) deadline in {inc["days_left"]} days ({inc["deadline"]}).</div>', unsafe_allow_html=True)
    st.markdown(f"## {student['name']} ({student_number})")
    if st.button("← Back to Student List"):
        st.session_state.staff_selected_student = None
        st.session_state.staff_show_update = False
        st.rerun()
    tabs = st.tabs(["📝 Student Info", "📚 Coursework", "📌 Milestones", "📁 Uploads", "🔐 Data Requests", "⚙️ Admin Controls"])
    with tabs[0]:
        col1, col2 = st.columns([1,2])
        with col1:
            pic_path = get_profile_picture_path(student_number)
            if pic_path: st.image(pic_path, width=150)
            else: st.info("No profile picture")
        with col2:
            st.markdown(f"**Student Number:** {student_number}")
            st.markdown(f"**Name:** {student['name']}")
            st.markdown(f"**Program:** {student['program']}")
            st.markdown(f"**Adviser:** {student['advisor']}")
            st.markdown(f"**Admitted:** {format_ay(student['ay_start'], student['semester'])}")
            st.markdown(f"**Required Units:** {student['total_units_required']}")
            st.markdown(f"**Student Status:** {student.get('student_status', 'Regular')}")
            new_reviewer = st.text_input("External Reviewer (for PhD Final Defense)", value=get_external_reviewer(student_number))
            if new_reviewer != get_external_reviewer(student_number):
                set_external_reviewer(student_number, new_reviewer)
                st.success("External reviewer updated.")
        render_profile_approval_section(student, is_staff=True)
    with tabs[1]:
        st.subheader("Academic Record")
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
        existing = load_semester_records()
        existing = existing[existing["student_number"]==student_number]
        for ay,sem in prospectus:
            if not ((existing["academic_year"]==ay) & (existing["semester"]==sem)).any():
                try:
                    add_semester_record(student_number, ay, sem, [], semester_status="Regular")
                except ValueError as e:
                    st.error(str(e))
        semesters = load_semester_records()
        semesters = semesters[semesters["student_number"]==student_number]
        semesters = semesters.sort_values(["ay_num","order"]).reset_index(drop=True)
        for _, row in semesters.iterrows():
            render_semester_block_general(student_number, row, is_staff=True, override_edit=can_edit)
        if can_edit and st.button("➕ Add Next Semester (Staff)"):
            last_sem = semesters.iloc[-1] if not semesters.empty else None
            if last_sem:
                create_next_semester(student_number, last_sem["academic_year"], last_sem["semester"])
                st.rerun()
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
                if m['file_path'] and m['file_path'] != 'nan' and os.path.exists(m['file_path']):
                    with open(m['file_path'], "rb") as f:
                        st.download_button("Download proof", f, file_name=os.path.basename(m['file_path']))
                if can_edit and m['status'] != "Completed":
                    allowed, reason = check_milestone_prerequisite(student_number, program_type, m['milestone'], milestones_df)
                    if not allowed:
                        st.error(reason)
                    else:
                        if st.button(f"Mark {m['milestone']} as Completed", key=f"staff_complete_{m['milestone']}"):
                            update_milestone(student_number, m['milestone'], "Completed", datetime.now().strftime("%Y-%m-%d"), "", "Marked by staff")
                            st.success("Milestone completed.")
                            st.rerun()
        if is_phd_program(student["program"]):
            st.markdown("---")
            st.markdown("**External Reviewer (required for PhD Final Examination)**")
            rev = get_external_reviewer(student_number)
            if not rev:
                st.warning("No external reviewer assigned. Please assign one before final defense.")
            else:
                st.success(f"External reviewer: {rev}")
    with tabs[3]:
        st.subheader("Student Uploads")
        uploads_df = load_uploads()
        student_uploads = uploads_df[uploads_df["student_number"] == student_number]
        if student_uploads.empty:
            st.info("No documents uploaded.")
        else:
            for _, up in student_uploads.iterrows():
                st.write(f"**{UPLOAD_DISPLAY_NAMES.get(up['category'], up['category'])}** – Status: {up['status']}")
                if up["status"] == "Pending" and can_edit:
                    remarks_up = st.text_area("Remarks", key=f"upload_remarks_{up['category']}_{student_number}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ Approve", key=f"approve_upload_{student_number}_{up['category']}"):
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
    with tabs[4]:
        st.subheader("Data Rights Requests")
        requests_df = load_data_requests()
        student_requests = requests_df[requests_df["student_number"] == student_number]
        if student_requests.empty:
            st.info("No data requests from this student.")
        else:
            for _, req in student_requests.iterrows():
                st.write(f"**Request #{req['request_id']}** – Type: {req['request_type']} – Status: {req['status']}")
                st.write(f"Details: {req['details']}")
                if req["status"] == "Pending" and can_edit:
                    remarks = st.text_area("Reviewer comment", key=f"req_remarks_{req['request_id']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ Approve Request", key=f"approve_req_{req['request_id']}"):
                            if req["request_type"] == "Deletion":
                                # Mark student as deleted (anonymize)
                                df_stud = load_students_data()
                                df_stud.loc[df_stud["student_number"] == student_number, "name"] = "DELETED"
                                df_stud.loc[df_stud["student_number"] == student_number, "special_status"] = "Deleted"
                                save_data(df_stud)
                            elif req["request_type"] == "Correction":
                                # For prototype, just note that correction would be applied manually
                                st.info("Correction request noted. Manual intervention required for actual data change.")
                            # Update request status
                            requests_df.loc[requests_df.index[req.name], "status"] = "Approved"
                            requests_df.loc[requests_df.index[req.name], "reviewer_comment"] = remarks
                            requests_df.loc[requests_df.index[req.name], "reviewed_by"] = st.session_state.display_name
                            requests_df.loc[requests_df.index[req.name], "review_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            save_data_requests(requests_df)
                            st.success("Request approved.")
                            st.rerun()
                    with col2:
                        if st.button(f"❌ Reject Request", key=f"reject_req_{req['request_id']}"):
                            requests_df.loc[requests_df.index[req.name], "status"] = "Rejected"
                            requests_df.loc[requests_df.index[req.name], "reviewer_comment"] = remarks
                            requests_df.loc[requests_df.index[req.name], "reviewed_by"] = st.session_state.display_name
                            requests_df.loc[requests_df.index[req.name], "review_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            save_data_requests(requests_df)
                            st.warning("Request rejected.")
                            st.rerun()
    with tabs[5]:
        st.subheader("Administrative Controls")
        st.markdown("**Change Adviser**")
        faculty_df = load_faculty()
        adviser_options = ["Not assigned"] + faculty_df["display_name"].tolist()
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
        st.markdown("**Manual Override: Remove Residency Block**")
        if st.button("Grant Extension (add 1 year)"):
            # Simple extension: increase max_years by 1
            current_max = student["residency_max_years"]
            df.loc[df["student_number"] == student_number, "residency_max_years"] = current_max + 1
            save_data(df)
            st.success(f"Residency extended to {current_max+1} years.")
            st.rerun()

# ==================== MAIN ====================
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

df = load_students_data()

with st.sidebar:
    st.markdown(f"<div style='text-align:center'><h3>👤 {st.session_state.display_name}</h3><div>{st.session_state.role}</div><div>✅ Consent given</div></div>", unsafe_allow_html=True)
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.consent_given = False
        st.rerun()
    st.markdown("---")
    st.caption("Version 17.0 | Full UPLB Compliance | Grade 4.0 | Auto-INC | Residency Enforcement | Data Rights")

st.title("🎓 SESAM Graduate Student Lifecycle Management")
st.caption("Fully compliant with UPLB Graduate School policies: Grade 4.0 tracking, automatic INC conversion, residency enforcement, probation checks, and data privacy rights.")

role = st.session_state.role

if role == "SESAM Staff":
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
        st.info("Use the buttons above to register a new student or update existing student information.")

elif role == "Faculty Adviser":
    st.subheader(f"👨‍🏫 Your Advisees – {st.session_state.display_name}")
    advisees = df[df["advisor"] == st.session_state.display_name].copy()
    if advisees.empty:
        st.warning("No students assigned to you.")
    else:
        for _, student in advisees.iterrows():
            with st.expander(f"{student['name']} ({student['student_number']}) – {student['program']}"):
                st.write(f"GWA: {student['gwa']:.2f}, Units: {student['total_units_taken']}/{student['total_units_required']}")
                if student.get("profile_pending_status") == "Pending":
                    st.warning("Profile update pending approval")
                if st.button(f"View & Validate", key=f"view_{student['student_number']}"):
                    st.session_state.staff_selected_student = student["student_number"]
                    st.session_state.staff_show_update = True
                    st.rerun()
        if st.session_state.get("staff_show_update", False) and st.session_state.staff_selected_student:
            staff_view_student_profile(st.session_state.staff_selected_student)

elif role == "Student":
    student = df[df["name"] == st.session_state.display_name].iloc[0].copy()
    program_type = get_program_type(student["program"])
    st.subheader(f"📘 Your Dashboard – {student['name']}")
    if student.get("profile_pending_status") == "Pending":
        st.warning("Your profile update is pending approval.")
    elif student.get("profile_pending_status") == "Rejected":
        st.error(f"Profile update rejected: {student.get('profile_pending_remarks','')}")
    exceeded, years_used, max_years = check_residency_alert(student)
    if exceeded:
        st.markdown(f'<div class="danger-banner">⚠️ RESIDENCY EXCEEDED! You have used {years_used} out of {max_years} years. Please consult your adviser.</div>', unsafe_allow_html=True)
    elif exceeded == "warning":
        st.markdown(f'<div class="warning-banner">⚠️ Residency warning: {years_used} out of {max_years} years used. Only one year remaining.</div>', unsafe_allow_html=True)
    inc_items = get_inc_grades_with_deadline(student["student_number"])
    for inc in inc_items:
        if inc["status"] == "expired":
            st.markdown(f'<div class="danger-banner">❌ INC/4.0 in {inc["course"]} ({inc["semester"]}) expired on {inc["deadline"]}. This has been converted to 5.00. Please retake the course.</div>', unsafe_allow_html=True)
        elif inc["status"] == "warning":
            st.markdown(f'<div class="warning-banner">⚠️ INC/4.0 in {inc["course"]} ({inc["semester"]}) deadline in {inc["days_left"]} days ({inc["deadline"]}).</div>', unsafe_allow_html=True)
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
    tabs = st.tabs(["👤 My Profile", "📚 Coursework", "📌 Milestones", "📁 Uploads", "🔐 Data Rights"])
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
            st.markdown(f"**Student Status:** {student.get('student_status', 'Regular')}")
            if student.get("profile_pending_status") == "Pending":
                st.info("Your contact details are pending approval.")
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
        existing = load_semester_records()
        existing = existing[existing["student_number"]==student["student_number"]]
        for ay,sem in prospectus:
            if not ((existing["academic_year"]==ay) & (existing["semester"]==sem)).any():
                try:
                    add_semester_record(student["student_number"], ay, sem, [], semester_status="Regular")
                except ValueError as e:
                    st.error(str(e))
        semesters = load_semester_records()
        semesters = semesters[semesters["student_number"]==student["student_number"]]
        semesters = semesters.sort_values(["ay_num","order"]).reset_index(drop=True)
        for _, row in semesters.iterrows():
            render_semester_block_general(student["student_number"], row, is_staff=False, override_edit=False)
        if st.button("➕ Add Next Semester"):
            last_sem = semesters.iloc[-1] if not semesters.empty else None
            if last_sem:
                create_next_semester(student["student_number"], last_sem["academic_year"], last_sem["semester"])
                st.rerun()
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
                    allowed, reason = check_milestone_prerequisite(student["student_number"], program_type, m['milestone'], milestones_df)
                    if not allowed:
                        st.error(reason)
                    else:
                        uploaded = st.file_uploader("Upload proof", type=["pdf","jpg","png"], key=f"milestone_{m['milestone']}")
                        if st.button(f"Submit {m['milestone']}", key=f"submit_{m['milestone']}"):
                            if uploaded:
                                filepath = save_milestone_file(student["student_number"], m['milestone'], uploaded)
                                update_milestone(student["student_number"], m['milestone'], "Pending", datetime.now().strftime("%Y-%m-%d"), filepath, "")
                                st.success("Submitted for approval.")
                                st.rerun()
                            else:
                                st.error("Please upload a file.")
        if is_phd_program(student["program"]):
            st.markdown("---")
            st.markdown("**External Reviewer (required for PhD Final Examination)**")
            rev = get_external_reviewer(student["student_number"])
            if not rev:
                st.warning("No external reviewer assigned yet. Your adviser will assign one before your final defense.")
            else:
                st.success(f"External reviewer: {rev}")
    with tabs[3]:
        st.subheader("Upload Supporting Documents")
        category = st.selectbox("Document Type", UPLOAD_CATEGORIES, format_func=lambda x: UPLOAD_DISPLAY_NAMES.get(x,x))
        file = st.file_uploader("Choose file", type=["pdf","jpg","jpeg","png"])
        if st.button("Upload") and file:
            path = save_uploaded_file(student["student_number"], category, file)
            if path:
                st.success("Uploaded. Waiting for validation.")
                st.rerun()
    with tabs[4]:
        st.subheader("Your Data Privacy Rights")
        st.markdown("Under the Data Privacy Act of 2012, you have the right to request correction or deletion of your personal data.")
        req_type = st.selectbox("Request Type", ["Correction", "Deletion"])
        details = st.text_area("Details (for correction, specify which field and new value)")
        if st.button("Submit Request"):
            if details:
                submit_data_request(student["student_number"], req_type, details)
                st.success("Request submitted. Staff will review it.")
                st.rerun()
            else:
                st.error("Please provide details.")
        st.markdown("---")
        # Show existing requests
        req_df = load_data_requests()
        my_reqs = req_df[req_df["student_number"] == student["student_number"]]
        if not my_reqs.empty:
            st.subheader("Your Previous Requests")
            for _, req in my_reqs.iterrows():
                st.write(f"**{req['request_type']}** – Status: {req['status']} – Submitted: {req['submitted_date']}")
                if req["status"] == "Rejected" and req["reviewer_comment"]:
                    st.warning(f"Rejection reason: {req['reviewer_comment']}")
    st.caption("For corrections, contact your adviser or SESAM Staff.")

# Run once to ensure grade conversion on startup
convert_expired_grades()
