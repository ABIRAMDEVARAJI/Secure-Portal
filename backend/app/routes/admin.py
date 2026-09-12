import uuid
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies import require_admin, validate_origin
from app.models.content import Content
from app.models.user import User
from app.schemas.content import ContentMetadataUpdate, ContentResponse
from app.services.storage_service import storage
from app.utils.file_validation import inspect_upload


router = APIRouter(prefix="/api/admin/content", tags=["administration"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
def upload_content(
    request: Request,
    title: str = Form(..., min_length=1, max_length=255),
    description: str | None = Form(default=None, max_length=5000),
    category: str | None = Form(default=None, max_length=100),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    validate_origin(request)
    if not title.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Title cannot be blank")
    content_type, mime_type, file_size, original_filename = inspect_upload(file)
    storage_key = f"content/{uuid.uuid4()}_{uuid.uuid4().hex}{original_filename[original_filename.rfind('.'):].lower()}"
    try:
        storage.put(storage_key, file.file, mime_type)
        content = Content(
            title=title.strip(), description=description, category=category,
            content_type=content_type, storage_key=storage_key,
            original_filename=original_filename, mime_type=mime_type,
            file_size=file_size, created_by=admin.id,
        )
        db.add(content)
        db.commit()
        db.refresh(content)
        return content
    except Exception as exc:
        db.rollback()
        try:
            storage.delete(storage_key)
        except Exception:
            logger.exception("Failed to clean up storage object after upload failure")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Content upload failed") from exc


@router.patch("/{content_id}", response_model=ContentResponse)
def update_content(content_id: int, payload: ContentMetadataUpdate, request: Request, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    validate_origin(request)
    if not payload.title.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Title cannot be blank")
    content = db.get(Content, content_id)
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    content.title = payload.title.strip()
    content.description = payload.description
    content.category = payload.category
    db.commit()
    db.refresh(content)
    return content


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_content(content_id: int, request: Request, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    validate_origin(request)
    content = db.get(Content, content_id)
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    try:
        storage.delete(content.storage_key)
        db.delete(content)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Content deletion failed") from exc