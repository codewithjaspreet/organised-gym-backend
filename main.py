from functools import lru_cache
from fastapi import FastAPI
from app.core import config
from contextlib import asynccontextmanager

from app.db.db import create_db_and_tables


@asynccontextmanager
async def on_startup(application: FastAPI):
    create_db_and_tables()
    yield


@lru_cache()
def get_settings():
    return config.settings

app = FastAPI(title=config.settings.app_name,lifespan=on_startup)

@app.get("/")
def root():
    return {"message": "Hello World"}