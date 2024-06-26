""" LTI Token utils """
import re
import json
from datetime import datetime
from jose import jwt, jws
from common.models import Tool, LTIContentItem, LineItem, LTIAssignment
from common.utils.logging_handler import Logger
from services.keys_manager import get_platform_public_keyset
from utils.request_handler import get_method
from config import TOKEN_TTL, LTI_ISSUER_DOMAIN, LTI_PLATFORM_UNIQUE_ID, LTI_PLATFORM_NAME
# pylint: disable=line-too-long, broad-exception-raised


def lti_claim_field(field_type, claim_type, suffix=None):
  """ Add claims field in the token """
  lti_suffix = ("-" + suffix) if suffix else ""
  return f"https://purl.imsglobal.org/spec/lti{lti_suffix}/{field_type}/{claim_type}"


def generate_token_claims(lti_request_type, client_id, login_hint,
                          lti_message_hint, nonce, redirect_uri):
  """ Generate claims for the token """
  tool = Tool.find_by_client_id(client_id)
  tool_info = tool.get_fields(reformat_datetime=True)

  if redirect_uri not in tool_info.get("redirect_uris"):
    raise Exception(f"Unknown redirect_uri {redirect_uri}")

  get_user_url = f"http://user-management/user-management/api/v1/user/{login_hint}"
  user_res = get_method(url=get_user_url, use_bot_account=True)

  if user_res.status_code == 200:
    user = user_res.json().get("data")
  else:
    raise Exception(
        f"Internal error from get user API with status code - {user_res.status_code}"
    )

  token_claims = {
      "iss": LTI_ISSUER_DOMAIN,
      "aud": client_id,
      "nonce": nonce,
      "iat": int(datetime.now().timestamp()),
      "exp": int(datetime.now().timestamp()) + TOKEN_TTL,
      "sub": login_hint,
      "given_name": user.get("first_name"),
      "family_name": user.get("last_name"),
      "name": user.get("first_name") + " " + user.get("last_name"),
      "email": user.get("email"),
      "picture": user.get("photo_url"),
      lti_claim_field("claim", "tool_platform"): {
          "guid": LTI_PLATFORM_UNIQUE_ID,
          "name": LTI_PLATFORM_NAME
      }
  }

  context_id = lti_message_hint.get("context_id")
  context_type = lti_message_hint.get("context_type")

  get_context_url = f"http://classroom-shim/classroom-shim/api/v1/contexts/{context_id}"
  context_res = get_method(url=get_context_url, use_bot_account=True)

  if context_res.status_code == 200:
    context_data = context_res.json().get("data")
  else:
    Logger.error(
        f"Error 1009 response: Status code: {context_res.status_code}; Response: {context_res.text}"
    )
    raise Exception("Request failed with error code 1009")

  if context_type.lower() == "course_template":
    lti_context_type = "http://purl.imsglobal.org/vocab/lis/v2/course#CourseTemplate"
  else:
    lti_context_type = "http://purl.imsglobal.org/vocab/lis/v2/course#CourseSection"

  lti_context_id = context_data.get("id")
  token_claims[lti_claim_field("claim", "context")] = {
      "id": lti_context_id,
      "label": context_data.get("description"),
      "title": context_data.get("name"),
      "type": [lti_context_type]
  }

  if lti_request_type == "deep_link":
    token_claims[lti_claim_field("claim", "deep_linking_settings", "dl")] = {
        "accept_types": ["link", "file", "html", "ltiResourceLink", "image"],
        "accept_presentation_document_targets": ["iframe", "window", "embed"],
        "accept_multiple":
            False,
        "auto_create":
            False,
        "title":
            "",
        "text":
            "",
        "deep_link_return_url":
            f"{LTI_ISSUER_DOMAIN}/lti/api/v1/content-item-return?context_id={lti_context_id}"
    }

    token_claims[lti_claim_field("claim",
                                 "message_type")] = "LtiDeepLinkingRequest"

  if lti_request_type == "resource_link":
    token_claims[lti_claim_field("claim",
                                 "message_type")] = "LtiResourceLinkRequest"

    lti_content_item_id = lti_message_hint.get("lti_content_item_id")
    lti_content_item = LTIContentItem.find_by_id(lti_content_item_id)

    # process content item info claims required for launch
    content_item_info = lti_content_item.content_item_info
    if content_item_info:
      if content_item_info.get("url"):
        token_claims[lti_claim_field(
            "claim", "target_link_uri")] = content_item_info.get("url")
      else:
        token_claims[lti_claim_field("claim",
                                     "target_link_uri")] = tool_info["tool_url"]

    # process custom parameters
    final_custom_claims = {**content_item_info.get("custom", {})}
    custom_params = lti_message_hint.get("custom_params_for_substitution")

    if tool_info.get("custom_params", None) is not None:
      cpm = tool_info.get("custom_params")
      # process custom parameter from tool registration

      # separate params string using ";"
      cpm = re.split(";", cpm)
      final_cpm = {}
      for i in cpm:
        # separate params string using "="
        if i:
          i = i.replace(" ", "")
          single_cpm = re.split("=", i)
          final_cpm[single_cpm[0]] = single_cpm[1]

      for key, value in final_cpm.items():
        if custom_params.get(value) is not None:
          final_custom_claims[key] = custom_params.get(value)

    if "custom" in content_item_info.keys():
      # process custom parameters from content_item
      for key, value in content_item_info.get("custom").items():
        if isinstance(value, str) and value.startswith(
            "$") and custom_params.get(value) is not None:
          final_custom_claims[key] = custom_params.get(value)

      token_claims[lti_claim_field("claim", "custom")] = final_custom_claims

    # process grade sync functionality
    if tool_info.get("enable_grade_sync"):
      token_claims[lti_claim_field("claim", "endpoint", "ags")] = {
          "scope": [
              "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
              "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
              "https://purl.imsglobal.org/spec/lti-ags/scope/score"
          ],
          "lineitems":
              f"{LTI_ISSUER_DOMAIN}/lti/api/v1/{lti_context_id}/line_items",
      }

    # process line_item claims
    if "lineItem" in content_item_info.keys():
      line_item = LineItem.find_by_resource_link_id(lti_content_item.id)

      token_claims[lti_claim_field("claim", "endpoint", "ags")] = {
          "scope": [
              lti_claim_field("scope", "lineitem", "ags"),
              lti_claim_field("scope", "result.readonly", "ags"),
              lti_claim_field("scope", "score", "ags")
          ],
          "lineitems":
              f"{LTI_ISSUER_DOMAIN}/lti/api/v1/{lti_context_id}/line_items",
          "lineitem":
              f"{LTI_ISSUER_DOMAIN}/lti/api/v1/{lti_context_id}/line_items/{line_item.id}"
      }

    if tool_info.get("enable_nrps"):
      token_claims[lti_claim_field("claim", "namesroleservice", "nrps")] = {
          "context_memberships_url":
              f"{LTI_ISSUER_DOMAIN}/lti/api/v1/{lti_context_id}/memberships",
          "service_versions": ["2.0"]
      }
    if not content_item_info.get("title") or content_item_info.get(
        "title") == tool_info.get("name"):
      assignment = LTIAssignment.collection.filter("lti_content_item_id", "==",
                                                   lti_content_item_id).get()
      if assignment:
        resource_link_title = assignment.lti_assignment_title
        resource_link_description = ""
      else:
        resource_link_title = content_item_info.get("title")
        resource_link_description = content_item_info.get("text")
    else:
      resource_link_title = content_item_info.get("title")
      resource_link_description = content_item_info.get("text")

    resource_link_claim_info = {
        "id": lti_content_item.id,
        "title": resource_link_title,
        "description": resource_link_description
    }

    token_claims[lti_claim_field("claim",
                                 "resource_link")] = resource_link_claim_info

  token_claims[lti_claim_field("claim", "version")] = "1.3.0"
  token_claims[lti_claim_field("claim",
                               "deployment_id")] = tool_info["deployment_id"]

  if user.get("user_type") == "learner":
    token_claims[lti_claim_field("claim", "roles")] = [
        "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner",
        "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Learner",
        "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Student"
    ]

  elif user.get("user_type") == "faculty":
    token_claims[lti_claim_field("claim", "roles")] = [
        "http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor",
        "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Faculty",
        "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Instructor"
    ]
  # Role claims for Admin -
  elif user.get("user_type") == "admin":
    token_claims[lti_claim_field("claim", "roles")] = [
        "http://purl.imsglobal.org/vocab/lis/v2/membership#Administrator",
        "http://purl.imsglobal.org/vocab/lis/v2/system/person#Administrator",
        "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Administrator"
    ]

  return token_claims


def encode_token(claims):
  """Generates a token by encoding the given claims using the private key"""
  key_set = get_platform_public_keyset()
  token = jwt.encode(
      claims,
      key_set.get("web_key"),
      algorithm="RS256",
      headers={"kid": key_set.get("web_key").get("kid")})
  return token


def decode_token(token, key, audience):
  """Decodes a given token and verifies it using the provided public key"""
  decoded_token = jwt.decode(
      token=token, algorithms="RS256", key=key, audience=audience)
  return decoded_token


def get_unverified_token_claims(token):
  """Decodes a given token using the provided public key"""
  unverified_claims = jws.get_unverified_claims(token=token).decode("UTF-8")
  return json.loads(unverified_claims)
