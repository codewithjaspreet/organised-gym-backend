from pydantic import BaseModel, Field


class DashboardKPIsResponse(BaseModel):
    active_members: int =Field(description="The number of active members")
    total_check_ins_today: int= Field(description="The total number of check-ins today")
    total_check_outs_today: int= Field(description="The total number of check-outs today")
    total_fee_due_members: int= Field(description="The total number of members with due fees")

class DashboardKPIsRequest(BaseModel):
    gym_id : str = Field(description="The gym id")

