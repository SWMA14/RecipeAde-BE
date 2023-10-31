from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from service.recipe import RecipeService, RecipeCRUD
from service.recommend import RecommendService
from service.user import UserCRUD
from schema.schemas import (
    CustomizeCreate,
    CustomizeUpdate,
    CustomizeRecipeResponse,
    dynamoResponse,
    dynamoDbRecipe
)
from schema.schemas import User
from utils.service_result import handle_result
from typing import List,Annotated
from config.database import get_db,get_test_db
from service.customize import CustomizeService, CustomizeCRUD
from service.defaultRecipes import defaultRecipesService


router = APIRouter(
    prefix="/customize",
    tags=["customize recipe"],
    responses={404: {"description": "Not found"}},
)
db_sys = get_test_db
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="tokenUrl", auto_error=False)

@router.get("/recipe/{recipeId}", response_model=CustomizeRecipeResponse)
async def get_customize(
    recipeId:str,
    token:str = Depends(oauth2_scheme),
    db:db_sys = Depends()
):
    res = CustomizeService(db,token).get_customize(recipeId)
    return handle_result(res)

@router.get("/recipes", response_model=List[CustomizeRecipeResponse])
async def get_recipes(
    token:str = Depends(oauth2_scheme),
    db: db_sys = Depends()
):
    res = CustomizeService(db,token).get_customize_recipes()
    return handle_result(res)

@router.post("/update/{recipeId}", response_model=CustomizeRecipeResponse)
async def udpate_customize(
    recipeId:str,
    recipe: CustomizeUpdate,
    token:str = Depends(oauth2_scheme),
    db:db_sys = Depends()
):
    res = CustomizeService(db,token).update_customize(recipe,recipeId)
    return handle_result(res)

@router.delete("/{recipeId}")
async def delete_customize(
    recipeId:str,
    token:str = Depends(oauth2_scheme),
    db:db_sys = Depends()
):
    res = CustomizeService(db,token).delete_customize(recipeId)
    return handle_result(res)

@router.post("/create_default", response_model=CustomizeRecipeResponse)
async def create_customize(
    sourceLink: str,
    backgroundTasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme),
    db: db_sys = Depends()
):
    res = CustomizeService(db,token).create_default(sourceLink,backgroundTasks)
    return handle_result(res)

@router.get("/getAllDefaults",response_model=List[dynamoDbRecipe])
async def get_all_default_from_db():
    res = defaultRecipesService().getallRecipes()
    return handle_result(res)

@router.get("/check_valid")
async def test(
    sourceLink: str,
    db: db_sys = Depends()
):
    token=""
    return CustomizeCRUD(db,token).check_valid_url(sourceLink)