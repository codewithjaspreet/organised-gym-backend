from sqlmodel import select
from app.core.exceptions import NotFoundError, UserNameAlreadyExistsError, UserNotFoundError
from app.db.db import SessionDep
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate


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

    def create_user(self, user: UserCreate) -> UserResponse:
        stmt = select(User).where(User.user_name == user.user_name)
        existing = self.session.exec(stmt).first()
        if existing:
            raise UserNameAlreadyExistsError()
        
        user = User(**user.model_dump())
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return UserResponse(**user.model_dump(exclude={"password_hash"}))

