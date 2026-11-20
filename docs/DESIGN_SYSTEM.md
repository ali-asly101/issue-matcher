# DESIGN SYSTEM

Owner: Architect (tokens), Web agent (implementation in `web/`). Applies to the website, the HTML map export and any email the product sends. Visual reference: the screen designs linked from `docs/WEB_APP_SPEC.md`.

## Direction

**Clean, trustworthy, minimal but not empty.** The reference point is Stripe's dashboard and docs: a calm neutral base, white surfaces, dark text, one accent colour, status colours that always mean the same thing, plain-language labels, sensible defaults with advanced options collapsed, and every number or decision explained. We borrow those principles, not Stripe's brand (no Stripe purple, no gradient mesh, no copied layouts).

"Just enough" means: every screen has one job, one primary action, and enough real content (reasons, evidence, status) that it never looks like a template. Empty states show what the screen will look like and the one step to fill it.

## Typography

| Role | Font | Size / line height | Weight | Colour |
| --- | --- | --- | --- | --- |
| Display (marketing hero) | Arial | 44 / 52 px | 700 | `ink` |
| Page title | Arial | 24 / 32 px | 700 | `ink` |
| Section title | Arial | 18 / 26 px | 700 | `ink` |
| Card title | Arial | 15 / 22 px | 700 | `ink` |
| Body | Arial | 14 / 22 px | 400 | `ink` |
| Secondary | Arial | 13 / 20 px | 400 | `ink-2` |
| Caption / meta | Arial | 12 / 16 px | 400 | `ink-3` |
| Numbers in tables | Arial, `font-variant-numeric: tabular-nums` | as row | 400 | `ink` |
| Code, keys, paths | `ui-monospace, Menlo, Consolas, monospace` | 12.5 / 18 px | 400 | `ink` |

- Font stack: `Arial, "Helvetica Neue", Helvetica, sans-serif`.
- Arial has two real weights, 400 and 700. Build hierarchy with size and colour first; use 700 only for titles and key values. Never fake 500/600.
- Letter spacing: -0.01em on display and page titles only.
- Sentence case everywhere (buttons, headings, tabs). No ALL CAPS except tiny 11 px table headers if needed.

## Colour

One accent, a cool neutral ramp, and four status colours. All text/background pairs below meet WCAG AA (4.5:1) for body text.

### Neutrals

| Token | Hex | Use |
| --- | --- | --- |
| `ink` | `#101828` | Primary text, headings |
| `ink-2` | `#475467` | Secondary text, labels |
| `ink-3` | `#667085` | Captions, placeholders, meta |
| `line` | `#E4E7EC` | Borders, dividers |
| `line-strong` | `#D0D5DD` | Input borders, hover borders |
| `canvas` | `#F7F8FA` | App background |
| `surface` | `#FFFFFF` | Cards, panels, tables |
| `surface-2` | `#F2F4F7` | Subtle fills: table header, code, chips |

### Accent (cobalt)

| Token | Hex | Use |
| --- | --- | --- |
| `accent` | `#2E5BFF` | Primary button, links, focus ring, selected state |
| `accent-hover` | `#1F45D6` | Primary button hover |
| `accent-soft` | `#EEF2FF` | Selected row, active nav, info badge background |
| `accent-ink` | `#1E3A8A` | Text on `accent-soft` |

### Status (always the same meaning)

| Token | Text | Soft background | Meaning |
| --- | --- | --- | --- |
| `success` | `#067647` | `#ECFDF3` | Good fit, connected, verified skill, written to tracker |
| `warning` | `#B54708` | `#FFFAEB` | Stretch pick, declared (unverified) skill, dry-run, needs attention |
| `danger` | `#B42318` | `#FEF3F2` | Broken connection, write failed, destructive action |
| `neutral` | `#475467` | `#F2F4F7` | Pending, maybe, unknown |

Fit scores use the same scale everywhere: `success` for strong fit (score >= 0.7), `accent` text for good (0.5 to 0.7), `neutral` for weak. Never use red for a low score; red only means something is broken or destructive.

### Dark mode

Later (S5). Tokens are named by role so a dark theme is one token file.

## Spacing, layout and shape

- 4 px base grid. Common steps: 4, 8, 12, 16, 24, 32, 48, 64.
- App shell: 240 px left sidebar, 56 px top bar, content max width 1200 px, 32 px page padding.
- Marketing pages: max width 1120 px, 96 px vertical section spacing.
- Radius: 6 px for inputs and buttons, 10 px for cards and panels, 999 px for pills and avatars.
- Borders: 1 px `line`. Shadows only for floating layers (menus, dialogs): `0 8px 24px rgba(16,24,40,0.08), 0 2px 6px rgba(16,24,40,0.06)`. Cards are flat with a border, no shadow.
- Density: table rows 44 px, list rows 56 to 72 px, form controls 36 px (40 px on marketing pages).

## Components

| Component | Rules |
| --- | --- |
| Button | Primary (filled `accent`, white text), secondary (white, `line-strong` border, `ink` text), ghost (text only), danger (filled `danger`, only in confirm dialogs). One primary per view. Verb first: "Connect Jira", "Assign", "Claim ticket". |
| Input / select | 36 px, 1 px `line-strong`, 6 px radius, 3 px `accent` focus ring at 25% opacity. Label above, helper text below in `ink-3`, error text in `danger`. |
| Card | `surface`, 1 px `line`, 10 px radius, 20 to 24 px padding. Title row, body, optional footer with actions on the right. |
| Badge / pill | 12 px text, 2 px 8 px padding, soft status background with matching text colour. |
| Skill chip | Pill with a leading dot: green dot = verified by evidence, amber dot = declared or from CV, grey = inferred. Removable (x) on the person's own profile. |
| Fit meter | Score number (700 weight) plus a 4 px bar in the fit colour. Always paired with confidence text ("High confidence"). |
| Reason line | 13 px `ink-2`, starts with an icon (code, ticket, clock, sparkle for "want to learn"), links to the evidence (PR, ticket, commit). |
| Table | Header row `surface-2`, 12 px `ink-2` labels; rows separated by `line`; numbers right-aligned and tabular. |
| Status row (integration) | Logo, name, connected account, last sync time, health badge, "Manage" button. |
| Empty state | Small illustration or ghost preview of the filled screen, one-sentence explanation, one primary action, optional secondary link. Never "Nothing here yet." |
| Toast | Bottom-left, 4 s, one at a time, past-tense confirmation ("Assigned in Jira"). |
| Dialog | For confirmations that write to a tracker or delete data. Shows exactly what will happen ("Set assignee to Aisha and add this comment:" + preview). |
| Icons | One outline set (Lucide or Tabler), 1.5 px stroke, 16 px inline, 20 px in nav. |

## Content and voice

- Plain words, no jargon: "Good fit", "Stretch", "Already taken", not "match coefficient".
- Say what happened and what to do: "Jira disconnected. Reconnect to keep syncing."
- Show the math when we can: "Similar fixes changed 30 to 90 lines (#6044, #6187)."
- No exclamation marks, no "simply", no "please", no fake urgency.

## Trust patterns (apply on every screen)

1. **Explain every suggestion** in one or two reason lines with links to the evidence; let people drill down for more.
2. **Show confidence** honestly; low-confidence items sit in a separate "Maybe" group.
3. **Let people correct the system**: "Not for me", "Wrong skill", edit profile, undo. Overriding is a feature, not an error.
4. **Preview every write** to a tracker before it happens; show dry-run clearly with a `warning` banner.
5. **Keep integrations visible after setup**: last sync, health, scopes, one-click reconnect, clear disconnect.
6. **Never hide state changes**: activity log, timestamps, who approved what.

## Accessibility

- AA contrast for all text; focus ring on every interactive element; full keyboard support (Cmd/Ctrl+K command menu later).
- Never use colour alone: every status has text or an icon too.
- Respect `prefers-reduced-motion`; motion is 120 to 200 ms ease-out, fades and small slides only.

## Implementation notes (for the Web agent)

- Tokens as CSS custom properties in `web/src/styles/tokens.css`; components read only tokens.
- Suggested base: Radix primitives (accessible behaviour) styled with these tokens. No component library theme on top.
- Every new component gets a story or a test page showing all states (default, hover, focus, disabled, loading, error, empty).
