from models.recipe import Recipe,Tag, Review, ReviewImage
from .main import AppCRUD, AppService
from schema.schemas import RecipeResponse, ReviewCreate, ReviewResponse
from typing import List
from utils.service_result import ServiceResult
from utils.app_exceptions import AppException
import boto3
from fastapi import UploadFile
import os
from dotenv import load_dotenv

load_dotenv()

class ReviewService(AppService):
    def getReviews(self, recipe_id:int) -> ServiceResult:
        res = ReviewCRUD(self.db).getReviews(recipe_id)
        if not res:
            return ServiceResult(AppException.FooGetItem({"item_id":recipe_id}))
        return ServiceResult(res)
    
    def deleteReview(self,review_id:int) -> ServiceResult:
        res = ReviewCRUD(self.db).deleteReview(review_id)
        if not res:
            return ServiceResult(AppException.FooGetItem({"item_id":review_id}))
        return ServiceResult(res)
    
    def getReview(self,review_id:int) -> ServiceResult:
        res = ReviewCRUD(self.db).getReview(review_id)
        if not res:
            return ServiceResult(AppException.FooGetItem({"item_id":review_id}))
        return ServiceResult(res)

    def postReview(self, recipe_id: int, authorId:int, content:str, files:List[UploadFile]) -> ServiceResult:
        res = ReviewCRUD(self.db).postReview(recipe_id,authorId,content,files)
        if not res:
            return ServiceResult(AppException.FooGetItem({"item_id":recipe_id}))
        return ServiceResult(res)

    def updateReview(self, review_id: int, content: str, files:List[UploadFile]) -> ServiceResult:
        res = ReviewCRUD(self.db).updateReview(review_id,content,files)
        if not res:
            return ServiceResult(AppException.FooGetItem({"item_id":review_id}))
        return ServiceResult(res)

class ReviewCRUD(AppCRUD):
    def s3_connect(self):
        try:
            s3 = boto3.client(
                's3',
                region_name = os.getenv("region_name"),
                aws_access_key_id = os.getenv("aws_access_key_id"),
                aws_secret_access_key= os.getenv("aws_secret_access_key")
            )
        except Exception as e:
            print(e)
        else:
            return s3
        
    def s3_upload(self,files, review, review_id):
        s3 = self.s3_connect()
        try:
            for file in files:
                imageName = "reviewId"+str(review_id)+file.filename
                s3.put_object(
                    Bucket = 'recipeade',
                    Body = file.file,
                    Key = imageName,
                    ContentType = file.content_type
                )
                imageUrl = "https://recipeade.s3.ap-northeast-2.amazonaws.com/"+imageName
                review.reviewImages.append(ReviewImage(image = imageUrl, fileName = file.filename))
            self.db.commit()
        except Exception as e:
            print(e)
        return review
            
    def getReviews(self, recipe_id:int) -> List[ReviewResponse]:
        reviews = self.db.query(Review).filter(Review.recipeId == recipe_id, Review.deleted == False).all()
        return reviews
    
    def getReview(self, review_id:int) -> ReviewResponse:
        review = self.db.query(Review).filter(Review.id == review_id, Review.deleted == False).first()
        return review
    
    def postReview(self, recipe_id: int, authorId:int, content:str, files:List[UploadFile]) -> ReviewResponse: 
        newReview = Review(author=authorId, content=content)
        recipe = self.db.query(Recipe).filter(Recipe.id==recipe_id).first()
        recipe.reviews.append(newReview)
        self.db.commit()
        reviewId = newReview.id
        self.s3_upload(files,newReview,reviewId)
        return newReview
    
    def deleteReview(self, review_id: int):
        review = self.db.query(Review).filter(Review.id == review_id).first()
        review.deleted = True
        for image in review.reviewImages:
            image.deleted = True
        self.db.commit()
        return "SUCCESS"

    def updateReview(self,review_id:int, content:str, files:List[UploadFile]) -> ReviewResponse:
        review = self.db.query(Review).filter(Review.id ==review_id).first()
        review.content = content
        reviewImages = review.reviewImages
        for reviewImage in reviewImages:
            reviewImage.deleted = True
        self.db.commit()
        self.s3_upload(files, review, review_id)
        return review