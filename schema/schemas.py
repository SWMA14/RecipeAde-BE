from typing import List
from pydantic import BaseModel, root_validator
from datetime import datetime


class RecipeStepBase(BaseModel):
    description: str
    timestamp: str


class RecipeStepCreate(RecipeStepBase):
    recipeId: int
    pass


class RecipeStep(RecipeStepBase):
    id: int
    deleted: bool
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    class Config:
        orm_mode = True
        validate_assignment = True

    @root_validator
    def number_validator(cls, values):
        values["updated_at"] = datetime.now()
        return values


class IngredientBase(BaseModel):
    name: str
    quantity: int
    unit: str


class IngredientCreate(IngredientBase):
    recipeId: int
    pass


class Ingredient(IngredientBase):
    id: int
    deleted: bool
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    class Config:
        orm_mode = True
        validate_assignment = True

    @root_validator
    def number_validator(cls, values):
        values["updated_at"] = datetime.now()
        return values


class RecipeBase(BaseModel):
    youtubeThumnail: str
    youtubeTitle: str
    youtubeChannel: str
    youtubeViewCount: int
    youtubePublishedAt: str
    youtubeLikeCount: int
    youtubeTag: str
    youtubeDescription: str
    youtubeCaption: str
    rating: float
    difficulty: str
    category: str


class RecipeCreate(RecipeBase):
    pass


class Recipe(RecipeBase):
    id: int
    deleted: bool
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    ingredients: List[Ingredient]
    recipesteps: List[RecipeStep]

    class Config:
        orm_mode = True
        validate_assignment = True

    @root_validator
    def number_validator(cls, values):
        values["updated_at"] = datetime.now()
        return values
