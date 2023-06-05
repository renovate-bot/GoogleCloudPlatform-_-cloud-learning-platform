"""Example Data for testing"""
import datetime
from common.models.cohort import Cohort
from common.models.section import Section
from common.models.course_template import CourseTemplate

TEST_USER = {
    "user_id": "kh5FoIBOx5qDsfh4ZRuv",
    "first_name": "first",
    "last_name": "last",
    "email": "xyz@gmail.com",
    "user_type": "learner",
    "status": "active",
    "gaia_id": "1234577657333",
    "photo_url": "https://lh3.googleusercontent.com/a/AEd"
}

TEST_COURSE_TEMPLATE = {
    "name": "name",
    "description": "description",
    "admin": "admin@gmail.com",
    "instructional_designer": "idesiner@gmail.com",
    "classroom_id": "clID",
    "classroom_code": "clcode",
    "classroom_url": "https://classroom.google.com"
}

TEST_COHORT = {
    "name": "name",
    "description": "description",
    "start_date": datetime.datetime(year=2022, month=10, day=14),
    "end_date": datetime.datetime(year=2022, month=12, day=25),
    "registration_start_date": datetime.datetime(year=2022, month=10, day=20),
    "registration_end_date": datetime.datetime(year=2022, month=11, day=14),
    "max_students": 100,
    "enrolled_students_count": 0
}

TEST_SECTION = {
    "name": "section_name",
    "section": "section c",
    "description": "description",
    "classroom_id": "cl_id",
    "classroom_code": "cl_code",
    "classroom_url": "https://classroom.google.com",
    "enrolled_students_count": 0,
    "max_students":25
}

TEST_COURSE_TEMPLATE2 = {
    "name": "test-name",
    "description": "test-description",
    "admin": "test-admin@gmail.com",
    "instructional_designer": "IDesiner@gmail.com",
    "classroom_id": "fake_classroom_id",
    "classroom_code": "fake-classroom_code",
    "classroom_url": "https://classroom.google.com"
}

TEST_COHORT2 = {
    "name": "name",
    "description": "description",
    "course_template": "fake_template_id",
    "start_date": datetime.datetime(year=2022, month=10, day=14),
    "end_date": datetime.datetime(year=2022, month=12, day=25),
    "registration_start_date": datetime.datetime(year=2022, month=10, day=20),
    "registration_end_date": datetime.datetime(year=2022, month=11, day=14),
    "max_students": 100,
    "enrolled_students_count": 0
}

TEST_SECTION2 = {
    "name": "section_name",
    "section": "section c",
    "description": "description",
    "classroom_id": "cl_id",
    "classroom_code": "cl_code",
    "classroom_url": "https://classroom.google.com",
    "course_template": "fake_template_id",
    "cohort": "fake_cohort_id",
    "enrolled_students_count": 0,
    "max_students":25

}


def create_fake_data(test_course_template, test_cohort, test_section,
                     classroom_id):
  """Function to create temprory data"""

  test_course_template["classroom_id"] = classroom_id
  course_template = CourseTemplate.from_dict(test_course_template)
  course_template.save()
  test_cohort["course_template"] = course_template
  cohort = Cohort.from_dict(test_cohort)
  cohort.save()
  test_section["cohort"] = cohort
  test_section["course_template"] = course_template
  section = Section.from_dict(test_section)
  section.save()
  return course_template, cohort, section
