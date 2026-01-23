from fastapi import APIRouter, status
from sqlmodel import select
from datetime import datetime
from app.core.permissions import require_any_authenticated, require_og
from app.db.db import SessionDep
from app.models.user import User
from app.models.app_info import AppInfo
from app.schemas.app_info import AppInfoResponse, AppInfoUpdate
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/app-info", tags=["app-info"])


@router.get("/", response_model=APIResponse[AppInfoResponse], status_code=status.HTTP_200_OK)
def get_app_info(
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Get app information (version and maintenance mode status) - accessible by all roles"""
    # Get the first app_info record (or default one)
    stmt = select(AppInfo).limit(1)
    app_info = session.exec(stmt).first()
    
    if not app_info:
        # Return default values if no record exists
        app_info = AppInfo(
            platform="default",
            android_app_version="1.0.0",
            ios_app_version="1.0.0",
            android_maintenance_mode=False,
            ios_maintenance_mode=False
        )
    
    app_info_response = AppInfoResponse.model_validate(app_info, from_attributes=True)
    return success_response(
        data=app_info_response,
        message="App info fetched successfully"
    )


@router.put("/", response_model=APIResponse[AppInfoResponse], status_code=status.HTTP_200_OK)
def update_app_info(
    app_info_update: AppInfoUpdate,
    session: SessionDep = None,
    current_user: User = require_og
):
    """Update app information (version and maintenance mode status) - accessible by OG role only"""
    # Get the first app_info record or create if it doesn't exist
    stmt = select(AppInfo).limit(1)
    app_info = session.exec(stmt).first()
    
    if not app_info:
        # Create new app_info record with default values
        app_info = AppInfo(
            platform="default",
            android_app_version="1.0.0",
            ios_app_version="1.0.0",
            android_maintenance_mode=False,
            ios_maintenance_mode=False
        )
        session.add(app_info)
    
    # Update only provided fields
    update_data = app_info_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(app_info, field, value)
    
    # Update the updated_at timestamp
    app_info.updated_at = datetime.now()
    
    session.commit()
    session.refresh(app_info)
    
    app_info_response = AppInfoResponse.model_validate(app_info, from_attributes=True)
    return success_response(
        data=app_info_response,
        message="App info updated successfully"
    )
