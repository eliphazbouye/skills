---
name: imprint
description: Keep a project's UI coherent across many sessions by capturing its real component patterns into context/project/ui-registry.md, then finding where the codebase has drifted from them. Scans the UI for buttons, spacing, color, typography and other recurring patterns, reconciles them against the registry, updates the registry with the canonical set, and produces a fix list of the inconsistencies — without mass-editing the code. Use after several sessions of UI work, when buttons/spacing/tokens have started to diverge, before a design pass, or whenever the user says "imprint", "capture the design system", or "the UI is drifting".
---

# Imprint

The failure this prevents: you build UI across many sessions, and each session quietly invents its own version of the same thing. By session three the buttons don't match, the spacing is off by a few pixels in half the screens, and the "design system" has accumulated small contradictions nobody decided on. None of it is visible in any single diff — it only shows up when you look at everything at once. This skill is that look.

The goal is not to redesign anything. The goal is to **make the design system explicit and find where the code has wandered from it** — capturing the canonical patterns into `context/project/ui-registry.md` so future sessions build against a written standard instead of guessing from whatever file they happened to open.

There are two outputs, and they're different:

- **The registry** (`context/project/ui-registry.md`) — this skill *writes*. It is the source of truth for UI patterns, and keeping it current is the whole point.
- **The fix list** — this skill *reports*, it does not apply. Like a review, it hands you the inconsistencies and you decide what to change.

## The rules

1. **The registry is canonical; the code is evidence.** When the registry and the code disagree, the registry usually wins — that's drift to be fixed. But the code is how new, legitimate patterns appear. A value that shows up consistently in recent code and contradicts the registry might be an intentional evolution, not a mistake. Don't silently overwrite either side.
2. **Drift vs. decision — when unsure, ask.** A one-off `padding: 14px` among twenty `16px` buttons is drift. A new card variant used coherently across five screens is a decision. The hard cases are in between. When you can't tell whether a divergence is a mistake to fix or a new pattern to adopt, surface it and let the user decide — don't guess and bake the guess into the registry.
3. **Capture what's real, not what's ideal.** The registry records the patterns the codebase actually uses, not the design system you wish it had. Don't invent tokens, rename things to be tidier, or import conventions from elsewhere. If the project uses three button styles, the registry says three — and the fix list flags whether that's intended.
4. **Never mass-edit the code.** The fix list is the deliverable. Even an obvious find-and-replace gets reported, not applied, unless the user explicitly asks you to apply a specific fix. One careless sweep across a design system can break more than it fixes.
5. **Concrete over vague.** Every registry entry and every fix names real values and real locations. "Buttons are inconsistent" is useless. "`Button` primary uses `px-4 py-2` in 12 files but `px-3 py-2` in `SettingsForm.tsx:40` and `Modal.tsx:88`" is a finding — with clickable file:line links.

## Process

### 1. Load the standard, if there is one

Read `context/project/ui-registry.md` if it exists — that's the baseline to reconcile against. If it's still at the old location (`context/ui-registry.md`), move it to `context/project/` first (`git mv` if the repo is tracked) and update any `CLAUDE.md` pointer to it. Also read `./context/` more broadly, CLAUDE.md, and any design-token source the project already has: a Tailwind/theme config, a tokens file, a component-library setup, CSS variables. These are stronger evidence of intent than scattered component code.

If there's no registry yet, this is the **bootstrap run**: there's nothing to reconcile against, so the job is to build the first registry from the codebase. Say so up front — the output will be the new registry plus whatever inconsistencies already exist in it.

### 2. Find the UI surface

Determine what to scan. Locate the components and styles — the component directory, shared/primitive UI folder, stylesheets, theme config. Prefer the project's own structure over guessing; if it's unclear, ask where the UI lives rather than scanning the whole tree.

For a large or sprawling UI, this is worth fanning out: have parallel readers each sweep a slice (one for buttons/controls, one for spacing/layout, one for color/typography, one for the token/theme config) and report the values they find. You only need the extracted patterns back, not the file dumps.

### 3. Extract the patterns actually in use

Across the UI, pull out the recurring patterns and their concrete values. Cover at least:

- **Components & variants** — buttons, inputs, cards, modals, badges, etc., and the variants of each. What props/classes define each variant, and what does it render.
- **Spacing** — padding/margin/gap scales, and whether they come from tokens or hardcoded values.
- **Color** — palette, semantic roles (primary/danger/muted), and where raw hex/rgb values bypass the tokens.
- **Typography** — font families, sizes, weights, line-heights, and the scale they're supposed to follow.
- **Radius, borders, shadows, transitions** — the smaller tokens that drift quietly.

For each pattern, note the dominant value (what most of the code does) and the outliers (what diverges, and where). The outliers are the raw material for both the reconciliation and the fix list.

### 4. Reconcile against the registry

Put the extracted reality next to the registry (or, on a bootstrap run, against itself — what's internally consistent vs not). Sort every divergence into one of three:

- **Drift** — code that diverges from a clear, dominant standard for no reason. Goes on the fix list; the registry value stands.
- **New pattern** — a coherent pattern the registry doesn't yet describe. Gets added to the registry. If it *replaces* an old pattern, that's a decision — confirm with the user before retiring the old one.
- **Ambiguous** — can't tell which of the above. Don't resolve it silently. Collect these and ask the user, one clear question per genuine fork (per rule 2).

Resolve the ambiguous cases with the user before writing anything.

### 5. Update the registry

Write the reconciled, canonical patterns to `context/project/ui-registry.md`. Keep it a working reference, not prose: each pattern with its canonical value, its variants, and where the source of truth lives (token name, config file, primitive component). New patterns get added; retired ones get removed only after the user confirms. The registry should be something the *next* session can read and build against without re-deriving any of this.

### 6. Report the fix list

Present the inconsistencies directly in the conversation — don't write them to a file unless asked. Group by what kind of coherence they break (e.g. Buttons, Spacing, Color, Typography), and within each, order by how widespread the divergence is. For each finding: the file:line link, the canonical value, the divergent value found there, and the one-line fix.

Be explicit about what changed in the registry (new patterns captured, anything retired) versus what's left for you to fix in the code. Then stop — applying the fixes is the user's call, one at a time or in a batch they approve.
