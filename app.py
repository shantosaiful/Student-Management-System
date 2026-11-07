import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(
    page_title="Student Management System (CCN PI)",
    page_icon="🎓",
    layout="wide"
)

# Database
conn = sqlite3.connect(
    "students.db",
    check_same_thread=False
)
cursor = conn.cursor()

# Create table
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
existing_columns = [row[1] for row in cursor.fetchall()]

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

# Admin Password
try:
    ADMIN_PASSWORD = st.secrets["auth"]["admin_password"]
except Exception:
    ADMIN_PASSWORD = None

# Website Title
st.title("🎓 Student Management System (CCN PI)")

# Admin Login
if "admin" not in st.session_state:
    st.session_state.admin = False

with st.sidebar:
    st.header("Admin Login")

    if ADMIN_PASSWORD is None:
        st.error("Admin password সেট করা হয়নি।")

    elif not st.session_state.admin:

        password = st.text_input(
            "Password",
            type="password"
        )

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

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Add Student",
        "View Students",
        "Search Student",
        "Edit Student",
        "Delete Student"
    ])

else:

    tab2, tab3 = st.tabs([
        "View Students",
        "Search Student"
    ])


# Add Student
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
                    name.strip(),
                    roll.strip(),
                    department.strip(),
                    semester.strip(),
                    student_id.strip(),
                    result.strip()
                ]):
                    st.warning("সব তথ্য পূরণ করো।")

                else:
                    try:

                        cursor.execute("""
                            INSERT INTO students
                            (name, roll, department, semester,
                             student_id, result)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            name.strip(),
                            roll.strip(),
                            department.strip(),
                            semester.strip(),
                            student_id.strip(),
                            result.strip()
                        ))

                        conn.commit()

                        st.success("Student added successfully!")

                    except sqlite3.IntegrityError:

                        st.error(
                            "এই Roll অথবা Student ID আগে থেকেই আছে।"
                        )


# View Students
with tab2:

    st.subheader("All Students")

    df = pd.read_sql_query("""
        SELECT
            name AS Name,
            roll AS Roll,
            department AS Department,
            semester AS Semester,
            student_id AS ID,
            result AS Result
        FROM students
        ORDER BY roll
    """, conn)

    st.write("Total Students:", len(df))

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# Search Student
with tab3:

    st.subheader("Search Student")

    search_value = st.text_input(
        "Enter Roll or Student ID"
    )

    if search_value.strip():

        result_df = pd.read_sql_query("""
            SELECT
                name AS Name,
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


# Edit Student (Admin Only)
if st.session_state.admin:

    with tab4:

        st.subheader("Edit Student Information")

        edit_value = st.text_input(
            "Enter Student Roll or ID",
            key="edit_student_search"
        )

        if edit_value.strip():

            student = cursor.execute("""
                SELECT name, roll, department,
                       semester, student_id, result
                FROM students
                WHERE roll = ? OR student_id = ?
            """, (
                edit_value.strip(),
                edit_value.strip()
            )).fetchone()

            if student:

                st.success("Student Found!")

                with st.form("edit_student_form"):

                    new_name = st.text_input(
                        "Student Name",
                        value=student[0] or ""
                    )

                    new_roll = st.text_input(
                        "Roll",
                        value=student[1] or ""
                    )

                    new_department = st.text_input(
                        "Department",
                        value=student[2] or ""
                    )

                    new_semester = st.text_input(
                        "Semester",
                        value=student[3] or ""
                    )

                    new_id = st.text_input(
                        "Student ID",
                        value=student[4] or ""
                    )

                    new_result = st.text_input(
                        "Result",
                        value=student[5] or ""
                    )

                    update = st.form_submit_button(
                        "Update Student"
                    )

                    if update:

                        if not all([
                            new_name.strip(),
                            new_roll.strip(),
                            new_department.strip(),
                            new_semester.strip(),
                            new_id.strip(),
                            new_result.strip()
                        ]):

                            st.warning("সব তথ্য পূরণ করো।")

                        else:

                            try:

                                cursor.execute("""
                                    UPDATE students
                                    SET
                                        name = ?,
                                        roll = ?,
                                        department = ?,
                                        semester = ?,
                                        student_id = ?,
                                        result = ?
                                    WHERE roll = ?
                                """, (
                                    new_name.strip(),
                                    new_roll.strip(),
                                    new_department.strip(),
                                    new_semester.strip(),
                                    new_id.strip(),
                                    new_result.strip(),
                                    student[1]
                                ))

                                conn.commit()

                                st.success(
                                    "Student updated successfully!"
                                )

                            except sqlite3.IntegrityError:

                                st.error(
                                    "এই Roll অথবা Student ID অন্য Student ব্যবহার করছে।"
                                )

            else:

                st.warning(
                    "এই Roll অথবা ID-এর কোনো Student পাওয়া যায়নি।"
                )


# Delete Student (Admin Only)
if st.session_state.admin:

    with tab5:

        st.subheader("Delete Student")

        delete_value = st.text_input(
            "যে Student মুছতে চাও তার Roll অথবা ID লেখো"
        )

        if delete_value.strip():

            student_df = pd.read_sql_query("""
                SELECT
                    name AS Name,
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

                        st.success(
                            "Student deleted successfully!"
                        )

                        st.rerun()

                    else:

                        st.warning(
                            "আগে নিশ্চিত হওয়ার ঘরে টিক দাও।"
                        )

            else:

                st.warning(
                    "এই Roll বা ID-এর কোনো Student পাওয়া যায়নি।"
                )


conn.close()
