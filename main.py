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
from app.core import config
from contextlib import asynccontextmanager
from app.db.db import create_db_and_tables
from app.schemas.response import APIResponse


@asynccontextmanager
async def on_startup(application: FastAPI):
    create_db_and_tables()
    yield


@lru_cache()
def get_settings():
    return config.settings

app = FastAPI(title=config.settings.app_name, lifespan=on_startup)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors and return standardized format
    """
    # Extract error messages from validation errors
    errors = exc.errors()
    error_messages = []
    
    for error in errors:
        # Get the field path (skip 'body' prefix for cleaner messages)
        loc = error.get("loc", [])
        field_path = [str(loc_item) for loc_item in loc if loc_item != "body"]
        field = ".".join(field_path) if field_path else "request"
        
        # Get a user-friendly error message
        msg = error.get("msg", "Validation error")
        error_type = error.get("type", "")
        
        # Format message based on error type
        if "pattern" in error_type or "string_pattern_mismatch" in error_type:
            error_messages.append(f"{field}: Invalid format")
        elif "missing" in error_type:
            error_messages.append(f"{field}: This field is required")
        elif "value_error" in error_type:
            error_messages.append(f"{field}: {msg}")
        else:
            error_messages.append(f"{field}: {msg}")
    
    # Combine all error messages
    message = "; ".join(error_messages) if error_messages else "Validation error"
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=APIResponse(
            status=False,
            message=message,
            data=errors
        ).model_dump()
    )


# Include role-based routers
app.include_router(owners_router, prefix="/api/v1")
app.include_router(members_router, prefix="/api/v1")
app.include_router(platform_admin_router, prefix="/api/v1")
app.include_router(staff_router, prefix="/api/v1")
app.include_router(trainers_router, prefix="/api/v1")

# Include shared/common routers
app.include_router(shared_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Hello World"}