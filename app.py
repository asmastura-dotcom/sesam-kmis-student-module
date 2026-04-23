import streamlit as st
import pandas as pd
from datetime import datetime

# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="SESAM Student Module", page_icon="🎓", layout="wide")

# ==================== INITIALIZE SESSION STATE ====================
if "students" not in st.session_state:
    st.session_state.students = []  # list of dicts

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
    """Return thesis units limit based on program"""
    if "MS" in program:
        return 6
    elif "PhD" in program:
        return 12
    else:
        return 0  # other programs may have capstone

# ==================== SIDEBAR ====================
st.sidebar.title("SESAM KMIS")
st.sidebar.markdown("### Student Module")
st.sidebar.info(
    "**ISSP 2026-2031**\n\n"
    "Knowledge Management Information System\n"
    "Student Lifecycle Management"
)
st.sidebar.markdown("---")
st.sidebar.caption("Version 1.2 | Prototype for SESAM")

# ==================== MAIN TITLE ====================
st.title("🎓 SESAM Student Module")
st.markdown("Register and track graduate students – name format: **Last, First Middle**")

# ==================== FORM TO ADD STUDENT ====================
with st.expander("➕ Register New Student", expanded=True):
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
        
        col6, col7 = st.columns(2)
        with col6:
            year_admitted = st.number_input("Year Admitted", min_value=2000, max_value=2030, value=2026, step=1)
        with col7:
            advisor = st.text_input("Advisor (optional)", placeholder="Dr. Faustino-Eslava")
        
        submitted = st.form_submit_button("Register Student")
        
        if submitted:
            if not last_name or not first_name or not student_number or not program:
                st.error("Please fill all required fields (*).")
            else:
                # Create student record
                new_student = {
                    "id": len(st.session_state.students) + 1,
                    "last_name": last_name.strip(),
                    "first_name": first_name.strip(),
                    "middle_name": middle_name.strip() if middle_name else "",
                    "student_number": student_number.strip(),
                    "program": program,
                    "year_admitted": year_admitted,
                    "advisor": advisor.strip() if advisor else "Not assigned",
                    "registered_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
    
    # Select columns to display
    display_cols = ["full_name", "student_number", "program", "year_admitted", "advisor", "thesis_units_limit", "registered_on"]
    display_df = df[display_cols].rename(columns={
        "full_name": "Name (Last, First Middle)",
        "student_number": "Student No.",
        "program": "Program",
        "year_admitted": "Year",
        "advisor": "Advisor",
        "thesis_units_limit": "Thesis Units Limit",
        "registered_on": "Registered"
    })
    
    st.dataframe(display_df, use_container_width=True)
    
    # Optional: individual cards
    if st.checkbox("Show as cards instead"):
        for _, student in df.iterrows():
            with st.container():
                st.markdown(f"""
                <div style="border-left: 4px solid #2c7da0; padding: 10px; margin: 10px 0; background: #f9f9f9;">
                    <strong>{student['full_name']}</strong><br>
                    📚 {student['program']} | 🆔 {student['student_number']}<br>
                    🗓️ Admitted: {student['year_admitted']} | 👨‍🏫 Advisor: {student['advisor']}<br>
                    📖 Thesis units limit: {get_thesis_limit(student['program'])}
                </div>
                """, unsafe_allow_html=True)

# ==================== OPTIONS TO MANAGE DATA ====================
with st.expander("⚙️ Data Management"):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear All Students", type="primary"):
            st.session_state.students = []
            st.success("All students cleared.")
            st.rerun()
    with col2:
        if len(st.session_state.students) > 0:
            # Download as CSV
            df_download = pd.DataFrame(st.session_state.students)
            csv = df_download.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"sesam_students_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
