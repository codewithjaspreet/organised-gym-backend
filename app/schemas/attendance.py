from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional


class AttendanceCheckInRequest(BaseModel):
    user_id: str = Field(description="The user id")
    check_in_time : str = Field(description="The user check in time")
    gym_id: str = Field(description="The gym id")


class AttendanceCheckInResponse(BaseModel):
    id: str = Field(description="The attendance id")
    user_id: str = Field(description="The user id")
    check_in_time : str = Field(description="The user check in time")
    gym_id: str = Field(description="The gym id")
    created_at: datetime = Field(description="The attendance creation date")
    updated_at: datetime = Field(description="The attendance update date")


class AttendanceCheckOutRequest(BaseModel):
    user_id: str = Field(description="The user id")
    check_out_time : str = Field(description="The user check out time")
    gym_id: str = Field(description="The gym id")


class AttendanceCheckOutResponse(BaseModel):
    id: str = Field(description="The attendance id")
    user_id: str = Field(description="The user id")
    check_out_time : str = Field(description="The user check out time")
    gym_id: str = Field(description="The gym id")
    created_at: datetime = Field(description="The attendance creation date")


class MarkAttendanceRequest(BaseModel):
    gym_id: str = Field(description="The gym id")
    today_focus: str = Field(description="Today's focus/workout goal")
    gym_code: str = Field(description="The gym code for verification")


class MarkAttendanceResponse(BaseModel):
    focus: str = Field(description="Today's focus")
    checked_in_time: str = Field(description="Check-in time in Indian format (24hr clock)")


class CheckoutRequest(BaseModel):
    checkout: bool = Field(description="Checkout flag")


class CheckoutResponse(BaseModel):
    checked_in_time: str = Field(description="Check-in time in Indian format (24hr clock)")
    checked_out_time: str = Field(description="Check-out time in Indian format (24hr clock)")
    total_workout_duration: str = Field(description="Total workout duration in HH:MM:SS format")
    focus: Optional[str] = Field(description="Today's workout focus", default=None)


class ActiveCheckInStatusResponse(BaseModel):
    has_active_checkin: bool = Field(description="Whether the member has an active check-in")


class MemberAttendanceItem(BaseModel):
    user_id: str = Field(description="Member user ID")
    name: str = Field(description="Member name")
    user_name: str = Field(description="Member username")
    photo_url: Optional[str] = Field(description="Member photo URL", default=None)
    check_in_time: Optional[str] = Field(description="Check-in time in Indian format (24hr clock)", default=None)
    focus: Optional[str] = Field(description="Workout focus", default=None)
    status: str = Field(description="Status: 'present' or 'absent'")


class DailyAttendanceSummary(BaseModel):
    date: str = Field(description="Date in DD-MM-YYYY format")
    present_count: int = Field(description="Number of members present")
    absent_count: int = Field(description="Number of members absent")
    total_members: int = Field(description="Total number of members in the gym")


class DailyAttendanceResponse(BaseModel):
    summary: DailyAttendanceSummary = Field(description="Daily attendance summary")
    members: List[MemberAttendanceItem] = Field(description="List of members with attendance status")