"""
Generate sample data for SESAM KMIS demonstration.
Run this script once before starting the Streamlit app.
It creates realistic CSV files in the current directory.
"""

import pandas as pd
import json
import random
from datetime import datetime, timedelta
import os

# ------------------------------
# Configuration
# ------------------------------
NUM_STUDENTS = 12
PROGRAMS = [
    "MS Environmental Science",
    "PhD Environmental Science",
    "PhD Environmental Diplomacy and Negotiations",
    "Master in Resilience Studies (M-ReS)",
    "Professional Masters in Tropical Marine Ecosystems Management (PM-TMEM)",
    "PhD by Research Environmental Science"
]

ADVISERS = ["Dr. Eslava", "Dr. Sanchez"]
SEMESTERS = ["1st Sem", "2nd Sem", "Summer"]
CURRENT_YEAR = 2025

# Helper: random date within last 2 years
def random_date(start_year=2023, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

# Helper: get milestone list for a program type
def get_milestone_list(program):
    if program.startswith("MS") or program.startswith("Master"):
        if "Resilience" in program or "TMEM" in program:
            return [
                "Guidance Committee Formation",
                "Plan of Study (POS)",
                "General Examination",
                "External Review",
                "Graduation Clearance"
            ]
        else:
            return [
                "Guidance Committee Formation",
                "Plan of Study (POS)",
                "General Examination",
                "Thesis Work",
                "External Review",
                "Publishable Article",
                "Final Examination",
                "Final Submission",
                "Graduation Clearance"
            ]
    elif program.startswith("PhD by Research"):
        return [
            "Supervisory Committee Formation",
            "Plan of Research",
            "Seminar Series (4 seminars)",
            "Research Progress Review",
            "Thesis Draft",
            "Publication (min 2 papers)",
            "Final Oral Examination",
            "Thesis Submission",
            "Graduation"
        ]
    else:  # regular PhD
        return [
            "Advisory Committee Formation",
            "Qualifying Exam",
            "Plan of Study",
            "Comprehensive Exam",
            "Dissertation",
            "External Review",
            "Publication",
            "Final Defense",
            "Submission",
            "Graduation"
        ]

# ------------------------------
# 1. students.csv
# ------------------------------
def generate_students():
    students = []
    for i in range(1, NUM_STUDENTS + 1):
        # Assign program based on student index to cover variety
        prog_idx = (i - 1) % len(PROGRAMS)
        program = PROGRAMS[prog_idx]
        advisor = random.choice(ADVISERS)
        ay_start = random.choice([2022, 2023, 2024])
        semester = random.choice(SEMESTERS)
        gwa = round(random.uniform(1.2, 3.5), 2)
        units_taken = random.randint(12, 50)
        units_required = 32 if "MS" in program or "Master" in program else (50 if "PhD" in program else 36)
        thesis_units_taken = random.randint(0, 12)
        thesis_units_limit = 6 if "MS" in program else 12
        thesis_extension = 0
        residency_years_used = CURRENT_YEAR - ay_start
        residency_extension = 0 if residency_years_used <= 5 else 1
        pos_status = random.choice(["Approved", "Pending", "Rejected"])
        # Exams statuses
        qualifying = random.choice(["Passed", "Failed", "Not Taken", "N/A"])
        written_comp = random.choice(["Passed", "Failed", "Not Taken", "N/A"])
        oral_comp = random.choice(["Passed", "Failed", "Not Taken", "N/A"])
        general_exam = random.choice(["Passed", "Failed", "Not Taken"])
        final_exam = random.choice(["Passed", "Failed", "Not Taken"])
        external_reviewer = "Dr. Smith" if random.random() > 0.7 else ""
        final_attempts = random.randint(0, 2)
        # Committee members for committee milestone (JSON)
        committee = []
        if random.random() > 0.3:
            num_members = random.randint(2, 4)
            roles = ["Chair", "Co-chair"] + ["Member"] * (num_members - 2)
            random.shuffle(roles)
            for j in range(num_members):
                committee.append({
                    "name": f"Professor {chr(65+j)}",
                    "role": roles[j] if j < len(roles) else "Member"
                })
        committee_json = json.dumps(committee)
        # Profile data
        profile_pending = random.choice(["", "Pending", "Rejected"]) if random.random() > 0.8 else ""
        special_status = random.choice(["Regular", "On Leave", "Shifted", "Inactive"]) if random.random() > 0.9 else "Regular"

        student = {
            "student_number": f"2024-{i:04d}",
            "name": f"Student_{i:02d}, Sample",
            "last_name": f"Student_{i:02d}",
            "first_name": "Sample",
            "middle_name": "M.",
            "program": program,
            "advisor": advisor,
            "ay_start": ay_start,
            "semester": semester,
            "gwa": gwa,
            "total_units_taken": units_taken,
            "total_units_required": units_required,
            "thesis_units_taken": thesis_units_taken,
            "thesis_units_limit": thesis_units_limit,
            "thesis_extension_units": thesis_extension,
            "residency_years_used": residency_years_used,
            "residency_extension_years": residency_extension,
            "pos_status": pos_status,
            "qualifying_exam_status": qualifying,
            "written_comprehensive_status": written_comp,
            "oral_comprehensive_status": oral_comp,
            "general_exam_status": general_exam,
            "final_exam_status": final_exam,
            "external_reviewer": external_reviewer,
            "final_exam_attempts": final_attempts,
            "profile_pic": "",
            "committee_members_structured": committee_json,
            "committee_approval_date": "",
            "thesis_outline_approved": random.choice(["Yes", "No"]),
            "thesis_status": random.choice(["In Progress", "Approved", "Pending"]),
            "prior_ms_graduate": random.choice([True, False]) if "PhD Environmental Science" in program else False,
            "student_status": random.choice(["Regular", "Probationary", "Conditional"]),
            "address": f"{random.randint(1,100)} Main St, Los Baños",
            "phone": f"+63 {random.randint(900,999)} {random.randint(100,999)} {random.randint(1000,9999)}",
            "institutional_email": f"student{i}@up.edu.ph",
            "gender": random.choice(["Male", "Female", "Other"]),
            "civil_status": random.choice(["Single", "Married"]),
            "citizenship": "Filipino",
            "birthdate": random_date(1990, 2000).strftime("%Y-%m-%d"),
            "religion": random.choice(["Roman Catholic", "Iglesia ni Cristo", " Muslim", "None"]),
            "emergency_name": f"Emergency Contact {i}",
            "emergency_relationship": "Spouse",
            "emergency_country_code": "+63",
            "emergency_phone": f"{random.randint(900,999)} {random.randint(100,999)} {random.randint(1000,9999)}",
            "special_status": special_status,
            "residency_max_years": 5 if "MS" in program or "Master" in program else 7,
            "profile_pending_status": profile_pending,
            "profile_pending_remarks": "",
            "profile_pending_address": "",
            "profile_pending_phone": "",
            "profile_pending_email": "",
            "profile_pending_gender": "",
            "profile_pending_civil_status": "",
            "profile_pending_citizenship": "",
            "profile_pending_birthdate": "",
            "profile_pending_religion": "",
            "profile_pending_emergency_name": "",
            "profile_pending_emergency_relationship": "",
            "profile_pending_emergency_country_code": "",
            "profile_pending_emergency_phone": "",
        }
        students.append(student)
    df = pd.DataFrame(students)
    df.to_csv("students.csv", index=False)
    print("✅ students.csv generated")

# ------------------------------
# 2. semester_records.csv
# ------------------------------
def generate_semester_records(students_df):
    records = []
    for _, student in students_df.iterrows():
        sn = student["student_number"]
        start_ay = student["ay_start"]
        # Create 4 to 6 semesters
        for sem_idx in range(1, random.randint(4, 7)):
            year = start_ay + (sem_idx - 1) // 3
            sem_order = ["1st Sem", "2nd Sem", "Summer"]
            sem_name = sem_order[(sem_idx - 1) % 3]
            ay = f"{year}-{year+1}"
            # Random subjects (3-5 courses)
            subjects = []
            pos_courses = []
            for c in range(random.randint(3, 5)):
                course_code = f"ES {random.randint(200, 300)}"
                grade = random.choice(["1.00", "1.25", "1.50", "1.75", "2.00", "2.25", "2.50", "2.75", "3.00", "4.00", "INC", "P"])
                units = 3
                subjects.append({
                    "course_code": course_code,
                    "course_description": f"Course {course_code}",
                    "units": units,
                    "grade": grade
                })
                pos_courses.append(course_code)
            # Maybe add thesis units
            if "Thesis" in student["program"] or "Dissertation" in student["program"]:
                if random.random() > 0.7:
                    subjects.append({
                        "course_code": "THESIS 300",
                        "course_description": "Master's Thesis",
                        "units": 6,
                        "grade": random.choice(["1.00", "1.50", "2.00", "IP"])
                    })
                    pos_courses.append("THESIS 300")
            # POS status
            pos_approved_status = random.choice(["Approved", "Pending", ""])
            semester_status = random.choice(["Regular", "Off-Sem", "On Leave"]) if random.random() > 0.8 else "Regular"
            # Document upload
            doc_status = random.choice(["Approved", "Pending", "Rejected", ""]) if semester_status == "Regular" else ""
            doc_path = f"uploads/{sn}/semester_docs/{ay}_{sem_name}_doc.pdf" if doc_status else ""
            record = {
                "student_number": sn,
                "academic_year": ay,
                "semester": sem_name,
                "subjects_json": json.dumps(subjects),
                "total_units": sum(s["units"] for s in subjects),
                "gwa": round(random.uniform(1.0, 3.5), 2),
                "doc_path": doc_path,
                "doc_upload_time": random_date(2024, 2025).strftime("%Y-%m-%d %H:%M:%S") if doc_path else "",
                "doc_status": doc_status,
                "doc_remarks": "Please resubmit" if doc_status == "Rejected" else "",
                "doc_validated_by": random.choice(["Dr. Eslava", "Staff"]) if doc_status in ["Approved","Rejected"] else "",
                "doc_validated_time": random_date(2024, 2025).strftime("%Y-%m-%d %H:%M:%S") if doc_status in ["Approved","Rejected"] else "",
                "semester_status": semester_status,
                "pos_courses": json.dumps(pos_courses),
                "pos_approved_status": pos_approved_status
            }
            records.append(record)
    df = pd.DataFrame(records)
    df.to_csv("semester_records.csv", index=False)
    print("✅ semester_records.csv generated")

# ------------------------------
# 3. milestone_tracking.csv
# ------------------------------
def generate_milestone_tracking(students_df):
    milestones = []
    for _, student in students_df.iterrows():
        sn = student["student_number"]
        program = student["program"]
        milestone_names = get_milestone_list(program)
        # Random status progression: first few approved, next pending, rest not started
        approved_count = random.randint(0, len(milestone_names))
        for idx, m in enumerate(milestone_names):
            if idx < approved_count:
                status = "Approved"
                date_val = random_date(2023, 2025).strftime("%Y-%m-%d")
                reviewed_by = random.choice(["Dr. Eslava", "Dr. Sanchez"])
                review_date = random_date(2023, 2025).strftime("%Y-%m-%d %H:%M:%S")
                remarks = "Approved"
                file_path = f"uploads/{sn}/milestones/{m.replace(' ', '_')}_doc.pdf" if random.random() > 0.3 else ""
            elif idx == approved_count:
                status = "Pending"
                date_val = random_date(2024, 2025).strftime("%Y-%m-%d")
                reviewed_by = ""
                review_date = ""
                remarks = ""
                file_path = f"uploads/{sn}/milestones/{m.replace(' ', '_')}_submitted.pdf"
            else:
                status = "Not Started"
                date_val = ""
                reviewed_by = ""
                review_date = ""
                remarks = ""
                file_path = ""
            milestones.append({
                "student_number": sn,
                "milestone": m,
                "status": status,
                "date": date_val,
                "file_path": file_path,
                "remarks": remarks,
                "reviewed_by": reviewed_by,
                "review_date": review_date
            })
    df = pd.DataFrame(milestones)
    df.to_csv("milestone_tracking.csv", index=False)
    print("✅ milestone_tracking.csv generated")

# ------------------------------
# 4. uploads.csv
# ------------------------------
def generate_uploads(students_df):
    categories = ["admission_letter", "amis_screenshot", "committee_form", "plan_of_study", "thesis_file"]
    uploads = []
    for _, student in students_df.iterrows():
        sn = student["student_number"]
        for cat in categories:
            if random.random() > 0.6:  # 40% chance of having upload
                status = random.choice(["Pending", "Approved", "Rejected"])
                uploads.append({
                    "student_number": sn,
                    "category": cat,
                    "file_path": f"uploads/{sn}/{cat}_{random.randint(1,100)}.pdf",
                    "original_filename": f"{cat}_document.pdf",
                    "upload_date": random_date(2024, 2025).strftime("%Y-%m-%d %H:%M:%S"),
                    "status": status,
                    "reviewer_comment": "Looks good" if status == "Approved" else "Please correct",
                    "reviewed_by": random.choice(["Dr. Eslava", "Staff"]) if status != "Pending" else "",
                    "review_date": random_date(2024, 2025).strftime("%Y-%m-%d %H:%M:%S") if status != "Pending" else ""
                })
    df = pd.DataFrame(uploads)
    df.to_csv("uploads.csv", index=False)
    print("✅ uploads.csv generated")

# ------------------------------
# 5. data_requests.csv
# ------------------------------
def generate_data_requests(students_df):
    request_types = ["Deletion", "Correction", "Access"]
    requests = []
    for _, student in students_df.iterrows():
        if random.random() > 0.8:
            requests.append({
                "request_id": len(requests) + 1,
                "student_number": student["student_number"],
                "request_type": random.choice(request_types),
                "details": f"Request to {random.choice(['update address', 'delete account', 'correct name'])}",
                "status": random.choice(["Pending", "Approved", "Rejected"]),
                "submitted_date": random_date(2024, 2025).strftime("%Y-%m-%d %H:%M:%S"),
                "reviewer_comment": "",
                "reviewed_by": "",
                "review_date": ""
            })
    df = pd.DataFrame(requests)
    df.to_csv("data_requests.csv", index=False)
    print("✅ data_requests.csv generated")

# ------------------------------
# 6. final_exam_votes.csv (optional)
# ------------------------------
def generate_final_exam_votes(students_df):
    votes = []
    for _, student in students_df.iterrows():
        if "PhD" in student["program"] and random.random() > 0.7:
            sn = student["student_number"]
            for v in range(random.randint(1, 3)):
                vote = random.choice(["Positive", "Negative"])
                votes.append({
                    "student_number": sn,
                    "milestone": "Final Examination",
                    "voter_name": f"Committee Member {v}",
                    "vote": vote,
                    "voter_role": "Committee",
                    "vote_date": random_date(2024, 2025).strftime("%Y-%m-%d %H:%M:%S")
                })
    df = pd.DataFrame(votes)
    df.to_csv("final_exam_votes.csv", index=False)
    print("✅ final_exam_votes.csv generated")

# ------------------------------
# Main execution
# ------------------------------
if __name__ == "__main__":
    # Ensure the uploads folder structure exists (dummy)
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("profile_pics", exist_ok=True)
    os.makedirs("student_uploads", exist_ok=True)

    students_df = generate_students()
    students_df = pd.read_csv("students.csv")  # reload to get consistent data
    generate_semester_records(students_df)
    generate_milestone_tracking(students_df)
    generate_uploads(students_df)
    generate_data_requests(students_df)
    generate_final_exam_votes(students_df)
    print("\n🎉 All sample data generated successfully! Now run your Streamlit app.")