# Architecture and security decisions

## Request flow

1. React calls FastAPI with `credentials: include`.
2. FastAPI reads the HttpOnly session cookie and hashes the opaque token.
3. PostgreSQL resolves the session and user role.
4. The endpoint performs its operation-specific authorization check.
5. Content bytes are read from private storage and returned through the API.

## Why these choices

- **FastAPI** provides typed request validation, dependency-based authorization,
  and useful OpenAPI documentation with little ceremony.
- **PostgreSQL and SQLAlchemy** keep user, session, and content metadata
  relational and queryable; binary files do not bloat database backups.
- **Alembic** makes schema changes reproducible in local and hosted databases.
- **Google OAuth** delegates password security and identity verification to a
  well-supported provider. There is no password database to protect.
- **Database-backed sessions** allow server-side revocation and expiration.
  Cookies are HttpOnly, SameSite=Lax, and Secure in production.
- **Private object storage** prevents guessed public URLs. Storage keys contain
  random UUIDs and never use an original filename as a path.
- **Protected range streaming** lets browsers seek through videos while every
  request still passes authentication and authorization.
- **PDF.js** renders PDF pages in the application instead of handing viewers a
  direct public file URL. It is a deterrent, not DRM.
- **Sandboxed HTML** treats uploaded markup as untrusted and does not inject it
  into the React document. The response also has a restrictive CSP.
- **Server-side RBAC** prevents a viewer from using curl, Postman, or a hidden
  URL to reach an admin operation.

## Storage failure handling

Upload writes the object first and creates the metadata row second. If the row
fails, the object is deleted. Delete removes the object before the metadata row;
if storage fails, the database record is retained so the failure is visible and
retryable rather than silently losing metadata.

## Known limitations

The local adapter is for development only. Production should use a private
bucket and HTTPS. Content delivered to an authorized browser can still be
captured. The application does not claim to provide DRM or impossible downloads.