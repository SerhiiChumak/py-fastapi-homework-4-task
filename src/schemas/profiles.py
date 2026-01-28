from datetime import date

from fastapi import UploadFile, Form, File, HTTPException
from pydantic import BaseModel, field_validator, HttpUrl

from validation import (
    validate_name,
    validate_image,
    validate_gender,
    validate_birth_date
)

from pydantic import BaseModel, Field
from datetime import date
from typing import Optional
from database.models.accounts import GenderEnum

class ProfileCreateSchema(BaseModel):
    first_name: str = Field(..., max_length=100, example="John")
    last_name: str = Field(..., max_length=100, example="Doe")
    gender: Optional[GenderEnum] = Field(None, example=GenderEnum.MAN)
    date_of_birth: Optional[date] = Field(None, example="1990-01-01")
    info: Optional[str] = Field(None, example="I love movies!")

class ProfileResponseSchema(BaseModel):
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    avatar: Optional[str]
    gender: Optional[GenderEnum]
    date_of_birth: Optional[date]
    info: Optional[str]
    user_id: int

    class Config:
        from_attributes = True
