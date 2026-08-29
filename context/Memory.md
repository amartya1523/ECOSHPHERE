# Memory Log — EcoSphere

> **Instructions for the AI coding assistant working on this project:**
>
> This file is your persistent memory across chat sessions. The codebase and other planning docs (PRD, Architecture, Rules, Phases, Design) don't change often, but you need a fast way to know *where things stand* without re-reading the whole project every time.
>
> **Update this file whenever you:**
> - Complete a phase or a meaningful chunk of work
> - Make a decision that deviates from the original docs (and why)
> - Hit a blocker or leave something half-finished
> - Learn something about the codebase that isn't obvious from the code itself
>
> **Format for each entry:** append, don't rewrite history. Use:
> ```
> ## {Date or Session Label}
> - Status: {what's done}
> - Next: {what to do next}
> - Notes: {gotchas, decisions, deviations from the plan}
> ```
>
> At the start of a new chat session, read this file first (before re-reading the whole codebase) to get oriented. Only dig into the actual code when this file doesn't answer your question.

---

<!-- New entries go below this line -->

## 2026-08-29 — Phases 6–10 completed
- Status: Added a native environmental dashboard and departmental monthly carbon rollup, CSR evidence approval controls, diversity metrics, standalone training completion tracking, policy attachments/acknowledgements/reminders, and compliance overdue tracking via scheduled cron.
- Verification: Upgraded `eco_sphere_esg` on the local Odoo 17 `ecosphere_db`. The Odoo suite reports 10 test methods, 0 failures and 0 errors (14 total EcoSphere tests).
- Notes: The Odoo 17 runtime requires `<tree>` XML roots; merged Odoo 18-style `<list>` roots were normalized across module views during validation.

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

## 2026-08-29 — Phases 1-5 backend completion
- Status: Completed phases 1-5 in the existing `eco_sphere_esg` Odoo addon rather than creating a separate `esg_core` module. Added the planned ESG Admin/User security shape, hierarchy-aware department employee counts, settings weight validation coverage, emission-factor effective dates, carbon transaction search filters, environmental goal target metric/value tracking, product ESG profiles, and purchase-order based auto carbon transaction generation controlled by the Auto Emission Calculation setting.
- Next: Continue with Phase 6: native Odoo environmental dashboard and department carbon tracking rollups.
- Notes: This work was previously verified in a Docker/Odoo 18 environment. The current workstation runs the addon natively with Odoo 17 and PostgreSQL 18, so Odoo 17 compatibility should remain the local target.
