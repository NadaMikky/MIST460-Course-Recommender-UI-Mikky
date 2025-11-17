import pandas as pd
import streamlit as st
import requests

FASTAPI_URL = "https://MIST460-Course-Recommender-Apis-Mikky.azurewebsites.net" #change to your lastname

# ensure session state key exists to avoid KeyError when UI first loads
if "app_user_id" not in st.session_state:
	# default 0 means "not validated yet"
	st.session_state.app_user_id = 0

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
		# handle both {"data": [...]} and direct object/list responses
		if isinstance(payload, dict) and "data" in payload:
			rows = payload.get("data", [])
		elif isinstance(payload, list):
			rows = payload
		elif isinstance(payload, dict):
			# single object response; wrap in list
			rows = [payload]
		else:
			rows = []
		df = pd.DataFrame(rows)
		return df

	else:
		try:
			error_detail = response.json().get("detail", response.text)
		except:
			error_detail = response.text
		st.error(f"Error fetching data: {response.status_code} — {error_detail}")
		return None
	
#create a sidebar with a dropdown to select the API endpoint
st.sidebar.title("Course Recommender Functionalities")
api_endpoint = st.sidebar.selectbox(
	"api_endpoint",
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
elif api_endpoint == "find_current_semester_course_offerings":
	st.header("Find Current Semester Course Offerings")
	subject_code = st.text_input("Subject Code")
	course_number = st.text_input("Course Number")
	if st.button("Find Offerings"):
		# corrected endpoint name (plural) to match API
		df = fetch_data("find_current_semester_course_offerings/", {"subjectCode": subject_code, "courseNumber": course_number})
		if df is not None and not df.empty:
			st.dataframe(df)
		else:
			st.info("No course offerings found for the specified course.")

# 3. Enroll Student in Course Offering
elif api_endpoint == "enroll_student_in_course_offering":
	st.header("Enroll Student in Course Offering")
	student_id = st.number_input("Student ID", value=st.session_state.get("app_user_id", 0), disabled=True)
	course_offering_id = st.number_input("Course Offering ID", min_value=1, step=1)
	if st.button("Enroll"):
		df = fetch_data(
			"enroll_student_in_course_offering/",
			{"studentID": student_id, "courseOfferingID": course_offering_id},
			method="post"
		)
		if df is not None and not df.empty:
			# handle multiple possible response field names
			enroll_succeeded = None
			if "EnrollmentSucceeded" in df.columns:
				enroll_succeeded = bool(df["EnrollmentSucceeded"].values[0])
			elif "enrollmentStatus" in df.columns:
				# some APIs return a status string instead
				enroll_succeeded = str(df["enrollmentStatus"].values[0]).lower() in ("enrolled","success","enrollment succeeded")
			elif "EnrollmentStatus" in df.columns:
				enroll_succeeded = str(df["EnrollmentStatus"].values[0]).lower() in ("enrolled","success")
			if enroll_succeeded is True:
				st.success("Enrollment successful.")
			else:
				# try to show a meaningful message if available
				response_msg = None
				for key in ("EnrollmentResponse","enrollmentResponse","enrollmentStatus","EnrollmentStatus"):
					if key in df.columns:
						response_msg = str(df[key].values[0])
						break
				output_string = "Enrollment failed." + (f" {response_msg}" if response_msg else "")
				st.error(output_string)
		else:
			st.error("Could not complete enrollment request")

# 4. Get Student Enrolled Course Offerings
elif api_endpoint == "get_student_enrolled_course_offerings":
	st.header("Get Student Enrolled Course Offerings")
	student_id = st.number_input("Student ID", value=st.session_state.get("app_user_id", 0), disabled=True)
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
elif api_endpoint == "check_if_student_has_taken_all_prerequisites_for_course":
	st.header("Check If Student Has Taken All Prerequisites for a Course")
	student_id = st.number_input("Student ID", value=st.session_state.get("app_user_id", 0), disabled=True)
	subject_code = st.text_input("Subject Code")
	course_number = st.text_input("Course Number")
	if st.button("Check Prereqs"):
		# corrected endpoint name to match API
		df = fetch_data(
			"check_if_student_has_taken_all_prerequisites_for_course/",
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

elif api_endpoint == "drop_student_from_course_offering":
	st.header("Drop Student from Course Offering")
	student_id = st.number_input("Student ID", value=st.session_state.get("app_user_id", 0), disabled=True)
	course_offering_id = st.number_input("Course Offering ID", min_value=1, step=1)
	if st.button("Drop"):
		df = fetch_data(
			"drop_student_from_course_offering/",
			{"studentID": student_id, "courseOfferingID": course_offering_id},
			method="post"
		)

		# Defensive checks
		if df is None:
			st.error("Could not complete drop request")
		elif df.empty:
			st.info("No enrollment record returned for the specified student/course.")
		else:
			# Try multiple column/key names and embedded dict responses
			status = None
			candidate_keys = ("EnrollmentStatus","enrollmentStatus","enrollment_status","enrollmentstatus","status","EnrollmentSucceeded","EnrollmentResponse","enrollmentResponse")
			for key in candidate_keys:
				if key in df.columns:
					status = df[key].values[0]
					break

			# If first cell is a dict-like object, look inside it
			if status is None:
				first_cell = df.iloc[0,0]
				if isinstance(first_cell, dict):
					for key in candidate_keys:
						if key in first_cell:
							status = first_cell.get(key)
							break

			# Normalize and evaluate status
			if status is not None:
				status_str = str(status).strip()
				if status_str.lower() in ("dropped","drop","success","dropped successfully"):
					st.success("Drop successful.")
				else:
					st.error("Drop failed. " + status_str)
			else:
				# Could not determine status — surface the raw response for debugging
				st.error("Drop failed. Unable to determine enrollment status from response.")
				st.write(df)