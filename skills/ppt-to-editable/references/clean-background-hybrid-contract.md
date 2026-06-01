# Clean Background + Editable Text Contract

Use this reference when the output mode is `clean-background`.

This mode turns a source image slide into a PowerPoint slide with a clean/textless background and editable text boxes. It is useful only when the old visible source text is removed or regenerated away; a visible overlay on top of old source text is not an acceptable final output.

Do not use this mode as the default for a multi-page source. For manually split or experimental multi-page inputs, first route each slide with `references/deck-routing-and-qa.md`. Structured pages dominated by simple cards, rows, product pills, tables, process steps, and native-friendly lines should usually be routed to reconstruction instead.

## Output Contract

Each final slide must contain:

- one full-slide 16:9 clean background image;
- native PowerPoint text boxes for all final visible text;
- no readable source text, duplicate text, fake text, pseudo text, numbers, watermarks, or OCR residue embedded in the background.

Allowed in the background:

- visual structure, proof objects, photos, screenshots, icons, connectors, containers, shadows, gradients, texture, and reserved text zones;
- non-text decorative marks that cannot be mistaken for words.

Not allowed in the background:

- title text, subtitle text, labels, notes, body copy, source lines, page markers, numeric badges, or source glyph fragments that should become editable.

## Workflow

1. Save the source image unchanged.
2. Run OCR and save `ocr_results.json`.
3. Create `ocr_overlay_debug.png` when practical.
4. Create `ocr_review_manifest.json`; do not send raw OCR directly to the final PPTX.
5. Build a text removal mask from accepted/corrected OCR bboxes and manually marked OCR misses only.
6. Classify text regions before removal: dark text, light text on dark header, colored labels, composite badges, complex visual text.
7. Remove source text locally and save `text_mask_debug.png`.
8. Inspect the textless background before packaging.
9. Create `text_layout_manifest.json` from OCR line boxes or reviewed corrections.
10. Use line-level trace by default when source line breaks matter.
11. Package with `scripts/package_clean_background_deck.py`.
12. Inspect the PPTX with `scripts/inspect_pptx_editability.py`.
13. Write `editability_report.json`.

## Source-Image Text Removal

Text removal must begin from source text geometry, not final text-box guesses.

Use these region policies:

- `dark_text_on_light`: mask dark or colored ink inside the OCR bbox; preserve pale backgrounds and card borders.
- `light_text_on_dark_header`: use the full local header/title bbox when white-pixel masking leaves residue.
- `colored_label`: mask saturated colored ink while preserving nearby pale rules.
- `composite_badge`: remove the source badge region, rebuild the simple ring/circle natively when practical, then overlay the number as editable text.
- `complex_visual_text`: remove the source text pixels or a small local region, then keep the complex visual behind editable text.

Repeated modules require instance-level geometry. Do not copy coordinates from a visually similar badge, header, icon, or label unless source geometry confirms the match.

## Text Placement

Default to line-level trace:

- one editable text box per visible OCR line;
- `trace_level: "line"`;
- `no_wrap: true`;
- `source_bbox_px` from OCR;
- OCR confidence and review status;
- no PowerPoint auto-fit.

Use paragraph groups only when the user prioritizes easier paragraph editing. If the preview drifts, switch back to line-level trace.

## Manifest Rules

All final text comes from `text_layout_manifest.json`.

For each text box, include:

- `text`;
- `x`, `y`, `w`, `h`;
- `role`;
- font family, font size, color, bold/italic, alignment;
- OCR provenance fields when the page starts from an image.

For line-level trace, also include:

- `ocr_id`;
- `source_bbox_px`;
- `trace_level: "line"`;
- `no_wrap: true`;
- `review_status`;
- `original_font_size` and `font_fit` when mechanical fitting was used.

## QA Checklist

Reject the run if:

- the final background still contains readable source text;
- editable text duplicates visible background text;
- OCR was skipped for an image-source quality run;
- raw OCR was accepted without review;
- text boxes rely on PowerPoint auto-wrap to reproduce source line breaks;
- dark headers, badges, counters, or labels show glyph residue behind the editable layer;
- text overflows its reserved region;
- a structured page is visibly worse because simple objects were inpainted instead of reconstructed;
- the output lacks an editability report.

Acceptance checks:

- `slides` equals expected page count;
- `backgroundPictures` equals slide count;
- `editableTextBodies` is greater than zero;
- in line-level trace, accepted OCR line count equals editable text body count or every omitted line has an `omit_reason`;
- no-wrap and no-autofit are present on line-level text boxes;
- the preview is close enough that remaining differences are documented rather than hidden.

## Failure Labels

- `duplicate source text`
- `dirty text removal`
- `source text residual`
- `ocr unavailable`
- `ocr bbox drift`
- `text layer misaligned`
- `auto-wrap linebreak drift`
- `dark-header text residual`
- `composite badge duplicated`
- `repeated module coordinate assumption`
- `structured page forced into hybrid`
- `raw ocr accepted without review`
- `dirty inpaint inside simple shape`
