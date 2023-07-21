from typing import List, Optional
from pydantic import BaseModel, root_validator
from datetime import datetime


class TagBase(BaseModel):
    tagName: str


class TagCreate(TagBase):
    recipeId: int


class Tag(TagBase):
    id: int
    deleted: bool
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    class Config:
        orm_mode = True
        validate_assignment = True



class ChannelBase(BaseModel):
    channelID: str
    ChannelName: str
    ChannelThumbnail: str


class ChannelCreate(ChannelBase):
    allowed: Optional[bool] = False
    pass


class Channel(ChannelBase):
    id: int
    deleted: bool
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    class Config:
        orm_mode = True
        validate_assignment = True




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



class RecipeBase(BaseModel):
    youtubeVideoId: str
    youtubeTitle: str
    youtubeChannel: Optional[str] = None
    youtubeViewCount: int
    difficulty: Optional[str] = None
    category: Optional[str] = None


class RecipeResponse(RecipeBase):
    pass


class RecipeCreate(RecipeBase):
    youtubePublishedAt: str
    youtubeLikeCount: int


class Recipe(RecipeBase):
    id: int
    deleted: bool
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    ingredients: List[Ingredient]
    recipesteps: List[RecipeStep]
    tags: List[Tag]
    # channels: Channel
    rating: float

    class Config:
        orm_mode = True
        validate_assignment = True

    
class ReviewBase(BaseModel):
    author: int
    content: str

class ReviewCreate(ReviewBase):
    pass

class Review(ReviewBase):
    id: int
    deleted: bool
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    recipeId: int

    class Config:
        orm_mode = True
        validate_assignment = True

class ReviewImageCreate(BaseModel):
    reviewId: int
    image: str

class ReviewImage(ReviewImageCreate):
    id: int
    deleted: bool
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    class Config:
        orm_mode = True
        validate_assignment = True