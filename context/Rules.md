# Rules — EcoSphere

## Backend rules

- Use Odoo ORM; do not use raw SQL for standard create/read/update/delete workflows.
- Use `ValidationError` or `UserError` for business-rule failures.
- Keep score weights configurable through `res.config.settings`; never hardcode 40/30/30 in calculations.
- Every model needs a corresponding access-control entry.
- Approval/workflow records should inherit `mail.thread` and, when relevant, `mail.activity.mixin`.
- Carbon, CSR, governance, challenge and rewards behavior must enforce its rules server-side.
- New Odoo dependencies (such as `purchase`, `mrp`, `hr_expense` or `fleet`) require an explicit decision before adding them to the manifest.

## Frontend rules

- Do not call PostgreSQL from React. Use an authenticated Odoo API integration when it is added.
- Treat the Create Account form as UI-only until a backend endpoint exists; do not claim it creates a database user.
- Use Framer Motion springs for interaction-driven movement. Keep animation interruptible and respect `prefers-reduced-motion`.
- Preserve responsive design and accessible form labels/error messages.
- Keep domain calculations and security in Odoo, not duplicated in React.

## Repository rules

- Read `context/Memory.md` first in a new implementation session.
- Update the memory log after meaningful implementation, design or architecture changes.
- Do not rewrite existing memory entries; append chronologically.
- Run an appropriate check before declaring work complete: `npm run build` for frontend and Odoo install/tests for addon work.
