import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.database import get_db
from app.dependencies import get_current_user
from app.models.content import Content, ContentType
from app.models.user import User
from app.schemas.content import ContentResponse
from app.services.storage_service import storage


router = APIRouter(prefix="/api/content", tags=["content"])
RANGE_PATTERN = re.compile(r"bytes=(\d*)-(\d*)$")


def find_content(content_id: int, db: Session) -> Content:
    content = db.get(Content, content_id)
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    return content


@router.get("", response_model=list[ContentResponse])
def list_content(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.scalars(select(Content).order_by(Content.created_at.desc())).all()


@router.get("/{content_id}", response_model=ContentResponse)
def get_content(content_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return find_content(content_id, db)


def content_stream(content: Content, request: Request):
    file_obj = storage.open(content.storage_key)
    range_header = request.headers.get("range")
    start = 0
    end = content.file_size - 1
    status_code = status.HTTP_200_OK
    if range_header:
        match = RANGE_PATTERN.fullmatch(range_header.strip())
        if not match:
            file_obj.close()
            raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, detail="Invalid byte range")
        requested_start, requested_end = match.groups()
        if requested_start:
            start = int(requested_start)
            if requested_end:
                end = int(requested_end)
            else:
                end = content.file_size - 1
        elif requested_end:
            suffix_length = int(requested_end)
            start = max(content.file_size - suffix_length, 0)
        if start > end or start >= content.file_size:
            file_obj.close()
            raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, detail="Range is outside content")
        end = min(end, content.file_size - 1)
        status_code = status.HTTP_206_PARTIAL_CONTENT
    file_obj.seek(start)
    remaining = end - start + 1

    def iterator():
        nonlocal remaining
        try:
            while remaining:
                chunk = file_obj.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk
        finally:
            file_obj.close()

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(end - start + 1),
        "Content-Disposition": "inline",
        "Cache-Control": "private, no-store",
    }
    if status_code == status.HTTP_206_PARTIAL_CONTENT:
        headers["Content-Range"] = f"bytes {start}-{end}/{content.file_size}"
    return StreamingResponse(iterator(), status_code=status_code, media_type=content.mime_type, headers=headers)


def file_iterator(file_obj):
    try:
        while chunk := file_obj.read(1024 * 1024):
            yield chunk
    finally:
        file_obj.close()


@router.get("/{content_id}/stream")
def stream_video(content_id: int, request: Request, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    content = find_content(content_id, db)
    if content.content_type != ContentType.VIDEO:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Content is not a video")
    return content_stream(content, request)


@router.get("/{content_id}/pdf")
def render_pdf(content_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    content = find_content(content_id, db)
    if content.content_type != ContentType.PDF:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Content is not a PDF")
    file_obj = storage.open(content.storage_key)
    return StreamingResponse(file_iterator(file_obj), media_type="application/pdf", headers={"Content-Disposition": "inline", "Cache-Control": "private, no-store"})


@router.get("/{content_id}/html")
def render_html(content_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    content = find_content(content_id, db)
    if content.content_type != ContentType.HTML:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Content is not HTML")
    file_obj = storage.open(content.storage_key)
    return StreamingResponse(file_iterator(file_obj), media_type="text/html", headers={
        "Content-Security-Policy": f"default-src 'none'; style-src 'unsafe-inline'; img-src data:; frame-ancestors {settings.FRONTEND_URL};",
        "Content-Disposition": "inline",
        "Cache-Control": "private, no-store",
    })