# ECOSHPHERE

## EcoSphere ESG Management Platform

Native Odoo addon for ESG operations, kept deliberately split into:

- `backend/eco_sphere_esg/` — installable Odoo addon, ORM models, security, views, data and QWeb reports.
- `frontend/` — boundary and implementation notes for the later standalone OWL/dashboard layer.

## Install

Add `backend/` to Odoo's `addons_path`, update the Apps list, then install **EcoSphere ESG Management**. The addon depends on `base`, `mail`, `hr`, and `product`.

## Included business safeguards

- CSR approvals enforce the global evidence setting and activity-level evidence requirement.
- Challenges use the required lifecycle: Draft → Active → Under Review → Completed; archive is always available.
- Compliance issues require owner and due date and expose an overdue flag while open.
- Reward requests reject insufficient XP or depleted stock, then reserve one unit of stock.
- Department ESG totals use configurable Environmental/Social/Governance weights, validated to 100%.

## Deferred frontend work

The supplied wireframes are implemented using standard Odoo views now. No custom OWL widgets have been introduced, per the current project decision. Future dashboard widgets belong in `backend/eco_sphere_esg/static/src/` and should not duplicate backend domain rules.
