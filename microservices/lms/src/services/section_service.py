"""Section API services"""
import traceback
import datetime
import requests
from common.utils import classroom_crud
from common.utils.bq_helper import insert_rows_to_bq
from common.utils.secrets import get_backend_robot_id_token
from common.utils.logging_handler import Logger
from common.models import Section, CourseEnrollmentMapping, User
from common.utils.http_exceptions import (InternalServerError,
                                          ResourceNotFound)
from common.utils.errors import ValidationError
from services import common_service
from config import BQ_TABLE_DICT, BQ_DATASET


# disabling for linting to pass
# pylint: disable = broad-except, line-too-long
def copy_course_background_task(course_template_details,
                                sections_details,
                                cohort_details,
                                headers,
                                message=""):
  """Create section  Background Task to copy course and updated database
  for newly created section
  Args:
    course_template_details (template object): course template object which
    will referenced in section
    sections_details (str):Input section details provided by user in API
    cohort_details(str):course template object which will
    referenced in section
    headers(str):Authentications headers
  Raises:
    HTTPException: 500 Internal Server Error if something fails

  Returns:
    True : (bool) on success
  """
  try:
    # Create a new course
    Logger.info(
        f"Background Task started for the cohort id {cohort_details.id}\
                course template {course_template_details.id} \
                with section name{sections_details.name}")
    new_course = classroom_crud.create_course(course_template_details.name,
                                              sections_details.description,
                                              sections_details.name, "me")

    # Create section with the required fields
    section = Section()
    section.name = course_template_details.name
    section.section = sections_details.name
    section.description = sections_details.description
    section.max_students = sections_details.max_students
    # Reference document can be get using get() method
    section.course_template = course_template_details
    section.cohort = cohort_details
    section.classroom_id = new_course["id"]
    section.classroom_code = new_course["enrollmentCode"]
    section.classroom_url = new_course["alternateLink"]
    section.enrolled_students_count = 0
    section.status = "PROVISIONING"
    section_id = section.save().id
    classroom_id = new_course["id"]

    error_flag = False
    target_folder_id = new_course["teacherFolder"]["id"]
    Logger.info(f"ID of target drive folder for section {target_folder_id}")

    # Get topics of current course
    topics = classroom_crud.get_topics(course_template_details.classroom_id)
    # add new_course to pubsub topic for both course work and roaster changes
    classroom_crud.enable_notifications(new_course["id"],
                                        "COURSE_WORK_CHANGES")
    classroom_crud.enable_notifications(new_course["id"],
                                        "COURSE_ROSTER_CHANGES")
    # add instructional designer
    try:
      add_teacher(headers, section,
                  course_template_details.instructional_designer)
    except Exception as error:
      error = traceback.format_exc().replace("\n", " ")
      Logger.error(f"Create teacher failed for \
          for {course_template_details.instructional_designer}")
      Logger.error(error)

    #If topics are present in course create topics returns a dict
    # with keys a current topicID and new topic id as values
    if topics is not None:
      topic_id_map = classroom_crud.create_topics(new_course["id"], topics)
    # Calling function to get edit_url and view url of
    # google form which returns
    # a dictionary of view_links as keys and edit
    #  links/  and file_id as values for all drive files
    url_mapping = classroom_crud.\
            get_edit_url_and_view_url_mapping_of_form()

    # Get coursework of current course and create a new course
    coursework_list = classroom_crud.get_coursework_list(
        course_template_details.classroom_id)

    # final_coursewok=[]
    for coursework in coursework_list:
      coursework_lti_assignment_ids = []
      try:
        #Check if a coursework is linked to a topic if yes then
        # replace the old topic id to new topic id using topic_id_map

        lti_assignment_details = {
            "section_id": section_id,
            "start_date": None,
            "end_date": None,
            "due_date": None
        }

        # Update the due date of the course work if exists
        if coursework.get("dueDate"):
          coursework_due_date = coursework.get("dueDate")

          if coursework.get("dueTime"):
            coursework_due_time = coursework.get("dueTime")
            coursework_due_datetime = datetime.datetime(
                coursework_due_date.get("year"), coursework_due_date.get("month"),
                coursework_due_date.get("day"), coursework_due_time.get("hours", 0),
                coursework_due_time.get("minutes", 0))
          else:
            coursework_due_datetime = datetime.datetime(
                coursework_due_date.get("year"), coursework_due_date.get("month"),
                coursework_due_date.get("day"))

          curr_utc_timestamp = datetime.datetime.utcnow()
          lti_assignment_details["start_date"] = (
              cohort_details.start_date).strftime("%Y-%m-%dT%H:%M:%S%z")

          if coursework_due_datetime < curr_utc_timestamp:
            # Commented for now as the due dates are supposed to be updated by the user before
            # starting the copy course process

            # coursework["dueDate"] = {
            #   "year": cohort_details.end_date.year,
            #   "month": cohort_details.end_date.month,
            #   "day": cohort_details.end_date.day
            # }
            # coursework["dueTime"] = {
            #   "hours": cohort_details.end_date.hour,
            #   "minutes": cohort_details.end_date.minute
            # }

            lti_assignment_details["end_date"] = lti_assignment_details[
                "due_date"] = (
                    cohort_details.end_date).strftime("%Y-%m-%dT%H:%M:%S%z")

          else:
            lti_assignment_details["end_date"] = lti_assignment_details[
                "due_date"] = coursework_due_datetime.strftime(
                    "%Y-%m-%dT%H:%M:%S%z")

        if "topicId" in coursework.keys():
          coursework["topicId"] = topic_id_map[coursework["topicId"]]
        #Check if a material is present in coursework
        if "materials" in coursework.keys():
          coursework_update_output = update_coursework_material(
              materials=coursework["materials"],
              url_mapping=url_mapping,
              target_folder_id=target_folder_id,
              coursework_type="coursework",
              lti_assignment_details=lti_assignment_details)
          coursework["materials"] = coursework_update_output["material"]
          coursework_lti_assignment_ids.extend(
              coursework_update_output["lti_assignment_ids"])
        # final_coursewok.append(coursework)

        coursework_data = classroom_crud.create_coursework(
            new_course["id"], coursework)

        for assignment_id in coursework_lti_assignment_ids:
          coursework_id = coursework_data.get("id")
          input_json = {"course_work_id":coursework_id}
          # update assignment with new coursework id
          lti_assignment_req = requests.patch(
              f"http://classroom-shim/classroom-shim/api/v1/lti-assignment/{assignment_id}",
              headers={
                  "Authorization": f"Bearer {get_backend_robot_id_token()}"
              },
              json=input_json,
              timeout=60)

          if lti_assignment_req.status_code != 200:
            error_flag = True
            Logger.error(
                f"Failed to update assignment {assignment_id} with course work id {coursework_id} due to error - {lti_assignment_req.text} with status code - {lti_assignment_req.status_code}"
            )

          Logger.info(f"Updated the course work id for new LTI assignment - {assignment_id}")

      except Exception as error:
        title = coursework["title"]
        error_flag = True
        Logger.error(f"Get coursework failed for \
              course_id{course_template_details.classroom_id} for {title}")
        error = traceback.format_exc().replace("\n", " ")
        Logger.error(error)
        continue

    # # Create coursework in new course
    # # return final_coursewok
    # if final_coursewok is not None:
    #   classroom_crud.create_coursework(new_course["id"],final_coursewok)
    # Get the list of courseworkMaterial
    final_coursewok_material = []
    coursework_material_list = classroom_crud.get_coursework_material_list(
        course_template_details.classroom_id)
    for coursework_material in coursework_material_list:
      try:
        #Check if a coursework material is linked to a topic if yes then
        # replace the old topic id to new topic id using topic_id_map
        if "topicId" in coursework_material.keys():
          coursework_material["topicId"] = topic_id_map[
              coursework_material["topicId"]]
        #Check if a material is present in coursework
        if "materials" in coursework_material.keys():

          coursework_material_update_output = update_coursework_material(
              materials=coursework_material["materials"],
              url_mapping=url_mapping,
              target_folder_id=target_folder_id)

          coursework_material["materials"] = coursework_material_update_output[
              "material"]
          print("Updated coursework material attached")
        final_coursewok_material.append(coursework_material)
      except Exception as error:
        title = coursework_material["title"]
        error_flag = True
        Logger.error(f"Get coursework material failed for\
        course_id{course_template_details.classroom_id} for {title}")
        error = traceback.format_exc().replace("\n", " ")
        Logger.error(error)
        continue
    # Create coursework in new course
    if final_coursewok_material is not None:
      classroom_crud.create_coursework_material(new_course["id"],
                                                final_coursewok_material)

    # Classroom copy is successful then the section status is changed to active
    if error_flag:
      section.status = "FAILED_TO_PROVISION"
    else:
      section.status = "ACTIVE"
    section.update()

    rows=[{
      "sectionId":section_id,\
      "courseId":new_course["id"],\
      "classroomUrl":new_course["alternateLink"],\
        "name":new_course["section"],\
        "description":new_course["description"],\
          "cohortId":cohort_details.id,\
        "courseTemplateId":course_template_details.id,\
          "status":section.status,\
        "enrollmentStatus": section.enrollment_status,
        "maxStudents": section.max_students,
          "timestamp":datetime.datetime.utcnow()
    }]
    insert_rows_to_bq(rows=rows,
                      dataset=BQ_DATASET,
                      table_name=BQ_TABLE_DICT["BQ_COLL_SECTION_TABLE"])
    Logger.info(message)
    Logger.info(f"Background Task Completed for section Creation for cohort\
                {cohort_details.id}")
    Logger.info(f"Section Details are section id {section_id},\
                classroom id {classroom_id}")
    return True
  except Exception as e:
    error = traceback.format_exc().replace("\n", " ")
    Logger.error(error)
    Logger.error(e)
    raise InternalServerError(str(e)) from e


def update_coursework_material(materials,
                               url_mapping,
                               target_folder_id,
                               coursework_type=None,
                               lti_assignment_details=None):
  """Takes the material attached to any type of cursework and copy it in the
    target folder Id also removes duplicates from material list
  Args:
    materials (list of dictionary): Coursework materials list which is obtained
      from list coursework method
    url_mapping (dict):Dict of view url as key and edit url, fileid as values
    target_folder_id(str):Drive folder Id of section
  Returns:
    updated_material : (list of dict) returns a updated
  """
  drive_ids = []
  youtube_ids = []
  link_urls = []
  updated_material = []
  lti_assignment_ids = []
  # Loop to check the different types of material attached to coursework
  # 1.If a material is driveFile call called copy_material function which
  #  copies is drivefile in target_folder_id and updates the driveFile
  #  dict with new file id for section drive folder
  # 2.If a material is YoutubeVideo or link check for duplicate youtube
  #   video and link
  # 3.If a material is form use url_mapping dictionary to get the file_id
  # of form which is used to copy form in target_folder_id of section and
  # attach form as link in coursework since attaching forms via api is not
  # supported by classroom

  for material in materials:
    if "driveFile" in material.keys():
      if material["driveFile"]["driveFile"]["id"] not in drive_ids:
        classroom_crud.copy_material(material, target_folder_id)
        drive_ids.append(material["driveFile"]["driveFile"]["id"])
        updated_material.append({"driveFile": material["driveFile"]})

    if "youtubeVideo" in material.keys():
      if material["youtubeVideo"]["id"] not in youtube_ids:
        youtube_ids.append(material["youtubeVideo"]["id"])
        updated_material.append({"youtubeVideo": material["youtubeVideo"]})
    if "link" in material.keys():
      if material["link"]["url"] not in link_urls:
        link = material["link"]

        if coursework_type == "coursework":
          # Update lti assignment with the course work details
          if "/classroom-shim/api/v1/launch?lti_assignment_id=" in link["url"]:
            split_url = link["url"].split(
                "/classroom-shim/api/v1/launch?lti_assignment_id=")
            lti_assignment_id = split_url[-1]
            Logger.info(f"LTI Course copy started for assignment - {lti_assignment_id}")
            copy_assignment = requests.post(
                "http://classroom-shim/classroom-shim/api/v1/lti-assignment/copy",
                headers={
                    "Authorization": f"Bearer {get_backend_robot_id_token()}"
                },
                json={
                    "lti_assignment_id": lti_assignment_id,
                    "context_id": lti_assignment_details.get("section_id"),
                    "start_date": lti_assignment_details.get("start_date"),
                    "end_date": lti_assignment_details.get("end_date"),
                    "due_date": lti_assignment_details.get("due_date")
                },
                timeout=60)

            if copy_assignment.status_code == 200:
              new_lti_assignment_id = copy_assignment.json().get("data").get("id")
              updated_material_link_url = link["url"].replace(
                  lti_assignment_id, new_lti_assignment_id)
              lti_assignment_ids.append(new_lti_assignment_id)

              updated_material.append({"link": {"url": updated_material_link_url}})
              Logger.info(f"LTI link updated for new assignment - {new_lti_assignment_id}")
              Logger.info(f"LTI Course copy completed for assignment - {lti_assignment_id}")
            else:
              Logger.error(
                  f"Copying an LTI Assignment failed for {lti_assignment_id}\
                           in the new section {lti_assignment_details.get('section_id')} with status code: \
                           {copy_assignment.status_code} and error msg: {copy_assignment.text}"
              )
          else:
            updated_material.append({"link": material["link"]})

        else:
          if "/classroom-shim/api/v1/launch?lti_assignment_id=" in link["url"]:
            split_url = link["url"].split(
                "/classroom-shim/api/v1/launch?lti_assignment_id=")
            lti_assignment_id = split_url[-1]
            Logger.info(f"LTI link removed in course work material with assignment ID - {lti_assignment_id}")
          else:
            updated_material.append({"link": material["link"]})

        link_urls.append(material["link"]["url"])

    if "form" in material.keys():
      if "title" not in material["form"].keys():
        raise ResourceNotFound("Form to be copied is deleted")
      result1 = classroom_crud.drive_copy(
          url_mapping[material["form"]["formUrl"]]["file_id"],
          target_folder_id, material["form"]["title"])
      material["link"] = {
          "title": material["form"]["title"],
          "url": result1["webViewLink"]
      }
      updated_material.append({"link": material["link"]})
      material.pop("form")

  return {
      "material": updated_material,
      "lti_assignment_ids": lti_assignment_ids
  }


def update_grades(material, section, coursework_id):
  """Takes the forms all responses ,section, and coursework_id aInd
  updates the grades of student who have responsed to form and
  submitted the coursework
  """
  student_grades = {}
  count = 0
  Logger.info(f"Student grade update background tasks started\
              for coursework_id {coursework_id}")
  #Get url mapping of google forms view links and edit ids
  url_mapping = classroom_crud.get_edit_url_and_view_url_mapping_of_form()
  form_details = url_mapping[material["form"]["formUrl"]]

  form_id = form_details["file_id"]
  # Get all responses for the form if no responses of
  # the form then return
  all_responses_of_form = classroom_crud.\
  retrieve_all_form_responses(form_id)
  if all_responses_of_form == {}:
    Logger.error("Responses not available for google form")
  for response in all_responses_of_form["responses"]:
    try:
      if "respondentEmail" not in response.keys():
        raise Exception(f"Respondent Email is not collected in form for\
        coursework {coursework_id} Update form settings to collect Email")
      respondent_email = response["respondentEmail"]
      submissions = classroom_crud.list_coursework_submissions_user(
          section.classroom_id, coursework_id, response["respondentEmail"])
      if submissions:
        if submissions[0]["state"] == "TURNED_IN":
          Logger.info(f"Updating grades for {respondent_email}")
          if "totalScore" not in response.keys():
            response["totalScore"] = 0
          classroom_crud.patch_student_submission(section.classroom_id,
                                                  coursework_id,
                                                  submissions[0]["id"],
                                                  response["totalScore"],
                                                  response["totalScore"])
          count += 1
          student_grades[response["respondentEmail"]] = response["totalScore"]
          Logger.info(f"Updated grades for {respondent_email}")
        else:
          Logger.info(f"Submission state is not turn in {respondent_email}")
    except Exception as e:
      error = traceback.format_exc().replace("\n", " ")
      Logger.error(error)
      Logger.error(e)
      continue
  Logger.info(f"Student grades updated\
                for {count} student_data {student_grades}")
  return count, student_grades


def add_teacher(headers, section, teacher_email):
  """_summary_

  Args:
      headers (_type_): _description_
      course_id (_type_): _description_
      teacher_email (_type_): _description_
  """
  invitation_object = classroom_crud.invite_user(section.classroom_id,
                                                 teacher_email, "TEACHER")
  try:
    classroom_crud.acceept_invite(invitation_object["id"], teacher_email)
    user_profile = classroom_crud.\
        get_user_profile_information(teacher_email)

    data = {
        "first_name": user_profile["name"]["givenName"],
        "last_name": user_profile["name"]["familyName"],
        "email": teacher_email,
        "user_type": "faculty",
        "user_groups": [],
        "status": "active",
        "is_registered": True,
        "failed_login_attempts_count": 0,
        "access_api_docs": False,
        "gaia_id": user_profile["id"],
        "photo_url": user_profile["photoUrl"]
    }
    status = "active"
    invitation_id = ""
  except Exception as hte:
    Logger.info(hte)
    data = {
        "first_name": "first_name",
        "last_name": "last_name",
        "email": teacher_email,
        "user_type": "faculty",
        "user_groups": [],
        "status": "active",
        "is_registered": True,
        "failed_login_attempts_count": 0,
        "access_api_docs": False,
        "gaia_id": "",
        "photo_url": ""
    }
    status = "invited"
    invitation_id = invitation_object["id"]
  user_dict = common_service.create_teacher(headers, data)
  Logger.info(user_dict)
  course_enrollment_mapping = CourseEnrollmentMapping()
  course_enrollment_mapping.section = section
  course_enrollment_mapping.role = "faculty"
  course_enrollment_mapping.user = User.find_by_user_id(user_dict["user_id"])
  course_enrollment_mapping.status = status
  course_enrollment_mapping.invitation_id = invitation_id
  course_enrollment_mapping.save()
  return course_enrollment_mapping

def validate_section(section):
  """
  Validate the section if it is eligile for enrollment
  validate the count of enrolled students ,enrollment status, max_students
  """
  if section.enrolled_students_count >= section.max_students:
    raise ValidationError("Maximum student count reached for section hence student can't be enrolled"
      )
  Logger.info(f"Enrollment status {section.enrolled_students_count} {section.status}")
  if section.enrolled_students_count == "CLOSED" or section.status != "ACTIVE":
    raise ValidationError("Enrollment is not active for this section"
      )
  return True
