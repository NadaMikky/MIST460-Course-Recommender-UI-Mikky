from typing import Dict, Optional
import pandas as pd
import streamlit as st
import requests

FASTAPI_URL = "http://localhost:8000" #change this

# set up a method fetch data for each endpoint
def fetch_data(endpoint: str, params: Optional[Dict] = None, method: str = "GET"):
    try:
        # helpers to make GET or POST requests based on method parameter
        if method == "GET":
            response = requests.get(f"{FASTAPI_URL}/{endpoint}", params=params)
        elif method == "POST":
            response = requests.post(f"{FASTAPI_URL}/{endpoint}", json=params)
        else:
            # Handle other HTTP methods if needed
            st.error(f"Unsupported HTTP method: {method}")
            return None

        if response.status_code != 200:
            st.error(f"Server returned error {response.status_code}")
            return None

        data = response.json()

        # Some endpoints return {"data": [...]} others return {"prerequisites": ...}
        # Standardize to DataFrame if list-like data is present
        for key in ["rows", "data", "prerequisites"]:
            if key in data and isinstance(data[key], list):
                return pd.DataFrame(data[key])

        return data  # if scalar response (e.g., boolean result)

    except Exception as e:
        st.error(f"Request failed: {e}")
        return None


# create a sidebar with a dropdown to select the API endpoint
st.sidebar.title("Course Recommender Functionalities")
api_endpoint = st.sidebar.selectbox(
    "Select API Endpoint",
    [
        "validate_user",
        "find_current_semester_course_offerings",
        "find_prerequisites",
        "check_if_student_has_taken_all_prerequisites_for_course",
        "enroll_student_in_course_offering",
        "get_student_enrolled_course_offerings",
        "drop_student_from_course_offering"
    ]
)

# 1. validate_user
if api_endpoint == "validate_user":
    st.header("Validate User")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Validate"):
        df = fetch_data("validate_user/", params={"username": username, "password": password})
        if df is not None:
            st.success("User validated successfully!")
            st.dataframe(df)
        else:
            st.error("Invalid username or password.")

# 2. find_current_semester_course_offerings
elif api_endpoint == "find_current_semester_course_offerings":
    st.header("Find Current Semester Course Offerings")
    subject_code = st.text_input("Subject Code (e.g., MIST)")
    course_number = st.text_input("Course Number (eg., 460)")

    if st.button("Find Offerings"):
        df = fetch_data("find_current_semester_course_offerings/", params={"subject_code": subject_code})
        if df is not None and not df.empty:
            st.dataframe(df)
        else:
            st.info("No course offerings found for that subject!")

# 3. find_prerequisites
elif api_endpoint == "find_prerequisites":
    st.header("Find Prerequisites for a Course")
    subject_code = st.text_input("Course Code (e.g., MIST)")
    course_number = st.text_input("Course Number (e.g., 460)")

    if st.button("Find Prerequisites"):
        df = fetch_data("find_prerequisites/", params={"subject_code": subject_code, "course_number": course_number})
        if df is not None and not df.empty:
            st.dataframe(df)
        else:
            st.info("No prerequisites found for that course!")

# 4. check_if_student_has_taken_all_prerequisites_for_course
elif api_endpoint == "check_if_student_has_taken_all_prerequisites_for_course":
    st.header("Check if Student has Taken All Prerequisites for a Course")
    StudentID = st.number_input("Student ID", min_value=1, step=1)
    subject_code = st.text_input("Course Code (e.g., MIST)")
    course_number = st.text_input("Course Number (e.g., 460)")

    if st.button("Check Prerequisites"):
        result = fetch_data(
            "check_if_student_has_taken_all_prerequisites_for_course/",
            params={"student_id": student_id, "course_code": subject_code, "course_number": course_number}
        )
        if result is not None:
            if result.get("has_taken_all_prerequisites"):
                st.success("Student has taken all prerequisites for the course.")
            else:
                st.warning("Student has NOT taken all prerequisites for the course.")
        else:
            st.error("Error checking prerequisites.")

# 5. enroll_student_in_course_offering
elif api_endpoint == "enroll_student_in_course_offering":
    st.header("Enroll Student in a Course Offering")
    StudentID = st.number_input("Student ID", min_value=1)
    CRN = st.number_input("CRN", min_value=1)

    if st.button("Enroll"):
        # Call the API
        df = fetch_data(
            "enroll_student_in_course_offering/",
            params={"student_id": student_id, "CRN": CRN},
            method="POST"
        )

        if df is not None:
            # Check if the enrollment succeeded
            if df.get("EnrollmentSucceeded", [False])[0]:
                st.success("Enrollment successful.")
            else:
                # Provide detailed feedback if enrollment failed
                enrollment_msg = df.get("EnrollmentResponse", ["No additional info"])[0]
                st.error(f"Enrollment failed: {enrollment_msg}")
        else:
            st.error("Enrollment request failed: No response from server.")
