"""
  LTI Microservice
"""

# pylint: disable=pointless-string-statement
# pylint: disable=wrong-import-position
# """ For Local Development
""" For Local Development
"""
import sys
import os

sys.path.append("../../../common/src")
os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
os.environ["GOOGLE_CLOUD_PROJECT"] = "fake-project"

os.environ["DATABASE_PREFIX"] = "ram_"
import config
import uvicorn
from fastapi import FastAPI, Depends
from routes import (tool_registration, content_item, content_item_return,
                    platform_registration, platform_auth, platform_launch,
                    tool_auth, tool_launch, line_item)
from common.utils.http_exceptions import add_exception_handlers
from common.utils.auth_service import validate_token

app = FastAPI()


@app.get("/ping")
def health_check():
  return {
      "success": True,
      "message": "Successfully reached LTI microservice",
      "data": {}
  }


api = FastAPI(title="LTI Service APIs", version="latest")

# LTI as a platform routes
api.include_router(tool_registration.router)
api.include_router(platform_launch.router)
api.include_router(platform_auth.router)
api.include_router(content_item_return.router)
api.include_router(content_item.router)
api.include_router(line_item.router)

# LTI as a tool routes
# api.include_router(platform_registration.router)
# api.include_router(tool_auth.router)
# api.include_router(tool_launch.router)

add_exception_handlers(app)
add_exception_handlers(api)
app.mount("/lti/api/v1", api)

if __name__ == "__main__":
  uvicorn.run(
      "main:app", host="0.0.0.0", port=9030, log_level="debug", reload=True)
