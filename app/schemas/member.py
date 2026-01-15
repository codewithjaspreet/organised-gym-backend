from pydantic import BaseModel, Field


class AddMemberRequest(BaseModel):
    member_user_name: str = Field(description="The username of the member to add")
    gym_id: str = Field(description="The gym id to assign the member to")
