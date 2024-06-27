from typing import List, Optional
from pydantic import BaseModel, root_validator, Field
from datetime import datetime
from uuid import uuid4, UUID


class TagBase(BaseModel):
    tagName: str


class TagCreate(TagBase):
    pass

class TagResponse(TagBase):
    pass 

class Tag(TagBase):
    recipeId: int
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
    #ChannelThumbnail: str


class ChannelCreate(ChannelBase):
    allowed: Optional[bool] = False

class ChannelResponse(ChannelBase):
    id:int

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

class RecipeStepResponse(RecipeStepBase):
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
    quantity: Optional[str] = None
    unit: Optional[str] = None


class IngredientCreate(IngredientBase):
    pass


class IngredientResponse(IngredientBase):
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
    youtubeViewCount: int
    difficulty: Optional[int] = None
    category: Optional[str] = None
    youtubeThumbnail: str

class RecipeResponse(RecipeBase):
    id: int
    rating: float
    ingredients: List[IngredientResponse]
    recipesteps: List[RecipeStepResponse]
    channel:ChannelResponse


class RecipeCreate(RecipeBase):
    youtubePublishedAt: str
    youtubeLikeCount: int
    youtubeChannel: str


class Recipe(RecipeBase):
    id: int
    deleted: bool
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    ingredients: List[Ingredient]
    recipesteps: List[RecipeStep]
    tags: List[Tag]
    rating: float
    youtubeChannel: str

    class Config:
        orm_mode = True
        validate_assignment = True

    
class ReviewBase(BaseModel):
    author: int
    content: str

class ReviewCreate(ReviewBase):
    pass

class ReviewResponse(ReviewBase):
    id: int
    recipeId: int

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
    fileName: str

class ReviewImage(ReviewImageCreate):
    id: int
    deleted: bool
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    class Config:
        orm_mode = True
        validate_assignment = True

class RecipeResponseDetail(RecipeResponse):
    reviews:List[Review]

class UserBase(BaseModel):
    password: str
    email: str
    

class UserSignin(UserBase):
    name: str

class UserSignUp(UserSignin):
    gender: str
    age: str

class User(UserSignUp):
    id: UUID
    deleted: bool
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    class Config:
        orm_mode = True
        validate_assignment = True

class token(BaseModel):
    token_type:str
    token:str

class customizeSteps(BaseModel):
    step: str
    timestamp: str

class CustomizeBase(BaseModel):
    title: str
    steps: List[customizeSteps]
    ingredients: List[IngredientCreate]
    tags: str
    difficulty: str
    category: str

class CustomizeCreate(CustomizeBase):
    sourceId: str

class CustomizeUpdate(CustomizeBase):
    pass

class CustomizeRecipe(CustomizeBase):
    userId: UUID
    sourceId: str

class CustomizeRecipeResponse(CustomizeBase):
    sourceId: str
    id: UUID

class DefaultRecipeBase(BaseModel):
    steps: str
    ingredients: str
    videoId: str

class DefaultRecipe(DefaultRecipeBase):
    id: UUID
    deleted: bool
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

class dynamoDbRecipe(BaseModel):
    steps: List[customizeSteps]
    ingredients: List[IngredientCreate]
    count: int
    video_id: str
    status: str

class dynamoResponse(BaseModel):
    recipes: List[dynamoDbRecipe]