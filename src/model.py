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
            raise ValueError("月は1から12の間で指定して下さい")
        return v

    @field_validator("birth_day")
    def validate_birth_day(cls, v):
        if v and v < 1 or v > 12:
            raise ValueError("日は1から31の間で指定して下さい")
        return v


class BirthdayChannel(BaseModel):
    server_id: int
    channel_id: Optional[int] = None
