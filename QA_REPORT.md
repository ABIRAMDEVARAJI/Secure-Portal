# Secure Content Portal QA Matrix

Checks executed locally on 2026-09-12. Google OAuth and cloud deployment are
externally blocked because no provider credentials or deployed environment are
present.

| Feature | Admin | Viewer | Unauthenticated | Result |
| --- | --- | --- | --- | --- |
| Backend startup/health | PASS | PASS | PASS | PASS |
| Browse content API | PASS | PASS | 401 | PASS |
| Upload | PASS | 403 | 401 | PASS |
| Edit metadata | PASS | 403 | 401 | PASS |
| Delete content | PASS | 403 | 401 | PASS |
| Invalid upload rejection | PASS | 403 | 401 | PASS |
| Private HTML delivery | PASS | protected | 401 | PASS |
| Video range delivery | PASS | protected | 401 | PASS |
| PDF.js viewer | PASS | PASS | 401 | PASS |
| Sandboxed HTML viewer | implemented | implemented | 401 | PASS |
| Google OAuth | not configured | not configured | N/A | BLOCKED |
| Production deployment | not deployed | not deployed | N/A | BLOCKED |

## Executed checks

- `pip check`: passed
- `alembic check`: passed
- `pytest -q`: 7 passed
- Python compilation: passed
- `npm audit --omit=dev`: 0 vulnerabilities
- `npm run lint`: passed
- `npm run build`: passed, with a non-failing PDF.js bundle-size warning
- FastAPI `/`: 200
- FastAPI `/health`: 200 with PostgreSQL connected
- Unauthenticated `/api/content`: 401
- Credentialed 127.0.0.1 CORS preflight: 200
- Mobile browser viewport: no horizontal overflow; local/session storage empty
- Protected video `206` Range response and `Content-Range`: passed
- Protected PDF response and sandbox HTML CSP: passed
- Logout invalidation: passed