from typing import List

from sqlmodel import select
from app.core.exceptions import AlreadyExistsError, NotFoundError
from app.db.db import SessionDep
from app.models.gym import Gym
from app.schemas.gym import GymCreate, GymResponse, GymUpdate


class GymService:

    def __init__(self , session: SessionDep):
        self.session = session


    def create_gym(self, gym: GymCreate) -> GymResponse:
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
            is_active=gym.is_active
        )
        self.session.add(db_gym)
        self.session.commit()
        self.session.refresh(db_gym)

        return GymResponse.model_validate(db_gym)
        
        

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

        return GymResponse.model_validate(db_gym)

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

   
        
    