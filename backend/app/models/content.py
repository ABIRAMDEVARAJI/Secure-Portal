import enum

from sqlalchemy import (
    String,
    Text,
    DateTime,
    Enum,
    BigInteger,
    ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database.database import Base


class ContentType(str, enum.Enum):
    VIDEO = "VIDEO"
    PDF = "PDF"
    HTML = "HTML"


class Content(Base):
    __tablename__ = "content"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )

    content_type: Mapped[ContentType] = mapped_column(
        Enum(ContentType),
        nullable=False
    )

    storage_key: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        nullable=False
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )