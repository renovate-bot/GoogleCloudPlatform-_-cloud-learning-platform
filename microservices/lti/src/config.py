"""
  LTI Service config file
"""
# pylint: disable=line-too-long
import os
from schemas.error_schema import (UnauthorizedResponseModel,
                                  InternalServerErrorResponseModel,
                                  ValidationErrorResponseModel)
from google.cloud import secretmanager

secrets = secretmanager.SecretManagerServiceClient()

PORT = os.environ["PORT"] if os.environ.get("PORT") is not None else 80

PROJECT_ID = os.environ.get("PROJECT_ID", "")
os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID

DATABASE_PREFIX = os.getenv("DATABASE_PREFIX", "")

API_BASE_URL = os.getenv("API_BASE_URL")

SERVICE_NAME = os.getenv("SERVICE_NAME")

ERROR_RESPONSES = {
    500: {
        "model": InternalServerErrorResponseModel
    },
    401: {
        "model": UnauthorizedResponseModel
    },
    422: {
        "model": ValidationErrorResponseModel
    }
}

TOKEN_TTL = 3600

ISSUER = "https://core-learning-services-dev.cloudpssolutions.com"

LTI_SERVICE_PLATFORM_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnd0embUgNn71DKfHhnVD
FdGLggMFx307Tk4gjNVtOBPs3sdOqwcengS1Q8EE5GDzmTPZIBs1KiQrX8qRiIXF
E6LWhhaOS1A51bUOoXZhEYzhUbIJ+OEpijaBGtF1VhjMRKOYqWjfl7Xlr6JsHRGe
2MNOXFx2tixTOkDthWQrm365JckxGhr0ZqL/wx1eietTzN3VRRde6R651d5BzmT7
TR0JtBtDOgbB16cGuB39FdNfm/9VWclp+SMhFZLdvV6OtsfQ4HuIG/VIY3/bEYBD
nm/Q6FmoAlkGS6bDslSBqRlBwgzofyxJVqqHHLOhMqkLrcI+PcvuV/lWVJik63ZZ
qQIDAQAB
-----END PUBLIC KEY-----"""

LTI_SERVICE_PLATFORM_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAnd0embUgNn71DKfHhnVDFdGLggMFx307Tk4gjNVtOBPs3sdO
qwcengS1Q8EE5GDzmTPZIBs1KiQrX8qRiIXFE6LWhhaOS1A51bUOoXZhEYzhUbIJ
+OEpijaBGtF1VhjMRKOYqWjfl7Xlr6JsHRGe2MNOXFx2tixTOkDthWQrm365Jckx
Ghr0ZqL/wx1eietTzN3VRRde6R651d5BzmT7TR0JtBtDOgbB16cGuB39FdNfm/9V
Wclp+SMhFZLdvV6OtsfQ4HuIG/VIY3/bEYBDnm/Q6FmoAlkGS6bDslSBqRlBwgzo
fyxJVqqHHLOhMqkLrcI+PcvuV/lWVJik63ZZqQIDAQABAoIBAAESfjih4eWaMfy8
YR0y4RaTYNBXHWpZ0nz+pJOtpDX3NyATsRgudZ1q35oz54G9tvOjTTYaMvwbGNeL
lVMVpb1lNZzBCxPhmexL7Rz8eYx6G2fLV8/Uh3cQAG7gq9ViPB/XHZ/5nYUsP/m3
j5FfwWdeHq3/MquN0a+tPtUYXI495Tw50fMPSZ9St/PAz7UYK3U6Oti693Q3ZEE7
UVyIYgFNJowHb9mGYLlncfFoAwIpWYlQpLKaJ3KIn/Jd3OtOIi7lECz4tJqHriXR
iB9ILwp58Jlvd4jAUg+d/aKg68xax/tmU3pgWrq/Umb6LOP1xF9SqZGA3q6a+LQY
jpBBABUCgYEAwIuGlF0ABc3tGei4NLo8T50EgxzyZD3QrHTv6+kEf71EMCYXilKm
vJIm2OSXPTiInKc1IoQ5wJcZIwXY7AzC5mlgUs++rzrt36vpmi1mBTagaez7eAh+
KSzOhD8Asak6rbEU23si2dngs/Cl+gwg6xtQ9vGmjgUOmIKTHTfPb+UCgYEA0eOi
N8gafeipR23OGBXSIZ/GG7iFvu3ZkBhpFQLvGh678Tz/ly+9K+monrINgAIl684z
3bzegH2eTMqVgBtCUNKfSOFoeMP7mN3bE3w7irCq2xSSAw53Zjjex76qS6XBqWKB
Cw/sPHPcWYq1b1oKX01cx/oV9yyqDoDk9g3n/nUCgYEAk54lBrgqXUjcv+Fo4Jvr
w0npfLADshCmXKGmk6JpnZm4noWFxLnLNYWDnQPcY8ZlDl0vYpAnSt1NG0nPXmIG
RuqBO9wkIGo4lyRRC7BEqDiSUcOrpAI231CH4GIBITRSVXoPOJo2RPlCyhH03jjQ
QBAISdtIy1dbMlfhfCQeuHUCgYBNv+o2iayumYIjkJx4tZSamgoT+L2qpYcjZrd+
bhDOdzYdvf/cLHYCD1NEPibcFW+gs0jpSe6OYHpEbgMFapOdRvh0UfOWUNshnIVr
6WhRDvKrpyoTccdvGYAFNC73SNa9fVzaETLsjerBTK27KvqOpSTKe2ypnGT+bGbk
cvBOhQKBgQCk9XfXF9UHsfQmG84TW2Iot7FR/rOvDdSJM2hodU/OvCrCNuvFUvof
AOByFxwW4nIRF68+72zLCPu7R/YqEG+ANekiaQCZkLESbtUbfFSquNg9/ORasPI4
rA8NcG5q2UJNxQKKChaPRrvaxQUWv6GwEI1ViCBtL8YaqEX5rRTbLg==
-----END RSA PRIVATE KEY-----"""

LTI_SERVICE_TOOL_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnd0embUgNn71DKfHhnVD
FdGLggMFx307Tk4gjNVtOBPs3sdOqwcengS1Q8EE5GDzmTPZIBs1KiQrX8qRiIXF
E6LWhhaOS1A51bUOoXZhEYzhUbIJ+OEpijaBGtF1VhjMRKOYqWjfl7Xlr6JsHRGe
2MNOXFx2tixTOkDthWQrm365JckxGhr0ZqL/wx1eietTzN3VRRde6R651d5BzmT7
TR0JtBtDOgbB16cGuB39FdNfm/9VWclp+SMhFZLdvV6OtsfQ4HuIG/VIY3/bEYBD
nm/Q6FmoAlkGS6bDslSBqRlBwgzofyxJVqqHHLOhMqkLrcI+PcvuV/lWVJik63ZZ
qQIDAQAB
-----END PUBLIC KEY-----"""

LTI_SERVICE_TOOL_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAnd0embUgNn71DKfHhnVDFdGLggMFx307Tk4gjNVtOBPs3sdO
qwcengS1Q8EE5GDzmTPZIBs1KiQrX8qRiIXFE6LWhhaOS1A51bUOoXZhEYzhUbIJ
+OEpijaBGtF1VhjMRKOYqWjfl7Xlr6JsHRGe2MNOXFx2tixTOkDthWQrm365Jckx
Ghr0ZqL/wx1eietTzN3VRRde6R651d5BzmT7TR0JtBtDOgbB16cGuB39FdNfm/9V
Wclp+SMhFZLdvV6OtsfQ4HuIG/VIY3/bEYBDnm/Q6FmoAlkGS6bDslSBqRlBwgzo
fyxJVqqHHLOhMqkLrcI+PcvuV/lWVJik63ZZqQIDAQABAoIBAAESfjih4eWaMfy8
YR0y4RaTYNBXHWpZ0nz+pJOtpDX3NyATsRgudZ1q35oz54G9tvOjTTYaMvwbGNeL
lVMVpb1lNZzBCxPhmexL7Rz8eYx6G2fLV8/Uh3cQAG7gq9ViPB/XHZ/5nYUsP/m3
j5FfwWdeHq3/MquN0a+tPtUYXI495Tw50fMPSZ9St/PAz7UYK3U6Oti693Q3ZEE7
UVyIYgFNJowHb9mGYLlncfFoAwIpWYlQpLKaJ3KIn/Jd3OtOIi7lECz4tJqHriXR
iB9ILwp58Jlvd4jAUg+d/aKg68xax/tmU3pgWrq/Umb6LOP1xF9SqZGA3q6a+LQY
jpBBABUCgYEAwIuGlF0ABc3tGei4NLo8T50EgxzyZD3QrHTv6+kEf71EMCYXilKm
vJIm2OSXPTiInKc1IoQ5wJcZIwXY7AzC5mlgUs++rzrt36vpmi1mBTagaez7eAh+
KSzOhD8Asak6rbEU23si2dngs/Cl+gwg6xtQ9vGmjgUOmIKTHTfPb+UCgYEA0eOi
N8gafeipR23OGBXSIZ/GG7iFvu3ZkBhpFQLvGh678Tz/ly+9K+monrINgAIl684z
3bzegH2eTMqVgBtCUNKfSOFoeMP7mN3bE3w7irCq2xSSAw53Zjjex76qS6XBqWKB
Cw/sPHPcWYq1b1oKX01cx/oV9yyqDoDk9g3n/nUCgYEAk54lBrgqXUjcv+Fo4Jvr
w0npfLADshCmXKGmk6JpnZm4noWFxLnLNYWDnQPcY8ZlDl0vYpAnSt1NG0nPXmIG
RuqBO9wkIGo4lyRRC7BEqDiSUcOrpAI231CH4GIBITRSVXoPOJo2RPlCyhH03jjQ
QBAISdtIy1dbMlfhfCQeuHUCgYBNv+o2iayumYIjkJx4tZSamgoT+L2qpYcjZrd+
bhDOdzYdvf/cLHYCD1NEPibcFW+gs0jpSe6OYHpEbgMFapOdRvh0UfOWUNshnIVr
6WhRDvKrpyoTccdvGYAFNC73SNa9fVzaETLsjerBTK27KvqOpSTKe2ypnGT+bGbk
cvBOhQKBgQCk9XfXF9UHsfQmG84TW2Iot7FR/rOvDdSJM2hodU/OvCrCNuvFUvof
AOByFxwW4nIRF68+72zLCPu7R/YqEG+ANekiaQCZkLESbtUbfFSquNg9/ORasPI4
rA8NcG5q2UJNxQKKChaPRrvaxQUWv6GwEI1ViCBtL8YaqEX5rRTbLg==
-----END RSA PRIVATE KEY-----"""
