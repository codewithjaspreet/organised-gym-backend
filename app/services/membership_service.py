from sqlmodel import select
from app.core.exceptions import NotFoundError
from app.db.db import SessionDep
from app.models.membership import Membership
from app.schemas.membership import MembershipCreate, MembershipResponse, MembershipUpdate


class MembershipService:

    def __init__(self, session: SessionDep):
        self.session = session

    def create_membership(self, membership: MembershipCreate) -> MembershipResponse:
        db_membership = Membership(
            user_id=membership.user_id,
            gym_id=membership.gym_id,
            start_date=membership.start_date,
            end_date=membership.end_date,
            status=membership.status,
            plan_id=membership.plan_id,
            new_duration=membership.new_duration,
            new_price=membership.new_price
        )
        self.session.add(db_membership)
        self.session.commit()
        self.session.refresh(db_membership)

        return MembershipResponse.model_validate(db_membership.model_dump())

    def get_membership(self, membership_id: str) -> MembershipResponse:
        stmt = select(Membership).where(Membership.id == membership_id)
        membership = self.session.exec(stmt).first()
        if not membership:
            raise NotFoundError(detail=f"Membership with id {membership_id} not found")

        return MembershipResponse.model_validate(membership)

    def update_membership(self, membership_id: str, membership_update: MembershipUpdate) -> MembershipResponse:
        stmt = select(Membership).where(Membership.id == membership_id)
        membership = self.session.exec(stmt).first()
        if not membership:
            raise NotFoundError(detail=f"Membership with id {membership_id} not found")

        # Update only provided fields
        update_data = membership_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(membership, field, value)

        self.session.commit()
        self.session.refresh(membership)

        return MembershipResponse.model_validate(membership)

    def delete_membership(self, membership_id: str) -> None:
        stmt = select(Membership).where(Membership.id == membership_id)
        membership = self.session.exec(stmt).first()
        if not membership:
            raise NotFoundError(detail=f"Membership with id {membership_id} not found")

        self.session.delete(membership)
        self.session.commit()
        return None

