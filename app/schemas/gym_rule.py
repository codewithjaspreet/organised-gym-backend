from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class GymRuleCreate(BaseModel):
    gym_id: str = Field(description="The gym id")
    title: str = Field(description="The rule title", min_length=1)
    description: str = Field(description="The rule description", min_length=1)


class GymRuleUpdate(BaseModel):
    title: Optional[str] = Field(description="The rule title", nullable=True, min_length=1)
    description: Optional[str] = Field(description="The rule description", nullable=True, min_length=1)


class GymRuleResponse(BaseModel):
    id: str
    gym_id: str
    title: str
    description: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class GymRuleListResponse(BaseModel):
    rules: List[GymRuleResponse] = Field(description="The list of gym rules")
