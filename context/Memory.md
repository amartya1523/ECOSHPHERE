# Memory Log — EcoSphere

> Read this file first at the start of a new implementation session. Append a dated entry after meaningful work; do not rewrite history.

---

## 2026-08-29 — Initial implementation
- Status: Created the native `backend/eco_sphere_esg` Odoo addon with models, XML views, security, seed data, reports and a report-builder wizard. Python compilation and XML parsing passed.
- Next: Install the addon on the selected Odoo version and add automated Odoo tests.
- Notes: Auto-emission source hooks and production notifications still need target-module dependencies and explicit implementation.

## 2026-08-29 — Standalone frontend
- Status: Added `frontend/` with Vite, React and Framer Motion. It contains Apple-inspired login/sign-up views, a responsive executive dashboard and reduced-motion support. `npm run build` passes.
- Next: Connect authentication and dashboard data to Odoo through secure HTTP/JSON-RPC endpoints.
- Notes: Create Account is a UI prototype only; it does not persist Odoo users yet.

## 2026-08-29 — Context system added
- Status: Added the project-local `context/` documentation suite (PRD, Architecture, Rules, Phases, Design and this Memory log).
- Next: Keep these documents aligned with actual code decisions, particularly Odoo install status and API integration.
- Notes: The previous `memory.md` in Downloads remains a historical external reference; `context/Memory.md` is the repository source of truth from now on.

## 2026-08-29 — Local backend runtime setup
- Status: Added `backend/docker-compose.yml`, `.env.example` and `backend/README.md` for Odoo 17 + PostgreSQL 16 local startup.
- Next: Install/open Docker Desktop, create `backend/.env` from the example, start the containers, create `ecosphere_db`, and install the addon.
- Notes: Docker CLI is not currently installed in this workspace, so Compose could not be executed or validated against a local Docker daemon.

## 2026-08-29 — Native Odoo runtime resolved
- Status: Odoo 17 is installed at `~/odoo-17` and runs against the existing PostgreSQL 18 `ecosphere_db` database. The EcoSphere addon was installed successfully and HTTP login at `http://127.0.0.1:8069/web/login` returned 200.
- Next: Use the running Odoo UI for workflow testing, then add automated Odoo tests and install `wkhtmltopdf` before validating PDF reports.
- Notes: macOS 26 + Intel Homebrew Python 3.11 was incompatible (empty macOS version and `pyexpat`/libpq linker errors). The working runtime uses the existing native Python 3.12 at `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12` and `psycopg2-binary==2.9.9`. Manifest data order was corrected so the report-builder action loads before its menu reference.
