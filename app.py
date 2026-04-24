"""
SESAM KMIS - Student Module V2 (Graduate School Rules Integration)
Enhanced with Degree Audit & Basic Reporting for Capstone
Author: SESAM Dev Team
Date: 2026-04-24
Description: Graduate student milestone tracker with automated degree audit, reporting, and what-if simulation.
Based on UPLB Graduate School Policies, Rules and Regulations (2009).
"""

import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
from PIL import Image
import io
import json

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="SESAM Graduate Student Tracker",
    page_icon="🎓",
    layout="wide"
)

# ==================== INITIALIZE SESSION STATE ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None
if "display_name" not in st.session_state:
    st.session_state.display_name = None
if "student_number" not in st.session_state:
    st.session_state.student_number = None

# ==================== USER AUTH (with student numbers) ====================
USERS = {
    "staff1": {"password": "admin123", "role": "SESAM Staff", "display_name": "SESAM Administrator", "student_number": None},
    "adviser1": {"password": "adv123", "role": "Faculty Adviser", "display_name": "Dr. Eslava", "student_number": None},
    "adviser2": {"password": "adv456", "role": "Faculty Adviser", "display_name": "Dr. Sanchez", "student_number": None},
    "student1": {"password": "stu123", "role": "Student", "display_name": "Cruz, Juan M.", "student_number": "S001"},
    "student2": {"password": "stu456", "role": "Student", "display_name": "Santos, Maria L.", "student_number": "S002"}
}

# ==================== PROGRAM DEFINITIONS ====================
PROGRAMS = [
    "MS Environmental Science",
    "PhD Environmental Science",
    "PhD Environmental Diplomacy and Negotiations",
    "Master in Resilience Studies (M-ReS)",
    "Professional Masters in Tropical Marine Ecosystems Management (PM-TMEM)"
]

PhD_TRACKS = ["MS EnvSci graduate", "non-MS EnvSci graduate"]
SEMESTERS = ["1st Sem", "2nd Sem", "Summer"]

current_year = date.today().year
ACADEMIC_YEARS = [f"{year}-{year+1}" for year in range(current_year-5, current_year+6)]

def is_master_program(program):
    return program.startswith("MS") or program.startswith("Master") or program.startswith("Professional Masters")

def is_phd_program(program):
    return program.startswith("PhD")

def get_thesis_limit_from_program(program):
    return 6 if is_master_program(program) else 12

def get_residency_max_from_program(program):
    return 5 if is_master_program(program) else 7

def get_required_units(program, phd_track=None):
    if program == "MS Environmental Science":
        return 32
    elif program == "PhD Environmental Science":
        if phd_track == "MS EnvSci graduate":
            return 37
        else:
            return 50
    else:
        if is_master_program(program):
            return 36
        else:
            return 48

def format_ay(ay_start, semester):
    return f"A.Y. {ay_start}-{ay_start+1} ({semester})"

def get_thesis_pattern_description(program):
    if is_master_program(program):
        return "💡 MS students: thesis units (6 total) can be taken as 2-2-2 (three terms) or 3-3 (two terms)."
    else:
        return "💡 PhD students: dissertation units (12 total) can be taken as 3-3-3-3 (four terms) or 4-4-4 (three terms)."

def compute_coursework_progress(row):
    taken = row.get("total_units_taken", 0)
    required = row.get("total_units_required", 24)
    if required <= 0:
        return 0
    return min(100, int((taken / required) * 100))

def check_deadline_alerts(row):
    alerts = []
    program = row["program"]
    thesis_units = row["thesis_units_taken"]
    outline_approved = row["thesis_outline_approved"]
    pos_status = row["pos_status"]
    residency_used = row.get("residency_years_used", 0)
    
    if program.startswith("MS") and residency_used >= 1 and pos_status not in ["Approved", "Completed"]:
        alerts.append("⚠️ Plan of Study (POS) should be approved by 2nd semester of residence.")
    elif program.startswith("PhD") and row.get("qualifying_exam_status") == "Passed" and pos_status != "Approved":
        alerts.append("⚠️ Plan of Study (POS) pending approval after qualifying exam.")
    
    if program.startswith("MS") and thesis_units >= 4 and outline_approved != "Yes":
        alerts.append("⚠️ Thesis outline approval overdue (must be approved by 2nd thesis semester).")
    if program.startswith("PhD") and thesis_units >= 8 and outline_approved != "Yes":
        alerts.append("⚠️ Dissertation outline approval overdue (must be approved by 3rd dissertation semester).")
    
    if program.startswith("PhD") and residency_used >= 1 and row["qualifying_exam_status"] not in ["Passed", "N/A"]:
        alerts.append("⚠️ Qualifying exam should be taken before 2nd semester of residence.")
    
    if program.startswith("PhD") and row["total_units_taken"] >= row["total_units_required"] and row["written_comprehensive_status"] != "Passed":
        alerts.append("⚠️ Written comprehensive exam pending after completing all coursework.")
    
    return alerts

# ==================== DEGREE AUDIT FUNCTION ====================
def compute_degree_audit(student):
    """Returns a list of (requirement, status, details) for automated degree audit."""
    audit = []
    program = student["program"]
    units_taken = int(student["total_units_taken"])
    units_required = int(student["total_units_required"])
    thesis_taken = int(student["thesis_units_taken"])
    thesis_limit = int(student["thesis_units_limit"])
    residency_used = int(student["residency_years_used"])
    residency_max = int(student["residency_max_years"])
    pos_status = student["pos_status"]
    
    # 1. Total coursework units
    if units_taken >= units_required:
        audit.append(("✅ Total Coursework Units", f"{units_taken}/{units_required} – Completed", "passed"))
    else:
        audit.append(("⚠️ Total Coursework Units", f"{units_taken}/{units_required} – {units_required - units_taken} units remaining", "pending"))
    
    # 2. Thesis/Dissertation units
    if thesis_taken >= thesis_limit:
        audit.append(("✅ Thesis/Dissertation Units", f"{thesis_taken}/{thesis_limit} – Completed", "passed"))
    else:
        audit.append(("⚠️ Thesis/Dissertation Units", f"{thesis_taken}/{thesis_limit} – {thesis_limit - thesis_taken} units remaining", "pending"))
    
    # 3. Residency
    if residency_used >= residency_max:
        audit.append(("❌ Residency", f"{residency_used}/{residency_max} years – Exceeded limit", "failed"))
    elif residency_used >= residency_max - 1:
        audit.append(("⚠️ Residency", f"{residency_used}/{residency_max} years – Approaching limit", "pending"))
    else:
        audit.append(("✅ Residency", f"{residency_used}/{residency_max} years – Within limit", "passed"))
    
    # 4. POS approval
    if pos_status == "Approved":
        audit.append(("✅ Plan of Study (POS)", "Approved", "passed"))
    else:
        audit.append(("⚠️ Plan of Study (POS)", f"Status: {pos_status} – Not yet approved", "pending"))
    
    # 5. Exams (depends on program)
    if is_phd_program(program):
        qual = student["qualifying_exam_status"]
        written = student["written_comprehensive_status"]
        oral = student["oral_comprehensive_status"]
        if qual == "Passed":
            audit.append(("✅ Qualifying Exam", "Passed", "passed"))
        else:
            audit.append(("⚠️ Qualifying Exam", qual, "pending"))
        if written == "Passed":
            audit.append(("✅ Written Comprehensive", "Passed", "passed"))
        else:
            audit.append(("⚠️ Written Comprehensive", written, "pending"))
        if oral == "Passed":
            audit.append(("✅ Oral Comprehensive", "Passed", "passed"))
        else:
            audit.append(("⚠️ Oral Comprehensive", oral, "pending"))
    else:
        gen = student["general_exam_status"]
        if gen == "Passed":
            audit.append(("✅ General Exam (MS)", "Passed", "passed"))
        else:
            audit.append(("⚠️ General Exam (MS)", gen, "pending"))
    
    # 6. Final exam
    final = student["final_exam_status"]
    if final == "Passed":
        audit.append(("✅ Final Exam", "Passed", "passed"))
    else:
        audit.append(("⚠️ Final Exam", final, "pending"))
    
    # 7. Graduation application
    grad_app = student["graduation_applied"]
    grad_approved = student["graduation_approved"]
    if grad_app == "Yes" and grad_approved == "Yes":
        audit.append(("✅ Graduation", "Approved", "passed"))
    elif grad_app == "Yes":
        audit.append(("⏳ Graduation", "Applied – Pending approval", "pending"))
    else:
        audit.append(("ℹ️ Graduation", "Not yet applied", "pending"))
    
    return audit

# ==================== IMAGE COMPRESSION AND STORAGE ====================
PROFILE_FOLDER = "profile_pics"
AMIS_FOLDER = "amis_screenshots"
for folder in [PROFILE_FOLDER, AMIS_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def compress_image(file, max_size_kb=200, output_width=500):
    """Compress uploaded image to max_size_kb and resize width."""
    img = Image.open(file)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    ratio = output_width / float(img.size[0])
    output_height = int(float(img.size[1]) * ratio)
    img = img.resize((output_width, output_height), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    quality = 85
    while True:
        buffer.seek(0)
        buffer.truncate()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        if buffer.tell() <= max_size_kb * 1024 or quality <= 10:
            break
        quality -= 5
    return buffer.getvalue()

def save_profile_picture(student_number, uploaded_file):
    if uploaded_file is None:
        return None
    try:
        compressed = compress_image(uploaded_file, max_size_kb=150, output_width=300)
        filename = f"{student_number}.jpg"
        filepath = os.path.join(PROFILE_FOLDER, filename)
        with open(filepath, "wb") as f:
            f.write(compressed)
        return filename
    except Exception as e:
        st.error(f"Profile picture compression failed: {e}")
        return None

def delete_profile_picture(student_number):
    for f in os.listdir(PROFILE_FOLDER):
        if f.startswith(str(student_number) + "."):
            os.remove(os.path.join(PROFILE_FOLDER, f))
            return True
    return False

def get_profile_picture_path(student_number):
    for f in os.listdir(PROFILE_FOLDER):
        if f.startswith(str(student_number) + "."):
            return os.path.join(PROFILE_FOLDER, f)
    return None

def save_amis_screenshot(student_number, uploaded_file):
    if uploaded_file is None:
        return None
    try:
        compressed = compress_image(uploaded_file, max_size_kb=200, output_width=600)
        filename = f"{student_number}.jpg"
        filepath = os.path.join(AMIS_FOLDER, filename)
        with open(filepath, "wb") as f:
            f.write(compressed)
        return filename
    except Exception as e:
        st.error(f"AMIS image compression failed: {e}")
        return None

def delete_amis_screenshot(student_number):
    for f in os.listdir(AMIS_FOLDER):
        if f.startswith(str(student_number) + "."):
            os.remove(os.path.join(AMIS_FOLDER, f))
            return True
    return False

def get_amis_screenshot_path(student_number):
    for f in os.listdir(AMIS_FOLDER):
        if f.startswith(str(student_number) + "."):
            return os.path.join(AMIS_FOLDER, f)
    return None

# ==================== NOTIFICATION FUNCTIONS ====================
def get_notifications(student_row):
    """Return list of notifications from student row (JSON column)."""
    notif_str = student_row.get("notifications", "[]")
    try:
        return json.loads(notif_str)
    except:
        return []

def add_notification(df, student_number, adviser_name, message, notif_type="General"):
    """Append a new notification to the student's record."""
    idx = df[df["student_number"] == student_number].index
    if len(idx) == 0:
        return df
    current_list = []
    try:
        current_list = json.loads(df.at[idx[0], "notifications"])
    except:
        pass
    new_notif = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "from": adviser_name,
        "message": message,
        "type": notif_type,
        "read": False
    }
    current_list.append(new_notif)
    df.at[idx[0], "notifications"] = json.dumps(current_list)
    return df

def dismiss_notification(df, student_number, notif_index):
    """Remove a notification by index."""
    idx = df[df["student_number"] == student_number].index
    if len(idx) == 0:
        return df
    notif_list = get_notifications(df.loc[idx[0]])
    if 0 <= notif_index < len(notif_list):
        notif_list.pop(notif_index)
        df.at[idx[0], "notifications"] = json.dumps(notif_list)
    return df

# ==================== LOGIN PAGE ====================
if not st.session_state.logged_in:
    st.title("🔐 SESAM KMIS Login")
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
    with col2:
        st.caption("Demo accounts:")
        st.caption("staff1 / admin123")
        st.caption("adviser1 / adv123")
        st.caption("student1 / stu123")

    if st.button("Login"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = USERS[username]["role"]
            st.session_state.display_name = USERS[username]["display_name"]
            st.session_state.student_number = USERS[username]["student_number"]
            st.success("✅ Login successful")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")
    st.stop()

# ==================== DATA LOADING WITH MIGRATION ====================
DATA_FILE = "students.csv"

def create_default_data():
    return pd.DataFrame({
        "student_number": ["S001", "S002", "S003", "S004", "S005"],
        "name": ["Cruz, Juan M.", "Santos, Maria L.", "Rizal, Jose P.", "Reyes, Ana C.", "Lopez, Carlos R."],
        "last_name": ["Cruz", "Santos", "Rizal", "Reyes", "Lopez"],
        "first_name": ["Juan", "Maria", "Jose", "Ana", "Carlos"],
        "middle_name": ["M.", "L.", "P.", "C.", "R."],
        "program": [PROGRAMS[0], PROGRAMS[1], PROGRAMS[0], PROGRAMS[1], PROGRAMS[0]],
        "phd_track": ["", "MS EnvSci graduate", "", "non-MS EnvSci graduate", ""],
        "advisor": ["Dr. Eslava", "Dr. Sanchez", "Dr. Eslava", "Dr. Sanchez", "Dr. Eslava"],
        "ay_start": [2024, 2023, 2024, 2022, 2024],
        "semester": ["1st Sem", "1st Sem", "2nd Sem", "1st Sem", "1st Sem"],
        "profile_pic": ["", "", "", "", ""],
        "amis_screenshot": ["", "", "", "", ""],
        "notifications": ["[]", "[]", "[]", "[]", "[]"],
        "committee_members": ["Dr. Eslava, Dr. Sanchez", "Dr. Sanchez, Dr. Eslava", "Dr. Eslava", "Dr. Sanchez, Dr. Eslava", "Dr. Eslava"],
        "committee_approval_date": ["2024-02-01", "2023-07-01", "", "2022-09-15", ""],
        "pos_status": ["Approved", "Approved", "Pending", "Approved", "Pending"],
        "pos_submitted_date": ["2024-01-15", "2023-06-10", "", "2022-09-01", ""],
        "pos_approved_date": ["2024-02-01", "2023-07-01", "", "2022-09-15", ""],
        "gwa": [1.75, 1.85, 2.10, 1.95, 2.05],
        "total_units_taken": [12, 18, 9, 24, 6],
        "total_units_required": [32, 37, 32, 50, 32],
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
    
    # ---- COLUMN MIGRATION ----
    if "advisor_username" in df.columns and "advisor" not in df.columns:
        df.rename(columns={"advisor_username": "advisor"}, inplace=True)
    if "year_admitted" in df.columns and "ay_start" not in df.columns:
        df["ay_start"] = df["year_admitted"]
        df["semester"] = "1st Sem"
        df.drop(columns=["year_admitted"], inplace=True)
    
    default_df = create_default_data()
    for col in default_df.columns:
        if col not in df.columns:
            df[col] = default_df[col]
    
    if "notifications" not in df.columns:
        df["notifications"] = "[]"
    for idx in df.index:
        val = df.at[idx, "notifications"]
        if pd.isna(val) or not isinstance(val, str) or (val.strip() == ""):
            df.at[idx, "notifications"] = "[]"
        else:
            try:
                json.loads(val)
            except:
                df.at[idx, "notifications"] = "[]"
    
    if "last_name" not in df.columns:
        df["last_name"] = ""
    if "first_name" not in df.columns:
        df["first_name"] = ""
    if "middle_name" not in df.columns:
        df["middle_name"] = ""
    
    def build_name(row):
        last = str(row.get("last_name", "")).strip()
        first = str(row.get("first_name", "")).strip()
        middle = str(row.get("middle_name", "")).strip()
        if last and first:
            middle_part = f" {middle}" if middle else ""
            return f"{last}, {first}{middle_part}"
        return row.get("name", "")
    
    df["name"] = df.apply(build_name, axis=1)
    
    df = df[df["student_number"].notna() & (df["student_number"].astype(str).str.strip() != "")]
    df = df[df["student_number"] != "None"]
    
    numeric_int_cols = [
        "thesis_units_taken", "thesis_units_limit",
        "total_units_taken", "total_units_required",
        "residency_years_used", "residency_max_years",
        "extension_count", "loa_total_terms", "transfer_units_approved",
        "ay_start"
    ]
    for col in numeric_int_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    
    df["gwa"] = pd.to_numeric(df["gwa"], errors='coerce').fillna(2.0).astype(float)
    
    string_cols = ["profile_pic", "amis_screenshot", "committee_members", "committee_approval_date", "phd_track",
                   "advisor", "pos_status", "thesis_outline_approved", "thesis_status",
                   "qualifying_exam_status", "written_comprehensive_status", "oral_comprehensive_status",
                   "general_exam_status", "final_exam_status", "awol_status", "semester",
                   "graduation_applied", "graduation_approved", "re_admission_status",
                   "extension_end_date", "loa_start_date", "loa_end_date", "awol_lifted_date",
                   "graduation_date", "re_admission_date", "pos_submitted_date", "pos_approved_date",
                   "qualifying_exam_passed_date", "written_comprehensive_passed_date",
                   "oral_comprehensive_passed_date", "general_exam_passed_date", "final_exam_passed_date"]
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).replace("nan", "").fillna("")
    
    for idx, row in df.iterrows():
        program = str(row["program"]).strip()
        if program not in PROGRAMS:
            if program == "MS":
                program = PROGRAMS[0]
            elif program == "PhD":
                program = PROGRAMS[1]
            else:
                program = PROGRAMS[0]
            df.at[idx, "program"] = program
        
        if program in ["PhD Environmental Science", "PhD Environmental Diplomacy and Negotiations"]:
            track = row.get("phd_track", "")
            if track not in PhD_TRACKS:
                track = "MS EnvSci graduate"
            req = get_required_units(program, track)
        else:
            req = get_required_units(program)
        df.at[idx, "total_units_required"] = req
        df.at[idx, "residency_max_years"] = get_residency_max_from_program(program)
        df.at[idx, "thesis_units_limit"] = get_thesis_limit_from_program(program)
        
        if row["ay_start"] >= 2025:
            df.at[idx, "total_units_taken"] = 0
            df.at[idx, "written_comprehensive_status"] = "N/A"
            df.at[idx, "oral_comprehensive_status"] = "N/A"
            df.at[idx, "qualifying_exam_status"] = "N/A"
            df.at[idx, "general_exam_status"] = "N/A"
            df.at[idx, "final_exam_status"] = "Not Taken"
    
    df.to_csv(DATA_FILE, index=False)
    return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def get_thesis_limit(program):
    return get_thesis_limit_from_program(program)

def get_residency_max(program):
    return get_residency_max_from_program(program)

# ==================== WARNING FUNCTIONS (existing) ====================
def get_warning_text(program, units_taken):
    limit = get_thesis_limit(program)
    try:
        units_taken = float(units_taken)
        limit = float(limit)
    except:
        return "⚠️ Thesis units data error"
    if units_taken > limit:
        return f"⚠️ Thesis units exceeded: {units_taken}/{limit} (exceeded by {units_taken - limit})"
    return f"✅ Thesis units: {units_taken}/{limit}"

def check_residency_warning(row):
    used = row.get("residency_years_used", 0)
    program = str(row.get("program", PROGRAMS[0])).strip()
    try:
        used = float(used)
    except:
        return "⚠️ Residency data error"
    max_years = get_residency_max(program)
    if used >= max_years:
        return f"⚠️ Residency limit reached ({used}/{max_years} years). Extension required."
    elif used >= max_years - 1:
        return f"⚠️ Approaching residency limit ({used}/{max_years} years)."
    return f"✅ Residency: {used}/{max_years} years used"

def check_gwa_warning(gwa):
    try:
        gwa = float(gwa)
    except:
        return "⚠️ GWA data error"
    if gwa > 2.00:
        return f"⚠️ GWA {gwa:.2f} is below 2.00 – may affect exam eligibility and graduation"
    return f"✅ GWA {gwa:.2f} – good standing"

def check_awol_warning(row):
    status = str(row.get("awol_status", "No")).strip()
    if status == "Yes":
        return "⚠️ AWOL – registration privileges curtailed"
    return "✅ No AWOL"

def check_loa_warning(row):
    total_terms = row.get("loa_total_terms", 0)
    try:
        total_terms = float(total_terms)
    except:
        return "⚠️ LOA data error"
    if total_terms > 2:
        return f"⚠️ LOA total exceeds 2 years ({total_terms} terms). Not allowed."
    elif total_terms > 0:
        return f"ℹ️ LOA total: {total_terms} term(s)"
    return "✅ No LOA"

def check_thesis_outline_deadline(row):
    program = str(row.get("program", PROGRAMS[0]))
    units_taken = row.get("thesis_units_taken", 0)
    outline_approved = str(row.get("thesis_outline_approved", "No")).strip()
    try:
        units_taken = float(units_taken)
    except:
        return "⚠️ Thesis units data error"
    if is_master_program(program) and units_taken > 0:
        if units_taken >= 4 and outline_approved != "Yes":
            return "⚠️ Thesis outline approval overdue (should be approved by 2nd thesis semester)"
    elif is_phd_program(program) and units_taken > 0:
        if units_taken >= 8 and outline_approved != "Yes":
            return "⚠️ Dissertation outline approval overdue (should be approved by 3rd dissertation semester)"
    return "✅ Outline on track"

def check_qualifying_exam_deadline(row):
    program = str(row.get("program", PROGRAMS[0]))
    residency_used = row.get("residency_years_used", 0)
    exam_status = str(row.get("qualifying_exam_status", "N/A")).strip()
    try:
        residency_used = float(residency_used)
    except:
        return "⚠️ Residency data error"
    if is_phd_program(program) and residency_used >= 1:
        if exam_status not in ["Passed", "N/A"]:
            return "⚠️ Qualifying exam should be taken before 2nd semester of residence"
    return "✅ Qualifying exam on track"

def check_comprehensive_exam_deadline(row):
    program = str(row.get("program", PROGRAMS[0]))
    total_taken = row.get("total_units_taken", 0)
    total_required = row.get("total_units_required", 24)
    written_status = str(row.get("written_comprehensive_status", "N/A")).strip()
    ay_start = row.get("ay_start", 2026)
    try:
        total_taken = float(total_taken)
        total_required = float(total_required)
    except:
        return "⚠️ Units data error"
    if is_phd_program(program) and total_taken >= total_required and ay_start <= 2023:
        if written_status != "Passed":
            return "⚠️ Written comprehensive exam pending after completing coursework"
    return "✅ Comprehensive exam on track"

def get_all_warnings(row):
    warnings = []
    thesis_warn = get_warning_text(row["program"], row["thesis_units_taken"])
    if "⚠️" in thesis_warn:
        warnings.append(thesis_warn)
    res_warn = check_residency_warning(row)
    if "⚠️" in res_warn:
        warnings.append(res_warn)
    gwa_warn = check_gwa_warning(row["gwa"])
    if "⚠️" in gwa_warn:
        warnings.append(gwa_warn)
    awol_warn = check_awol_warning(row)
    if "⚠️" in awol_warn:
        warnings.append(awol_warn)
    loa_warn = check_loa_warning(row)
    if "⚠️" in loa_warn:
        warnings.append(loa_warn)
    outline_warn = check_thesis_outline_deadline(row)
    if "⚠️" in outline_warn:
        warnings.append(outline_warn)
    qual_warn = check_qualifying_exam_deadline(row)
    if "⚠️" in qual_warn:
        warnings.append(qual_warn)
    comp_warn = check_comprehensive_exam_deadline(row)
    if "⚠️" in comp_warn:
        warnings.append(comp_warn)
    if not warnings:
        return ["✅ All rules satisfied"]
    return warnings

# Load data
df = load_data()

# ==================== SIDEBAR ====================
st.sidebar.title("🎓 KMIS Student Module")
st.sidebar.markdown("---")
st.sidebar.write(f"👤 {st.session_state.display_name}")
st.sidebar.write(f"🔑 {st.session_state.role}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.display_name = None
    st.session_state.student_number = None
    st.rerun()
st.sidebar.markdown("---")
st.sidebar.caption("Version 2.0 | ISSP 2026-2031 | Graduate School Rules")

st.title("🎓 SESAM Graduate Student Milestone Tracker")
st.markdown("*Centralized tracking for graduate students based on UPLB Graduate School Policies*")
st.markdown("---")

role = st.session_state.role

def safe_index(options, value):
    try:
        return options.index(value)
    except ValueError:
        return 0

def filter_dataframe(search_term, data):
    if not search_term:
        return data
    mask = (
        data["name"].str.contains(search_term, case=False, na=False) |
        data["student_number"].str.contains(search_term, case=False, na=False)
    )
    return data[mask]

# ==================== STAFF VIEW ====================
if role == "SESAM Staff":
    st.subheader("📋 All Students")
    search = st.text_input("🔍 Search by name or student number", placeholder="e.g., Cruz or S001")
    filtered_df = filter_dataframe(search, df)
    filtered_df["academic_year"] = filtered_df.apply(lambda row: format_ay(row["ay_start"], row["semester"]), axis=1)
    display_cols = ["student_number", "name", "program", "academic_year", "advisor", "gwa", "thesis_units_taken", "thesis_units_limit", "pos_status", "final_exam_status"]
    st.dataframe(filtered_df[display_cols], width='stretch', height=400)
    
    # --- EXPORT REPORT BUTTON ---
    st.markdown("---")
    st.subheader("📄 Generate Report")
    if st.button("Export Current Student List to CSV"):
        export_df = filtered_df[display_cols].copy()
        csv = export_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"sesam_students_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    
    st.markdown("---")
    st.subheader("✏️ Update Student Record")

    if len(filtered_df) > 0:
        st.subheader("🔍 Search Student to Edit")
        edit_search = st.text_input("Type name or student number", value="", placeholder="e.g., Cruz or S001", key="edit_search")
        if edit_search:
            edit_filtered = filter_dataframe(edit_search, filtered_df)
            edit_filtered_names = edit_filtered["name"].tolist()
        else:
            edit_filtered_names = filtered_df["name"].tolist()
        
        if not edit_filtered_names:
            st.warning("No matching students found.")
            st.stop()
        
        student_name = st.selectbox("Select Student", edit_filtered_names)
        student = df[df["name"] == student_name].iloc[0].copy()
        student_number = student["student_number"]

        # ----- PROFILE PICTURE at upper right (view only) -----
        st.markdown("---")
        col_left, col_right = st.columns([3, 1])
        with col_right:
            pic_path = get_profile_picture_path(student_number)
            if pic_path and os.path.exists(pic_path):
                st.image(pic_path, width=100, caption="Profile Picture")
            else:
                st.info("No profile picture")
        with col_left:
            st.markdown("### Student Information")
            col1, col2, col3 = st.columns(3)
