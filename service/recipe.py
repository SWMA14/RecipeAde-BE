from sqlalchemy.orm import Session
from models.recipe import Recipe, Ingredient, RecipeStep
from schema.schemas import RecipeCreate, IngredientCreate, RecipeStepCreate
from typing import List
from .main import AppCRUD, AppService
from utils.service_result import ServiceResult
from utils.app_exceptions import AppException


import random
import string


def random_string(length: int) -> str:
    if length > 10:
        length = 10
    elif length < 1:
        length = 1
    result = "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(length)
    )
    return result


def random_number() -> int:
    result = random.randint(1, 9999)
    return result


class RecipeService(AppService):
    def create_dummydata(self) -> ServiceResult:
        for i in range(20):
            recipe_seed = {
                "youtubeTitle": random_string(i),
                "youtubeThumnail": random_string(i),
                "youtubeTitle": random_string(i),
                "youtubeChannel": random_string(i),
                "youtubeViewCount": random_number(),
                "youtubePublishedAt": random_string(i),
                "youtubeLikeCount": random_number(),
                "youtubeTag": random_string(i),
                "youtubeDescription": random_string(i),
                "youtubeCaption": random_string(i),
                "rating": random_number(),
                "difficulty": random_string(i),
                "category": random_string(i),
            }
            db_item = RecipeCreate(**recipe_seed)
            recipe = RecipeCRUD(self.db).create_recipe(db_item)
            recipe_id = recipe.id

            for j in range(3):
                ingredient_seed = {
                    "name": random_string(j + i),
                    "quantity": random_number(),
                    "unit": random_string(j + i),
                    "recipeId": recipe_id,
                }
                db_ingredient = IngredientCreate(**ingredient_seed)
                ingredient = IngredientCRUD(self.db).create_ingredient(db_ingredient)

            for k in range(5):
                recipestep_seed = {
                    "description": random_string(k + i),
                    "timestamp": random_string(k + i),
                    "recipeId": recipe_id,
                }

                db_recipestep = RecipeStepCreate(**recipestep_seed)
                recipestep = RecipeStepCRUD(self.db).create_recipeStep(db_recipestep)

        recipes = RecipeCRUD(self.db).get_recipes()
        return ServiceResult(recipes)

    def create_recipe(self, item: RecipeCreate) -> ServiceResult:
        recipe = RecipeCRUD(self.db).create_recipe(item)
        if not recipe:
            return ServiceResult(AppException.FooCreateItem())
        return ServiceResult(recipe)

    def get_item(self, item_id: int) -> ServiceResult:
        recipe = RecipeCRUD(self.db).get_recipe(item_id)
        if not recipe:
            return ServiceResult(AppException.FooGetItem({"item_id": item_id}))
        return ServiceResult(recipe)

    def create_ingredient(self, item: IngredientCreate) -> ServiceResult:
        Ingredient = IngredientCRUD(self.db).create_ingredient(item)
        if not Ingredient:
            return ServiceResult(AppException.FooCreateItem())
        return ServiceResult(Ingredient)

    def create_ingredients(self, items: List[IngredientCreate]) -> ServiceResult:
        ingredients = IngredientCRUD(self.db).create_ingredients(items)
        if not ingredients:
            return ServiceResult(AppException.FooCreateItem())
        return ServiceResult(ingredients)

    def create_recipeStep(self, item: RecipeStepCreate) -> ServiceResult:
        recipeStep = RecipeStepCRUD(self.db).create_recipeStep(item)
        if not recipeStep:
            return ServiceResult(AppException.FooCreateItem())
        return ServiceResult(recipeStep)

    def create_recipeSteps(self, items: List[RecipeStepCreate]) -> ServiceResult:
        recipeSteps = RecipeStepCRUD(self.db).create_recipeSteps(items)
        if not recipeSteps:
            return ServiceResult(AppException.FooCreateItem())
        return ServiceResult(recipeSteps)


class RecipeCRUD(AppCRUD):
    def create_recipe(self, item: RecipeCreate) -> Recipe:
        recipe = Recipe(**item.dict())
        self.db.add(recipe)
        self.db.commit()
        self.db.refresh(recipe)
        return recipe

    def get_recipe(self, recipe_id: int) -> Recipe:
        recipe = self.db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if recipe:
            return recipe
        return None

    def get_recipes(self) -> List[Recipe]:
        recipe = self.db.query(Recipe).all()
        if recipe:
            return recipe
        return None


class IngredientCRUD(AppCRUD):
    def create_ingredient(self, item: IngredientCreate) -> Ingredient:
        ingredient = Ingredient(**item.dict())
        self.db.add(ingredient)
        self.db.commit()
        self.db.refresh(ingredient)
        return ingredient

    def create_ingredients(self, items: List[IngredientCreate]) -> List[Ingredient]:
        objects = [Ingredient(**item.dict()) for item in items]
        self.db.add_all(objects)
        self.db.commit()
        return objects


class RecipeStepCRUD(AppCRUD):
    def create_recipeStep(self, item: RecipeStepCreate) -> RecipeStep:
        recipeStep = RecipeStep(**item.dict())
        self.db.add(recipeStep)
        self.db.commit()
        self.db.refresh(recipeStep)
        return recipeStep

    def create_recipeSteps(self, items: List[RecipeStepCreate]) -> List[RecipeStep]:
        objects = [RecipeStep(**item.dict()) for item in items]
        self.db.add_all(objects)
        self.db.commit()
        return objects
