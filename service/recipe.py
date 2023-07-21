from models.recipe import Recipe, Ingredient, RecipeStep, Channel, Tag
from schema.schemas import (
    RecipeCreate,
    IngredientCreate,
    RecipeStepCreate,
    ChannelCreate,
    TagCreate,
    RecipeResponse,
)
from typing import List
from .main import AppCRUD, AppService
from utils.service_result import ServiceResult
from utils.app_exceptions import AppException
from .youtubeAPI import YoutubeAPI
from sqlalchemy import or_,desc

class RecipeService(AppService):
    def create_recipe(
        self,
        item: RecipeCreate,
        ingredient_items: List[IngredientCreate],
        recipeStep_items: List[RecipeStepCreate],
        channelID: str,
    ) -> ServiceResult:
        recipe = RecipeCRUD(self.db).create_recipe(
            item=item,
            ingredient_items=ingredient_items,
            recipeStep_items=recipeStep_items,
            channelID=channelID,
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

    def create_channel(self, channel_item: ChannelCreate) -> ServiceResult:
        channel = ChannelCRUD(self.db).create_channel(channel_item)
        if not channel:
            return ServiceResult(AppException.FooCreateItem())
        return ServiceResult(channel)

    def get_channel(self, channel_id: int) -> ServiceResult:
        channel = ChannelCRUD(self.db).get_channel_by_id(channel_id)
        if not channel:
            return ServiceResult(AppException.FooGetItem({"channel_id": channel_id}))
        return ServiceResult(channel)


class RecipeCRUD(AppCRUD):
    def create_recipe(
        self,
        item: RecipeCreate,
        ingredient_items: List[IngredientCreate],
        recipeStep_items: List[RecipeStepCreate],
        channelID: str,
    ) -> Recipe:
        # channel = ChannelCRUD(self.db).get_channel_by_channelId(channelID)
        # if channel:
        #     channelid = channel.id
        # else:
        #     youtube = YoutubeAPI()
        #     channel_obj = ChannelCRUD(self.db).create_channel(
        #         youtube.get_channelInfo(channelID)
        #     )
        #     channel = ChannelCRUD(self.db).create_channel(channel_obj)
        #     self.db.flush()
        #     channelid = channel.id
        recipe = Recipe(**item.dict())
        self.db.add(recipe)
        self.db.flush()
        tags = TagCRUD(self.db).create_tags(
            [TagCreate(tagName="reciped", recipeId=recipe.id)]
        )
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

    def update_ingredient(
        self,
        ingredient_id: int,
        newIngredient: IngredientCreate,
    ) -> Ingredient:
        ingredient = self.db.query(Ingredient).filter(Ingredient.id == ingredient_id)
        ingredient = newIngredient
        self.db.commit()
        return ingredient


class RecipeStepCRUD(AppCRUD):
    def create_recipeSteps(
        self, items: List[RecipeStepCreate], recipe_id: int
    ) -> List[RecipeStep]:
        objects = [RecipeStep(**item.dict(), recipeId=recipe_id) for item in items]
        self.db.add_all(objects)
        return objects

    def update_recipeStep(
        self, recipeStep_id: int, newRecipeStep: RecipeStepCreate
    ) -> RecipeStep:
        recipeStep = self.db.query(RecipeStep).filter(RecipeStep.id == recipeStep_id)
        recipeStep = newRecipeStep
        self.db.commit()
        return recipeStep


class ChannelCRUD(AppCRUD):
    def get_channel_by_id(self, channel_id: int) -> Channel:
        channel = self.db.query(Channel).filter(Channel.id == channel_id).first()
        if channel:
            return channel
        return None

    def get_channel_by_channelId(self, youtubeChannelId: str) -> Channel:
        channel = (
            self.db.query(Channel).filter(Channel.channelID == youtubeChannelId).first()
        )
        if channel:
            return channel
        return None

    def create_channel(self, channel_item: ChannelCreate) -> Channel:
        channel = Channel(**channel_item.dict())
        self.db.add(channel)
        self.db.commit()
        self.db.refresh(channel)
        return channel


class TagCRUD(AppCRUD):
    def create_tags(self, tag_items: List[TagCreate]) -> List[Tag]:
        tags = [Tag(**tag.dict()) for tag in tag_items]
        self.db.add_all(tags)
        return tags

    def get_tags(self, tag_name: str) -> List[Tag]:
        tags = self.db.query(Tag).filter(Tag.tagName.like(tag_name))
        return tags

class SearchTest(AppService):
    def searchTest(self,keyword,category, diff, sort):
        query = self.db.query(Recipe)
        searchtitle = "%{}%".format(keyword)
        searchChannel = "%{}%".format(keyword)
        searchTag = "%{}%".format(keyword)
        tags = self.db.query(Tag).filter(Tag.tagName.like(searchTag)).all()
        recipeIds = [tag.recipeId for tag in tags]
        query = query.filter(or_(Recipe.youtubeTitle.like(searchtitle), Recipe.youtubeChannel.like(searchChannel), Recipe.id.in_(recipeIds)))
        if category:
            query = query.filter(Recipe.category == category)
        if diff:
            query = query.filter(Recipe.difficulty == diff)
        if sort:
            if sort == "rating":
                query = query.order_by(desc(Recipe.rating))
            elif sort == "current":
                query = query.order_by(desc(Recipe.youtubePublishedAt))
            else:
                query = query.order_by(desc(Recipe.youtubeViewCount))
        recipes = query.all()
        return recipes