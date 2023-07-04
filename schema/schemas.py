from typing import List
from pydantic import BaseModel, root_validator
from datetime import datetime


class RecipeStepBase(BaseModel):
    description: str
    timestamp: str


class RecipeStepCreate(RecipeStepBase):
    pass


class RecipeStep(RecipeStepBase):
    id: int
    deleted: bool
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    recipeId: int

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
    pass


class Ingredient(IngredientBase):
    id: int
    deleted: bool
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    recipeId: int

    class Config:
        orm_mode = True
        validate_assignment = True

    @root_validator
    def number_validator(cls, values):
        values["updated_at"] = datetime.now()
        return values


class RecipeBase(BaseModel):
    youtubeVideoId: str
    youtubeTitle: str
    youtubeChannel: str
    youtubeViewCount: int
    difficulty: str
    category: str


class RecipeResponse(RecipeBase):
    pass


class RecipeCreate(RecipeBase):
    youtubePublishedAt: str
    youtubeLikeCount: int
    youtubeTag: str
    youtubeDescription: str
    youtubeCaption: str


class Recipe(RecipeBase):
    id: int
    deleted: bool
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    ingredients: List[Ingredient]
    recipesteps: List[RecipeStep]
    rating: float

    class Config:
        orm_mode = True
        validate_assignment = True

    @root_validator
    def number_validator(cls, values):
        values["updated_at"] = datetime.now()
        return values
