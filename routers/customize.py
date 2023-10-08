from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from service.recipe import RecipeService, RecipeCRUD
from service.recommend import RecommendService
from service.user import UserCRUD
from schema.schemas import (
    CustomizeCreate,
    CustomizeUpdate
)
from schema.schemas import User
from utils.service_result import handle_result
from typing import List,Annotated
from config.database import get_db
from service.customize import CustomizeService, CustomizeCRUD


router = APIRouter(
    prefix="/customize",
    tags=["customize recipe"],
    responses={404: {"description": "Not found"}},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="tokenUrl", auto_error=False)

@router.get("/recipe/{recipeId}")
async def get_customize(
    recipeId:str,
    token:str = Depends(oauth2_scheme),
    db:get_db = Depends()
):
    res = CustomizeService(db,token).get_customize(recipeId)
    return handle_result(res)

@router.get("/recipes")
async def get_recipes(
    token:str = Depends(oauth2_scheme),
    db: get_db = Depends()
):
    res = CustomizeService(db,token).get_customize_recipes()
    return handle_result(res)

@router.post("/create")
async def create_customize(
    recipe: CustomizeCreate,
    token:str = Depends(oauth2_scheme),
    db:get_db = Depends()
):
    res = CustomizeService(db,token).create_customize(recipe)
    return handle_result(res)

@router.post("/update/{recipeId}")
async def udpate_customize(
    recipeId:str,
    recipe: CustomizeUpdate,
    token:str = Depends(oauth2_scheme),
    db:get_db = Depends()
):
    res = CustomizeService(db,token).update_customize(recipe,recipeId)
    return handle_result(res)

@router.delete("/{recipeId}")
async def delete_customize(
    recipeId:str,
    token:str = Depends(oauth2_scheme),
    db:get_db = Depends()
):
    res = CustomizeService(db,token).delete_customize(recipeId)
    return handle_result(res)

@router.get("/create_default")
async def test(
    sourceLink: str,
    token:str = Depends(oauth2_scheme),
    db:get_db = Depends()
):
    res = CustomizeCRUD(db,token).create_default(sourceLink)
    return res  