# Rules — EcoSphere

## Libraries & Tools
**Use:**
- Odoo's built-in ORM, views, security (`ir.model.access.csv`, record rules) — never bypass with raw SQL unless a computed aggregate genuinely can't be expressed in ORM (and if so, comment why).
- Odoo's `mail` module (`mail.thread`, `mail.activity.mixin`) for notifications and audit trails — don't build a parallel notification table.
- Odoo's native report engine (QWeb + `report.report_xlsx` for Excel, standard CSV export) for the four standard reports and Custom Report Builder.
- OWL components only for genuinely interactive widgets (leaderboard, gamification dashboard) — standard list/form/kanban views for everything else. Don't reach for OWL/custom JS where a native view type already does the job.
- `ir.cron` for scheduled jobs (auto emission calc, badge award sweep, compliance overdue flagging, score recompute).

**Avoid:**
- No external Python web frameworks (Flask/FastAPI) bolted alongside Odoo — everything runs inside the Odoo application server.
- No direct `cr.execute()` raw SQL for anything the ORM can express — breaks access rules and audit trail.
- No hardcoded scoring weights in Python — must read from `esg.config.settings` so the 40/30/30 default stays admin-configurable per the spec.
- No new top-level Odoo apps beyond the `ecosphere` structure in Architecture.md — new features become models within the existing pillar modules unless a genuinely new pillar is introduced (ask before creating a new module).

## Error Handling
- Use Odoo's `ValidationError` / `UserError` from `odoo.exceptions` for business-rule violations (e.g. redeeming a Reward with insufficient stock, approving CSR participation without proof when Evidence Requirement is on) — never fail silently or with a bare Python exception.
- Constraints that must always hold (e.g. Compliance Issue must have Owner + Due Date) go in `@api.constrains`, not just UI-level required fields — so imports/API writes can't bypass them.
- Cron jobs (auto emission calc, badge award, overdue flagging) must log failures via Odoo's logging (`_logger`) and continue processing remaining records rather than aborting the whole batch on one bad record.
- Wizard actions (report builder, reward redemption) should return clear user-facing error messages via `UserError`, not stack traces.

## Coding Standards
- Model names follow Odoo convention: `esg.department`, `esg.carbon.transaction`, `esg.challenge`, etc. — dotted, lowercase, pillar-prefixed where it disambiguates.
- One model per file, filename matches model name (`carbon_transaction.py` for `esg.carbon.transaction`).
- Every model needs `_description` set, and `mail.thread`/`mail.activity.mixin` inherited wherever the spec implies an approval workflow or audit trail (Employee Participation, Challenge Participation, Compliance Issue, Audit).
- Fields referenced in the spec's "Key Fields" columns must exist with matching semantics even if named idiomatically for Odoo (e.g. `Status` → `state` Selection field with explicit `[('draft','Draft'), ...]` per the Challenge lifecycle).
- Security: every new model gets an `ir.model.access.csv` entry at minimum; record rules (multi-department visibility) added where a Department Head should only see their own department's data.
- XML view IDs follow `{model_name}_view_{type}` (e.g. `esg_challenge_view_form`).

## AI Assistant Boundaries
- Should always: read Phases.md and build in phase order; check Memory.md at the start of a session before re-reading the whole codebase; run the module's tests (`odoo-bin -i esg_x --test-enable --stop-after-init`) before marking a phase done; ask before adding any new Odoo module dependency beyond `base`, `mail`, `hr`, `purchase`, `mrp`, `hr_expense`, `fleet`.
- Should never: bypass the ORM with raw SQL for standard CRUD; hardcode the 40/30/30 score weighting; mark a phase "done" without running the relevant tests; delete or rewrite Memory.md history (append only); introduce a new top-level module without flagging it first.
