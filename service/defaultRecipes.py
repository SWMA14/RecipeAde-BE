from sqlalchemy.orm import Session
from .main import AppCRUD, AppService
from utils.service_result import ServiceResult
from utils.app_exceptions import AppException, AppExceptionCase
import boto3
import os
from boto3.dynamodb.conditions import Key,Attr

class defaultRecipesService():
    def __init__(self):
        try:
            access_key = os.getenv("ACCESS_KEY")
            access_secret = os.getenv("ACCESS_SECRET")
            client = boto3.resource("dynamodb",
                                    region_name = "ap-northeast-2",
                                    aws_access_key_id=access_key,
                                    aws_secret_access_key=access_secret)
            table = client.Table("recipeade-test")
            self.table = table
        except:
            raise AppException.ConnectionFailed({"msg":"aws connection failed"})
    def getallRecipes(self, lang:str):
        try:
            if not lang in ("ko","en"):
                return  ServiceResult(AppException.FooGetItem({"msg":"lang parameter must be 'ko' or 'en'"}))
            res = self.table.scan(
                FilterExpression = Attr("status").eq("complete") & Attr("lang").eq(lang)
            )
            items = res["Items"]
            return ServiceResult(items)
        except:
            raise AppException.ConnectionFailed({"msg":"dynamodb connection failed"})