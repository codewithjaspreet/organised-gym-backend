from typing import List, Optional
from datetime import date, datetime, timedelta
from sqlmodel import select, func, and_, or_
from app.core.exceptions import NotFoundError, UserNameAlreadyExistsError, UserNotFoundError
from app.db.db import SessionDep
from app.models.user import RoleEnum, User
from app.models.role import Role
from app.models.membership import Membership
from app.schemas.user import UserCreate, UserResponse, UserUpdate, MemberListResponse
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

    def get_all_members(
        self,
        gym_id: str,
        search: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> MemberListResponse:
        """Get all members with filtering, sorting, and pagination"""
        from app.models.role import Role as RoleModel
        
        # Get MEMBER role id
        member_role_stmt = select(RoleModel).where(RoleModel.name == "MEMBER")
        member_role = self.session.exec(member_role_stmt).first()
        if not member_role:
            return MemberListResponse(
                members=[],
                total=0,
                page=page,
                page_size=page_size,
                has_next=False
            )
        
        # Base query: all members in the gym
        stmt = select(User).where(
            and_(
                User.gym_id == gym_id,
                User.role_id == member_role.id
            )
        )
        
        # Apply search filter (name or email)
        if search:
            search_term = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(User.name).like(search_term),
                    func.lower(User.email).like(search_term)
                )
            )
        
        # Apply status filter
        if status and status != "all":
            if status == "new_joins":
                # New joins: created in last 30 days
                thirty_days_ago = datetime.now() - timedelta(days=30)
                stmt = stmt.where(User.created_at >= thirty_days_ago)
            else:
                today = date.today()
                user_ids_subquery = None
                
                if status == "active":
                    # Active plans: end_date >= today
                    user_ids_subquery = select(Membership.user_id).where(
                        and_(
                            Membership.gym_id == gym_id,
                            Membership.status == "active",
                            Membership.end_date >= today
                        )
                    )
                elif status == "expired":
                    # Expired plans: end_date < today
                    user_ids_subquery = select(Membership.user_id).where(
                        and_(
                            Membership.gym_id == gym_id,
                            Membership.end_date < today
                        )
                    )
                elif status == "payment_pending":
                    # Payment pending: users with pending payments
                    from app.models.billing import Payment
                    user_ids_subquery = select(func.distinct(Payment.user_id)).where(
                        and_(
                            Payment.gym_id == gym_id,
                            Payment.status == "pending"
                        )
                    )
                
                if user_ids_subquery is not None:
                    user_ids = [uid for uid in self.session.exec(user_ids_subquery).all()]
                    if user_ids:
                        stmt = stmt.where(User.id.in_(user_ids))
                    else:
                        # No matching users, return empty
                        return MemberListResponse(
                            members=[],
                            total=0,
                            page=page,
                            page_size=page_size,
                            has_next=False
                        )
        
        # Apply sorting
        if sort_by == "name_asc":
            stmt = stmt.order_by(User.name.asc())
        elif sort_by == "name_desc":
            stmt = stmt.order_by(User.name.desc())
        elif sort_by == "newest_joiners":
            stmt = stmt.order_by(User.created_at.desc())
        elif sort_by == "plan_expiry_soonest":
            # Sort by plan expiry - get users with active memberships first, sorted by end_date
            # Then users without memberships
            today = date.today()
            active_membership_users = select(Membership.user_id).where(
                and_(
                    Membership.gym_id == gym_id,
                    Membership.end_date >= today
                )
            ).order_by(Membership.end_date.asc())
            
            # For simplicity, sort by name for now
            # Full plan expiry sorting would require a more complex query
            stmt = stmt.order_by(User.name.asc())
        else:
            # Default: name ascending
            stmt = stmt.order_by(User.name.asc())
        
        # Get total count - use same query but count instead of select
        count_stmt = select(func.count(User.id)).where(
            and_(
                User.gym_id == gym_id,
                User.role_id == member_role.id
            )
        )
        
        if search:
            search_term = f"%{search.lower()}%"
            count_stmt = count_stmt.where(
                or_(
                    func.lower(User.name).like(search_term),
                    func.lower(User.email).like(search_term)
                )
            )
        
        if status and status != "all":
            if status == "new_joins":
                thirty_days_ago = datetime.now() - timedelta(days=30)
                count_stmt = count_stmt.where(User.created_at >= thirty_days_ago)
            else:
                # For active/expired/payment_pending, we already filtered stmt above
                # So we need to apply same filter to count
                today = date.today()
                if status == "active":
                    user_ids_subquery = select(Membership.user_id).where(
                        and_(
                            Membership.gym_id == gym_id,
                            Membership.status == "active",
                            Membership.end_date >= today
                        )
                    )
                elif status == "expired":
                    user_ids_subquery = select(Membership.user_id).where(
                        and_(
                            Membership.gym_id == gym_id,
                            Membership.end_date < today
                        )
                    )
                elif status == "payment_pending":
                    from app.models.billing import Payment
                    user_ids_subquery = select(func.distinct(Payment.user_id)).where(
                        and_(
                            Payment.gym_id == gym_id,
                            Payment.status == "pending"
                        )
                    )
                else:
                    user_ids_subquery = None
                
                if user_ids_subquery is not None:
                    user_ids = [uid for uid in self.session.exec(user_ids_subquery).all()]
                    if user_ids:
                        count_stmt = count_stmt.where(User.id.in_(user_ids))
                    else:
                        total = 0
                        return MemberListResponse(
                            members=[],
                            total=0,
                            page=page,
                            page_size=page_size,
                            has_next=False
                        )
        
        total = self.session.exec(count_stmt).first() or 0
        
        # Apply pagination
        offset = (page - 1) * page_size
        stmt = stmt.limit(page_size).offset(offset)
        
        # Execute query
        users = self.session.exec(stmt).all()
        
        # Convert to response
        members = [
            UserResponse(**user.model_dump(exclude={"password_hash"}))
            for user in users
        ]
        
        has_next = (page * page_size) < total
        
        return MemberListResponse(
            members=members,
            total=total,
            page=page,
            page_size=page_size,
            has_next=has_next
        )
 
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

