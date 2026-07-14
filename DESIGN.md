# Design System — CSV AI Generator

## Context and goals
The CSV AI Generator is a cloud-platform-style data tool: schema design → synthetic data generation → DB export. The visual language must reduce friction for a long, multi-step workflow while staying approachable. We adopt an enterprise, dark, Heroku/Vercel-like aesthetic with IBM Plex Sans, an 8pt spacing grid, and 6 semantic color tokens.

## Design tokens and foundations

### Color
| Token | Value | Use |
|---|---|---|
| `--primary` | `#0C5CAB` | Primary actions, active tab underline, focus ring base |
| `--secondary` | `#0a4a8a` | Hover/active states on primary controls |
| `--success` | `#10b981` | Schema locked, generation completed, DB push OK |
| `--warning` | `#f59e0b` | Partial generation, replaced target, near-limit inputs |
| `--danger` | `#ef4444` | Errors, validation failures, generation aborted |
| `--surface` | `#09090b` | App background |
| `--surface-panel` | `#141417` | Cards/containers (1 step above surface) |
| `--border-subtle` | `#27272a` | 1px dividers, panel edges |
| `--text` | `#fafafa` | Primary copy |
| `--text-muted` | `#a1a1aa` | Captions, secondary labels |
| `--text-soft` | `#71717a` | Disabled, placeholder |

Required contrast ratios (WCAG 2.2 AA): `--text` on `--surface` ≥ 4.5:1, `--primary` on `--surface-panel` ≥ 4.5:1, `--text-muted` on `--surface` ≥ 4.5:1.

### Typography
Fonts: IBM Plex Sans for display, body, and mono (single-family = consistency). The scale is `12 / 14 / 16 / 20 / 24 / 32`:
- `--text-display-2xl` 32 / 40 / 600 — page title
- `--text-display-xl`   24 / 32 / 600 — section header
- `--text-display-lg`   20 / 28 / 500 — subheader
- `--text-body-lg`      16 / 24 / 400 — primary body
- `--text-body`         14 / 20 / 400 — default UI text
- `--text-caption`      12 / 16 / 400 — captions, metadata

### Spacing
8pt baseline grid: `4 / 8 / 12 / 16 / 24 / 32`. Vertical rhythm between sections MUST be 24 or 32. Inner component padding MUST be 16. Tight gaps inside rows MAY be 8 or 12.

### Radii, borders, shadows
- `--radius-sm` 6px — inputs, small buttons
- `--radius-md` 8px — default buttons, panels
- `--radius-lg` 12px — card containers
- `--border-1` 1px solid `--border-subtle`
- `--shadow-panel` `0 1px 2px rgba(0,0,0,0.3), 0 8px 24px -8px rgba(0,0,0,0.5)`
- Glass-like panels: `background: rgba(20,20,23,0.72); backdrop-filter: blur(8px)`

### Motion
Transtions limited to 150ms ease-out for state changes. No decorative animation. Must respect `prefers-reduced-motion: reduce` — disable transitions.

### Focus
All interactive elements MUST show a 2px outline `--primary` with 2px offset on `:focus-visible`. Never rely on outline:none. Minimum 44x44px hit area.

## Component-level rules

### Page header
- Title uses `--text-display-2xl` (32/40/600) in `--text`
- Caption directly below uses `--text-caption` (12/16) in `--text-muted`
- Vertical spacing from header to first content MUST be 32

### Section header
- `--text-display-lg` in `--text`
- Optional caption (12 muted) 8px below
- 24px space below before content

### Panel (container component)
```html
<section class="panel">
```
- `background: var(--surface-panel)`
- `border: var(--border-1)`, `border-radius: var(--radius-lg)`
- `padding: 16`, `shadow: var(--shadow-panel)`
- Used to wrap: schema editor, data preview, db export form

### Button (Streamlit primary/secondary overrides)
States: default | hover | focus-visible | active | disabled | loading
- Default: `background: var(--primary)` `color: white` `border-radius: var(--radius-md)`
- Hover: `background: var(--secondary)`
- focus-visible: `outline: 2px solid var(--primary); outline-offset: 2px`
- Disabled: `background: var(--surface-panel)` `color: var(--text-soft)` `cursor: not-allowed`
- Min height: 40px (≥44 when touch)
- No decorative icons; labels alone

### Text input / selectbox / textarea
- Default bg `--surface-panel`, border `--border-subtle`
- focus: border 2px `--primary`, no glow (motion-safe 150ms border-color)
- placeholder color `--text-soft`
- 40px tall hit area

### Tabs
- Active tab text `--text` weight 600 with 2px underline `--primary`
- Inactive tab text `--text-muted` weight 400
- Tab container `border-bottom: var(--border-1)`

### Data table (dataframe/data_editor)
- Header: `surface-panel` bg, 14/600 in `--text`
- Body: 14/400 in `--text`
- Row hover: `rgba(255,255,255,0.04)`
- Borders between rows: 1px solid `--border-subtle`

### State banners (empty / loading / error / success / warning)
- Empty: `--text-muted` body inside panel; centered
- Loading: linear progress bar in `--primary` (1.5px tall) and caption text
- Success: `--success` accent + `--primary` mask text box with 8px padding
- Warning: `--warning` accent text and matching 8px left border on panel
- Error: `--danger` accent text and matching 8px left border on panel

### Caption system
- Stats caption `f"{rows} rows · {cols} cols · {size} KB"` uses `--text-caption` in `--text-muted`
- Spacing: 8px to data table below

### DB export form
- Single 1-column layout for selectbox + uri toggle → 1 column for credentials → 1 row for target + if_exists → primary button full-width
- Credentials row: 2 sub-cols for Host/Port, 2 sub-cols for User/Password, 1 input for DB name
- Vertical rhythm: 8px between inputs in a row, 16px between rows

## Accessibility requirements (testable)
1. Every text input MUST pair a visible `<label>` (resolved by Streamlit's default `label` rendering — do not hide with CSS).
2. Every primary button MUST get a focus-visible outline using `--primary`. Acceptance: Tab through page, each focus ring visible.
3. Color-contrast: caption on surface ≥ 4.5:1; primary on panel ≥ 4.5:1.
4. Reduced motion: transitions disabled under `@media (prefers-reduced-motion: reduce)`.
5. Touch targets ≥ 44x44px on all buttons (override Streamlit default 38px).
6. Status messages (success/error/warning) use Streamlit's `st.success/st.error/st.warning` — these produce `<role=alert>` semantic markup.

## Anti-patterns
- Do NOT use multiple accent colors on the same panel (e.g. primary button + warning checkbox). Pick one type per panel.
- Do NOT add bloom/glow; use box-shadow only for elevation.
- Do NOT mix border radii inside one panel.
- Do NOT override the focus ring outline appearance; only adjust color/offset.
- Avoid decorative motion (loading spinners beside static text, blinking cursors).

## QA checklist (code review)
- [ ] All colors sourced from CSS variables (no hex literals in Python)
- [ ] `prefers-reduced-motion` block present
- [ ] Focus ring visible on tab navigation
- [ ] Every primary button has only Streamlit `type="primary"` — no manual `background-color` overrides
- [ ] 8pt spacing applied between sections (24/32) and within (8/16)
- [ ] Empty and error states cover: no schema, no API key, no data, DB connection fails
- [ ] Tab labels are 1-3 word imperative verbs / nouns ("Schema Design", not "Step 1 — Schema")
- [ ] Panels use `--surface-panel` not `--surface` for container backgrounds