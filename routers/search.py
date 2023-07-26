from fastapi import APIRouter, Depends
from config.database import get_db
from service.search import SearchService
from schema.schemas import Recipe, RecipeResponse
from utils.service_result import handle_result
from typing import List

router = APIRouter(
    prefix="/search",
    tags=['search']
)
@router.get("/{keyword}",response_model=List[RecipeResponse])
async def searchTest(
    keyword: str,
    category: str | None = None,
    diff: str | None = None,
    sort: str | None = None,
    db: get_db=Depends()
):
    res = SearchService(db).search_service(keyword,category,diff, sort)
    return handle_result(res)