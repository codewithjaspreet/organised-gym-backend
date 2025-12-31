from sqlmodel import select
from app.core.exceptions import NotFoundError
from app.db.db import SessionDep
from app.models.plan import Plan
from app.schemas.plan import PlanCreate, PlanResponse, PlanUpdate


class PlanService:

    def __init__(self, session: SessionDep):
        self.session = session

    def create_plan(self, plan: PlanCreate) -> PlanResponse:
        db_plan = Plan(
            gym_id=plan.gym_id,
            name=plan.name,
            duration_days=plan.duration_days,
            price=plan.price,
            description=plan.description,
            is_active=plan.is_active
        )
        self.session.add(db_plan)
        self.session.commit()
        self.session.refresh(db_plan)

        return PlanResponse.model_validate(db_plan)

    def get_plan(self, plan_id: str) -> PlanResponse:
        stmt = select(Plan).where(Plan.id == plan_id)
        plan = self.session.exec(stmt).first()
        if not plan:
            raise NotFoundError(detail=f"Plan with id {plan_id} not found")

        return PlanResponse.model_validate(plan)

    def update_plan(self, plan_id: str, plan_update: PlanUpdate) -> PlanResponse:
        stmt = select(Plan).where(Plan.id == plan_id)
        plan = self.session.exec(stmt).first()
        if not plan:
            raise NotFoundError(detail=f"Plan with id {plan_id} not found")

        # Update only provided fields
        update_data = plan_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(plan, field, value)

        self.session.commit()
        self.session.refresh(plan)

        return PlanResponse.model_validate(plan)

    def delete_plan(self, plan_id: str) -> None:
        stmt = select(Plan).where(Plan.id == plan_id)
        plan = self.session.exec(stmt).first()
        if not plan:
            raise NotFoundError(detail=f"Plan with id {plan_id} not found")

        self.session.delete(plan)
        self.session.commit()
        return None

