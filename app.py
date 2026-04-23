    # ========== ADD NEW STUDENT ==========
    st.markdown("---")
    st.subheader("➕ Add New Student")
    
    with st.expander("Click to expand and add a new student record"):
        with st.form("add_student_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_id = st.text_input("Student ID (unique)", max_chars=10, help="Example: S011")
                new_name = st.text_input("Full Name", max_chars=50)
                new_program = st.selectbox("Program", ["MS", "PhD"])
                new_advisor = st.selectbox("Advisor Username", ["adviser1", "adviser2"])
                new_year = st.number_input("Year Admitted", min_value=2000, max_value=2030, step=1, value=2025)
            with col2:
                st.markdown("**Initial Milestone Statuses**")
                new_pos = st.selectbox("POS Filed", ["Pending", "Completed"])
                new_compre = st.selectbox("Comprehensive Exam", ["Pending", "Passed", "Failed"])
                new_proposal = st.selectbox("Proposal Defense", ["Pending", "Completed", "Revisions Required"])
                new_thesis_sub = st.selectbox("Thesis Submitted", ["No", "Yes"])
                new_units = st.number_input("Thesis Units Taken", min_value=0, max_value=20, step=1, value=0)
            
            submitted = st.form_submit_button("➕ Add Student")
            
            if submitted:
                # Validation
                if not new_id or not new_name:
                    st.error("❌ Student ID and Name are required.")
                elif new_id in df["student_id"].values:
                    st.error(f"❌ Student ID '{new_id}' already exists. Please use a unique ID.")
                elif new_advisor not in ["adviser1", "adviser2"]:
                    st.error("❌ Invalid advisor username. Use 'adviser1' or 'adviser2'.")
                else:
                    # Create new student row
                    new_row = pd.DataFrame([{
                        "student_id": new_id,
                        "name": new_name,
                        "program": new_program,
                        "advisor_username": new_advisor,
                        "year_admitted": new_year,
                        "pos_filed": new_pos,
                        "comp_exam": new_compre,
                        "proposal_defense": new_proposal,
                        "thesis_submitted": new_thesis_sub,
                        "thesis_units_taken": new_units
                    }])
                    # Append to existing DataFrame
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)
                    st.success(f"✅ Student '{new_name}' (ID: {new_id}) added successfully!")
                    st.rerun()