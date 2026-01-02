from fastapi import APIRouter, status, HTTPException
from app.core.permissions import require_any_authenticated
from app.db.db import SessionDep
from app.models.user import User, Role

router = APIRouter(prefix="/create", tags=["trainers"])


@router.post("/profile", status_code=status.HTTP_201_CREATED)
def create_trainer_profile(
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Create trainer profile (placeholder for future trainer-specific features)"""
    if current_user.role != Role.TRAINER:
        raise HTTPException(
            status_code=403,
            detail="Only trainers can access this endpoint"
        )
    
    return {"message": "Trainer profile creation endpoint"}

