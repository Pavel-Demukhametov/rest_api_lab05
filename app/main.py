from fastapi import FastAPI
from app.config import setup_database
from app.api.routes import router as api_router
from app.api.auth import router as auth_router

app = FastAPI()

setup_database()

app.include_router(auth_router, prefix="")

app.include_router(api_router)