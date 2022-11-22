'''Cohort Endpoint'''
import datetime
import json
import logging
from fastapi import APIRouter
from schemas.cohort import CohortListModel,CohortModel,CreateCohortResponseModel,InputCohort,DeleteCohort
from common.models import Cohort,CourseTemplate
from common.utils.logging_handler import Logger
from common.utils.errors import ResourceNotFoundException
from common.utils.http_exceptions import ResourceNotFound, InternalServerError
from schemas.error_schema import (InternalServerErrorResponseModel, NotFoundErrorResponseModel,
                                  ConflictResponseModel, ValidationErrorResponseModel)
from utils.helper import convert_cohort_to_cohort_model

router = APIRouter(prefix="/cohorts", tags=["Cohort"], responses={
    500: {
        "model": InternalServerErrorResponseModel
    },
    404: {
        "model": NotFoundErrorResponseModel
    },
    409: {
        "model": ConflictResponseModel
    },
    422: {
        "model": ValidationErrorResponseModel
    }
})


@router.get("", response_model=CohortListModel)
def get_cohort_list():
    """Get a list of Cohort endpoint
    Raises:
        HTTPException: 500 Internal Server Error if something fails.

    Returns:
        CohortListModel: object which contains list of Cohort object.
        InternalServerErrorResponseModel: if the get cohort list raises an exception.
    """
    try:
        fetched_cohort_list = Cohort.collection.filter(
            "is_deleted", "==", False).fetch()
        if fetched_cohort_list is None:
            return {"message": "Successfully get the cohort list, but the list is empty.", "cohort_list": []}
        cohort_list = [convert_cohort_to_cohort_model(i) for i in fetched_cohort_list]
        return {"cohort_list": cohort_list}
    except ResourceNotFoundException as re:
        raise ResourceNotFound(str(re)) from re
    except Exception as e:
        print(e.message)
        Logger.error(e)
        raise InternalServerError(str(e)) from e


@router.get("/{cohort_id}", response_model=CohortModel)
def get_cohort(cohort_id: str):
    """Get a Cohort endpoint

    Args:
        cohort_id (str): unique id of the cohort

    Raises:
        ResourceNotFoundException: If the Cohort does not exist.
        HTTPException: 500 Internal Server Error if something fails.

    Returns:
        CohortModel: Cohort object for the provided id
        NotFoundErrorResponseModel: if the Cohort not found,
        InternalServerErrorResponseModel: if the get Cohort raises an exception
    """
    try:
        cohort = Cohort.find_by_uuid(cohort_id)
        if cohort is None:
            raise ResourceNotFoundException(
                f'Cohort with uuid {cohort_id} is not found')
        loaded_cohort = convert_cohort_to_cohort_model(cohort)
        return loaded_cohort
    except ResourceNotFoundException as re:
        raise ResourceNotFound(str(re)) from re
    except Exception as e:
        Logger.error(e)
        raise InternalServerError(str(e)) from e


@router.post("", response_model=CreateCohortResponseModel)
def create_cohort(input_cohort: InputCohort):
    """Create a Cohort endpoint

    Args:
        input_cohort (InputCohortModel): input Cohort to be inserted

    Raises:
        ResourceNotFoundException: If the Course Template does not exist.
        Exception: 500 Internal Server Error if something went wrong

    Returns:
        CreateCohortResponseModel: Cohort Object,
        NotFoundErrorResponseModel: if the Course template not found,
        InternalServerErrorResponseModel: if the Cohort creation raises an exception
  """
    try:
        cohort_dict = {**input_cohort.dict()}
        course_template = CourseTemplate.find_by_uuid(
            cohort_dict["course_template_uuid"])
        if course_template is None:
            raise ResourceNotFoundException(
                f'Course Template with uuid {cohort_dict["course_template_uuid"]} is not found')
        cohort_dict.pop("course_template_uuid")
        cohort=Cohort.from_dict(cohort_dict)
        cohort.course_template=course_template
        timestamp=datetime.datetime.utcnow()
        cohort.created_timestamp=timestamp
        cohort.last_updated_timestamp=timestamp
        cohort.save()
        cohort.uuid = cohort.id
        cohort.update()
        return {"cohort": convert_cohort_to_cohort_model(cohort)}
    except ResourceNotFoundException as re:
        raise ResourceNotFound(str(re)) from re
    except Exception as e:
        Logger.error(e)
        raise InternalServerError(str(e)) from e


@router.delete("/{cohort_id}", response_model=DeleteCohort)
def delete_cohort(cohort_id: str):
    """Delete a Cohort endpoint
    Args:
        cohort_id (str): unique id of the Cohort

    Raises:
        ResourceNotFoundException: If the Cohort does not exist
        HTTPException: 500 Internal Server Error if something fails

    Returns:
        DeleteCohortModel: if the Cohort is deleted,
        NotFoundErrorResponseModel: if the Cohort not found,
        InternalServerErrorResponseModel: if the Cohort deletion raises an exception
    """
    try:
        if Cohort.archive_by_uuid(cohort_id):
            return {"message": f"Successfully deleted the Cohort with uuid {cohort_id}"}
        else:
            raise ResourceNotFoundException(
                f'Cohort with uuid {cohort_id} is not found')
    except ResourceNotFoundException as re:
        raise ResourceNotFound(str(re)) from re
    except Exception as e:
        Logger.error(e)
        raise InternalServerError(str(e)) from e

