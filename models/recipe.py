from sqlalchemy import (
    Integer,
    String,
    Column,
    Boolean,
    DateTime,
    ForeignKey,
    Float,
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

    youtubeVideoId = Column(String)
    youtubeTitle = Column(String)
    youtubeViewCount = Column(Integer)
    youtubeChannel = Column(Integer, ForeignKey("channels.id"))
    youtubePublishedAt = Column(String)
    youtubeLikeCount = Column(Integer)
    rating = Column(Float, default=0)
    difficulty = Column(String, default="")
    category = Column(String, default="")

    ingredients = relationship("Ingredient", back_populates="recipe")
    recipesteps = relationship("RecipeStep", back_populates="recipe")
    channels = relationship("Channel", back_populates="recipe")
    tags = relationship("Tag", back_populates="recipe")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    name = Column(String)
    quantity = Column(Integer)
    unit = Column(String)
    recipeId = Column(Integer, ForeignKey("recipes.id"))

    recipe = relationship("Recipe", back_populates="ingredients")


class RecipeStep(Base):
    __tablename__ = "recipesteps"

    id = Column(Integer, primary_key=True, index=True)
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    description = Column(String)
    timestamp = Column(String)
    recipeId = Column(Integer, ForeignKey("recipes.id"))

    recipe = relationship("Recipe", back_populates="recipesteps")


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    channelID = Column(String)
    ChannelName = Column(String)
    ChannelThumbnail = Column(String)
    allowed = Column(Boolean, default=False)

    recipe = relationship("Recipe", back_populates="channels")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    recipeId = Column(Integer, ForeignKey("recipes.id"))
    tagName = Column(String, index=True)

    recipe = relationship("Recipe", back_populates="tags")
