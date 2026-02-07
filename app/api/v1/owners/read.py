from fastapi import APIRouter, status, Query
from sqlmodel import select, and_
from typing import Optional, List
from app.core.permissions import require_admin, require_any_authenticated
from app.db.db import SessionDep
from app.models.user import User, RoleEnum
from app.models.gym import Gym
from app.models.role import Role
from app.schemas.user import UserResponse, MemberListResponse, MemberDetailResponse, AvailableMembersListResponse, OGPlanInfoResponse
from app.schemas.gym import GymResponse
from app.schemas.plan import PlanResponse, PlanListResponse
from app.schemas.gym_rule import GymRuleResponse, GymRuleListResponse
from app.schemas.membership import MembershipResponse
from app.schemas.announcement import AnnouncementResponse, AnnouncementListResponse
from app.schemas.dashboard import DashboardKPIsResponse
from app.schemas.payments import PendingPaymentListResponse, GymRevenueResponse
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.user_service import UserService
from app.core.exceptions import NotFoundError, UserNotFoundError
from app.services.gym_service import GymService
from app.services.plan_service import PlanService
from app.services.membership_service import MembershipService
from app.services.announcement_service import AnnouncementService
from app.services.dashboard_service import DashboardService
from app.services.attendance_service import AttendanceService
from app.services.payment import PaymentService
from app.schemas.attendance import DailyAttendanceResponse
from datetime import date

router = APIRouter(prefix="/read", tags=["owners"])


def get_owner_gym(current_user: User, session: SessionDep) -> Optional[Gym]:
    """Helper function to get the gym owned by the current admin user"""
    stmt = select(Gym).where(Gym.owner_id == current_user.id)
    gym = session.exec(stmt).first()
    return gym


def _get_user_role_name(current_user: User, session: SessionDep) -> str:
    """Get the role name for a user from their role_id"""
    if not current_user.role_id:
        return ""
    stmt = select(Role).where(Role.id == current_user.role_id)
    role = session.exec(stmt).first()
    if not role:
        return ""
    return role.name


def get_user_gym_id(user: User, session: SessionDep) -> Optional[str]:
    """Get gym_id for the user (member gets their gym, owner gets their owned gym)"""
    if user.gym_id:
        return user.gym_id

    # If user is owner/admin, get their owned gym
    gym = get_owner_gym(user, session)
    if gym:
        return gym.id

    return None


def get_active_og_plan_for_gym(gym_id: str, session: SessionDep) -> Optional[OGPlanInfoResponse]:
    """Get active OG Plan information for a gym"""
    from app.models.gym_subscription import GymSubscription, SubscriptionStatus

    if not gym_id:
        return None

    today = date.today()
    subscription_stmt = select(GymSubscription).where(
        and_(
            GymSubscription.gym_id == gym_id,
            GymSubscription.status == SubscriptionStatus.ACTIVE,
            GymSubscription.end_date >= today
        )
    ).order_by(GymSubscription.end_date.desc())
    active_subscription = session.exec(subscription_stmt).first()

    if not active_subscription:
        return None

    # Get OG Plan details
    from app.models.og_plan import OGPlan
    og_plan_stmt = select(OGPlan).where(OGPlan.id == active_subscription.og_plan_id)
    og_plan = session.exec(og_plan_stmt).first()

    if not og_plan:
        return None

    return OGPlanInfoResponse(
        og_plan_id=og_plan.id,
        og_plan_name=og_plan.name,
        og_plan_end_date=active_subscription.end_date.isoformat(),
        og_plan_status=active_subscription.status.value
    )


@router.get("/profile", response_model=APIResponse[UserResponse])
def get_profile(
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    user_service = UserService(session=session)
    user_data = user_service.get_user(current_user.id)

    # OG Plan only for ADMIN
    if user_data.role_name == RoleEnum.ADMIN.value and user_data.gym_id:
        og_plan_info = get_active_og_plan_for_gym(user_data.gym_id, session)
        user_data.og_plan = og_plan_info

    return success_response(
        data=user_data,
        message="Profile fetched successfully"
    )


@router.get("/members", response_model=APIResponse[MemberListResponse], status_code=status.HTTP_200_OK)
def get_all_members(
    search: Optional[str] = Query(None, description="Search by name or email"),
    status: Optional[str] = Query("all", description="Filter by status: all, active, expired, new_joins, payment_pending"),
    sort_by: Optional[str] = Query("name_asc", description="Sort by: name_asc, name_desc, newest_joiners, plan_expiry_soonest"),
    pending_fees: Optional[bool] = Query(None, description="Filter members with pending/overdue fees"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get all members for the owner's gym with filtering, sorting, and pagination"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None
        )

    user_service = UserService(session=session)
    members_data = user_service.get_all_members(
        gym_id=gym.id,
        search=search,
        status=status,
        sort_by=sort_by,
        pending_fees=pending_fees,
        page=page,
        page_size=page_size
    )
    return success_response(data=members_data, message="Members fetched successfully")


@router.get("/pending-payments", response_model=APIResponse[PendingPaymentListResponse], status_code=status.HTTP_200_OK)
def get_pending_payments(
    filter_status: Optional[str] = Query("pending", description="Filter by status: all, approved, rejected, pending"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get payments for approval with pagination and status filtering"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )

    payment_service = PaymentService(session=session)
    pending_payments = payment_service.get_pending_payments(
        gym_id=gym.id,
        filter_status=filter_status,
        page=page,
        page_size=page_size
    )

    return success_response(
        data=pending_payments,
        message="Payments fetched successfully"
    )

@router.get(
    "/revenue",
    response_model=APIResponse[GymRevenueResponse],
    status_code=status.HTTP_200_OK
)
def get_gym_revenue(
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    session: SessionDep = None,
    current_user: User = require_admin
):
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )

    start_d = date.fromisoformat(start_date) if start_date else None
    end_d = date.fromisoformat(end_date) if end_date else None

    payment_service = PaymentService(session=session)
    revenue = payment_service.get_gym_revenue(
        gym_id=gym.id,
        start_date=start_d,
        end_date=end_d
    )

    return success_response(
        data=revenue,
        message="Revenue fetched successfully"
    )


@router.get("/dashboard", response_model=APIResponse[DashboardKPIsResponse], status_code=status.HTTP_200_OK)
def get_dashboard_kpis(
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Fetch key gym metrics (active members, check-ins, etc.)"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None
        )
    # Get role name from database
    stmt = select(Role).where(Role.id == current_user.role_id)
    role = session.exec(stmt).first()
    if not role:
        return failure_response(
            message="User role not found",
            data=None
        )
    role_enum = RoleEnum(role.name)

    dashboard_service = DashboardService(session=session)
    kpis_data = dashboard_service.get_user_kpis(
        user_id=current_user.id,
        role=role_enum,
        gym_id=gym.id
    )
    return success_response(data=kpis_data, message="Dashboard KPIs fetched successfully")


@router.get("/gym", response_model=APIResponse[GymResponse], status_code=status.HTTP_200_OK)
def get_owner_gym_info(
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get owner's gym information"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None
        )
    gym_service = GymService(session=session)
    gym_data = gym_service.get_gym(gym.id)
    return success_response(data=gym_data, message="Gym information fetched successfully")


@router.get("/members/{member_id}", response_model=APIResponse[MemberDetailResponse], status_code=status.HTTP_200_OK)
def get_member_detail(
    member_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get detailed member information with current plan"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None
        )

    user_service = UserService(session=session)
    try:
        member_detail = user_service.get_member_detail(member_id, gym.id)
        return success_response(data=member_detail, message="Member details fetched successfully")
    except UserNotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "Member not found",
            data=None
        )


@router.get("/available-members", response_model=APIResponse[AvailableMembersListResponse], status_code=status.HTTP_200_OK)
def get_available_members(
    query: Optional[str] = Query(None, description="Search across name, email, phone, and username"),
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get list of available members (not assigned to any gym). Search across all fields with a single query parameter."""
    user_service = UserService(session=session)
    members_data = user_service.get_available_members(query=query)
    return success_response(data=members_data, message="Available members fetched successfully")


@router.get("/staff/{staff_id}", response_model=APIResponse[UserResponse], status_code=status.HTTP_200_OK)
def get_staff(
    staff_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get a staff member by ID"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None
        )
    user_service = UserService(session=session)
    staff = user_service.get_user(staff_id)

    if staff.gym_id != gym.id or staff.role != "STAFF":
        return failure_response(
            message="Staff not found in your gym",
            data=None
        )

    return success_response(data=staff, message="Staff data fetched successfully")


@router.get("/trainers/{trainer_id}", response_model=APIResponse[UserResponse], status_code=status.HTTP_200_OK)
def get_trainer(
    trainer_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get a trainer by ID"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None
        )
    user_service = UserService(session=session)
    trainer = user_service.get_user(trainer_id)

    if trainer.gym_id != gym.id or trainer.role != "TRAINER":
        return failure_response(
            message="Trainer not found in your gym",
            data=None
        )

    return success_response(data=trainer, message="Trainer data fetched successfully")


@router.get("/plans/{plan_id}", response_model=APIResponse[PlanResponse], status_code=status.HTTP_200_OK)
def get_plan(
    plan_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get a plan by ID"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None
        )
    plan_service = PlanService(session=session)
    plan = plan_service.get_plan(plan_id)

    if plan.gym_id != gym.id:
        return failure_response(
            message="Plan not found in your gym",
            data=None
        )

    return success_response(data=plan, message="Plan fetched successfully")


@router.get("/plans", response_model=APIResponse[PlanListResponse], status_code=status.HTTP_200_OK)
def get_all_plans(
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get all plans for the owner's gym"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None
        )

    plan_service = PlanService(session=session)
    plans_data = plan_service.get_all_plans(gym_id=gym.id)
    return success_response(data=plans_data, message="Plans fetched successfully")


@router.get("/rules", response_model=APIResponse[GymRuleListResponse], status_code=status.HTTP_200_OK)
def get_all_gym_rules(
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get all gym rules for the owner's gym"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None
        )

    gym_service = GymService(session=session)
    rules_data = gym_service.get_all_gym_rules(gym_id=gym.id)
    return success_response(data=rules_data, message="Gym rules fetched successfully")


@router.get("/attendance", response_model=APIResponse[DailyAttendanceResponse], status_code=status.HTTP_200_OK)
def get_daily_attendance(
    target_date: Optional[str] = Query(
        None,
        description="Date in YYYY-MM-DD format. Defaults to today if not provided."
    ),
    filter_status: Optional[str] = Query(
        None,
        description="Filter by status: 'present', 'absent', or None for all",
        pattern="^(present|absent)$"
    ),
    search: Optional[str] = Query(
        None,
        description="Search by member name or username"
    ),
    session: SessionDep = None,
    current_user: User = require_admin
):
    """
    Get daily attendance for the owner's gym with date query, filtering, and search.

    Query Parameters:
    - target_date: Date in YYYY-MM-DD format (defaults to today)
    - filter_status: 'present' or 'absent' to filter members (optional)
    - search: Search query for member name or username (optional)
    """
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )

    # Parse target_date or use today
    if target_date:
        try:
            query_date = date.fromisoformat(target_date)
        except ValueError:
            return failure_response(
                message="Invalid date format. Use YYYY-MM-DD",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
    else:
        query_date = date.today()

    attendance_service = AttendanceService(session=session)
    try:
        attendance_data = attendance_service.get_daily_attendance(
            gym_id=gym.id,
            target_date=query_date,
            filter_status=filter_status,
            search_query=search
        )
        return success_response(
            data=attendance_data,
            message="Daily attendance fetched successfully"
        )
    except NotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else str(e),
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )


@router.get("/rules/{rule_id}", response_model=APIResponse[GymRuleResponse], status_code=status.HTTP_200_OK)
def get_gym_rule(
    rule_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get a gym rule by ID"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None
        )

    gym_service = GymService(session=session)
    rule = gym_service.get_gym_rule(rule_id)

    if rule.gym_id != gym.id:
        return failure_response(
            message="Rule not found in your gym",
            data=None
        )

    return success_response(data=rule, message="Gym rule fetched successfully")


@router.get("/memberships/{membership_id}", response_model=APIResponse[MembershipResponse], status_code=status.HTTP_200_OK)
def get_membership(
    membership_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get a membership by ID"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None
        )
    membership_service = MembershipService(session=session)
    membership = membership_service.get_membership(membership_id)

    if membership.gym_id != gym.id:
        return failure_response(
            message="Membership not found in your gym",
            data=None
        )

    return success_response(data=membership, message="Membership fetched successfully")


@router.get("/announcements", response_model=APIResponse[AnnouncementListResponse], status_code=status.HTTP_200_OK)
def get_announcements(
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get announcements relevant to the logged-in user (user-specific filtering)."""
    announcement_service = AnnouncementService(session=session)
    announcements = announcement_service.get_announcements_for_user(current_user=current_user)
    announcements_data = AnnouncementListResponse(announcements=announcements)
    return success_response(data=announcements_data, message="Announcements fetched successfully")
