# Architecture — EcoSphere

## Repository layout

```text
ECOshphere/
├── backend/
│   └── eco_sphere_esg/       # Native Odoo addon
│       ├── models/           # ORM models and configuration
│       ├── views/            # XML list/form/kanban/settings/menu views
│       ├── security/         # Groups and model access controls
│       ├── data/             # Seed categories, badges and factors
│       ├── reports/          # QWeb report templates
│       └── wizard/           # Custom report builder
├── frontend/                 # Independent React/Vite client
│   └── src/                  # App.jsx, styles.css and UI logic
└── context/                  # Persistent planning context for agents
```

## Backend

`backend/eco_sphere_esg` is a single installable Odoo addon. It depends on `base`, `mail`, `hr`, and `product`; PostgreSQL is the only supported database.

Core models include `esg.department`, `esg.category`, `esg.emission.factor`, `esg.carbon.transaction`, `esg.environmental.goal`, `esg.csr.activity`, `esg.csr.participation`, `esg.policy`, `esg.audit`, `esg.compliance.issue`, `esg.challenge`, `esg.challenge.participation`, `esg.badge`, `esg.reward`, `esg.reward.redemption` and `esg.department.score`.

Settings extend `res.config.settings`. Odoo's ORM, QWeb and `mail.thread` are the native integration points; no external Python API application belongs beside Odoo.

## Frontend

`frontend/` is a Vite + React + Framer Motion app. It is currently an independently runnable executive prototype. It does **not** persist created users or read Odoo data yet.

Future API integration should use Odoo HTTP/JSON-RPC endpoints with authenticated sessions. Do not expose Odoo's database directly to React, and never put database secrets in frontend environment variables.

## Execution

- Frontend: `cd frontend && npm install && npm run dev`
- Odoo: add `backend/` to `addons_path`, then install **EcoSphere ESG Management** in an Odoo database.

## Key decisions

- One addon is intentionally retained for the current hackathon scope. Do not split it into multiple addons without an explicit migration plan.
- Standard Odoo views are the backend UI baseline; use OWL only where native views cannot express the interaction.
- React is the polished public/executive experience and is separate from Odoo's own UI.
