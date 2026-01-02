from typing import Optional
from datetime import date, datetime
from sqlmodel import select, func, and_
from app.db.db import SessionDep
from app.models.user import Role
from app.models.membership import Membership
from app.models.attendance import Attendance
from app.models.billing import Payment
from app.schemas.dashboard import DashboardKPIsResponse


class DashboardService:

    def __init__(self, session: SessionDep):
        self.session = session

    def get_user_kpis(
        self,
        user_id: str,
        role: Role,
        gym_id: Optional[str]
    ) -> DashboardKPIsResponse:
        """
        Main method to get KPIs based on user role.
        
        Logic:
        - ADMIN (Gym Owner): Gets full gym KPIs (all 4 metrics)
        - MEMBER: Gets personal stats (their own check-ins, check-outs, fee status)
        - STAFF/TRAINER: Gets limited gym stats (check-ins, check-outs only)
        - OG: Can see all gyms (but for now, same as ADMIN if they have a gym_id)
        
        Returns DashboardKPIsResponse with role-appropriate data.
        """
        if role == Role.ADMIN:
            return self._get_admin_kpis(gym_id)
        elif role == Role.MEMBER:
            return self._get_member_kpis(user_id, gym_id)
        elif role in [Role.STAFF, Role.TRAINER]:
            return self._get_staff_kpis(gym_id)
        else:
            # OG or other roles - default to admin if gym_id exists
            if gym_id:
                return self._get_admin_kpis(gym_id)
            else:
                # Return empty/default KPIs
                return DashboardKPIsResponse(
                    active_members=0,
                    total_check_ins_today=0,
                    total_check_outs_today=0,
                    total_fee_due_members=0
                )

    def _get_admin_kpis(self, gym_id: Optional[str]) -> DashboardKPIsResponse:
        """Get KPIs for ADMIN (Gym Owner) role - full gym statistics"""
        if not gym_id:
            return DashboardKPIsResponse(
                active_members=0,
                total_check_ins_today=0,
                total_check_outs_today=0,
                total_fee_due_members=0
            )
        
        today = date.today()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        # 1. Active members: Count memberships that are active and not expired
        active_members_stmt = select(func.count(Membership.id)).where(
            and_(
                Membership.gym_id == gym_id,
                Membership.status == "active",
                Membership.start_date <= today,
                Membership.end_date >= today
            )
        )
        active_members = self.session.exec(active_members_stmt).first() or 0
        
        # 2. Total check-ins today
        check_ins_stmt = select(func.count(Attendance.id)).where(
            and_(
                Attendance.gym_id == gym_id,
                Attendance.check_in_at >= start_of_day,
                Attendance.check_in_at <= end_of_day
            )
        )
        total_check_ins_today = self.session.exec(check_ins_stmt).first() or 0
        
        # 3. Total check-outs today
        check_outs_stmt = select(func.count(Attendance.id)).where(
            and_(
                Attendance.gym_id == gym_id,
                Attendance.check_out_at.isnot(None),
                Attendance.check_out_at >= start_of_day,
                Attendance.check_out_at <= end_of_day
            )
        )
        total_check_outs_today = self.session.exec(check_outs_stmt).first() or 0
        
        # 4. Total fee due members: Count distinct users with pending payments
        fee_due_stmt = select(func.count(func.distinct(Payment.user_id))).where(
            and_(
                Payment.gym_id == gym_id,
                Payment.status == "pending"
            )
        )
        total_fee_due_members = self.session.exec(fee_due_stmt).first() or 0
        
        return DashboardKPIsResponse(
            active_members=active_members,
            total_check_ins_today=total_check_ins_today,
            total_check_outs_today=total_check_outs_today,
            total_fee_due_members=total_fee_due_members
        )

    def _get_member_kpis(self, user_id: str, gym_id: Optional[str]) -> DashboardKPIsResponse:
        """Get KPIs for MEMBER role - personal statistics only"""
        today = date.today()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        # 1. Active members: Return 0 (members don't see gym-wide stats)
        active_members = 0
        
        # 2. Total check-ins today: Count user's own check-ins
        check_ins_stmt = select(func.count(Attendance.id)).where(
            and_(
                Attendance.user_id == user_id,
                Attendance.check_in_at >= start_of_day,
                Attendance.check_in_at <= end_of_day
            )
        )
        total_check_ins_today = self.session.exec(check_ins_stmt).first() or 0
        
        # 3. Total check-outs today: Count user's own check-outs
        check_outs_stmt = select(func.count(Attendance.id)).where(
            and_(
                Attendance.user_id == user_id,
                Attendance.check_out_at.isnot(None),
                Attendance.check_out_at >= start_of_day,
                Attendance.check_out_at <= end_of_day
            )
        )
        total_check_outs_today = self.session.exec(check_outs_stmt).first() or 0
        
        # 4. Total fee due members: Check if user has any pending payments
        fee_due_stmt = select(Payment).where(
            and_(
                Payment.user_id == user_id,
                Payment.status == "pending"
            )
        )
        has_pending_fees = self.session.exec(fee_due_stmt).first() is not None
        total_fee_due_members = 1 if has_pending_fees else 0
        
        return DashboardKPIsResponse(
            active_members=active_members,
            total_check_ins_today=total_check_ins_today,
            total_check_outs_today=total_check_outs_today,
            total_fee_due_members=total_fee_due_members
        )

    def _get_staff_kpis(self, gym_id: Optional[str]) -> DashboardKPIsResponse:
        """Get KPIs for STAFF/TRAINER role - limited gym statistics"""
        if not gym_id:
            return DashboardKPIsResponse(
                active_members=0,
                total_check_ins_today=0,
                total_check_outs_today=0,
                total_fee_due_members=0
            )
        
        today = date.today()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        # 1. Active members: Return 0 (staff don't see member count)
        active_members = 0
        
        # 2. Total check-ins today: Same as admin
        check_ins_stmt = select(func.count(Attendance.id)).where(
            and_(
                Attendance.gym_id == gym_id,
                Attendance.check_in_at >= start_of_day,
                Attendance.check_in_at <= end_of_day
            )
        )
        total_check_ins_today = self.session.exec(check_ins_stmt).first() or 0
        
        # 3. Total check-outs today: Same as admin
        check_outs_stmt = select(func.count(Attendance.id)).where(
            and_(
                Attendance.gym_id == gym_id,
                Attendance.check_out_at.isnot(None),
                Attendance.check_out_at >= start_of_day,
                Attendance.check_out_at <= end_of_day
            )
        )
        total_check_outs_today = self.session.exec(check_outs_stmt).first() or 0
        
        # 4. Total fee due members: Return 0 (staff don't see financial info)
        total_fee_due_members = 0
        
        return DashboardKPIsResponse(
            active_members=active_members,
            total_check_ins_today=total_check_ins_today,
            total_check_outs_today=total_check_outs_today,
            total_fee_due_members=total_fee_due_members
        )

