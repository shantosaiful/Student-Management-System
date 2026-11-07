```python
import streamlit as st
import sqlite3
import pandas as pd
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

st.set_page_config(
    page_title="Student Information & Management System (CCN PI)",
    page_icon="🎓",
    layout="wide"
)

# Database
conn = sqlite3.connect(
    "students.db",
    check_same_thread=False
)

cursor = conn.cursor()

# Create Table
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

conn.commit()

# Admin Password
try:
    ADMIN_PASSWORD = st.secrets["auth"]["admin_password"]
except Exception:
    ADMIN_PASSWORD = None


# Website Title
st.title("🎓 Student Information & Management System (CCN PI)")
st.caption("Student Information Management Portal")

# Admin Session
if "admin" not in st.session_state:
    st.session_state.admin = False


# Sidebar Login
with st.sidebar:

    st.header("🔐 Admin Login")

    if ADMIN_PASSWORD is None:

        st.error("Admin password সেট করা হয়নি।")

    elif not st.session_state.admin:

        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button("Login", use_container_width=True):

            if password == ADMIN_PASSWORD:

                st.session_state.admin = True
                st.rerun()

            else:

                st.error("Wrong Password")

    else:

        st.success("Admin Logged In")

        if st.button("Logout", use_container_width=True):

            st.session_state.admin = False
            st.rerun()


# Get Student Data
def get_students():

    return pd.read_sql_query("""
        SELECT rowid AS Record,
               name AS Name,
               roll AS Roll,
               department AS Department,
               semester AS Semester,
               student_id AS ID,
               result AS Result
        FROM students
        ORDER BY roll
    """, conn)


# Excel Download
def create_excel(df):

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        df.drop(
            columns=["Record"],
            errors="ignore"
        ).to_excel(
            writer,
            index=False,
            sheet_name="Students"
        )

    return output.getvalue()


# PDF Download
def create_pdf(df):

    output = io.BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=landscape(A4)
    )

    data = [
        [
            "Name",
            "Roll",
            "Department",
            "Semester",
            "Student ID",
            "Result"
        ]
    ]

    for _, row in df.iterrows():

        data.append([
            str(row["Name"]),
            str(row["Roll"]),
            str(row["Department"]),
            str(row["Semester"]),
            str(row["ID"]),
            str(row["Result"])
        ])

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.lightgrey])
    ]))

    document.build([table])

    return output.getvalue()


# Tabs
if st.session_state.admin:

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard",
        "➕ Add Student",
        "👥 View Students",
        "🔍 Search Student",
        "✏️ Edit Student",
        "🗑️ Delete Student"
    ])

else:

    tab1, tab3, tab4 = st.tabs([
        "📊 Dashboard",
        "👥 View Students",
        "🔍 Search Student"
    ])


# Dashboard
with tab1:

    st.subheader("📊 Dashboard")

    df = get_students()

    total_students = len(df)

    total_departments = (
        df["Department"].nunique()
        if not df.empty else 0
    )

    total_semesters = (
        df["Semester"].nunique()
        if not df.empty else 0
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "👨‍🎓 Total Students",
        total_students
    )

    col2.metric(
        "🏫 Departments",
        total_departments
    )

    col3.metric(
        "📚 Semesters",
        total_semesters
    )

    st.divider()

    if not df.empty:

        st.subheader("Department Wise Students")

        department_data = df["Department"].value_counts()

        st.bar_chart(department_data)

        st.subheader("Recent Student Records")

        st.dataframe(
            df.drop(columns=["Record"]).tail(5),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("এখনো কোনো Student যোগ করা হয়নি।")


# Add Student
if st.session_state.admin:

    with tab2:

        st.subheader("➕ Add New Student")

        with st.form("add_student_form"):

            name = st.text_input("Student Name")

            roll = st.text_input("Roll")

            department = st.text_input("Department")

            semester = st.text_input("Semester")

            student_id = st.text_input("Student ID")

            result = st.text_input("Result")

            submitted = st.form_submit_button(
                "Add Student",
                use_container_width=True
            )

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
                            (name, roll, department,
                             semester, student_id, result)
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
with tab3:

    st.subheader("👥 All Students")

    df = get_students()

    st.write("Total Students:", len(df))

    st.dataframe(
        df.drop(columns=["Record"]),
        use_container_width=True,
        hide_index=True
    )

    if not df.empty:

        st.divider()

        col1, col2 = st.columns(2)

        with col1:

            st.download_button(
                "📥 Download Excel",
                data=create_excel(df),
                file_name="students.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col2:

            st.download_button(
                "📄 Download PDF",
                data=create_pdf(df),
                file_name="students.pdf",
                mime="application/pdf",
                use_container_width=True
            )


# Advanced Search
with tab4:

    st.subheader("🔍 Advanced Student Search")

    search_value = st.text_input(
        "Search by Name, Roll, ID, Department or Result"
    )

    df = get_students()

    col1, col2 = st.columns(2)

    with col1:

        departments = ["All"] + sorted(
            df["Department"].dropna().unique().tolist()
        )

        selected_department = st.selectbox(
            "Select Department",
            departments
        )

    with col2:

        semesters = ["All"] + sorted(
            df["Semester"].dropna().unique().tolist()
        )

        selected_semester = st.selectbox(
            "Select Semester",
            semesters
        )

    filtered_df = df.copy()

    if search_value.strip():

        mask = filtered_df.drop(
            columns=["Record"]
        ).astype(str).apply(
            lambda col: col.str.contains(
                search_value.strip(),
                case=False,
                na=False
            )
        ).any(axis=1)

        filtered_df = filtered_df[mask]

    if selected_department != "All":

        filtered_df = filtered_df[
            filtered_df["Department"] == selected_department
        ]

    if selected_semester != "All":

        filtered_df = filtered_df[
            filtered_df["Semester"] == selected_semester
        ]

    st.write("Found Students:", len(filtered_df))

    st.dataframe(
        filtered_df.drop(columns=["Record"]),
        use_container_width=True,
        hide_index=True
    )


# Edit Student
if st.session_state.admin:

    with tab5:

        st.subheader("✏️ Edit Student Information")

        df = get_students()

        if not df.empty:

            selected_record = st.selectbox(
                "Select Student",
                df["Record"].tolist(),
                format_func=lambda x: (
                    f"{df.loc[df['Record'] == x, 'Name'].iloc[0]} "
                    f"- Roll: {df.loc[df['Record'] == x, 'Roll'].iloc[0]}"
                )
            )

            student = df[df["Record"] == selected_record].iloc[0]

            with st.form("edit_student_form"):

                edit_name = st.text_input(
                    "Student Name",
                    value=student["Name"]
                )

                edit_roll = st.text_input(
                    "Roll",
                    value=student["Roll"]
                )

                edit_department = st.text_input(
                    "Department",
                    value=student["Department"]
                )

                edit_semester = st.text_input(
                    "Semester",
                    value=student["Semester"]
                )

                edit_id = st.text_input(
                    "Student ID",
                    value=student["ID"]
                )

                edit_result = st.text_input(
                    "Result",
                    value=student["Result"]
                )

                update = st.form_submit_button(
                    "Update Student",
                    use_container_width=True
                )

                if update:

                    if not all([
                        edit_name.strip(),
                        edit_roll.strip(),
                        edit_department.strip(),
                        edit_semester.strip(),
                        edit_id.strip(),
                        edit_result.strip()
                    ]):

                        st.warning("সব তথ্য পূরণ করো।")

                    else:

                        try:

                            cursor.execute("""
                                UPDATE students
                                SET name = ?,
                                    roll = ?,
                                    department = ?,
                                    semester = ?,
                                    student_id = ?,
                                    result = ?
                                WHERE rowid = ?
                            """, (
                                edit_name.strip(),
                                edit_roll.strip(),
                                edit_department.strip(),
                                edit_semester.strip(),
                                edit_id.strip(),
                                edit_result.strip(),
                                int(selected_record)
                            ))

                            conn.commit()

                            st.success(
                                "Student updated successfully!"
                            )

                            st.rerun()

                        except sqlite3.IntegrityError:

                            st.error(
                                "এই Roll অথবা Student ID অন্য Student ব্যবহার করছে।"
                            )

        else:

            st.info("কোনো Student পাওয়া যায়নি।")


# Delete Student
if st.session_state.admin:

    with tab6:

        st.subheader("🗑️ Delete Student")

        delete_value = st.text_input(
            "Student Roll অথবা ID লেখো",
            key="delete_student_value"
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
                    "কোনো Student পাওয়া যায়নি।"
                )


conn.close()
```
