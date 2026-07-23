from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from .languages import valid_language


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=48)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Room name must not be empty")
        return value


class RoomResponse(BaseModel):
    id: str
    name: str
    created_at: str


class JoinParameters(BaseModel):
    member_id: str = Field(min_length=8, max_length=64)
    name: str = Field(min_length=1, max_length=32)
    language: str = Field(min_length=2, max_length=10)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Name must not be empty")
        return value

    @field_validator("language")
    @classmethod
    def check_language(cls, value: str) -> str:
        value = value.lower()
        if not valid_language(value):
            raise ValueError("Unsupported language")
        return value
