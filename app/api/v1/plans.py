from fastapi import APIRouter, status, Depends
from sqlmodel import select
from app.core.permissions import require_any_authenticated, check_gym_ownership
from app.db.db import SessionDep
from app.models.user import User
from app.models.plan import Plan
from app.schemas.plan import PlanCreate, PlanResponse, PlanUpdate
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.plan_service import PlanService
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/plans", tags=["plans"])

@router.post("/", response_model=APIResponse[PlanResponse], status_code=status.HTTP_201_CREATED)
def create_plan(
    plan: PlanCreate,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    # Only gym owner (ADMIN) can create plans for their gym
    check_gym_ownership(plan.gym_id, current_user, session)
    try:
        plan_service = PlanService(session=session)
        plan_data = plan_service.create_plan(plan)
        return success_response(data=plan_data, message="Plan created successfully")
    except Exception as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "Failed to create plan",
            status_code=status.HTTP_400_BAD_REQUEST
        )

@router.get("/{plan_id}", response_model=APIResponse[PlanResponse])
def get_plan(
    plan_id: str,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    try:
        plan_service = PlanService(session=session)
        plan_data = plan_service.get_plan(plan_id)
        return success_response(data=plan_data, message="Plan fetched successfully")
    except NotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "Plan not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

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
        return failure_response(
            message="Plan not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    check_gym_ownership(db_plan.gym_id, current_user, session)
    
    try:
        plan_service = PlanService(session=session)
        updated_plan = plan_service.update_plan(plan_id, plan)
        return success_response(data=updated_plan, message="Plan updated successfully")
    except NotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "Plan not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

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
        return failure_response(
            message="Plan not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    check_gym_ownership(db_plan.gym_id, current_user, session)
    
    try:
        plan_service = PlanService(session=session)
        plan_service.delete_plan(plan_id)
        return success_response(data=None, message="Plan deleted successfully")
    except NotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "Plan not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

