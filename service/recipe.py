from models.recipe import Recipe, Ingredient, RecipeStep
from schema.schemas import RecipeCreate, IngredientCreate, RecipeStepCreate
from typing import List
from .main import AppCRUD, AppService
from utils.service_result import ServiceResult
from utils.app_exceptions import AppException
from .youtubeAPI import YoutubeAPI

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


# for i in range(20):
#     recipe_seed = {
#         "youtubeTitle": random_string(i),
#         "youtubeThumnail": random_string(i),
#         "youtubeTitle": random_string(i),
#         "youtubeChannel": random_string(i),
#         "youtubeViewCount": random_number(),
#         "youtubePublishedAt": random_string(i),
#         "youtubeLikeCount": random_number(),
#         "youtubeTag": random_string(i),
#         "youtubeDescription": random_string(i),
#         "youtubeCaption": random_string(i),
#         "rating": random_number(),
#         "difficulty": random_string(i),
#         "category": random_string(i),
#     }
#     db_item = RecipeCreate(**recipe_seed)
#     recipe = RecipeCRUD(self.db).create_recipe(db_item)
#     recipe_id = recipe.id

#     for j in range(3):
#         ingredient_seed = {
#             "name": random_string(j + i),
#             "quantity": random_number(),
#             "unit": random_string(j + i),
#             "recipeId": recipe_id,
#         }
#         db_ingredient = IngredientCreate(**ingredient_seed)
#         ingredient = IngredientCRUD(self.db).create_ingredient(db_ingredient)

#     for k in range(5):
#         recipestep_seed = {
#             "description": random_string(k + i),
#             "timestamp": random_string(k + i),
#             "recipeId": recipe_id,
#         }

#         db_recipestep = RecipeStepCreate(**recipestep_seed)
#         recipestep = RecipeStepCRUD(self.db).create_recipeStep(db_recipestep)

# recipes = RecipeCRUD(self.db).get_recipes()


class RecipeService(AppService):
    def create_recipe(
        self,
        item: RecipeCreate,
        ingredient_items: List[IngredientCreate],
        recipeStep_items: List[RecipeStepCreate],
    ) -> ServiceResult:
        recipe = RecipeCRUD(self.db).create_recipe(
            item=item,
            ingredient_items=ingredient_items,
            recipeStep_items=recipeStep_items,
        )
        if not recipe:
            return ServiceResult(AppException.FooCreateItem())
        return ServiceResult(recipe)

    def get_recipe(self, item_id: int) -> ServiceResult:
        recipe = RecipeCRUD(self.db).get_recipe(item_id)
        if not recipe:
            return ServiceResult(AppException.FooGetItem({"item_id": item_id}))
        return ServiceResult(recipe)

    def get_recipes(self) -> ServiceResult:
        recipes = RecipeCRUD(self.db).get_recipes()
        if not recipes:
            return ServiceResult(AppException.FooGetItem({"item_ids": None}))
        return ServiceResult(recipes)


class RecipeCRUD(AppCRUD):
    def create_recipe(
        self,
        item: RecipeCreate,
        ingredient_items: List[IngredientCreate],
        recipeStep_items: List[RecipeStepCreate],
    ) -> Recipe:
        recipe = Recipe(**item.dict())
        self.db.add(recipe)
        self.db.flush()
        ingredients = IngredientCRUD(self.db).create_ingredients(
            ingredient_items, recipe.id
        )
        recipeSteps = RecipeStepCRUD(self.db).create_recipeSteps(
            recipeStep_items, recipe.id
        )
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
    def create_ingredients(
        self, items: List[IngredientCreate], recipe_id: int
    ) -> List[Ingredient]:
        objects = [Ingredient(**item.dict(), recipeId=recipe_id) for item in items]
        self.db.add_all(objects)
        # self.db.commit()
        return objects


class RecipeStepCRUD(AppCRUD):
    def create_recipeSteps(
        self, items: List[RecipeStepCreate], recipe_id: int
    ) -> List[RecipeStep]:
        objects = [RecipeStep(**item.dict(), recipeId=recipe_id) for item in items]
        self.db.add_all(objects)
        return objects
