from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from uuid import uuid4

if TYPE_CHECKING:
    from app.models.user import User


class PasswordResetToken(SQLModel, table=True):
    __tablename__ = "password_reset_tokens"
    
    id: str = Field(
        description="The password reset token id",
        primary_key=True,
        default_factory=lambda: str(uuid4())
    )
    user_id: str = Field(
        description="The user id",
        foreign_key="users.id",
        index=True
    )
    token_hash: str = Field(
        description="The hashed token",
        index=True
    )
    expires_at: datetime = Field(
        description="The token expiration date"
    )
    used: bool = Field(
        description="Whether the token has been used",
        default=False
    )
    created_at: datetime = Field(
        description="The token creation date",
        default_factory=datetime.now
    )
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="password_reset_tokens")
