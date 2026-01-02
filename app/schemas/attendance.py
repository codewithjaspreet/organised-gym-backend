import datetime
from pydantic import BaseModel, Field


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