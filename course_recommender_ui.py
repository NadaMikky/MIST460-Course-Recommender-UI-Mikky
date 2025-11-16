import pandas as pd
import streamlit as st
import requests

FASTAPI_URL = "https://MIST460-Course-Recommender-Apis-Mikky.azurewebsites.net" #change to your lastname

def fetch_data(endpoint : str, params : dict, method: str = "get") -> pd.DataFrame:
    if method == "get":
        response = requests.get(f"{FASTAPI_URL}/{endpoint}", params=params)
    elif method == "post":
        response = requests.post(f"{FASTAPI_URL}/{endpoint}", params=params)
    else:
        st.error(f"Unsupported HTTP method: {method}")
        return None

    if response.status_code == 200:
        payload = response.json()
        rows = payload.get("data", [])
        df = pd.DataFrame(rows)
        return df

    else:
        st.error(f"Error fetching data: {response.status_code}")
        return None
    
#create a sidebar with a dropdown to select the API endpoint
st.sidebar.title("Course Recommender Functionalities")
api_endpoint = st.sidebar.selectbox(
    "api_endpoint",
    [
        "validate_user",
        "find_current_semester_course_offering",
        "find_prerequisites",
        "check_prereqs",
        "enroll_student",
        "get_student_enrolled_course_offerings",
        "drop_student"
    ]
)

# 1. Validate User
if api_endpoint == "validate_user":
    st.header("Validate User")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Validate"):
        df = fetch_data("validate_user/", {"username": username, "password": password})
        if df is not None:
            st.success("User validated successfully!")
            output_string = "App User ID: " + str(df["AppUserID"].values[0]) + ", Full Name: " + df["FullName"].iloc[0]
            st.write(output_string)
            st.session_state.app_user_id = df["AppUserID"].values[0]

        else:
            st.error("Invalid username or password.")

# 2. Find Current Semester Course Offerings
elif api_endpoint == "find_current_semester_course_offering":
    st.header("Find Current Semester Course Offerings")
    subject_code = st.text_input("Subject Code")
    course_number = st.text_input("Course Number")
    if st.button("Find Offerings"):
        df = fetch_data("find_current_semester_course_offering/", {"subjectCode": subject_code, "courseNumber": course_number})
        if df is not None and not df.empty:
            st.dataframe(df)
        else:
            st.info("No course offerings found for the specified course.")

# 3. Enroll Student in Course Offering
elif api_endpoint == "enroll_student":
    st.header("Enroll Student in Course Offering")
    student_id = st.number_input("Student ID", value=st.session_state.app_user_id, disabled=True)
    course_offering_id = st.number_input("Course Offering ID", min_value=1, step=1)
    if st.button("Enroll"):
        df = fetch_data(
            "enroll_student/",
            {"studentID": student_id, "courseOfferingID": course_offering_id},
            method="post"
        )
        if df is not None and not df.empty:
            if df["EnrollmentSucceeded"].values[0] == True:
                st.success("Enrollment successful.")
            else:
                output_string = "Enrollment failed. " + df["EnrollmentResponse"].values[0]
                st.error(output_string)
        else:
            st.error("Could not complete enrollment request")

# 4. Get Student Enrolled Course Offerings
elif api_endpoint == "get_student_enrolled_course_offerings":
    st.header("Get Student Enrolled Course Offerings")
    student_id = st.number_input("Student ID", value=st.session_state.app_user_id, disabled=True)
    if st.button("Get Student's Enrollments"):
        df = fetch_data("get_student_enrolled_course_offerings/", {"studentID": student_id})
        if df is not None and not df.empty:
            st.dataframe(df)
        else:
            st.info("No enrolled course offerings found for the specified student.")

# 5. Find Prerequisites for a Course
elif api_endpoint == "find_prerequisites":
    st.header("Find Prerequisites for a Course")
    subject_code = st.text_input("Subject Code")
    course_number = st.text_input("Course Number")
    if st.button("Find Prerequisites"):
        df = fetch_data("find_prerequisites/", {"subjectCode": subject_code, "courseNumber": course_number})
        if df is not None and not df.empty:
            st.dataframe(df)
        else:
            st.info("No prerequisites found for the specified course.")

#6. Check If Student Has Taken All Prerequisites for a Course
elif api_endpoint == "check_prereqs":
    st.header("Check If Student Has Taken All Prerequisites for a Course")
    student_id = st.number_input("Student ID", value=st.session_state.app_user_id, disabled=True)
    subject_code = st.text_input("Subject Code")
    course_number = st.text_input("Course Number")
    if st.button("Check Prereqs"):
        df = fetch_data(
            "check_prerequisites/",
            {"studentID": student_id, "subjectCode": subject_code, "courseNumber": course_number}
        )
        if df is not None:
            if df.empty:
                st.success("The student has taken all prerequisites for the specified course.")
            else:
                st.warning("The student has NOT taken all prerequisites for the specified course. Missing prerequisites:")
                st.dataframe(df)
        else:
            st.error("Error checking prerequisites.")

elif api_endpoint == "drop_student":
    st.header("Drop Student from Course Offering")
    student_id = st.number_input("Student ID", value=st.session_state.app_user_id, disabled=True)
    course_offering_id = st.number_input("Course Offering ID", min_value=1, step=1)
    if st.button("Drop"):
        df = fetch_data(
            "drop_student/",
            {"studentID": student_id, "courseOfferingID": course_offering_id},
            method="post"
        )
        if df["EnrollmentStatus"].values[0] == "Dropped":
             st.success("Drop successful.")
        else:
             output_string = "Drop failed. " + df["EnrollmentStatus"].values[0]
             st.error(output_string)