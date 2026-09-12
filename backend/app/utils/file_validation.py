from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.config.settings import settings
from app.models.content import ContentType


ALLOWED_FILES = {
    ".mp4": (ContentType.VIDEO, "video/mp4", settings.MAX_VIDEO_SIZE_MB),
    ".pdf": (ContentType.PDF, "application/pdf", settings.MAX_PDF_SIZE_MB),
    ".html": (ContentType.HTML, "text/html", settings.MAX_HTML_SIZE_MB),
    ".htm": (ContentType.HTML, "text/html", settings.MAX_HTML_SIZE_MB),
}


def inspect_upload(upload: UploadFile) -> tuple[ContentType, str, int, str]:
    filename = Path(upload.filename or "").name
    suffix = Path(filename).suffix.lower()
    definition = ALLOWED_FILES.get(suffix)
    if not definition:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Only MP4, PDF, and HTML files are supported")
    content_type, expected_mime, max_size_mb = definition
    if upload.content_type and upload.content_type != expected_mime:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f"Expected MIME type {expected_mime}")
    upload.file.seek(0, 2)
    file_size = upload.file.tell()
    upload.file.seek(0)
    if file_size > max_size_mb * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"File exceeds the {max_size_mb} MB limit")
    signature = upload.file.read(16)
    upload.file.seek(0)
    if content_type == ContentType.PDF and not signature.startswith(b"%PDF-"):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="File is not a valid PDF")
    if content_type == ContentType.VIDEO and b"ftyp" not in signature[4:12]:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="File is not a valid MP4")
    if content_type == ContentType.HTML:
        if b"\x00" in signature:
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="File is not valid HTML text")
    safe_name = filename[:255] or f"content{suffix}"
    return content_type, expected_mime, file_size, safe_name