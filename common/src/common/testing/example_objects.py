"""Example Data for testing"""
import datetime
from common.models.cohort import Cohort
from common.models.section import Section
from common.models.course_template import CourseTemplate

TEST_USER= {
        "uuid":"fake-user-id",
        "auth_id" : "fake-user-auth-id",
        "email" : "user@gmail.com",
        "role" : "Admin"
      }

TEST_COURSE_TEMPLATE={
            "uuid":"fake-course-id",
            "name" : "name",
            "description" : "description",
            "admin" : "admin",
            "instructional_designer": "IDesiner",
            "classroom_id":"clID",
            "classroom_code":"clcode"
        }

TEST_COHORT={
            "uuid":"fake-cohort-id",
            "name": "name",
            "description": "description",
            "start_date": datetime.datetime(year=2022,
                                            month=10, day=14),
            "end_date": datetime.datetime(year=2022,
                                          month=12, day=25),
            "registration_start_date": datetime.datetime(year=2022,
                                                         month=10, day=20),
            "registration_end_date": datetime.datetime(year=2022,
                                                       month=11, day=14),
            "max_student": 0,
            "enrolled_student_count":0
        }

TEST_SECTION={
            "uuid":"fake-section-id",
            "name" : "section_name",
            "section" : "section c",
            "description": "description",
            "classroom_id" :"cl_id",
            "classroom_code" :"cl_code",
            "teachers_list":["teachera@gmail.com","teacherb@gmail.com"]
        }

TEST_COURSE_TEMPLATE2 = {
      "name": "test-name",
      "uuid":"fake_template_id",
      "description": "test-description",
      "admin": "test-admin@gmail.com",
      "instructional_designer": "IDesiner@gmail.com",
      "classroom_id": "fake_classroom_id",
      "classroom_code": "fake-classroom_code"
    }

TEST_COHORT2 = {
    "uuid":"fake_cohort_id",
    "name": "name",
    "description": "description",
    "course_template":"fake_template_id",
    "start_date": datetime.datetime(year=2022,month=10, day=14),
    "end_date": datetime.datetime(year=2022,month=12, day=25),
    "registration_start_date": datetime.datetime(year=2022,month=10, day=20),
    "registration_end_date": datetime.datetime(year=2022,month=11, day=14),
    "max_student": 0,
    "enrolled_student_count":0
  }

TEST_SECTION2 = {
    "uuid":"fake_section_id",
    "name" : "section_name",
    "section" : "section c",
    "description": "description",
    "classroom_id" :"cl_id",
    "classroom_code" :"cl_code",
    "course_template":"fake_template_id",
    "cohort":"fake_cohort_id",
    "teachers_list":["fake_email_id@gmail.com"]
  }

def create_fake_data(TEST_COURSE_TEMPLATE,TEST_COHORT,TEST_SECTION,classroom_id):
  """Function to create temprory data"""

  TEST_COURSE_TEMPLATE["classroom_id"]=classroom_id
  course_template = CourseTemplate.from_dict(TEST_COURSE_TEMPLATE)
  course_template.save()

  TEST_COHORT["course_template"]=course_template
  
  cohort = Cohort.from_dict(TEST_COHORT)
  cohort.save()
  TEST_SECTION["cohort"]=cohort
  TEST_SECTION["course_template"] = course_template
  section = Section.from_dict(TEST_SECTION2)
  section.save()
  return course_template , cohort,section