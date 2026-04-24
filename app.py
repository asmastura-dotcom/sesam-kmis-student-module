"""
SESAM KMIS - Graduate Student Milestone Workflow System (FIXED)
Full milestone tracking, document uploads, validation workflows, alerts, and dashboards.
Author: SESAM Dev Team
Date: 2026-04-24
Based on UPLB Graduate School Rules.
"""

import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, timedelta
from PIL import Image
import io
import json
import plotly.express as px
import plotly.graph_objects as go

# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="SESAM KMIS - Milestone Workflow", page_icon="🎓", layout="wide")

# ==================== SESSION STATE ====================
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

# ==================== USER AUTH ====================
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
        return 37 if phd_track == "MS EnvSci graduate" else 50
    else:
        return 36 if is_master_program(program) else 48

def format_ay(ay_start, semester):
    return f"A.Y. {ay_start}-{ay_start+1} ({semester})"

def get_start_date(ay_start, semester):
    """Approximate start date for deadline calculations (fixed for 2nd Sem/Summer)."""
    if semester == "1st Sem":
        return date(ay_start, 8, 1)
    elif semester == "2nd Sem":
        return date(ay_start + 1, 1, 1)   # Jan of next year
    else:  # Summer
        return date(ay_start + 1, 4, 1)   # April of next year

# ==================== FOLDER SETUP ====================
FOLDERS = ["profile_pics", "amis_screenshots", "admission_letters", "committee_docs",
           "coursework_grades", "exam_results", "thesis_docs", "manuscripts"]
for folder in FOLDERS:
    if not os.path.exists(folder):
        os.makedirs(folder)

def compress_image(file, max_size_kb=200, output_width=500):
    img = Image.open(file)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    ratio = output_width / float(img.size[0])
    output_height = int(float(img.size[1]) * ratio)
    # Use legacy LANCZOS for compatibility with older Pillow
    img = img.resize((output_width, output_height), Image.LANCZOS)
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

def save_uploaded_file(folder, student_number, file, prefix):
    if file is None:
        return None
    try:
        ext = file.name.split('.')[-1].lower()
        if ext in ['jpg', 'jpeg', 'png', 'gif']:
            compressed = compress_image(file)
            filename = f"{student_number}_{prefix}.jpg"
        else:
            compressed = file.getvalue()
            filename = f"{student_number}_{prefix}.{ext}"
        filepath = os.path.abspath(os.path.join(folder, filename))
        with open(filepath, "wb") as f:
            f.write(compressed)
        return filepath
    except Exception as e:
        st.error(f"Upload failed: {e}")
        return None

def delete_file(filepath):
    if filepath and os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False

def get_file_path(folder, student_number, prefix):
    for f in os.listdir(folder):
        if f.startswith(f"{student_number}_{prefix}"):
            return os.path.join(folder, f)
    return None

# ==================== NOTIFICATION FUNCTIONS ====================
def get_notifications(student_row):
    try:
        val = student_row.get("notifications", "[]")
        if pd.isna(val) or val == "":
            return []
        return json.loads(val)
    except:
        return []

def add_notification(df, student_number, from_name, message, notif_type="General"):
    idx = df[df["student_number"] == student_number].index
    if len(idx) == 0:
        return df
    notif_list = get_notifications(df.loc[idx[0]])
    notif_list.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "from": from_name,
        "message": message,
        "type": notif_type,
        "read": False
    })
    df.at[idx[0], "notifications"] = json.dumps(notif_list)
    return df

def dismiss_notification(df, student_number, index):
    idx = df[df["student_number"] == student_number].index
    if len(idx) == 0:
        return df
    notif_list = get_notifications(df.loc[idx[0]])
    if 0 <= index < len(notif_list):
        notif_list.pop(index)
        df.at[idx[0], "notifications"] = json.dumps(notif_list)
    return df

# ==================== DATA LOADING WITH NEW COLUMNS ====================
DATA_FILE = "students.csv"

def create_default_data():
    return pd.DataFrame({
        "student_number": ["S001", "S002"],
        "name": ["Cruz, Juan M.", "Santos, Maria L."],
        "last_name": ["Cruz", "Santos"],
        "first_name": ["Juan", "Maria"],
        "middle_name": ["M.", "L."],
        "program": [PROGRAMS[0], PROGRAMS[1]],
        "phd_track": ["", "MS EnvSci graduate"],
        "advisor": ["Dr. Eslava", "Dr. Sanchez"],
        "ay_start": [2024, 2023],
        "semester": ["1st Sem", "1st Sem"],
        "profile_pic": ["", ""],
        "amis_screenshot": ["", ""],
        "notifications": ["[]", "[]"],
        "committee_members": ["", ""],
        "committee_approval_date": ["", ""],
        # Admission milestone
        "admission_status": ["Approved", "Approved"],
        "admission_letter_path": ["", ""],
        "admission_validator": ["staff1", "staff1"],
        "admission_validation_date": ["2024-01-15", "2023-06-10"],
        # Committee formation
        "committee_status": ["Approved", "Approved"],
        "committee_doc_path": ["", ""],
        "committee_deadline": ["2024-10-01", "2023-08-01"],
        "committee_validation_by": ["adviser1", "adviser2"],
        # Coursework per semester (JSON)
        "semester_records": ["[]", "[]"],
        # Major exam (MS: General, PhD: Comprehensive)
        "major_exam_status": ["Pending", "Passed"],
        "major_exam_doc_path": ["", ""],
        "major_exam_date": ["", "2024-02-10"],
        "major_exam_validator": ["", "adviser2"],
        # PhD specific: Qualifying exam
        "qualifying_exam_status": ["N/A", "Passed"],
        "qualifying_exam_doc_path": ["", ""],
        "qualifying_exam_date": ["", "2023-12-01"],
        # POS after qualifying (PhD)
        "pos_phd_status": ["N/A", "Approved"],
        "pos_phd_doc_path": ["", ""],
        # Thesis/dissertation detailed
        "proposal_approved_date": ["", "2024-01-10"],
        "manuscript_progress": [0, 50],
        "external_review_status": ["Not Started", "Not Started"],
        "thesis_docs": ["[]", "[]"],
        # Final defense
        "defense_status": ["Pending", "Pending"],
        "defense_result": ["", ""],
        "negative_votes": [0, 0],
        "defense_date": ["", ""],
        # Manuscript & publication
        "final_manuscript_pdf": ["", ""],
        "final_manuscript_word": ["", ""],
        "publication_upload": ["", ""],
        "manuscript_complete": ["No", "No"],
        # Graduation clearance
        "clearance_status": ["Not Cleared", "Not Cleared"],
        "clearance_date": ["", ""],
        "cleared_by": ["", ""],
        # Existing fields
        "pos_status": ["Approved", "Approved"],
        "pos_submitted_date": ["", ""],
        "pos_approved_date": ["", ""],
        "gwa": [1.75, 1.85],
        "total_units_taken": [12, 18],
        "total_units_required": [32, 37],
        "thesis_units_taken": [3, 8],
        "thesis_units_limit": [6, 12],
        "thesis_outline_approved": ["No", "Yes"],
        "thesis_outline_approved_date": ["", "2024-01-10"],
        "thesis_status": ["In Progress", "Draft with Adviser"],
        "written_comprehensive_status": ["N/A", "Passed"],
        "written_comprehensive_passed_date": ["", "2024-02-10"],
        "oral_comprehensive_status": ["N/A", "Pending"],
        "oral_comprehensive_passed_date": ["", ""],
        "general_exam_status": ["Pending", "N/A"],
        "general_exam_passed_date": ["", ""],
        "final_exam_status": ["Pending", "Pending"],
        "final_exam_passed_date": ["", ""],
        "residency_years_used": [1, 2],
        "residency_max_years": [5, 7],
        "extension_count": [0, 0],
        "extension_end_date": ["", ""],
        "loa_start_date": ["", ""],
        "loa_end_date": ["", ""],
        "loa_total_terms": [0, 0],
        "awol_status": ["No", "No"],
        "awol_lifted_date": ["", ""],
        "transfer_units_approved": [0, 0],
        "graduation_applied": ["No", "No"],
        "graduation_approved": ["No", "No"],
        "graduation_date": ["", ""],
        "re_admission_status": ["Not Applicable", "Not Applicable"],
        "re_admission_date": ["", ""]
    })

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = create_default_data()
    
    # Add missing columns from default
    default_df = create_default_data()
    for col in default_df.columns:
        if col not in df.columns:
            df[col] = default_df[col]
    
    # Ensure JSON columns are valid
    for col in ["notifications", "semester_records", "thesis_docs"]:
        for idx in df.index:
            val = df.at[idx, col]
            if pd.isna(val) or val == "" or (isinstance(val, str) and val.strip() == ""):
                df.at[idx, col] = "[]"
            else:
                try:
                    json.loads(val)
                except:
                    df.at[idx, col] = "[]"
    
    # Convert numeric columns
    numeric_int = ["ay_start", "total_units_taken", "total_units_required", "thesis_units_taken",
                   "thesis_units_limit", "residency_years_used", "residency_max_years", "extension_count",
                   "loa_total_terms", "transfer_units_approved", "negative_votes", "manuscript_progress"]
    for col in numeric_int:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    df["gwa"] = pd.to_numeric(df["gwa"], errors='coerce').fillna(2.0).astype(float)
    
    # Recompute program-specific values and committee deadline
    for idx, row in df.iterrows():
        prog = row["program"]
        if prog not in PROGRAMS:
            prog = PROGRAMS[0]
            df.at[idx, "program"] = prog
        track = row.get("phd_track", "")
        req = get_required_units(prog, track if track in PhD_TRACKS else None)
        df.at[idx, "total_units_required"] = req
        df.at[idx, "residency_max_years"] = get_residency_max_from_program(prog)
        df.at[idx, "thesis_units_limit"] = get_thesis_limit_from_program(prog)
        
        # Set committee deadline (2 months after start) - fixed date logic
        start = get_start_date(row["ay_start"], row["semester"])
        deadline = start + timedelta(days=60)
        df.at[idx, "committee_deadline"] = deadline.strftime("%Y-%m-%d")
    
    # Build name from components if needed
    if "last_name" in df.columns and "first_name" in df.columns:
        def build_name(r):
            last = str(r.get("last_name", "")).strip()
            first = str(r.get("first_name", "")).strip()
            middle = str(r.get("middle_name", "")).strip()
            if last and first:
                return f"{last}, {first}" + (f" {middle}" if middle else "")
            return r.get("name", "")
        df["name"] = df.apply(build_name, axis=1)
    
    df.to_csv(DATA_FILE, index=False)
    return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()

# ==================== HELPER FUNCTIONS ====================
def compute_milestone_progress(student):
    """Return percentage of completed milestones based on role."""
    milestones = {
        "Admission": student["admission_status"] == "Approved",
        "Committee Formation": student["committee_status"] == "Approved",
        "Coursework (50%)": student["total_units_taken"] >= student["total_units_required"] * 0.5,
        "Major Exam": student["major_exam_status"] == "Passed",
        "Thesis Proposal": student.get("proposal_approved_date", "") != "",
        "Final Defense": student["defense_status"] == "Passed",
        "Manuscript Submitted": student["manuscript_complete"] == "Yes",
        "Graduation Cleared": student["clearance_status"] == "Cleared"
    }
    if is_phd_program(student["program"]):
        milestones["Qualifying Exam"] = student["qualifying_exam_status"] == "Passed"
        milestones["POS after Qualifying"] = student["pos_phd_status"] == "Approved"
    else:
        milestones["POS (Coursework)"] = student["pos_status"] == "Approved"
    
    completed = sum(milestones.values())
    total = len(milestones)
    return int(completed / total * 100) if total else 0, milestones

def check_deadline_alerts(student):
    alerts = []
    today = date.today()
    # Committee deadline
    if student["committee_status"] not in ["Approved", "Rejected"]:
        deadline = student.get("committee_deadline", "")
        if deadline:
            try:
                d = datetime.strptime(deadline, "%Y-%m-%d").date()
                if today > d:
                    alerts.append(f"📌 Committee formation overdue (deadline: {deadline})")
                elif (d - today).days <= 14:
                    alerts.append(f"⚠️ Committee formation deadline approaching: {deadline}")
            except:
                pass
    # Admission pending validation
    if student["admission_status"] == "Pending":
        alerts.append("📌 Admission validation pending")
    # Major exam eligibility
    if student["major_exam_status"] == "Pending" and student["total_units_taken"] >= student["total_units_required"]:
        if student["gwa"] <= 2.0:
            alerts.append("✅ You are eligible for major exam. Please request scheduling.")
        else:
            alerts.append("⚠️ GWA above 2.0 – not eligible for major exam yet.")
    return alerts

def get_eligibility_for_major_exam(student):
    required_units = student["total_units_required"]
    taken = student["total_units_taken"]
    gwa_ok = student["gwa"] <= 2.0
    if taken >= required_units and gwa_ok:
        return True, "Eligible: coursework complete and GWA ≤ 2.0"
    else:
        reasons = []
        if taken < required_units:
            reasons.append(f"Insufficient units ({taken}/{required_units})")
        if not gwa_ok:
            reasons.append(f"GWA too high ({student['gwa']:.2f} > 2.0)")
        return False, "; ".join(reasons)

def get_early_warning_indicators(row):
    warnings = []
    if row["gwa"] > 2.0:
        warnings.append(f"⚠️ High GWA: {row['gwa']:.2f}")
    if row["thesis_units_taken"] > row["thesis_units_limit"]:
        warnings.append(f"⚠️ Exceeded thesis units: {row['thesis_units_taken']}/{row['thesis_units_limit']}")
    if row["defense_status"] == "Failed":
        warnings.append("⚠️ Final defense failed")
    if row["clearance_status"] != "Cleared" and row["defense_status"] == "Passed":
        warnings.append("📌 Graduation clearance pending")
    return warnings

# ==================== LOGIN ====================
if not st.session_state.logged_in:
    st.title("🔐 SESAM KMIS Login")
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
    with col2:
        st.caption("Demo accounts:")
        st.caption("staff1 / admin123 | adviser1 / adv123 | student1 / stu123")
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

# ==================== SIDEBAR ====================
st.sidebar.title("🎓 KMIS Workflow")
st.sidebar.write(f"👤 {st.session_state.display_name} ({st.session_state.role})")
if st.sidebar.button("Logout"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
st.sidebar.markdown("---")
st.sidebar.caption("Milestone‑based workflow | UPLB Graduate School Rules")

# ==================== MAIN APP ====================
st.title("🎓 SESAM Graduate Student Milestone Workflow")
st.markdown("*Track every stage from admission to graduation with automated validations and alerts*")

role = st.session_state.role

# ==================== STAFF VIEW ====================
if role == "SESAM Staff":
    st.subheader("📊 Staff Dashboard – All Students")
    search = st.text_input("🔍 Search by name or student number")
    if search:
        filtered = df[df["name"].str.contains(search, case=False) | df["student_number"].str.contains(search, case=False)]
    else:
        filtered = df.copy()
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Students", len(df))
    col2.metric("Pending Admissions", len(df[df["admission_status"]=="Pending"]))
    col3.metric("Pending Clearance", len(df[(df["defense_status"]=="Passed") & (df["clearance_status"]!="Cleared")]))
    col4.metric("Graduated", len(df[df["graduation_approved"]=="Yes"]))
    
    st.dataframe(filtered[["student_number","name","program","advisor","admission_status","committee_status","major_exam_status","defense_status","clearance_status"]], use_container_width=True)
    
    # Student selection for detailed management
    st.markdown("---")
    student_choice = st.selectbox("Select student to manage", filtered["name"].tolist() if len(filtered)>0 else ["No students"])
    if student_choice and student_choice != "No students":
        student = filtered[filtered["name"]==student_choice].iloc[0]
        st.subheader(f"Managing: {student['name']} ({student['student_number']})")
        
        # Progress bar
        progress, milestones = compute_milestone_progress(student)
        st.progress(progress/100, text=f"Overall Progress: {progress}%")
        cols = st.columns(len(milestones))
        for i, (name, done) in enumerate(milestones.items()):
            cols[i].metric(name, "✅" if done else "⏳")
        
        # Tabs for each milestone
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
            ["Admission", "Committee", "Coursework", "Exams", "Thesis/Defense", "Manuscript", "Clearance"])
        
        with tab1:
            st.subheader("Admission & Registration")
            st.write(f"Status: **{student['admission_status']}**")
            if student["admission_letter_path"] and os.path.exists(student["admission_letter_path"]):
                with open(student["admission_letter_path"], "rb") as f:
                    st.download_button("Download Admission Letter", f, file_name="admission_letter.pdf")
            if student["admission_status"] == "Pending":
                new_status = st.selectbox("Validate Admission", ["Approved", "Rejected"])
                if st.button("Submit Validation"):
                    df.loc[df["student_number"]==student["student_number"], "admission_status"] = new_status
                    df.loc[df["student_number"]==student["student_number"], "admission_validator"] = st.session_state.username
                    df.loc[df["student_number"]==student["student_number"], "admission_validation_date"] = date.today().isoformat()
                    save_data(df)
                    add_notification(df, student["student_number"], st.session_state.display_name,
                                     f"Your admission has been {new_status.lower()}.", "Validation")
                    st.success(f"Admission {new_status}")
                    st.rerun()
            else:
                st.info(f"Validated by {student['admission_validator']} on {student['admission_validation_date']}")
        
        with tab2:
            st.subheader("Advisory Committee Formation")
            st.write(f"Status: **{student['committee_status']}**")
            st.write(f"Deadline: {student['committee_deadline']}")
            if student["committee_doc_path"] and os.path.exists(student["committee_doc_path"]):
                with open(student["committee_doc_path"], "rb") as f:
                    st.download_button("Download Committee Document", f)
            if student["committee_status"] == "Pending":
                new_status = st.selectbox("Validate Committee", ["Approved", "Rejected"])
                if st.button("Update Committee Status"):
                    df.loc[df["student_number"]==student["student_number"], "committee_status"] = new_status
                    df.loc[df["student_number"]==student["student_number"], "committee_validation_by"] = st.session_state.username
                    save_data(df)
                    add_notification(df, student["student_number"], st.session_state.display_name,
                                     f"Committee formation {new_status.lower()}.", "Milestone")
                    st.success("Updated")
                    st.rerun()
        
        with tab3:
            st.subheader("Coursework & Grades (Per Semester)")
            sem_records = json.loads(student["semester_records"])
            if sem_records:
                for i, rec in enumerate(sem_records):
                    with st.expander(f"{rec.get('semester', 'Semester')} - GWA: {rec.get('gwa','')}"):
                        st.write(f"Units taken: {rec.get('units_taken',0)} | Passed: {rec.get('units_passed',0)}")
                        if rec.get("amis_path") and os.path.exists(rec["amis_path"]):
                            st.image(rec["amis_path"], width=200)
                        if rec.get("grades_path") and os.path.exists(rec["grades_path"]):
                            with open(rec["grades_path"], "rb") as f:
                                st.download_button(f"Download Grades Screenshot {i}", f)
            else:
                st.info("No semester records yet.")
        
        with tab4:
            st.subheader("Major Examination")
            if is_master_program(student["program"]):
                st.write("Master's General Examination")
            else:
                st.write("PhD Comprehensive Examination")
            st.write(f"Status: {student['major_exam_status']}")
            eligible, reason = get_eligibility_for_major_exam(student)
            if eligible:
                st.success(reason)
            else:
                st.warning(reason)
            if student["major_exam_doc_path"] and os.path.exists(student["major_exam_doc_path"]):
                with open(student["major_exam_doc_path"], "rb") as f:
                    st.download_button("Download Exam Result", f)
            if student["major_exam_status"] == "Pending" and eligible:
                new_status = st.selectbox("Validate Exam Result", ["Passed", "Failed"])
                if st.button("Record Exam Result"):
                    df.loc[df["student_number"]==student["student_number"], "major_exam_status"] = new_status
                    df.loc[df["student_number"]==student["student_number"], "major_exam_date"] = date.today().isoformat()
                    df.loc[df["student_number"]==student["student_number"], "major_exam_validator"] = st.session_state.username
                    save_data(df)
                    add_notification(df, student["student_number"], st.session_state.display_name,
                                     f"Major examination result: {new_status}", "Exam")
                    st.success(f"Exam marked {new_status}")
                    st.rerun()
        
        with tab5:
            st.subheader("Thesis/Dissertation & Final Defense")
            st.write(f"Proposal approved: {student.get('proposal_approved_date', 'Not yet')}")
            st.write(f"Manuscript progress: {student.get('manuscript_progress',0)}%")
            defense_status = student["defense_status"]
            st.write(f"Final Defense: {defense_status}")
            if defense_status == "Passed":
                st.write(f"Result: {student['defense_result']} | Negative votes: {student['negative_votes']}")
                if student['negative_votes'] > 1:
                    st.error("⚠️ More than one negative vote – rule violation.")
            if defense_status != "Passed":
                result = st.selectbox("Update Defense Result", ["Passed", "Failed"])
                neg_votes = st.number_input("Number of negative votes", 0, 5, 0)
                if st.button("Record Defense"):
                    if neg_votes > 1:
                        st.error("Cannot pass with more than 1 negative vote.")
                    else:
                        df.loc[df["student_number"]==student["student_number"], "defense_status"] = result
                        df.loc[df["student_number"]==student["student_number"], "defense_result"] = result
                        df.loc[df["student_number"]==student["student_number"], "negative_votes"] = neg_votes
                        df.loc[df["student_number"]==student["student_number"], "defense_date"] = date.today().isoformat()
                        save_data(df)
                        add_notification(df, student["student_number"], st.session_state.display_name,
                                         f"Final defense result: {result}", "Defense")
                        st.success("Updated")
                        st.rerun()
        
        with tab6:
            st.subheader("Final Manuscript & Publication")
            if student["final_manuscript_pdf"] and os.path.exists(student["final_manuscript_pdf"]):
                with open(student["final_manuscript_pdf"], "rb") as f:
                    st.download_button("Download Final Manuscript (PDF)", f)
            if student["publication_upload"] and os.path.exists(student["publication_upload"]):
                with open(student["publication_upload"], "rb") as f:
                    st.download_button("Download Publication-ready Article", f)
            if st.button("Mark Manuscript Complete"):
                df.loc[df["student_number"]==student["student_number"], "manuscript_complete"] = "Yes"
                save_data(df)
                st.success("Manuscript submission recorded")
                st.rerun()
        
        with tab7:
            st.subheader("Graduation Clearance")
            st.write(f"Clearance Status: {student['clearance_status']}")
            if student["clearance_status"] != "Cleared" and student["defense_status"] == "Passed" and student["manuscript_complete"] == "Yes":
                if st.button("Grant Clearance"):
                    df.loc[df["student_number"]==student["student_number"], "clearance_status"] = "Cleared"
                    df.loc[df["student_number"]==student["student_number"], "clearance_date"] = date.today().isoformat()
                    df.loc[df["student_number"]==student["student_number"], "cleared_by"] = st.session_state.username
                    save_data(df)
                    add_notification(df, student["student_number"], st.session_state.display_name,
                                     "You are cleared for graduation!", "Clearance")
                    st.success("Student cleared for graduation")
                    st.rerun()
            elif student["clearance_status"] == "Cleared":
                st.success(f"Cleared on {student['clearance_date']} by {student['cleared_by']}")

# ==================== ADVISER VIEW ====================
elif role == "Faculty Adviser":
    st.subheader(f"👨‍🏫 Your Advisees")
    advisees = df[df["advisor"] == st.session_state.display_name]
    if len(advisees) == 0:
        st.warning("No students assigned.")
    else:
        search_adv = st.text_input("🔍 Search among your advisees")
        if search_adv:
            advisees = advisees[advisees["name"].str.contains(search_adv, case=False)]
        st.dataframe(advisees[["student_number","name","program","admission_status","committee_status","major_exam_status","defense_status"]])
        
        for _, student in advisees.iterrows():
            with st.expander(f"📘 {student['name']} – {student['student_number']}"):
                progress, _ = compute_milestone_progress(student)
                st.progress(progress/100, text=f"Overall progress: {progress}%")
                alerts = check_deadline_alerts(student)
                for alert in alerts:
                    st.warning(alert)
                # Adviser can validate committee and major exam
                if student["committee_status"] == "Pending":
                    if st.button(f"Approve Committee for {student['name']}", key=f"comm_{student['student_number']}"):
                        df.loc[df["student_number"]==student["student_number"], "committee_status"] = "Approved"
                        df.loc[df["student_number"]==student["student_number"], "committee_validation_by"] = st.session_state.username
                        save_data(df)
                        add_notification(df, student["student_number"], st.session_state.display_name, "Your committee has been approved.", "Milestone")
                        st.rerun()
                if student["major_exam_status"] == "Pending":
                    eligible, reason = get_eligibility_for_major_exam(student)
                    if eligible:
                        new_status = st.radio(f"Major Exam Result for {student['name']}", ["Passed","Failed"], key=f"exam_{student['student_number']}")
                        if st.button(f"Submit Exam Result", key=f"submit_exam_{student['student_number']}"):
                            df.loc[df["student_number"]==student["student_number"], "major_exam_status"] = new_status
                            df.loc[df["student_number"]==student["student_number"], "major_exam_date"] = date.today().isoformat()
                            df.loc[df["student_number"]==student["student_number"], "major_exam_validator"] = st.session_state.username
                            save_data(df)
                            add_notification(df, student["student_number"], st.session_state.display_name, f"Your major exam result: {new_status}", "Exam")
                            st.rerun()
                # Send notification
                with st.form(key=f"notif_{student['student_number']}"):
                    msg = st.text_area("Send message to student")
                    if st.form_submit_button("Send"):
                        if msg.strip():
                            df = add_notification(df, student["student_number"], st.session_state.display_name, msg)
                            save_data(df)
                            st.success("Sent")
                            st.rerun()
        st.info("You can validate committee approvals, exam results, and send notifications.")

# ==================== STUDENT VIEW ====================
elif role == "Student":
    student_row = df[df["student_number"] == st.session_state.student_number].iloc[0] if st.session_state.student_number else None
    if student_row is None:
        st.error("Student record not found.")
        st.stop()
    
    st.subheader(f"🎓 Welcome, {student_row['name']}")
    # Notifications
    notifs = get_notifications(student_row)
    if notifs:
        st.markdown("### 📬 Notifications")
        for i, n in enumerate(notifs):
            st.info(f"**{n['type']}** from {n['from']} at {n['timestamp']}\n\n{n['message']}")
            if st.button(f"Dismiss", key=f"dismiss_{i}"):
                df = dismiss_notification(df, student_row["student_number"], i)
                save_data(df)
                st.rerun()
    
    # Progress dashboard
    progress, milestones = compute_milestone_progress(student_row)
    st.markdown("### Your Milestone Progress")
    st.progress(progress/100, text=f"{progress}% complete")
    cols = st.columns(4)
    for i, (name, done) in enumerate(milestones.items()):
        cols[i%4].metric(name, "✅" if done else "⌛")
    
    # Alerts
    alerts = check_deadline_alerts(student_row)
    for alert in alerts:
        st.error(alert)
    early_warnings = get_early_warning_indicators(student_row)
    for warn in early_warnings:
        st.warning(warn)
    
    # Tabs for student actions
    st.markdown("---")
    tab_admit, tab_cmt, tab_course, tab_exam, tab_thesis, tab_manu = st.tabs(
        ["Admission", "Committee", "Coursework & Grades", "Exams", "Thesis/Defense", "Manuscript"])
    
    with tab_admit:
        st.subheader("Upload Admission Acceptance Letter")
        uploaded = st.file_uploader("Upload PDF/JPG", type=["pdf","jpg","jpeg","png"])
        if uploaded:
            path = save_uploaded_file("admission_letters", student_row["student_number"], uploaded, "admission")
            if path:
                df.loc[df["student_number"]==student_row["student_number"], "admission_letter_path"] = path
                # If adviser assigned, set pending adviser validation; else staff
                if student_row["advisor"] and student_row["advisor"] != "Not assigned":
                    df.loc[df["student_number"]==student_row["student_number"], "admission_status"] = "Pending"
                    add_notification(df, student_row["student_number"], "System", "Your admission letter is pending adviser validation.")
                else:
                    df.loc[df["student_number"]==student_row["student_number"], "admission_status"] = "Pending"
                    add_notification(df, student_row["student_number"], "System", "Your admission letter is pending staff validation.")
                save_data(df)
                st.success("Admission letter uploaded. Awaiting validation.")
                st.rerun()
        st.info(f"Current status: {student_row['admission_status']}")
    
    with tab_cmt:
        st.subheader("Advisory Committee Formation")
        st.write(f"Deadline: {student_row['committee_deadline']}")
        st.write(f"Status: {student_row['committee_status']}")
        uploaded_cmt = st.file_uploader("Upload approved committee document", type=["pdf","jpg","jpeg","png"], key="cmt")
        if uploaded_cmt:
            path = save_uploaded_file("committee_docs", student_row["student_number"], uploaded_cmt, "committee")
            if path:
                df.loc[df["student_number"]==student_row["student_number"], "committee_doc_path"] = path
                df.loc[df["student_number"]==student_row["student_number"], "committee_status"] = "Pending"
                save_data(df)
                add_notification(df, student_row["student_number"], "System", "Committee document uploaded. Pending adviser validation.")
                st.success("Document uploaded. Waiting for validation.")
                st.rerun()
    
    with tab_course:
        st.subheader("Semester Coursework & Grades")
        sem_records = json.loads(student_row["semester_records"])
        if sem_records:
            for rec in sem_records:
                st.write(f"**{rec['semester']}** – GWA: {rec['gwa']}, Units: {rec['units_taken']} taken, {rec['units_passed']} passed")
        with st.form("new_semester"):
            sem_name = st.text_input("Semester (e.g., 1st Sem 2025-2026)")
            amis_file = st.file_uploader("AMIS Screenshot (subjects enrolled)", type=["jpg","jpeg","png"], key="amis")
            grades_file = st.file_uploader("Grades Screenshot (end of semester)", type=["jpg","jpeg","png"], key="grades")
            gwa = st.number_input("GWA", 1.0, 5.0, 1.75, step=0.01)
            units_taken = st.number_input("Total units taken this semester", 0, 20, 9)
            units_passed = st.number_input("Units passed", 0, 20, 9)
            if st.form_submit_button("Submit Semester Record"):
                amis_path = save_uploaded_file("amis_screenshots", student_row["student_number"], amis_file, f"amis_{sem_name}") if amis_file else ""
                grades_path = save_uploaded_file("coursework_grades", student_row["student_number"], grades_file, f"grades_{sem_name}") if grades_file else ""
                new_record = {
                    "semester": sem_name,
                    "amis_path": amis_path,
                    "grades_path": grades_path,
                    "gwa": gwa,
                    "units_taken": units_taken,
                    "units_passed": units_passed
                }
                sem_records.append(new_record)
                df.loc[df["student_number"]==student_row["student_number"], "semester_records"] = json.dumps(sem_records)
                # Update cumulative totals
                total_units = sum(r["units_taken"] for r in sem_records)
                df.loc[df["student_number"]==student_row["student_number"], "total_units_taken"] = total_units
                # Update GWA as average of recorded semesters (simple average)
                if sem_records:
                    avg_gwa = sum(r["gwa"] for r in sem_records) / len(sem_records)
                    df.loc[df["student_number"]==student_row["student_number"], "gwa"] = avg_gwa
                save_data(df)
                st.success("Semester record saved. Adviser can validate later.")
                st.rerun()
    
    with tab_exam:
        st.subheader("Major Examination")
        if is_master_program(student_row["program"]):
            st.write("**Master's General Examination**")
        else:
            st.write("**PhD Comprehensive Examination**")
        eligible, reason = get_eligibility_for_major_exam(student_row)
        if eligible:
            st.success(reason)
            exam_file = st.file_uploader("Upload exam result (signed result form)", type=["pdf","jpg","jpeg","png"])
            if exam_file:
                path = save_uploaded_file("exam_results", student_row["student_number"], exam_file, "major_exam")
                if path:
                    df.loc[df["student_number"]==student_row["student_number"], "major_exam_doc_path"] = path
                    df.loc[df["student_number"]==student_row["student_number"], "major_exam_status"] = "Pending"
                    save_data(df)
                    add_notification(df, student_row["student_number"], "System", "Exam result uploaded. Pending validation.")
                    st.success("Result uploaded.")
                    st.rerun()
        else:
            st.warning(reason)
        st.write(f"Current exam status: {student_row['major_exam_status']}")
    
    with tab_thesis:
        st.subheader("Thesis/Dissertation Tracking")
        st.write(f"Proposal approved date: {student_row.get('proposal_approved_date', 'Not yet')}")
        st.write(f"Manuscript progress: {student_row.get('manuscript_progress',0)}%")
        new_progress = st.slider("Update manuscript progress (%)", 0, 100, int(student_row.get("manuscript_progress",0)))
        if st.button("Update Progress"):
            df.loc[df["student_number"]==student_row["student_number"], "manuscript_progress"] = new_progress
            save_data(df)
            st.success("Progress updated")
            st.rerun()
        if student_row.get("defense_status") != "Passed":
            if st.button("Request Final Defense Scheduling"):
                add_notification(df, student_row["student_number"], st.session_state.display_name,
                                 "Final defense requested. Please coordinate with your committee.", "Request")
                st.success("Request sent to adviser.")
    
    with tab_manu:
        st.subheader("Final Manuscript & Publication Submission")
        pdf_file = st.file_uploader("Final Manuscript (PDF)", type=["pdf"])
        word_file = st.file_uploader("Final Manuscript (Word)", type=["docx"])
        pub_file = st.file_uploader("Publication-ready article", type=["pdf","docx"])
        if st.button("Submit Manuscripts"):
            if pdf_file:
                path_pdf = save_uploaded_file("manuscripts", student_row["student_number"], pdf_file, "final_pdf")
                if path_pdf:
                    df.loc[df["student_number"]==student_row["student_number"], "final_manuscript_pdf"] = path_pdf
            if word_file:
                path_word = save_uploaded_file("manuscripts", student_row["student_number"], word_file, "final_word")
                if path_word:
                    df.loc[df["student_number"]==student_row["student_number"], "final_manuscript_word"] = path_word
            if pub_file:
                path_pub = save_uploaded_file("manuscripts", student_row["student_number"], pub_file, "publication")
                if path_pub:
                    df.loc[df["student_number"]==student_row["student_number"], "publication_upload"] = path_pub
            if pdf_file or word_file or pub_file:
                df.loc[df["student_number"]==student_row["student_number"], "manuscript_complete"] = "Yes"
                save_data(df)
                add_notification(df, student_row["student_number"], "System", "Manuscript submitted. Awaiting clearance.")
                st.success("Manuscripts submitted!")
                st.rerun()
    
    st.markdown("---")
    st.caption("Need to update profile picture or AMIS screenshot? Use the sidebar (if available) or contact staff.")

# ==================== FOOTER ====================
st.markdown("---")
st.caption("SESAM KMIS – Full Milestone Workflow with Role‑Based Validation | UPLB Graduate School Rules")
