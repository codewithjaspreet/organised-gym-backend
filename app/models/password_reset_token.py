from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from uuid import uuid4

if TYPE_CHECKING:
    from app.models.user import User


class PasswordResetToken(SQLModel, table=True):
    __tablename__ = "password_reset_tokens"
    
    id: str = Field(
        description="The token's id",
        primary_key=True,
        default_factory=lambda: str(uuid4())
    )
    user_id: str = Field(
        description="The user's id",
        foreign_key="users.id",
        index=True
    )
    token: str = Field(
        description="The reset token",
        unique=True,
        index=True
    )
    expires_at: datetime = Field(
        description="The token expiration time"
    )
    is_used: bool = Field(
        description="Whether the token has been used",
        default=False
    )
    created_at: datetime = Field(
        description="The token creation time",
        default_factory=datetime.now
    )
    used_at: Optional[datetime] = Field(
        description="When the token was used",
        nullable=True
    )
    
    # Relationships
    user: Optional["User"] = Relationship()
