from sqlmodel import select
from app.core.exceptions import EmailAlreadyExistsError, InvalidCredentialsError, PhoneAlreadyExistsError, UserAlreadyExistsError, UserNameAlreadyExistsError, NotFoundError
from app.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password
from app.db.db import SessionDep
from app.models.user import User
from app.models.role import Role
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.user import UserCreate

class AuthService:

    def __init__(self , session: SessionDep):
        self.session = session

    
    def register(self, user: UserCreate) -> LoginResponse:
            # 1. Check if user already exists by email
            stmt = select(User).where(User.email == user.email)
            existing_user = self.session.exec(stmt).first()
            if existing_user:
                raise EmailAlreadyExistsError(detail="User with this email is already registered")
            
            # 2. Check if user already exists by phone
            stmt = select(User).where(User.phone == user.phone)
            existing_user = self.session.exec(stmt).first()
            if existing_user:
                raise PhoneAlreadyExistsError(detail="User with this phone number is already registered")
            
            # 3. Get role_id from role name
            stmt = select(Role).where(Role.name == user.role.upper())
            role = self.session.exec(stmt).first()
            if not role:
                raise NotFoundError(detail=f"Role '{user.role}' not found")
            
            # 4. Generate username if not provided
            if not user.user_name:
                user.user_name = self._generate_username(user.email, user.name)
            
            # 5. Check if username exists and generate a unique one
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
            
            # 4. Hash password
            hashed_password = get_password_hash(user.password)
            
            # 5. Create user object
            db_user = User(
                user_name=user.user_name,
                name=user.name,
                email=user.email,
                password_hash=hashed_password,
                phone=user.phone,
                gender=user.gender,
                address_line1=user.address_line1,
                address_line2=user.address_line2,
                city=user.city,
                state=user.state,
                postal_code=user.postal_code,
                country=user.country,
                dob=user.dob,
                role_id=role.id,
                gym_id=user.gym_id,
                device_token=user.device_token,
                app_version=user.app_version,
                platform=user.platform,  # Already normalized by validator
                is_active=True
            )
            
            # 7. Save to database
            self.session.add(db_user)
            self.session.commit()
            self.session.refresh(db_user)
            
            # 8. Get role name for token
            role_name = role.name
            
            # 9. Create tokens (auto-login)
            token_data = {"sub": db_user.id, "email": db_user.email, "role": role_name}
            access_token = create_access_token(data=token_data)
            refresh_token = create_refresh_token(data=token_data)
            
            # 10. Return LoginResponse with tokens and username
            return LoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                role=role_name,
                user_name=db_user.user_name
            )
    
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
        
        
    def login(self, req: LoginRequest) -> LoginResponse:
        # 1. Find user by email
        stmt = select(User).where(User.email == req.email)
        user = self.session.exec(stmt).first()
        
        if not user:
            raise InvalidCredentialsError()
        
        # 2. Verify password
        if not verify_password(req.password, user.password_hash):
            raise InvalidCredentialsError()
        
        # 3. Check if user is active
        if not user.is_active:
            raise InvalidCredentialsError(detail="User account is inactive")
        
        # 4. Update device_token, app_version, and platform if provided
        if req.device_token is not None:
            user.device_token = req.device_token
        if req.app_version is not None:
            user.app_version = req.app_version
        if req.platform is not None:
            user.platform = req.platform  # Already normalized by validator
        
        # Save user updates
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        
        # 5. Get role name for token
        stmt = select(Role).where(Role.id == user.role_id)
        role = self.session.exec(stmt).first()
        role_name = role.name if role else "MEMBER"
        
        # 6. Create tokens
        token_data = {"sub": user.id, "email": user.email, "role": role_name}
        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)
        
        # 7. Return tokens with role
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            role=role_name
        )