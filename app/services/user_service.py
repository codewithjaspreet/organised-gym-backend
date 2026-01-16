from typing import List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlmodel import select, func, and_, or_
from app.core.exceptions import NotFoundError, UserNameAlreadyExistsError, UserNotFoundError
from app.db.db import SessionDep
from app.models.user import RoleEnum, User
from app.models.role import Role
from app.models.membership import Membership
from app.models.plan import Plan
from app.schemas.user import (
    UserCreate, UserResponse, UserUpdate, 
    MemberListResponse, MemberListItemResponse, 
    MemberDetailResponse, CurrentPlanResponse,
    AvailableMembersListResponse, AvailableMemberResponse
)
from app.core.security import get_password_hash

class UserService:

    def __init__(self, session: SessionDep):
        self.session = session

    def get_user(self, user_id: str) -> UserResponse:
        from app.models.role import Role as RoleModel
        from app.models.gym import Gym
        
        stmt = select(User).where(User.id == user_id)
        user = self.session.exec(stmt).first()
        if not user:
            raise UserNotFoundError(detail=f"User with id {user_id} not found")
        
        # Get role name
        role_name = None
        if user.role_id:
            role_stmt = select(RoleModel).where(RoleModel.id == user.role_id)
            role = self.session.exec(role_stmt).first()
            role_name = role.name if role else None
        
        # Get gym name
        gym_name = None
        if user.gym_id:
            gym_stmt = select(Gym).where(Gym.id == user.gym_id)
            gym = self.session.exec(gym_stmt).first()
            gym_name = gym.name if gym else None
        
        user_dict = user.model_dump(exclude={"password_hash"})
        user_dict["role_name"] = role_name
        user_dict["gym_name"] = gym_name
        return UserResponse(**user_dict)

    def get_member_detail(self, member_id: str, gym_id: str) -> MemberDetailResponse:
        """Get detailed member information with current plan"""
        # Get user
        stmt = select(User).where(User.id == member_id)
        user = self.session.exec(stmt).first()
        if not user:
            raise UserNotFoundError(detail=f"Member with id {member_id} not found")
        
        # Verify it's a member and belongs to the gym
        from app.models.role import Role as RoleModel
        member_role_stmt = select(RoleModel).where(RoleModel.name == "MEMBER")
        member_role = self.session.exec(member_role_stmt).first()
        
        if not member_role or user.role_id != member_role.id or user.gym_id != gym_id:
            raise UserNotFoundError(detail=f"Member with id {member_id} not found")
        
        # Get role name
        role_stmt = select(RoleModel).where(RoleModel.id == user.role_id)
        role = self.session.exec(role_stmt).first()
        role_name = role.name if role else "MEMBER"
        
        # Get current active membership and plan
        today = date.today()
        membership_stmt = select(Membership).where(
            and_(
                Membership.user_id == member_id,
                Membership.gym_id == gym_id,
                Membership.end_date >= today,
                Membership.status == "active"
            )
        ).order_by(Membership.end_date.desc())
        membership = self.session.exec(membership_stmt).first()
        
        current_plan = None
        if membership:
            plan_stmt = select(Plan).where(Plan.id == membership.plan_id)
            plan = self.session.exec(plan_stmt).first()
            
            if plan:
                # Use discounted_plan_price if available, otherwise use plan.price
                total_price = float(membership.discounted_plan_price) if membership.discounted_plan_price else float(plan.price)
                
                # Calculate monthly price (approximate from total price and duration)
                # Use actual membership duration (plan duration + bonus duration)
                total_duration = plan.duration_days + (membership.bonus_duration or 0)
                monthly_price = total_price / (total_duration / 30.0) if total_duration > 0 else total_price
                
                # Determine status
                days_left = (membership.end_date - today).days
                if days_left <= 7:
                    status = "expiring_soon"
                else:
                    status = "active"
                
                current_plan = CurrentPlanResponse(
                    plan_id=plan.id,
                    plan_name=plan.name,
                    expiry_date=membership.end_date.isoformat(),
                    monthly_price=round(monthly_price, 2),
                    status=status,
                    days_left=days_left
                )
        
        return MemberDetailResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone,
            gender=user.gender,
            dob=user.dob,
            photo_url=user.photo_url,
            role=role_name,
            current_plan=current_plan,
            address_line1=user.address_line1,
            address_line2=user.address_line2,
            city=user.city,
            state=user.state,
            postal_code=user.postal_code,
            country=user.country,
            created_at=user.created_at
        )

    def get_all_members(
        self,
        gym_id: str,
        search: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: Optional[str] = None,
        pending_fees: Optional[bool] = None,
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
        
        # Apply pending_fees filter (if provided, overrides status filter for fees)
        if pending_fees is not None:
            from app.models.billing import Payment
            # Get users with pending or overdue payments
            today = date.today()
            user_ids_subquery = select(func.distinct(Payment.user_id)).where(
                and_(
                    Payment.gym_id == gym_id,
                    Payment.status == "pending"
                )
            )
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
        
        # Get plan info for each member
        members = []
        today = date.today()
        
        for user in users:
            # Get active membership for this user
            membership_stmt = select(Membership).where(
                and_(
                    Membership.user_id == user.id,
                    Membership.gym_id == gym_id,
                    Membership.end_date >= today
                )
            ).order_by(Membership.end_date.desc())
            membership = self.session.exec(membership_stmt).first()
            
            plan_name = None
            plan_status = None
            plan_expiry_date = None
            days_left = None
            
            if membership:
                # Get plan details
                plan_stmt = select(Plan).where(Plan.id == membership.plan_id)
                plan = self.session.exec(plan_stmt).first()
                
                if plan:
                    plan_name = plan.name
                    plan_expiry_date = membership.end_date
                    
                    # Calculate days left
                    if membership.end_date >= today:
                        days_left = (membership.end_date - today).days
                        if days_left <= 7:
                            plan_status = "expiring_soon"
                        else:
                            plan_status = "active"
                    else:
                        plan_status = "expired"
                        days_left = 0
                else:
                    plan_status = "expired" if membership.end_date < today else "active"
            else:
                # Check if user has any expired membership
                expired_stmt = select(Membership).where(
                    and_(
                        Membership.user_id == user.id,
                        Membership.gym_id == gym_id,
                        Membership.end_date < today
                    )
                ).order_by(Membership.end_date.desc())
                expired_membership = self.session.exec(expired_stmt).first()
                
                if expired_membership:
                    plan_stmt = select(Plan).where(Plan.id == expired_membership.plan_id)
                    plan = self.session.exec(plan_stmt).first()
                    if plan:
                        plan_name = plan.name
                    plan_status = "expired"
                    plan_expiry_date = expired_membership.end_date
                    days_left = 0
            
            members.append(MemberListItemResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                photo_url=user.photo_url,
                plan_name=plan_name,
                plan_status=plan_status,
                plan_expiry_date=plan_expiry_date,
                days_left=days_left
            ))
        
        has_next = (page * page_size) < total
        
        return MemberListResponse(
            members=members,
            total=total,
            page=page,
            page_size=page_size,
            has_next=has_next
        )
 
    def update_user(self, user_id: str, user_update: UserUpdate) -> UserResponse:
        from app.models.role import Role as RoleModel
        
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

        # Get role name for response
        role_name = None
        if user.role_id:
            role_stmt = select(RoleModel).where(RoleModel.id == user.role_id)
            role = self.session.exec(role_stmt).first()
            role_name = role.name if role else None

        user_dict = user.model_dump(exclude={"password_hash"})
        user_dict["role_name"] = role_name
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

    def get_available_members(
        self,
        query: Optional[str] = None
    ) -> AvailableMembersListResponse:
        """Get all members that are not assigned to any gym (gym_id is null) with optional search query"""
        from app.models.role import Role as RoleModel
        
        # Get MEMBER role id
        member_role_stmt = select(RoleModel).where(RoleModel.name == "MEMBER")
        member_role = self.session.exec(member_role_stmt).first()
        
        if not member_role:
            return AvailableMembersListResponse(members=[])
        
        # Base query: members with gym_id = null and role = MEMBER
        stmt = select(User).where(
            and_(
                User.role_id == member_role.id,
                User.gym_id.is_(None)
            )
        )
        
        # Apply search query across all fields if provided
        if query:
            search_term = f"%{query.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(User.name).like(search_term),
                    func.lower(User.email).like(search_term),
                    func.lower(User.user_name).like(search_term),
                    User.phone.like(f"%{query}%")
                )
            )
        
        stmt = stmt.order_by(User.name.asc())
        
        users = self.session.exec(stmt).all()
        
        members = [
            AvailableMemberResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                phone=user.phone,
                user_name=user.user_name
            )
            for user in users
        ]
        
        return AvailableMembersListResponse(members=members)

    def add_member_to_gym(
        self, 
        member_user_name: str, 
        gym_id: str,
        plan_id: Optional[str] = None,
        bonus_duration: Optional[int] = None,
        discounted_plan_price: Optional[Decimal] = None
    ) -> UserResponse:
        """Add an existing member to a gym by username and create membership if plan_id is provided"""
        from app.models.role import Role as RoleModel
        from app.models.plan import Plan
        from app.models.membership import Membership
        from datetime import date, timedelta
        
        # Find user by username
        stmt = select(User).where(User.user_name == member_user_name)
        user = self.session.exec(stmt).first()
        
        if not user:
            raise UserNotFoundError(detail=f"User with username '{member_user_name}' not found")
        
        # Verify user is a MEMBER
        member_role_stmt = select(RoleModel).where(RoleModel.name == "MEMBER")
        member_role = self.session.exec(member_role_stmt).first()
        
        if not member_role or user.role_id != member_role.id:
            raise NotFoundError(detail=f"User '{member_user_name}' is not a member")
        
        # Check if user is already assigned to a gym
        if user.gym_id is not None:
            if user.gym_id == gym_id:
                # Already in this gym
                return UserResponse(**user.model_dump(exclude={"password_hash"}))
            else:
                raise NotFoundError(detail=f"User '{member_user_name}' is already assigned to another gym")
        
        # Assign user to gym
        user.gym_id = gym_id
        self.session.commit()
        self.session.refresh(user)
        
        # Create membership if plan_id is provided
        if plan_id:
            # Verify plan exists and belongs to the gym
            plan_stmt = select(Plan).where(
                and_(
                    Plan.id == plan_id,
                    Plan.gym_id == gym_id
                )
            )
            plan = self.session.exec(plan_stmt).first()
            
            if not plan:
                raise NotFoundError(detail=f"Plan with id '{plan_id}' not found for this gym")
            
            # Calculate start and end dates
            today = date.today()
            total_duration = plan.duration_days + (bonus_duration or 0)
            end_date = today + timedelta(days=total_duration)
            
            # Create membership
            membership = Membership(
                user_id=user.id,
                gym_id=gym_id,
                start_date=today,
                end_date=end_date,
                status="active",
                plan_id=plan_id,
                bonus_duration=bonus_duration,
                discounted_plan_price=discounted_plan_price
            )
            self.session.add(membership)
            self.session.commit()
        
        return UserResponse(**user.model_dump(exclude={"password_hash"}))

