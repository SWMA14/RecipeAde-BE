from fastapi import APIRouter, Depends, Request
from jose import jwt
from datetime import timezone, timedelta
import requests
from service.login import AppleOauth2

router = APIRouter(
    prefix="/login",
    tags=["login"],
    responses={404: {"description": "Not found"}},
)


@router.get("/oauth_apple")
async def oauth_apple(request: Request):
    """
    Apple OAuth2
    """
    code = request.query_params.get("code")
    apple = AppleOauth2()
    response = apple.do_auth(code)
    return response
