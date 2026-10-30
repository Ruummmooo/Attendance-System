import sqlite3
from datetime import datetime, date
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "attendance.db"

st.set_page_config(
    page_title="Classroom Intelligence",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Database ----------
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def setup_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                course TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                session_date TEXT NOT NULL,
                marked_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Present',
                UNIQUE(student_id, session_date),
                FOREIGN KEY(student_id) REFERENCES students(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS engagement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_date TEXT NOT NULL,
                session_name TEXT NOT NULL,
                participation INTEGER NOT NULL,
                interaction INTEGER NOT NULL,
                inactivity INTEGER NOT NULL,
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()

def read_table(query, params=()):
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)

def add_student(roll_no, name, course):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO students (roll_no, name, course, created_at) VALUES (?, ?, ?, ?)",
            (roll_no.strip(), name.strip(), course.strip(), datetime.now().isoformat(timespec="seconds"))
        )
        conn.commit()

def mark_attendance(student_id, session_day):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO attendance (student_id, session_date, marked_at, status)
            VALUES (?, ?, ?, 'Present')
            ON CONFLICT(student_id, session_date) DO UPDATE SET
                marked_at=excluded.marked_at, status='Present'
        """, (int(student_id), str(session_day), datetime.now().isoformat(timespec="seconds")))
        conn.commit()

def save_engagement(session_name, participation, interaction, inactivity, notes):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO engagement
            (session_date, session_name, participation, interaction, inactivity, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            date.today().isoformat(), session_name, int(participation),
            int(interaction), int(inactivity), notes,
            datetime.now().isoformat(timespec="seconds")
        ))
        conn.commit()

setup_database()

# ---------- Styling ----------
st.markdown("""
<style>
    .stApp { background: #0b1020; color: #eef2ff; }
    section[data-testid="stSidebar"] { background: #111a30; border-right: 1px solid #263451; }
    .block-container { padding-top: 1.8rem; padding-bottom: 2rem; max-width: 1500px; }
    h1, h2, h3 { color: #f4f7ff !important; }
    p, label, .stMarkdown { color: #cbd5e1; }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #172440, #202b4b);
        border: 1px solid #34466c; padding: 18px; border-radius: 15px;
    }
    div[data-testid="stMetric"] label { color: #aab9d4 !important; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #ffffff !important; }
    .hero {
        padding: 25px 28px; border-radius: 18px;
        background: linear-gradient(110deg, #172a50, #34245e);
        border: 1px solid #46558c; margin-bottom: 22px;
    }
    .hero p { color: #d5ddf4; margin-bottom: 0; }
    .small-note { color: #91a3c5; font-size: 0.88rem; }
    div.stButton > button {
        border-radius: 10px; border: 1px solid #5369a3;
        background: linear-gradient(90deg, #3159a8, #6546a8);
        color: white; font-weight: 600;
    }
    div.stButton > button:hover { border-color: #9ab4ff; color: white; }
    div[data-testid="stDataFrame"] { border: 1px solid #2b3b5d; border-radius: 12px; }
    hr { border-color: #273653; }
</style>
""", unsafe_allow_html=True)

# ---------- Helpers ----------
def engagement_score(participation, interaction, inactivity):
    # Simple transparent classroom indicator, not a measure of learning or attention.
    return round((participation * 0.4) + (interaction * 0.4) + ((100 - inactivity) * 0.2))

def teaching_suggestions(p, i, inactive):
    suggestions = []
    if p < 40:
        suggestions.append("Try a short question, poll, or pair discussion to invite more participation.")
    if i < 40:
        suggestions.append("Add a brief question-and-answer activity to encourage classroom interaction.")
    if inactive > 60:
        suggestions.append("Consider a short break, a change of activity, or a quick recap.")
    if not suggestions:
        suggestions.append("The recorded activity indicators look balanced. Continue the current teaching approach and check again later.")
    return suggestions

def load_face_detector():
    cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(str(cascade_path))
    if detector.empty():
        raise RuntimeError("OpenCV face detector could not be loaded.")
    return detector

def detect_faces(pil_image):
    rgb = np.array(pil_image.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    detector = load_face_detector()
    faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(35, 35))
    annotated = rgb.copy()
    for (x, y, w, h) in faces:
        cv2.rectangle(annotated, (x, y), (x+w, y+h), (55, 190, 255), 3)
    return annotated, len(faces)

def metric_card(label, value, help_text=None):
    st.metric(label, value, help=help_text)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🎓 Classroom AI")
    st.caption("Attendance & Engagement Agent")
    st.markdown("---")
    page = st.radio(
        "NAVIGATION",
        ["Dashboard", "Students", "Webcam Attendance", "Engagement Lab", "Reports", "About"],
        label_visibility="visible"
    )
    st.markdown("---")
    st.markdown("**System status**")
    st.success("Offline database ready")
    st.caption(f"Today: {date.today().strftime('%d %b %Y')}")
    st.caption("Data stays in the local project database.")

students = read_table("SELECT * FROM students ORDER BY name")
today = date.today().isoformat()
today_att = read_table("""
    SELECT a.id, s.roll_no, s.name, s.course, a.session_date, a.marked_at, a.status
    FROM attendance a JOIN students s ON a.student_id=s.id
    WHERE a.session_date=? ORDER BY a.marked_at DESC
""", (today,))
engagement_data = read_table("SELECT * FROM engagement ORDER BY id DESC")

# ---------- Pages ----------
if page == "Dashboard":
    st.markdown("""
    <div class="hero">
      <h1>Good day, Teacher 👋</h1>
      <p>Your classroom overview, attendance records and session activity in one simple workspace.</p>
    </div>
    """, unsafe_allow_html=True)

    total_students = len(students)
    present = len(today_att)
    attendance_rate = round((present / total_students) * 100) if total_students else 0
    latest_score = "—"
    if not engagement_data.empty:
        row = engagement_data.iloc[0]
        latest_score = f"{engagement_score(row['participation'], row['interaction'], row['inactivity'])}/100"

    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Registered students", total_students)
    with c2: metric_card("Present today", present)
    with c3: metric_card("Attendance rate", f"{attendance_rate}%")
    with c4: metric_card("Latest activity indicator", latest_score, "A simple classroom activity summary, not a learning score.")

    st.markdown("### Today's attendance")
    if today_att.empty:
        st.info("No attendance has been marked today. Open Webcam Attendance to begin.")
    else:
        st.dataframe(today_att[["roll_no", "name", "course", "marked_at", "status"]], use_container_width=True, hide_index=True)

    st.markdown("### Recent classroom activity")
    if engagement_data.empty:
        st.info("No session activity has been recorded yet. Visit Engagement Lab to add a session summary.")
    else:
        chart_df = engagement_data.head(7).copy().sort_values("id")
        chart_df["score"] = chart_df.apply(
            lambda r: engagement_score(r["participation"], r["interaction"], r["inactivity"]), axis=1
        )
        fig = px.line(chart_df, x="session_date", y="score", markers=True,
                      hover_data=["session_name"], title="Recent classroom activity indicator")
        fig.update_layout(paper_bgcolor="#0b1020", plot_bgcolor="#111a30",
                          font_color="#dbe6ff", yaxis_range=[0, 100],
                          xaxis_title="Session date", yaxis_title="Indicator (0–100)")
        st.plotly_chart(fig, use_container_width=True)

elif page == "Students":
    st.title("👥 Student Management")
    st.write("Add learners to your local classroom register.")
    with st.expander("➕ Add a new student", expanded=students.empty):
        with st.form("student_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            roll = col1.text_input("Roll number", placeholder="e.g. CSE001")
            name = col2.text_input("Student name", placeholder="e.g. Aisha Khan")
            course = st.text_input("Course / Section", placeholder="e.g. B.Tech CSE AIML")
            submitted = st.form_submit_button("Add student", use_container_width=True)
            if submitted:
                if not roll.strip() or not name.strip():
                    st.error("Please enter both roll number and student name.")
                else:
                    try:
                        add_student(roll, name, course)
                        st.success("Student added successfully.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("That roll number already exists.")

    st.markdown("### Student register")
    if students.empty:
        st.info("No students yet. Add your first student above.")
    else:
        st.dataframe(students[["roll_no", "name", "course", "created_at"]],
                     use_container_width=True, hide_index=True)
        st.caption(f"{len(students)} student(s) registered.")

        with st.expander("🗑️ Remove a student"):
            options = {f"{r.roll_no} — {r.name}": int(r.id) for r in students.itertuples()}
            selected = st.selectbox("Select student", list(options.keys()))
            if st.button("Delete selected student"):
                sid = options[selected]
                with get_connection() as conn:
                    conn.execute("DELETE FROM attendance WHERE student_id=?", (sid,))
                    conn.execute("DELETE FROM students WHERE id=?", (sid,))
                    conn.commit()
                st.success("Student and their attendance records were deleted.")
                st.rerun()

elif page == "Webcam Attendance":
    st.title("📷 Webcam Attendance")
    st.write("Capture a classroom image, detect visible faces, then confirm the student identity manually.")
    st.warning("Face detection only locates faces. It does not recognize who a person is. Obtain appropriate consent before capturing classroom images.")
    if students.empty:
        st.info("Add students first in Student Management.")
    else:
        camera_image = st.camera_input("Take a classroom photo")
        if camera_image is not None:
            image = Image.open(camera_image)
            try:
                annotated, face_count = detect_faces(image)
                st.image(annotated, caption="Detected faces highlighted with blue boxes", use_container_width=True)
                st.success(f"Detected {face_count} face(s).")
                st.caption("The image is processed for face detection and is not saved to the database.")
                student_options = {
                    f"{r.roll_no} — {r.name}": int(r.id)
                    for r in students.itertuples()
                }
                chosen = st.selectbox("Teacher: confirm the student to mark present", list(student_options.keys()))
                if st.button("✅ Confirm and mark attendance", use_container_width=True):
                    mark_attendance(student_options[chosen], today)
                    st.success(f"Attendance marked for {chosen}.")
                    st.rerun()
            except Exception as e:
                st.error(f"Could not process the image: {e}")
        st.markdown("---")
        st.markdown("### Attendance marked today")
        if today_att.empty:
            st.info("No students marked present yet.")
        else:
            st.dataframe(today_att[["roll_no", "name", "marked_at", "status"]],
                         use_container_width=True, hide_index=True)

elif page == "Engagement Lab":
    st.title("📊 Engagement & Session Dynamics")
    st.write("Record simple classroom observations and receive practical teaching suggestions.")
    st.info("This beginner version uses teacher-entered observations. It does not infer a student's emotions, attention, or learning ability from their face or voice.")
    with st.form("engagement_form", clear_on_submit=True):
        session_name = st.text_input("Session name", placeholder="e.g. Python – Functions")
        c1, c2, c3 = st.columns(3)
        participation = c1.slider("Participation level", 0, 100, 60, help="Teacher's estimate of class participation.")
        interaction = c2.slider("Interaction level", 0, 100, 60, help="Teacher's estimate of questions and discussion.")
        inactivity = c3.slider("Inactivity observed", 0, 100, 30, help="Teacher's estimate of time with little classroom activity.")
        notes = st.text_area("Session notes (optional)", placeholder="What worked well? What could be improved?")
        save = st.form_submit_button("Save session analysis", use_container_width=True)
        if save:
            if not session_name.strip():
                st.error("Please enter a session name.")
            else:
                save_engagement(session_name, participation, interaction, inactivity, notes)
                st.success("Session activity saved.")
                st.rerun()

    score = engagement_score(participation, interaction, inactivity)
    st.markdown("### Live preview")
    a, b = st.columns([1, 2])
    with a:
        st.metric("Activity indicator", f"{score}/100")
        st.caption("An illustrative summary of entered indicators, not a validated engagement measurement.")
    with b:
        for suggestion in teaching_suggestions(participation, interaction, inactivity):
            st.markdown(f"- {suggestion}")

    st.markdown("---")
    st.markdown("### Saved sessions")
    if engagement_data.empty:
        st.info("No sessions saved yet.")
    else:
        display = engagement_data.copy()
        display["activity_indicator"] = display.apply(
            lambda r: engagement_score(r["participation"], r["interaction"], r["inactivity"]), axis=1
        )
        st.dataframe(display[["session_date", "session_name", "participation", "interaction",
                              "inactivity", "activity_indicator", "notes"]],
                     use_container_width=True, hide_index=True)

elif page == "Reports":
    st.title("📄 Reports & Analytics")
    if students.empty:
        st.info("Add students to start generating reports.")
    else:
        attendance = read_table("""
            SELECT s.roll_no, s.name, s.course, a.session_date, a.marked_at, a.status
            FROM attendance a JOIN students s ON a.student_id=s.id
            ORDER BY a.session_date DESC, s.name
        """)
        if attendance.empty:
            st.info("No attendance records available yet.")
        else:
            st.markdown("### Attendance history")
            st.dataframe(attendance, use_container_width=True, hide_index=True)
            csv = attendance.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download attendance CSV", csv,
                               file_name="attendance_report.csv", mime="text/csv")
            per_student = attendance.groupby(["roll_no", "name"]).size().reset_index(name="days_present")
            fig = px.bar(per_student, x="name", y="days_present", color="days_present",
                         title="Recorded attendance by student")
            fig.update_layout(paper_bgcolor="#0b1020", plot_bgcolor="#111a30",
                              font_color="#dbe6ff", xaxis_title="Student", yaxis_title="Days present")
            st.plotly_chart(fig, use_container_width=True)

        if not engagement_data.empty:
            st.markdown("### Session activity history")
            e = engagement_data.copy()
            e["activity_indicator"] = e.apply(
                lambda r: engagement_score(r["participation"], r["interaction"], r["inactivity"]), axis=1
            )
            st.dataframe(e[["session_date", "session_name", "activity_indicator", "notes"]],
                         use_container_width=True, hide_index=True)
            st.download_button("⬇️ Download session CSV", e.to_csv(index=False).encode("utf-8"),
                               file_name="session_activity_report.csv", mime="text/csv")

elif page == "About":
    st.title("ℹ️ About this project")
    st.markdown("""
    ### Multimodal Attendance & Engagement Agent

    A beginner-friendly, offline-first classroom support application built with Python.

    **Current modules**
    - Student registration using SQLite.
    - Webcam image capture using Streamlit.
    - Face detection using OpenCV Haar cascades.
    - Teacher-confirmed attendance.
    - Teacher-entered classroom activity indicators.
    - Rule-based teaching suggestions.
    - CSV reports and charts.

    **Privacy and limitations**
    - Face detection is not face recognition.
    - The webcam image is processed in memory and is not stored by this app.
    - Student identity is selected and confirmed by the teacher.
    - Activity indicators are descriptive estimates, not proof of attention, emotion, or academic performance.
    - The application stores student details and attendance in a local SQLite database.
    - Use only with appropriate institutional approval and informed consent.

    **Built with:** Python, Streamlit, OpenCV, SQLite, NumPy, Pandas and Plotly.
    """)
    st.markdown("---")
    st.caption("Project edition 1.0 · Original beginner implementation")
