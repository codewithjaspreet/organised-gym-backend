from logging.config import fileConfig
import sys
import os
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context
from sqlmodel import SQLModel

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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

# Alembic config
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata
target_metadata = SQLModel.metadata


def get_database_url() -> str:
    url = os.getenv("ALEMBIC_DATABASE_URL")
    if not url:
        raise RuntimeError(
            "ALEMBIC_DATABASE_URL is not set. "
            "This variable is required only when running Alembic migrations."
        )
    return url


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