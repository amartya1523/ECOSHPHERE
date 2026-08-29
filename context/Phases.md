# Build Phases — EcoSphere

## Phase 1: Scaffold `esg_core` module skeleton
**Goal:** Get a blank, installable Odoo module with manifest, security stub, and menu shell.
**Done when:**
- [ ] `esg_core` module installs cleanly with no models yet (just `__manifest__.py`, empty `models/__init__.py`, top-level menu action)
- [ ] Top-level "ESG" app icon appears in Odoo backend with placeholder sub-menus (Environmental, Social, Governance, Gamification, Settings, Reports)
- [ ] `ir.model.access.csv` and security groups (`esg.group_esg_admin`, `esg.group_esg_user`) exist, even if unused yet

## Phase 2: Master data — Department & Category
**Goal:** Core shared master data other modules depend on.
**Done when:**
- [ ] `esg.department` model with Name, Code, Head (`hr.employee`), Parent Department (self-referential), Employee Count (computed), Status
- [ ] `esg.category` model with Name, Type (Selection: CSR Activity / Challenge), Status
- [ ] List + form views for both, accessible from Settings menu
- [ ] Basic tests: create a department hierarchy (parent/child), confirm Employee Count computes correctly

## Phase 3: ESG Configuration & scoring skeleton
**Goal:** Central config model and an (initially empty) scoring engine to build on.
**Done when:**
- [ ] `esg.config.settings` (extends `res.config.settings`) with fields for: Environmental/Social/Governance weights (default 40/30/30, must sum to 100), Auto Emission Calculation toggle, Evidence Requirement toggle, Badge Auto-Award toggle
- [ ] `esg.department.score` model with Department, Environmental Score, Social Score, Governance Score, Total Score fields (values 0 for now — no source data yet)
- [ ] Constraint: weights must sum to 100, enforced via `@api.constrains`
- [ ] Settings screen shows all toggles/weights and saves correctly

## Phase 4: Environmental — Emission Factors & Carbon Transactions (manual)
**Goal:** Manual carbon accounting works end-to-end before automation is added.
**Done when:**
- [ ] `esg.emission.factor` model (source/activity type, factor value, unit, effective date range)
- [ ] `esg.carbon.transaction` model (Department, Emission Factor, quantity, calculated emission value, source reference, date) — manual entry via form view
- [ ] Emission value computes correctly from quantity × factor
- [ ] List view filterable by Department and date range
- [ ] Tests: create a transaction, verify computed emission value

## Phase 5: Environmental — Goals & Auto Emission Calculation
**Goal:** Automate carbon transaction creation from operational records; add goal tracking.
**Done when:**
- [ ] `esg.environmental.goal` model (target metric, target value, deadline, linked Department)
- [ ] `esg.product.esg.profile` model linked to `product.template`
- [ ] Auto Emission Calculation: hook (via `ir.cron` or model override) generates Carbon Transactions from linked Purchase/Manufacturing/Expense/Fleet records when the Settings toggle is enabled
- [ ] Toggle off → no auto-generation; manual entry still works (regression check against Phase 4)
- [ ] Tests: enable toggle, create a qualifying Purchase record, confirm a Carbon Transaction auto-generates with correct Emission Factor applied

## Phase 6: Environmental Dashboard & Department Carbon Tracking
**Goal:** Visual rollup of environmental data per department.
**Done when:**
- [ ] Department Carbon Tracking view (grouped/pivoted by Department, date)
- [ ] Environmental Dashboard (native Odoo dashboard view or OWL widget) showing totals, trend, goal progress
- [ ] Manually verified against Phase 4/5 test data that numbers match

## Phase 7: Social — CSR Activities & Employee Participation
**Goal:** Core social-module workflow: activity creation → employee participation → approval.
**Done when:**
- [ ] `esg.csr.activity` model (Title, Category [linked to `esg.category`], Description, Date, Department)
- [ ] `esg.employee.participation` model: Employee, Activity, Proof (attachment field), Approval Status (Selection: Draft/Submitted/Approved/Rejected), Points Earned, Completion Date
- [ ] Evidence Requirement toggle enforced: cannot set Approval Status = Approved without a Proof attachment when toggle is on (`@api.constrains`)
- [ ] Tests: toggle on, attempt approval without proof → raises `ValidationError`; attach proof → approval succeeds

## Phase 8: Social — Diversity Metrics & Training Completion
**Goal:** Remaining social sub-features.
**Done when:**
- [ ] `esg.diversity.metric` model (Department, metric type, value, period)
- [ ] Training Completion tracking (model or extension linking to existing `hr` training/e-learning if available, else standalone `esg.training.completion`)
- [ ] Views accessible from Social menu, filterable by Department

## Phase 9: Governance — Policies & Acknowledgements
**Goal:** Policy lifecycle and employee acknowledgement tracking.
**Done when:**
- [ ] `esg.policy` model (Title, Description, Document attachment, Effective Date, Status)
- [ ] `esg.policy.acknowledgement` model (Employee, Policy, Acknowledged Date, Status)
- [ ] Policy Acknowledgement Reminder notification wired to Odoo `mail` (stub trigger is fine here; full Notification System comes in Phase 12)
- [ ] Tests: employee acknowledges a policy, status updates correctly

## Phase 10: Governance — Audits & Compliance Issues
**Goal:** Audit and compliance workflow with mandatory ownership enforcement.
**Done when:**
- [ ] `esg.audit` model (Department, Auditor, Date, Findings summary, Status)
- [ ] `esg.compliance.issue` model: Audit (link), Severity (Selection: Low/Medium/High, per mockup), Description, Owner (required), Due Date (required), Status (Selection: Open/Resolved, expandable later)
- [ ] `@api.constrains` enforcing Owner and Due Date are always set — record cannot save without them
- [ ] `ir.cron` job flags issues where Due Date has passed and Status is still Open (sets a computed `is_overdue` flag or similar)
- [ ] Tests: attempt to create Compliance Issue without Owner → fails; create one with a past Due Date, run the cron, confirm it's flagged

## Phase 11: Gamification — Challenges & Challenge Participation
**Goal:** Full challenge lifecycle and participation tracking.
**Done when:**
- [ ] `esg.challenge` model: Title, Category, Description, XP, Difficulty, Evidence Required (bool), Deadline, Status (Selection: Draft/Active/Under Review/Completed/Archived)
- [ ] State transitions enforced via explicit action methods (not free-form field edit) — e.g. `action_activate()`, `action_archive()`, matching Draft → Active → Under Review → Completed, or Archived at any point
- [ ] Challenges list view includes a horizontal state-filter bar (Draft/Active/Under Review/Completed/Archived as clickable filter pills above the challenge cards, per mockup) in addition to the kanban/card display
- [ ] `esg.challenge.participation` model: Challenge, Employee, Progress, Proof, Approval, XP Awarded
- [ ] Tests: walk a challenge through its full state lifecycle; verify Archived is reachable from any prior state

## Phase 12: Gamification — Badges, XP, Rewards & Redemption
**Goal:** Reward loop: XP accrual → badge unlock → reward redemption.
**Done when:**
- [ ] `esg.badge` model (Name, Description, Unlock Rule [structured — e.g. XP threshold or completed-challenge count], Icon)
- [ ] Badge Auto-Award: `ir.cron` or triggered computation checks employees against Unlock Rules and assigns Badges automatically when the Settings toggle is on
- [ ] `esg.reward` model (Name, Description, Points Required, Stock, Status)
- [ ] `esg.reward.redemption` wizard/model: validates sufficient Points balance and Stock > 0, deducts Points, decrements Stock on confirm
- [ ] Tests: toggle badge auto-award on, push an employee's XP past a threshold via approved participation, confirm badge assigns automatically; attempt redemption with insufficient stock → blocked with clear error

## Phase 13: Gamification — Leaderboards
**Goal:** Visual ranking of employee XP/points.
**Done when:**
- [ ] Leaderboard view (OWL component per Architecture.md) ranking employees by XP/Points, filterable by Department and time period
- [ ] Manually verified ranking order matches underlying XP data from Phase 11/12 test records

## Phase 14: Scoring Engine — full rollup
**Goal:** Wire real Environmental/Social/Governance data into the scoring skeleton from Phase 3.
**Done when:**
- [ ] `esg.department.score` computation reads real Carbon Transactions (Environmental), Participation + Diversity (Social), Compliance + Audits (Governance) and produces per-pillar scores per Department
- [ ] Total Score per Department computed from the three pillar scores
- [ ] Overall ESG Score computed as the weighted average of Department Total Scores, using the configurable weights from Phase 3
- [ ] "Recalculate now" manual action available in addition to the scheduled cron
- [ ] Tests: known input data produces an expected, hand-verified score at each level (pillar → department total → overall)

## Phase 15: Organization Dashboard
**Goal:** Top-level executive dashboard tying environmental/social/governance/gamification together, matching the confirmed mockup layout.
**Done when:**
- [ ] Four KPI score tiles across the top: Environmental Score, Social Score, Governance Score, Overall ESG Score — each with pillar-colored border (see Design.md)
- [ ] "Emissions Trend (12 mo)" line chart panel
- [ ] "Department ESG Ranking" bar chart panel (per-department comparison)
- [ ] "Recent Activity" feed panel (recent completions, new compliance issues, carbon transactions logged, policy acknowledgements — pulled from across modules)
- [ ] "Quick Actions" panel with shortcut buttons (e.g. Log Carbon Data, Start Challenge, View Reports) linking into the relevant module screens
- [ ] Left sidebar navigation tree (Dashboard/Environmental/Social/Governance/Gamification/Reports/Settings with sub-items) present on the dashboard view per Design.md layout structure
- [ ] Top tab bar for module switching, consistent across all module screens (not just Dashboard)

## Phase 16: Notification System
**Goal:** Wire all required notification triggers via Odoo `mail`.
**Done when:**
- [ ] Notifications fire for: new Compliance Issue raised, CSR/Challenge approval decisions, policy acknowledgement reminders, badge unlocks
- [ ] Notification Settings screen (Settings → Notification Settings) lets admin enable/disable each notification type and choose in-app vs. email
- [ ] Tests: trigger each of the four event types, confirm notification generates (or is suppressed when disabled)

## Phase 17: Standard Reports
**Goal:** The four fixed reports.
**Done when:**
- [ ] Environmental Report, Social Report, Governance Report, ESG Summary Report each generate via Odoo's report engine
- [ ] Each supports the filter set: Department, Date Range, Module, Employee, Challenge, ESG Category (wherever applicable to that report)
- [ ] Output verified in PDF at minimum

## Phase 18: Custom Report Builder
**Goal:** User-composable report/export tool.
**Done when:**
- [ ] Wizard (`TransientModel`) lets a user combine the six filter dimensions freely
- [ ] Export works in PDF, Excel, and CSV
- [ ] Tests: build a report with 2+ combined filters, confirm the exported file's row count matches the filtered record count

## Phase 19: End-to-end regression pass
**Goal:** Confirm nothing broke across modules as they were added incrementally.
**Done when:**
- [ ] Full test suite across all `esg_*` modules passes (`--test-enable --stop-after-init`)
- [ ] Manual walkthrough: configure org → run a purchase → auto-generate carbon transaction → run a CSR activity → approve participation → earn XP → unlock badge → redeem reward → raise compliance issue → view updated dashboard and generate ESG Summary Report
- [ ] Memory.md reflects final state and any deviations from this plan
