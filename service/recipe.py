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
    def delete_recipe(self,recipe_id):
        RecipeCRUD(self.db).delete_recipe(recipe_id)

    def create_recipe(
        self,
        item: RecipeCreate,
        ingredient_items: List[IngredientCreate],
        recipeStep_items: List[RecipeStepCreate],
        tags: List[TagCreate]
    ) -> ServiceResult:
        recipe = RecipeCRUD(self.db).create_recipe(
            item=item,
            ingredient_items=ingredient_items,
            recipeStep_items=recipeStep_items,
            channelID=item.youtubeChannel,
            tags=tags
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
    def insert_data(self, videoId, thumbnail, title, viewCount, channelname, publishedAt, channelID,
                    ingredients : List[IngredientCreate],
                    recipeSteps : List[RecipeStepCreate]) -> Recipe:
        # youtube = YoutubeAPI()
        # channelID = youtube.findChannelId(channelname)
        # channel = ChannelCRUD(self.db).get_channel_by_channelId(channelID)
        if not channel:
            newChannel = ChannelCRUD(self.db).create_channel(ChannelCreate(ChannelName=channelname, channelID = channelID))
            self.db.commit()
            channel = newChannel
        recipe = Recipe(youtubeVideoId = videoId, 
                        channel=channel,
                        youtubeTitle = title,
                        youtubeViewCount = viewCount,
                        youtubePublishedAt = publishedAt,
                        youtubeThumbnail = thumbnail
                        )
        self.db.add(recipe)
        self.db.flush()
        # tags = youtube.getTagById(videoId)
        # TagCRUD(self.db).create_tags(
        #     tags, recipe.id
        # )
        IngredientCRUD(self.db).create_ingredients(
            ingredients, recipe.id
        )
        RecipeStepCRUD(self.db).create_recipeSteps(
            recipeSteps, recipe.id
        )
        self.db.commit()
        self.db.refresh(recipe)
        return recipe

    def delete_recipe(self, recipe_id: int):
        recipe = self.db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if recipe:
            recipe.deleted = True
        self.db.commit()

    def create_recipe(
        self,
        item: RecipeCreate,
        ingredient_items: List[IngredientCreate],
        recipeStep_items: List[RecipeStepCreate],
        channelID: str,
        tags: List[TagCreate]
    ) -> Recipe: # 외래 키 제약조건 위배 -> 레시피 입력 시 채널 추가까지 
        channel = ChannelCRUD(self.db).get_channel_by_channelId(channelID)
        if not channel:
            newChannel = ChannelCRUD(self.db).create_channel(ChannelCreate(channelID==channelID, ChannelName="none"))
            self.db.commit()
            channel = newChannel
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
        recipe = Recipe(**item.dict(), channel=channel)
        self.db.add(recipe)
        self.db.flush()
        TagCRUD(self.db).create_tags(
            tags, recipe.id
        )
        IngredientCRUD(self.db).create_ingredients(
            ingredient_items, recipe.id
        )
        RecipeStepCRUD(self.db).create_recipeSteps(
            recipeStep_items, recipe.id
        )
        self.db.commit()
        self.db.refresh(recipe)
        return recipe

    def get_recipe(self, recipe_id: int) -> Recipe:
        recipe = self.db.query(Recipe).filter(Recipe.id == recipe_id, Recipe.deleted == False).first()
        if recipe:
            return recipe
        return None

    def get_recipes(self) -> List[Recipe]:
        recipe = self.db.query(Recipe).filter(Recipe.deleted == False).all()
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
    def create_tags(self, tag_items: List[TagCreate], recipe:int) -> List[Tag]:
        tags = [Tag(**tag.dict(), recipeId = recipe) for tag in tag_items]
        self.db.add_all(tags)
        return tags

    def get_tags(self, tag_name: str) -> List[Tag]:
        tags = self.db.query(Tag).filter(Tag.tagName.like(tag_name))
        return tags