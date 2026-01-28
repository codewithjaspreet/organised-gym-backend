from logging.config import fileConfig
import sys
import os
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context
from sqlmodel import SQLModel

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Import settings and database URL builder
from app.core.config import settings

# Import models so Alembic sees them
from app.models.user import User
from app.models.gym import Gym
from app.models.role import Role
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.membership import Membership
from app.models.plan import Plan
from app.models.payments import Payment
from app.models.attendance import Attendance
from app.models.announcement import Announcement
from app.models.og_plan import OGPlan
from app.models.gym_subscription import GymSubscription
from app.models.password_reset_token import PasswordResetToken

# Alembic config
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata
target_metadata = SQLModel.metadata


def get_database_url() -> str:
    """Build database URL from settings, same as app/db/db.py"""
    import boto3
    
    # Check if password is provided (for testing/fallback)
    password = settings.db_password
    
    if password:
        return (
            f"postgresql+psycopg2://{settings.db_user}:"
            f"{password}@"
            f"{settings.db_host}:"
            f"{settings.db_port}/"
            f"{settings.db_name}"
            f"?sslmode=require"
        )
    
    # Use IAM authentication
    rds = boto3.client("rds", region_name=settings.aws_region)
    token = rds.generate_db_auth_token(
        DBHostname=settings.db_host,
        Port=settings.db_port,
        DBUsername=settings.db_user,
    )
    return (
        f"postgresql+psycopg2://{settings.db_user}:"
        f"{token}@"
        f"{settings.db_host}:"
        f"{settings.db_port}/"
        f"{settings.db_name}"
        f"?sslmode=require"
    )


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""
    config.set_main_option("sqlalchemy.url", get_database_url())

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()