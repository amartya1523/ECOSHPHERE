# Project Requirements Document — EcoSphere

## Overview
EcoSphere is an ESG (Environmental, Social, Governance) management platform built as an Odoo module suite. It integrates ESG measurement directly into day-to-day ERP operations — carbon accounting, CSR participation, compliance tracking — instead of leaving ESG reporting as a manual, disconnected process bolted onto operational data. Gamification (XP, badges, challenges, rewards) drives employee participation.

## Target Users
- **Sustainability/ESG managers** — configure emission factors, goals, policies; monitor org-wide ESG score and generate reports.
- **Department heads** — track their department's ESG score and CSR/compliance status.
- **Employees** — participate in CSR activities and challenges, earn XP/badges, redeem rewards, acknowledge policies.
- **Auditors/compliance officers** — run audits, raise and track compliance issues.
- **Executives** — consume dashboards and summary reports for decision-making.

## Core Features (v1 / MVP)
- **Environmental module**: Emission Factor configuration, Carbon Transaction calculation (manual and auto from Purchase/Manufacturing/Expense/Fleet), Department Carbon Tracking, Sustainability Goals, Environmental Dashboard.
- **Social module**: CSR Activity management, Employee Participation tracking (with proof/approval workflow), Diversity Metrics, Training Completion tracking.
- **Governance module**: ESG Policy management, Policy Acknowledgements, Audits, Compliance Issues (with mandatory Owner + Due Date and overdue flagging).
- **Gamification module**: Challenges (full lifecycle Draft → Active → Under Review → Completed/Archived), XP tracking, Badges (auto-award on Unlock Rule match), Rewards catalog with redemption (Points deduction, stock check), Leaderboards.
- **Scoring engine**: Department-level Environmental/Social/Governance/Total scores rolling up to an org-wide weighted Overall ESG Score (default 40/30/30, configurable).
- **Settings & Administration**: Department management, Category management, ESG Configuration (weights, toggles), Notification Settings.
- **Notifications**: In-app and/or email for compliance issue raised, CSR/Challenge approval decisions, policy acknowledgement reminders, badge unlocks.
- **Reports**: Environmental, Social, Governance, ESG Summary, and a Custom Report Builder (filter by Department/Date Range/Module/Employee/Challenge/ESG Category; export PDF/Excel/CSV).

## Future Scope (not in v1)
- Department ESG rankings (cross-department leaderboard beyond individual leaderboards)
- Advanced smart dashboard visualizations (beyond standard Odoo dashboard views)
- Mobile-responsive/dedicated mobile interface
- Multi-organization / multi-company benchmarking

## Success Criteria
- An admin can configure Departments, Categories, and Emission Factors from Settings.
- A Carbon Transaction can be created manually or auto-generated from a linked Purchase/Manufacturing/Expense/Fleet record when the toggle is enabled, and correctly applies the relevant Emission Factor.
- An employee can join a Challenge, submit progress with proof, get approved, and receive XP — and a Badge auto-awards when their Unlock Rule is met (when the toggle is enabled).
- An employee can redeem a Reward, with Points deducted and stock decremented, blocked if stock is insufficient.
- A Compliance Issue with a Due Date that lapses while still Open is flagged and triggers a notification.
- Department Environmental/Social/Governance scores calculate correctly and roll up into a weighted Overall ESG Score, configurable per organization.
- All four standard reports generate correctly, and the Custom Report Builder can filter across all six listed dimensions and export to PDF/Excel/CSV.
- Notifications fire for all four required event types and are configurable via Settings.

## Out of Scope
- Payroll, procurement, or manufacturing logic itself (EcoSphere reads/links to these records, it doesn't reimplement them).
- Third-party carbon-offset marketplace integration.
- External auditor portals (audits are managed internally by the org's own users).
- Real-time IoT sensor ingestion for emissions (data enters via linked ERP transactions, not live sensors).
