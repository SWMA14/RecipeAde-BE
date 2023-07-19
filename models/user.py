from sqlalchemy import (
    Integer,
    String,
    Column,
    Boolean,
    DateTime,
)
from datetime import datetime
from config.database import Base

class User(Base):
    __tablename__="users"

    id = Column(Integer, primary_key=True, index=True)
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    uid = Column(String, unique=True)
    password = Column(String)
    nickname = Column(String, unique=True)