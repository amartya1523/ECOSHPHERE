# Architecture — EcoSphere

## App Flow
EcoSphere ships as a suite of Odoo addon modules (not a standalone app) that plug into an existing Odoo instance:

1. **Master configuration** (admin, once): Departments, Categories, Emission Factors, Product ESG Profiles, Environmental Goals, ESG Policies, Challenges are set up via Odoo backend views.
2. **Daily operations**: Existing ERP transactions (Purchase, Manufacturing, Expense, Fleet) occur as normal in their native Odoo modules.
3. **Carbon calculation**: A scheduled action or a model hook (`create`/`write` override, or a cron) reads eligible operational records and generates `esg.carbon.transaction` records, applying the linked Emission Factor — either automatically (if `auto_emission_calc` is enabled in ESG Configuration) or left for manual entry.
4. **Participation & compliance**: Employees interact via CSR Activities, Challenges, Policy Acknowledgements — each creates transactional records (`esg.employee.participation`, `esg.challenge.participation`, `esg.policy.acknowledgement`) tied to `hr.employee`.
5. **Scoring**: A computed/cron-based scoring engine aggregates Carbon Transactions, Participation, and Compliance records per Department into `esg.department.score` (Environmental/Social/Governance/Total), then rolls up into an Overall ESG Score using configurable weights.
6. **Dashboard & reports**: Odoo dashboard views (or OWL-based custom dashboard components) read the aggregated scores; QWeb/report engine generates the four standard reports plus the Custom Report Builder output (PDF/Excel/CSV via Odoo's report and `xlsx`/`csv` export mechanisms).
7. **Gamification loop**: XP earned from approved Participation/Challenges triggers Badge unlock-rule checks (via a computed method or cron) and updates Leaderboard views; Reward redemption deducts Points via a transactional wizard.
8. **Notifications**: Odoo's `mail` module (`mail.thread`, activities, `mail.template`) sends in-app/email notifications on the four defined trigger events, gated by Notification Settings.

## Tech Stack
| Layer | Choice | Why |
|---|---|---|
| Backend | Python (Odoo framework) | Given stack — Odoo's module system provides ORM, security, views, and workflow out of the box. |
| Web framework | Odoo framework | Native fit — avoids reinventing views/routing/ACL that Odoo already provides. |
| Database | PostgreSQL | Odoo's required and only supported database; also matches ESG's relational data model (Departments, Scores, Transactions) well. |
| Frontend | JavaScript / OWL | Odoo's native component framework for custom widgets (dashboards, leaderboards, gamification UI). |
| UI templating | XML views + OWL components | Standard Odoo view definition; OWL for interactive pieces (dashboards, challenge cards). |
| API | XML-RPC / JSON-RPC / HTTP controllers | Odoo's native external API surface, used if EcoSphere needs to expose data to other systems (e.g. custom report export endpoints). |
| ORM | Odoo ORM | Required by the framework; also gives free audit logging (`mail.thread`), access rules, and computed/related fields for the scoring engine. |
| Styling | SCSS, Bootstrap-based | Matches Odoo's existing design system so EcoSphere views feel native, not bolted-on. |
| Async/Realtime | Longpolling / Odoo bus | For live notification delivery (badge unlocks, compliance alerts) without a separate infra dependency. |
| Server | Linux (dev can be cross-platform) | Standard Odoo deployment target. |
| Web server/proxy | Nginx | Standard in front of Odoo workers in production. |
| Workers | Odoo multiprocessing workers | Needed once cron jobs (scoring, auto-emission calc) run alongside user traffic. |
| Source control | Git | Standard addon-repo workflow. |
| Deployment | Docker / Linux servers / Odoo.sh | Any is compatible; Docker recommended for local dev parity with prod. |

## Module (Folder) Structure
EcoSphere is split into one base module plus sub-modules per ESG pillar, mirroring how Odoo apps are typically decomposed so each is independently installable/testable.

```
ecosphere/                          # umbrella meta-module (depends on all below)
├── __manifest__.py
└── ...

esg_core/                           # shared master data + scoring engine
├── __manifest__.py
├── models/
│   ├── esg_department.py
│   ├── esg_category.py
│   ├── esg_config_settings.py
│   ├── esg_department_score.py
│   └── mixins/
│       └── esg_scorable_mixin.py
├── security/
│   ├── ir.model.access.csv
│   └── esg_security.xml
├── views/
│   ├── esg_department_views.xml
│   ├── esg_category_views.xml
│   └── esg_config_settings_views.xml
├── data/
│   └── esg_config_defaults.xml
└── reports/
    └── esg_summary_report.xml

esg_environmental/                  # depends on esg_core
├── models/
│   ├── emission_factor.py
│   ├── carbon_transaction.py
│   ├── product_esg_profile.py
│   └── environmental_goal.py
├── views/
├── data/
│   └── ir_cron_auto_emission.xml
└── reports/
    └── environmental_report.xml

esg_social/                         # depends on esg_core, hr
├── models/
│   ├── csr_activity.py
│   ├── employee_participation.py
│   └── diversity_metric.py
├── views/
└── reports/
    └── social_report.xml

esg_governance/                     # depends on esg_core
├── models/
│   ├── esg_policy.py
│   ├── policy_acknowledgement.py
│   ├── audit.py
│   └── compliance_issue.py
├── data/
│   └── ir_cron_compliance_overdue.xml
├── views/
└── reports/
    └── governance_report.xml

esg_gamification/                   # depends on esg_core, esg_social
├── models/
│   ├── badge.py
│   ├── reward.py
│   ├── reward_redemption.py
│   ├── challenge.py
│   └── challenge_participation.py
├── data/
│   └── ir_cron_badge_award.py
├── views/
│   └── leaderboard_dashboard.xml
└── static/src/
    ├── js/leaderboard_dashboard.js   # OWL component
    └── scss/gamification.scss

esg_reports/                        # depends on all — Custom Report Builder
├── wizards/
│   └── esg_custom_report_wizard.py
├── views/
└── reports/
```

## Key Architectural Decisions
- **Split into per-pillar modules, not one monolith**: matches Phases.md build order, lets each pillar be tested independently, and mirrors how Odoo apps are conventionally packaged (so future maintainers/AI agents recognize the pattern instantly).
- **`esg_core` owns Department, Category, scoring engine, and config**: all other modules depend on it, avoiding circular dependencies and giving one place to change scoring weight logic.
- **Scoring via mixin + cron, not real-time compute-on-every-write**: ESG scores aggregate potentially large transaction volumes; a scheduled recompute (with a manual "recalculate now" action) avoids performance hits on every CSR/Carbon record save.
- **Auto-emission calculation and badge auto-award are toggle-gated at the model level**, reading from `esg.config.settings` (extends `res.config.settings`), so the business-rule toggles from the spec are enforced centrally rather than duplicated per module.
- **Notifications reuse Odoo's `mail` module** rather than a custom notification table — gives in-app + email for free and matches user expectations inside an Odoo instance.
- **Custom Report Builder is a wizard (`TransientModel`)**, not a stored model — it's a filter-and-export tool, not data that needs to persist.
