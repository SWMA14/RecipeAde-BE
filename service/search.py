from models.recipe import Recipe,Tag
from .main import AppCRUD, AppService
from schema.schemas import RecipeResponse
from typing import List
from utils.service_result import ServiceResult
from utils.app_exceptions import AppException

class SearchService(AppService):
    def getRecipesByTitle(self, title: str) -> ServiceResult:
        recipes = SearchCRUD(self.db).getRecipesByTitle(title)
        if not recipes:
            return ServiceResult(AppException.FooGetItem({"item": None}))
        return ServiceResult(recipes)
    
    def getRecipesByChannel(self, channel: str) -> ServiceResult:
        recipes = SearchCRUD(self.db).getRecipesByChannel(channel)
        if not recipes:
            return ServiceResult(AppException.FooGetItem({"item": None}))
        return ServiceResult(recipes)
    
    def getRecipesByTag(self,tag:str) -> ServiceResult:
        recipes = SearchCRUD(self.db).getRecipesByTag(tag)
        if not recipes:
            return ServiceResult(AppException.FooGetItem({"item": None}))
        return ServiceResult(recipes)

class SearchCRUD(AppCRUD):
    def getRecipesByTitle(self, title: str) -> List[RecipeResponse]:
        searchtitle = "%{}%".format(title)
        recipes = self.db.query(Recipe).filter(Recipe.youtubeTitle.like(searchtitle)).all()
        if recipes:
            return recipes
        return None

    def getRecipesByChannel(self, channel: str) -> List[RecipeResponse]:
        searchChannel = "%{}%".format(channel)
        recipes = self.db.query(Recipe).filter(Recipe.youtubeChannel.like(searchChannel)).all()
        if recipes:
            return recipes
        return None
    
    def getRecipesByTag(self, tag: str) -> List[RecipeResponse]:
        searchTag = "%{}%".format(tag)
        tags = self.db.query(Tag).filter(Tag.tagName.like(searchTag)).all()
        recipes=[]
        for tag in tags:
            recipes.append(tag.recipe)
        if recipes:
            return recipes
        return None