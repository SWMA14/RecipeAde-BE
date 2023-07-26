from models.recipe import Recipe,Tag
from .main import AppCRUD, AppService
from typing import List
from utils.service_result import ServiceResult
from utils.app_exceptions import AppException
from sqlalchemy import or_,desc
from schema.schemas import RecipeResponse


class SearchService(AppService):
    def search_service(self, keyword,category,diff,sort) -> ServiceResult:
        recipes = SearchCRUD(self.db).search_recipe(keyword, category,diff,sort)
        if not recipes:
            return ServiceResult(AppException.FooGetItem({"iteem_ids":None}))
        return ServiceResult(recipes)

class SearchCRUD(AppCRUD):
    def search_recipe(self,keyword,category, diff, sort) -> List[RecipeResponse]:
        query = self.db.query(Recipe)
        searchtitle = "%{}%".format(keyword)
        searchChannel = "%{}%".format(keyword)
        searchTag = "%{}%".format(keyword)
        tags = self.db.query(Tag).filter(Tag.tagName.like(searchTag)).all()
        recipeIds = [tag.recipeId for tag in tags]
        query = query.filter(or_(Recipe.youtubeTitle.like(searchtitle), Recipe.youtubeChannel.like(searchChannel), Recipe.id.in_(recipeIds)), Recipe.deleted==False)
        if category:
            query = query.filter(Recipe.category == category, Recipe.deleted == False)
        if diff:
            query = query.filter(Recipe.difficulty == diff, Recipe.deleted==False)
        if sort:
            if sort == "rating":
                query = query.order_by(desc(Recipe.rating))
            elif sort == "current":
                query = query.order_by(desc(Recipe.youtubePublishedAt))
            else:
                query = query.order_by(desc(Recipe.youtubeViewCount))
        recipes = query.all()
        return recipes