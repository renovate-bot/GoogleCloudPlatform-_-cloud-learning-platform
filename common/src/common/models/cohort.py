"""
Module to add cohort in Fireo
"""
import os


from common.models import BaseModel,CourseTemplate
from fireo.fields import TextField,DateTime,NumberField,ReferenceField,BooleanField

DATABASE_PREFIX = os.getenv("DATABASE_PREFIX", "")
PROJECT_ID = os.environ.get("PROJECT_ID", "")


class Cohort(BaseModel):
  """Cohort ORM class
  """
  uuid=TextField()
  name = TextField(required=True)
  description = TextField(required=True)
  start_date = DateTime(required=True)
  end_date = DateTime(required=True)
  registration_start_date = DateTime(required=True)
  registration_end_date = DateTime(required=True)
  max_student = NumberField()
  enrolled_student_count=NumberField()
  course_template=ReferenceField(CourseTemplate,required=True)
  is_deleted = BooleanField(default=False)
  created_timestamp = DateTime()
  last_updated_timestamp = DateTime()
  deleted_at_timestamp = DateTime()

  class Meta:
    ignore_none_field = False
    collection_name = DATABASE_PREFIX + "cohorts"

  @classmethod
  def find_by_uuid(cls, uuid):
    """Find a Cohort using uuid (UUID)
    Args:
        uuid (string): Cohort ID
    Returns:
        Cohort: Cohort Object
    """
    cohort = Cohort.collection.filter(
        "uuid", "==", uuid).filter("is_deleted", "==", False).get()
    return cohort

  @classmethod
  def archive_by_uuid(cls, uuid):
    '''Soft Delete a Cohort by using uuid
    Args:
        uuid (String): Cohort ID
    '''
    cohort = Cohort.collection.filter("uuid", "==", uuid).filter(
        "is_deleted", "==", False).get()
    if cohort is None:
      return False
    else:
      cohort.is_deleted = True
      cohort.update()
      return True
