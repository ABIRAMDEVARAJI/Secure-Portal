from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.content import ContentType


class ContentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    category: str | None
    content_type: ContentType
    original_filename: str
    mime_type: str
    file_size: int
    created_by: int
    created_at: datetime
    updated_at: datetime


class ContentMetadataUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    category: str | None = Field(default=None, max_length=100)