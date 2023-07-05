from fastapi import APIRouter, Depends

from service.recipe import RecipeService
from schema.schemas import (
    Recipe,
    RecipeCreate,
    Ingredient,
    IngredientCreate,
    RecipeStep,
    RecipeStepCreate,
    Channel,
    ChannelCreate,
)

from utils.service_result import handle_result
from typing import List
from config.database import get_db

from service.youtubeAPI import YoutubeAPI


router = APIRouter(
    prefix="/recipe",
    tags=["recipe"],
    responses={404: {"description": "Not found"}},
)


@router.post("/channel/", response_model=Channel)
async def create_channel(
    channel_item: ChannelCreate,
    db: get_db = Depends(),
):
    result = RecipeService(db).create_channel(channel_item)
    return handle_result(result)


@router.get("/channel/{channel_id}", response_model=Channel)
async def get_channel(
    channel_id: int,
    db: get_db = Depends(),
):
    result = RecipeService(db).get_channel(channel_id)
    return handle_result(result)


@router.post("/", response_model=Recipe)
async def create_recipe(
    item: RecipeCreate,
    item2: List[IngredientCreate],
    item3: List[RecipeStepCreate],
    db: get_db = Depends(),
):
    result = RecipeService(db).create_recipe(item, item2, item3)
    return handle_result(result)


@router.get("/{item_id}", response_model=Recipe)
async def get_item(item_id: int, db: get_db = Depends()):
    result = RecipeService(db).get_recipe(item_id)
    return handle_result(result)


@router.get("/", response_model=List[Recipe])
async def get_items(db: get_db = Depends()):
    result = RecipeService(db).get_recipes()
    return handle_result(result)
