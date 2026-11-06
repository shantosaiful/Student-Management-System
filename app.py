import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(
    page_title="Student Management System",
    page_icon="🎓",
    layout="wide"
)

# Database
conn = sqlite3.connect("students.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
# Create and update database table
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    name TEXT,
    roll TEXT UNIQUE,
    department TEXT,
    semester TEXT,
    student_id TEXT UNIQUE,
    result TEXT
)
""")

# Check existing columns
cursor.execute("PRAGMA table_info(students)")
existing_columns = [
    column[1] for column in cursor.fetchall()
]

# Add missing columns automatically
required_columns = {
    "name": "TEXT",
    "roll": "TEXT",
    "department": "TEXT",
    "semester": "TEXT",
    "student_id": "TEXT",
    "result": "TEXT"
}

for column, data_type in required_columns.items():
    if column not in existing_columns:
        cursor.execute(
            f"ALTER TABLE students ADD COLUMN {column} {data_type}"
        )

conn.commit()

# Admin password from Streamlit Secrets
try:
    ADMIN_PASSWORD = st.secrets["auth"]["admin_password"]
except Exception:
    ADMIN_PASSWORD = None

st.title("🎓 Student Management System")

# Admin login
if "admin" not in st.session_state:
    st.session_state.admin = False

if ADMIN_PASSWORD is None:
    st.error("Admin password সেট করা হয়নি। Streamlit Secrets-এ সেট করো।")
else:
    with st.sidebar:
        st.header("Admin Login")

        if not st.session_state.admin:
            password = st.text_input("Password", type="password")

            if st.button("Login"):
                if password == ADMIN_PASSWORD:
                    st.session_state.admin = True
                    st.rerun()
                else:
                    st.error("Wrong Password")
        else:
            st.success("Admin Logged In")
            if st.button("Logout"):
                st.session_state.admin = False
                st.rerun()

# Tabs
if st.session_state.admin:
    tab1, tab2, tab3, tab4 = st.tabs([
        "Add Student",
        "View Students",
        "Search Student",
        "Delete Student"
    ])
else:
    tab2, tab3 = st.tabs([
        "View Students",
        "Search Student"
    ])

# Add Student - Admin only
if st.session_state.admin:
    with tab1:
        st.subheader("Add New Student")

        with st.form("add_student_form"):
            name = st.text_input("Student Name")
            roll = st.text_input("Roll")
            department = st.text_input("Department")
            semester = st.text_input("Semester")
            student_id = st.text_input("Student ID")
            result = st.text_input("Result")

            submitted = st.form_submit_button("Add Student")

            if submitted:
                if not all([
                    name.strip(), roll.strip(),
                    department.strip(), semester.strip(),
                    student_id.strip(), result.strip()
                ]):
                    st.warning("সব তথ্য পূরণ করো।")
                else:
                    try:
                        cursor.execute("""
                        INSERT INTO students
                        (name, roll, department, semester, student_id, result)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            name.strip(), roll.strip(),
                            department.strip(), semester.strip(),
                            student_id.strip(), result.strip()
                        ))
                        conn.commit()
                        st.success("Student added successfully!")
                    except sqlite3.IntegrityError:
                        st.error("এই Roll অথবা Student ID আগে থেকেই আছে।")

# View Students - Everyone
with tab2:
    st.subheader("All Students")

    df = pd.read_sql_query("""
        SELECT name AS Name,
               roll AS Roll,
               department AS Department,
               semester AS Semester,
               student_id AS ID,
               result AS Result
        FROM students
        ORDER BY roll
    """, conn)

    st.write("Total Students:", len(df))
    st.dataframe(df, use_container_width=True, hide_index=True)

# Search Student - Everyone
with tab3:
    st.subheader("Search Student")

    search_value = st.text_input("Enter Roll or Student ID")

    if search_value.strip():
        result_df = pd.read_sql_query("""
            SELECT name AS Name,
                   roll AS Roll,
                   department AS Department,
                   semester AS Semester,
                   student_id AS ID,
                   result AS Result
            FROM students
            WHERE roll = ? OR student_id = ?
        """, conn, params=(
            search_value.strip(),
            search_value.strip()
        ))

        if not result_df.empty:
            st.dataframe(
                result_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("কোনো Student পাওয়া যায়নি।")

# Delete Student - Admin only
if st.session_state.admin:
    with tab4:
        st.subheader("Delete Student")

        delete_value = st.text_input(
            "যে Student মুছতে চাও তার Roll অথবা ID লেখো"
        )

        if delete_value.strip():
            student_df = pd.read_sql_query("""
                SELECT name AS Name,
                       roll AS Roll,
                       department AS Department,
                       semester AS Semester,
                       student_id AS ID,
                       result AS Result
                FROM students
                WHERE roll = ? OR student_id = ?
            """, conn, params=(
                delete_value.strip(),
                delete_value.strip()
            ))

            if not student_df.empty:
                st.dataframe(
                    student_df,
                    use_container_width=True,
                    hide_index=True
                )

                confirm = st.checkbox(
                    "আমি নিশ্চিত, এই Student-এর তথ্য মুছতে চাই।"
                )

                if st.button("Delete Student"):
                    if confirm:
                        cursor.execute("""
                            DELETE FROM students
                            WHERE roll = ? OR student_id = ?
                        """, (
                            delete_value.strip(),
                            delete_value.strip()
                        ))
                        conn.commit()
                        st.success("Student deleted successfully!")
                        st.rerun()
                    else:
                        st.warning("আগে নিশ্চিত হওয়ার ঘরে টিক দাও।")
            else:
                st.warning("এই Roll বা ID-এর কোনো Student পাওয়া যায়নি।")

conn.close()
