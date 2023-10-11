from sqlalchemy import (
    Integer,
    String,
    Column,
    Boolean,
    DateTime,
    ForeignKey,
    Float,
    Text
)
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base
from sqlalchemy.types import Uuid
from uuid import uuid4

class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    youtubeVideoId = Column(String(30))
    youtubeTitle = Column(String(30))
    youtubeViewCount = Column(Integer)
    youtubeChannel = Column(String(50), ForeignKey("channels.channelID"))
    youtubePublishedAt = Column(String(30))
    youtubeLikeCount = Column(Integer)
    youtubeThumbnail = Column(Text)
    rating = Column(Float, default=0)
    difficulty = Column(Integer)
    category = Column(String(20), default="")

    ingredients = relationship("Ingredient", back_populates="recipe")
    recipesteps = relationship("RecipeStep", back_populates="recipe")
    channel = relationship("Channel", back_populates="recipes")
    tags = relationship("Tag", back_populates="recipe")
    reviews = relationship("Review",back_populates="recipe")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    name = Column(String(20))
    quantity = Column(String(20))
    unit = Column(String(20))
    recipeId = Column(Integer, ForeignKey("recipes.id"))

    recipe = relationship("Recipe", back_populates="ingredients")


class RecipeStep(Base):
    __tablename__ = "recipesteps"

    id = Column(Integer, primary_key=True, index=True)
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    description = Column(Text)
    timestamp = Column(String(20))
    recipeId = Column(Integer, ForeignKey("recipes.id"))

    recipe = relationship("Recipe", back_populates="recipesteps")


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    channelID = Column(String(50), unique=True)
    ChannelName = Column(String(50))
    ChannelThumbnail = Column(Text, default="")
    allowed = Column(Boolean, default=False)

    recipes = relationship("Recipe", back_populates="channel")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    recipeId = Column(Integer, ForeignKey("recipes.id"))
    tagName = Column(String(20), index=True)

    recipe = relationship("Recipe", back_populates="tags")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    recipeId = Column(Integer,ForeignKey("recipes.id"))
    author = Column(Integer)
    content = Column(Text)

    recipe = relationship("Recipe", back_populates="reviews")
    reviewImages = relationship("ReviewImage",back_populates="review")

class ReviewImage(Base):
    __tablename__ = "reviewImages"

    id = Column(Integer, primary_key=True)
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    reviewId = Column(Integer,ForeignKey("reviews.id"))
    image = Column(Text)
    fileName = Column(String(50))

    review = relationship("Review",back_populates="reviewImages")

class User(Base):
    __tablename__ = "users"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    name = Column(String(30))
    email = Column(String(50))
    password = Column(String(100))
    age = Column(String(10))
    gender = Column(String(10))

    recipes = relationship("Customize",back_populates="user")

class Customize(Base):
    __tablename__ = "customize"
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    title = Column(String(50))
    sourceId = Column(String(30))
    steps = Column(Text)
    tags = Column(Text)
    difficulty = Column(String(10))
    category = Column(String(20))
    ingredients = Column(Text)

    userId = Column(Uuid(as_uuid=True),ForeignKey("users.id"))

    user = relationship("User",back_populates="recipes")

class DefaultRecipe(Base):
    __tablename__ = "defaultRecipe"
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    videoId = Column(String(50))
    steps = Column(Text)
    ingredients = Column(Text)