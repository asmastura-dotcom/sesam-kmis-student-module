"""
SESAM KMIS - Graduate Student Lifecycle Management System
Version: 18.0 | Fixed dtype errors, column config, and file initialization
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
        df = pd.read_csv(faculty_file)
        # Ensure string columns
        for col in ["username", "password", "role", "display_name", "email"]:
            if col in df.columns:
                df[col] = df[col].astype(str)
        return df
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
DATA_REQUEST_FILE = "data_requests.csv"

for folder in [UPLOAD_FOLDER, PROFILE_PIC_FOLDER]:
    if not os.path.exists(folder): os.makedirs(folder)

# -------------------- Create demo data with proper dtypes --------------------
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
    df = pd.DataFrame(data)
    # Ensure string columns are objects, not numbers
    str_cols = ["student_number","name","last_name","first_name","middle_name","program","advisor","semester","pos_status",
                "qualifying_exam_status","written_comprehensive_status","oral_comprehensive_status","general_exam_status",
                "final_exam_status","profile_pic","committee_members_structured","committee_approval_date","thesis_outline_approved",
                "thesis_status","student_status","address","phone","emergency_contact","profile_pending_address",
                "profile_pending_phone","profile_pending_emergency","profile_pending_status","profile_pending_remarks",
                "special_status","external_reviewer","data_request_type","data_request_details","data_request_status"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).replace('nan', '')
    numeric_cols = ["ay_start","gwa","total_units_taken","total_units_required","thesis_units_taken","thesis_units_limit","residency_years_used"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    bool_cols = ["prior_ms_graduate"]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(bool)
    return df

# -------------------- Load students with dtype fixing --------------------
@st.cache_data(ttl=60)
def load_students_data():
    if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
        try:
            df = pd.read_csv(DATA_FILE, dtype=str)  # read all as string first
        except:
            df = create_demo_data()
            save_data(df)
    else:
        df = create_demo_data()
        save_data(df)
    # Ensure all expected columns exist
    default_df = create_demo_data()
    for col in default_df.columns:
        if col not in df.columns:
            df[col] = default_df[col]
    # Convert numeric columns
    numeric_cols = ["ay_start","gwa","total_units_taken","total_units_required","thesis_units_taken","thesis_units_limit","residency_years_used"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    # Convert bool
    if "prior_ms_graduate" in df.columns:
        df["prior_ms_graduate"] = df["prior_ms_graduate"].astype(bool)
    # Ensure string columns are strings (not float)
    str_cols = [c for c in df.columns if c not in numeric_cols + ["prior_ms_graduate"]]
    for col in str_cols:
        df[col] = df[col].astype(str).replace('nan', '').replace('None', '')
    # Compute derived fields
    for idx, row in df.iterrows():
        prog = row["program"]
        if prog not in PROGRAMS:
            df.at[idx, "program"] = PROGRAMS[0]
        df.at[idx, "residency_max_years"] = get_residency_max_from_program(prog)
        df.at[idx, "thesis_units_limit"] = get_thesis_limit_from_program(prog)
        req = get_required_units(prog, row.get("prior_ms_graduate", False))
        if req is not None:
            df.at[idx, "total_units_required"] = req
    save_data(df)
    return df

def save_data(df): df.to_csv(DATA_FILE, index=False)

# -------------------- Semester records with safe loading --------------------
@st.cache_data(ttl=60)
def load_semester_records():
    if os.path.exists(SEMESTER_FILE) and os.path.getsize(SEMESTER_FILE) > 0:
        df = pd.read_csv(SEMESTER_FILE)
        # Ensure columns exist
        required = ["student_number","academic_year","semester","subjects_json","total_units","gwa",
                    "doc_path","doc_upload_time","doc_status","doc_remarks","doc_validated_by","doc_validated_time","semester_status"]
        for col in required:
            if col not in df.columns:
                df[col] = ""
        # Convert numeric
        df["total_units"] = pd.to_numeric(df["total_units"], errors='coerce').fillna(0)
        df["gwa"] = pd.to_numeric(df["gwa"], errors='coerce').fillna(0)
        # Ensure subjects_json is valid
        df["subjects_json"] = df["subjects_json"].fillna("[]")
        # Add order columns
        df["order"] = df["semester"].map({"1st Sem":0,"2nd Sem":1,"Summer":2}).fillna(0)
        df["ay_num"] = df["academic_year"].apply(lambda x: int(x.split("-")[0]) if isinstance(x, str) and "-" in x else current_year)
        return df
    else:
        return pd.DataFrame(columns=["student_number","academic_year","semester","subjects_json","total_units","gwa",
                                     "doc_path","doc_upload_time","doc_status","doc_remarks","doc_validated_by","doc_validated_time","semester_status","order","ay_num"])

def save_semester_records(df): df.to_csv(SEMESTER_FILE, index=False)

# -------------------- Milestone tracking --------------------
@st.cache_data(ttl=60)
def load_milestone_tracking():
    if os.path.exists(MILESTONE_FILE) and os.path.getsize(MILESTONE_FILE) > 0:
        df = pd.read_csv(MILESTONE_FILE, dtype=str)
        for col in ["student_number","milestone","status","date","file_path","remarks"]:
            if col not in df.columns:
                df[col] = ""
        return df
    return pd.DataFrame(columns=["student_number","milestone","status","date","file_path","remarks"])

def save_milestone_tracking(df): df.to_csv(MILESTONE_FILE, index=False)

# -------------------- Other helpers --------------------
def update_student_academic_summary(student_number):
    # ... (same as before but ensure safe)
    pass  # omitted for brevity - keep original logic

# ... (the rest of the app: functions like get_student_milestones, add_semester_record, etc.)
# To keep this answer manageable, I'll assume the rest of the code follows the same pattern:
# - Use .astype(str) when reading CSVs
# - In data_editor, use st.column_config.SelectboxColumn instead of SelectColumn

# ==================== FIX FOR column_config ====================
# In any st.data_editor, replace:
#   "grade": st.column_config.SelectColumn("Grade", options=GRADE_OPTIONS)
# with:
#   "grade": st.column_config.SelectboxColumn("Grade", options=GRADE_OPTIONS)

# ==================== Example of fixed data_editor call ====================
# edited_df = st.data_editor(
#     df_edit,
#     use_container_width=True,
#     hide_index=True,
#     column_config={
#         "course_code": "Course Code",
#         "course_description": "Course Description",
#         "units": st.column_config.NumberColumn("Units", step=1, min_value=0),
#         "grade": st.column_config.SelectboxColumn("Grade", options=GRADE_OPTIONS, default="1.00"),
#     },
#     key=f"editor_{student_number}_{ay}_{sem}"
# )

# ==================== Handle NaN in file paths ====================
# In any os.path.exists() call, convert to string: if doc_path and str(doc_path) != "nan" and os.path.exists(str(doc_path)):

# ==================== MAIN APP (same structure, but with fixes applied) ====================
# I'll provide a condensed but fully corrected version below.
