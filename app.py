import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(
    page_title="Student Management System",
    page_icon="🎓",
    layout="centered"
)

conn = sqlite3.connect("students.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    name TEXT,
    roll TEXT UNIQUE,
    age TEXT,
    department TEXT,
    semester TEXT
)
""")
conn.commit()

st.title("🎓 Student Management System")
st.write("Manage Your Student Information")

tab1, tab2, tab3 = st.tabs([
    "Add Student",
    "View Students",
    "Search Student"
])

with tab1:
    st.subheader("Add New Student")

    with st.form("add_form"):
        name = st.text_input("Student Name")
        roll = st.text_input("Roll Number")
        age = st.text_input("Age")
        department = st.text_input("Department")
        semester = st.text_input("Semester")

        submit = st.form_submit_button("Add Student")

        if submit:
            if name and roll and age and department and semester:
                try:
                    cursor.execute(
                        "INSERT INTO students VALUES (?, ?, ?, ?, ?)",
                        (name, roll, age, department, semester)
                    )
                    conn.commit()
                    st.success("Student Added Successfully!")
                except sqlite3.IntegrityError:
                    st.error("This Roll Number Already Exists!")
            else:
                st.warning("Please Fill All Information")

with tab2:
    st.subheader("All Students")

    cursor.execute("SELECT * FROM students")
    data = cursor.fetchall()

    if data:
        df = pd.DataFrame(
            data,
            columns=["Name", "Roll", "Age", "Department", "Semester"]
        )
        st.dataframe(df, use_container_width=True)
        st.success(f"Total Students: {len(data)}")
    else:
        st.info("No Student Found")

with tab3:
    st.subheader("Search Student")

    search_roll = st.text_input("Enter Roll Number")

    if st.button("Search"):
        cursor.execute(
            "SELECT * FROM students WHERE roll = ?",
            (search_roll,)
        )
        result = cursor.fetchone()

        if result:
            st.success("Student Found!")
            st.write("Name:", result[0])
            st.write("Roll:", result[1])
            st.write("Age:", result[2])
            st.write("Department:", result[3])
            st.write("Semester:", result[4])
        else:
            st.error("Student Not Found!")
