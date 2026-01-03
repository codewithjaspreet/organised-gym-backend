from fastapi import APIRouter, status, HTTPException, Depends
from sqlmodel import select
from app.core.permissions import require_any_authenticated, check_gym_ownership
from app.db.db import SessionDep
from app.models.user import User
from app.models.plan import Plan
from app.schemas.plan import PlanCreate, PlanResponse, PlanUpdate
from app.schemas.response import APIResponse
from app.utils.response import success_response
from app.services.plan_service import PlanService

router = APIRouter(prefix="/plans", tags=["plans"])

@router.post("/", response_model=APIResponse[PlanResponse], status_code=status.HTTP_201_CREATED)
def create_plan(
    plan: PlanCreate,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    # Only gym owner (ADMIN) can create plans for their gym
    check_gym_ownership(plan.gym_id, current_user, session)
    plan_service = PlanService(session=session)
    plan_data = plan_service.create_plan(plan)
    return success_response(data=plan_data, message="Plan created successfully")

@router.get("/{plan_id}", response_model=APIResponse[PlanResponse])
def get_plan(
    plan_id: str,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    plan_service = PlanService(session=session)
    plan_data = plan_service.get_plan(plan_id)
    return success_response(data=plan_data, message="Plan fetched successfully")

@router.put("/{plan_id}", response_model=APIResponse[PlanResponse])
def update_plan(
    plan_id: str,
    plan: PlanUpdate,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    # Check gym ownership through plan
    stmt = select(Plan).where(Plan.id == plan_id)
    db_plan = session.exec(stmt).first()
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    check_gym_ownership(db_plan.gym_id, current_user, session)
    
    plan_service = PlanService(session=session)
    updated_plan = plan_service.update_plan(plan_id, plan)
    return success_response(data=updated_plan, message="Plan updated successfully")

@router.delete("/{plan_id}", response_model=APIResponse[dict])
def delete_plan(
    plan_id: str,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    # Check gym ownership through plan
    stmt = select(Plan).where(Plan.id == plan_id)
    db_plan = session.exec(stmt).first()
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    check_gym_ownership(db_plan.gym_id, current_user, session)
    
    plan_service = PlanService(session=session)
    plan_service.delete_plan(plan_id)
    return success_response(data=None, message="Plan deleted successfully")

