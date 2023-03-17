import uuid
import behave
import requests
from testing_objects.test_config import API_URL
from testing_objects.course_template import COURSE_TEMPLATE_INPUT_DATA
from environment import create_course
from e2e.gke_api_tests.secrets_helper import get_student_email_and_token

# ------------------------------list student to Section-------------------------------------



@behave.given("A section has a students enrolled")
def step_impl_1(context):
  context.url = f'{API_URL}/sections/{context.enroll_student_data["section_id"]}/students'


@behave.when("API request with valid section Id is sent")
def step_impl_2(context):
  resp = requests.get(context.url,headers=context.header)
  context.status = resp.status_code
  context.response = resp.json()

@behave.then("Section will be fetch using the given id and list of studnets enrolled")
def step_impl_3(context):
    assert context.status == 200, "Status 200"



# ------------------------------Delete student to Section-------------------------------------


@behave.given("A section has a students enrolled and has course enrollment mapping present")
def step_impl_4(context):
  context.url = f'{API_URL}/sections/{context.enroll_student_data["section_id"]}/students/{context.enroll_student_data["user_id"]}'


@behave.when("API request with valid section Id and user id is sent to delete student")
def step_impl_5(context):
  resp = requests.delete(context.url,headers=context.header)
  context.status = resp.status_code
  context.response = resp.json()


@behave.then("Student is marked as inactive in course enrollment mapping and removed from google classroom using user id")
def step_impl_6(context):
  assert context.status == 200, "Status 200"


#----delete using email---------

@behave.given("A user wants to remove a student from a section using email id")
def step_impl_7(context):
  context.url = f'{API_URL}/sections/{context.enroll_student_data["section_id"]}/students/{context.enroll_student_data["email"]}'


@behave.when("API request with valid section Id and email is sent to delete student")
def step_impl_8(context):
  resp = requests.delete(context.url, headers=context.header)
  context.status = resp.status_code
  context.response = resp.json()


@behave.then("Student is marked as inactive in course enrollment mapping and removed from google classroom using email id")
def step_impl_9(context):
  print(f"______DELETE USING EMAIL RESPONSE______:{context.response},{context.status}")
  assert context.status == 200, "Status 200"

#-------------------------------Get student in cohort--------------------------------------
@behave.given("A section has a students enrolled in cohort")
def step_impl_10(context):
  context.url = f'{API_URL}/cohorts/{context.enroll_student_data["cohort_id"]}/students/{context.enroll_student_data["user_id"]}'

@behave.when("API request with valid cohort Id  user_id is sent")
def step_impl_11(context):
  resp = requests.get(context.url,headers=context.header)
  print("GET student cohort response",resp.status_code)
  print(resp.json())
  context.status = resp.status_code
  context.response = resp.json()

@behave.then("student details will be fetch using the given id for cohort")
def step_impl_12(context):
    assert context.status == 200, "Status 200"
    assert context.response["data"]["cohort_id"] == context.enroll_student_data["cohort_id"]

#------------------------------Invite student to section------------------------------
@behave.given("A user is invited to a section using email")
def step_impl_13(context):
  print("IN Invite student ID",context.sections.id)
  student_email =get_student_email_and_token()
  context.url = f'{API_URL}/sections/{context.sections.id}/invite/{student_email["invite_student_email"]}'



@behave.when("API request is sent with valid section id and email")
def step_impl_14(context):
  resp = requests.post(context.url,headers=context.header)
  print(resp.json())
  context.status = resp.status_code
  context.response = resp.json()


@behave.then("Invitation is sent to student via email and course enrollmet object with status invited is created")
def step_impl_15(context):
  assert context.status == 200, "Status 200"
  assert "invitation_id" in context.response["data"].keys()

#-------------------------------Update invites patch api--------------------------------------
@behave.given("A student is invited and has accepted the invite via email")
def step_impl_16(context):
  context.url = f'{API_URL}/sections/update_invites'

@behave.when("cron job is triggered and calls update_invites endpoint")
def step_impl_17(context):
  resp = requests.patch(context.url,headers=context.header)
  context.status = resp.status_code
  context.response = resp.json()

@behave.then("student details will be updated in user collection and course enrollment mapping status is updated to active")
def step_impl_18(context):
    assert context.status == 200, "Status 200"

#------------------------------Invite student to cohort------------------------------
@behave.given("A user is invited to a cohort_id using email")
def step_impl_19(context):
  print("IN Invite student ID",context.cohort.id)
  student_email =get_student_email_and_token()
  context.url = f'{API_URL}/cohorts/{context.cohort.id}/invite/{student_email["invite_student_email"]}'



@behave.when("API request is sent with valid cohort id and email")
def step_impl_20(context):
  resp = requests.post(context.url,headers=context.header)
  print("THIS IS RESPONSE FROM INVITE STUDNET cohort ")
  print(resp.json())
  context.status = resp.status_code
  context.response = resp.json()
  print("ADD_STUDENT RESPONSE _________",resp.json())


@behave.then("Invitation is sent to student via email and student invited to section with min count in cohort")
def step_impl_21(context):
  assert context.status == 200, "Status 200"
  assert "invitation_id" in context.response["data"].keys()
