# Worker Compact Protocol v3 Preview

This is the default short protocol for per-slide workers in multi-page multi-Agent runs.
It is intentionally compact: read this first, then read fallback references only
when blocked or when a QA gate needs the longer explanation.

## Default Reading Order

Read only these files before conversion:

1. `AGENT_TASK.md`
2. `slide_job_manifest.json`
3. `page_conversion_contract.json`
4. `crop_manifest_contract.json`
5. `WORKER_COMPACT_PROTOCOL.md`

Do not read full references, old round outputs, previous QA HTML, process audit
reports, or baseline artifacts unless the task explicitly tells you to diagnose
or compare them.

## Conversion Rules

- Use the bundled v3 preview single-page scripts as the primary engine.
- Keep meaningful text editable when practical.
- Group same-style semantic multiline body/callout text into one text box.
- Use Microsoft YaHei for generated Chinese text.
- Clear unwanted native shadows, glow, bevel, reflection, and soft edge.
- Do not add invented pale text backing rectangles.
- Do not force native redraw for complex artwork, product images, detailed icon
  groups, curved/gradient arrows, textured modules, or source-specific panels.
- Use source crop or textless crop plus editable text when native redraw would
  visibly drift.
- Preserve non-text anchors: arrows, arrowheads, route lines, connectors, step
  markers, card edges, dividers, icons, and cut corners.
- Do not use a whole-slide textless crop unless explicitly accepted as fallback.
- A 3-5 region crop plan must be backed by real bounded region crops or native
  objects. If multiple regions all use the same whole-slide/background picture as
  evidence, mark the slide `failed-retryable` or `image-fallback`; do not report
  `passed` or `accepted-with-limitations`.
- Sequential token-saving is retired and must not be used for release workflows.

## QA Rules

Before returning success, produce:

- `slide.pptx`
- `render_report.json`
- `visual-qa-comparison.html`
- `editability_report.json`
- `crop_manifest.json`
- `qa_summary.json`

`qa_summary.json` must report:

- `references_read`: the compact required-reading ids actually read;
- `fallback_references_read`: fallback references read, or an empty list;
- `font_policy_applied`;
- `effects_cleared`;
- `font_size_consistency_review`;
- `complex_visual_strategy_review`;
- `text_background_policy`;
- `non_text_anchor_preservation_review`;
- `single_page_engine_used`;
- `single_page_engine_scripts_used`;
- real worker identity.

## Fallback Reading

Read the longer references only when needed:

- `SKILL.md`: if the compact protocol conflicts with task setup or mode choice.
- `source-crop-tools.md`: if crop/textless crop manifests are unclear.
- `reconstruction-qa.md`: if a reconstruction QA gate fails.
- `source-reconstruction-plan-schema.md`: if plan schema is unclear.
- `ocr-to-plan-review-guide.md`: if OCR scaffold text needs review.
- `visual-fidelity-contract.md` or `visual-fidelity-execution.md`: if visual
  fidelity rules are ambiguous.
- `multi-agent-slide-protocol.md`: if worker identity, handoff, or deck-level
  protocol is unclear.

If a fallback reference is read, list it in `fallback_references_read` and keep
the reason short.
