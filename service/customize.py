from sqlalchemy.orm import Session
from models.recipe import Customize, DefaultRecipe
from schema.schemas import (
    CustomizeCreate,
    CustomizeUpdate,
    User,
    DefaultRecipeBase
)
from typing import List
from .main import AppCRUD, AppService
from utils.service_result import ServiceResult
from utils.app_exceptions import AppException
from service.user import UserCRUD
from fastapi import Depends, BackgroundTasks
from sqlalchemy import or_,desc
from config.database import get_db
import uuid
from youtube_transcript_api import YouTubeTranscriptApi
import requests
from service.youtubeAPI import YoutubeAPI
import re
import json
from pytube import YouTube
import openai
import os

class CustomizeService(AppService):
    def __init__(self, db: Session, token:str):
        super().__init__(db)
        self.token = token

    def get_customize(self,recipeId: str):
        recipe = CustomizeCRUD(self.db,self.token).get_customize(recipeId)
        if not recipe:
            return ServiceResult(AppException.FooGetItem({"msg":"customize recipe not exist"}))
        return ServiceResult(recipe)
    
    def get_customize_recipes(self):
        recipes = CustomizeCRUD(self.db,self.token).get_customize_recipes()
        if not recipes:
            return ServiceResult(AppException.FooGetItem({"msg":"customize recipes not exist"}))
        return ServiceResult(recipes)
        
    def create_customize(self,recipe:CustomizeCreate):
        new_recipe = CustomizeCRUD(self.db, self.token).create_customize(recipe)
        if not new_recipe:
            return ServiceResult(AppException.FooGetItem({"msg":"create recipe failed"}))
        return ServiceResult(new_recipe)
    
    def update_customize(self,new_recipe:CustomizeUpdate, recipeId:str):
        recipe = CustomizeCRUD(self.db, self.token).update_customize(new_recipe,recipeId)
        return ServiceResult(recipe)
    
    def delete_customize(self,recipeId:str):
        res = CustomizeCRUD(self.db,self.token).delete_customize(recipeId)
        return ServiceResult(res)

class CustomizeCRUD(AppCRUD):
    def __init__(self, db: Session, token: str):
        super().__init__(db)
        #self.token = token
        # try:
        #     self.user = UserCRUD(db).get_current_user(token)
        # except:
        #     raise AppException.FooInvalidToken({"msg":"invalid token"})
        
    def get_customize(self, recipeId: str):
        try:
            recipe = self.db.query(Customize).filter(Customize.id == uuid.UUID(recipeId)).first()
        except:
            raise AppException.FooGetItem({"msg":"invalid customize recipe id form"})
        return recipe
    
    def get_customize_recipes(self):
        recipes = self.user.recipes
        return recipes

    def create_customize(self, recipe: CustomizeCreate):
        user:User = self.user
        new_recipe = Customize(**recipe.dict())
        user.recipes.append(new_recipe)
        self.db.commit()
        self.db.refresh(new_recipe)
        return new_recipe

    def update_customize(self, new_recipe: CustomizeUpdate, recipeId: str):
        try:
            recipe = self.db.query(Customize).filter(Customize.id == uuid.UUID(recipeId)).first()
            recipe.category = new_recipe.category
            recipe.difficulty = new_recipe.difficulty
            recipe.title = new_recipe.title
            recipe.steps = new_recipe.steps
            recipe.tags = new_recipe.tags
            self.db.commit()
            self.db.refresh(recipe)
            return recipe
        except Exception as e:
            raise AppException.FooGetItem({"msg":"invalid recipe id"})
        
    def delete_customize(self,recipeId: str):
        try:
            recipe = self.db.query(Customize).filter(Customize.id == uuid.UUID(recipeId)).first()
            recipe.deleted = True
            return {"msg":"recipe deleted!"}
        except:
            raise AppException.FooGetItem({"msg":"invalid recipe id"})
        
    def check_valid_url(self, sourceLink:str):
        pattern1 = r"https\:\/\/www\.youtube\.com\/watch\?v=([\d\D]+)"
        pattern2 = r"https\:\/\/youtu\.be\/(.+)\?[\d\D]+"
        if not re.match(pattern1,sourceLink) and not re.match(pattern2,sourceLink):
            raise AppException.FooCreateItem({"msg":"invalid youtube link"})
        match = re.search(pattern1,sourceLink) or re.search(pattern2,sourceLink)
        sourceId = str(match.group(1))
        return sourceId
        
    def get_trans_by_whisper(self,videoId:str):
        try:
            yt = YouTube("https://www.youtube.com/watch?v="+videoId)
            filename = str(uuid.uuid4())+".mp4"
            yt.streams.filter(only_audio=True).first().download(output_path="./whisper",filename=filename)
            api_key = "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"
            audio = open("./whisper/"+filename,"rb")
            openai.api_key = api_key
            trans = openai.Audio.transcribe("whisper-1",audio,response_format="text")
            os.remove("./whisper/"+filename)
            return trans
        except:
            raise AppException.FooCreateItem({"msg":"get whisper failed"})

    def get_trans_by_youtube(self,videoId):
        try:
            srt = YouTubeTranscriptApi.get_transcript(videoId,languages=['en'])
            input_text=""
            for i in srt:
                time_step = f'({i["start"]}) {i["text"]}, '
                input_text+=time_step
            return input_text
        except:
            raise AppException.FooCreateItem({"msg":"get transcript failed"})
    
    def get_ingredient_by_subscription(self,sourceId):
        youtube = YoutubeAPI()
        recipe_data,tags,channel_id,descriptioin = youtube.getVideoInfoById(sourceId)
        res = str(descriptioin).split("\n")
        ingredients=[]
        stack=[]
        flag=0
        for i in range(len(res)):
            if not flag:
                if "재료" in res[i] and len(res[i])<7:
                    flag=1
                continue
            if res[i] != "":
                if ord(res[i][0]) == 32 and ord(res[i][-1]) == 32:
                    ingredients.extend(stack)
                    stack=[]
                    flag=0
                    continue
                stack.append(res[i])
            else:
                if len(stack):
                    ingredients.extend(stack)
                    stack=[]
                    flag=0
                else:
                    continue
        print(ingredients)
    
    def get_ingredient_by_script(self,script):
        try:
            req_json = {
                "model": "gpt-4-0613",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an ingredient extractor for a recipe video. User will give you description and transcript of it, and you must extract all ingredients from them. You must try your very best to find exact amount of ingredients. Be sure to must capture the unit of them too which often appears right after the ingredient name. Your output need to be Korean."
                    },
                    {
                        "role": "user",
                        "content": "Descriptoin: (설명)\n\nTranscript: "+script
                    }
                ],
                "functions": [
                    {
                        "name": "get_ingredients",
                        "description": "Get ingredients from the given description and transcript of the recipe video in Korean form",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "ingredients": {
                                    "type": "array",
                                    "description": "An array of Korean strings containing the all ingredients in the recipe video with exact amount, e.g. ['깻잎 4장', '새우 3마리', '간장 1TSP', '설탕 300g', '당근 반 개']",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {
                                                "type": "string",
                                                "description": "The name of the ingredient, e.g. '깻잎', '새우', '간장', '설탕', '당근'. Quantity or unit should never be contained in the name. This need to be Korean."
                                            },
                                            "quantity": {
                                                "type": "null",
                                                "description": "The amount of the ingredient, e.g. 1, 200, 1/2. Initially set to null."
                                            },
                                            "unit": {
                                                "type": "null",
                                                "description": "The unit of the ingredient, e.g. tsp, tbsp, g, kg, 개, 마리. Initially set to null. This need to be Korean."
                                            }
                                        }
                                    }
                                }
                            },
                            "required": ["ingredients"]
                        }
                    }
                ]
            }
            res = requests.post("https://api.openai.com/v1/chat/completions",json=req_json,headers={"Authorization":"Bearer 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"})
            res_json = res.json()
            arguments = res_json["choices"][0]["message"]["function_call"]["arguments"]
            dict = json.loads(arguments)
            list = dict["ingredients"]
            ingredients = {}
            for i in list:
                ingredients[i["name"]] = str(i["quantity"]) + str(i["unit"])
            return ingredients
        except Exception as e:
            print(e)
            raise AppException.FooCreateItem({"msg":"get ingredient failed"})
    
    def get_steps_by_script(self,script):
        try:
            req_json = {
                "model": "gpt-4-0613",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an video summarize service for a recipe video. User will give you transcript and start time of each text, and you must summarize the video. You must try get result each timestamp and step. Your output need to be Korean."
                    },
                    {
                        "role": "user",
                        "content": script
                    }
                ],
                "functions": [
                    {
                        "name": "summarize",
                        "description": "summarize the content of the recipe video with step and timestamp in Korean form",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "steps": {
                                    "type": "array",
                                    "description": "An array of Korean strings containing the all steps in the recipe video with exact amount, e.g. ['깻잎 4장', '새우 3마리', '간장 1TSP', '설탕 300g', '당근 반 개']",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "step": {
                                                "type": "string",
                                                "description": "Summarized step for recipe video, Every steps should include the ingredient of recipe and the way to cook. The output should be korean and should not include the time of each step"
                                            },
                                            "time": {
                                                "type": "string",
                                                "description": "The timestamp for each step and only get minute and second, e.g. 1:20, 98:30"
                                            }
                                        }
                                    }
                                }
                            },
                            "required": ["stpes"]
                        }
                    }
                ]
            }
            res = requests.post("https://api.openai.com/v1/chat/completions",json=req_json,headers={"Authorization":"Bearer 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"})
            res_json = res.json()
            arguments = res_json["choices"][0]["message"]["function_call"]["arguments"]
            dict = json.loads(arguments)
            return dict
        except Exception as e:
            print(e)
            raise AppException.FooCreateItem({"msg":"get steps failed"})
    
    def sub_exist(self, videoId):
        transcript_list = YouTubeTranscriptApi.list_transcripts(videoId)
        if 'en' in transcript_list._manually_created_transcripts:
            trans = transcript_list.find_manually_created_transcript(['en'])
            return trans
        
    def find_exist_default(self,videoId):
        default = self.db.query(DefaultRecipe).filter(DefaultRecipe.videoId == videoId).first()
        if default:
            ingredient_res = eval(default.ingredients)
            steps_res = eval(default.steps)
            return {
                "ingredient":ingredient_res,
                "steps":steps_res
            }
    def create_default_background(self,sourceId:str):
        try:
            if self.sub_exist(sourceId):
                print("yt sub")
                script = self.get_trans_by_youtube(sourceId)
            else:
                print("whisper sub")
                script = self.get_trans_by_whisper(sourceId)
            ingredients = self.get_ingredient_by_script(script)
            steps = self.get_steps_by_script(script)["steps"]
            new_default_recipe = DefaultRecipe(
                steps = str(steps),
                ingredients = str(ingredients),
                videoId = sourceId
            )
            self.db.add(new_default_recipe)
            self.db.commit()
        except Exception as e:
            print(e)

    def create_default(self,url:str,backgroudtasks:BackgroundTasks):
        try:
            sourceId = self.check_valid_url(url)
            defaultRecipe = self.find_exist_default(sourceId)
            if defaultRecipe:
                return {
                    "ingredient":defaultRecipe["ingredient"],
                    "steps":defaultRecipe["steps"]
                }
            
            backgroudtasks.add_task(self.create_default_background,sourceId)
            return {
                "msg":"process started"
            }
        except Exception as e:
            print(e)
            raise AppException.FooCreateItem({"msg":"default recipe create failed"})