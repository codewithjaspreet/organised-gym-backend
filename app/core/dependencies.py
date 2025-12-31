from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import session
from sqlmodel import Session, select

from app.core.security import decode_token
from app.db.db import get_session
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

async def get_current_user(token:str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:

    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

     
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    stmt = select(User).where(User.id == user_id)
    user = session.exec(stmt).first()
    if user is None:
        raise credentials_exception
    
    return user