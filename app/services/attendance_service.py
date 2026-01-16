from datetime import datetime, date
from zoneinfo import ZoneInfo
from sqlmodel import select, and_, func, or_
from typing import List, Optional
from app.core.exceptions import NotFoundError
from app.db.db import SessionDep
from app.models.attendance import Attendance
from app.models.gym import Gym
from app.models.user import User
from app.models.role import Role as RoleModel
from app.schemas.attendance import (
    AttendanceCheckInRequest,
    AttendanceCheckInResponse,
    AttendanceCheckOutRequest,
    AttendanceCheckOutResponse,
    MarkAttendanceRequest,
    MarkAttendanceResponse,
    CheckoutRequest,
    CheckoutResponse,
    ActiveCheckInStatusResponse,
    DailyAttendanceResponse,
    DailyAttendanceSummary,
    MemberAttendanceItem
)


class AttendanceService:

    def __init__(self, session: SessionDep):
        self.session = session

    def create_check_in(self, attendance: AttendanceCheckInRequest) -> AttendanceCheckInResponse:
        """Create a check-in record"""
        # Parse the check_in_time string to datetime
        try:
            check_in_datetime = datetime.fromisoformat(attendance.check_in_time)
        except ValueError:
            # If ISO format fails, try parsing as string
            check_in_datetime = datetime.strptime(attendance.check_in_time, "%Y-%m-%d %H:%M:%S")
        
        db_attendance = Attendance(
            user_id=attendance.user_id,
            gym_id=attendance.gym_id,
            check_in_at=check_in_datetime,
            check_out_at=None
        )
        self.session.add(db_attendance)
        self.session.commit()
        self.session.refresh(db_attendance)
        
        return AttendanceCheckInResponse(
            id=db_attendance.id,
            user_id=db_attendance.user_id,
            check_in_time=db_attendance.check_in_at.isoformat(),
            gym_id=db_attendance.gym_id,
            created_at=db_attendance.check_in_at,
            updated_at=db_attendance.check_in_at
        )

    def create_check_out(self, attendance: AttendanceCheckOutRequest) -> AttendanceCheckOutResponse:
        """Create or update a check-out record"""
        # Parse the check_out_time string to datetime
        try:
            check_out_datetime = datetime.fromisoformat(attendance.check_out_time)
        except ValueError:
            # If ISO format fails, try parsing as string
            check_out_datetime = datetime.strptime(attendance.check_out_time, "%Y-%m-%d %H:%M:%S")
        
        # Find the most recent check-in for this user at this gym without a check-out
        stmt = select(Attendance).where(
            Attendance.user_id == attendance.user_id,
            Attendance.gym_id == attendance.gym_id,
            Attendance.check_out_at.is_(None)
        ).order_by(Attendance.check_in_at.desc())
        
        db_attendance = self.session.exec(stmt).first()
        
        if not db_attendance:
            raise NotFoundError(
                detail=f"No active check-in found for user {attendance.user_id} at gym {attendance.gym_id}"
            )
        
        # Update the check-out time
        db_attendance.check_out_at = check_out_datetime
        self.session.commit()
        self.session.refresh(db_attendance)
        
        return AttendanceCheckOutResponse(
            id=db_attendance.id,
            user_id=db_attendance.user_id,
            check_out_time=db_attendance.check_out_at.isoformat() if db_attendance.check_out_at else None,
            gym_id=db_attendance.gym_id,
            created_at=db_attendance.check_in_at
        )

    def get_attendance_by_id(self, attendance_id: str) -> Attendance:
        """Get a single attendance record by ID"""
        stmt = select(Attendance).where(Attendance.id == attendance_id)
        attendance = self.session.exec(stmt).first()
        if not attendance:
            raise NotFoundError(detail=f"Attendance with id {attendance_id} not found")
        
        return attendance

    def mark_attendance(
        self, 
        user_id: str, 
        request: MarkAttendanceRequest
    ) -> MarkAttendanceResponse:
        """Mark attendance for a member - validates gym membership and gym code"""
        # Check if member belongs to the gym
        from app.models.user import User
        stmt = select(User).where(User.id == user_id)
        user = self.session.exec(stmt).first()
        
        if not user:
            raise NotFoundError(detail="User not found")
        
        if user.gym_id != request.gym_id:
            raise NotFoundError(detail="Member does not belong to this gym")
        
        # Check if gym exists and verify gym_code
        stmt = select(Gym).where(Gym.id == request.gym_id)
        gym = self.session.exec(stmt).first()
        
        if not gym:
            raise NotFoundError(detail="Gym not found")
        
        if gym.gym_code != request.gym_code:
            raise NotFoundError(detail="Invalid gym code")
        
        # Create attendance record with current datetime
        check_in_time = datetime.now(ZoneInfo("Asia/Kolkata"))
        
        db_attendance = Attendance(
            user_id=user_id,
            gym_id=request.gym_id,
            check_in_at=check_in_time,
            check_out_at=None,
            focus=request.today_focus
        )
        self.session.add(db_attendance)
        self.session.commit()
        self.session.refresh(db_attendance)
        
        # Format time in Indian format (24hr clock): DD-MM-YYYY HH:MM:SS
        formatted_time = check_in_time.strftime("%d-%m-%Y %H:%M:%S")
        
        return MarkAttendanceResponse(
            focus=request.today_focus,
            checked_in_time=formatted_time
        )

    def checkout(
        self,
        user_id: str
    ) -> CheckoutResponse:
        """Checkout a member - finds their active check-in and marks checkout"""
        # Find the most recent check-in for this user without a check-out
        stmt = select(Attendance).where(
            Attendance.user_id == user_id,
            Attendance.check_out_at.is_(None)
        ).order_by(Attendance.check_in_at.desc())
        
        db_attendance = self.session.exec(stmt).first()
        
        if not db_attendance:
            raise NotFoundError(detail="No active check-in found. Please check in first.")
        
        # Set check-out time to current datetime (IST)
        check_out_time = datetime.now(ZoneInfo("Asia/Kolkata"))
        db_attendance.check_out_at = check_out_time
        self.session.commit()
        self.session.refresh(db_attendance)
        
        # Convert check_in_at to IST timezone-aware for consistent formatting
        # Database might store it as UTC or naive, so we need to handle both cases
        check_in_at = db_attendance.check_in_at
        if check_in_at.tzinfo is None:
            # If naive, assume it's stored as UTC in database and convert to IST
            # IST is UTC+5:30
            from datetime import timezone, timedelta
            utc_time = check_in_at.replace(tzinfo=timezone.utc)
            check_in_at = utc_time.astimezone(ZoneInfo("Asia/Kolkata"))
        else:
            # If timezone-aware, convert to IST
            check_in_at = check_in_at.astimezone(ZoneInfo("Asia/Kolkata"))
        
        # Calculate workout duration (both should be timezone-aware now)
        duration = check_out_time - check_in_at
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Format times in Indian format (24hr clock): DD-MM-YYYY HH:MM:SS
        # Both are now in IST timezone
        check_in_formatted = check_in_at.strftime("%d-%m-%Y %H:%M:%S")
        check_out_formatted = check_out_time.strftime("%d-%m-%Y %H:%M:%S")
        
        return CheckoutResponse(
            checked_in_time=check_in_formatted,
            checked_out_time=check_out_formatted,
            total_workout_duration=duration_str,
            focus=db_attendance.focus
        )

    def has_active_checkin(self, user_id: str) -> ActiveCheckInStatusResponse:
        """Check if member has an active check-in (checked in but not checked out)"""
        stmt = select(Attendance).where(
            Attendance.user_id == user_id,
            Attendance.check_out_at.is_(None)
        ).order_by(Attendance.check_in_at.desc())
        
        db_attendance = self.session.exec(stmt).first()
        has_active = db_attendance is not None
        
        return ActiveCheckInStatusResponse(has_active_checkin=has_active)

    def get_daily_attendance(
        self,
        gym_id: str,
        target_date: date,
        filter_status: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> DailyAttendanceResponse:
        """
        Get daily attendance for a gym with filtering and search.
        
        Args:
            gym_id: The gym ID
            target_date: The date to query attendance for
            filter_status: Optional filter - 'present', 'absent', or None (all)
            search_query: Optional search query to filter by member name or username
        
        Returns:
            DailyAttendanceResponse with summary and member list
        """
        # Get all members of the gym
        member_role_stmt = select(RoleModel).where(RoleModel.name == "MEMBER")
        member_role = self.session.exec(member_role_stmt).first()
        
        if not member_role:
            raise NotFoundError(detail="MEMBER role not found")
        
        # Build member query
        member_stmt = select(User).where(
            and_(
                User.gym_id == gym_id,
                User.role_id == member_role.id,
                User.is_active == True
            )
        )
        
        # Apply search filter if provided
        if search_query:
            search_pattern = f"%{search_query.lower()}%"
            member_stmt = member_stmt.where(
                or_(
                    func.lower(User.name).like(search_pattern),
                    func.lower(User.user_name).like(search_pattern)
                )
            )
        
        all_members = self.session.exec(member_stmt).all()
        total_members = len(all_members)
        
        # Calculate date range for the target date (IST timezone)
        ist = ZoneInfo("Asia/Kolkata")
        start_of_day_ist = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=ist)
        end_of_day_ist = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=ist)
        
        # Convert to UTC for database query (if database stores in UTC)
        # Or use naive datetime if database stores as-is
        start_of_day = start_of_day_ist
        end_of_day = end_of_day_ist
        
        # Get all attendance records for this date and gym
        attendance_stmt = select(Attendance).where(
            and_(
                Attendance.gym_id == gym_id,
                Attendance.check_in_at >= start_of_day,
                Attendance.check_in_at <= end_of_day
            )
        )
        
        attendance_records = self.session.exec(attendance_stmt).all()
        
        # Create a map of user_id -> attendance record for quick lookup
        attendance_map = {record.user_id: record for record in attendance_records}
        
        # Build member attendance list
        member_attendance_list: List[MemberAttendanceItem] = []
        present_count = 0
        absent_count = 0
        
        for member in all_members:
            attendance_record = attendance_map.get(member.id)
            is_present = attendance_record is not None
            
            # Apply status filter
            if filter_status == "present" and not is_present:
                continue
            if filter_status == "absent" and is_present:
                continue
            
            # Format check-in time if present
            check_in_time_str = None
            focus = None
            
            if attendance_record:
                # Convert check_in_at to IST for formatting
                check_in_at = attendance_record.check_in_at
                if check_in_at.tzinfo is None:
                    # Assume UTC if naive
                    from datetime import timezone as tz
                    check_in_at = check_in_at.replace(tzinfo=tz.utc).astimezone(ist)
                else:
                    check_in_at = check_in_at.astimezone(ist)
                
                check_in_time_str = check_in_at.strftime("%d-%m-%Y %H:%M:%S")
                focus = attendance_record.focus
                present_count += 1
            else:
                absent_count += 1
            
            member_attendance_list.append(
                MemberAttendanceItem(
                    user_id=member.id,
                    name=member.name,
                    user_name=member.user_name,
                    photo_url=member.photo_url,
                    check_in_time=check_in_time_str,
                    focus=focus,
                    status="present" if is_present else "absent"
                )
            )
        
        # Sort by status (present first) then by check-in time
        member_attendance_list.sort(
            key=lambda x: (
                0 if x.status == "present" else 1,
                x.check_in_time if x.check_in_time else ""
            ),
            reverse=True
        )
        
        # Format date
        date_str = target_date.strftime("%d-%m-%Y")
        
        summary = DailyAttendanceSummary(
            date=date_str,
            present_count=present_count,
            absent_count=absent_count,
            total_members=total_members
        )
        
        return DailyAttendanceResponse(
            summary=summary,
            members=member_attendance_list
        )
