from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List


class BankAccountCreate(BaseModel):
    account_holder_name: str = Field(description="The account holder's name", min_length=1)
    bank_name: str = Field(description="The bank name", min_length=1)
    account_number: str = Field(description="The bank account number", min_length=1)
    ifsc_code: str = Field(description="The IFSC code", min_length=1)
    upi_id: Optional[str] = Field(description="The UPI ID", default=None)


class BankAccountUpdate(BaseModel):
    account_holder_name: Optional[str] = Field(default=None, description="The account holder's name")
    bank_name: Optional[str] = Field(default=None, description="The bank name")
    account_number: Optional[str] = Field(default=None, description="The bank account number")
    ifsc_code: Optional[str] = Field(default=None, description="The IFSC code")
    upi_id: Optional[str] = Field(default=None, description="The UPI ID")


class BankAccountResponse(BaseModel):
    id: str
    user_id: str
    account_holder_name: str
    bank_name: str
    account_number: str
    ifsc_code: str
    upi_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BankAccountListResponse(BaseModel):
    bank_accounts: List[BankAccountResponse]
