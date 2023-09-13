from jose import jwt
from datetime import datetime,timedelta,timezone
from dotenv import load_dotenv
from passlib.context import CryptContext
from pydantic import ValidationError
from fastapi import HTTPException,status, Request
import requests
import jwt
import os
from utils.app_exceptions import AppException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_EXPIRE = 1
REFRESH_TOKEN_EXPIRE = 60 * 24 * 7
ALG = os.getenv("ALGORYTHM")
JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY")
JWT_REFRESH_KEY=os.getenv("JWT_REFRESH_KEY")

load_dotenv()

class AppleOauth2:
    """
    Apple Authentication Backend
    """

    __name__ = "apple"
    ACCESS_TOKEN_URL = "https://appleid.apple.com/auth/token"

    def get_user_info(self, access_token):
        response_data = {}
        client_id = "net.recipeade.svelte"
        client_secret = self.get_key_and_secret()

        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": access_token,
            "grant_type": "authorization_code",
            "redirect_uri": "https://recipeade.net/login/oauth_apple",
        }

        res = requests.post(AppleOauth2.ACCESS_TOKEN_URL, data=data, headers=headers)
        response_dict = res.json()
        id_token = response_dict.get("id_token", None)

        if id_token:
            decoded = jwt.decode(id_token, "", verify=False)
            response_data.update(
                {"email": decoded["email"]} if "email" in decoded else None
            )
            response_data.update({"name": decoded["sub"]} if "sub" in decoded else None)

        return response_data

    def get_key_and_secret(self):
        """
        Get Key and Secret from settings
        """
        headers = {"kid": os.getenv("SOCIAL_AUTH_APPLE_KEY_ID")}

        payload = {
            "iss": "49AL3MH8WT",
            "iat": timezone.now(),
            "exp": timezone.now() + timedelta(days=180),
            "aud": "https://appleid.apple.com",
            "sub": os.getenv("SOCIAL_AUTH_CLIENT_ID"),
        }

        client_secret = jwt.encode(
            payload,
            os.getenv("SOCIAL_AUTH_APPLE_PRIVATE_KEY"),
            algorithm="ES256",
            headers=headers,
        ).decode("utf-8")

        return client_secret

class googleOauth:
    def get_user_info(self,token):
        res = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            params={
                'access_token': token
            }
        )
        response = res.json()
        email = response.get("email")
        name = response.get("name")
        return {
            "email":email,
            "name":name
        }
    
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
            print(payload)
        except jwt.exceptions.InvalidSignatureError:
            raise AppException.FooInvalidToken({"msg":"invalid token"})
        except jwt.exceptions.ExpiredSignatureError:
            raise AppException.FooInvalidToken({"msg":"token expired"})
        return payload.get("email")