from models.recipe import User
from schema.schemas import (
    UserSignin,
    UserSignUp,
    UserBase,
    token
)
from .main import AppCRUD, AppService
from utils.service_result import ServiceResult
from utils.app_exceptions import AppException
from fastapi import requests, HTTPException, status
from service.token import Token,googleOauth,AppleOauth2
import re
ACCESS_TOKEN_EXPIRE=30 # 30분
REFRESH_TOKEN_EXPIRE=60*24*7 # 7일

class UserSerivce(AppService):
    def oauth_signup(self, token:token,platform:str):
        if not token.token_type == "id_token":
            return ServiceResult(AppException.FooInvalidToken({"msg":"not id_token"}))
        jwt = UserCRUD(self.db).oauth_login(token.token,platform)
        return ServiceResult(jwt)
    def create_user_email(self, user: UserSignin):
        jwt = UserCRUD(self.db).create_user(user)
        return ServiceResult(jwt)
    def user_login_email(self, user: UserBase):
        jwt = UserCRUD(self.db).user_login(user)
        return ServiceResult(jwt)
    def get_current_user(self,jwt):
        if not jwt:
            return ServiceResult(AppException.UnauthorizedUser({"msg":"unauthorized user request"}))
        return ServiceResult(UserCRUD(self.db).get_current_user(jwt))
    def email_validate(self,email:str):
        return ServiceResult(UserCRUD(self.db).email_validate(email))
    def get_users(self):
        users = UserCRUD(self.db).get_all_users()
        if not users:
            return ServiceResult(AppException.FooGetItem({"msg":"users not exist"}))
        return ServiceResult(users)
        
class UserCRUD(AppCRUD):
    def oauth_login(self, token: str, platform: str):
        userdata = AppleOauth2().get_user_info(token) if platform == "apple" else googleOauth().get_user_info(token)
        email = userdata["email"]
        find_user = self.db.query(User).filter(User.email == email).first()
        if not find_user:
            raise AppException.FooGetItem({"msg":"not exist oauth user"})
        access_token,refresh_token = Token.create_token(email)
        return {
            "access_token":access_token,
            "refresh_token":refresh_token
        }
    
    def create_user(self, user: UserSignUp):
        find_user = self.db.query(User).filter(User.email==user.email).first()
        if find_user:
            raise AppException.FooCreateItem({"msg":"email alredy exist"})
        new_user = User(
            age = user.age,
            gender = user.gender,
            password = Token.get_hashed_pwd(user.password),
            email = user.email,
            name = user.name,
        )
        access_token,refresh_token = Token.create_token(user.email)
        self.db.add(new_user)
        self.db.commit()
        return {
            "access_token":access_token,
            "refresh_token":refresh_token
        }
    
    def user_login(self,user:UserBase):
        find = self.db.query(User).filter(User.email == user.email).first()
        if not find:
            raise AppException.FooGetItem(
                {"msg":"invalid email"}
            )
        if not Token.verify_pwd(user.password,find.password):
            raise AppException.FooGetItem(
                {"msg":"password incorrect"}
            )
        access_token,refresh_token = Token.create_token(user.email)
        return {
            "access_token":access_token,
            "refresh_token":refresh_token
        }
    
    def get_current_user(self,jwt:str):
        email = Token.jwt_decode(jwt,"access_token")
        user = self.db.query(User).filter(User.email == email).first()
        return user
    
    def get_all_users(self):
        return self.db.query(User).filter().all()
    
    def email_validate(self,email:str):
        pattern = r"[a-zA-Z0-9-+.]+@[a-zA-Z]+\.\w+"
        if not re.match(pattern,email):
            return AppException.FooCreateItem({"msg":"Invalid Email Form"})
        find_user = self.db.query(User).filter(User.email==email).first()
        if find_user:
            return AppException.FooCreateItem({"msg":"email alredy exist"})
        return {"msg":"valid Email Form"}