from sqlmodel import select
from app.core.exceptions import NotFoundError
from app.db.db import SessionDep
from app.models.og_plan import OGPlan
from app.schemas.og_plan import OGPlanCreate, OGPlanResponse, OGPlanUpdate, OGPlanListResponse


class OGPlanService:

    def __init__(self, session: SessionDep):
        self.session = session

    def create_og_plan(self, og_plan: OGPlanCreate) -> OGPlanResponse:
        db_og_plan = OGPlan(
            name=og_plan.name,
            price=og_plan.price,
            billing_cycle=og_plan.billing_cycle,
            max_members=og_plan.max_members,
            max_staff=og_plan.max_staff,
            features=og_plan.features if og_plan.features is not None else None,
            is_active=og_plan.is_active
        )
        self.session.add(db_og_plan)
        self.session.commit()
        self.session.refresh(db_og_plan)

        return OGPlanResponse.model_validate(db_og_plan, from_attributes=True)

    def get_og_plan(self, og_plan_id: str) -> OGPlanResponse:
        stmt = select(OGPlan).where(OGPlan.id == og_plan_id)
        og_plan = self.session.exec(stmt).first()
        if not og_plan:
            raise NotFoundError(detail=f"OG Plan with id {og_plan_id} not found")

        return OGPlanResponse.model_validate(og_plan)

    def update_og_plan(self, og_plan_id: str, og_plan_update: OGPlanUpdate) -> OGPlanResponse:
        stmt = select(OGPlan).where(OGPlan.id == og_plan_id)
        og_plan = self.session.exec(stmt).first()
        if not og_plan:
            raise NotFoundError(detail=f"OG Plan with id {og_plan_id} not found")

        # Update only provided fields
        update_data = og_plan_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(og_plan, field, value)

        self.session.commit()
        self.session.refresh(og_plan)

        return OGPlanResponse.model_validate(og_plan)

    def delete_og_plan(self, og_plan_id: str) -> None:
        stmt = select(OGPlan).where(OGPlan.id == og_plan_id)
        og_plan = self.session.exec(stmt).first()
        if not og_plan:
            raise NotFoundError(detail=f"OG Plan with id {og_plan_id} not found")

        self.session.delete(og_plan)
        self.session.commit()
        return None

    def get_all_og_plans(self) -> OGPlanListResponse:
        """Get all OG plans"""
        stmt = select(OGPlan).order_by(OGPlan.created_at.desc())
        og_plans = self.session.exec(stmt).all()
        
        og_plan_responses = [
            OGPlanResponse.model_validate(og_plan, from_attributes=True)
            for og_plan in og_plans
        ]
        
        return OGPlanListResponse(og_plans=og_plan_responses)

