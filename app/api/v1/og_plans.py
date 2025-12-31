from fastapi import APIRouter, status, Depends
from app.core.permissions import require_og
from app.db.db import SessionDep
from app.models.user import User
from app.schemas.og_plan import OGPlanCreate, OGPlanResponse, OGPlanUpdate
from app.services.og_plan_service import OGPlanService

router = APIRouter(prefix="/og-plans", tags=["og-plans"])

@router.post("/", response_model=OGPlanResponse, status_code=status.HTTP_201_CREATED)
def create_og_plan(
    og_plan: OGPlanCreate,
    session: SessionDep,
    current_user: User = require_og
):
    og_plan_service = OGPlanService(session=session)
    return og_plan_service.create_og_plan(og_plan)

@router.get("/{og_plan_id}", response_model=OGPlanResponse)
def get_og_plan(
    og_plan_id: str,
    session: SessionDep,
    current_user: User = require_og
):
    og_plan_service = OGPlanService(session=session)
    return og_plan_service.get_og_plan(og_plan_id)

@router.put("/{og_plan_id}", response_model=OGPlanResponse)
def update_og_plan(
    og_plan_id: str,
    og_plan: OGPlanUpdate,
    session: SessionDep,
    current_user: User = require_og
):
    og_plan_service = OGPlanService(session=session)
    return og_plan_service.update_og_plan(og_plan_id, og_plan)

@router.delete("/{og_plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_og_plan(
    og_plan_id: str,
    session: SessionDep,
    current_user: User = require_og
):
    og_plan_service = OGPlanService(session=session)
    return og_plan_service.delete_og_plan(og_plan_id)

