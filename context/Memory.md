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

## 2026-08-29 — Phases 1-5 backend completion
- Status: Completed phases 1-5 in the existing `eco_sphere_esg` Odoo addon rather than creating a separate `esg_core` module. Added the planned ESG Admin/User security shape, hierarchy-aware department employee counts, settings weight validation coverage, emission-factor effective dates, carbon transaction search filters, environmental goal target metric/value tracking, product ESG profiles, and purchase-order based auto carbon transaction generation controlled by the Auto Emission Calculation setting.
- Next: Continue with Phase 6: native Odoo environmental dashboard and department carbon tracking rollups.
- Notes: Verified by updating the live `Ecosphere` database and running Odoo tests in Docker against `ecosphere_phase_1_5_test` with `--test-enable --test-tags /eco_sphere_esg`; result was 0 failures and 0 errors. Docker Compose was aligned to Odoo 18 because the active local backend is Odoo 18.
