from fastapi import APIRouter, status, Depends
from sqlmodel import select
from app.core.permissions import require_any_authenticated, check_gym_ownership
from app.db.db import SessionDep
from app.models.user import User, Role
from app.models.membership import Membership
from app.schemas.membership import MembershipCreate, MembershipResponse, MembershipUpdate
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.membership_service import MembershipService
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/memberships", tags=["memberships"])

@router.post("/", response_model=APIResponse[MembershipResponse], status_code=status.HTTP_201_CREATED)
def create_membership(
    membership: MembershipCreate,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    # Only gym owner (ADMIN) can create memberships for their gym
    # Or members can create their own membership
    if current_user.role == Role.ADMIN:
        check_gym_ownership(membership.gym_id, current_user, session)
    elif membership.user_id != current_user.id:
        return failure_response(
            message="You can only create memberships for yourself",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    try:
        membership_service = MembershipService(session=session)
        membership_data = membership_service.create_membership(membership)
        return success_response(data=membership_data, message="Membership created successfully")
    except Exception as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "Failed to create membership",
            status_code=status.HTTP_400_BAD_REQUEST
        )

@router.get("/{membership_id}", response_model=APIResponse[MembershipResponse])
def get_membership(
    membership_id: str,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    # Check if user owns membership or is gym admin
    stmt = select(Membership).where(Membership.id == membership_id)
    db_membership = session.exec(stmt).first()
    if not db_membership:
        return failure_response(
            message="Membership not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if current_user.role == Role.ADMIN:
        check_gym_ownership(db_membership.gym_id, current_user, session)
    elif db_membership.user_id != current_user.id:
        return failure_response(
            message="You can only access your own memberships",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    try:
        membership_service = MembershipService(session=session)
        membership_data = membership_service.get_membership(membership_id)
        return success_response(data=membership_data, message="Membership fetched successfully")
    except NotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "Membership not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

@router.put("/{membership_id}", response_model=APIResponse[MembershipResponse])
def update_membership(
    membership_id: str,
    membership: MembershipUpdate,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    # Only gym owner (ADMIN) can update memberships
    stmt = select(Membership).where(Membership.id == membership_id)
    db_membership = session.exec(stmt).first()
    if not db_membership:
        return failure_response(
            message="Membership not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    check_gym_ownership(db_membership.gym_id, current_user, session)
    
    try:
        membership_service = MembershipService(session=session)
        updated_membership = membership_service.update_membership(membership_id, membership)
        return success_response(data=updated_membership, message="Membership updated successfully")
    except NotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "Membership not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

@router.delete("/{membership_id}", response_model=APIResponse[dict])
def delete_membership(
    membership_id: str,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    # Only gym owner (ADMIN) can delete memberships
    stmt = select(Membership).where(Membership.id == membership_id)
    db_membership = session.exec(stmt).first()
    if not db_membership:
        return failure_response(
            message="Membership not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    check_gym_ownership(db_membership.gym_id, current_user, session)
    
    try:
        membership_service = MembershipService(session=session)
        membership_service.delete_membership(membership_id)
        return success_response(data=None, message="Membership deleted successfully")
    except NotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "Membership not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

