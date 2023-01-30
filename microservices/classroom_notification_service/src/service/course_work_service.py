# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Save User Data to BQ Service
"""
import datetime
import json
import uuid
from common.utils.logging_handler import Logger
from googleapiclient.errors import HttpError
from helper.bq_helper import insert_rows_to_bq
from helper.classroom_helper import get_course_work,get_student_submissions
from config import BQ_LOG_CW_TABLE,BQ_COLL_CW_TABLE,BQ_COLL_SCW_TABLE
# disabling for linting to pass
# pylint: disable = broad-except

def save_course_work(data):
  """_summary_

  Args:
    data (_type_): _description_

  Returns:
    _type_: _description_
  """
  try:
    rows = [{
    "message_id": data["message_id"], "collection": data["collection"],
    "event_type":data["eventType"], "resource":json.dumps(data["resourceId"]),
    "publish_time":data["publish_time"],"timestamp":datetime.datetime.utcnow()
        }]
    if len(data["collection"].split(".")) == 3:
      if data["collection"].split(".")[2] == "studentSubmissions":
        return insert_rows_to_bq(
            rows=rows, table_name=BQ_LOG_CW_TABLE) & save_student_submission(
                course_id=data["resourceId"]["courseId"],
                message_id=data["message_id"],
                course_work_id=data["resourceId"]["courseWorkId"],
                submissions_id=data["resourceId"]["id"])
    else:
      return insert_rows_to_bq(rows=rows,
        table_name=BQ_LOG_CW_TABLE) & save_course_work_collection(
            course_id=data["resourceId"]["courseId"],
            message_id=data["message_id"],
            course_work_id=data["resourceId"]["id"])
  except HttpError as ae:
    Logger.error(ae)
    return False
  except Exception as e:
    Logger.error(e)
    return False



def save_course_work_collection(course_id,course_work_id,message_id):
  """_summary_

  Args:
    course_id (_type_): _description_
    course_work_id (_type_): _description_
    message_id (_type_): _description_

  Returns:
    _type_: _description_
  """
  course_work=get_course_work(course_id=course_id,course_work_id=course_work_id)
  course_work["uuid"] = str(uuid.uuid4())
  course_work["message_id"] = message_id
  course_work["assignment"] =convert_to_json(course_work,"assignment")
  course_work["multipleChoiceQuestion"] = convert_to_json(
      course_work, "multipleChoiceQuestion")
  course_work["individualStudentsOptions"] = convert_to_json(
      course_work, "individualStudentsOptions")
  course_work["gradeCategory"] = convert_to_json(course_work, "gradeCategory")
  course_work["materials"] = convert_dict_array_to_json(course_work,"materials")
  course_work["timestamp"] = datetime.datetime.utcnow()
  return insert_rows_to_bq(rows=[course_work], table_name=BQ_COLL_CW_TABLE)


def save_student_submission(course_id, course_work_id,
                            submissions_id, message_id):
  """_summary_

  Args:
    course_id (string): unique classroom id
    course_work_id (string): unique course work id
    submissions_id (string): _description_
    message_id (string): _description_

  Returns:
    bool: _description_
  """
  submission = get_student_submissions(
      course_id, course_work_id, submissions_id)
  submission["uuid"] = str(uuid.uuid4())
  submission["message_id"]=message_id
  submission["assignmentSubmission"] = convert_to_json(
      submission, "assignmentSubmission")
  submission["submissionHistory"] =convert_dict_array_to_json( submission,
                    "submissionHistory")
  submission["shortAnswerSubmission"] = convert_to_json(
      submission, "shortAnswerSubmission")
  submission["multipleChoiceSubmission"] = convert_to_json(
      submission, "multipleChoiceSubmission")
  submission["timestamp"] = datetime.datetime.utcnow()
  return insert_rows_to_bq([submission],BQ_COLL_SCW_TABLE)


def convert_to_json(dict_object,key):
  """_summary_

  Args:
    dict_object (_type_): _description_
    key (_type_): _description_

  Returns:
    _type_: _description_
  """
  if key in dict_object.keys():
    return json.dumps(dict_object[key])
  return None


def convert_dict_array_to_json(dict_object, key):
  """_summary_

  Args:
    dict_object (_type_): _description_
    key (_type_): _description_

  Returns:
    _type_: _description_
  """
  if key in dict_object.keys():
    return [json.dumps(i) for i in dict_object[key]]
  else:
    return None