# Visual Style Master

Use this reference when the user provides a reference image, approved sample, good example, bad example, or asks for style continuity.

The style master is not a color picker. It is the full-page rhythm that made the prior slide work.

## What To Extract

Capture these traits before writing prompts:

- Action-title scale, weight, and placement.
- Subtitle position, length, and visual weight.
- Main proof-object type and dominance.
- Evidence band structure and density.
- Bottom-takeaway treatment: heavy banner, light rule, or omitted.
- How numbers are embedded in the proof object.
- Palette role: base, anchor, accent, risk color.
- Typography mood, icon style, line weight, shadows, material treatment.
- Page rhythm: where the eye lands first, second, and last.

Write a short `Style master notes` block in the slide brief. Example:

```markdown
Style master notes:
- Large action title at top; subtitle directly below.
- One central proof object dominates the page.
- Evidence band supports the proof object instead of becoming a KPI dashboard.
- One strong bottom takeaway; source notes remain small and quiet.
- Green is an anchor for gates and status, not the whole page.
```

## Color And Linework Discipline

Color and linework must express information hierarchy, not decorate every module.

- Use the main brand color for orientation, mechanism emphasis, key words, or selected status cues.
- Use pale fills only where they carry a role: a mechanism area, evidence band, validation zone, or bottom conclusion band.
- Do not give every evidence item a filled card. Prefer whitespace, alignment, typographic hierarchy, and light dividers.
- Use heavy borders only when a boundary is part of the proof object. Otherwise use thin rules or no border.
- Bottom conclusion bands may use a pale fill without an outline. Do not make them look like buttons or UI alerts unless that is the chosen style.
- If every module has a border, shadow, or pale fill, the page has lost hierarchy; remove frames before changing colors.

## What To Preserve

Preserve:

- Information density target.
- Relationship between title, proof object, evidence band, and takeaway.
- Color proportions, not just hex values.
- Level of visual force: calm report, strong executive exhibit, or hero concept.
- Whether the bottom conclusion is a heavy banner or a light closing line.

Do not preserve:

- Private client names.
- Local paths.
- Case-specific brand references.
- Sensitive screenshots or assets.
- A prior page's exact takeaway noun when the new claim needs another noun.

## Style Conflicts

If the style master conflicts with the new user request, call out the tradeoff before prompting.

Examples:

- User wants dense standalone report, but style master is sparse live-presentation page.
- User wants green palette, but style master relies on blue/black authority.
- User wants many caveats, but style master has only one low-weight source note.

Resolve by preserving the page rhythm first, then adapting palette and content density.

## Prompt Guidance

Use language like:

```text
Use the provided reference as the strict style master for page rhythm: action-title scale, subtitle weight, central proof-object dominance, evidence-band density, bottom-takeaway treatment, typography mood, line weight, and color proportions.
Do not interpret it as only a palette reference.
```

Avoid:

- "Use the same colors" without rhythm details.
- Copying every object position exactly.
- Turning a reference exhibit into generic cards because the new content has many bullets.

## Acceptance Check

The generated sample should feel like it belongs to the same deck family as the style master:

- Same first-glance hierarchy.
- Similar information density.
- Similar relationship between proof object and evidence band.
- Same restraint around color and notes.
- No extra conclusion zones that were not present in the style master.
