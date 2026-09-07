from pydantic import BaseModel, Field


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    organization: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)
