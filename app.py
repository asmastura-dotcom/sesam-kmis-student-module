elif role == "Student":
    st.subheader(f"📘 Your Academic Progress ({st.session_state.display_name})")
    
    # Use student_number for reliable lookup
    if st.session_state.student_number:
        student_record = df[df["student_number"] == st.session_state.student_number]
    else:
        # Fallback to name match (for older deployments)
        student_record = df[df["name"] == st.session_state.display_name]
    
    if len(student_record) == 0:
        st.error("Your record was not found. Please contact SESAM Staff to verify your student number.")
        st.stop()
    
    student = student_record.iloc[0]
    # ... rest of student view remains exactly the same ...
