from typing import List
from datetime import datetime
import random
import string

from sqlmodel import select
from app.core.exceptions import AlreadyExistsError, NotFoundError
from app.db.db import SessionDep
from app.models.gym import Gym
from app.models.gym_rule import GymRule
from app.schemas.gym import GymCreate, GymResponse, GymUpdate
from app.schemas.gym_rule import GymRuleCreate, GymRuleUpdate, GymRuleResponse, GymRuleListResponse


class GymService:

    def __init__(self , session: SessionDep):
        self.session = session


    def create_gym(self, gym: GymCreate) -> GymResponse:
        # Generate unique 6-letter gym code
        gym_code = self._generate_gym_code()
        
        db_gym = Gym(
            owner_id=gym.owner_id,
            name=gym.name,
            logo=gym.logo,
            address_line1=gym.address_line1,
            address_line2=gym.address_line2,
            city=gym.city,
            state=gym.state,
            postal_code=gym.postal_code,
            country=gym.country,
            dob=gym.dob,
            opening_hours=gym.opening_hours,
            is_active=gym.is_active,
            gym_code=gym_code
        )
        self.session.add(db_gym)
        self.session.commit()
        self.session.refresh(db_gym)

        return GymResponse.model_validate(db_gym.model_dump())
    
    def _generate_gym_code(self) -> str:
        """Generate a unique 6-letter coupon-type code"""
        while True:
            # Generate 6 random uppercase letters
            code = ''.join(random.choices(string.ascii_uppercase, k=6))
            
            # Check if code already exists
            stmt = select(Gym).where(Gym.gym_code == code)
            existing = self.session.exec(stmt).first()
            
            if not existing:
                return code
        
        

    def get_gym(self, gym_id: str) -> GymResponse:
        stmt = select(Gym).where(Gym.id == gym_id)
        gym = self.session.exec(stmt).first()
        if not gym:
            raise NotFoundError(
                detail=f"Gym with id {gym_id} not found"
            )

        return GymResponse.model_validate(gym)

    def update_gym(self, gym_id: str, gym_update: GymUpdate) -> GymResponse:
        stmt = select(Gym).where(Gym.id == gym_id)
        db_gym = self.session.exec(stmt).first()
        if not db_gym:
            raise NotFoundError(
                detail=f"Gym with id {gym_id} not found"
            )

        # Update only provided fields
        update_data = gym_update.model_dump(exclude_unset=True, exclude={"id"})
        for field, value in update_data.items():
            setattr(db_gym, field, value)

        self.session.commit()
        self.session.refresh(db_gym)

        return GymResponse.model_validate(db_gym.model_dump())

    def delete_gym(self , gym_id:str) -> None:
       # find gym by id
       stmt = select(Gym).where(Gym.id == gym_id)
       gym = self.session.exec(stmt).first()
       if not gym:
           raise NotFoundError(
               detail=f"Gym with id {gym_id} not found"
           )

       self.session.delete(gym)
       self.session.commit()

       return None

    # Gym Rules Methods
    def create_gym_rule(self, rule: GymRuleCreate) -> GymRuleResponse:
        """Create a new gym rule"""
        db_rule = GymRule(
            gym_id=rule.gym_id,
            title=rule.title,
            description=rule.description
        )
        self.session.add(db_rule)
        self.session.commit()
        self.session.refresh(db_rule)
        
        return GymRuleResponse.model_validate(db_rule.model_dump())

    def get_all_gym_rules(self, gym_id: str) -> GymRuleListResponse:
        """Get all rules for a gym"""
        stmt = select(GymRule).where(GymRule.gym_id == gym_id)
        stmt = stmt.order_by(GymRule.created_at.desc())
        
        rules = self.session.exec(stmt).all()
        rule_responses = [
            GymRuleResponse.model_validate(rule.model_dump())
            for rule in rules
        ]
        
        return GymRuleListResponse(rules=rule_responses)

    def get_gym_rule(self, rule_id: str) -> GymRuleResponse:
        """Get a single gym rule by ID"""
        stmt = select(GymRule).where(GymRule.id == rule_id)
        rule = self.session.exec(stmt).first()
        if not rule:
            raise NotFoundError(detail=f"Gym rule with id {rule_id} not found")
        
        return GymRuleResponse.model_validate(rule.model_dump())

    def update_gym_rule(self, rule_id: str, rule_update: GymRuleUpdate) -> GymRuleResponse:
        """Update a gym rule"""
        stmt = select(GymRule).where(GymRule.id == rule_id)
        db_rule = self.session.exec(stmt).first()
        if not db_rule:
            raise NotFoundError(detail=f"Gym rule with id {rule_id} not found")
        
        update_data = rule_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_rule, field, value)
        
        db_rule.updated_at = datetime.now()
        
        self.session.commit()
        self.session.refresh(db_rule)
        
        return GymRuleResponse.model_validate(db_rule.model_dump())

    def delete_gym_rule(self, rule_id: str) -> None:
        """Delete a gym rule"""
        stmt = select(GymRule).where(GymRule.id == rule_id)
        rule = self.session.exec(stmt).first()
        if not rule:
            raise NotFoundError(detail=f"Gym rule with id {rule_id} not found")
        
        self.session.delete(rule)
        self.session.commit()
        return None

   
        
    