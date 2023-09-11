from fastapi import APIRouter, Depends, Request
from typing import Annotated
from config.database import get_db
from service.user import UserSerivce
from schema.schemas import UserSignin,UserBase


router = APIRouter(
    prefix="/login",
    tags=["login"],
    responses={404: {"description": "Not found"}},
)

@router.get('/signup/oauth')
async def signup(
    token: str,
    db: get_db=Depends()
):
    return UserSerivce(db).oauth_signup(token)

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
    token: str,
    db: get_db=Depends()
):
    return UserSerivce(db).get_current_user(token)