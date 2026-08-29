# Design — EcoSphere

## Current visual direction

The React experience is intentionally **Apple-inspired light mode**, superseding the original wireframe's utilitarian desktop look for the standalone frontend. It uses calm near-white surfaces, forest green as the core brand color, translucent materials, soft shadows and a data-dense but generous layout.

Odoo XML views should remain native and familiar to Odoo users. Do not try to force the React visual system onto all Odoo core widgets.

## Design system

| Role | Direction |
|---|---|
| Brand | Forest green, `#253d2e` |
| Environmental | Green |
| Social | Blue |
| Governance | Violet |
| Gamification | Orange |
| Surfaces | Near-white / light translucent glass |
| Type | Manrope with system font fallback; tight tracking for large headings |
| Motion | Framer Motion springs; no decorative looping motion |

## Layout requirements

- Login is the first screen and includes sign-in plus account-creation states.
- Desktop workspace has a persistent sidebar containing the full ESG hierarchy from the provided wireframe.
- Dashboard includes E/S/G/overall KPI cards, emissions trend, people activity, department momentum and next actions.
- At mobile widths, sidebar converts to a dismissible drawer and content stacks into one column.

## Motion and accessibility

- Press feedback is immediate; use spring transitions for cards, form state changes and navigation.
- Scroll-linked motion is limited to subtle background depth, never essential content.
- `prefers-reduced-motion` removes spatial movement while retaining status feedback.
- Text and form controls must retain clear contrast, labels and error states.
