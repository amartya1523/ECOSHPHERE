# Design — EcoSphere

## Visual Tone
Dark-mode-first, data-dense enterprise dashboard — confirmed from the actual mockup (4 screenshots reviewed, not just the unreadable Excalidraw link). Near-black backgrounds throughout, with each ESG pillar carrying its own accent color to orient the user at a glance (green=Environmental, blue=Social, purple=Governance, orange=Gamification). Every screen carries a small red/amber/green "traffic light" dot cluster as a window-chrome motif in the top bar — purely decorative branding, consistent across all modules. Gamification screens lean into the orange accent and card-based layouts more than the data-table-heavy Environmental/Social/Governance screens.

**Source:** actual mockup screenshots (4 images) reviewed directly — this supersedes the earlier placeholder palette guessed before the mockup was viewable.

## Layout Structure (confirmed from mockup)
- **Left sidebar** (Dashboard view only): full navigation tree grouped by module — Dashboard, Environmental, Social, Governance, Gamification, Reports, Settings — each with its sub-items listed (e.g. under Environmental: Emission Factors, Product ESG Profiles, Carbon Transactions, Environmental Goals). Icon + colored label per top-level module.
- **Top tab bar** (all module screens): horizontal tabs for Dashboard / Environmental / Social / Governance / Gamification / Reports / Settings — the primary navigation once inside a module, sidebar is dashboard-only.
- **Sub-tab bar** within each module screen: e.g. Environmental → [Emission Factors | Product ESG Profiles | Carbon Transactions | Environmental Goals]; Governance → [Policies | Policy Acknowledgements | Audits | Compliance Issues]; Gamification → [Challenges | Challenge Participation | Badges | Rewards | Leaderboard]; Reports → [Environmental | Social | Governance | ESG Summary | Custom Builder]; Settings → [Departments | Categories | ESG Configuration | Notification Settings].
- **Window-chrome bar**: every module screen has a light-gray header strip with the 3 traffic-light dots + "EcoSphere: {Module}" label — treat as a reusable header component.

## Color Palette
| Role | Color | Hex (approx.) |
|---|---|---|
| Background (page) | Near-black | #0F0F0F |
| Background (card/panel) | Dark gray | #1A1A1A |
| Window-chrome bar | Light gray | #C9CDD3 |
| Environmental accent | Green | #3FAE5C |
| Social accent | Blue | #3B8FE0 |
| Governance accent | Purple | #8B5FE0 |
| Gamification accent | Orange | #E0812E |
| Overall/Score (neutral) | Blue | #3B8FE0 |
| Text (primary, on dark) | Off-white | #E8E8E8 |
| Text (muted/label) | Gray | #9AA0A6 |
| Success / Approved / Active | Green | #4CAF6D |
| Warning / Pending / Medium severity | Amber | #E0A83B |
| Error / Open issue / High severity | Red | #D9534F |
| Info / Completed / Under Review | Blue-Purple | #6C7FE0 |

Score cards on the Dashboard use a colored **border** (not fill) matching the pillar accent, on a dark card background — Environmental=green border, Social=blue border, Governance=purple border, Overall=blue border.

## Typography
- Heading font: Inter or system-ui sans-serif (clean, geometric — matches the mockup's crisp label style)
- Body font: Inter / system-ui fallback
- Scale: base 14px, section headings ~18-20px with a numbered-circle prefix (①②③ etc. — seen in mockup section headers), score numbers large (~28-32px) and bold

## Spacing & Theme Conventions
- Rounded corners on all cards/buttons/badges (~6-8px radius), consistent across score tiles, activity cards, challenge cards, badge tiles.
- Status pills/badges (Active, Pending, Approved, Open, High, etc.) are small rounded-rect labels with color-coded background matching their semantic state (see palette above) — used consistently across Employee Participation, Compliance Issues, Challenges, Audits.
- Challenge cards and CSR Activity cards: bordered card (accent-colored outline), title + icon, key stat line (XP/Difficulty/Deadline or joined-count), status pill, primary action button (Join Challenge / Join) pinned at the bottom.
- Progress bars (Environmental Goals): horizontal bar with percentage label, green fill, used consistently for goal-tracking rows.
- Dashboard KPI tiles: large bold number + label + colored border, arranged in a 4-across row (Environmental / Social / Governance / Overall).
- Bar and line charts (Emissions Trend, Department ESG Ranking): minimal axis styling, single accent color per chart, no gridlines clutter — matches the dark, low-noise aesthetic.
- Follow Odoo's Bootstrap-based spacing utilities (`.p-*`, `.m-*`) for implementation, but override Odoo's default light theme with this dark palette via SCSS — do not attempt to reskin every native Odoo widget, focus dark-theme overrides on EcoSphere's own views first.
