from fastapi import APIRouter, Depends, Header, Request, Form
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated, Union
from config.database import get_db
from service.user import UserSerivce
from schema.schemas import UserSignin,UserBase,token,UserSignUp
from utils.service_result import handle_result
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
from service.token import googleOauth,AppleOauth2,Token

router = APIRouter(
    prefix="/login",
    tags=["login"],
    responses={404: {"description": "Not found"}},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="tokenUrl", auto_error=False)

@router.post('/oauth/google')
async def signup_google(
    token: token,
    db: get_db=Depends()
):
    return handle_result(UserSerivce(db).oauth_signup(token,"google"))

@router.post('/oauth/apple')
async def signup_apple(
    token: token,
    db: get_db=Depends()
):
    return handle_result(UserSerivce(db).oauth_signup(token,"apple"))

@router.post('/signup')
async def system_signup(
    user: UserSignUp,
    db: get_db=Depends()
):
    res = UserSerivce(db).create_user_email(user)
    return handle_result(res)

@router.post('/')
async def login(
    user: UserBase,
    db: get_db=Depends()
):
    res = UserSerivce(db).user_login_email(user)
    return handle_result(res)

@router.get('/me')
async def userinfo(
    Authorization: str = Depends(oauth2_scheme),
    db: get_db=Depends()
):
    return handle_result(UserSerivce(db).get_current_user(Authorization))

@router.post('/refresh')
async def refresh_access_token(
    token:token,
):
    res = Token.refresh_token(token)
    return handle_result(res)

@router.get('/email-validation')
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

@router.get("/all-user")
async def get_users(
    db:get_db=Depends()
):
    users = UserSerivce(db).get_users()
    return handle_result(users)

@router.post("/logout")
async def logout(
    Authorization: str = Depends(oauth2_scheme)
):
    return Token.del_refresh_token(Authorization)