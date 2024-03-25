""" Route module for parsing skills from assessment """

import traceback
from fastapi import APIRouter
from services.skill_parsing.skill_parsing import SkillParser
from common.utils.logging_handler import Logger
from common.utils.errors import ResourceNotFoundException, ValidationError
from common.utils.http_exceptions import (InternalServerError, BadRequest,
                                          ResourceNotFound)
from schemas.skill_parsing_schema import (SkillParsingByQueryRequestModel,
                                          SkillParsingByQueryResponseModel)
from schemas.error_schema import NotFoundErrorResponseModel
from config import ERROR_RESPONSES

router = APIRouter(
    prefix="/assessment/skill-alignment/query",
    tags=["Parse Skills from assessment"],
    responses=ERROR_RESPONSES)


@router.post(
    "",
    response_model=SkillParsingByQueryResponseModel,
    responses={404: {
        "model": NotFoundErrorResponseModel
    }})
def search_by_query(req_body: SkillParsingByQueryRequestModel):
  """Given a query this function return skills that are most relevant to
    the given assessment

  Args:
    req_body (SkillParsingByQueryRequestModel): Required body for skill parsing

  Raises:
    HTTPException: 500 Internal Server Error if something fails

  Returns:
    [JSON] (SkillParsingByQueryRequestModel): list of dicts containing
    skills with their name, description and score
  """
  try:
    request_body = req_body.__dict__
    alignment_sources = request_body.get("skill_alignment_sources", ["snhu"])
    skill_dict = {}
    for alignment_source in alignment_sources:
      db_index = "skill" + "_" + alignment_source
      skill_parse_obj = SkillParser(source=alignment_source, db_index=db_index)
      skill_list = skill_parse_obj.get_relevant_skills(request_body)
      skill_dict[alignment_source] = skill_list
      response = {
          "name": request_body["name"],
          "description": request_body["description"],
          "aligned_skills": skill_dict
      }
  except ValidationError as e:
    Logger.error(e)
    Logger.error(traceback.print_exc())
    raise BadRequest(str(e)) from e
  except ResourceNotFoundException as e:
    Logger.error(e)
    Logger.error(traceback.print_exc())
    raise ResourceNotFound(str(e)) from e
  except Exception as e:
    Logger.error(e)
    Logger.error(traceback.print_exc())
    raise InternalServerError(str(e)) from e
  return {"data": response}
