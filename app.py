"""
SESAM KMIS - Graduate Student Lifecycle Management System
Version: 18.0 | Full UPLB Policy Compliance & Data Handling Fixes
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
        if st.button("✅ I Consent", width="stretch", disabled=not agree):
            st.session_state.consent_given = True
            log_consent(st.session_state.username, st.session_state.role, st.session_state.display_name)
            st.rerun()

# ==================== USER AUTH ====================
def load_faculty():
    faculty_file = "faculty.csv"
    if os.path.exists(faculty_file) and os.path.getsize(faculty_file) > 0:
        df = pd.read_csv(faculty_file, dtype=str)
    else:
        df = pd.DataFrame([
            {"username": "adviser1", "password": "adv123", "role": "Faculty Adviser", "display_name": "Dr. Eslava", "email": "eslava@up.edu.ph"},
            {"username": "adviser2", "password": "adv456", "role": "Faculty Adviser", "display_name": "Dr. Sanchez", "email": "sanchez@up.edu.ph"}
        ])
        df.to_csv(faculty_file, index=False)
    return df

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
GRADE_OPTIONS = ["1.00", "1.25", "1.50", "1.75", "2.00", "2.25", "2.50", "2.75", "3.00", "4.00", "INC", "DRP", "5.00", "P", "IP"]
SEMESTER_STATUS_OPTIONS = ["Regular", "Off-Sem", "On Leave", "Shifted Program", "Transferred"]

def get_program_type(program_name):
    if program_name.startswith("MS") or program_name.startswith("Master"):
        return "MS_Thesis" if "Resilience" not in program_name or "Environmental Science" in program_name else "MS_NonThesis"
    elif program_name.startswith("PhD by Research"):
        return "PhD_Research"
    elif program_name.startswith("PhD"):
        return "PhD_Regular"
    return "MS_Thesis"

def is_master_program(program): return get_program_type(program).startswith("MS")
def is_phd_program(program): return get_program_type(program).startswith("PhD")
def get_required_units(program, prior_ms_graduate=False):
    if program == "MS Environmental Science": return 32
    if program == "PhD Environmental Science": return 37 if prior_ms_graduate else 50
    return None
def get_thesis_limit_from_program(program):
    ptype = get_program_type(program)
    if ptype in ["PhD_Regular", "PhD_Straight", "PhD_Research"]: return 12
    if ptype == "MS_Thesis": return 6
    return 0
def get_residency_max_from_program(program): return 5 if is_master_program(program) else 7
def format_ay(ay_start, semester): return f"A.Y. {ay_start}-{ay_start+1} ({semester})"

# ==================== DATA FILES ====================
DATA_FILE = "students.csv"
SEMESTER_FILE = "semester_records.csv"
MILESTONE_FILE = "milestone_tracking.csv"
UPLOAD_FOLDER = "student_uploads"
PROFILE_PIC_FOLDER = "profile_pics"
UPLOAD_FILE = "uploads.csv"
DATA_REQUEST_FILE = "data_requests.csv"

for folder in [UPLOAD_FOLDER, PROFILE_PIC_FOLDER]:
    if not os.path.exists(folder): os.makedirs(folder)

# ==================== CORE DATA FUNCTIONS ====================
def create_demo_students():
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
    df = pd.DataFrame(data)
    # Convert numeric cols
    for col in ["ay_start","gwa","total_units_taken","total_units_required","thesis_units_taken","thesis_units_limit","residency_years_used"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    # All other columns as string
    for col in df.columns:
        if col not in ["ay_start","gwa","total_units_taken","total_units_required","thesis_units_taken","thesis_units_limit","residency_years_used","prior_ms_graduate"]:
            df[col] = df[col].astype(str).replace("nan", "").replace("None", "")
    df["prior_ms_graduate"] = df["prior_ms_graduate"].astype(bool)
    return df

def load_students():
    if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
        df = pd.read_csv(DATA_FILE, dtype=str)
        # Convert numeric cols
        numeric = ["ay_start","gwa","total_units_taken","total_units_required","thesis_units_taken","thesis_units_limit","residency_years_used"]
        for col in numeric:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        # Ensure string columns are strings
        for col in df.columns:
            if col not in numeric and col != "prior_ms_graduate":
                df[col] = df[col].astype(str).replace("nan", "").replace("None", "")
        if "prior_ms_graduate" in df.columns:
            df["prior_ms_graduate"] = df["prior_ms_graduate"].astype(bool)
        else:
            df["prior_ms_graduate"] = False
    else:
        df = create_demo_students()
    # Recalculate derived fields
    for idx, row in df.iterrows():
        prog = row["program"]
        if prog not in PROGRAMS:
            df.at[idx, "program"] = PROGRAMS[0]
        df.at[idx, "residency_max_years"] = get_residency_max_from_program(prog)
        df.at[idx, "thesis_units_limit"] = get_thesis_limit_from_program(prog)
        req = get_required_units(prog, row.get("prior_ms_graduate", False))
        if req is not None:
            df.at[idx, "total_units_required"] = req
    df.to_csv(DATA_FILE, index=False)
    return df

def save_students(df): df.to_csv(DATA_FILE, index=False)

def load_semesters():
    if os.path.exists(SEMESTER_FILE) and os.path.getsize(SEMESTER_FILE) > 0:
        df = pd.read_csv(SEMESTER_FILE, dtype=str)
        required = ["student_number","academic_year","semester","subjects_json","total_units","gwa","doc_path","doc_upload_time","doc_status","doc_remarks","doc_validated_by","doc_validated_time","semester_status"]
        for col in required:
            if col not in df.columns:
                df[col] = ""
        df["total_units"] = pd.to_numeric(df["total_units"], errors="coerce").fillna(0)
        df["gwa"] = pd.to_numeric(df["gwa"], errors="coerce").fillna(0)
        df["subjects_json"] = df["subjects_json"].fillna("[]")
        df["order"] = df["semester"].map({"1st Sem":0,"2nd Sem":1,"Summer":2}).fillna(0)
        df["ay_num"] = df["academic_year"].apply(lambda x: int(x.split("-")[0]) if isinstance(x, str) and "-" in x else 2024)
        return df
    else:
        return pd.DataFrame(columns=["student_number","academic_year","semester","subjects_json","total_units","gwa","doc_path","doc_upload_time","doc_status","doc_remarks","doc_validated_by","doc_validated_time","semester_status","order","ay_num"])

def save_semesters(df): df.to_csv(SEMESTER_FILE, index=False)

def load_milestones():
    if os.path.exists(MILESTONE_FILE) and os.path.getsize(MILESTONE_FILE) > 0:
        df = pd.read_csv(MILESTONE_FILE, dtype=str)
        for col in ["student_number","milestone","status","date","file_path","remarks"]:
            if col not in df.columns:
                df[col] = ""
        return df
    return pd.DataFrame(columns=["student_number","milestone","status","date","file_path","remarks"])

def save_milestones(df): df.to_csv(MILESTONE_FILE, index=False)

def load_uploads():
    if os.path.exists(UPLOAD_FILE) and os.path.getsize(UPLOAD_FILE) > 0:
        return pd.read_csv(UPLOAD_FILE, dtype=str)
    return pd.DataFrame(columns=["student_number","category","file_path","original_filename","upload_date","status","reviewer_comment","reviewed_by","review_date"])

def save_uploads(df): df.to_csv(UPLOAD_FILE, index=False)

def load_data_requests():
    if os.path.exists(DATA_REQUEST_FILE) and os.path.getsize(DATA_REQUEST_FILE) > 0:
        return pd.read_csv(DATA_REQUEST_FILE, dtype=str)
    return pd.DataFrame(columns=["request_id","student_number","request_type","details","status","submitted_date","reviewer_comment","reviewed_by","review_date"])

def save_data_requests(df): df.to_csv(DATA_REQUEST_FILE, index=False)

# ==================== RULE ENFORCEMENT ====================
def check_residency_alert(student):
    admission_year = student["ay_start"]
    years_used = date.today().year - admission_year
    max_years = student.get("residency_max_years", 5)
    if years_used > max_years:
        return "exceeded", years_used, max_years
    if years_used > max_years - 1:
        return "warning", years_used, max_years
    return "ok", years_used, max_years

def convert_expired_grades():
    semesters = load_semesters()
    modified = False
    for idx, row in semesters.iterrows():
        try:
            subjects = json.loads(row["subjects_json"]) if row["subjects_json"] else []
        except:
            continue
        sem_date = row.get("doc_upload_time", "")
        if sem_date and sem_date != "nan":
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
        save_semesters(semesters)
        # Update GWA and units for all affected students
        for sn in semesters["student_number"].unique():
            update_student_academic_summary(sn)

def check_probationary_status(student_number):
    students = load_students()
    student = students[students["student_number"] == student_number].iloc[0]
    if student.get("student_status") != "Probationary":
        return
    sems = load_semesters()
    sems = sems[(sems["student_number"] == student_number) & (sems["semester_status"] == "Regular")]
    if len(sems) == 0:
        return
    first_sem = sems.sort_values(["ay_num","order"]).iloc[0]
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
        save_students(students)

def update_student_academic_summary(student_number):
    sems = load_semesters()
    sems = sems[sems["student_number"] == student_number]
    total_grade = 0
    total_units = 0
    thesis_units = 0
    for _, row in sems.iterrows():
        if row["semester_status"] != "Regular":
            continue
        try:
            subjects = json.loads(row["subjects_json"]) if row["subjects_json"] else []
        except:
            continue
        for subj in subjects:
            grade_val = subj.get("grade", "")
            if grade_val in ["INC", "DRP", "P", "IP", "4.00"]:
                continue
            units = float(subj.get("units", 0))
            total_units += units
            try:
                grade_num = float(grade_val)
                total_grade += units * grade_num
            except:
                pass
            if "thesis" in subj.get("course_code", "").lower() or "dissertation" in subj.get("course_code", "").lower():
                if grade_val not in ["INC","DRP","4.00"]:
                    try:
                        if 1.0 <= float(grade_val) <= 3.0:
                            thesis_units += units
                    except:
                        pass
    students = load_students()
    idx = students[students["student_number"] == student_number].index
    if len(idx) > 0:
        if total_units > 0:
            students.loc[idx, "gwa"] = total_grade / total_units
            students.loc[idx, "total_units_taken"] = total_units
        students.loc[idx, "thesis_units_taken"] = thesis_units
        save_students(students)

def check_residency_enforce(student, action):
    status, used, max_y = check_residency_alert(student)
    if status == "exceeded":
        return False, f"Residency exceeded ({used} > {max_y} years). Cannot {action}."
    return True, ""

def check_milestone_prerequisite(student_number, program_type, milestone, milestones_df):
    milestone_order = {
        "MS_Thesis": ["Admission","Registration","Guidance Committee Formation","Plan of Study (POS)","Coursework Completion","General Examination","Thesis Work","External Review","Publishable Article","Final Examination","Final Submission","Graduation Clearance"],
        "MS_NonThesis": ["Admission","Registration","Guidance Committee Formation","Plan of Study (POS)","Coursework Completion","General Examination","External Review","Graduation Clearance"],
        "PhD_Regular": ["Admission","Registration","Advisory Committee Formation","Qualifying Exam","Plan of Study","Coursework","Comprehensive Exam","Dissertation","External Review","Publication","Final Defense","Submission","Graduation"],
        "PhD_Straight": ["Admission","Registration","Advisory Committee Formation","Plan of Study","Coursework","Comprehensive Exam","Dissertation","External Review","Publication (2 papers)","Final Defense","Submission","Graduation"],
        "PhD_Research": ["Admission","Registration","Supervisory Committee Formation","Plan of Research","Seminar Series (4 seminars)","Research Progress Review","Thesis Draft","Publication (min 2 papers)","Final Oral Examination","Thesis Submission","Graduation"]
    }
    order = milestone_order.get(program_type, milestone_order["MS_Thesis"])
    if milestone not in order:
        return True, ""
    idx = order.index(milestone)
    if idx == 0:
        return True, ""
    prev = order[idx-1]
    prev_status = milestones_df[milestones_df["milestone"] == prev]["status"].values
    if len(prev_status) == 0 or prev_status[0] != "Completed":
        return False, f"Previous milestone '{prev}' not completed. Cannot mark '{milestone}'."
    return True, ""

# ==================== MILESTONE TRACKING ====================
def get_student_milestones(student_number, program_type):
    df = load_milestones()
    student_df = df[df["student_number"] == student_number]
    order = {
        "MS_Thesis": ["Admission","Registration","Guidance Committee Formation","Plan of Study (POS)","Coursework Completion","General Examination","Thesis Work","External Review","Publishable Article","Final Examination","Final Submission","Graduation Clearance"],
        "MS_NonThesis": ["Admission","Registration","Guidance Committee Formation","Plan of Study (POS)","Coursework Completion","General Examination","External Review","Graduation Clearance"],
        "PhD_Regular": ["Admission","Registration","Advisory Committee Formation","Qualifying Exam","Plan of Study","Coursework","Comprehensive Exam","Dissertation","External Review","Publication","Final Defense","Submission","Graduation"],
        "PhD_Straight": ["Admission","Registration","Advisory Committee Formation","Plan of Study","Coursework","Comprehensive Exam","Dissertation","External Review","Publication (2 papers)","Final Defense","Submission","Graduation"],
        "PhD_Research": ["Admission","Registration","Supervisory Committee Formation","Plan of Research","Seminar Series (4 seminars)","Research Progress Review","Thesis Draft","Publication (min 2 papers)","Final Oral Examination","Thesis Submission","Graduation"]
    }
    milestones = order.get(program_type, order["MS_Thesis"])
    if student_df.empty:
        new_rows = [{"student_number": student_number, "milestone": m, "status": "Not Started", "date": "", "file_path": "", "remarks": ""} for m in milestones]
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
        save_milestones(df)
        return df[df["student_number"] == student_number]
    else:
        existing = set(student_df["milestone"])
        missing = [m for m in milestones if m not in existing]
        if missing:
            new_rows = [{"student_number": student_number, "milestone": m, "status": "Not Started", "date": "", "file_path": "", "remarks": ""} for m in missing]
            df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
            save_milestones(df)
        return df[df["student_number"] == student_number]

def update_milestone(student_number, milestone, status, date_str, file_path, remarks):
    df = load_milestones()
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
        new = pd.DataFrame([{"student_number": student_number, "milestone": milestone, "status": status, "date": date_str, "file_path": file_path, "remarks": remarks}])
        df = pd.concat([df, new], ignore_index=True)
    save_milestones(df)

# ==================== SEMESTER MANAGEMENT ====================
def add_semester_record(student_number, ay, sem, subjects, doc_path="", doc_upload_time="", semester_status="Regular"):
    students = load_students()
    student = students[students["student_number"] == student_number].iloc[0]
    ok, msg = check_residency_enforce(student, "add a new semester")
    if not ok:
        raise ValueError(msg)
    df = load_semesters()
    total_units = sum(float(s.get("units",0)) for s in subjects)
    # Compute GWA
    total_grade = 0
    total_grade_units = 0
    for s in subjects:
        g = s.get("grade", "")
        if g in ["INC", "DRP", "P", "IP"]:
            continue
        units = float(s.get("units",0))
        try:
            gnum = float(g)
            total_grade += units * gnum
            total_grade_units += units
        except:
            pass
    gwa = total_grade / total_grade_units if total_grade_units > 0 else 0.0
    new = pd.DataFrame([{
        "student_number": student_number,
        "academic_year": ay,
        "semester": sem,
        "subjects_json": json.dumps(subjects),
        "total_units": total_units,
        "gwa": gwa,
        "doc_path": str(doc_path),
        "doc_upload_time": doc_upload_time,
        "doc_status": "Pending" if doc_path else "",
        "doc_remarks": "",
        "doc_validated_by": "",
        "doc_validated_time": "",
        "semester_status": semester_status,
        "order": {"1st Sem":0,"2nd Sem":1,"Summer":2}.get(sem,0),
        "ay_num": int(ay.split("-")[0])
    }])
    df = pd.concat([df, new], ignore_index=True)
    save_semesters(df)
    update_student_academic_summary(student_number)
    check_probationary_status(student_number)
    return gwa

def update_semester_subjects(student_number, ay, sem, subjects):
    df = load_semesters()
    mask = (df["student_number"] == student_number) & (df["academic_year"] == ay) & (df["semester"] == sem)
    if not mask.any():
        return False
    idx = df[mask].index[0]
    total_units = sum(float(s.get("units",0)) for s in subjects)
    total_grade = 0
    total_grade_units = 0
    for s in subjects:
        g = s.get("grade", "")
        if g in ["INC", "DRP", "P", "IP"]:
            continue
        units = float(s.get("units",0))
        try:
            gnum = float(g)
            total_grade += units * gnum
            total_grade_units += units
        except:
            pass
    gwa = total_grade / total_grade_units if total_grade_units > 0 else 0.0
    df.at[idx, "subjects_json"] = json.dumps(subjects)
    df.at[idx, "total_units"] = total_units
    df.at[idx, "gwa"] = gwa
    if df.at[idx, "doc_status"] == "Approved":
        df.at[idx, "doc_status"] = "Pending"
        df.at[idx, "doc_remarks"] = "Subjects edited; re-upload required."
    save_semesters(df)
    update_student_academic_summary(student_number)
    check_probationary_status(student_number)
    return True

def update_semester_document(student_number, ay, sem, doc_path, doc_upload_time, status="Pending"):
    df = load_semesters()
    mask = (df["student_number"] == student_number) & (df["academic_year"] == ay) & (df["semester"] == sem)
    if mask.any():
        idx = df[mask].index[0]
        df.at[idx, "doc_path"] = str(doc_path)
        df.at[idx, "doc_upload_time"] = doc_upload_time
        df.at[idx, "doc_status"] = status
        df.at[idx, "doc_remarks"] = ""
        df.at[idx, "doc_validated_by"] = ""
        df.at[idx, "doc_validated_time"] = ""
        save_semesters(df)
        return True
    return False

def validate_semester_document(student_number, ay, sem, status, remarks, validator_name):
    df = load_semesters()
    mask = (df["student_number"] == student_number) & (df["academic_year"] == ay) & (df["semester"] == sem)
    if mask.any():
        idx = df[mask].index[0]
        df.at[idx, "doc_status"] = status
        df.at[idx, "doc_remarks"] = remarks
        df.at[idx, "doc_validated_by"] = validator_name
        df.at[idx, "doc_validated_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_semesters(df)
        return True
    return False

def get_student_semesters(student_number):
    df = load_semesters()
    return df[df["student_number"] == student_number].copy()

# ==================== EXTERNAL REVIEWER ====================
def get_external_reviewer(student_number):
    df = load_students()
    if "external_reviewer" in df.columns:
        val = df[df["student_number"] == student_number]["external_reviewer"].values
        return val[0] if len(val) > 0 else ""
    return ""

def set_external_reviewer(student_number, reviewer):
    df = load_students()
    if "external_reviewer" not in df.columns:
        df["external_reviewer"] = ""
    df.loc[df["student_number"] == student_number, "external_reviewer"] = str(reviewer)
    save_students(df)

# ==================== UI HELPER ====================
def get_status_badge(status):
    if status == "Approved":
        return '<span class="status-approved">✅ Approved</span>'
    elif status == "Rejected":
        return '<span class="status-rejected">❌ Rejected</span>'
    elif status == "Pending":
        return '<span class="status-pending">🟡 Pending</span>'
    return '<span class="status-pending">📄 Not submitted</span>'

def filter_dataframe(search_term, data):
    if not search_term:
        return data
    mask = data["name"].str.contains(search_term, case=False, na=False) | data["student_number"].str.contains(search_term, case=False, na=False)
    return data[mask]

# ==================== PROFILE PICTURE ====================
def get_profile_picture_path(student_number):
    for f in os.listdir(PROFILE_PIC_FOLDER):
        if f.startswith(str(student_number) + "."):
            return os.path.join(PROFILE_PIC_FOLDER, f)
    return None

def save_profile_picture(student_number, uploaded_file):
    if uploaded_file is None:
        return None
    ext = uploaded_file.name.split('.')[-1].lower()
    if ext not in ["jpg","jpeg","png","gif"]:
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

# ==================== STAFF VIEW ====================
def staff_view_student_profile(student_number):
    students = load_students()
    student = students[students["student_number"] == student_number].iloc[0].copy()
    program_type = get_program_type(student["program"])
    
    status, used, max_y = check_residency_alert(student)
    if status == "exceeded":
        st.markdown(f'<div class="danger-banner">⚠️ RESIDENCY EXCEEDED: {used} years used (max {max_y}). Action required.</div>', unsafe_allow_html=True)
    elif status == "warning":
        st.markdown(f'<div class="warning-banner">⚠️ Residency warning: {used} out of {max_y} years used. One year remaining.</div>', unsafe_allow_html=True)
    
    inc_items = get_inc_alert(student_number)
    for inc in inc_items:
        if inc["status"] == "expired":
            st.markdown(f'<div class="danger-banner">❌ {inc["course"]} ({inc["semester"]}) INC/4.0 expired on {inc["deadline"]}. Auto-converted to 5.00.</div>', unsafe_allow_html=True)
        elif inc["status"] == "warning":
            st.markdown(f'<div class="warning-banner">⚠️ {inc["course"]} ({inc["semester"]}) INC/4.0 deadline in {inc["days_left"]} days ({inc["deadline"]}).</div>', unsafe_allow_html=True)
    
    st.markdown(f"## {student['name']} ({student_number})")
    if st.button("← Back to Student List"):
        st.session_state.staff_selected_student = None
        st.session_state.staff_show_update = False
        st.rerun()
    
    can_edit = False
    if student["advisor"] == "Not assigned":
        can_edit = True
        st.info("ℹ️ No adviser assigned. You can edit this student's records directly.")
    else:
        st.warning(f"⚠️ Adviser assigned: {student['advisor']}. Editing is restricted.")
        if st.checkbox("🔓 Override restrictions (admin override)"):
            can_edit = True
            st.info("Override active – you can now edit this student's records.")
    
    tabs = st.tabs(["📝 Info", "📚 Coursework", "📌 Milestones", "📁 Uploads", "🔐 Data Requests", "⚙️ Admin"])
    with tabs[0]:
        col1, col2 = st.columns([1,2])
        with col1:
            pic = get_profile_picture_path(student_number)
            if pic:
                st.image(pic, width=150)
            else:
                st.info("No profile picture")
            up = st.file_uploader("Upload picture", type=["jpg","jpeg","png"], key="staff_pic")
            if up:
                fn = save_profile_picture(student_number, up)
                if fn:
                    students.loc[students["student_number"] == student_number, "profile_pic"] = fn
                    save_students(students)
                    st.success("Picture updated.")
                    st.rerun()
            if st.button("Delete picture"):
                if delete_profile_picture(student_number):
                    students.loc[students["student_number"] == student_number, "profile_pic"] = ""
                    save_students(students)
                    st.rerun()
        with col2:
            st.markdown(f"**Student Number:** {student_number}")
            st.markdown(f"**Name:** {student['name']}")
            st.markdown(f"**Program:** {student['program']}")
            st.markdown(f"**Adviser:** {student['advisor']}")
            st.markdown(f"**Admitted:** {format_ay(student['ay_start'], student['semester'])}")
            st.markdown(f"**Required Units:** {student['total_units_required']}")
            st.markdown(f"**Student Status:** {student.get('student_status', 'Regular')}")
            new_rev = st.text_input("External Reviewer (PhD Final Exam)", value=get_external_reviewer(student_number))
            if new_rev != get_external_reviewer(student_number):
                set_external_reviewer(student_number, new_rev)
                st.success("External reviewer updated.")
        # Profile approval
        if student.get("profile_pending_status") == "Pending":
            st.markdown("#### Pending Profile Update")
            st.write(f"New Address: {student['profile_pending_address']}")
            st.write(f"New Phone: {student['profile_pending_phone']}")
            st.write(f"New Emergency Contact: {student['profile_pending_emergency']}")
            remarks = st.text_area("Remarks", key="prof_remarks")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ Approve Profile Update"):
                    students.loc[students["student_number"] == student_number, "address"] = student["profile_pending_address"]
                    students.loc[students["student_number"] == student_number, "phone"] = student["profile_pending_phone"]
                    students.loc[students["student_number"] == student_number, "emergency_contact"] = student["profile_pending_emergency"]
                    students.loc[students["student_number"] == student_number, "profile_pending_status"] = "Approved"
                    students.loc[students["student_number"] == student_number, "profile_pending_remarks"] = remarks
                    save_students(students)
                    st.success("Profile approved.")
                    st.rerun()
            with col_b:
                if st.button("❌ Reject Profile Update"):
                    students.loc[students["student_number"] == student_number, "profile_pending_status"] = "Rejected"
                    students.loc[students["student_number"] == student_number, "profile_pending_remarks"] = remarks
                    save_students(students)
                    st.warning("Profile rejected.")
                    st.rerun()
        elif student.get("profile_pending_status") == "Rejected":
            st.error(f"Profile update rejected: {student.get('profile_pending_remarks','')}")
    
    with tabs[1]:
        st.subheader("Academic Record")
        # Auto-generate semesters
        total_years = 2 if is_master_program(student["program"]) else 3
        total_semesters_needed = total_years * 2 + (total_years - 1)
        start_ay = student["ay_start"] if pd.notna(student["ay_start"]) else 2024
        start_ay_str = f"{start_ay}-{start_ay+1}"
        start_sem = student["semester"]
        sem_order = ["1st Sem","2nd Sem","Summer"]
        all_sem = []
        for yr in range(total_years):
            ay = f"{start_ay+yr}-{start_ay+yr+1}"
            for sem in sem_order:
                all_sem.append((ay,sem))
        start_idx = 0
        for i, (ay,sem) in enumerate(all_sem):
            if ay == start_ay_str and sem == start_sem:
                start_idx = i
                break
        prospectus = all_sem[start_idx:start_idx+total_semesters_needed]
        existing = get_student_semesters(student_number)
        for ay,sem in prospectus:
            if not ((existing["academic_year"] == ay) & (existing["semester"] == sem)).any():
                try:
                    add_semester_record(student_number, ay, sem, [], semester_status="Regular")
                except ValueError as e:
                    st.error(str(e))
        semesters = get_student_semesters(student_number)
        semesters = semesters.sort_values(["ay_num","order"]).reset_index(drop=True)
        for _, row in semesters.iterrows():
            render_semester_block(student_number, row, is_staff=True, can_edit=can_edit)
        if can_edit and st.button("➕ Add Next Semester"):
            last = semesters.iloc[-1] if not semesters.empty else None
            if last:
                new_ay, new_sem = get_next_semester(last["academic_year"], last["semester"])
                if new_ay:
                    try:
                        add_semester_record(student_number, new_ay, new_sem, [], semester_status="Regular")
                        st.success(f"Added {new_ay} {new_sem}")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Units Taken", student["total_units_taken"])
        col2.metric("Required", student["total_units_required"])
        col3.metric("Remaining", max(0, student["total_units_required"] - student["total_units_taken"]))
        col4.metric("Cumulative GWA", f"{student['gwa']:.2f}")
    
    with tabs[2]:
        st.subheader("Milestone Tracker")
        milestones = get_student_milestones(student_number, program_type)
        for _, m in milestones.iterrows():
            with st.expander(f"{m['milestone']} – Status: {m['status']}"):
                st.write(f"Date: {m['date'] if m['date'] else 'Not set'}")
                if m['file_path'] and m['file_path'] != "nan" and os.path.exists(str(m['file_path'])):
                    with open(m['file_path'], "rb") as f:
                        st.download_button("Download proof", f, file_name=os.path.basename(m['file_path']))
                if can_edit and m['status'] != "Completed":
                    allowed, reason = check_milestone_prerequisite(student_number, program_type, m['milestone'], milestones)
                    if not allowed:
                        st.error(reason)
                    else:
                        if st.button(f"Mark as Completed", key=f"staff_complete_{m['milestone']}"):
                            update_milestone(student_number, m['milestone'], "Completed", datetime.now().strftime("%Y-%m-%d"), "", "Marked by staff")
                            st.success("Milestone completed.")
                            st.rerun()
        if is_phd_program(student["program"]):
            rev = get_external_reviewer(student_number)
            st.markdown("---")
            st.markdown("**External Reviewer (PhD Final Exam)**")
            if not rev:
                st.warning("No external reviewer assigned.")
            else:
                st.success(f"Assigned: {rev}")
    
    with tabs[3]:
        st.subheader("Uploaded Documents")
        uploads = load_uploads()
        student_uploads = uploads[uploads["student_number"] == student_number]
        if student_uploads.empty:
            st.info("No documents uploaded.")
        else:
            for _, u in student_uploads.iterrows():
                st.write(f"**{u['category']}** – Status: {u['status']}")
                if u["status"] == "Pending" and can_edit:
                    remarks = st.text_area("Remarks", key=f"rem_{u['category']}_{student_number}")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ Approve", key=f"app_{student_number}_{u['category']}"):
                            df_up = load_uploads()
                            df_up.loc[df_up.index[u.name], "status"] = "Approved"
                            df_up.loc[df_up.index[u.name], "reviewer_comment"] = remarks
                            df_up.loc[df_up.index[u.name], "reviewed_by"] = st.session_state.display_name
                            df_up.loc[df_up.index[u.name], "review_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            save_uploads(df_up)
                            st.success("Approved.")
                            st.rerun()
                    with c2:
                        if st.button("❌ Reject", key=f"rej_{student_number}_{u['category']}"):
                            df_up = load_uploads()
                            df_up.loc[df_up.index[u.name], "status"] = "Rejected"
                            df_up.loc[df_up.index[u.name], "reviewer_comment"] = remarks
                            df_up.loc[df_up.index[u.name], "reviewed_by"] = st.session_state.display_name
                            df_up.loc[df_up.index[u.name], "review_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            save_uploads(df_up)
                            st.warning("Rejected.")
                            st.rerun()
    
    with tabs[4]:
        st.subheader("Data Rights Requests")
        reqs = load_data_requests()
        student_reqs = reqs[reqs["student_number"] == student_number]
        if student_reqs.empty:
            st.info("No requests from this student.")
        else:
            for _, r in student_reqs.iterrows():
                st.write(f"**{r['request_type']}** – Status: {r['status']} – Submitted: {r['submitted_date']}")
                st.write(f"Details: {r['details']}")
                if r["status"] == "Pending" and can_edit:
                    comment = st.text_area("Reviewer comment", key=f"req_comment_{r['request_id']}")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ Approve", key=f"app_req_{r['request_id']}"):
                            if r["request_type"] == "Deletion":
                                # Anonymize student
                                students = load_students()
                                students.loc[students["student_number"] == student_number, "name"] = "DELETED"
                                students.loc[students["student_number"] == student_number, "special_status"] = "Deleted"
                                save_students(students)
                            # Update request
                            reqs.loc[reqs.index[r.name], "status"] = "Approved"
                            reqs.loc[reqs.index[r.name], "reviewer_comment"] = comment
                            reqs.loc[reqs.index[r.name], "reviewed_by"] = st.session_state.display_name
                            reqs.loc[reqs.index[r.name], "review_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            save_data_requests(reqs)
                            st.success("Request approved.")
                            st.rerun()
                    with c2:
                        if st.button("❌ Reject", key=f"rej_req_{r['request_id']}"):
                            reqs.loc[reqs.index[r.name], "status"] = "Rejected"
                            reqs.loc[reqs.index[r.name], "reviewer_comment"] = comment
                            reqs.loc[reqs.index[r.name], "reviewed_by"] = st.session_state.display_name
                            reqs.loc[reqs.index[r.name], "review_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            save_data_requests(reqs)
                            st.warning("Request rejected.")
                            st.rerun()
    
    with tabs[5]:
        st.subheader("Administrative Controls")
        st.markdown("**Change Adviser**")
        faculty_df = load_faculty()
        adviser_opts = ["Not assigned"] + faculty_df["display_name"].tolist()
        new_adv = st.selectbox("Select adviser", adviser_opts, index=adviser_opts.index(student["advisor"]) if student["advisor"] in adviser_opts else 0)
        if st.button("Update Adviser"):
            students.loc[students["student_number"] == student_number, "advisor"] = new_adv
            save_students(students)
            st.success("Adviser updated.")
            st.rerun()
        st.markdown("**Change Program**")
        new_prog = st.selectbox("New Program", PROGRAMS, index=PROGRAMS.index(student["program"]) if student["program"] in PROGRAMS else 0)
        if st.button("Update Program"):
            prior = student.get("prior_ms_graduate", False)
            new_req = get_required_units(new_prog, prior)
            students.loc[students["student_number"] == student_number, "program"] = new_prog
            if new_req is not None:
                students.loc[students["student_number"] == student_number, "total_units_required"] = new_req
            save_students(students)
            st.success("Program updated.")
            st.rerun()
        st.markdown("**Special Status**")
        status_opts = ["Regular","Transferred","Shifted","On Leave","Inactive","Deleted"]
        cur_special = student.get("special_status", "Regular")
        new_special = st.selectbox("Status", status_opts, index=status_opts.index(cur_special) if cur_special in status_opts else 0)
        if st.button("Update Special Status"):
            students.loc[students["student_number"] == student_number, "special_status"] = new_special
            save_students(students)
            st.success("Status updated.")
            st.rerun()
        st.markdown("**Extend Residency (add 1 year)**")
        if st.button("Grant Extension"):
            students.loc[students["student_number"] == student_number, "residency_max_years"] = student["residency_max_years"] + 1
            save_students(students)
            st.success("Residency extended.")
            st.rerun()

def render_semester_block(student_number, semester_row, is_staff=False, can_edit=False):
    ay = str(semester_row["academic_year"])
    sem = str(semester_row["semester"])
    semester_status = str(semester_row.get("semester_status","Regular")).strip()
    try:
        subjects = json.loads(semester_row["subjects_json"]) if semester_row["subjects_json"] else []
    except:
        subjects = []
    total_units = float(semester_row["total_units"]) if pd.notna(semester_row["total_units"]) else 0.0
    gwa = float(semester_row["gwa"]) if pd.notna(semester_row["gwa"]) else 0.0
    doc_status = str(semester_row.get("doc_status","")).strip()
    doc_path = str(semester_row.get("doc_path","")).strip()
    doc_remarks = str(semester_row.get("doc_remarks","")).strip()
    
    with st.expander(f"📅 {ay} | {sem} (Units: {total_units:.0f} | GWA: {gwa:.2f})", expanded=False):
        # Status dropdown
        if is_staff and can_edit:
            new_status = st.selectbox("Semester Status", SEMESTER_STATUS_OPTIONS,
                                      index=SEMESTER_STATUS_OPTIONS.index(semester_status) if semester_status in SEMESTER_STATUS_OPTIONS else 0,
                                      key=f"status_{student_number}_{ay}_{sem}")
            if new_status != semester_status:
                df = load_semesters()
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
                    save_semesters(df)
                    update_student_academic_summary(student_number)
                    st.success("Status updated.")
                    st.rerun()
        else:
            st.markdown(f"**Semester Status:** {semester_status}")
        
        st.markdown(f"**Document Validation:** {get_status_badge(doc_status)}", unsafe_allow_html=True)
        if doc_status == "Rejected" and doc_remarks:
            st.warning(f"Rejection reason: {doc_remarks}")
        
        if semester_status == "Regular" and (not is_staff or (is_staff and can_edit)):
            # Editable subjects table
            df_edit = pd.DataFrame(subjects) if subjects else pd.DataFrame(columns=["course_code","course_description","units","grade"])
            for col in ["course_code","course_description","units","grade"]:
                if col not in df_edit.columns:
                    df_edit[col] = "" if col != "units" else 0
            df_edit = df_edit[["course_code","course_description","units","grade"]]
            df_edit["units"] = pd.to_numeric(df_edit["units"], errors="coerce").fillna(0).astype(int)
            edited_df = st.data_editor(
                df_edit,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "course_code": "Code",
                    "course_description": "Description",
                    "units": st.column_config.NumberColumn("Units", step=1, min_value=0),
                    "grade": st.column_config.SelectboxColumn("Grade", options=GRADE_OPTIONS, default="1.00"),
                },
                key=f"editor_{student_number}_{ay}_{sem}"
            )
            # Save button
            if st.button("💾 Save Subjects", key=f"save_{student_number}_{ay}_{sem}"):
                new_subjects = edited_df.to_dict("records")
                for s in new_subjects:
                    s["units"] = int(s["units"]) if s["units"] else 0
                    s["course_code"] = str(s.get("course_code",""))
                    s["course_description"] = str(s.get("course_description",""))
                    s["grade"] = str(s.get("grade","1.00"))
                if update_semester_subjects(student_number, ay, sem, new_subjects):
                    st.success("Subjects saved! Waiting for validation.")
                    st.rerun()
                else:
                    st.error("Save failed.")
            
            # Add row button
            if st.button("➕ Add Row", key=f"add_{student_number}_{ay}_{sem}"):
                new_row = pd.DataFrame([{"course_code":"","course_description":"","units":0,"grade":"1.00"}])
                new_edited = pd.concat([edited_df, new_row], ignore_index=True)
                st.session_state[f"temp_edit_{student_number}_{ay}_{sem}"] = new_edited
                st.rerun()
        elif semester_status != "Regular":
            st.info(f"Semester status **{semester_status}** – subject editing disabled.")
            if subjects:
                st.dataframe(pd.DataFrame(subjects), use_container_width=True, hide_index=True)
        else:
            st.info("Editing disabled in this view.")
        
        # Document upload (only if student or staff override? here we allow student only for simplicity)
        st.markdown("---")
        st.markdown("**Upload Proof of Grades (AMIS Screenshot)**")
        if semester_status == "Regular":
            if doc_path and doc_path != "nan" and os.path.exists(doc_path):
                st.info(f"Current file: {os.path.basename(doc_path)}")
            if not is_staff:
                with st.form(key=f"upload_{student_number}_{ay}_{sem}"):
                    uploaded = st.file_uploader("Choose file (PDF/JPG/PNG)", type=["pdf","jpg","jpeg","png"], key=f"upload_file_{ay}_{sem}")
                    if st.form_submit_button("📎 Upload Document") and uploaded:
                        folder = os.path.join(UPLOAD_FOLDER, student_number, "semester_docs")
                        os.makedirs(folder, exist_ok=True)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        ext = uploaded.name.split('.')[-1].lower()
                        filename = f"{ay}_{sem}_{timestamp}.{ext}"
                        filepath = os.path.join(folder, filename)
                        with open(filepath, "wb") as f:
                            f.write(uploaded.getbuffer())
                        if update_semester_document(student_number, ay, sem, filepath, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Pending"):
                            st.success("Document uploaded! Pending validation.")
                            st.rerun()
            else:
                if doc_path and doc_path != "nan" and os.path.exists(doc_path):
                    st.caption("Document uploaded by student.")
        else:
            st.info(f"Semester status **{semester_status}** – no upload required.")
        
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

def get_next_semester(academic_year, semester):
    sem_order = ["1st Sem","2nd Sem","Summer"]
    if semester not in sem_order:
        return None, None
    idx = sem_order.index(semester)
    if idx < 2:
        return academic_year, sem_order[idx+1]
    else:
        start = int(academic_year.split("-")[0])
        return f"{start+1}-{start+2}", "1st Sem"

def get_inc_alert(student_number):
    sems = load_semesters()
    sems = sems[sems["student_number"] == student_number]
    alerts = []
    for _, row in sems.iterrows():
        try:
            subjects = json.loads(row["subjects_json"]) if row["subjects_json"] else []
        except:
            continue
        sem_date = row.get("doc_upload_time", "")
        if sem_date and sem_date != "nan":
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

def register_new_student_form():
    with st.form("register_student_form"):
        st.subheader("Register New Student")
        col1, col2 = st.columns(2)
        with col1:
            s_num = st.text_input("Student Number *")
            lname = st.text_input("Last Name *")
            fname = st.text_input("First Name *")
            mname = st.text_input("Middle Name")
        with col2:
            prog = st.selectbox("Program *", PROGRAMS)
            ay_sel = st.selectbox("Admission Academic Year *", [f"{y}-{y+1}" for y in range(2020, 2027)])
            sem = st.selectbox("Starting Semester *", ["1st Sem","2nd Sem","Summer"])
            status_sel = st.selectbox("Student Status", ["Regular","Probationary","Conditional"])
        faculty_df = load_faculty()
        adv_opt = ["Not assigned"] + faculty_df["display_name"].tolist()
        advisor = st.selectbox("Adviser", adv_opt)
        prior_ms = False
        if prog == "PhD Environmental Science":
            prior_ms = st.checkbox("Student is an MS Environmental Science graduate")
        submitted = st.form_submit_button("Register Student")
        if submitted:
            errors = []
            if not s_num: errors.append("Student Number")
            if not lname: errors.append("Last Name")
            if not fname: errors.append("First Name")
            if not prog: errors.append("Program")
            students = load_students()
            if s_num in students["student_number"].values:
                errors.append("Student number already exists")
            if errors:
                st.error(f"Missing: {', '.join(errors)}")
            else:
                full_name = f"{lname}, {fname} {mname}".strip()
                new_row = create_demo_students().iloc[0].to_dict()
                req_units = get_required_units(prog, prior_ms)
                new_row.update({
                    "student_number": s_num,
                    "name": full_name,
                    "last_name": lname,
                    "first_name": fname,
                    "middle_name": mname,
                    "program": prog,
                    "advisor": advisor,
                    "ay_start": int(ay_sel.split("-")[0]),
                    "semester": sem,
                    "student_status": status_sel,
                    "prior_ms_graduate": prior_ms,
                    "total_units_required": req_units if req_units else 24,
                    "thesis_units_limit": get_thesis_limit_from_program(prog),
                    "residency_max_years": get_residency_max_from_program(prog),
                    "address": "", "phone": "", "emergency_contact": "",
                    "profile_pending_address": "", "profile_pending_phone": "", "profile_pending_emergency": "",
                    "profile_pending_status": "", "profile_pending_remarks": "",
                    "special_status": "Regular",
                    "external_reviewer": "",
                    "data_request_type": "", "data_request_details": "", "data_request_status": ""
                })
                students = pd.concat([students, pd.DataFrame([new_row])], ignore_index=True)
                save_students(students)
                get_student_milestones(s_num, get_program_type(prog))
                st.success(f"Student {full_name} registered successfully.")
                st.rerun()

# ==================== MAIN APP ====================
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center'>🎓 SESAM KMIS</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login", width="stretch"):
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

# Run grade conversion on every load
convert_expired_grades()

students = load_students()

with st.sidebar:
    st.markdown(f"<div style='text-align:center'><h3>👤 {st.session_state.display_name}</h3><div>{st.session_state.role}</div><div>✅ Consent given</div></div>", unsafe_allow_html=True)
    if st.button("🚪 Logout", width="stretch"):
        st.session_state.logged_in = False
        st.session_state.consent_given = False
        st.rerun()
    st.markdown("---")
    st.caption("Version 18.0 | Full UPLB Compliance")

st.title("🎓 SESAM Graduate Student Lifecycle Management")
st.caption("Fully compliant: Grade 4.0, auto‑INC conversion, residency enforcement, probation checks, data rights.")

role = st.session_state.role

if role == "SESAM Staff":
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Register New Student", width="stretch"):
            st.session_state.staff_show_update = False
            st.session_state.staff_selected_student = None
            st.session_state.show_registration = True
        else:
            if "show_registration" not in st.session_state:
                st.session_state.show_registration = False
    with col2:
        if st.button("✏️ Update Student Information", width="stretch"):
            st.session_state.show_registration = False
            st.session_state.staff_show_update = True
            st.session_state.staff_selected_student = None

    if st.session_state.get("show_registration", False):
        register_new_student_form()
    elif st.session_state.get("staff_show_update", False):
        if st.session_state.staff_selected_student is None:
            st.subheader("Select a student to update")
            search = st.text_input("Search by name or student number")
            filtered = filter_dataframe(search, students)
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
    advisees = students[students["advisor"] == st.session_state.display_name].copy()
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
    student = students[students["name"] == st.session_state.display_name].iloc[0].copy()
    program_type = get_program_type(student["program"])
    st.subheader(f"📘 Your Dashboard – {student['name']}")
    if student.get("profile_pending_status") == "Pending":
        st.warning("Your profile update is pending approval.")
    elif student.get("profile_pending_status") == "Rejected":
        st.error(f"Profile update rejected: {student.get('profile_pending_remarks','')}")
    status, used, max_y = check_residency_alert(student)
    if status == "exceeded":
        st.markdown(f'<div class="danger-banner">⚠️ RESIDENCY EXCEEDED! You have used {used} out of {max_y} years. Consult your adviser.</div>', unsafe_allow_html=True)
    elif status == "warning":
        st.markdown(f'<div class="warning-banner">⚠️ Residency warning: {used} out of {max_y} years used. Only one year remaining.</div>', unsafe_allow_html=True)
    inc_alerts = get_inc_alert(student["student_number"])
    for inc in inc_alerts:
        if inc["status"] == "expired":
            st.markdown(f'<div class="danger-banner">❌ INC/4.0 in {inc["course"]} ({inc["semester"]}) expired on {inc["deadline"]}. Converted to 5.00. Please retake.</div>', unsafe_allow_html=True)
        elif inc["status"] == "warning":
            st.markdown(f'<div class="warning-banner">⚠️ INC/4.0 in {inc["course"]} ({inc["semester"]}) deadline in {inc["days_left"]} days ({inc["deadline"]}).</div>', unsafe_allow_html=True)
    milestones = get_student_milestones(student["student_number"], program_type)
    next_milestone = None
    for _, m in milestones.iterrows():
        if m["status"] != "Completed":
            next_milestone = m["milestone"]
            break
    if next_milestone:
        st.info(f"🎯 Next milestone: {next_milestone}")
    else:
        st.success("All milestones completed!")
    tabs = st.tabs(["👤 My Profile", "📚 Coursework", "📌 Milestones", "📁 Uploads", "🔐 Data Rights"])
    with tabs[0]:
        col1, col2 = st.columns([1,2])
        with col1:
            pic = get_profile_picture_path(student["student_number"])
            if pic:
                st.image(pic, width=150)
            else:
                st.info("No profile picture")
            up = st.file_uploader("Upload picture", type=["jpg","jpeg","png"], key="student_pic")
            if up:
                fn = save_profile_picture(student["student_number"], up)
                if fn:
                    students.loc[students["student_number"] == student["student_number"], "profile_pic"] = fn
                    save_students(students)
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
            cur_addr = student.get("profile_pending_address") if student.get("profile_pending_status") == "Pending" else student.get("address","")
            cur_phone = student.get("profile_pending_phone") if student.get("profile_pending_status") == "Pending" else student.get("phone","")
            cur_emerg = student.get("profile_pending_emergency") if student.get("profile_pending_status") == "Pending" else student.get("emergency_contact","")
            new_addr = st.text_input("Address", value=cur_addr)
            new_phone = st.text_input("Phone", value=cur_phone)
            new_emerg = st.text_input("Emergency Contact", value=cur_emerg)
            if st.form_submit_button("Submit for Approval"):
                students = load_students()
                students.loc[students["student_number"] == student["student_number"], "profile_pending_address"] = new_addr
                students.loc[students["student_number"] == student["student_number"], "profile_pending_phone"] = new_phone
                students.loc[students["student_number"] == student["student_number"], "profile_pending_emergency"] = new_emerg
                students.loc[students["student_number"] == student["student_number"], "profile_pending_status"] = "Pending"
                save_students(students)
                st.success("Changes submitted. Waiting for approval.")
                st.rerun()
    with tabs[1]:
        st.subheader("Your Academic Record")
        total_years = 2 if is_master_program(student["program"]) else 3
        total_semesters_needed = total_years * 2 + (total_years - 1)
        start_ay = student["ay_start"] if pd.notna(student["ay_start"]) else 2024
        start_ay_str = f"{start_ay}-{start_ay+1}"
        start_sem = student["semester"]
        sem_order = ["1st Sem","2nd Sem","Summer"]
        all_sem = []
        for yr in range(total_years):
            ay = f"{start_ay+yr}-{start_ay+yr+1}"
            for sem in sem_order:
                all_sem.append((ay,sem))
        start_idx = 0
        for i, (ay,sem) in enumerate(all_sem):
            if ay == start_ay_str and sem == start_sem:
                start_idx = i
                break
        prospectus = all_sem[start_idx:start_idx+total_semesters_needed]
        existing = get_student_semesters(student["student_number"])
        for ay,sem in prospectus:
            if not ((existing["academic_year"] == ay) & (existing["semester"] == sem)).any():
                try:
                    add_semester_record(student["student_number"], ay, sem, [], semester_status="Regular")
                except ValueError as e:
                    st.error(str(e))
        semesters = get_student_semesters(student["student_number"])
        semesters = semesters.sort_values(["ay_num","order"]).reset_index(drop=True)
        for _, row in semesters.iterrows():
            render_semester_block(student["student_number"], row, is_staff=False, can_edit=False)
        if st.button("➕ Add Next Semester"):
            last = semesters.iloc[-1] if not semesters.empty else None
            if last:
                new_ay, new_sem = get_next_semester(last["academic_year"], last["semester"])
                if new_ay:
                    try:
                        add_semester_record(student["student_number"], new_ay, new_sem, [], semester_status="Regular")
                        st.success(f"Added {new_ay} {new_sem}")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Units Taken", student["total_units_taken"])
        col2.metric("Required", student["total_units_required"])
        col3.metric("Remaining", max(0, student["total_units_required"] - student["total_units_taken"]))
        col4.metric("Cumulative GWA", f"{student['gwa']:.2f}")
    with tabs[2]:
        st.subheader("Milestone Tracker")
        milestones = get_student_milestones(student["student_number"], program_type)
        for _, m in milestones.iterrows():
            with st.expander(f"{m['milestone']} – Status: {m['status']}"):
                st.write(f"Date: {m['date'] if m['date'] else 'Not set'}")
                if m['file_path'] and m['file_path'] != "nan" and os.path.exists(str(m['file_path'])):
                    with open(m['file_path'], "rb") as f:
                        st.download_button("Download proof", f, file_name=os.path.basename(m['file_path']))
                if m['status'] != "Completed":
                    allowed, reason = check_milestone_prerequisite(student["student_number"], program_type, m['milestone'], milestones)
                    if not allowed:
                        st.error(reason)
                    else:
                        uploaded = st.file_uploader("Upload proof", type=["pdf","jpg","png"], key=f"milestone_{m['milestone']}")
                        if st.button(f"Submit {m['milestone']}", key=f"submit_{m['milestone']}"):
                            if uploaded:
                                folder = os.path.join(UPLOAD_FOLDER, student["student_number"], "milestone_proofs")
                                os.makedirs(folder, exist_ok=True)
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                safe_name = m['milestone'].replace(" ", "_").replace("/","_")
                                ext = uploaded.name.split('.')[-1].lower()
                                filepath = os.path.join(folder, f"{safe_name}_{timestamp}.{ext}")
                                with open(filepath, "wb") as f:
                                    f.write(uploaded.getbuffer())
                                update_milestone(student["student_number"], m['milestone'], "Pending", datetime.now().strftime("%Y-%m-%d"), filepath, "")
                                st.success("Submitted for approval.")
                                st.rerun()
                            else:
                                st.error("Please upload a file.")
        if is_phd_program(student["program"]):
            rev = get_external_reviewer(student["student_number"])
            st.markdown("---")
            st.markdown("**External Reviewer (required for PhD Final Examination)**")
            if not rev:
                st.warning("No external reviewer assigned yet. Your adviser will assign one before your final defense.")
            else:
                st.success(f"External reviewer: {rev}")
    with tabs[3]:
        st.subheader("Upload Supporting Documents")
        categories = ["admission_letter", "amis_screenshot", "committee_form", "plan_of_study", "thesis_file"]
        category = st.selectbox("Document Type", categories)
        file = st.file_uploader("Choose file", type=["pdf","jpg","jpeg","png"])
        if st.button("Upload") and file:
            folder = os.path.join(UPLOAD_FOLDER, student["student_number"])
            os.makedirs(folder, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = file.name.split('.')[-1].lower()
            filename = f"{category}_{timestamp}.{ext}"
            filepath = os.path.join(folder, filename)
            with open(filepath, "wb") as f:
                f.write(file.getbuffer())
            up_df = load_uploads()
            new_up = pd.DataFrame([{
                "student_number": student["student_number"],
                "category": category,
                "file_path": filepath,
                "original_filename": file.name,
                "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "Pending",
                "reviewer_comment": "",
                "reviewed_by": "",
                "review_date": ""
            }])
            up_df = pd.concat([up_df, new_up], ignore_index=True)
            save_uploads(up_df)
            st.success("Uploaded. Waiting for validation.")
            st.rerun()
    with tabs[4]:
        st.subheader("Your Data Privacy Rights")
        st.markdown("Under the Data Privacy Act, you may request correction or deletion of your personal data.")
        req_type = st.selectbox("Request Type", ["Correction", "Deletion"])
        details = st.text_area("Details (for correction, specify which field and new value)")
        if st.button("Submit Request"):
            if details:
                df_req = load_data_requests()
                req_id = len(df_req) + 1 if not df_req.empty else 1
                new_req = pd.DataFrame([{
                    "request_id": req_id,
                    "student_number": student["student_number"],
                    "request_type": req_type,
                    "details": details,
                    "status": "Pending",
                    "submitted_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "reviewer_comment": "",
                    "reviewed_by": "",
                    "review_date": ""
                }])
                df_req = pd.concat([df_req, new_req], ignore_index=True)
                save_data_requests(df_req)
                st.success("Request submitted. Staff will review it.")
                st.rerun()
            else:
                st.error("Please provide details.")
        st.markdown("---")
        my_reqs = load_data_requests()
        my_reqs = my_reqs[my_reqs["student_number"] == student["student_number"]]
        if not my_reqs.empty:
            st.subheader("Your Previous Requests")
            for _, r in my_reqs.iterrows():
                st.write(f"**{r['request_type']}** – Status: {r['status']} – Submitted: {r['submitted_date']}")
                if r["status"] == "Rejected" and r["reviewer_comment"]:
                    st.warning(f"Rejection reason: {r['reviewer_comment']}")
    st.caption("For corrections, contact your adviser or SESAM Staff.")
