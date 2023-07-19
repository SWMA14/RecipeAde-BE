from config.database import get_db
from fastapi import APIRouter, Depends
from schema.schemas import User
from service.user import UserService

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{uid}", response_model=User)
async def get_user(
    uid: int,
    db: get_db = Depends()
):
    result = UserService.get_user(uid)
    return result