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
from service.token import Token
ACCESS_TOKEN_EXPIRE=30
REFRESH_TOKEN_EXPIRE=60*24*7
ALG='HS256'
JWT_SECRET_KEY='RecipeAde_secret'
JWT_REFRESH_KEY='RecipeAde_refresh'

class UserSerivce(AppService):
    def oauth_signup(self, token):
        jwt = UserCRUD(self.db).oauth_signup_and_login(token)
        return jwt
    def create_user_email(self, user: UserSignin):
        jwt = UserCRUD(self.db).create_user(user)
        return jwt
    def user_login_email(self, user: UserBase):
        jwt = UserCRUD(self.db).user_login(user)
        return jwt
    def get_current_user(self,jwt:str):
        return UserCRUD(self.db).get_current_user(jwt)
class UserCRUD(AppCRUD):
    def oauth_signup_and_login(self, token: str):
        res = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            params={
                'access_token': token
            }
        )
        response = res.json()
        email = response.get("email")
        name = response.get("name")
        find_user = self.db.query(User).filter(User.email==email).first()
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="already exist"
            )
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect email"
            )
        if not Token.verify_pwd(user.password,find.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="pwd incorrect"
            )
        return {
            "access_token":Token.create_access_token({"email":user.email}),
            "refresh_token":Token.create_refresh_token({"email":user.email})
        }
    
    def get_current_user(self,jwt:str):
        email = Token.jwt_decode(jwt)
        user = self.db.query(User).filter(User.email == email).first()
        return user