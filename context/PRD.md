# Project Requirements Document — EcoSphere

## Overview

EcoSphere is an ESG (Environmental, Social, Governance) management platform. Its Odoo addon centralizes carbon accounting, CSR participation, governance compliance, gamification, reporting and departmental ESG scoring. A separate React frontend provides an Apple-inspired executive experience and account-entry prototype.

## Target users

- **ESG managers:** configure factors, goals, policies, weights and reports.
- **Department heads:** monitor department progress and resolve compliance issues.
- **Employees:** join CSR activities and challenges, submit proof, earn XP and redeem rewards.
- **Auditors and compliance officers:** run audits and own compliance remediation.
- **Executives:** consume organization scores, trends and reports.

## Current MVP scope

- Environmental: emission factors, product ESG profiles, carbon transactions and environmental goals.
- Social: CSR activities and evidence/approval-based employee participation.
- Governance: policies, acknowledgements, audits and owned, due-dated compliance issues.
- Gamification: challenges, participation, XP, badges, rewards and redemption.
- Score configuration: E/S/G weighted department scores with validated 40/30/30 default weights.
- Reporting: QWeb Environmental, Social, Governance and ESG Summary reports plus a report-builder wizard.
- React experience: sign in/create-account prototype, dashboard, sidebar and responsive mobile layout.

## Non-functional requirements

- Business rules must be enforced in Odoo models, not only in the UI.
- All records require appropriate Odoo access control entries.
- Frontend must respect reduced-motion preferences and work at mobile widths.
- The UI-only React account flow must not be presented as persistent authentication until it is connected to Odoo.

## Explicitly deferred

- Production React-to-Odoo authentication/API integration.
- Operational hooks for Purchase, Manufacturing, Expenses and Fleet auto-emission calculation.
- Production notification delivery and cron jobs.
- Excel/CSV export implementation beyond Odoo's native export surface.
