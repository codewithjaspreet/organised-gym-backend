from datetime import datetime
from sqlmodel import select
from app.core.exceptions import NotFoundError
from app.db.db import SessionDep
from app.models.attendance import Attendance
from app.schemas.attendance import (
    AttendanceCheckInRequest,
    AttendanceCheckInResponse,
    AttendanceCheckOutRequest,
    AttendanceCheckOutResponse
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
