from sqlalchemy.orm import Session
from models.recipe import Customize, DefaultRecipe
from schema.schemas import (
    CustomizeCreate,
    CustomizeUpdate,
    User,
    DefaultRecipeBase,
    CustomizeRecipeResponse
)
from typing import List
from .main import AppCRUD, AppService
from utils.service_result import ServiceResult
from utils.app_exceptions import AppException, AppExceptionCase
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
from service.token import redis_config
from datetime import datetime
from fastapi.encoders import jsonable_encoder
import boto3

OPENAI_KEY = os.getenv("OPENAI_KEY")

class CustomizeService(AppService):
    def __init__(self, db: Session, token:str):
        super().__init__(db)
        self.token = token

    def get_customize(self,recipeId: str):
        try:
            recipe = CustomizeCRUD(self.db,self.token).get_customize(recipeId)
            return ServiceResult(recipe)
        except Exception as e:
            return ServiceResult(e)
    
    def get_customize_recipes(self):
        try:
            recipes = CustomizeCRUD(self.db,self.token).get_customize_recipes()
            if not recipes:
                return ServiceResult(AppException.FooGetItem({"msg":"recipes not exist"}))
            return ServiceResult(recipes)
        except Exception as e:
            return ServiceResult(e)
        
    def create_customize(self,recipe:CustomizeCreate):
        new_recipe = CustomizeCRUD(self.db, self.token).create_customize(recipe)
        if not new_recipe:
            return ServiceResult(AppException.FooGetItem({"msg":"create recipe failed"}))
        self.db.commit()
        self.db.refresh(new_recipe)
        return ServiceResult(new_recipe)
    
    def update_customize(self,new_recipe:CustomizeUpdate, recipeId:str):
        try:
            recipe = CustomizeCRUD(self.db, self.token).update_customize(new_recipe,recipeId)
            self.db.commit()
            self.db.refresh(recipe)
            res = recipe.__dict__
            res["steps"] = eval(recipe.steps)
            res["ingredients"] = eval(recipe.ingredients)
            return ServiceResult(res)
        except Exception as e:
            return ServiceResult(e)
    
    def delete_customize(self,recipeId:str):
        try:
            res = CustomizeCRUD(self.db,self.token).delete_customize(recipeId)
            return ServiceResult(res)
        except Exception as e:
            return ServiceResult(e)
    
    def create_default(self,videoLink:str, backgroundTasks: BackgroundTasks):
        try:
            res = CustomizeCRUD(self.db,self.token).create_default(videoLink,backgroundTasks)
            return ServiceResult(res)
        except Exception as e:
            return ServiceResult(e)

class CustomizeCRUD(AppCRUD):
    def __init__(self, db: Session, token: str):
        super().__init__(db)
        self.rd = redis_config()
        self.token = token
        try:
            user = UserCRUD(db).get_current_user(token)
            access_key = os.getenv("ACCESS_KEY")
            access_secret = os.getenv("ACCESS_SECRET")
            client = boto3.resource("dynamodb",
                                    region_name = "ap-northeast-2",
                                    aws_access_key_id=access_key,
                                    aws_secret_access_key=access_secret)
            table = client.Table("default-recipe-table")
            if table:
                self.table = table
            else:
                raise AppException.FooGetItem({"msg":"AWS connection failed"})
            if user:
                self.user = user
            else:
                raise AppException.FooGetItem({"msg":"Invalid user"})
        except Exception as e:
            raise AppException.FooInvalidToken({"msg":"invalid token"})
        
    def get_customize(self, recipeId: str) -> CustomizeRecipeResponse:
        try:
            recipe = self.db.query(Customize).filter(Customize.id == uuid.UUID(recipeId) and Customize.deleted == False).first()
            res_dict = recipe.__dict__
            ingredient = recipe.ingredients
            step = recipe.steps
            if ingredient and step:
                res_dict["ingredients"] = eval(ingredient)
                res_dict["steps"] = eval(step)
                return res_dict
            else:
                raise AppException.FooGetItem({"msg":"This recipe is now processing"})
        except Exception as e:
            raise AppException.FooGetItem({"msg":"invalid customize recipe id"})
    
    def get_customize_recipes(self)-> List[CustomizeRecipeResponse]:
        try:
            res=[]
            recipes = self.user.recipes
            for recipe in recipes:
                if recipe.steps and recipe.ingredients and not recipe.deleted:
                    res_dict = recipe.__dict__
                    res_dict["ingredients"] = eval(recipe.ingredients)
                    res_dict["steps"] = eval(recipe.steps)
                    res.append(res_dict)
            return res
        except Exception as e:
            raise AppException.FooGetItem({"msg":"get customize recipes failed"+ str(e)})

    def update_customize(self, new_recipe: CustomizeUpdate, recipeId: str) -> CustomizeRecipeResponse:
        try:
            recipe = self.db.query(Customize).filter(Customize.id == uuid.UUID(recipeId) and Customize.deleted == False).first()
            recipe.category = new_recipe.category
            recipe.difficulty = new_recipe.difficulty
            recipe.title = new_recipe.title
            recipe.steps = str(jsonable_encoder(new_recipe.steps))
            recipe.tags = new_recipe.tags
            recipe.ingredients = str(jsonable_encoder(new_recipe.ingredients))
            return recipe
        except Exception as e:
            raise AppException.FooGetItem({"msg":"invalid recipe id"})
        
    def delete_customize(self,recipeId: str):
        try:
            recipe = self.db.query(Customize).filter(Customize.id == uuid.UUID(recipeId)).first()
            recipe.deleted = True
            self.db.commit()
            return {"msg":"recipe deleted!"}
        except:
            raise AppException.FooGetItem({"msg":"invalid recipe id"})
        
    def check_valid_url(self, sourceLink:str):
        pattern1 = r"https\:\/\/www\.youtube\.com\/watch\?v=([\d\D]+)"
        pattern2 = r"https\:\/\/youtu\.be\/(.[^\?]+)(.+)?"
        pattern3 = r"https\:\/\/www\.youtube\.com\/v\/([\d\D]+)\?[\d\D]+"
        if not re.match(pattern1,sourceLink) and not re.match(pattern2,sourceLink) and not re.match(pattern3,sourceLink):
            raise AppException.FooCreateItem({"msg":"invalid youtube link"})
        match = re.search(pattern1,sourceLink) or re.search(pattern2,sourceLink) or re.search(pattern3,sourceLink)
        sourceId = str(match.group(1))
        req_url = f"https://www.youtube.com/oembed?url=http://www.youtube.com/watch?v={sourceId}&format=json"
        res = requests.get(req_url).content.decode('utf-8')
        if res == "Bad Request":
            raise AppException.FooCreateItem({"msg":"Video with this video_id not exist"})
        res_dict = eval(res)
        res = requests.get(sourceLink).content
        print(len(res))
        return sourceId, res_dict["title"]
        
    def get_trans_by_whisper(self,videoId:str):
        try:
            yt = YouTube("https://www.youtube.com/watch?v="+videoId)
            filename = str(uuid.uuid4())+".mp4"
            yt.streams.filter(only_audio=True).first().download(output_path="./whisper",filename=filename)
            api_key = OPENAI_KEY
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
        recipe_data,tags,channel_id,descriptioin,run_time = youtube.getVideoInfoById(sourceId)
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
                                                "description": "The amount of the ingredient, e.g. 1개, 200g, 1/2스푼. Initially set to null."
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
            res = requests.post("https://api.openai.com/v1/chat/completions",json=req_json,headers={"Authorization":"Bearer "+OPENAI_KEY})
            res_json = res.json()
            arguments = res_json["choices"][0]["message"]["function_call"]["arguments"]
            dict = json.loads(arguments)
            list = dict["ingredients"]
            ingredients = []
            for i in list:
                ingredients.append({"name":i["name"], "quantity":str(i["quantity"])})
            return ingredients
        except Exception as e:
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
                                            "timestamp": {
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
            res = requests.post("https://api.openai.com/v1/chat/completions",json=req_json,headers={"Authorization":"Bearer "+OPENAI_KEY})
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
            table = self.table
            table.update_item(
                Key = {"video_id":sourceId},
                UpdateExpression = "set #status = :s, #steps = :steps, #ingredients = :ingredients",
                ExpressionAttributeValues={":s": "complete", ":steps":steps, ":ingredients":ingredients},
                ReturnValues="UPDATED_NEW",
                ExpressionAttributeNames={"#status":"status", "#steps":"steps", "#ingredients":"ingredients"}
            )
            recipes = self.db.query(Customize).filter(Customize.sourceId == sourceId and Customize.deleted == False).all()
            for recipe in recipes:
                recipe.ingredients = str(ingredients)
                recipe.steps = str(steps)
            self.db.commit()
        except Exception as e:
            print(e)

    def create_default(self,url:str,backgroundtasks:BackgroundTasks) -> CustomizeRecipeResponse:
        try:
            sourceId,videoTitle = self.check_valid_url(url)
            recipe_exist = self.db.query(Customize).filter(Customize.sourceId == sourceId, Customize.userId == self.user.id, Customize.deleted == False).first()
            if recipe_exist:
                return AppException.FooCreateItem({"msg":"Recipe with this videoId already exist"})
            
            table = self.table
            res = table.get_item(
                Key = {"video_id":sourceId}
            )
            steps = []
            ingredients = []
            cnt=0
            if "Item" in res.keys():
                item = res["Item"]
                cnt = item["count"]
                if item["status"] == "processing":
                    pass
                else:
                    steps = item["steps"]
                    ingredients = item["ingredients"]
            else:
                table.put_item(
                Item = {
                    "video_id":sourceId,
                    "status":"processing",
                    "count":0
                })
            
            table = self.table
            table.update_item(
                Key = {"video_id":sourceId},
                UpdateExpression = "set #count = :c",
                ExpressionAttributeValues={":c": cnt+1},
                ReturnValues="UPDATED_NEW",
                ExpressionAttributeNames={"#count":"count"}
            )

            user = self.user
            new_recipe = Customize(
                title = videoTitle,
                sourceId = sourceId,
                steps = str(steps),
                tags = "",
                difficulty = "",
                category = "",
                ingredients = str(ingredients),
                user = user
            )
            self.db.add(new_recipe)
            self.db.commit()
            self.db.refresh(new_recipe)
            new_res = new_recipe.__dict__
            if not steps or not ingredients:
                backgroundtasks.add_task(self.create_default_background,sourceId)
            new_res["steps"]=steps
            new_res["ingredients"]=ingredients
            return new_res
        except AppExceptionCase as e:
            raise e
        except:
            raise AppException.FooCreateItem({"msg":"create default recipe failed"})