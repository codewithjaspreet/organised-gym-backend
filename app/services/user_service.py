from sqlmodel import select
from app.core.exceptions import NotFoundError, UserNameAlreadyExistsError, UserNotFoundError
from app.db.db import SessionDep
from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.core.security import get_password_hash

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
        
        # Handle role name to role_id conversion
        if 'role' in update_data:
            role_name = update_data.pop('role')
            stmt = select(Role).where(Role.name == role_name.upper())
            role = self.session.exec(stmt).first()
            if not role:
                raise NotFoundError(detail=f"Role '{role_name}' not found")
            update_data['role_id'] = role.id
        
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

        # 1. Generate username if not provided
        if not user.user_name:
            user.user_name = self._generate_username(user.email, user.name)
        
        # 2. Check if username exists and generate a unique one
        stmt = select(User).where(User.user_name == user.user_name)
        existing = self.session.exec(stmt).first()
        if existing:
            # Generate a unique username by appending a number
            base_username = user.user_name
            counter = 1
            while existing:
                user.user_name = f"{base_username}{counter}"
                stmt = select(User).where(User.user_name == user.user_name)
                existing = self.session.exec(stmt).first()
                counter += 1
        
        # 3. Convert role name to role_id if role is provided
        user_dict = user.model_dump()
        if 'role' in user_dict and user_dict['role']:
            role_name = user_dict.pop('role')
            stmt = select(Role).where(Role.name == role_name.upper())
            role = self.session.exec(stmt).first()
            if not role:
                raise NotFoundError(detail=f"Role '{role_name}' not found")
            user_dict['role_id'] = role.id
        elif 'role_id' not in user_dict:
            raise NotFoundError(detail="Role is required when creating a user")
        
        # 4. Hash password if provided
        if 'password' in user_dict:
            user_dict['password_hash'] = get_password_hash(user_dict.pop('password'))
        
        db_user = User(**user_dict)
        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return UserResponse(**db_user.model_dump(exclude={"password_hash"}))
    
    def _generate_username(self, email: str, name: str) -> str:
        """
        Generate a username from email or name
        Ensures minimum length of 4 characters as required by the model
        """
        import re
        import random
        import string
        
        # Try to generate from email first (before @)
        if email:
            username = email.split('@')[0]
            # Remove special characters and keep only alphanumeric
            username = re.sub(r'[^a-zA-Z0-9]', '', username)
            if username and len(username) >= 4:
                return username.lower()
            elif username:
                # If too short, pad with random characters
                padding = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4-len(username)))
                return (username + padding).lower()
        
        # Fallback to name
        if name:
            username = re.sub(r'[^a-zA-Z0-9]', '', name)
            if username and len(username) >= 4:
                return username.lower()
            elif username:
                # If too short, pad with random characters
                padding = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4-len(username)))
                return (username + padding).lower()
        
        # Final fallback - generate a random username
        random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"user{random_part}"

