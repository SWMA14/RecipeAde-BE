from datetime import datetime,timedelta,timezone
from jose import jwt
from dotenv import load_dotenv
from passlib.context import CryptContext
from pydantic import ValidationError
from fastapi import HTTPException,status, Request
import requests
import jwt
import os
from utils.app_exceptions import AppException
import urllib.parse
import redis
from schema.schemas import token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_EXPIRE = 30
REFRESH_TOKEN_EXPIRE = 60 * 24 * 7
ALG = os.getenv("ALGORYTHM")
JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY")
JWT_REFRESH_KEY=os.getenv("JWT_REFRESH_KEY")

load_dotenv()

def redis_config() -> redis.Redis:
    try:
        rd = redis.Redis("host.docker.internal",6379,charset="UTF-8",db=0,decode_responses=True)
        return rd
    except:
        raise AppException.FooInvalidToken({"msg":"redis connection failed"})

class AppleOauth2:
    def get_user_info(self, token):
        try:
            token_decode = jwt.decode(token,"",options={"verify_signature":False})
            email = token_decode["email"]
            return {
                "email":email
            }
        except:
            raise AppException.FooInvalidToken({"msg":"invalid apple id_token"})


class googleOauth:
    def get_user_info(self,code):
        try:
            token_decode = jwt.decode(code,"",options={"verify_signature":False})
            email = token_decode["email"]
            return {
                "email":email
            }
        except:
            raise AppException.FooInvalidToken({"msg":"invalid google id_token"})
        # res = requests.get(
        #     "https://www.googleapis.com/oauth2/v3/userinfo",
        #     params={
        #         'access_token': code
        #     }
        # )
        # response = res.json()
        # print(response)
        # email = response.get("email")
        # return {
        #     "email":email
        # }
    
class Token:
    def get_hashed_pwd(password: str) -> str:
        return pwd_context.hash(password)
    
    def verify_pwd(password: str, hashed_pwd:str) -> bool:
        return pwd_context.verify(password,hashed_pwd)
    
    def create_access_token(data:dict, expires_delta:int = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE)
        
        to_encode.update({"exp":expire})
        encoded_jwt = jwt.encode(to_encode,JWT_SECRET_KEY,ALG)
        return encoded_jwt
    
    def create_refresh_token(data:dict, expires_delta:int = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE)
        
        to_encode.update({"exp":expire})
        encoded_jwt = jwt.encode(to_encode,JWT_REFRESH_KEY,ALG)
        return encoded_jwt
    
    def jwt_decode(token:str, type:str):
        key = JWT_SECRET_KEY if type=="access_token" else JWT_REFRESH_KEY
        try:
            payload = jwt.decode(token,key,algorithms=ALG)
        except jwt.exceptions.InvalidSignatureError:
            raise AppException.FooInvalidToken({"msg":"invalid token"})
        except jwt.exceptions.ExpiredSignatureError:
            raise AppException.FooInvalidToken({"msg":"token expired"})
        except Exception as e:
            raise AppException.FooInvalidToken({"msg":e})
        return payload.get("email")
    
    def set_refresh_token(email:str, token:str):
        try:
            rd = redis_config()
            rd.set(email,token)
        except Exception as e:
            raise AppException.FooInvalidToken({"msg":"set refresh token failed"})

    def del_refresh_token(token:str):
        try:
            email = Token.jwt_decode(token,"access_token")
            rd = redis_config()
            rd.delete(email)
        except:
            raise AppException.FooInvalidToken({"msg":"delete refresh token failed"})
    
    def create_token(email:str):
        access_token = Token.create_access_token({"email":email})
        refresh_token = Token.create_refresh_token({"email":email})
        Token.set_refresh_token(email,refresh_token)
        return access_token,refresh_token
    
    def refresh_token(refresh:token):
        if not refresh.token_type == "refresh_token":
            raise AppException.FooInvalidToken({"msg":"not refresh token"})
        rd = redis_config()
        token = refresh.token
        try:
            email = Token.jwt_decode(token,"refresh")
            if rd.get(email) == token:
                access_token = Token.create_access_token({"email":email})
                refresh_token = Token.create_refresh_token({"email":email})
                rd.set(email,refresh_token)
                return {
                    "access_token":access_token,
                    "refresh_token":refresh_token
                }
            else:
                raise AppException.FooInvalidToken({"msg":"Invalid Refresh Token"})
        except Exception as e:
            raise AppException.FooGetItem({"msg":"no refresh token exist"})
