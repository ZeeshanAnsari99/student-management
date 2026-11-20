"""
🎓 Student Management System — Streamlit UI

Register students and teachers, record grades and view details.
Data is stored in a local JSON file.

Run with:
    streamlit run app.py
"""

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd
import streamlit as st

DATABASE = Path(__file__).parent / "school_data.json"


# ---------------------------------------------------------------------------
# Data layer
# ---------------------------------------------------------------------------
def load() -> dict:
    data = {"students": [], "teachers": []}
    if DATABASE.exists():
        content = DATABASE.read_text()
        if content.strip():
            data.update(json.loads(content))
    return data


def save(data: dict) -> None:
    DATABASE.write_text(json.dumps(data, indent=4))


# ---------------------------------------------------------------------------
# OOP model (same structure as the original CLI version)
# ---------------------------------------------------------------------------
class Persons(ABC):
    def __init__(self, data: dict):
        self.data = data

    @abstractmethod
    def get_roles(self) -> str: ...

    @abstractmethod
    def register(self, **details) -> tuple[bool, str]: ...

    @abstractmethod
    def find(self, key: str) -> dict | None: ...

    @staticmethod
    def validate_email(email: str) -> bool:
        return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is not None


class Student(Persons):
    def get_roles(self):
        return "student"

    def register(self, name, age, email, roll_no):
        if not name or not roll_no:
            return False, "Name and roll number are required."
        if not self.validate_email(email):
            return False, "Invalid email address."
        if self.find(roll_no):
            return False, f"A student with roll number {roll_no} already exists."
        self.data["students"].append(
            {"name": name, "age": age, "email": email, "roll_no": roll_no, "grades": {}}
        )
        save(self.data)
        return True, f"Student **{name}** registered."

    def find(self, roll_no):
        return next((s for s in self.data["students"] if s["roll_no"] == roll_no), None)

    def add_grade(self, roll_no, subject, marks):
        student = self.find(roll_no)
        if student is None:
            return False, "Student not found."
        if not subject:
            return False, "Subject is required."
        student["grades"][subject] = marks
        save(self.data)
        return True, f"Grade for **{subject}** saved for {student['name']}."

    @staticmethod
    def average(student) -> float:
        g = student["grades"]
        return sum(g.values()) / len(g) if g else 0.0


class Teacher(Persons):
    def get_roles(self):
        return "teacher"

    def register(self, name, age, email, subject, employee_id):
        if not name or not employee_id:
            return False, "Name and employee ID are required."
        if not self.validate_email(email):
            return False, "Invalid email address."
        if self.find(employee_id):
            return False, f"A teacher with employee ID {employee_id} already exists."
        self.data["teachers"].append(
            {"name": name, "age": age, "email": email, "subject": subject, "employee_id": employee_id}
        )
        save(self.data)
        return True, f"Teacher **{name}** registered."

    def find(self, employee_id):
        return next((t for t in self.data["teachers"] if t["employee_id"] == employee_id), None)


# ---------------------------------------------------------------------------
# Page setup & styling
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Student Management", page_icon="🎓", layout="wide")

st.markdown(
    """
    <style>
    .hero {
        padding: 1.6rem 2rem;
        border-radius: 16px;
        background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 55%, #a855f7 100%);
        color: white;
        margin-bottom: 1.5rem;
    }
    .hero h1 { margin: 0; font-size: 2.2rem; color: white; }
    .hero p  { margin: .3rem 0 0; opacity: .9; font-size: 1.05rem; }
    .profile {
        padding: 1.2rem 1.4rem;
        border-radius: 14px;
        border: 1px solid rgba(128,128,128,.25);
        margin-bottom: 1rem;
    }
    .profile h3 { margin: 0 0 .3rem; }
    .profile span { opacity: .7; }
    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 12px;
        padding: .8rem 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

data = load()
stud = Student(data)
tech = Teacher(data)

with st.sidebar:
    st.markdown("## 🎓 School Manager")
    page = st.radio(
        "Menu",
        [
            "🏠 Dashboard",
            "🧑‍🎓 Register student",
            "👩‍🏫 Register teacher",
            "📝 Add grades",
            "🔍 Student details",
            "🔍 Teacher details",
        ],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Data stored in `school_data.json`")
    st.caption("Built with Python & Streamlit")

st.markdown(
    """
    <div class="hero">
        <h1>🎓 Student Management System</h1>
        <p>Register students and teachers, record grades and track performance.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


def show_result(ok: bool, msg: str):
    if ok:
        st.success("✅ " + msg)
    else:
        st.error(msg)


def student_options() -> dict:
    return {f"{s['roll_no']} — {s['name']}": s["roll_no"] for s in data["students"]}


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
if page == "🏠 Dashboard":
    students, teachers = data["students"], data["teachers"]
    graded = [s for s in students if s["grades"]]
    school_avg = sum(Student.average(s) for s in graded) / len(graded) if graded else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🧑‍🎓 Students", len(students))
    c2.metric("👩‍🏫 Teachers", len(teachers))
    c3.metric("📝 Grades recorded", sum(len(s["grades"]) for s in students))
    c4.metric("📊 School average", f"{school_avg:.1f}")

    tab_s, tab_t = st.tabs(["Students", "Teachers"])
    with tab_s:
        if students:
            df = pd.DataFrame(
                [
                    {
                        "Roll no": s["roll_no"],
                        "Name": s["name"],
                        "Age": s["age"],
                        "Email": s["email"],
                        "Subjects": len(s["grades"]),
                        "Average": round(Student.average(s), 1),
                    }
                    for s in students
                ]
            )
            st.dataframe(df, hide_index=True, width="stretch")
            if graded:
                st.subheader("Average by student")
                st.bar_chart(df[df["Subjects"] > 0].set_index("Name")["Average"])
        else:
            st.info("No students yet — register one from the sidebar.")
    with tab_t:
        if teachers:
            st.dataframe(
                pd.DataFrame(teachers).rename(
                    columns={"name": "Name", "age": "Age", "email": "Email",
                             "subject": "Subject", "employee_id": "Employee ID"}
                ),
                hide_index=True,
                width="stretch",
            )
        else:
            st.info("No teachers yet — register one from the sidebar.")

elif page == "🧑‍🎓 Register student":
    st.subheader("🧑‍🎓 Register a new student")
    with st.form("student_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Full name")
        roll_no = c2.text_input("Roll number")
        email = c1.text_input("Email")
        age = c2.number_input("Age", min_value=3, max_value=100, value=18, step=1)
        submitted = st.form_submit_button("Register student", type="primary", width="stretch")
    if submitted:
        ok, msg = stud.register(name.strip(), int(age), email.strip(), roll_no.strip())
        show_result(ok, msg)
        if ok:
            st.balloons()

elif page == "👩‍🏫 Register teacher":
    st.subheader("👩‍🏫 Register a new teacher")
    with st.form("teacher_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Full name")
        employee_id = c2.text_input("Employee ID")
        email = c1.text_input("Email")
        subject = c2.text_input("Subject")
        age = c1.number_input("Age", min_value=18, max_value=100, value=30, step=1)
        submitted = st.form_submit_button("Register teacher", type="primary", width="stretch")
    if submitted:
        ok, msg = tech.register(name.strip(), int(age), email.strip(), subject.strip(), employee_id.strip())
        show_result(ok, msg)
        if ok:
            st.balloons()

elif page == "📝 Add grades":
    st.subheader("📝 Add or update a grade")
    options = student_options()
    if not options:
        st.info("Register a student first.")
    else:
        with st.form("grade_form", clear_on_submit=True):
            label = st.selectbox("Student", list(options))
            c1, c2 = st.columns(2)
            subject = c1.text_input("Subject", placeholder="e.g. Maths")
            marks = c2.number_input("Marks", min_value=0.0, max_value=100.0, value=75.0, step=0.5)
            submitted = st.form_submit_button("Save grade", type="primary", width="stretch")
        if submitted:
            show_result(*stud.add_grade(options[label], subject.strip(), float(marks)))

elif page == "🔍 Student details":
    st.subheader("🔍 Student details")
    options = student_options()
    if not options:
        st.info("No students registered yet.")
    else:
        s = stud.find(options[st.selectbox("Choose a student", list(options))])
        st.markdown(
            f"""<div class="profile"><h3>🧑‍🎓 {s['name']}</h3>
            <span>Roll no {s['roll_no']} · Age {s['age']} · {s['email']}</span></div>""",
            unsafe_allow_html=True,
        )
        grades = s["grades"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Subjects", len(grades))
        c2.metric("Average", f"{Student.average(s):.1f}")
        c3.metric("Best subject", max(grades, key=grades.get) if grades else "—")
        if grades:
            gdf = pd.DataFrame({"Subject": list(grades), "Marks": list(grades.values())})
            left, right = st.columns([1, 2])
            left.dataframe(gdf, hide_index=True, width="stretch")
            right.bar_chart(gdf.set_index("Subject"))
        else:
            st.info("No grades recorded yet — add some from **📝 Add grades**.")

elif page == "🔍 Teacher details":
    st.subheader("🔍 Teacher details")
    options = {f"{t['employee_id']} — {t['name']}": t["employee_id"] for t in data["teachers"]}
    if not options:
        st.info("No teachers registered yet.")
    else:
        t = tech.find(options[st.selectbox("Choose a teacher", list(options))])
        st.markdown(
            f"""<div class="profile"><h3>👩‍🏫 {t['name']}</h3>
            <span>Employee ID {t['employee_id']} · Age {t['age']} · {t['email']}</span></div>""",
            unsafe_allow_html=True,
        )
        st.metric("Subject", t["subject"] or "—")
