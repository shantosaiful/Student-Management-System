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

conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

# Students Table
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

# Check Existing Columns
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

# Semester Results Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS semester_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll TEXT NOT NULL,
    semester TEXT NOT NULL,
    cgpa REAL NOT NULL,
    UNIQUE(roll, semester),
    FOREIGN KEY(roll)
        REFERENCES students(roll)
        ON UPDATE CASCADE
        ON DELETE CASCADE
)
""")

conn.commit()

# Semester List
semesters = [
    "1st Semester",
    "2nd Semester",
    "3rd Semester",
    "4th Semester",
    "5th Semester",
    "6th Semester",
    "7th Semester",
    "8th Semester"
]

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


# Student Search Function
def find_student(value):

    return cursor.execute("""
        SELECT name, roll, department,
               semester, student_id
        FROM students
        WHERE roll = ? OR student_id = ?
    """, (value, value)).fetchone()


# Student Information Display
def show_student(student):

    st.write("**Student Name:**", student[0])
    st.write("**Roll:**", student[1])
    st.write("**Department:**", student[2])
    st.write("**Current Semester:**", student[3])
    st.write("**Student ID:**", student[4])


# Semester Result Display
def show_results(roll):

    results = pd.read_sql_query("""
        SELECT
            semester AS Semester,
            cgpa AS CGPA
        FROM semester_results
        WHERE roll = ?
        ORDER BY
            CAST(
                REPLACE(
                    REPLACE(semester, 'st Semester', ''),
                    'nd Semester', ''
                ) AS INTEGER
            )
    """, conn, params=(roll,))

    st.subheader("Semester Wise CGPA")

    if not results.empty:

        results["CGPA"] = results["CGPA"].map(
            lambda x: f"{x:.2f}"
        )

        st.dataframe(
            results,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("এখনো কোনো Semester Result যোগ করা হয়নি।")


# Tabs
if st.session_state.admin:

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "Add Student",
        "View Students",
        "Search Student",
        "Add Semester Result",
        "Edit Student",
        "Edit Semester Result",
        "Delete Semester Result",
        "Delete Student"
    ])

else:

    tab2, tab3 = st.tabs([
        "View Students",
        "Search Student"
    ])


# =====================================
# ADD STUDENT
# =====================================

if st.session_state.admin:

    with tab1:

        st.subheader("Add New Student")

        with st.form("add_student_form"):

            name = st.text_input("Student Name")
            roll = st.text_input("Roll")
            department = st.text_input("Department")
            semester = st.selectbox(
                "Current Semester",
                semesters
            )
            student_id = st.text_input("Student ID")

            submitted = st.form_submit_button(
                "Add Student"
            )

            if submitted:

                if not all([
                    name.strip(),
                    roll.strip(),
                    department.strip(),
                    student_id.strip()
                ]):

                    st.warning("সব তথ্য পূরণ করো।")

                else:

                    try:

                        cursor.execute("""
                            INSERT INTO students
                            (name, roll, department,
                             semester, student_id, result)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            name.strip(),
                            roll.strip(),
                            department.strip(),
                            semester,
                            student_id.strip(),
                            ""
                        ))

                        conn.commit()

                        st.success(
                            "Student added successfully!"
                        )

                    except sqlite3.IntegrityError:

                        st.error(
                            "এই Roll অথবা Student ID আগে থেকেই আছে।"
                        )


# =====================================
# VIEW STUDENTS
# =====================================

with tab2:

    st.subheader("All Students")

    df = pd.read_sql_query("""
        SELECT
            name AS Name,
            roll AS Roll,
            department AS Department,
            semester AS Semester,
            student_id AS ID
        FROM students
        ORDER BY roll
    """, conn)

    st.write("Total Students:", len(df))

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.subheader("All Semester Results")

    all_results = pd.read_sql_query("""
        SELECT
            s.name AS Name,
            s.roll AS Roll,
            s.student_id AS ID,
            r.semester AS Semester,
            r.cgpa AS CGPA
        FROM semester_results r
        JOIN students s ON s.roll = r.roll
        ORDER BY s.roll, r.id
    """, conn)

    st.dataframe(
        all_results,
        use_container_width=True,
        hide_index=True
    )


# =====================================
# SEARCH STUDENT
# =====================================

with tab3:

    st.subheader("Search Student")

    search_value = st.text_input(
        "Enter Roll or Student ID",
        key="search_student"
    )

    if search_value.strip():

        student = find_student(
            search_value.strip()
        )

        if student:

            show_student(student)

            show_results(student[1])

        else:

            st.warning(
                "কোনো Student পাওয়া যায়নি।"
            )


# =====================================
# ADD SEMESTER RESULT
# =====================================

if st.session_state.admin:

    with tab4:

        st.subheader("Add Semester Result")

        with st.form("add_result_form"):

            result_search = st.text_input(
                "Enter Student Roll or ID"
            )

            result_semester = st.selectbox(
                "Select Semester",
                semesters
            )

            cgpa = st.number_input(
                "Enter CGPA",
                min_value=0.0,
                max_value=4.0,
                value=0.0,
                step=0.01,
                format="%.2f"
            )

            add_result = st.form_submit_button(
                "Save Semester Result"
            )

            if add_result:

                if not result_search.strip():

                    st.warning("Roll অথবা ID লেখো।")

                else:

                    student = find_student(
                        result_search.strip()
                    )

                    if student:

                        try:

                            cursor.execute("""
                                INSERT INTO semester_results
                                (roll, semester, cgpa)
                                VALUES (?, ?, ?)
                            """, (
                                student[1],
                                result_semester,
                                cgpa
                            ))

                            conn.commit()

                            st.success(
                                "Semester CGPA added successfully!"
                            )

                        except sqlite3.IntegrityError:

                            st.error(
                                "এই Semester-এর Result আগে থেকেই আছে। Edit অপশন ব্যবহার করো।"
                            )

                    else:

                        st.error(
                            "Student পাওয়া যায়নি।"
                        )


# =====================================
# EDIT STUDENT
# =====================================

if st.session_state.admin:

    with tab5:

        st.subheader("Edit Student Information")

        edit_search = st.text_input(
            "Enter Student Roll or ID",
            key="edit_student_search"
        )

        if edit_search.strip():

            student = find_student(
                edit_search.strip()
            )

            if student:

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

                    current_semester = (
                        student[3]
                        if student[3] in semesters
                        else semesters[0]
                    )

                    new_semester = st.selectbox(
                        "Current Semester",
                        semesters,
                        index=semesters.index(
                            current_semester
                        )
                    )

                    new_id = st.text_input(
                        "Student ID",
                        value=student[4] or ""
                    )

                    update_student = st.form_submit_button(
                        "Update Student"
                    )

                    if update_student:

                        if not all([
                            new_name.strip(),
                            new_roll.strip(),
                            new_department.strip(),
                            new_id.strip()
                        ]):

                            st.warning(
                                "সব তথ্য পূরণ করো।"
                            )

                        else:

                            try:

                                cursor.execute("""
                                    UPDATE students
                                    SET
                                        name = ?,
                                        roll = ?,
                                        department = ?,
                                        semester = ?,
                                        student_id = ?
                                    WHERE roll = ?
                                """, (
                                    new_name.strip(),
                                    new_roll.strip(),
                                    new_department.strip(),
                                    new_semester,
                                    new_id.strip(),
                                    student[1]
                                ))

                                conn.commit()

                                st.success(
                                    "Student updated successfully!"
                                )

                            except sqlite3.IntegrityError:

                                st.error(
                                    "এই Roll অথবা ID অন্য Student ব্যবহার করছে।"
                                )

            else:

                st.warning(
                    "Student পাওয়া যায়নি।"
                )


# =====================================
# EDIT SEMESTER RESULT
# =====================================

if st.session_state.admin:

    with tab6:

        st.subheader("Edit Semester Result")

        edit_result_search = st.text_input(
            "Enter Student Roll or ID",
            key="edit_result_search"
        )

        if edit_result_search.strip():

            student = find_student(
                edit_result_search.strip()
            )

            if student:

                show_student(student)

                result_rows = cursor.execute("""
                    SELECT semester, cgpa
                    FROM semester_results
                    WHERE roll = ?
                    ORDER BY id
                """, (student[1],)).fetchall()

                if result_rows:

                    available_semesters = [
                        row[0] for row in result_rows
                    ]

                    selected_semester = st.selectbox(
                        "Select Semester to Edit",
                        available_semesters
                    )

                    old_result = next(
                        row[1]
                        for row in result_rows
                        if row[0] == selected_semester
                    )

                    with st.form("edit_result_form"):

                        new_cgpa = st.number_input(
                            "New CGPA",
                            min_value=0.0,
                            max_value=4.0,
                            value=float(old_result),
                            step=0.01,
                            format="%.2f"
                        )

                        update_result = st.form_submit_button(
                            "Update CGPA"
                        )

                        if update_result:

                            cursor.execute("""
                                UPDATE semester_results
                                SET cgpa = ?
                                WHERE roll = ?
                                AND semester = ?
                            """, (
                                new_cgpa,
                                student[1],
                                selected_semester
                            ))

                            conn.commit()

                            st.success(
                                "CGPA updated successfully!"
                            )

                            st.rerun()

                else:

                    st.info(
                        "এই Student-এর কোনো Result নেই।"
                    )

            else:

                st.warning(
                    "Student পাওয়া যায়নি।"
                )


# =====================================
# DELETE SEMESTER RESULT
# =====================================

if st.session_state.admin:

    with tab7:

        st.subheader("Delete Semester Result")

        delete_result_search = st.text_input(
            "Enter Student Roll or ID",
            key="delete_result_search"
        )

        if delete_result_search.strip():

            student = find_student(
                delete_result_search.strip()
            )

            if student:

                show_student(student)

                result_rows = cursor.execute("""
                    SELECT semester, cgpa
                    FROM semester_results
                    WHERE roll = ?
                    ORDER BY id
                """, (student[1],)).fetchall()

                if result_rows:

                    semester_to_delete = st.selectbox(
                        "Select Semester",
                        [row[0] for row in result_rows]
                    )

                    confirm_result_delete = st.checkbox(
                        "আমি নিশ্চিত, এই Semester Result মুছতে চাই।"
                    )

                    if st.button("Delete Semester Result"):

                        if confirm_result_delete:

                            cursor.execute("""
                                DELETE FROM semester_results
                                WHERE roll = ?
                                AND semester = ?
                            """, (
                                student[1],
                                semester_to_delete
                            ))

                            conn.commit()

                            st.success(
                                "Semester Result deleted successfully!"
                            )

                            st.rerun()

                        else:

                            st.warning(
                                "আগে নিশ্চিত হওয়ার ঘরে টিক দাও।"
                            )

                else:

                    st.info(
                        "কোনো Semester Result পাওয়া যায়নি।"
                    )

            else:

                st.warning(
                    "Student পাওয়া যায়নি।"
                )


# =====================================
# DELETE STUDENT
# =====================================

if st.session_state.admin:

    with tab8:

        st.subheader("Delete Student")

        delete_search = st.text_input(
            "Enter Student Roll or ID",
            key="delete_student_search"
        )

        if delete_search.strip():

            student = find_student(
                delete_search.strip()
            )

            if student:

                show_student(student)

                show_results(student[1])

                confirm_delete = st.checkbox(
                    "আমি নিশ্চিত, এই Student-এর সব তথ্য মুছতে চাই।"
                )

                if st.button("Delete Student"):

                    if confirm_delete:

                        cursor.execute("""
                            DELETE FROM students
                            WHERE roll = ?
                        """, (student[1],))

                        conn.commit()

                        st.success(
                            "Student and all semester results deleted!"
                        )

                        st.rerun()

                    else:

                        st.warning(
                            "আগে নিশ্চিত হওয়ার ঘরে টিক দাও।"
                        )

            else:

                st.warning(
                    "Student পাওয়া যায়নি।"
                )


conn.close()
