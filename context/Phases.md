# Build Phases — EcoSphere

## Completed foundation

- [x] Native Odoo addon scaffold, manifest, groups, model access entries, menus and seed data.
- [x] Environmental, social, governance, gamification, reward, scoring and settings models.
- [x] Standard Odoo views, QWeb report templates and report-builder wizard.
- [x] Independent React/Vite frontend with login, create-account state and executive dashboard.
- [x] Frontend production build verification; Python compile and XML parse checks.

## Next backend phases

1. **Install verification:** run the addon against the target Odoo version and resolve XML/view compatibility errors.
2. **Automations:** add explicit cron/hooks for auto-emissions, overdue compliance alerts, score recalculation and badge notification flows.
3. **Data completeness:** add diversity/training tracking and production notification settings/templates.
4. **Reports:** implement scoped filters plus CSV/XLSX generation in the report-builder workflow.
5. **Security:** add record rules for department-head visibility and test with non-manager users.
6. **Tests:** write model and workflow tests, then run Odoo with `--test-enable --stop-after-init`.

## Next frontend phases

1. Define Odoo HTTP/JSON-RPC authentication endpoints and a secure session strategy.
2. Wire sign-in/create-account to Odoo users; add server-side validation, email verification and password-reset behavior.
3. Replace dashboard sample data with authenticated Odoo API data.
4. Add loading, empty, permission-denied and API-error states for each dashboard surface.
5. Deploy frontend separately or embed only agreed-upon OWL components in Odoo.
