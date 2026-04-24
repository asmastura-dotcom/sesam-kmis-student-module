import streamlit as st
import pandas as pd
import os

# ================= CONFIG =================
st.set_page_config(page_title="SESAM KMIS", layout="wide")

DATA_FILE = "students.csv"
UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= AUTH =================
USERS = {
    "staff1": {"password": "admin123", "role": "Staff"},
    "adviser1": {"password": "adv123", "role": "Adviser"},
    "student1": {"password": "stu123", "role": "Student"},
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ================= LOGIN =================
if not st.session_state.logged_in:
    st.title("🔐 KMIS Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USERS and USERS[u]["password"] == p:
            st.session_state.logged_in = True
            st.session_state.username = u
            st.session_state.role = USERS[u]["role"]
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# ================= DATA =================
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=[
            "student_id","name","program","advisor",
            "gwa","units","notification","profile_pic"
        ])
        df.to_csv(DATA_FILE, index=False)
        return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()

# ================= SIDEBAR =================
st.sidebar.write(f"👤 {st.session_state.username}")
st.sidebar.write(f"🔑 {st.session_state.role}")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# ================= STAFF VIEW =================
if st.session_state.role == "Staff":
    st.title("📋 Staff Dashboard")

    # 🔍 Search
    search = st.text_input("🔍 Search student")

    filtered = df.copy()
    if search:
        filtered = df[df["name"].str.contains(search, case=False, na=False)]

    st.dataframe(filtered, use_container_width=True)

    # 🎯 Select student
    if len(filtered) > 0:
        sid = st.selectbox("Select Student", filtered["student_id"])
        student = df[df["student_id"] == sid].iloc[0]

        st.subheader("📌 Student Details")

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Name:** {student['name']}")
            st.write(f"**Program:** {student['program']}")
            st.write(f"**Advisor:** {student['advisor']}")

            # Profile pic
            if pd.notna(student["profile_pic"]) and student["profile_pic"] != "":
                st.image(student["profile_pic"], width=150)

        with col2:
            st.write(f"**GWA:** {student['gwa']}")
            st.write(f"**Units:** {student['units']}")

            if student["gwa"] > 2.0:
                st.error("⚠️ Academic Warning!")

        # ✏️ Update
        st.subheader("✏️ Update Record")

        new_gwa = st.number_input("GWA", 1.0, 5.0, value=float(student["gwa"]) if pd.notna(student["gwa"]) else 1.0)
        new_units = st.number_input("Units", 0, value=int(student["units"]) if pd.notna(student["units"]) else 0)

        if st.button("Update"):
            df.loc[df["student_id"] == sid, "gwa"] = new_gwa
            df.loc[df["student_id"] == sid, "units"] = new_units
            save_data(df)
            st.success("Updated!")
            st.rerun()

    # ➕ Add student
    st.subheader("➕ Add Student")

    name = st.text_input("Name")
    program = st.selectbox("Program", ["MS", "PhD"])

    if st.button("Add Student"):
        new_id = f"S{len(df)+1:03d}"
        new_row = pd.DataFrame([{
            "student_id": new_id,
            "name": name,
            "program": program,
            "advisor": "adviser1",
            "gwa": 1.0,
            "units": 0,
            "notification": "",
            "profile_pic": ""
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        save_data(df)
        st.success("Student added!")
        st.rerun()

# ================= ADVISER VIEW =================
elif st.session_state.role == "Adviser":
    st.title("👨‍🏫 Adviser Dashboard")

    search = st.text_input("🔍 Search advisee")

    filtered = df.copy()
    if search:
        filtered = df[df["name"].str.contains(search, case=False, na=False)]

    st.dataframe(filtered)

    if len(filtered) > 0:
        sid = st.selectbox("Select Student", filtered["student_id"])

        msg = st.text_area("Send Notification")

        if st.button("Notify"):
            df.loc[df["student_id"] == sid, "notification"] = msg
            save_data(df)
            st.success("Notification sent!")

# ================= STUDENT VIEW =================
elif st.session_state.role == "Student":
    st.title("🎓 Student Dashboard")

    student = df.iloc[0]  # demo only

    st.write(f"Welcome {student['name']}")

    # 📩 Notification
    if student["notification"]:
        st.warning(f"📩 {student['notification']}")

    # 📊 Info
    st.metric("GWA", student["gwa"])
    st.metric("Units", student["units"])

    # 📤 Upload semester
    st.subheader("📤 Upload Semester Record")

    file = st.file_uploader("Upload AMIS Screenshot", type=["png","jpg"])

    gwa = st.number_input("GWA", 1.0, 5.0)
    units = st.number_input("Units", 0)

    if st.button("Submit Record"):
        path = os.path.join(UPLOAD_FOLDER, file.name) if file else ""
        if file:
            with open(path, "wb") as f:
                f.write(file.getbuffer())

        df.loc[df.index[0], "gwa"] = gwa
        df.loc[df.index[0], "units"] = units
        save_data(df)

        st.success("Submitted!")

    # 👤 Profile pic
    st.subheader("👤 Upload Profile Picture")

    pic = st.file_uploader("Upload Photo", type=["png","jpg"])

    if pic:
        path = os.path.join(UPLOAD_FOLDER, pic.name)
        with open(path, "wb") as f:
            f.write(pic.getbuffer())

        df.loc[df.index[0], "profile_pic"] = path
        save_data(df)

        st.success("Profile updated!")
