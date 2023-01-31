""" Helper Functions"""
import json
from google.cloud import secretmanager
import google_crc32c
import ttl_cache
from config import PROJECT_ID


@ttl_cache(3600)
def get_gke_pd_sa_key_from_secret_manager():
  """Copy course  API

  Args:
  Returns:
  return the POD service account keys in JSON format
  """ ""

  client = secretmanager.SecretManagerServiceClient()
  secret_id = "gke-pod-sa-key"
  secret_name = (f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest")

  response = client.access_secret_version(request={"name": secret_name})
  crc32c = google_crc32c.Checksum()
  crc32c.update(response.payload.data)
  if response.payload.data_crc32c != int(crc32c.hexdigest(), 16):
    print("Data corruption detected.")
    return response
  payload = response.payload.data.decode("UTF-8")
  response = json.loads(payload)
  return response


@ttl_cache(3600)
def get_offline_access_token_from_secret_manager():
  """_summary_

  Returns:
      dict: offline access token
  """
  client = secretmanager.SecretManagerServiceClient()
  secret_id = "registration_access_token"
  secret_name = (f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest")

  response = client.access_secret_version(request={"name": secret_name})
  crc32c = google_crc32c.Checksum()
  crc32c.update(response.payload.data)
  if response.payload.data_crc32c != int(crc32c.hexdigest(), 16):
    print("Data corruption detected.")
    return response
  payload = response.payload.data.decode("UTF-8")
  response = json.loads(payload)
  return response


def convert_cohort_to_cohort_model(cohort):
  """Convert Cohort Object to Cohort Model Object

  Args:
    cohort (Cohort): Cohort Object.
  Returns:
    return a dict in the cohort model format.
  """ ""
  loaded_cohort = cohort.to_dict()
  course_template = loaded_cohort.pop("course_template").to_dict()
  loaded_cohort["course_template"] = course_template["key"]
  loaded_cohort["course_template_name"] = course_template["name"]
  return loaded_cohort


def convert_section_to_section_model(section):
  """Convert Section Object to Section Model Object

  Args:
    section (Section): Section Object.
  Returns:
    return a dict in the section model format.
  """ ""
  loaded_section = section.to_dict()
  course_template = loaded_section.pop("course_template").to_dict()
  loaded_section["course_template"] = course_template["key"]
  cohort = loaded_section.pop("cohort").to_dict()
  loaded_section["cohort"] = cohort["key"]
  return loaded_section

