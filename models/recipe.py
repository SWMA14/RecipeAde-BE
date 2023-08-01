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
    rating = Column(Float, default=0)
    difficulty = Column(String(20), default="")
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
