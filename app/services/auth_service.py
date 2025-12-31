from sqlmodel import select
from app.core.exceptions import EmailAlreadyExistsError, InvalidCredentialsError, PhoneAlreadyExistsError, UserAlreadyExistsError, UserNameAlreadyExistsError
from app.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password
from app.db.db import SessionDep
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.user import UserCreate, UserResponse

class AuthService:

    def __init__(self , session: SessionDep):
        self.session = session

    
    def register(self, user: UserCreate) -> UserResponse:
            # 1. Check if username exists
            
            stmt = select(User).where(User.user_name == user.user_name)
            existing = self.session.exec(stmt).first()
            if existing:
                raise UserNameAlreadyExistsError()
            
            # 2. Hash password
            hashed_password = get_password_hash(user.password)
            
            # 3. Create user object
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
                role=user.role,
                is_active=True
            )
            
            # 5. Save to database
            self.session.add(db_user)
            self.session.commit()
            self.session.refresh(db_user)
            
            # 6. Return UserResponse (exclude password_hash)
            user_dict = db_user.model_dump(exclude={"password_hash"})
            return UserResponse(**user_dict)
        
        
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
        
        # 4. Create tokens
        token_data = {"sub": user.id, "email": user.email, "role": user.role.value}
        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)
        
        # 5. Return tokens
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )