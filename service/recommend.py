from models.recipe import Recipe
from .main import AppCRUD, AppService
from schema.schemas import RecipeResponse
from typing import List
from utils.service_result import ServiceResult
from utils.app_exceptions import AppException


class RecommendService(AppService):
    def get_recipes_by_same_category(self, category: str) -> ServiceResult:
        recipes = RecommendCRUD(self.db).get_recipes_by_same_category(category)
        if not recipes:
            return ServiceResult(AppException.FooGetItem({"item": None}))
        return ServiceResult(recipes)

    def get_recipes_by_same_difficulty(self, difficulty: str) -> ServiceResult:
        recipes = RecommendCRUD(self.db).get_recipes_by_same_difficulty(difficulty)
        if not recipes:
            return ServiceResult(AppException.FooGetItem({"item": None}))
        return ServiceResult(recipes)


class RecommendCRUD(AppCRUD):
    def get_recipes_by_same_category(self, categroy: str) -> List[RecipeResponse]:
        recipes = self.db.query(Recipe).filter(Recipe.category == categroy).all()
        if recipes:
            return recipes
        return None

    def get_recipes_by_same_difficulty(self, difficulty: str) -> List[RecipeResponse]:
        recipes = self.db.query(Recipe).filter(Recipe.difficulty == difficulty).all()
        if recipes:
            return recipes
        return None
