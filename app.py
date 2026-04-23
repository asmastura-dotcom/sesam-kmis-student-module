import streamlit as st
import pandas as pd
from datetime import datetime

# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="SESAM Student Module", page_icon="🎓", layout="wide")

# ==================== INITIALIZE SESSION STATE ====================
if "students" not in st.session_state:
    st.session_state.students = []  # list of dicts with full student records

if "logged_in" not in st.session_state:
    st.session_state.logged_in = True  # skip login for prototype

# ==================== PROGRAM LIST (from ISSP) ====================
PROGRAMS = [
    "MS Environmental Science",
    "PhD Environmental Science",
    "PhD Environmental Diplomacy and Negotiations",
    "Master in Resilience Studies (M-ReS)",
    "Professional Masters in Tropical Marine Ecosystems Management (PM-TMEM)"
]

def get_thesis_limit(program):
    """Return thesis units limit based on program (6 for master's, 12 for doctoral)"""
    if program.startswith("MS") or program.startswith("Master") or program.startswith("Professional Masters"):
        return 6
    else:
        return 12

def get_residency_max(program):
    """Return max residency years (5 for master's, 7 for PhD)"""
    if program.startswith("MS") or program.startswith("Master") or program.startswith("Professional Masters"):
        return 5
    else:
        return 7

def get_all_warnings(student):
    """Return list of warning messages based on student data"""
    warnings = []
    limit = get_thesis_limit(student["program"])
    if student.get("thesis_units_taken", 0) > limit:
        warnings.append(f"⚠️ Thesis units exceeded: {student['thesis_units_taken']}/{limit} (exceeded by {student['thesis_units_taken'] - limit})")
    if student.get("gwa", 2.0) > 2.0:
        warnings.append(f"⚠️ GWA {student['gwa']:.2f} is below 2.00 – may affect exam eligibility and graduation")
    if student.get("pos_status", "Not Filed") not in ["Approved", "Completed"]:
        warnings.append("⚠️ Plan of Study (POS) not yet approved")
    if student.get("final_exam_status", "Not Taken") != "Passed":
        warnings.append("⚠️ Final examination not yet passed")
    return warnings if warnings else ["✅ All rules satisfied"]

# ==================== SIDEBAR ====================
st.sidebar.title("SESAM KMIS")
st.sidebar.markdown("### Student Module")
st.sidebar.info(
    "**ISSP 2026-2031**\n\n"
    "Knowledge Management Information System\n"
    "Student Lifecycle Management"
)
st.sidebar.markdown("---")
st.sidebar.caption("Version 1.3 | Prototype for SESAM")

# ==================== MAIN TITLE ====================
st.title("🎓 SESAM Student Module")
st.markdown("Register and track graduate students – name format: **Last, First Middle**")

# ==================== FORM TO ADD STUDENT (expanded) ====================
with st.expander("➕ Register New Student", expanded=True):
    with st.form(key="add_student_form"):
        # Personal info
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
        
        col6, col7 = st.columns(2)
        with col6:
            year_admitted = st.number_input("Year Admitted", min_value=2000, max_value=2030, value=2026, step=1)
        with col7:
            advisor = st.text_input("Advisor (optional)", placeholder="Dr. Faustino-Eslava")
        
        st.markdown("---")
        st.markdown("### Initial Milestone Status (optional)")
        col8, col9, col10 = st.columns(3)
        with col8:
            gwa = st.number_input("Initial GWA", min_value=1.0, max_value=5.0, step=0.01, value=2.0, help="1.0 best, 5.0 failing")
        with col9:
            thesis_units_taken = st.number_input("Thesis Units Taken", min_value=0, max_value=20, step=1, value=0)
        with col10:
            pos_status = st.selectbox("POS Status", ["Not Filed", "Pending", "Approved"])
        
        col11, col12, col13 = st.columns(3)
        with col11:
            comp_exam = st.selectbox("Comprehensive Exam (PhD)", ["N/A", "Not Taken", "Passed", "Failed"])
        with col12:
            general_exam = st.selectbox("General Exam (MS)", ["N/A", "Not Taken", "Passed", "Failed"])
        with col13:
            final_exam = st.selectbox("Final Exam Status", ["Not Taken", "Passed", "Failed"])
        
        submitted = st.form_submit_button("Register Student")
        
        if submitted:
            if not last_name or not first_name or not student_number or not program:
                st.error("Please fill all required fields (*).")
            elif any(s["student_number"] == student_number for s in st.session_state.students):
                st.error("Student number already exists. Please use a unique number.")
            else:
                # Create full student record
                new_student = {
                    "id": len(st.session_state.students) + 1,
                    "last_name": last_name.strip(),
                    "first_name": first_name.strip(),
                    "middle_name": middle_name.strip() if middle_name else "",
                    "student_number": student_number.strip(),
                    "program": program,
                    "year_admitted": year_admitted,
                    "advisor": advisor.strip() if advisor else "Not assigned",
                    "registered_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    # Milestone fields
                    "gwa": gwa,
                    "thesis_units_taken": thesis_units_taken,
                    "pos_status": pos_status,
                    "comp_exam_status": comp_exam,
                    "general_exam_status": general_exam,
                    "final_exam_status": final_exam,
                    "thesis_outline_approved": "No",
                    "thesis_status": "Not Started",
                    "residency_years_used": 0,
                    "awol_status": "No",
                    "loa_total_terms": 0,
                    "graduation_applied": "No"
                }
                st.session_state.students.append(new_student)
                st.success(f"✅ Student {last_name}, {first_name} registered successfully!")
                st.rerun()

# ==================== DISPLAY STUDENT LIST ====================
st.markdown("---")
st.subheader(f"📋 Registered Students ({len(st.session_state.students)})")

if len(st.session_state.students) == 0:
    st.info("No students registered yet. Use the form above to add students.")
else:
    # Convert to DataFrame for display
    df = pd.DataFrame(st.session_state.students)
    
    # Create formatted name column
    df["full_name"] = df.apply(
        lambda row: f"{row['last_name']}, {row['first_name']}" + 
                    (f" {row['middle_name']}" if row['middle_name'] else ""),
        axis=1
    )
    
    # Add thesis limit column
    df["thesis_units_limit"] = df["program"].apply(get_thesis_limit)
    
    # Add warning summary (optional)
    df["warnings"] = df.apply(get_all_warnings, axis=1)
    
    # Select columns to display
    display_cols = ["full_name", "student_number", "program", "year_admitted", "advisor", 
                    "gwa", "thesis_units_taken", "thesis_units_limit", "pos_status", 
                    "final_exam_status", "warnings", "registered_on"]
    display_df = df[display_cols].rename(columns={
        "full_name": "Name",
        "student_number": "Student No.",
        "program": "Program",
        "year_admitted": "Year",
        "advisor": "Advisor",
        "gwa": "GWA",
        "thesis_units_taken": "Thesis Units",
        "thesis_units_limit": "Limit",
        "pos_status": "POS",
        "final_exam_status": "Final Exam",
        "warnings": "Status",
        "registered_on": "Registered"
    })
    
    st.dataframe(display_df, use_container_width=True, height=400)
    
    # ==================== EDIT STUDENT MILESTONES ====================
    st.markdown("---")
    st.subheader("✏️ Update Student Milestones")
    student_names = df["full_name"].tolist()
    selected_name = st.selectbox("Select Student", student_names)
    student = df[df["full_name"] == selected_name].iloc[0].to_dict()
    
    with st.form("update_student_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            new_gwa = st.number_input("GWA", min_value=1.0, max_value=5.0, step=0.01, value=float(student["gwa"]))
        with col2:
            new_thesis_units = st.number_input("Thesis Units Taken", min_value=0, max_value=20, step=1, value=int(student["thesis_units_taken"]))
        with col3:
            new_pos = st.selectbox("POS Status", ["Not Filed", "Pending", "Approved"], index=["Not Filed","Pending","Approved"].index(student["pos_status"]))
        
        col4, col5, col6 = st.columns(3)
        with col4:
            new_comp = st.selectbox("Comprehensive Exam (PhD)", ["N/A","Not Taken","Passed","Failed"], index=["N/A","Not Taken","Passed","Failed"].index(student["comp_exam_status"]))
        with col5:
            new_general = st.selectbox("General Exam (MS)", ["N/A","Not Taken","Passed","Failed"], index=["N/A","Not Taken","Passed","Failed"].index(student["general_exam_status"]))
        with col6:
            new_final = st.selectbox("Final Exam", ["Not Taken","Passed","Failed"], index=["Not Taken","Passed","Failed"].index(student["final_exam_status"]))
        
        col7, col8 = st.columns(2)
        with col7:
            new_outline = st.selectbox("Thesis Outline Approved", ["Yes","No"], index=0 if student["thesis_outline_approved"]=="Yes" else 1)
        with col8:
            new_thesis_status = st.selectbox("Thesis Status", ["Not Started","In Progress","Draft with Adviser","For Committee Review","Approved","Submitted"], index=["Not Started","In Progress","Draft with Adviser","For Committee Review","Approved","Submitted"].index(student["thesis_status"]))
        
        col9, col10 = st.columns(2)
        with col9:
            new_residency = st.number_input("Years of Residence Used", min_value=0, max_value=10, step=1, value=int(student["residency_years_used"]))
        with col10:
            new_awol = st.selectbox("AWOL Status", ["No","Yes"], index=0 if student["awol_status"]=="No" else 1)
        
        if st.form_submit_button("Update Student Record"):
            # Update the student in session_state
            for s in st.session_state.students:
                if s["student_number"] == student["student_number"]:
                    s["gwa"] = new_gwa
                    s["thesis_units_taken"] = new_thesis_units
                    s["pos_status"] = new_pos
                    s["comp_exam_status"] = new_comp
                    s["general_exam_status"] = new_general
                    s["final_exam_status"] = new_final
                    s["thesis_outline_approved"] = new_outline
                    s["thesis_status"] = new_thesis_status
                    s["residency_years_used"] = new_residency
                    s["awol_status"] = new_awol
                    break
            st.success(f"✅ Milestones updated for {selected_name}")
            st.rerun()

# ==================== DATA MANAGEMENT ====================
with st.expander("⚙️ Data Management"):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear All Students", type="primary"):
            st.session_state.students = []
            st.success("All students cleared.")
            st.rerun()
    with col2:
        if len(st.session_state.students) > 0:
            df_download = pd.DataFrame(st.session_state.students)
            csv = df_download.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"sesam_students_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
