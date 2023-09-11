from fastapi import FastAPI
from config.database import create_tables
from routers import recipe,search,review,login
import uvicorn
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from utils.request_exceptions import (
    http_exception_handler,
    request_validation_exception_handler,
)
from utils.app_exceptions import AppExceptionCase
from utils.app_exceptions import app_exception_handler
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()


origins = [
        '*'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, e):
    return await http_exception_handler(request, e)


@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(request, e):
    return await request_validation_exception_handler(request, e)


@app.exception_handler(AppExceptionCase)
async def custom_app_exception_handler(request, e):
    return await app_exception_handler(request, e)


create_tables()

app.include_router(recipe.router)
app.include_router(search.router)
app.include_router(review.router)
app.include_router(login.router)

@app.get("/")
def root():
    return {"message": "Hello World!"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
