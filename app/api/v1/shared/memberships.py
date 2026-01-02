from fastapi import APIRouter, status, HTTPException, Depends
from sqlmodel import select
from app.core.permissions import require_any_authenticated, check_gym_ownership
from app.db.db import SessionDep
from app.models.user import User, Role
from app.models.membership import Membership
from app.schemas.membership import MembershipCreate, MembershipResponse, MembershipUpdate
from app.services.membership_service import MembershipService

router = APIRouter(prefix="/memberships", tags=["memberships"])

@router.post("/", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED)
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create memberships for yourself"
        )
    
    membership_service = MembershipService(session=session)
    return membership_service.create_membership(membership)

@router.get("/{membership_id}", response_model=MembershipResponse)
def get_membership(
    membership_id: str,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    # Check if user owns membership or is gym admin
    stmt = select(Membership).where(Membership.id == membership_id)
    db_membership = session.exec(stmt).first()
    if not db_membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    
    if current_user.role == Role.ADMIN:
        check_gym_ownership(db_membership.gym_id, current_user, session)
    elif db_membership.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own memberships"
        )
    
    membership_service = MembershipService(session=session)
    return membership_service.get_membership(membership_id)

@router.put("/{membership_id}", response_model=MembershipResponse)
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
        raise HTTPException(status_code=404, detail="Membership not found")
    
    check_gym_ownership(db_membership.gym_id, current_user, session)
    
    membership_service = MembershipService(session=session)
    return membership_service.update_membership(membership_id, membership)

@router.delete("/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_membership(
    membership_id: str,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    # Only gym owner (ADMIN) can delete memberships
    stmt = select(Membership).where(Membership.id == membership_id)
    db_membership = session.exec(stmt).first()
    if not db_membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    
    check_gym_ownership(db_membership.gym_id, current_user, session)
    
    membership_service = MembershipService(session=session)
    return membership_service.delete_membership(membership_id)

