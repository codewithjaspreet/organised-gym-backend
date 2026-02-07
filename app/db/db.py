from typing import Annotated
from fastapi import Depends
from sqlmodel import SQLModel, Session, create_engine
import boto3
import sys
from sqlalchemy.engine import Engine

from app.core.config import settings
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
from app.models.password_reset_token import PasswordResetToken


_engine: Engine | None = None


def _generate_iam_token() -> str:
    rds = boto3.client("rds", region_name=settings.aws_region)

    return rds.generate_db_auth_token(
        DBHostname=settings.db_host,
        Port=settings.db_port,
        DBUsername=settings.db_user,
    )


def _build_database_url() -> str:
    # Check if password is provided (for testing/fallback)
    password = settings.db_password
    
    if password:
        print("🔑 Using password authentication", file=sys.stderr)

        print(f"postgresql+psycopg2://{settings.db_user}:"
            f"{password}@"
            f"{settings.db_host}:"
            f"{settings.db_port}/"
            f"{settings.db_name}" ) 
        

        # return f'postgresql+psycopg2://postgres:>Zz6WGoOiBi2RFg9Cud3>7!y:jjh@localhost:5432/postgres'
        return (
            f"postgresql+psycopg2://{settings.db_user}:"
            f"{password}@"
            f"{settings.db_host}:"
            f"{settings.db_port}/"
            f"{settings.db_name}"
        )

        

    print("🔑 Using IAM authentication", file=sys.stderr)
    token = _generate_iam_token()
    print(f"✅ IAM token generated (length: {len(token)})", file=sys.stderr)
    return (
        f"postgresql+psycopg2://{settings.db_user}:"
        f"{token}@"
        f"{settings.db_host}:"
        f"{settings.db_port}/"
        f"{settings.db_name}"
        f"?sslmode=require"
    )


def get_engine() -> Engine:
    global _engine

    if _engine is None:
        print("🚀 Creating database engine...", file=sys.stderr)
        _engine = create_engine(
            _build_database_url(),
            pool_pre_ping=True,
            pool_recycle=840,  # < 15 min IAM token expiry
            echo=False,
        )
        print("✅ Database engine created successfully", file=sys.stderr)

    return _engine


def get_session():
    engine = get_engine()
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def create_db_and_tables():
    """
    Run ONLY from local / bastion / CI
    Do NOT call from App Runner startup
    """
    print("📊 Creating database tables...", file=sys.stderr)
    try:
        engine = create_engine(_build_database_url(), pool_pre_ping=True)
        SQLModel.metadata.create_all(engine)
        engine.dispose()
        print("✅ Tables created successfully", file=sys.stderr)
    except Exception as e:
        print(f"❌ Failed to create tables: {e}", file=sys.stderr)