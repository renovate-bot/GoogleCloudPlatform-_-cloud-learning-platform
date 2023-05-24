'''LTI Assignment Endpoints'''
import traceback
import datetime
from fastapi import APIRouter
from common.models import LTIAssignment
from common.utils import classroom_crud
from common.utils.logging_handler import Logger
from common.utils.errors import ResourceNotFoundException, ValidationError
from common.utils.http_exceptions import (ResourceNotFound, InternalServerError,
                                          BadRequest)
from config import API_DOMAIN
from routes.context import get_context_details
from schemas.lti_assignment_schema import (
    LTIAssignmentListResponseModel, GetLTIAssignmentResponseModel,
    CreateLTIAssignmentResponseModel, InputLTIAssignmentModel,
    DeleteLTIAssignmentResponseModel, UpdateLTIAssignmentResponseModel,
    UpdateLTIAssignmentModel)
from schemas.error_schema import (InternalServerErrorResponseModel,
                                  NotFoundErrorResponseModel,
                                  ValidationErrorResponseModel)
# pylint: disable=line-too-long

router = APIRouter(
    tags=["LTI Assignments"],
    responses={
        500: {
            "model": InternalServerErrorResponseModel
        },
        404: {
            "model": NotFoundErrorResponseModel
        },
        422: {
            "model": ValidationErrorResponseModel
        }
    })


@router.get("/lti-assignments", response_model=LTIAssignmentListResponseModel)
def get_lti_assignments_list(context_id: str = None,
                             skip: int = 0,
                             limit: int = 10):
  """Get a list of LTI Assignments endpoint
    Raises:
        HTTPException: 500 Internal Server Error if something fails.

    Returns:
        LTIAssignmentListModel: object which contains list of LTI Assignment object.
        InternalServerErrorResponseModel:
            if the get LTI Assignment list raises an exception.
    """
  try:
    if skip < 0:
      raise ValidationError("Invalid value passed to \"skip\" query parameter")
    if limit < 1:
      raise ValidationError\
        ("Invalid value passed to \"limit\" query parameter")

    collection_manager = LTIAssignment.collection.filter(
        "deleted_at_timestamp", "==", None)

    if context_id:
      collection_manager = collection_manager.filter("context_id", "==",
                                                     context_id)

    lti_assignment_list = list(
        collection_manager.order("-created_time").offset(skip).fetch(limit))

    return {
        "success": True,
        "message": "Data fetched successfully",
        "data": lti_assignment_list
    }
  except ValidationError as e:
    Logger.error(e)
    raise BadRequest(str(e)) from e
  except ResourceNotFoundException as e:
    Logger.error(e)
    raise ResourceNotFound(str(e)) from e
  except Exception as e:
    Logger.error(e)
    Logger.error(traceback.print_exc())
    raise InternalServerError(str(e)) from e


@router.get(
    "/lti-assignment/{lti_assignment_id}",
    response_model=GetLTIAssignmentResponseModel)
def get_lti_assignment(lti_assignment_id: str):
  """Get a LTI Assignment endpoint

    Args:
        lti_assignment_id (str): unique id of the LTI Assignment

    Raises:
        ResourceNotFoundException: If the LTI Assignment does not exist.
        HTTPException: 500 Internal Server Error if something fails.

    Returns:
        LTIAssignmentModel: LTI Assignment object for the provided id
        NotFoundErrorResponseModel: if the LTI Assignment not found,
        InternalServerErrorResponseModel: if the get LTI Assignment raises an exception
    """
  try:

    lti_assignment = LTIAssignment.find_by_id(lti_assignment_id)
    lti_assignment_data = lti_assignment.to_dict()

    return {
        "success": True,
        "message": "Successfully fetched assignment",
        "data": lti_assignment_data
    }

  except ResourceNotFoundException as e:
    Logger.error(e)
    raise ResourceNotFound(str(e)) from e
  except Exception as e:
    Logger.error(e)
    Logger.error(traceback.print_exc())
    raise InternalServerError(str(e)) from e


@router.post("/lti-assignment", response_model=CreateLTIAssignmentResponseModel)
def create_lti_assignment(input_lti_assignment: InputLTIAssignmentModel):
  """Create a LTI Assignment endpoint

    Args:
        input_lti_assignment (InputLTIAssignmentModel): input LTI Assignment to be inserted

    Raises:
        ResourceNotFoundException: If the Course Template does not exist.
        Exception: 500 Internal Server Error if something went wrong

    Returns:
        CreateLTIAssignmentResponseModel: LTI Assignment Object,
        NotFoundErrorResponseModel: if the Course template not found,
        InternalServerErrorResponseModel:
            if the LTI Assignment creation raises an exception
  """
  try:

    lti_assignment_dict = {**input_lti_assignment.dict()}
    lti_assignment = LTIAssignment.from_dict(lti_assignment_dict)
    lti_assignment.save()
    lti_assignment_id = lti_assignment.id

    coursework = {
        "title": lti_assignment.lti_assignment_title,
        "materials": [{
            "link": {
                "url":
                    f"{API_DOMAIN}/classroom-shim/api/v1/launch?lti_assignment_id={lti_assignment_id}"
            }
        },],
        "workType": "ASSIGNMENT",
        "state": "PUBLISHED",
    }

    lti_assignment_due_date = lti_assignment_dict.get("due_date")
    if lti_assignment_due_date:
      curr_utc_timestamp = datetime.datetime.utcnow()
      lti_assignment_datetime = datetime.datetime.fromtimestamp(lti_assignment_due_date.timestamp())

      if lti_assignment_datetime < curr_utc_timestamp:
        raise ValidationError(
            f"Given due date - {lti_assignment_due_date} is in the past")

      coursework["dueDate"] = {
          "year": lti_assignment.due_date.year,
          "month": lti_assignment.due_date.month,
          "day": lti_assignment.due_date.day
      }
      coursework["dueTime"] = {
          "hours": lti_assignment.due_date.hour,
          "minutes": lti_assignment.due_date.minute
      }

    lti_assignment_max_points = lti_assignment_dict.get("max_points")
    if lti_assignment_max_points:
      if lti_assignment_max_points <= 0:
        raise ValidationError(
            f"Given max points - {lti_assignment_due_date} should be greater than zero"
        )
      coursework["maxPoints"] = lti_assignment_dict.get("max_points")

    context_resp = get_context_details(lti_assignment.context_id,
                                       lti_assignment.context_type)
    course_id = context_resp["data"]["classroom_id"]

    try:
      classroom_resp = classroom_crud.create_coursework(course_id, coursework)
    except Exception as e:
      LTIAssignment.delete_by_id(lti_assignment_id)
      Logger.error(
          f"Failed to create assignment (deleted assignment id - {lti_assignment_id}) due to error from classroom API with error - {e}"
      )
      raise Exception(
          f"Internal error from classroom - {e} for assigment - {lti_assignment_id}"
      ) from e

    lti_assignment.course_work_id = classroom_resp["id"]
    lti_assignment.update()
    lti_assignment_data = lti_assignment.to_dict()

    return {"data": lti_assignment_data}

  except ValidationError as e:
    raise BadRequest(str(e)) from e
  except ResourceNotFoundException as e:
    Logger.error(e)
    raise ResourceNotFound(str(e)) from e
  except Exception as e:
    Logger.error(e)
    Logger.error(traceback.print_exc())
    raise InternalServerError(str(e)) from e


@router.patch(
    "/lti-assignment/{lti_assignment_id}",
    response_model=UpdateLTIAssignmentResponseModel)
def update_lti_assignment(
    lti_assignment_id: str,
    update_lti_assignment_model: UpdateLTIAssignmentModel):
  """Update LTI Assignment API

    Args:
        update_lti_assignment_model (UpdateLTIAssignmentModel):
            Pydantic model object which contains update details
    Raises:
        InternalServerError: 500 Internal Server Error if something fails
        ResourceNotFoundException :
          404 if LTI Assignment not found
    Returns:
        UpdateLTIAssignment: Returns Updated LTI Assignment object
        InternalServerErrorResponseModel:
            If the LTI Assignment update raises an exception
    """
  try:
    lti_assignment_details = LTIAssignment.find_by_id(lti_assignment_id)
    update_lti_assignment_dict = {**update_lti_assignment_model.dict()}

    if not any(update_lti_assignment_dict.values()):
      raise ValidationError(
          "Invalid request please provide some data " +
          f"to update the LTI Assignment with id {lti_assignment_id}")

    context_resp = get_context_details(lti_assignment_details.context_id,
                                       lti_assignment_details.context_type)
    course_id = context_resp["data"]["classroom_id"]

    coursework_body = {}
    update_mask_list = []

    if update_lti_assignment_dict.get("lti_assignment_title"):
      update_mask_list.append("title")
      coursework_body["title"] = update_lti_assignment_dict[
          "lti_assignment_title"]

    if update_lti_assignment_dict.get("max_points"):
      update_mask_list.append("maxPoints")
      coursework_body["maxPoints"] = update_lti_assignment_dict["max_points"]

    if update_lti_assignment_dict.get("due_date"):
      update_mask_list.append("dueDate")
      update_mask_list.append("dueTime")
      coursework_body["dueDate"] = {
          "year": update_lti_assignment_dict["due_date"].year,
          "month": update_lti_assignment_dict["due_date"].month,
          "day": update_lti_assignment_dict["due_date"].day
      }
      coursework_body["dueTime"] = {
          "hours": update_lti_assignment_dict["due_date"].hour,
          "minutes": update_lti_assignment_dict["due_date"].minute
      }

    update_mask = ",".join(update_mask_list)

    if update_mask:
      try:
        classroom_crud.update_course_work(course_id,
                                          lti_assignment_details.course_work_id,
                                          update_mask, coursework_body)
      except Exception as e:
        Logger.error(
            f"Update coursework failed for assignment with id - {lti_assignment_id} due to error from classroom API with error - {e}"
        )
        raise Exception(
            f"Internal error from classroom - {e} for assignment - {lti_assignment_id}"
        ) from e

    for key in update_lti_assignment_dict:
      if update_lti_assignment_dict[key] is not None:
        setattr(lti_assignment_details, key, update_lti_assignment_dict[key])
    lti_assignment_details.update()
    lti_assignment_data = lti_assignment_details.to_dict()

    return {
        "message":
            f"Successfully updated the LTI Assignment with id {lti_assignment_id}",
        "data":
            lti_assignment_data
    }
  except ValidationError as e:
    Logger.error(e)
    raise BadRequest(str(e)) from e
  except ResourceNotFoundException as e:
    Logger.error(e)
    raise ResourceNotFound(str(e)) from e
  except Exception as e:
    Logger.error(e)
    Logger.error(traceback.print_exc())
    raise InternalServerError(str(e)) from e


@router.delete(
    "/lti-assignment/{lti_assignment_id}",
    response_model=DeleteLTIAssignmentResponseModel)
def delete_lti_assignment(lti_assignment_id: str):
  """Delete a LTI Assignment endpoint
    Args:
        lti_assignment_id (str): unique id of the LTI Assignment

    Raises:
        ResourceNotFoundException: If the LTI Assignment does not exist
        HTTPException: 500 Internal Server Error if something fails

    Returns:
        DeleteLTIAssignmentResponseModel: if the LTI Assignment is deleted
        NotFoundErrorResponseModel: if the LTI Assignment not found
        InternalServerErrorResponseModel:
            if the LTI Assignment deletion raises an exception
    """
  try:
    lti_assignment = LTIAssignment.find_by_id(lti_assignment_id)
    context_resp = get_context_details(lti_assignment.context_id,
                                       lti_assignment.context_type)
    course_id = context_resp["data"]["classroom_id"]

    try:
      classroom_crud.delete_course_work(course_id,
                                        lti_assignment.course_work_id)
    except Exception as e:
      Logger.error(
          f"Error deleting assignment with id - {lti_assignment_id} due to error from classroom API with error - {e}"
      )
      raise Exception(
          f"Internal error from classroom - {e} for assignment - {lti_assignment_id}"
      ) from e

    LTIAssignment.soft_delete_by_id(lti_assignment_id)
    return {
        "message":
            f"Successfully deleted the LTI Assignment with id {lti_assignment_id}"
    }
  except ResourceNotFoundException as e:
    Logger.error(e)
    raise ResourceNotFound(str(e)) from e
  except Exception as e:
    Logger.error(e)
    Logger.error(traceback.print_exc())
    raise InternalServerError(str(e)) from e
