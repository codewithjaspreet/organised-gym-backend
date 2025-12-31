from sqlmodel import select
from app.core.exceptions import NotFoundError, UserNotFoundError
from app.db.db import SessionDep
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate


class UserService:

    def __init__(self, session: SessionDep):
        self.session = session

    def get_user(self, user_id: str) -> UserResponse:
        stmt = select(User).where(User.id == user_id)
        user = self.session.exec(stmt).first()
        if not user:
            raise UserNotFoundError(detail=f"User with id {user_id} not found")
        
        user_dict = user.model_dump(exclude={"password_hash"})
        return UserResponse(**user_dict)

    def update_user(self, user_id: str, user_update: UserUpdate) -> UserResponse:
        stmt = select(User).where(User.id == user_id)
        user = self.session.exec(stmt).first()
        if not user:
            raise UserNotFoundError(detail=f"User with id {user_id} not found")

        # Update only provided fields
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        self.session.commit()
        self.session.refresh(user)

        user_dict = user.model_dump(exclude={"password_hash"})
        return UserResponse(**user_dict)

    def delete_user(self, user_id: str) -> None:
        stmt = select(User).where(User.id == user_id)
        user = self.session.exec(stmt).first()
        if not user:
            raise UserNotFoundError(detail=f"User with id {user_id} not found")

        self.session.delete(user)
        self.session.commit()
        return None

