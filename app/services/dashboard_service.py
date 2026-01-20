from typing import Optional, List
from datetime import date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo
from sqlmodel import select, func, and_, or_
from app.db.db import SessionDep
from app.models.user import Role, User
from app.models.role import Role as RoleModel
from app.models.membership import Membership
from app.models.attendance import Attendance
from app.models.payments import Payment
from app.schemas.dashboard import DashboardKPIsResponse, DailyAttendanceResponse


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
                    total_fee_due_members=0,
                    absent_today_count=0,
                    present_percentage=0.0,
                    present_today_trend_percentage=0.0,
                    total_fees_received_amount=Decimal("0.0"),
                    total_fees_received_members_count=0,
                    total_fees_pending_amount=Decimal("0.0"),
                    paid_percentage=0.0,
                    unpaid_percentage=0.0
                )

    def _get_admin_kpis(self, gym_id: Optional[str]) -> DashboardKPIsResponse:
        """Get KPIs for ADMIN (Gym Owner) role - full gym statistics"""
        if not gym_id:
            return DashboardKPIsResponse(
                active_members=0,
                total_check_ins_today=0,
                total_check_outs_today=0,
                total_fee_due_members=0,
                absent_today_count=0,
                present_percentage=0.0,
                present_today_trend_percentage=0.0,
                total_fees_received_amount=Decimal("0.0"),
                total_fees_received_members_count=0,
                total_fees_pending_amount=Decimal("0.0"),
                paid_percentage=0.0,
                unpaid_percentage=0.0
            )
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        start_of_yesterday = datetime.combine(yesterday, datetime.min.time())
        end_of_yesterday = datetime.combine(yesterday, datetime.max.time())
        
        # 1. Active members: Count total members (users with role MEMBER) in the gym
        # First, get the MEMBER role id
        member_role_stmt = select(RoleModel).where(RoleModel.name == "MEMBER")
        member_role = self.session.exec(member_role_stmt).first()
        
        if member_role:
            active_members_stmt = select(func.count(User.id)).where(
                and_(
                    User.gym_id == gym_id,
                    User.role_id == member_role.id,
                    User.is_active == True
                )
            )
            active_members = self.session.exec(active_members_stmt).first() or 0
        else:
            active_members = 0
        
        # 2. Total check-ins today
        check_ins_stmt = select(func.count(Attendance.id)).where(
            and_(
                Attendance.gym_id == gym_id,
                Attendance.check_in_at >= start_of_day,
                Attendance.check_in_at <= end_of_day
            )
        )
        total_check_ins_today = self.session.exec(check_ins_stmt).first() or 0
        
        # 3. Total check-ins yesterday (for trend calculation)
        check_ins_yesterday_stmt = select(func.count(Attendance.id)).where(
            and_(
                Attendance.gym_id == gym_id,
                Attendance.check_in_at >= start_of_yesterday,
                Attendance.check_in_at <= end_of_yesterday
            )
        )
        total_check_ins_yesterday = self.session.exec(check_ins_yesterday_stmt).first() or 0
        
        # 4. Total check-outs today
        check_outs_stmt = select(func.count(Attendance.id)).where(
            and_(
                Attendance.gym_id == gym_id,
                Attendance.check_out_at.isnot(None),
                Attendance.check_out_at >= start_of_day,
                Attendance.check_out_at <= end_of_day
            )
        )
        total_check_outs_today = self.session.exec(check_outs_stmt).first() or 0
        
        # 5. Total fee due members: Count distinct users with pending payments
        fee_due_stmt = select(func.count(func.distinct(Payment.user_id))).where(
            and_(
                Payment.gym_id == gym_id,
                Payment.status == "pending"
            )
        )
        total_fee_due_members = self.session.exec(fee_due_stmt).first() or 0
        
        # 6. Attendance Overview - Additional metrics
        absent_today_count = max(0, active_members - total_check_ins_today)
        present_percentage = (total_check_ins_today / active_members * 100) if active_members > 0 else 0.0
        
        # Calculate trend percentage: ((today - yesterday) / yesterday) * 100
        if total_check_ins_yesterday > 0:
            present_today_trend_percentage = ((total_check_ins_today - total_check_ins_yesterday) / total_check_ins_yesterday) * 100
        elif total_check_ins_today > 0:
            present_today_trend_percentage = 100.0  # 100% increase from 0
        else:
            present_today_trend_percentage = 0.0
        
        # 7. Fees & Revenue - Additional metrics
        # Total fees received: Sum of payments with status "paid" or "completed" or "verified"
        received_payments_stmt = select(func.sum(Payment.amount)).where(
            and_(
                Payment.gym_id == gym_id,
                or_(
                    Payment.status == "paid",
                    Payment.status == "completed",
                    Payment.status == "verified"
                )
            )
        )
        total_fees_received_amount = self.session.exec(received_payments_stmt).first() or Decimal("0.0")
        if total_fees_received_amount is None:
            total_fees_received_amount = Decimal("0.0")
        
        # Count distinct members who paid
        received_members_stmt = select(func.count(func.distinct(Payment.user_id))).where(
            and_(
                Payment.gym_id == gym_id,
                or_(
                    Payment.status == "paid",
                    Payment.status == "completed",
                    Payment.status == "verified"
                )
            )
        )
        total_fees_received_members_count = self.session.exec(received_members_stmt).first() or 0
        
        # Total fees pending: Sum of payments with status "pending"
        pending_payments_stmt = select(func.sum(Payment.amount)).where(
            and_(
                Payment.gym_id == gym_id,
                Payment.status == "pending"
            )
        )
        total_fees_pending_amount = self.session.exec(pending_payments_stmt).first() or Decimal("0.0")
        if total_fees_pending_amount is None:
            total_fees_pending_amount = Decimal("0.0")
        
        # Calculate paid/unpaid percentages
        total_expected_amount = total_fees_received_amount + total_fees_pending_amount
        if total_expected_amount > 0:
            paid_percentage = (float(total_fees_received_amount) / float(total_expected_amount)) * 100
            unpaid_percentage = (float(total_fees_pending_amount) / float(total_expected_amount)) * 100
        else:
            paid_percentage = 0.0
            unpaid_percentage = 0.0
        
        return DashboardKPIsResponse(
            active_members=active_members,
            total_check_ins_today=total_check_ins_today,
            total_check_outs_today=total_check_outs_today,
            total_fee_due_members=total_fee_due_members,
            absent_today_count=absent_today_count,
            present_percentage=round(present_percentage, 2),
            present_today_trend_percentage=round(present_today_trend_percentage, 2),
            total_fees_received_amount=total_fees_received_amount,
            total_fees_received_members_count=total_fees_received_members_count,
            total_fees_pending_amount=total_fees_pending_amount,
            paid_percentage=round(paid_percentage, 2),
            unpaid_percentage=round(unpaid_percentage, 2)
        )

    def _get_member_kpis(self, user_id: str, gym_id: Optional[str]) -> DashboardKPIsResponse:
        """Get KPIs for MEMBER role - personal statistics only"""
        today = date.today()
        
        # Get user info
        user_stmt = select(User).where(User.id == user_id)
        user = self.session.exec(user_stmt).first()
        user_name = user.user_name if user else None
        name = user.name if user else None
        
        # Get membership expiry date and days remaining
        membership_expiry_date = None
        membership_days_remaining = None
        
        if gym_id:
            # Get active membership (status = 'active' and end_date >= today)
            membership_stmt = select(Membership).where(
                and_(
                    Membership.user_id == user_id,
                    Membership.gym_id == gym_id,
                    Membership.status == "active",
                    Membership.end_date >= today
                )
            ).order_by(Membership.end_date.asc())
            active_membership = self.session.exec(membership_stmt).first()
            
            if active_membership:
                expiry_date = active_membership.end_date
                membership_expiry_date = expiry_date.strftime("%d-%m-%Y")
                days_remaining = (expiry_date - today).days
                membership_days_remaining = max(0, days_remaining)
        
        # Get last 7 days attendance streak
        last_7_days_attendance = self._get_last_7_days_attendance(user_id)
        
        # Get daily quote based on day of month
        quote = self._get_daily_quote()
        
        # Get today's attendance record (check-in time, checkout time, focus)
        check_in_time = None
        checkout_time = None
        focus = None
        
        ist = ZoneInfo("Asia/Kolkata")
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=ist)
        today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=ist)
        
        today_attendance_stmt = select(Attendance).where(
            and_(
                Attendance.user_id == user_id,
                Attendance.check_in_at >= today_start,
                Attendance.check_in_at <= today_end
            )
        ).order_by(Attendance.check_in_at.desc())
        
        today_attendance = self.session.exec(today_attendance_stmt).first()
        
        if today_attendance:
            # Format check-in time
            check_in_at = today_attendance.check_in_at
            if check_in_at.tzinfo is None:
                from datetime import timezone as tz
                check_in_at = check_in_at.replace(tzinfo=tz.utc).astimezone(ist)
            else:
                check_in_at = check_in_at.astimezone(ist)
            check_in_time = check_in_at.strftime("%d-%m-%Y %H:%M:%S")
            
            # Format checkout time if available
            if today_attendance.check_out_at:
                check_out_at = today_attendance.check_out_at
                if check_out_at.tzinfo is None:
                    from datetime import timezone as tz
                    check_out_at = check_out_at.replace(tzinfo=tz.utc).astimezone(ist)
                else:
                    check_out_at = check_out_at.astimezone(ist)
                checkout_time = check_out_at.strftime("%d-%m-%Y %H:%M:%S")
            
            # Get focus
            focus = today_attendance.focus
        
        return DashboardKPIsResponse(
            active_members=None,
            total_check_ins_today=None,
            total_check_outs_today=None,
            total_fee_due_members=None,
            absent_today_count=0,
            present_percentage=0.0,
            present_today_trend_percentage=0.0,
            total_fees_received_amount=Decimal("0.0"),
            total_fees_received_members_count=0,
            total_fees_pending_amount=Decimal("0.0"),
            paid_percentage=0.0,
            unpaid_percentage=0.0,
            user_name=user_name,
            name=name,
            membership_expiry_date=membership_expiry_date,
            membership_days_remaining=membership_days_remaining,
            last_7_days_attendance=last_7_days_attendance,
            quote=quote,
            check_in_time=check_in_time,
            checkout_time=checkout_time,
            focus=focus
        )
    
    def _get_last_7_days_attendance(self, user_id: str) -> List[DailyAttendanceResponse]:
        """Get last 7 days attendance streak with dates in Indian format"""
        today = date.today()
        attendance_list = []
        
        # Generate last 7 days (including today)
        for i in range(6, -1, -1):  # 6 days ago to today
            check_date = today - timedelta(days=i)
            date_str = check_date.strftime("%d-%m-%Y")
            
            # Check if user has attendance on this date
            start_of_day = datetime.combine(check_date, datetime.min.time())
            end_of_day = datetime.combine(check_date, datetime.max.time())
            
            attendance_stmt = select(Attendance).where(
                and_(
                    Attendance.user_id == user_id,
                    Attendance.check_in_at >= start_of_day,
                    Attendance.check_in_at <= end_of_day
                )
            )
            attendance_record = self.session.exec(attendance_stmt).first()
            
            status = "present" if attendance_record else "absent"
            attendance_list.append(
                DailyAttendanceResponse(date=date_str, status=status)
            )
        
        return attendance_list
    
    def _get_daily_quote(self) -> str:
        """Get motivational quote based on current day of the month"""
        QUOTES = {
            "1": "Sweat today, shine tomorrow.",
            "2": "No pain, no gain.",
            "3": "Push harder than yesterday.",
            "4": "Your body can stand almost anything. It's your mind you have to convince.",
            "5": "Strength grows in the moments you think you can't go on.",
            "6": "Lift heavy, love lightly.",
            "7": "Train insane or remain the same.",
            "8": "The gym is my therapy.",
            "9": "Beast mode: ON.",
            "10": "Muscles are earned, not given.",
            "11": "One more rep, one more dream.",
            "12": "Grind now, glow later.",
            "13": "Weights before dates.",
            "14": "Pain is temporary, pride is forever.",
            "15": "Build your body, build your future.",
            "16": "Sweat is fat crying.",
            "17": "Champions train, losers complain.",
            "18": "Every rep counts.",
            "19": "Rise and grind.",
            "20": "Stronger every day.",
            "21": "Fuel your hustle.",
            "22": "Earn your body.",
            "23": "No excuses, just results.",
            "24": "Lift, laugh, repeat.",
            "25": "Progress over perfection.",
            "26": "Iron sharpens iron.",
            "27": "Conquer from within.",
            "28": "Flex on them haters.",
            "29": "Workout because you love your body.",
            "30": "Dream big, lift bigger.",
            "31": "Unleash the beast."
        }
        
        day_of_month = date.today().day
        quote_key = str(day_of_month)
        return QUOTES.get(quote_key, QUOTES["1"])

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
            total_fee_due_members=total_fee_due_members,
            absent_today_count=0,
            present_percentage=0.0,
            present_today_trend_percentage=0.0,
            total_fees_received_amount=Decimal("0.0"),
            total_fees_received_members_count=0,
            total_fees_pending_amount=Decimal("0.0"),
            paid_percentage=0.0,
            unpaid_percentage=0.0
        )

