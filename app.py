"""
SESAM KMIS - Student Module V2 (Graduate School Rules Integration)
Enhanced with Faculty-to-Student Notification System & Adviser Monitoring Dashboard
Author: SESAM Dev Team
Date: 2026-04-24
Description: Tracks graduate student milestones, thesis units, exams, residency, LOA/AWOL, etc.
Students upload profile picture and AMIS screenshot (with manual GWA entry).
Staff & faculty can only view uploaded images.
Faculty advisers can send notifications to students; students see them in real time.
Enhanced with early warning indicators, at-risk dashboards, and visual analytics.
Based on UPLB Graduate School Policies, Rules and Regulations (2009).
"""

import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
from PIL import Image
import io
import json
import plotly.express as px
import plotly.graph_objects as go

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
        alerts.append("📌 Plan of Study (POS) should be approved by 2nd semester of residence.")
    elif program.startswith("PhD") and row.get("qualifying_exam_status") == "Passed" and pos_status != "Approved":
        alerts.append("📌 Plan of Study (POS) pending approval after qualifying exam.")
    
    if program.startswith("MS") and thesis_units >= 4 and outline_approved != "Yes":
        alerts.append("📌 Thesis outline approval overdue (must be approved by 2nd thesis semester).")
    if program.startswith("PhD") and thesis_units >= 8 and outline_approved != "Yes":
        alerts.append("📌 Dissertation outline approval overdue (must be approved by 3rd dissertation semester).")
    
    if program.startswith("PhD") and residency_used >= 1 and row["qualifying_exam_status"] not in ["Passed", "N/A"]:
        alerts.append("📌 Qualifying exam should be taken before 2nd semester of residence.")
    
    if program.startswith("PhD") and row["total_units_taken"] >= row["total_units_required"] and row["written_comprehensive_status"] != "Passed":
        alerts.append("📌 Written comprehensive exam pending after completing all coursework.")
    
    return alerts

def get_early_warning_indicators(row):
    """Return a list of early warning indicators for a student."""
    warnings = []
    # High GWA (above 2.0)
    gwa = float(row["gwa"])
    if gwa > 2.0:
        warnings.append(f"⚠️ High GWA: {gwa:.2f} (above 2.0 threshold)")
    # Exceeded thesis units
    thesis_units = int(row["thesis_units_taken"])
    limit = get_thesis_limit(row["program"])
    if thesis_units > limit:
        warnings.append(f"⚠️ Exceeded thesis units: {thesis_units}/{limit}")
    # Failed exams
    if is_phd_program(row["program"]):
        if row["written_comprehensive_status"] == "Failed":
            warnings.append("⚠️ Written comprehensive exam failed")
        if row["oral_comprehensive_status"] == "Failed":
            warnings.append("⚠️ Oral comprehensive exam failed")
    else:
        if row["general_exam_status"] == "Failed":
            warnings.append("⚠️ General exam failed")
    if row["final_exam_status"] == "Failed":
        warnings.append("⚠️ Final exam failed")
    # Overdue milestones (from deadline alerts)
    alerts = check_deadline_alerts(row)
    if alerts:
        for a in alerts:
            warnings.append(a.replace("📌", "⚠️ Overdue:"))
    # Low residency warning
    residency_used = int(row["residency_years_used"])
    max_res = get_residency_max(row["program"])
    if residency_used >= max_res - 1:
        warnings.append(f"⚠️ Approaching residency limit ({residency_used}/{max_res} years)")
    # LOA exceeding limit
    loa_terms = int(row["loa_total_terms"])
    if loa_terms > 2:
        warnings.append(f"⚠️ LOA exceeds 2 years ({loa_terms} terms)")
    # AWOL
    if row["awol_status"] == "Yes":
        warnings.append("⚠️ Student is AWOL")
    return warnings

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
    notif_str = student_row.get("notifications", "[]")
    try:
        return json.loads(notif_str)
    except:
        return []

def add_notification(df, student_number, adviser_name, message, notif_type="General"):
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
    
    # Add missing columns
    default_df = create_default_data()
    for col in default_df.columns:
        if col not in df.columns:
            df[col] = default_df[col]
    
    # Ensure notifications column exists and is valid JSON
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
    
    # ---- ENSURE NAME COMPONENTS EXIST ----
    if "last_name" not in df.columns:
        df["last_name"] = ""
    if "first_name" not in df.columns:
        df["first_name"] = ""
    if "middle_name" not in df.columns:
        df["middle_name"] = ""
    
    # ---- REBUILD NAME FROM COMPONENTS ----
    def build_name(row):
        last = str(row.get("last_name", "")).strip()
        first = str(row.get("first_name", "")).strip()
        middle = str(row.get("middle_name", "")).strip()
        if last and first:
            middle_part = f" {middle}" if middle else ""
            return f"{last}, {first}{middle_part}"
        return row.get("name", "")
    
    df["name"] = df.apply(build_name, axis=1)
    
    # ---- REMOVE ROWS WITH EMPTY STUDENT NUMBER ----
    df = df[df["student_number"].notna() & (df["student_number"].astype(str).str.strip() != "")]
    df = df[df["student_number"] != "None"]
    
    # Convert numeric columns
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
    
    # Force string columns
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
    
    # Recalculate program-specific values
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

# ==================== WARNING FUNCTIONS (backward compatibility) ====================
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

# ==================== STAFF VIEW (full editing + basic analytics) ====================
if role == "SESAM Staff":
    st.subheader("📋 All Students")
    search = st.text_input("🔍 Search by name or student number", placeholder="e.g., Cruz or S001")
    filtered_df = filter_dataframe(search, df)
    filtered_df["academic_year"] = filtered_df.apply(lambda row: format_ay(row["ay_start"], row["semester"]), axis=1)
    display_cols = ["student_number", "name", "program", "academic_year", "advisor", "gwa", "thesis_units_taken", "thesis_units_limit", "pos_status", "final_exam_status"]
    st.dataframe(filtered_df[display_cols], width='stretch', height=400)

    # ---- Simple analytics dashboard for staff ----
    st.markdown("---")
    st.subheader("📊 Program Analytics")
    col_metrics = st.columns(4)
    total_students = len(df)
    at_risk = df[df["gwa"] > 2.0].shape[0] + df[df["thesis_units_taken"] > df["thesis_units_limit"]].shape[0]
    with col_metrics[0]:
        st.metric("Total Students", total_students)
    with col_metrics[1]:
        st.metric("At-Risk Students", at_risk, delta=f"{at_risk/total_students*100:.0f}%")
    with col_metrics[2]:
        st.metric("Master's Students", df[df["program"].apply(is_master_program)].shape[0])
    with col_metrics[3]:
        st.metric("PhD Students", df[df["program"].apply(is_phd_program)].shape[0])
    
    # Graphs placed at the bottom, side by side, smaller
    st.markdown("---")
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        prog_counts = df["program"].value_counts().reset_index()
        prog_counts.columns = ["Program", "Count"]
        fig = px.bar(prog_counts, x="Program", y="Count", title="Student Distribution by Program", color="Program", height=300)
        st.plotly_chart(fig, use_container_width=True)
    with col_chart2:
        fig_gwa = px.histogram(df, x="gwa", nbins=20, title="GWA Distribution", color_discrete_sequence=["green"], height=300)
        st.plotly_chart(fig_gwa, use_container_width=True)

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

        # ----- PROFILE PICTURE (view only) at upper right -----
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
            with col1:
                st.markdown(f"**Student Number:** {student['student_number']}")
                st.markdown(f"**Name:** {student['name']}")
            with col2:
                st.markdown(f"**Program:** {student['program']}")
                st.markdown(f"**Advisor:** {student['advisor']}")
            with col3:
                limit = get_thesis_limit(student["program"])
                st.markdown(f"**Thesis Units:** {student['thesis_units_taken']} / {limit}")
                st.markdown(f"**Academic Year & Semester:** {format_ay(student['ay_start'], student['semester'])}")
                if student["thesis_units_taken"] > limit:
                    st.error("⚠️ Units exceeded!")

        # ----- AMIS SCREENSHOT (view only) -----
        st.markdown("---")
        st.subheader("📊 AMIS Screenshot (View Only)")
        amis_path = get_amis_screenshot_path(student_number)
        if amis_path and os.path.exists(amis_path):
            st.image(amis_path, width=250, caption="AMIS Screenshot")
        else:
            st.info("No AMIS screenshot uploaded by student.")

        # ----- MANUAL GWA ENTRY -----
        st.markdown("---")
        st.subheader("📈 Manual GWA Entry (based on AMIS)")
        current_gwa = float(student["gwa"])
        new_gwa = st.number_input("Enter the GWA exactly as shown on the AMIS screenshot", 
                                  min_value=1.0, max_value=5.0, step=0.01, value=current_gwa)
        if st.button("Update GWA from AMIS"):
            df.loc[df["student_number"] == student_number, "gwa"] = new_gwa
            save_data(df)
            st.success(f"GWA updated to {new_gwa}")
            st.rerun()

        # ----- DEADLINE ALERTS & WARNINGS -----
        deadline_alerts = check_deadline_alerts(student)
        if deadline_alerts:
            for alert in deadline_alerts:
                st.error(alert)

        warnings = get_all_warnings(student)
        if any("⚠️" in w for w in warnings):
            for w in warnings:
                st.error(w)
        else:
            st.success("\n".join(warnings))

        # ----- EDIT TABS (milestone editing) -----
        tabs = st.tabs(["Coursework & Thesis", "Exams", "Residency & Leave", "Graduation", "Committee", "Other"])
        
        with tabs[0]:
            with st.form("coursework_form"):
                st.subheader("Plan of Study (POS)")
                pos_options = ["Not Filed", "Pending", "Approved"]
                pos_status = st.selectbox("POS Status", pos_options, index=safe_index(pos_options, student["pos_status"]))
                pos_submitted = st.text_input("POS Submitted Date (YYYY-MM-DD)", student["pos_submitted_date"])
                pos_approved = st.text_input("POS Approved Date (YYYY-MM-DD)", student["pos_approved_date"])
                st.subheader("Coursework")
                gwa = st.number_input("GWA", min_value=1.0, max_value=5.0, step=0.01, value=float(student["gwa"]))
                total_units_taken = st.number_input("Total Units Taken", min_value=0, max_value=60, step=1, value=int(student["total_units_taken"]))
                total_units_required = st.number_input("Total Units Required", min_value=0, max_value=60, step=1, value=int(student["total_units_required"]))
                progress = compute_coursework_progress(student)
                st.progress(progress / 100, text=f"Coursework completion: {progress}% ({student['total_units_taken']} of {student['total_units_required']} units)")
                st.caption(f"Remaining units: {max(0, student['total_units_required'] - student['total_units_taken'])}")
                st.subheader("Thesis/Dissertation")
                thesis_units_taken = st.number_input("Thesis Units Taken", min_value=0, max_value=20, step=1, value=int(student["thesis_units_taken"]))
                st.caption(get_thesis_pattern_description(student["program"]))
                outline_options = ["Yes", "No"]
                thesis_outline_approved = st.selectbox("Thesis Outline Approved", outline_options, index=safe_index(outline_options, student["thesis_outline_approved"]))
                thesis_outline_date = st.text_input("Outline Approval Date", student["thesis_outline_approved_date"])
                status_options = ["Not Started", "In Progress", "Draft with Adviser", "For Committee Review", "Approved", "Submitted"]
                thesis_status = st.selectbox("Thesis Status", status_options, index=safe_index(status_options, student["thesis_status"]))
                if st.form_submit_button("Update Coursework & Thesis"):
                    df.loc[df["student_number"] == student_number, ["pos_status","pos_submitted_date","pos_approved_date","gwa","total_units_taken","total_units_required","thesis_units_taken","thesis_outline_approved","thesis_outline_approved_date","thesis_status"]] = [pos_status, pos_submitted, pos_approved, gwa, total_units_taken, total_units_required, thesis_units_taken, thesis_outline_approved, thesis_outline_date, thesis_status]
                    save_data(df)
                    st.success("✅ Updated!")
                    st.rerun()
        with tabs[1]:
            with st.form("exams_form"):
                st.subheader("Examinations")
                qual_options = ["N/A", "Not Taken", "Passed", "Failed", "Re-exam Scheduled"]
                qualifying = st.selectbox("Qualifying Exam Status (PhD)", qual_options, index=safe_index(qual_options, student["qualifying_exam_status"]))
                qualifying_date = st.text_input("Qualifying Exam Passed Date", student["qualifying_exam_passed_date"])
                wcomp_options = ["N/A", "Not Taken", "Passed", "Failed"]
                written_comp = st.selectbox("Written Comprehensive Status", wcomp_options, index=safe_index(wcomp_options, student["written_comprehensive_status"]))
                written_comp_date = st.text_input("Written Comprehensive Passed Date", student["written_comprehensive_passed_date"])
                ocomp_options = ["N/A", "Not Taken", "Passed", "Failed"]
                oral_comp = st.selectbox("Oral Comprehensive Status", ocomp_options, index=safe_index(ocomp_options, student["oral_comprehensive_status"]))
                oral_comp_date = st.text_input("Oral Comprehensive Passed Date", student["oral_comprehensive_passed_date"])
                gen_options = ["N/A", "Not Taken", "Passed", "Failed"]
                general = st.selectbox("General Exam Status (MS)", gen_options, index=safe_index(gen_options, student["general_exam_status"]))
                general_date = st.text_input("General Exam Passed Date", student["general_exam_passed_date"])
                final_options = ["Not Taken", "Passed", "Failed", "Re-exam Scheduled"]
                final = st.selectbox("Final Exam Status", final_options, index=safe_index(final_options, student["final_exam_status"]))
                final_date = st.text_input("Final Exam Passed Date", student["final_exam_passed_date"])
                if st.form_submit_button("Update Exams"):
                    df.loc[df["student_number"] == student_number, ["qualifying_exam_status","qualifying_exam_passed_date","written_comprehensive_status","written_comprehensive_passed_date","oral_comprehensive_status","oral_comprehensive_passed_date","general_exam_status","general_exam_passed_date","final_exam_status","final_exam_passed_date"]] = [qualifying, qualifying_date, written_comp, written_comp_date, oral_comp, oral_comp_date, general, general_date, final, final_date]
                    save_data(df)
                    st.success("✅ Updated!")
                    st.rerun()
        with tabs[2]:
            with st.form("residency_form"):
                st.subheader("Residency")
                residency_used = st.number_input("Years of Residence Used", min_value=0, max_value=10, step=1, value=int(student["residency_years_used"]))
                max_years = get_residency_max(student["program"])
                st.info(f"Maximum allowed: {max_years} years")
                extension_count = st.number_input("Number of Extensions Granted", min_value=0, max_value=3, step=1, value=int(student["extension_count"]))
                extension_end = st.text_input("Extension End Date (if applicable)", student["extension_end_date"])
                st.subheader("Leave of Absence (LOA)")
                loa_start = st.text_input("LOA Start Date", student["loa_start_date"])
                loa_end = st.text_input("LOA End Date", student["loa_end_date"])
                loa_terms = st.number_input("Total LOA Terms (each term = 0.5 year)", min_value=0, max_value=4, step=1, value=int(student["loa_total_terms"]))
                st.subheader("AWOL")
                awol_options = ["No", "Yes"]
                awol = st.selectbox("AWOL Status", awol_options, index=safe_index(awol_options, student["awol_status"]))
                awol_lifted = st.text_input("AWOL Lifted Date", student["awol_lifted_date"])
                if st.form_submit_button("Update Residency & Leave"):
                    df.loc[df["student_number"] == student_number, ["residency_years_used","extension_count","extension_end_date","loa_start_date","loa_end_date","loa_total_terms","awol_status","awol_lifted_date"]] = [residency_used, extension_count, extension_end, loa_start, loa_end, loa_terms, awol, awol_lifted]
                    save_data(df)
                    st.success("✅ Updated!")
                    st.rerun()
        with tabs[3]:
            with st.form("graduation_form"):
                st.subheader("Graduation")
                yn_options = ["No", "Yes"]
                grad_applied = st.selectbox("Graduation Applied", yn_options, index=safe_index(yn_options, student["graduation_applied"]))
                grad_approved = st.selectbox("Graduation Approved", yn_options, index=safe_index(yn_options, student["graduation_approved"]))
                grad_date = st.text_input("Graduation Date (YYYY-MM-DD)", student["graduation_date"])
                st.subheader("Transfer Credit")
                transfer_units = st.number_input("Transfer Credits Approved (max 9 units)", min_value=0, max_value=9, step=1, value=int(student["transfer_units_approved"]))
                if st.form_submit_button("Update Graduation & Transfer"):
                    df.loc[df["student_number"] == student_number, ["graduation_applied","graduation_approved","graduation_date","transfer_units_approved"]] = [grad_applied, grad_approved, grad_date, transfer_units]
                    save_data(df)
                    st.success("✅ Updated!")
                    st.rerun()
        with tabs[4]:
            with st.form("committee_form"):
                st.subheader("Guidance / Advisory Committee")
                committee_members = st.text_area("Committee Members (one per line)", value=student.get("committee_members", ""), height=150,
                                                 help="List names of major professor/adviser and other committee members.")
                committee_approval_date = st.text_input("Committee Approval Date (YYYY-MM-DD)", student.get("committee_approval_date", ""))
                if st.form_submit_button("Update Committee"):
                    df.loc[df["student_number"] == student_number, "committee_members"] = committee_members
                    df.loc[df["student_number"] == student_number, "committee_approval_date"] = committee_approval_date
                    save_data(df)
                    st.success("Committee information updated!")
                    st.rerun()
        with tabs[5]:
            with st.form("other_form"):
                st.subheader("Re-admission (for students who exceeded time limit)")
                readmit_options = ["Not Applicable", "Applied", "Approved", "Denied"]
                re_status = st.selectbox("Re-admission Status", readmit_options, index=safe_index(readmit_options, student["re_admission_status"]))
                re_date = st.text_input("Re-admission Date", student["re_admission_date"])
                if st.form_submit_button("Update Re-admission"):
                    df.loc[df["student_number"] == student_number, ["re_admission_status","re_admission_date"]] = [re_status, re_date]
                    save_data(df)
                    st.success("✅ Updated!")
                    st.rerun()
    else:
        st.info("No students match the current search. Try a different name/number or add a new student below.")

    # ----- ADD NEW STUDENT (simplified) -----
    st.markdown("---")
    st.subheader("➕ Add New Student")
    with st.expander("Register New Student", expanded=True):
        with st.form(key="add_student_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                last_name = st.text_input("Last Name *", placeholder="Dela Cruz")
            with col2:
                first_name = st.text_input("First Name *", placeholder="Juan")
            with col3:
                middle_name = st.text_input("Middle Name", placeholder="Santos (optional)")
            
            col4, col5 = st.columns(2)
            with col4:
                student_number = st.text_input("Student Number *", placeholder="2025-00123")
            with col5:
                program = st.selectbox("Program *", options=PROGRAMS)
            
            phd_track = None
            if program in ["PhD Environmental Science", "PhD Environmental Diplomacy and Negotiations"]:
                track_col, dummy = st.columns([1, 1])
                with track_col:
                    phd_track = st.selectbox("PhD Track *", options=PhD_TRACKS, help="Select based on your previous degree")
            
            col6, col7 = st.columns(2)
            with col6:
                selected_ay_range = st.selectbox("Academic Year *", options=ACADEMIC_YEARS, 
                                                index=ACADEMIC_YEARS.index(f"{current_year}-{current_year+1}") if f"{current_year}-{current_year+1}" in ACADEMIC_YEARS else 0)
                ay_start = int(selected_ay_range.split("-")[0])
            with col7:
                semester = st.selectbox("Semester *", options=SEMESTERS)
            
            col8, col9 = st.columns(2)
            with col8:
                advisor = st.text_input("Advisor (optional)", placeholder="Dr. Faustino-Eslava")
            with col9:
                st.empty()
            
            submitted = st.form_submit_button("Register Student")
            if submitted:
                errors = []
                if not last_name:
                    errors.append("Last Name is required.")
                if not first_name:
                    errors.append("First Name is required.")
                if not student_number:
                    errors.append("Student Number is required.")
                if student_number in df["student_number"].values:
                    errors.append("Student number already exists. Please use a unique number.")
                if program in ["PhD Environmental Science", "PhD Environmental Diplomacy and Negotiations"] and not phd_track:
                    errors.append("PhD Track is required.")
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    middle = f" {middle_name.strip()}" if middle_name.strip() else ""
                    full_name = f"{last_name.strip()}, {first_name.strip()}{middle}"
                    if program in ["PhD Environmental Science", "PhD Environmental Diplomacy and Negotiations"]:
                        required_units = get_required_units(program, phd_track)
                    else:
                        required_units = get_required_units(program)
                    new_row = create_default_data().iloc[0].to_dict()
                    new_row.update({
                        "student_number": student_number.strip(),
                        "name": full_name,
                        "last_name": last_name.strip(),
                        "first_name": first_name.strip(),
                        "middle_name": middle_name.strip(),
                        "program": program,
                        "phd_track": phd_track if phd_track else "",
                        "advisor": advisor.strip() if advisor else "Not assigned",
                        "ay_start": ay_start,
                        "semester": semester,
                        "pos_status": "Not Filed",
                        "gwa": 2.00,
                        "thesis_units_taken": 0,
                        "thesis_units_limit": get_thesis_limit(program),
                        "total_units_required": required_units,
                        "residency_max_years": get_residency_max(program),
                        "profile_pic": "",
                        "amis_screenshot": "",
                        "notifications": "[]",
                        "committee_members": "",
                        "committee_approval_date": "",
                        "pos_submitted_date": "",
                        "pos_approved_date": "",
                        "total_units_taken": 0,
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
                        "re_admission_date": ""
                    })
                    new_df = pd.DataFrame([new_row])
                    df = pd.concat([df, new_df], ignore_index=True)
                    save_data(df)
                    st.success(f"✅ Student {full_name} (Number: {student_number}) registered successfully!")
                    st.rerun()

# ==================== ENHANCED ADVISER VIEW (with dashboard & early warnings) ====================
elif role == "Faculty Adviser":
    st.subheader(f"👨‍🏫 Your Advisees")
    adviser_name = st.session_state.display_name
    advisees = df[df["advisor"] == adviser_name].copy()
    
    if len(advisees) == 0:
        st.warning(f"You have no students assigned yet. Contact SESAM Staff to assign students to you.")
    else:
        # ---- Dashboard metrics for adviser ----
        st.markdown("### 📊 Advising Dashboard")
        col1, col2, col3, col4 = st.columns(4)
        total_advisees = len(advisees)
        at_risk_count = 0
        overdue_count = 0
        pending_pos = 0
        for _, row in advisees.iterrows():
            warnings = get_early_warning_indicators(row)
            if len(warnings) > 0:
                at_risk_count += 1
            if row["pos_status"] == "Pending":
                pending_pos += 1
            if len(check_deadline_alerts(row)) > 0:
                overdue_count += 1
        with col1:
            st.metric("Total Advisees", total_advisees)
        with col2:
            st.metric("At-Risk Students", at_risk_count, delta=f"{at_risk_count/total_advisees*100:.0f}%")
        with col3:
            st.metric("Pending POS", pending_pos)
        with col4:
            st.metric("Overdue Alerts", overdue_count)
        
        # ---- At-risk list (compact) ----
        if at_risk_count > 0:
            with st.expander("⚠️ At-Risk Students (click to view details)", expanded=False):
                at_risk_df = advisees.apply(lambda row: pd.Series({
                    "Name": row["name"],
                    "Student #": row["student_number"],
                    "GWA": row["gwa"],
                    "Thesis Units": f"{row['thesis_units_taken']}/{row['thesis_units_limit']}",
                    "POS Status": row["pos_status"],
                    "Warnings": len(get_early_warning_indicators(row))
                }), axis=1)
                at_risk_df = at_risk_df[at_risk_df["Warnings"] > 0]
                st.dataframe(at_risk_df[["Name", "Student #", "GWA", "Thesis Units", "POS Status"]], width='stretch')
        
        # ---- Search and table ----
        st.markdown("---")
        search_adv = st.text_input("🔍 Search by name or student number", placeholder="e.g., Cruz or S001")
        filtered_advisees = filter_dataframe(search_adv, advisees)
        filtered_advisees["academic_year"] = filtered_advisees.apply(lambda row: format_ay(row["ay_start"], row["semester"]), axis=1)
        filtered_advisees["warnings"] = filtered_advisees.apply(lambda row: "\n".join(get_all_warnings(row)), axis=1)
        display_cols = ["student_number", "name", "program", "academic_year", "gwa", "thesis_units_taken", "thesis_units_limit", "pos_status", "final_exam_status", "warnings"]
        st.dataframe(filtered_advisees[display_cols], width='stretch')
        
        # ---- Milestone completion chart (placed at bottom, smaller) ----
        if len(filtered_advisees) > 0:
            milestone_status = []
            for _, row in filtered_advisees.iterrows():
                milestone_status.append({
                    "Student": row["name"],
                    "POS Approved": 1 if row["pos_status"] == "Approved" else 0,
                    "Thesis Units Completed": 1 if row["thesis_units_taken"] >= get_thesis_limit(row["program"]) else 0,
                    "Final Exam Passed": 1 if row["final_exam_status"] == "Passed" else 0
                })
            milestone_df = pd.DataFrame(milestone_status)
            if not milestone_df.empty:
                st.markdown("---")
                st.subheader("📈 Key Milestone Completion (Overview)")
                fig_milestone = go.Figure(data=[
                    go.Bar(name="POS Approved", x=milestone_df["Student"], y=milestone_df["POS Approved"], marker_color="blue"),
                    go.Bar(name="Thesis Units Completed", x=milestone_df["Student"], y=milestone_df["Thesis Units Completed"], marker_color="orange"),
                    go.Bar(name="Final Exam Passed", x=milestone_df["Student"], y=milestone_df["Final Exam Passed"], marker_color="green")
                ])
                fig_milestone.update_layout(barmode='group', title="", xaxis_tickangle=-45, height=350)
                st.plotly_chart(fig_milestone, use_container_width=True)
        
        # ---- Detailed student expanders ----
        if len(filtered_advisees) > 0:
            st.markdown("---")
            st.subheader("📌 Detailed Student Progress & Notifications")
            for _, row in filtered_advisees.iterrows():
                with st.expander(f"📘 {row['name']} ({row['student_number']})", expanded=False):
                    # Profile picture at upper right
                    pic_path = get_profile_picture_path(row["student_number"])
                    col_pic_left, col_pic_right = st.columns([4, 1])
                    with col_pic_right:
                        if pic_path and os.path.exists(pic_path):
                            st.image(pic_path, width=100, caption="Profile Picture")
                        else:
                            st.info("No picture")
                    with col_pic_left:
                        col1, col2, col3 = st.columns([2, 2, 2])
                        with col1:
                            st.markdown(f"**Program:** {row['program']}")
                            st.metric("GWA", f"{row['gwa']:.2f}", delta="Good" if row['gwa'] <= 2.0 else "Alert", delta_color="normal")
                            st.markdown(f"**Academic Year:** {format_ay(row['ay_start'], row['semester'])}")
                        with col2:
                            st.metric("Residency", f"{row['residency_years_used']} / {get_residency_max(row['program'])} years")
                            st.metric("Thesis Units", f"{row['thesis_units_taken']} / {row['thesis_units_limit']}")
                            st.metric("POS Status", row['pos_status'])
                        with col3:
                            st.metric("Final Exam", row['final_exam_status'])
                            st.metric("Graduation Applied", row['graduation_applied'])
                    
                    # Early warning indicators for this student
                    early_warnings = get_early_warning_indicators(row)
                    if early_warnings:
                        st.warning("🚨 Early Warning Indicators")
                        for w in early_warnings:
                            st.markdown(f"- {w}")
                    
                    st.markdown("---")
                    st.subheader("📚 Coursework Progress")
                    units_taken = int(row['total_units_taken'])
                    units_required = int(row['total_units_required'])
                    progress_pct = compute_coursework_progress(row)
                    st.progress(progress_pct / 100, text=f"{progress_pct}% completed ({units_taken} of {units_required} units)")
                    st.caption(f"Remaining units: {max(0, units_required - units_taken)}")
                    
                    st.markdown("---")
                    st.subheader("📋 Milestone Status & Dates")
                    milestone_data = []
                    pos_date = row['pos_approved_date'] if row['pos_approved_date'] and row['pos_approved_date'] != 'nan' else row['pos_submitted_date'] if row['pos_submitted_date'] and row['pos_submitted_date'] != 'nan' else ''
                    milestone_data.append(["Plan of Study (POS)", row['pos_status'], pos_date])
                    if is_phd_program(row['program']):
                        milestone_data.append(["Written Comprehensive Exam", row['written_comprehensive_status'], row['written_comprehensive_passed_date']])
                        milestone_data.append(["Oral Comprehensive Exam", row['oral_comprehensive_status'], row['oral_comprehensive_passed_date']])
                    else:
                        milestone_data.append(["General Exam (MS)", row['general_exam_status'], row['general_exam_passed_date']])
                    thesis_date = row['thesis_outline_approved_date'] if row['thesis_outline_approved'] == 'Yes' else ''
                    milestone_data.append(["Thesis/Dissertation Outline", row['thesis_outline_approved'], thesis_date])
                    milestone_data.append(["Thesis/Dissertation Status", row['thesis_status'], ""])
                    milestone_data.append(["Final Exam", row['final_exam_status'], row['final_exam_passed_date']])
                    milestone_data.append(["Graduation Application", row['graduation_applied'], ""])
                    milestone_data.append(["Graduation Approved", row['graduation_approved'], row['graduation_date']])
                    
                    milestone_df_table = pd.DataFrame(milestone_data, columns=["Milestone", "Status", "Date"])
                    st.dataframe(milestone_df_table, width='stretch', hide_index=True)
                    
                    st.markdown("---")
                    st.subheader("⚠️ Remaining Requirements")
                    pend = []
                    if row['pos_status'] not in ["Approved", "Completed"]:
                        pend.append("❌ POS not approved")
                    if is_phd_program(row['program']):
                        if row['written_comprehensive_status'] != "Passed":
                            pend.append("❌ Written comprehensive exam not passed")
                        if row['written_comprehensive_status'] == "Passed" and row['oral_comprehensive_status'] != "Passed":
                            pend.append("❌ Oral comprehensive exam not passed")
                    else:
                        if row['general_exam_status'] != "Passed":
                            pend.append("❌ General exam not passed")
                    if row['thesis_outline_approved'] != "Yes" and ((is_master_program(row['program']) and row['thesis_units_taken'] >= 4) or (is_phd_program(row['program']) and row['thesis_units_taken'] >= 8)):
                        pend.append("❌ Thesis outline overdue")
                    if row['final_exam_status'] != "Passed":
                        pend.append("❌ Final exam not passed")
                    if row['graduation_applied'] == "Yes" and row['graduation_approved'] != "Yes":
                        pend.append("⏳ Graduation pending approval")
                    if row['awol_status'] == "Yes":
                        pend.append("🚨 AWOL")
                    if int(row['loa_total_terms']) > 0:
                        pend.append(f"📅 On LOA: {row['loa_total_terms']} term(s)")
                    if pend:
                        for p in pend:
                            st.warning(p)
                    else:
                        st.success("✅ All requirements satisfied – student is on track.")
                    
                    # Committee info
                    if row.get('committee_members') and row['committee_members'] not in ['', 'nan']:
                        with st.expander("📋 Guidance/Advisory Committee"):
                            st.text(row['committee_members'].replace(", ", "\n"))
                            if row.get('committee_approval_date') and row['committee_approval_date'] not in ['', 'nan']:
                                st.caption(f"Approved on: {row['committee_approval_date']}")
                    
                    # LOA/AWOL details
                    if row['loa_start_date'] and row['loa_start_date'] not in ['', 'nan']:
                        st.caption(f"LOA period: {row['loa_start_date']} to {row['loa_end_date']}")
                    if row['awol_lifted_date'] and row['awol_lifted_date'] not in ['', 'nan']:
                        st.caption(f"AWOL lifted on: {row['awol_lifted_date']}")
                    
                    st.markdown("---")
                    # AMIS screenshot
                    amis_path = get_amis_screenshot_path(row["student_number"])
                    if amis_path and os.path.exists(amis_path):
                        with st.expander("📄 View AMIS Screenshot"):
                            st.image(amis_path, width=300)
                    else:
                        st.info("No AMIS screenshot uploaded.")
                    
                    st.markdown("---")
                    # Send notification
                    st.subheader("📬 Send Notification to Student")
                    with st.form(key=f"notif_form_{row['student_number']}"):
                        notif_type = st.selectbox("Notification Type", ["General Reminder", "Academic Warning", "Meeting Request", "Requirement Follow-up"])
                        message = st.text_area("Message", height=100, placeholder="Type your message here...")
                        send = st.form_submit_button("Send Notification")
                        if send and message.strip():
                            df = add_notification(df, row["student_number"], adviser_name, message, notif_type)
                            save_data(df)
                            st.success(f"Notification sent to {row['name']}!")
                            st.rerun()
                        elif send and not message.strip():
                            st.error("Message cannot be empty.")
                    
                    # Deadline alerts and warnings
                    alerts = check_deadline_alerts(row)
                    if alerts:
                        for alert in alerts:
                            st.error(alert)
                    warnings_text = row["warnings"]
                    if any("⚠️" in w for w in warnings_text.split("\n")):
                        for w in warnings_text.split("\n"):
                            st.error(w)
                    else:
                        st.success(warnings_text)
        else:
            st.info("No matching students.")
    st.info("📌 You can send notifications to your advisees. They will see them immediately when they log in.")

# ==================== STUDENT VIEW (unchanged) ====================
elif role == "Student":
    st.subheader(f"📘 Your Academic Progress ({st.session_state.display_name})")
    if st.session_state.student_number:
        student_record = df[df["student_number"] == st.session_state.student_number]
    else:
        student_record = df[df["name"] == st.session_state.display_name]
    
    if len(student_record) == 0:
        st.error("Your record was not found. Please contact SESAM Staff to verify your student number.")
        st.stop()
    
    student = student_record.iloc[0]

    # Display notifications
    notifications = get_notifications(student)
    if notifications:
        st.markdown("---")
        st.subheader("📬 Messages from Your Adviser")
        for i, notif in enumerate(notifications):
            notif_type = notif.get("type", "General")
            if notif_type == "Academic Warning":
                st.error(f"🚨 **{notif_type}** – {notif['timestamp']}\n\n*From: {notif['from']}*\n\n{notif['message']}")
            elif notif_type == "Meeting Request":
                st.info(f"📅 **{notif_type}** – {notif['timestamp']}\n\n*From: {notif['from']}*\n\n{notif['message']}")
            else:
                st.info(f"📌 **{notif_type}** – {notif['timestamp']}\n\n*From: {notif['from']}*\n\n{notif['message']}")
            if st.button(f"Dismiss", key=f"dismiss_{i}"):
                df = dismiss_notification(df, student["student_number"], i)
                save_data(df)
                st.rerun()
    
    # Deadline alerts & warnings
    alerts = check_deadline_alerts(student)
    if alerts:
        for alert in alerts:
            st.error(alert)
    warnings = get_all_warnings(student)
    if any("⚠️" in w for w in warnings):
        for w in warnings:
            st.error(w)
    else:
        st.success("\n".join(warnings))

    # Profile picture at upper right
    st.markdown("---")
    col_left, col_right = st.columns([3, 1])
    with col_right:
        pic_path = get_profile_picture_path(student["student_number"])
        if pic_path and os.path.exists(pic_path):
            st.image(pic_path, width=100, caption="Your Picture")
        else:
            st.info("No profile picture")
    with col_left:
        st.subheader("Student Information")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Student Number", student["student_number"])
            st.metric("Program", student["program"])
            st.metric("Academic Year", format_ay(student["ay_start"], student["semester"]))
        with col2:
            st.metric("Advisor", student["advisor"])
            st.metric("GWA", f"{student['gwa']:.2f}")
            st.metric("POS Status", student["pos_status"])
        with col3:
            limit = get_thesis_limit(student["program"])
            st.metric("Thesis Units", f"{student['thesis_units_taken']} / {limit}")
            st.metric("Residency", f"{student['residency_years_used']} / {get_residency_max(student['program'])} years")
            st.metric("Final Exam", student["final_exam_status"])
    
    # Profile picture upload/delete
    st.markdown("---")
    st.subheader("📸 Update Your Profile Picture")
    uploaded_file = st.file_uploader("Upload new profile picture (JPG, PNG, GIF)", type=["jpg", "jpeg", "png", "gif"], key="profile_upload")
    if uploaded_file:
        new_filename = save_profile_picture(student["student_number"], uploaded_file)
        if new_filename:
            df.loc[df["student_number"] == student["student_number"], "profile_pic"] = new_filename
            save_data(df)
            st.success("Profile picture updated!")
            st.rerun()
    if st.button("🗑️ Delete my profile picture"):
        if delete_profile_picture(student["student_number"]):
            df.loc[df["student_number"] == student["student_number"], "profile_pic"] = ""
            save_data(df)
            st.success("Profile picture deleted.")
            st.rerun()

    # AMIS screenshot
    st.markdown("---")
    st.subheader("📊 Your AMIS Screenshot (Subjects, Grades, Units)")
    col_amis1, col_amis2 = st.columns([1, 2])
    with col_amis1:
        amis_path = get_amis_screenshot_path(student["student_number"])
        if amis_path and os.path.exists(amis_path):
            st.image(amis_path, width=250, caption="Your AMIS Screenshot")
        else:
            st.info("No AMIS screenshot uploaded.")
    with col_amis2:
        uploaded_amis = st.file_uploader("Upload AMIS screenshot (JPG/PNG)", type=["jpg", "jpeg", "png"], key="amis_upload_student")
        if uploaded_amis:
            new_file = save_amis_screenshot(student["student_number"], uploaded_amis)
            if new_file:
                st.success("AMIS screenshot uploaded!")
                st.rerun()
        if st.button("🗑️ Delete my AMIS screenshot"):
            if delete_amis_screenshot(student["student_number"]):
                st.success("AMIS screenshot deleted.")
                st.rerun()

    # Manual GWA entry
    st.markdown("---")
    st.subheader("📈 Update GWA from AMIS Screenshot")
    current_gwa = float(student["gwa"])
    new_gwa = st.number_input("Enter GWA exactly as on the screenshot", 
                              min_value=1.0, max_value=5.0, step=0.01, value=current_gwa)
    if st.button("Update My GWA"):
        df.loc[df["student_number"] == student["student_number"], "gwa"] = new_gwa
        save_data(df)
        st.success(f"GWA updated to {new_gwa}")
        st.rerun()

    # Coursework progress
    st.markdown("---")
    st.subheader("📚 Coursework Progress")
    prog = compute_coursework_progress(student)
    st.progress(prog / 100, text=f"{prog}% completed ({student['total_units_taken']} of {student['total_units_required']} units)")
    st.caption(f"Remaining units: {max(0, student['total_units_required'] - student['total_units_taken'])}")

    # Committee information
    if student.get("committee_members"):
        with st.expander("📋 Your Guidance/Advisory Committee"):
            st.text_area("Committee Members", value=student["committee_members"], height=120, disabled=True)
            if student.get("committee_approval_date"):
                st.caption(f"Approved on: {student['committee_approval_date']}")

    # Milestone status
    st.markdown("---")
    st.subheader("📌 Milestone Status")
    milestone_df = pd.DataFrame({
        "Milestone": [
            "Plan of Study (POS)",
            "General Exam (MS) / Qualifying Exam (PhD)",
            "Written Comprehensive (PhD)",
            "Oral Comprehensive (PhD)",
            "Thesis/Dissertation Outline",
            "Final Examination"
        ],
        "Status": [
            student["pos_status"],
            student["general_exam_status"] if is_master_program(student["program"]) else student["qualifying_exam_status"],
            student["written_comprehensive_status"] if is_phd_program(student["program"]) else "N/A",
            student["oral_comprehensive_status"] if is_phd_program(student["program"]) else "N/A",
            student["thesis_outline_approved"],
            student["final_exam_status"]
        ]
    })
    st.dataframe(milestone_df, width='stretch', hide_index=True)
    st.info("📌 Read‑only view. For updates, contact your adviser or SESAM Staff.")

# ==================== FOOTER ====================
st.markdown("---")
st.caption("SESAM KMIS – Student Module V2 | Faculty-to-Student Notifications | Based on UPLB Graduate School Rules (2009)")
