from functools import lru_cache
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.api.v1.owners import router as owners_router
from app.api.v1.members import router as members_router
from app.api.v1.platform_admin import router as platform_admin_router
from app.api.v1.staff import router as staff_router
from app.api.v1.trainers import router as trainers_router
from app.api.v1.shared import router as shared_router
from app.api.v1.users import router as users_router
from app.core import config
from contextlib import asynccontextmanager
from app.db.db import create_db_and_tables
from app.schemas.response import APIResponse
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def on_startup(application: FastAPI):
    create_db_and_tables()
    yield


@lru_cache()
def get_settings():
    return config.settings
origins=["*"]

app = FastAPI(title=config.settings.app_name, lifespan=on_startup)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include role-based routers
app.include_router(owners_router, prefix="/api/v1")
app.include_router(members_router, prefix="/api/v1")
app.include_router(platform_admin_router, prefix="/api/v1")
app.include_router(staff_router, prefix="/api/v1")
app.include_router(trainers_router, prefix="/api/v1")

# Include shared/common routers
app.include_router(shared_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Hello World"}