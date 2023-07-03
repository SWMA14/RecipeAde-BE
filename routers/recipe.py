from fastapi import APIRouter, Depends

from service.recipe import RecipeService
from schema.schemas import (
    Recipe,
    RecipeCreate,
    Ingredient,
    IngredientCreate,
    RecipeStep,
    RecipeStepCreate,
)

from utils.service_result import handle_result
from typing import List
from config.database import get_db


router = APIRouter(
    prefix="/recipe",
    tags=["recipe"],
    responses={404: {"description": "Not found"}},
)


@router.get("/dummy_data", response_model=List[Recipe])
async def get_dummy_data(db: get_db = Depends()):
    result = RecipeService(db).create_dummydata()
    return handle_result(result)


@router.post("/", response_model=Recipe)
async def create_item(item: RecipeCreate, db: get_db = Depends()):
    result = RecipeService(db).create_recipe(item)
    return handle_result(result)


@router.get("/{item_id}", response_model=Recipe)
async def get_item(item_id: int, db: get_db = Depends()):
    result = RecipeService(db).get_item(item_id)
    return handle_result(result)


@router.post("/ingredients", response_model=Ingredient)
async def create_ingredient(item: IngredientCreate, db: get_db = Depends()):
    result = RecipeService(db).create_ingredient(item)
    return handle_result(result)


@router.post("/ingredients/multi", response_model=List[Ingredient])
async def create_ingredients(items: List[IngredientCreate], db: get_db = Depends()):
    result = RecipeService(db).create_ingredients(items)
    return handle_result(result)


@router.post("/recipestep/multi", response_model=List[RecipeStep])
async def create_recipesteps(items: List[RecipeStepCreate], db: get_db = Depends()):
    result = RecipeService(db).create_recipeSteps(items)
    return handle_result(result)
