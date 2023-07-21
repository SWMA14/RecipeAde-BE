from fastapi import APIRouter, Depends, UploadFile

from service.recipe import RecipeService, SearchTest
from service.recommend import RecommendService
from service.search import SearchService
from service.review import ReviewService
from schema.schemas import (
    Recipe,
    RecipeCreate,
    IngredientCreate,
    RecipeStepCreate,
    Channel,
    ChannelCreate,
    ReviewCreate
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


@router.get("/recoomend/", response_model=List[Recipe])
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


@router.post("", response_model=Recipe)
async def create_recipe(
    item: RecipeCreate,
    item2: List[IngredientCreate],
    item3: List[RecipeStepCreate],
    channelID: str,
    db: get_db = Depends(),
):
    result = RecipeService(db).create_recipe(item, item2, item3, channelID)
    return handle_result(result)


@router.get("/{item_id}", response_model=Recipe)
async def get_item(item_id: int, db: get_db = Depends()):
    result = RecipeService(db).get_recipe(item_id)
    return handle_result(result)


@router.get("", response_model=List[Recipe])
async def get_items(db: get_db = Depends()):
    result = RecipeService(db).get_recipes()
    return handle_result(result)

@router.get("/search/", response_model=List[Recipe])
async def get_recipe_by_search(
    title: str | None = None,
    channel: str | None = None,
    tag: str | None = None,
    db: get_db=Depends()
):
    if title:
        result = SearchService(db).getRecipesByTitle(title)
        return handle_result(result)
    elif channel:
        result = SearchService(db).getRecipesByChannel(channel)
        return handle_result(result)
    elif tag:
        result = SearchService(db).getRecipesByTag(tag)
        return handle_result(result)
    else:
        return "none"
    
@router.get("/review/{recipe_id}")
async def get_reviews(
    recipe_id: int,
    db: get_db=Depends()
):
    res = ReviewService(db).getReviews(recipe_id)
    return handle_result(res)

@router.post("/review/{recipe_id}")
async def post_review(
    recipe_id: int,
    #review: ReviewCreate,
    file: UploadFile | None = None,
    db: get_db=Depends()
):
    ReviewService(db).postReview(recipe_id,file)

    
@router.get("/searchTest/{keyword}")
async def searchTest(
    keyword: str,
    category: str | None = None,
    diff: str | None = None,
    sort: str | None = None,
    db: get_db=Depends()
):
    return SearchTest(db).searchTest(keyword,category,diff, sort)