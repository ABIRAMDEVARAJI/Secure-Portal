from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database.database import SessionLocal
from app.main import app
from app.models.content import Content
from app.models.user import User, UserRole, UserSession
from app.services.storage_service import storage
from app.utils.security import create_session_token, hash_session_token


client = TestClient(app)


def session_for(role: UserRole) -> tuple[int, str]:
    db = SessionLocal()
    user = User(google_id=f"test-{uuid4()}", email=f"{uuid4()}@example.com", name="Test User", role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    user_id = user.id
    token = create_session_token()
    db.add(UserSession(user_id=user.id, token_hash=hash_session_token(token), expires_at=datetime.now(timezone.utc) + timedelta(hours=1)))
    db.commit()
    db.close()
    return user_id, token


def cleanup(user_id: int) -> None:
    db = SessionLocal()
    contents = db.query(Content).filter(Content.created_by == user_id).all()
    for content in contents:
        storage.delete(content.storage_key)
    db.execute(delete(UserSession).where(UserSession.user_id == user_id))
    db.execute(delete(Content).where(Content.created_by == user_id))
    db.execute(delete(User).where(User.id == user_id))
    db.commit()
    db.close()


def test_unauthenticated_user_cannot_access_content():
    response = client.get("/api/content")
    assert response.status_code == 401


def test_viewer_cannot_access_admin_upload():
    user_id, token = session_for(UserRole.VIEWER)
    try:
        response = client.post(
            "/api/admin/content",
            cookies={"scp_session": token},
            files={"file": ("reference.html", b"<h1>Reference</h1>", "text/html")},
            data={"title": "Reference"},
        )
        assert response.status_code == 403
    finally:
        cleanup(user_id)


def test_invalid_file_type_is_rejected_for_admin():
    user_id, token = session_for(UserRole.ADMIN)
    try:
        response = client.post(
            "/api/admin/content",
            cookies={"scp_session": token},
            files={"file": ("payload.exe", b"MZ-not-allowed", "application/octet-stream")},
            data={"title": "Bad upload"},
        )
        assert response.status_code == 415
    finally:
        cleanup(user_id)


def test_admin_can_upload_edit_and_delete_private_content():
    user_id, token = session_for(UserRole.ADMIN)
    try:
        created = client.post(
            "/api/admin/content",
            cookies={"scp_session": token},
            files={"file": ("reference.html", b"<h1>Reference</h1>", "text/html")},
            data={"title": "Reference", "description": "Original", "category": "Training"},
        )
        assert created.status_code == 201
        content_id = created.json()["id"]
        assert "storage_key" not in created.json()

        updated = client.patch(
            f"/api/admin/content/{content_id}",
            cookies={"scp_session": token},
            json={"title": "Updated reference", "description": "Revised", "category": "Security"},
        )
        assert updated.status_code == 200
        assert updated.json()["title"] == "Updated reference"

        delivered = client.get(f"/api/content/{content_id}/html", cookies={"scp_session": token})
        assert delivered.status_code == 200
        assert delivered.headers["content-type"].startswith("text/html")

        deleted = client.delete(f"/api/admin/content/{content_id}", cookies={"scp_session": token})
        assert deleted.status_code == 204
        assert client.get(f"/api/content/{content_id}", cookies={"scp_session": token}).status_code == 404
    finally:
        cleanup(user_id)


def test_viewer_cannot_edit_or_delete_content():
    user_id, token = session_for(UserRole.VIEWER)
    try:
        assert client.patch(
            "/api/admin/content/1",
            cookies={"scp_session": token},
            json={"title": "Attempt", "description": "", "category": ""},
        ).status_code == 403
        assert client.delete("/api/admin/content/1", cookies={"scp_session": token}).status_code == 403
    finally:
        cleanup(user_id)