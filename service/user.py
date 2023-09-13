from models.recipe import User
from schema.schemas import (
    UserSignin,
    UserSignUp,
    UserBase
)
from .main import AppCRUD, AppService
from utils.service_result import ServiceResult
from utils.app_exceptions import AppException
from fastapi import requests, HTTPException, status
import requests
from service.token import Token,googleOauth,AppleOauth2
ACCESS_TOKEN_EXPIRE=30
REFRESH_TOKEN_EXPIRE=60*24*7
ALG='HS256'
JWT_SECRET_KEY='RecipeAde_secret'
JWT_REFRESH_KEY='RecipeAde_refresh'

class UserSerivce(AppService):
    def oauth_signup(self, token,platform):
        if not "Bearer" in token:
            return ServiceResult(AppException.FooInvalidToken({"msg":"Invalid access-Token form"}))
        jwt = UserCRUD(self.db).oauth_signup_and_login(token[7:],platform)
        return ServiceResult(jwt)
    def create_user_email(self, user: UserSignin):
        jwt = UserCRUD(self.db).create_user(user)
        return jwt
    def user_login_email(self, user: UserBase):
        jwt = UserCRUD(self.db).user_login(user)
        return jwt
    def get_current_user(self,jwt):
        if not "Bearer" in jwt:
            return ServiceResult(AppException.FooInvalidToken({"msg":"Invalid access-Token form"}))
        return ServiceResult(UserCRUD(self.db).get_current_user(jwt[7:]))
    def access_token_refresh(self,token):
        if not "Bearer" in token:
            return ServiceResult(AppException.FooInvalidToken({"msg":"Invalid fresh-Token form"}))
        jwt = UserCRUD(self.db).refresh_tokens(token[7:])
        return ServiceResult(jwt)
    def refresh_token(self,token):
        if not "Bearer" in token:
            return ServiceResult(AppException.FooInvalidToken({"msg":"Invalid refresh-Token form"}))
        return ServiceResult(UserCRUD(self.db).refresh_tokens(token[7:]))
class UserCRUD(AppCRUD):
    def oauth_signup_and_login(self, token: str, platform: str):
        userdata = AppleOauth2().get_user_info(token) if platform == "apple" else googleOauth().get_user_info(token)
        email = userdata["email"]
        name = userdata["name"]
        find_user = self.db.query(User).filter(User.email == email).first()
        if not find_user:
            self.db.add(User(email=email, name=name))
            self.db.commit()
        return {
            "access_token":Token.create_access_token({"email":email}),
            "refresh_token":Token.create_refresh_token({"email":email})
        }
    
    def create_user(self, user: UserSignin):
        find_user = self.db.query(User).filter(User.email==user.email).first()
        if find_user:
            raise AppException.FooCreateItem({"msg":"email alredy exist"})
        new_user = User(
            password = Token.get_hashed_pwd(user.password),
            email = user.email,
            name = user.name
        )
        self.db.add(new_user)
        self.db.commit()
        return {
            "access_token":Token.create_access_token({"email":user.email}),
            "refresh_token":Token.create_refresh_token({"email":user.email})
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
        return {
            "access_token":Token.create_access_token({"email":user.email}),
            "refresh_token":Token.create_refresh_token({"email":user.email})
        }
    
    def get_current_user(self,jwt:str):
        email = Token.jwt_decode(jwt,"access_token")
        user = self.db.query(User).filter(User.email == email).first()
        return user
    
    def refresh_tokens(self, refresh_token):
        email = Token.jwt_decode(refresh_token,"refresh_token")
        # user = self.db.query(User).filter(User.refresh == refresh_token).first()
        # access_token = Token.create_access_token({"email":email})
        # refresh = Token.create_refresh_token({"email":email})
        # user.refresh=refresh

        return {
            "access_token":Token.create_access_token({"email":email}),
            "refresh_token":Token.create_refresh_token({"email":email})
        }