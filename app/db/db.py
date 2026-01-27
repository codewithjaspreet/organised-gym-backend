# from typing import Annotated
# from fastapi import Depends
# from sqlmodel import SQLModel, Session, create_engine
# import boto3
# import os
# from sqlalchemy.engine import Engine


# from app.models.user import User
# from app.models.gym import Gym
# from app.models.gym_subscription import GymSubscription
# from app.models.og_plan import OGPlan
# from app.models.membership import Membership
# from app.models.plan import Plan
# from app.models.payments import Payment
# from app.models.attendance import Attendance
# from app.models.announcement import Announcement
# from app.models.permission import Permission
# from app.models.role import Role
# from app.models.role_permission import RolePermission


# def generate_iam_auth_token() -> str:
#     rds = boto3.client(
#         "rds",
#         region_name=os.environ["AWS_REGION"]
#     )
#     return rds.generate_db_auth_token(
#         DBHostname=os.environ["DB_HOST"],
#         Port=int(os.environ["DB_PORT"]),
#         DBUsername=os.environ["DB_USER"]
#     )


# def get_engine() -> Engine:
#     token = generate_iam_auth_token()

#     database_url = (
#         f"postgresql+psycopg2://{os.environ['DB_USER']}:"
#         f"{token}@"
#         f"{os.environ['DB_HOST']}:"
#         f"{os.environ['DB_PORT']}/"
#         f"{os.environ['DB_NAME']}?sslmode=require"
#     )

#     return create_engine(
#         database_url,
#         pool_pre_ping=True,
#         pool_recycle=300,  
#     )

# engine = get_engine()



# def get_session():
#     with Session(engine) as session:
#         yield session

# SessionDep = Annotated[Session, Depends(get_session)]



# def create_db_and_tables():
#     SQLModel.metadata.create_all(engine)
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