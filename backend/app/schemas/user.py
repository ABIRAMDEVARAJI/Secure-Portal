from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.user import UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    profile_picture: str | None
    role: UserRole
    created_at: datetime