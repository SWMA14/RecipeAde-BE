from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"
SQLALCHEMY_DATABASE_URL_TEST = "sqlite:///./test.db"
#SQLALCHEMY_DATABASE_URL = "mysql+pymysql://admin:test1234@recipeade-db.crvjttygkv2r.ap-northeast-2.rds.amazonaws.com/recipeAde"

# connect_args 는 sqlite에서만 필요함
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

engines = {
    "maindb" : create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    ),
    "testdb" : create_engine(
        SQLALCHEMY_DATABASE_URL_TEST, connect_args={"check_same_thread": False}
    )
}

SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind = engines["maindb"])
TestSessionLocal = sessionmaker(autocommit=False, autoflush=True, bind = engines["testdb"])

Base = declarative_base()


def get_db(): # 메인 db
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_test_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engines["maindb"])
    Base.metadata.create_all(bind=engines["testdb"])