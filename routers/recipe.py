from fastapi import APIRouter, Depends

from service.recipe import RecipeService, RecipeCRUD
from service.recommend import RecommendService
from schema.schemas import (
    Recipe,
    RecipeCreate,
    IngredientCreate,
    RecipeStepCreate,
    Channel,
    ChannelCreate,
    RecipeResponse,
    TagCreate,
    RecipeResponseDetail
)

from utils.service_result import handle_result
from typing import List,Annotated
from config.database import get_db

from pydantic import BaseModel


router = APIRouter(
    prefix="/recipe",
    tags=["recipe"],
    responses={404: {"description": "Not found"}},
)

class Item(BaseModel):
    video:str
    thumbnail:str
    title:str
    viewCount:int
    channel:str
    publishedAt:str
    difficulty:int
    cateogry:str
    ingredients: List[IngredientCreate]
    steps: List[RecipeStepCreate]

@router.get("/recommend/", response_model=List[Recipe])
async def get_recipes_by_same(
    difficulty: str | None = None,
    category: str | None = None,
    db: get_db = Depends(),
):
    if difficulty:
        result = RecommendService(db).get_recipes_by_same_difficulty(difficulty)
        return handle_result(result)
    else:
        result = RecommendService(db).get_recipes_by_same_category(category)
        return handle_result(result)


@router.post("/channel", response_model=Channel)
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


@router.post("", response_model=RecipeResponse)
async def create_recipe(
    item: RecipeCreate,
    item2: List[IngredientCreate],
    item3: List[RecipeStepCreate],
    tags: List[TagCreate],
    db: get_db = Depends(),
):
    result = RecipeService(db).create_recipe(item, item2, item3, tags)
    return handle_result(result)


@router.get("/{item_id}", response_model=RecipeResponseDetail)
async def get_item(item_id: int, db: get_db = Depends()):
    result = RecipeService(db).get_recipe(item_id)
    return handle_result(result)


@router.get("", response_model=List[RecipeResponse])
async def get_items(db: get_db = Depends()):
    result = RecipeService(db).get_recipes()
    return handle_result(result)

@router.delete("/{recipe_id}")
async def delete_recipe(recipe_id: int, db:get_db = Depends()):
    RecipeService(db).delete_recipe(recipe_id)

@router.post('/insert')
async def insert_data(
    item : Item,
    db: get_db = Depends(),
    ):
    res = RecipeCRUD(db).insert_data(
        videoId=item.video,
        thumbnail=item.thumbnail,
        title=item.title,
        viewCount=item.viewCount,
        channelname=item.channel,
        publishedAt=item.publishedAt,
        difficulty=item.difficulty,
        category=item.cateogry,
        ingredients=item.ingredients,
        recipeSteps=item.steps
    )
    return res

@router.post('insertById')
async def isnert_by_id(
    videoId: str,
    difficulty: int,
    category: str,
    ingredients:List[IngredientCreate],
    recipeSteps:List[RecipeStepCreate],
    db:get_db = Depends()
):
    res = RecipeCRUD(db).create_recipe_by_id(videoId=videoId,category=category,difficulty=difficulty, ingredients=ingredients, recipeSteps=recipeSteps)
    return res