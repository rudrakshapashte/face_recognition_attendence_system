import streamlit as st
from datetime import date
from database import (
    init_database,
    add_student,
    student_exists,
    get_students,
    get_attendance,
    get_today_stats,
    delete_student
)

st.set_page_config(
    page_title="Face Recognition Attendance System",
    page_icon="👤",
    layout="wide"
)

init_database()

st.title("👤 Face Recognition Attendance System")
st.write("Student Registration and Attendance Management")

stats = get_today_stats()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Students", stats["total_students"])

with col2:
    st.metric("Present Today", stats["present"])

with col3:
    st.metric("Absent Today", stats["absent"])

with col4:
    st.metric("Attendance", f'{stats["percentage"]}%')

st.divider()

menu = st.sidebar.selectbox(
    "Menu",
    [
        "Dashboard",
        "Register Student",
        "Students",
        "Attendance Report"
    ]
)

if menu == "Dashboard":

    st.subheader("Dashboard")
    st.success("Streamlit application is working successfully.")

    attendance = get_attendance()

    if attendance:
        st.dataframe(
            attendance,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No attendance records available.")

elif menu == "Register Student":

    st.subheader("Register Student")

    name = st.text_input("Student Name")
    roll_no = st.text_input("Roll Number")

    camera_image = st.camera_input("Take a photo")

    if st.button("Register Student", type="primary"):

        if not name.strip() or not roll_no.strip():
            st.warning("Please enter both student name and roll number.")

        elif camera_image is None:
            st.warning("Please take a face photo first.")

        elif student_exists(roll_no.strip()):
            st.error("This roll number is already registered.")

        else:
            try:
                student_id = add_student(
                    name.strip(),
                    roll_no.strip()
                )

                st.success(
                    f"Student registered successfully! Student ID: {student_id}"
                )

                st.image(
                    camera_image,
                    caption="Captured Face",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"Registration failed: {e}")

elif menu == "Students":

    st.subheader("Registered Students")

    students = get_students()

    if students:

        st.dataframe(
            students,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        student_options = {
            f'{s["name"]} - {s["roll_no"]}': s["id"]
            for s in students
        }

        selected = st.selectbox(
            "Select student to delete",
            list(student_options.keys())
        )

        if st.button("Delete Selected Student"):

            student_id = student_options[selected]

            try:
                delete_student(student_id)
                st.success("Student deleted successfully.")
                st.rerun()

            except Exception as e:
                st.error(f"Delete failed: {e}")

    else:
        st.info("No students registered yet.")

elif menu == "Attendance Report":

    st.subheader("Attendance Report")

    selected_date = st.date_input(
        "Select Date",
        value=date.today()
    )

    records = get_attendance(
        selected_date.strftime("%Y-%m-%d")
    )

    if records:

        st.dataframe(
            records,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Download Attendance CSV",
            data="\n".join(
                ",".join(str(value) for value in row.values())
                for row in records
            ),
            file_name=f"attendance_{selected_date}.csv",
            mime="text/csv"
        )

    else:
        st.info("No attendance records found for this date.")
