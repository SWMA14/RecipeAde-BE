from fastapi import APIRouter, Depends, Header, Request, Form
from typing import Annotated, Union
from config.database import get_db
from service.user import UserSerivce
from schema.schemas import UserSignin,UserBase
from utils.service_result import handle_result
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
from service.token import googleOauth,AppleOauth2

class Refresh_token(BaseModel):
    refresh_token:str

router = APIRouter(
    prefix="/login",
    tags=["login"],
    responses={404: {"description": "Not found"}},
)

@router.get('/oauth/google')
async def signup_google(
    Authorization: Union[str,None] = Header(default=""),
    db: get_db=Depends()
):
    return handle_result(UserSerivce(db).oauth_signup(Authorization,"google"))

@router.get('/oauth/apple')
async def signup_apple(
    Authorization: Union[str,None] = Header(default=""),
    db: get_db=Depends()
):
    return handle_result(UserSerivce(db).oauth_signup(Authorization,"apple"))

@router.post('/signup')
async def system_signup(
    user: UserSignin,
    db: get_db=Depends()
):
    return UserSerivce(db).create_user_email(user)

@router.post('/')
async def login(
    user: UserBase,
    db: get_db=Depends()
):
    return UserSerivce(db).user_login_email(user)

@router.get('/me')
async def userinfo(
    Authorization: Union[str,None] = Header(default=""),
    db: get_db=Depends()
):
    return handle_result(UserSerivce(db).get_current_user(Authorization))

@router.post('/refresh')
async def refresh_access_token(
    #refresh:Refresh_token,
    Authorization: Union[str,None] = Header(default=""),
    db: get_db=Depends()
):
    return handle_result(UserSerivce(db).refresh_token(Authorization))

@router.get('/possible')
async def email_validate(
    email: str,
    db: get_db=Depends()
):
    return handle_result(UserSerivce(db).email_validate(email))
    
@router.get('/oauth/gettoken')
async def get_auth_code(
):
    return RedirectResponse(googleOauth.get_auth_code())

@router.get('/callback')
async def callback(
    req:Request,
    db:get_db=Depends()
):
    code = req.query_params.get("code")
    return googleOauth().get_user_info(code)

@router.get("/apple/token")
async def get_code(
):
    return RedirectResponse(AppleOauth2.get_auth_code())

@router.post("/apple/callback")
async def apple_login(
    code:Annotated[str,Form()],
    db:get_db=Depends()
):
    return UserSerivce(db).oauth_signup(code,"apple")