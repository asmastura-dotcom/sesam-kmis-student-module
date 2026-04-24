# ==================== ENHANCED ADVISER VIEW (redesigned layout) ====================
elif role == "Faculty Adviser":
    st.subheader(f"👨‍🏫 Your Advisees")
    adviser_name = st.session_state.display_name
    advisees = df[df["advisor"] == adviser_name].copy()
    
    if len(advisees) == 0:
        st.warning(f"You have no students assigned yet. Contact SESAM Staff to assign students to you.")
    else:
        # ---- Dashboard metrics (cards) ----
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
        
        # ---- Detailed student expanders (unchanged) ----
        if len(filtered_advisees) > 0:
            st.markdown("---")
            st.subheader("📌 Detailed Student Progress & Notifications")
            for _, row in filtered_advisees.iterrows():
                with st.expander(f"📘 {row['name']} ({row['student_number']})", expanded=False):
                    # All the existing detailed content remains exactly as before
                    # (profile picture, metrics, early warnings, progress, milestone table, etc.)
                    # .. (copy the entire expander content from your current code) ..
        else:
            st.info("No matching students.")
    st.info("📌 You can send notifications to your advisees. They will see them immediately when they log in.")
