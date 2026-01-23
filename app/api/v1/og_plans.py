from fastapi import APIRouter, status, Depends
from app.core.permissions import require_og
from app.db.db import SessionDep
from app.models.user import User
from app.schemas.og_plan import OGPlanCreate, OGPlanResponse, OGPlanUpdate, OGPlanListResponse
from app.schemas.response import APIResponse
from app.utils.response import success_response
from app.services.og_plan_service import OGPlanService

router = APIRouter(prefix="/og-plans", tags=["og-plans"])

@router.post("/", response_model=APIResponse[OGPlanResponse], status_code=status.HTTP_201_CREATED)
def create_og_plan(
    og_plan: OGPlanCreate,
    session: SessionDep,
    current_user: User = require_og
):
    og_plan_service = OGPlanService(session=session)
    og_plan_data = og_plan_service.create_og_plan(og_plan)
    return success_response(data=og_plan_data, message="OG plan created successfully")

@router.get("/", response_model=APIResponse[OGPlanListResponse])
def get_all_og_plans(
    session: SessionDep,
    current_user: User = require_og
):
    """Get all OG plans"""
    og_plan_service = OGPlanService(session=session)
    og_plans_data = og_plan_service.get_all_og_plans()
    return success_response(data=og_plans_data, message="OG plans fetched successfully")

@router.get("/{og_plan_id}", response_model=APIResponse[OGPlanResponse])
def get_og_plan(
    og_plan_id: str,
    session: SessionDep,
    current_user: User = require_og
):
    og_plan_service = OGPlanService(session=session)
    og_plan_data = og_plan_service.get_og_plan(og_plan_id)
    return success_response(data=og_plan_data, message="OG plan fetched successfully")

@router.put("/{og_plan_id}", response_model=APIResponse[OGPlanResponse])
def update_og_plan(
    og_plan_id: str,
    og_plan: OGPlanUpdate,
    session: SessionDep,
    current_user: User = require_og
):
    og_plan_service = OGPlanService(session=session)
    updated_og_plan = og_plan_service.update_og_plan(og_plan_id, og_plan)
    return success_response(data=updated_og_plan, message="OG plan updated successfully")

@router.delete("/{og_plan_id}", response_model=APIResponse[dict])
def delete_og_plan(
    og_plan_id: str,
    session: SessionDep,
    current_user: User = require_og
):
    og_plan_service = OGPlanService(session=session)
    og_plan_service.delete_og_plan(og_plan_id)
    return success_response(data=None, message="OG plan deleted successfully")

