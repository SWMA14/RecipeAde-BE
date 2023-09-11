from jose import jwt
from datetime import datetime,timedelta
from passlib.context import CryptContext
from pydantic import ValidationError
from fastapi import HTTPException,status
import jwt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_EXPIRE = 30
REFRESH_TOKEN_EXPIRE = 60 * 24 * 7
ALG = 'HS256'
JWT_SECRET_KEY='secret'
JWT_REFRESH_KEY='refresh'

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
    
    def jwt_decode(token:str):
        try:
            payload = jwt.decode(token,JWT_SECRET_KEY,algorithms=ALG)

            if datetime.fromtimestamp(payload.get("exp")) < datetime.now():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="token expired", headers={"WWW-Authenticate":"Bearer"}
                )
        except (jwt.exceptions.InvalidTokenError,ValidationError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="could not validate token",headers={"WWW-Authenticate":"Bearer"}
            )
        return payload.get("email")