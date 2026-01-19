from typing import Annotated
from fastapi import Depends
from sqlmodel import SQLModel, create_engine ,Session
import sqlmodel
from app.core import config
from app.models.user import User
from app.models.gym import Gym
from app.models.gym_subscription import GymSubscription
from app.models.og_plan import OGPlan
from app.models.membership import Membership
from app.models.plan import Plan
from app.models.payments import Payment
from app.models.attendance import Attendance
from app.models.announcement import Announcement
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

engine = create_engine(url=config.settings.db_connection_url)
SessionDep = Annotated[Session, Depends(get_session)]