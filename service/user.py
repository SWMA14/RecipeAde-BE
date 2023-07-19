from .main import AppCRUD, AppService
from models.user import User
from typing import List
from utils.service_result import ServiceResult
from utils.app_exceptions import AppException

class UserCRUD(AppCRUD):
    def get_user(self, uid: int):
        user = self.db.query(User).filter(User.uid == uid)
        if user:
            return user
        return None
    
class UserService(AppService):
    def get_user(self, uid: int):
        user = UserCRUD(self.db).get_user(uid)
        if not user:
            return ServiceResult(AppException.FooGetItem({"user":None}))
        return user