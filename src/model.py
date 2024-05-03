from typing import Optional

from pydantic import BaseModel, field_validator


class Birthday(BaseModel):
    server_id: int
    member_id: int
    birth_month: Optional[int] = None
    birth_day: Optional[int] = None

    @field_validator("birth_month")
    def validate_birth_month(cls, v):
        if v and v < 1 or v > 12:
            raise ValueError("birth_month must be between 1 and 12")
        return v

    @field_validator("birth_day")
    def validate_birth_day(cls, v):
        if v and v < 1 or v > 12:
            raise ValueError("birth_month must be between 1 and 12")
        return v


class BirthdayChannel(BaseModel):
    server_id: int
    channel_id: Optional[int] = None
