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
from utils.Enums import Lang,Platform
from boto3.dynamodb.conditions import Attr

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
    
    def create_default(self,videoLink:str, backgroundTasks: BackgroundTasks, lang:str):
        try:
            res = CustomizeCRUD(self.db,self.token).create_default(videoLink,backgroundTasks,lang)
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
            table = client.Table("recipeade-test")
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
        return sourceId, res_dict["title"]
    
    def get_desc_from_youtube(self,videoId:str):
        yt = YouTube(f"https://www.youtube.com/watch?v={videoId}")
        stream = yt.streams.first()
        description = yt.description
        return description
        
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
    
    def get_ingredient_by_script(self,script,title, description, recipe, lang):
        try:
            prompt = '''You are an recipe ingredients extractor. You will be given recipe steps, transcript, description and title of a YouTube recipe video which is the origin of the recipe, each delimited in XML tags. Your task is to extract complete list of all the used ingredients and their exact amount.
            <recipe>
            {recipe}
            </recipe>
            <title>
            {title}
            </title>
            <description>
            {description}
            </description>
            <transcript>
            {script}
            </transcript>
            ### Guidelines:
            - Capture every ingredients and their amount. Amount can be mentioned directly in numbers, or expressed in verbal ways.
            - In the final list, every ingredient need to present only once.
            - Consider yourself as a viewer that is following the recipe, and think of what ingredients are crucial to your cooking process.
            - Description may have exact amount of ingredients. If so, actively reference them to minimize the error.
            ### Instructions:
            - Take a deep breath and work on the problem step-by-step, by following these steps:
            1. Repeat this task 5 times: Look into every information you are given and identify 1-3 ingredients you haven't found and extracted yet.
            - Must extract ingredients that are essential in the recipe. Think about how much impact could be on the recipe result if a specific ingredient is added or skipped.
            2. Try to find amounts of ingredients you identified. Be aware that some ingredients do not have mention of amount.
            3. Organize all of your works into a list.
            Answer in JSON, following this schema:
            [
            {{
                "name": string; // write in {lang}
                "amount": string | ""; // write in {lang}, and if there's no mention of amount, just write "".
            }},
            {{
                ...
            }},
            ...
            ]'''.replace("{lang}", "Korean" if lang == "ko" else "English") \
                .replace("{description}", description) \
                .replace("{title}", title) \
                .replace("{script}", script) \
                .replace("{recipe}", str(recipe))

            data = {
                "model": "gpt-4-1106-preview",
                "messages": [
                    {
                        "role": "system",
                        "content": prompt
                    }
                ]
            }
            response = requests.post("https://api.openai.com/v1/chat/completions", json=data, headers={"Authorization": f"Bearer {OPENAI_KEY}"}).json()
            content = re.search(r"\[.+\]", response["choices"][0]["message"]["content"], flags=re.S).group()
            entries = json.loads(content)
            ingredients = []

            for entry in entries:
                ingredients.append({
                    "name": entry["name"],
                    "quantity": entry["amount"]
                })

            return ingredients
        
        except Exception as e:
            print(e)
            raise AppException.FooCreateItem({"msg":"get ingredient failed"+str(e)})
    
    def get_steps_by_script(self,script,title,description,lang):
        try:
            examples = ["  - 팬에 식용유 2스푼을 두르고 썰어둔 다진 마늘과 다진 양파를 볶습니다.", "  - 양념에 소고기를 잘 버무려 두 시간 정도 재워줍니다.", "  - 올리고당이 없다면 물엿 3스푼으로 대체해도 괜찮습니다."] if lang == "ko" else ["  - Cook until vegetables are softened.", "  - Roast the vegetables in the preheated oven for 20-25 minutes.", "  - Stuff each bell pepper half with the quinoa mixture, pressing down gently."]
            prompt = '''You are a transcript-to-recipe converter. You will be given transcript, description and title of a YouTube recipe video, each delimited in XML tags. Your task is to convert given information into easy-to-follow and seamless recipe, while capturing all the cooking-crucial information.
            <title>
            {title}
            </title>
            <description>
            {description}
            </description>
            <transcript>
            {script}
            </transcript>
            ### Considerations:
            - Analyse all the recipe books, cuisine magazines or articles you have, and try to imitate the tones from them. Examples:
            {examples}
            - There are no limits in count of steps, but try to avoid making steps unnecessarilly too much.
            - Title may have correct form of the ingredients or useful information. If so, actively reference them to minimize the error.
            ### Guidelines:
            - Exclude unnecessary lines completely from your task, e.g., video introduction, final words, chatters.
            - Reflect about your descriptions and find mistakes you made, e.g., incorrect grammar, false information. Improve the description by rectifying identified mistakes.
            - Consider yourself as a master of cooking, and think of what will help the viewers to successfully complete the dish.
            ### Instructions:
            - Take a deep breath and work on the problem step-by-step, by following these instructions:
            1. Chronologically retrieve the whole transcript and cluster into recipe steps by grouping similar and close-located lines.
            - Each line of transcript is constructed in this way: `({{start timestamp of this line}}) {{transcribed text}}`.
            2. Write a new instructing, easy-to-follow description for each clustered step with 1-2 sentences.
            - Never miss critical information that can affect the result, e.g., the speaker's tip.
            - Description may have exact amount of ingredients or full list of recipe steps. If so, actively reference them to minimize the error.
            - Find the start timestamp of each step in the transcript. Timestamps must be in the transcript.
            - BAN: NEVER ADD CONTENTS THAT DO NOT PRESENT IN THE GIVEN INFORMATION, even when they are helpful. This action would only add more confusion to the user, which is severely againsts 'easy-to-follow and seamingless' duty of you.
            Answer in JSON, following this schema:
            [
            {{
                "startTimestamp": string; // need to be only one timestamp
                "description": string; // write in {lang}
                "flaws": string; // always write in English
                "improvedDescription": string; // write in {lang}
            }},
            {{
                ...
            }},
            ...
            ]'''.replace("{lang}", "Korean" if lang == "ko" else "English") \
                .replace("{examples}", "\n".join(examples)) \
                .replace("{description}", description) \
                .replace("{title}", title) \
                .replace("{script}", script)

            data = {
                "model": "gpt-4-1106-preview",
                "messages": [
                    {
                        "role": "system",
                        "content": prompt
                    }
                ]
            }
            response = requests.post("https://api.openai.com/v1/chat/completions", json=data, headers={"Authorization": f"Bearer {OPENAI_KEY}"}).json()
            content = re.search(r"\[.+\]", response["choices"][0]["message"]["content"], flags=re.S).group()
            entries = json.loads(content)
            steps = []
            
            for entry in entries:
                steps.append({
                    "step": entry["improvedDescription"],
                    "timestamp": entry["startTimestamp"]
                })

            return steps
        except Exception as e:
            print(e)
            raise AppException.FooCreateItem({"msg":"get steps failed"})
    
    def sub_exist(self, videoId):
        transcript_list = YouTubeTranscriptApi.list_transcripts(videoId)
        if 'en' in transcript_list._manually_created_transcripts:
            trans = transcript_list.find_manually_created_transcript(['en'])
            return trans

    def create_default_background(self,sourceId:str,title:str, lang:str):
        try:
            print(lang)
            if self.sub_exist(sourceId):
                print("yt sub")
                script = self.get_trans_by_youtube(sourceId)
            else:
                print("whisper sub")
                script = self.get_trans_by_whisper(sourceId)
            desc = self.get_desc_from_youtube(sourceId)
            steps = self.get_steps_by_script(script,title,desc, lang)
            ingredients = self.get_ingredient_by_script(script, title, desc, steps, lang)
            table = self.table
            table.update_item(
                Key = {"video_id":sourceId, "lang":lang},
                UpdateExpression = "set #status = :s, #steps = :steps, #ingredients = :ingredients",
                ExpressionAttributeValues={":s": "complete", ":steps":steps, ":ingredients":ingredients},
                ReturnValues="UPDATED_NEW",
                ExpressionAttributeNames={"#status":"status", "#steps":"steps", "#ingredients":"ingredients"}
            )
            recipes = self.db.query(Customize).filter(Customize.sourceId == sourceId and Customize.deleted == False and Customize.language == lang).all()
            for recipe in recipes:
                recipe.ingredients = str(ingredients)
                recipe.steps = str(steps)
            self.db.commit()
        except Exception as e:
            print(e)

    def create_default(self,url:str,backgroundtasks:BackgroundTasks, lang: str) -> CustomizeRecipeResponse:
        try:
            if lang not in ("ko","en"):
                raise AppException.FooCreateItem({"msg":"lang parameter must be 'ko' or 'en'"})
            sourceId,videoTitle = self.check_valid_url(url)
            recipe_exist = self.db.query(Customize).filter(Customize.sourceId == sourceId, Customize.userId == self.user.id, Customize.deleted == False, Customize.language == lang).first()
            if recipe_exist:
                return AppException.FooCreateItem({"msg":"Recipe with this videoId already exist"})
            
            table = self.table
            res = table.get_item(
                Key={"video_id":sourceId, "lang":lang}
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
                    "count":0,
                    "lang":lang
                })
            
            table = self.table
            table.update_item(
                Key = {"video_id":sourceId, "lang":lang},
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
                language = lang,
                user = user
            )
            self.db.add(new_recipe)
            self.db.commit()
            self.db.refresh(new_recipe)
            new_res = new_recipe.__dict__
            if not steps or not ingredients:
                backgroundtasks.add_task(self.create_default_background,sourceId,videoTitle, lang)
            new_res["steps"]=steps
            new_res["ingredients"]=ingredients
            return new_res
        except AppExceptionCase as e:
            raise e
        except Exception as e:
            raise AppException.FooCreateItem({"msg":"create default recipe failed"+str(e)})