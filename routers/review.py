from fastapi import APIRouter, Depends, UploadFile, Form, File
from config.database import get_db
from utils.service_result import handle_result
from typing import List
from service.review import ReviewService
from typing import Annotated, List
from schema.schemas import Review, ReviewResponse

router = APIRouter(
    tags=['review']
)
@router.get("/reviews/{recipe_id}", response_model=List[ReviewResponse])
async def get_reviewss(
    recipe_id: int,
    db: get_db=Depends()
):
    res = ReviewService(db).getReviews(recipe_id)
    return handle_result(res)

@router.get("/review/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: int,
    db: get_db=Depends()
):
    res = ReviewService(db).getReview(review_id)
    return handle_result(res)

@router.post("/review/{recipe_id}", response_model=ReviewResponse)
async def post_review(
    recipe_id: int,
    authorId: Annotated[int, Form()],
    content: Annotated[str, Form()],
    files: List[UploadFile] = File(None),
    db: get_db=Depends()
):
    res = ReviewService(db).postReview(recipe_id,authorId,content,files)
    return handle_result(res)

@router.put("/review/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: int,
    content: Annotated[str,Form()],
    files: List[UploadFile] = File(None),
    db: get_db=Depends()
):
    res = ReviewService(db).updateReview(review_id, content, files)
    return handle_result(res)

@router.delete("/review/{review_id}")
async def delete_review(
    review_id,
    db: get_db=Depends()
):
    res = ReviewService(db).deleteReview(review_id)
    return handle_result(res)