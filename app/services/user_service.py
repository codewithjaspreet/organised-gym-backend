from typing import List, Optional, Tuple
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy import exists
from sqlmodel import select, func, and_, or_, desc, asc
from app.core.exceptions import NotFoundError, UserNameAlreadyExistsError, UserNotFoundError
from app.db.db import SessionDep
from app.models.user import RoleEnum, User
from app.models.role import Role
from app.models.membership import Membership
from app.models.plan import Plan
from app.models.role import Role
from app.models.membership import Membership
from app.models.plan import Plan
from app.models.payments import Payment
from app.schemas.user import (
    UserCreate, UserResponse, UserUpdate,
    MemberListResponse, MemberListItemResponse,
    MemberDetailResponse, CurrentPlanResponse,
    AvailableMembersListResponse, AvailableMemberResponse
)
from app.core.security import create_reset_token, get_password_hash, verify_reset_token
from app.utils.emails import send_reset_password_mail

RESET_TOKEN_EXPIRE_MINUTES = 10


class UserService:

    def __init__(self, session: SessionDep):
        self.session = session

    def get_user(self, user_id: str) -> UserResponse:
        from app.models.role import Role as RoleModel
        from app.models.gym import Gym
        from datetime import date

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

        # For members, get plan_id and plan_amount from active membership instead of user.plan_id
        plan_id = user.plan_id
        plan_amount = None
        current_plan = None
        if role_name == "MEMBER" and user.gym_id:
            today = date.today()
            # Get active membership (status = 'active' and end_date >= today)
            membership_stmt = select(Membership).where(
                and_(
                    Membership.user_id == user_id,
                    Membership.gym_id == user.gym_id,
                    Membership.status == "active",
                    Membership.end_date >= today
                )
            ).order_by(desc(Membership.end_date))
            active_membership = self.session.exec(membership_stmt).first()

            if active_membership and active_membership.plan_id:
                plan_id = active_membership.plan_id

                # Get plan details to get the amount
                plan_stmt = select(Plan).where(Plan.id == active_membership.plan_id)
                plan = self.session.exec(plan_stmt).first()

                if plan:
                    # Use new_price if available, otherwise use plan.price (same logic as get_all_members)
                    plan_amount = active_membership.new_price if active_membership.new_price else plan.price

                    # Build current_plan object (same as member-detail)
                    total_price = float(active_membership.new_price) if active_membership.new_price else float(plan.price)
                    days_left = (active_membership.end_date - today).days
                    if days_left <= 7:
                        status = "expiring_soon"
                    else:
                        status = "active"

                    current_plan = CurrentPlanResponse(
                        plan_id=plan.id,
                        plan_name=plan.name,
                        expiry_date=active_membership.end_date.isoformat(),
                        monthly_price=round(total_price, 2),
                        status=status,
                        days_left=days_left
                    )
            else:
                # Check if user has any expired membership (fallback similar to get_all_members)
                expired_stmt = select(Membership).where(
                    and_(
                        Membership.user_id == user_id,
                        Membership.gym_id == user.gym_id,
                        Membership.end_date < today
                    )
                ).order_by(desc(Membership.end_date))
                expired_membership = self.session.exec(expired_stmt).first()

                if expired_membership and expired_membership.plan_id:
                    plan_id = expired_membership.plan_id

                    # Get plan details to get the amount
                    plan_stmt = select(Plan).where(Plan.id == expired_membership.plan_id)
                    plan = self.session.exec(plan_stmt).first()

                    if plan:
                        # Use new_price if available, otherwise use plan.price
                        plan_amount = expired_membership.new_price if expired_membership.new_price else plan.price

        user_dict = user.model_dump(exclude={"password_hash"})
        user_dict["role_name"] = role_name
        user_dict["gym_name"] = gym_name
        user_dict["plan_id"] = plan_id
        user_dict["plan_amount"] = plan_amount
        user_dict["current_plan"] = current_plan
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
        ).order_by(desc(Membership.end_date))
        membership = self.session.exec(membership_stmt).first()

        current_plan = None
        if membership:
            plan_stmt = select(Plan).where(Plan.id == membership.plan_id)
            plan = self.session.exec(plan_stmt).first()

            if plan:
                # Use new_price if available, otherwise use plan.price
                total_price = float(membership.new_price) if membership.new_price else float(plan.price)
                days_left = (membership.end_date - today).days
                if days_left <= 7:
                    status = "expiring_soon"
                else:
                    status = "active"

                current_plan = CurrentPlanResponse(
                    plan_id=plan.id,
                    plan_name=plan.name,
                    expiry_date=membership.end_date.isoformat(),
                    monthly_price=round(total_price, 2),
                    status=status,
                    days_left=days_left
                )

        return MemberDetailResponse(
            id=user.id,
            user_name=user.user_name,
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

        today = date.today()
        offset = (page - 1) * page_size

        member_role_id = self.session.exec(
            select(Role.id).where(Role.name == "MEMBER")
        ).first()

        if not member_role_id:
            return MemberListResponse(
                members=[], total=0, page=page, page_size=page_size, has_next=False
            )

        # ---- BASE FILTERS (HARD GUARANTEE) ----
        base_filters = [
            User.role_id == member_role_id,
            User.gym_id == gym_id,
            User.gym_id.is_not(None) # type: ignore
        ]

        # ---- SEARCH ----
        if search:
            term = f"%{search.lower()}%"
            base_filters.append(
                or_(
                    func.lower(User.name).like(term),
                    func.lower(User.email).like(term)
                )
            )

        # ---- STATUS FILTERS ----
        if status and status != "all":

            if status == "new_joins":
                base_filters.append(
                    User.created_at >= datetime.utcnow() - timedelta(days=30)
                )

            elif status in {"active", "expired"}:
                membership_conditions = [
                    Membership.user_id == User.id,
                    Membership.gym_id == gym_id
                ]

                if status == "active":
                    membership_conditions += [
                        Membership.status == "active",
                        Membership.end_date >= today
                    ]
                else:
                    membership_conditions.append(Membership.end_date < today)

                base_filters.append(
                    exists().where(and_(*membership_conditions))
                )

            elif status == "payment_pending":
                base_filters.append(
                    exists().where(
                        and_(
                            Payment.user_id == User.id,
                            Payment.gym_id == gym_id,
                            Payment.status == "pending"
                        )
                    )
                )

        # ---- PENDING FEES OVERRIDE ----
        if pending_fees is True:
            base_filters.append(
                exists().where(
                    and_(
                        Payment.user_id == User.id,
                        Payment.gym_id == gym_id,
                        Payment.status == "pending"
                    )
                )
            )

        # ---- MAIN QUERY ----
        stmt = (
            select(User, Membership, Plan)
            .join(
                Membership,
                and_(
                    Membership.user_id == User.id,
                    Membership.gym_id == gym_id
                ),
                isouter=True
            )
            .join(Plan, Plan.id == Membership.plan_id, isouter=True) # type: ignore
            .where(and_(*base_filters))
        )

        # ---- SORTING ----
        if sort_by == "name_desc":
            stmt = stmt.order_by(desc(User.name))
        elif sort_by == "newest_joiners":
            stmt = stmt.order_by(desc(User.created_at))
        else:
            stmt = stmt.order_by(asc(User.name))

        # ---- COUNT ----
        total = self.session.exec(
            select(func.count(func.distinct(User.id))).where(and_(*base_filters))
        ).first() or 0

        # ---- PAGINATION ----
        rows = self.session.exec(
            stmt.limit(page_size).offset(offset)
        ).all()

        members = {}
        for user, membership, plan in rows:

            if user.id in members:
                continue

            plan_name = plan_status = plan_expiry_date = days_left = None

            if membership and membership.end_date:
                plan_name = plan.name if plan else None
                plan_expiry_date = membership.end_date

                if membership.end_date >= today:
                    days_left = (membership.end_date - today).days
                    plan_status = "expiring_soon" if days_left <= 7 else "active"
                else:
                    plan_status = "expired"
                    days_left = 0

            members[user.id] = MemberListItemResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                photo_url=user.photo_url,
                plan_name=plan_name,
                plan_status=plan_status,
                plan_expiry_date=plan_expiry_date,
                days_left=days_left
            )

        return MemberListResponse(
            members=list(members.values()),
            total=total,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total
        )



    def update_user(self, user_id: str, user_update: UserUpdate) -> UserResponse:
        from app.models.role import Role as RoleModel

        stmt = select(User).where(User.id == user_id)
        user = self.session.exec(stmt).first()
        if not user:
            raise UserNotFoundError(detail=f"User with id {user_id} not found")

        # Update only provided fields
        update_data = user_update.model_dump(exclude_unset=True)

        # Name is not updatable via this endpoint (owner cannot change member name)
        update_data.pop("name", None)

        # Handle gym_id = None (remove member from gym)
        if 'gym_id' in update_data and update_data['gym_id'] is None:
            update_data['gym_id'] = None
            # Also remove plan_id when removing from gym
            update_data['plan_id'] = None
            # End all active memberships for this user
            today = date.today()
            active_memberships_stmt = select(Membership).where(
                and_(
                    Membership.user_id == user_id,
                    Membership.status == "active"
                )
            )
            active_memberships = self.session.exec(active_memberships_stmt).all()
            for membership in active_memberships:
                membership.status = "expired"
                if membership.end_date > today:
                    membership.end_date = today

        # Handle plan_id updates
        if 'plan_id' in update_data:
            plan_id_value = update_data['plan_id']

            if plan_id_value is None:
                # Remove plan - end active memberships
                today = date.today()
                active_memberships_stmt = select(Membership).where(
                    and_(
                        Membership.user_id == user_id,
                        Membership.status == "active"
                    )
                )
                active_memberships = self.session.exec(active_memberships_stmt).all()
                for membership in active_memberships:
                    membership.status = "expired"
                    if membership.end_date > today:
                        membership.end_date = today
            else:
                # Update plan_id - update active membership's plan_id
                today = date.today()

                active_membership_stmt = select(Membership).where(
                    and_(
                        Membership.user_id == user_id,
                        Membership.status == "active",
                        Membership.end_date >= today
                    )
                ).order_by(desc(Membership.end_date))

                active_membership = self.session.exec(active_membership_stmt).first()
                if active_membership:
                    active_membership.plan_id = plan_id_value

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
                User.gym_id == None
            )
        )

        # Apply search query across all fields if provided
        if query:
            search_term = f"%{query.lower()}%"
            stmt = stmt.where(  # type: ignore [arg-type]
                or_(
                    func.lower(User.name).like(search_term),
                    func.lower(User.email).like(search_term),
                    func.lower(User.user_name).like(search_term),
                    User.phone.like(f"%{query}%")  # type: ignore [attr-defined]
                )
            )

        stmt = stmt.order_by(asc(User.name))

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
        new_duration: Optional[int] = None,
        new_price: Optional[Decimal] = None
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

        # Member must be active
        if not user.is_active:
            raise NotFoundError(detail=f"User '{member_user_name}' is inactive and cannot be added to a gym")

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
            # Verify plan exists, belongs to the gym, and is active
            plan_stmt = select(Plan).where(
                and_(
                    Plan.id == plan_id,
                    Plan.gym_id == gym_id
                )
            )
            plan = self.session.exec(plan_stmt).first()

            if not plan:
                raise NotFoundError(detail=f"Plan with id '{plan_id}' not found for this gym")
            if not plan.is_active:
                raise NotFoundError(detail=f"Plan with id '{plan_id}' is inactive. Only active plans can be assigned.")

            # Calculate start and end dates
            # Use new_duration if provided, otherwise use plan duration
            today = date.today()
            duration = new_duration if new_duration is not None else plan.duration_days
            end_date = today + timedelta(days=duration)

            # Create membership
            membership = Membership(
                user_id=user.id,
                gym_id=gym_id,
                start_date=today,
                end_date=end_date,
                status="active",
                plan_id=plan_id,
                new_duration=new_duration,
                new_price=new_price
            )
            self.session.add(membership)
            self.session.commit()

        return UserResponse(**user.model_dump(exclude={"password_hash"}))

    def leave_gym(self, user_id: str) -> None:
        """Member leaves their gym: clear gym_id and plan_id, deactivate all active memberships for that gym."""
        stmt = select(User).where(User.id == user_id)
        user = self.session.exec(stmt).first()
        if not user:
            raise UserNotFoundError(detail="User not found")
        if not user.gym_id:
            raise NotFoundError(detail="User is not assigned to any gym")
        gym_id = user.gym_id
        user.gym_id = None
        user.plan_id = None
        self.session.add(user)
        # Deactivate all active memberships for this user in this gym
        membership_stmt = select(Membership).where(
            and_(
                Membership.user_id == user_id,
                Membership.gym_id == gym_id,
                Membership.status == "active",
            )
        )
        for m in self.session.exec(membership_stmt).all():
            m.status = "inactive"
            self.session.add(m)
        self.session.commit()

    def get_reset_link_data(
        self,
        email: str,
        base_url: str,
    ) -> Optional[Tuple[str, str, str, int]]:
        """
        Returns (recipient_email, user_name, reset_url, expire_minutes) if user exists.
        Silent fail if user does not exist (security best practice).
        """
        stmt = select(User).where(User.email == email)
        user = self.session.exec(stmt).first()
        if not user:
            return None
        token = create_reset_token(email, RESET_TOKEN_EXPIRE_MINUTES)
        reset_url = f"{base_url}v1/auth/reset-password?token={token}"
        return (email, user.name, reset_url, RESET_TOKEN_EXPIRE_MINUTES)

    def reset_password(
        self,
        token: str,
        new_password: str,
    ) -> User:
        """
        Verifies reset token and updates user password.
        Returns the user on success.
        """
        email = verify_reset_token(token)
        if not email:
            raise ValueError("Invalid or expired reset token")

        stmt = select(User).where(User.email == email)
        user = self.session.exec(stmt).first()

        if not user:
            raise ValueError("User not found")

        user.password_hash = get_password_hash(new_password)
        self.session.add(user)
        self.session.commit()
        return user

