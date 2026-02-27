"""Pydantic request/response schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class MessageResponse(BaseModel):
    """Simple message payload for success responses."""

    message: str


class UserSignupRequest(BaseModel):
    """Signup request body."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLoginRequest(BaseModel):
    """Login request body."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    """Authenticated user payload."""

    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT response payload."""

    access_token: str
    token_type: str = "bearer"


class WordCreateRequest(BaseModel):
    """Create word request body."""

    word_text: str = Field(min_length=1, max_length=120)
    meaning: str = Field(min_length=1, max_length=500)
    language: str = Field(min_length=2, max_length=20)
    category_mode: Literal["auto", "existing", "new"] = "auto"
    category_name: str | None = Field(default=None, min_length=1, max_length=100)


class WordUpdateRequest(BaseModel):
    """Update word request body."""

    word_text: str = Field(min_length=1, max_length=120)
    meaning: str = Field(min_length=1, max_length=500)
    language: str = Field(min_length=2, max_length=20)
    category_mode: Literal["auto", "existing", "new"] = "auto"
    category_name: str | None = Field(default=None, min_length=1, max_length=100)


class WordResponse(BaseModel):
    """Word response payload."""

    id: int
    word_text: str
    meaning: str
    language: str
    category: str
    created_at: datetime


class CategorySummaryResponse(BaseModel):
    """Category list payload with per-user count."""

    name: str
    count: int


class PracticeWordResponse(BaseModel):
    """Word payload for practice endpoint."""

    id: int
    word_text: str
    meaning: str
    language: str


class PracticeResponse(BaseModel):
    """Practice response body."""

    category: str
    requested_count: int
    words: list[PracticeWordResponse]
