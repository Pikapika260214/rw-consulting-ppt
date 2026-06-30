---
name: ppt-to-editable
description: Use when converting a single-page slide image, such as a PNG/JPG slide export or screenshot, into an editable PowerPoint PPTX with OCR review, clean backgrounds, reconstruction, native simple shapes, or tight source crops.
---

# PPT to Editable

Convert an existing single-page slide image into a more editable PowerPoint file. This skill currently supports one image input at a time: a PNG/JPG slide export, a screenshot saved as an image, or an approved generated slide image.

This skill does not generate a new consulting deck from notes, bullets, research, or page outlines. Use the separate deck-generation skill for that. This skill is a conversion layer.

## Core Rule

Do not ship a visible text-overlay result where the original text-bearing image remains underneath editable text. That is duplicate text, not useful editability.

The final PPTX must either:

- use a clean/textless background plus editable PowerPoint text; or
- reconstruct simple elements as native PPT objects and keep only complex visuals as tight source-derived crops.

OCR is required for quality runs that start from images. OCR is not only for reading words; it provides source text geometry for text removal, editable text placement, line breaks, and QA.

Current public scope is single-image to single-slide PPTX. Multi-page PDF input, image-only PPTX input, automatic deck routing, and batch assembly are roadmap or experimental until they have public smoke-test evidence. For multi-page sources, first split/export them into individual images and process one page at a time.

## Reconstruction-First Hard Gate

For structured business slides, default to `reconstruction` or mixed reconstruction. This is an agentic reconstruction workflow, not a guaranteed one-click script. It may require a page-specific `source_reconstruction_plan.json`, tight crop extraction, and a page-specific build script before packaging.

Hard constraints:

- If a slide is dominated by cards, rows, columns, real tables, process steps, funnels, timelines, lanes, badges, simple arrows, or repeated modules, route it to `reconstruction` or mixed reconstruction first.
- Do not silently downgrade a reconstruction-friendly slide to `clean-background` just because a generic reconstruction packager is unavailable.
- If reconstruction is the right route but no reconstruction plan or implementation exists yet, stop and mark the slide `requires_reconstruction_plan`. A clean-background PPTX may be produced only as a clearly labeled interim baseline, not as the final conversion.
- A PPTX labeled `reconstruction` must include `source_reconstruction_plan.json` or an equivalent layer plan, plus `editability_report.json`.
- A reconstruction report must prove native reconstruction: `nativeShapes > 0` for shape/card/line pages, `nativeTables > 0` for semantic table pages, and tight `pictures` only for complex source crops. `editableTextBodies` alone is not reconstruction.
- A reconstruction PPTX must not contain a full-slide background disguised as reconstruction unless the user explicitly accepted that fallback.
- Hybrid fallback requires explicit user acceptance or a recorded limitation named `hybrid_fallback_explicitly_accepted`. Otherwise treat it as incomplete.

## Modes

### Mode 1: Clean Background + Editable Text

Use this when the user mainly wants to edit text while preserving the original visual quality, and the slide is visually complex enough that native reconstruction would drift.

- Start from the source slide image.
- Run OCR and save source text geometry.
- Remove original source text from the background using OCR-driven masks.
- Keep or regenerate a clean 16:9 background with no readable text, fake text, numbers, or watermarks.
- Place all final visible words as native PowerPoint text boxes from `text_layout_manifest.json`.
- Package with `scripts/package_clean_background_deck.py`.

Read `references/clean-background-hybrid-contract.md`, `references/ocr-layout-recovery.md`, and `references/text-layout-manifest.md`.

Do not force this mode onto structured pages dominated by cards, tables, rows, columns, numbered modules, pills, simple connectors, or flow diagrams. On those pages it often creates dirty inpainted backgrounds and weaker editability than reconstruction.

### Mode 2: Reconstruction

Use this when the user wants more native PPT editability and the page has simple shapes, cards, labels, lines, tables, or repeated modules.

- Rebuild readable text as native PowerPoint text.
- Rebuild simple geometry as native shapes: rectangles, rounded cards, circles, badges, rules, arrows, and true dashed lines.
- Rebuild table regions as native PowerPoint tables when the source is a real row/column grid; do not fake tables with separate lines, rectangles, or grouped boxes unless the user explicitly accepts that fallback.
- Keep complex visual regions as tight transparent PNG crops from the original source image: photos, product screenshots, gradients, shadows, curved translucent paths, dense diagrams, complex icons, and detailed illustrations.
- Do not approximate-redraw complex visuals just because a clean redraw looks close.
- Write a layer plan and editability report before delivery.

Read `references/reconstruction-contract.md` and `references/ocr-layout-recovery.md`.

Use reconstruction first for structured business slides: tables, repeated cards, layer diagrams, numbered process rows, product-pill matrices, decision grids, flowcharts, roadmaps, simple funnels, and pages where most visual objects are rectangles, lines, circles, badges, arrows, and labels.

### Native Shape Styling

For native reconstruction, default to flat PowerPoint objects. Do not introduce shadows, glow, bevel, reflection, soft edges, or theme effect styles unless the source image clearly uses that effect and it is necessary for fidelity. Simple cards, metric panels, bars, badges, separators, list rows, and chart scaffolds should be flat by default.

When building with python-pptx or direct OOXML, explicitly clear inherited `effectRef`, `effectLst`, and `effectDag` styling on generated native shapes, connectors, text boxes, and source-crop pictures. Do not add decorative shadows to make the output look more designed.

## Routing

If the input is a single image, screenshot export, or rasterized slide, OCR first. This is the public stable route.

For multi-page sources that have already been manually split into individual images, process each image as an independent single-slide job:

1. Extract each slide/page to an unchanged source image.
2. Create one slide job per source image.
3. Run OCR and review gates per slide.
4. Choose `clean-background`, `reconstruction`, or a mixed route per slide.
5. Build and preview each slide independently.
6. Do not present the assembled result as stable automatic deck conversion unless that experimental limitation is explicitly recorded.

If the user does not choose a mode:

- choose `reconstruction` for pages dominated by simple geometry, cards, tables, labels, and lines;
- use mixed reconstruction inside a page when appropriate: native simple layers plus tight crops for complex regions.
- choose `clean-background` only for visually complex slides where preserving look matters most and native reconstruction would visibly drift.

Read `references/deck-routing-and-qa.md` only for experimental multi-page work or whenever a single image has both hybrid-friendly visuals and reconstruction-friendly structure.

Never promise full-native conversion unless the user provides the original PPT, vector design file, or chart/source data.

## Required Artifacts

For image-source quality runs, keep:

- original source image, unchanged;
- `ocr_results.json`;
- `ocr_overlay_debug.png` when practical;
- `ocr_review_manifest.json` or equivalent per-slide QA report before packaging OCR text;
- `text_mask_debug.png` for clean-background text removal;
- `text_layout_manifest.json` for clean-background output, or `source_reconstruction_plan.json` for reconstruction;
- preview image or rendered inspection artifact;
- PowerPoint/LibreOffice-rendered PNG when the local runtime supports it;
- `editability_report.json`.

## Text Rules

For high-fidelity image-to-editable conversion, default to line-level trace:

- one editable text box per accepted OCR line;
- `trace_level: "line"`;
- `no_wrap: true`;
- OCR `source_bbox_px`;
- OCR confidence and review status;
- no PowerPoint auto-wrap or auto-fit fallback.

Use paragraph groups only when the user explicitly prioritizes easier paragraph editing over visual line-break fidelity. If paragraph grouping drifts, switch back to line-level trace.

For short labels, card captions, legend labels, badge numbers, and one-line conclusion snippets, avoid PowerPoint auto-wrap when a single trailing Chinese character or punctuation would fall to a new line. Widen the text box, reduce font size within the readable range, or set `no_wrap: true`; do not accept one-character orphan wraps as a valid reconstruction.

Never send raw OCR directly to the final PPTX. Classify each OCR record first as `accepted`, `corrected`, `needs_review`, `omit`, `keep_in_background`, or `reconstruct_as_native`. Low-confidence single glyphs, icon text, numeric badges, decorative symbols, and unsupported vertical/rotated text should not become accidental horizontal editable text.

## Packaging And QA

For clean-background output:

```powershell
python scripts/run_rapidocr.py path\to\source.png --out path\to\ocr_results.json --overlay path\to\ocr_overlay_debug.png
python scripts/package_clean_background_deck.py path\to\text_layout_manifest.json --out path\to\editable.pptx
python scripts/inspect_pptx_editability.py path\to\editable.pptx --out path\to\editability_report.json
```

For line-level trace fitting:

```powershell
python scripts/run_rapidocr.py path\to\source.png --out path\to\ocr_results.json --overlay path\to\ocr_overlay_debug.png
python scripts/apply_manifest_role_presets.py path\to\text_layout_manifest.json --out path\to\text_layout_manifest.roles.json
python scripts/fit_manifest_to_source_bboxes.py path\to\text_layout_manifest.roles.json --source path\to\source.png --out path\to\text_layout_manifest.bboxes.json
python scripts/fit_manifest_typography.py path\to\text_layout_manifest.bboxes.json --source path\to\source.png --out path\to\text_layout_manifest.fit.json
python scripts/judge_line_alignment.py path\to\text_layout_manifest.fit.json --source path\to\source.png --out path\to\line_alignment_judge.json
python scripts/apply_line_alignment_patch.py path\to\text_layout_manifest.fit.json path\to\line_alignment_judge.json --out path\to\text_layout_manifest.patched.json
```

Use `scripts/render_manifest_first_preview.py` or `scripts/render_manifest_alignment_preview.py` when a visual preview of source image plus editable text boxes is needed before packaging. Use `scripts/trace_manifest_to_line_boxes.py` when paragraph or block boxes fail to preserve source line breaks.

Before delivery, verify:

- final visible background has no source text residue;
- every meaningful text line is editable or explicitly omitted with a reason;
- the selected mode is recorded for the single slide; experimental multi-page work must record mode and limitations per page;
- every OCR line included in the PPTX passed review or has a recorded correction;
- clean-background PPTX has one full-slide background for the output slide plus editable text boxes;
- reconstruction PPTX does not use a disguised full-slide background unless explicitly accepted as a fallback;
- simple shapes are native where practical;
- source tables are native PowerPoint tables, with row/column structure preserved in the editability report;
- complex regions are tight source-derived transparent crops;
- reconstructed native objects do not introduce new shadows or PowerPoint effects unless source-matched;
- no-wrap and no-autofit are present for line-level trace text boxes;
- the editability report separates editable text, native shapes, source crops, OCR corrections, omitted lines, and limitations.
- preview QA catches visual failures, not only structure counts. `editableTextBodies` and ZIP/XML validity do not prove visual quality.
- the PPTX opens or renders in PowerPoint/LibreOffice when those apps are available; ZIP/XML validity alone is not enough for delivery.

## Failure Labels

Reject and revise when any of these happen:

- `visible overlay only`
- `duplicate source text`
- `source text residual`
- `ocr unavailable`
- `ocr bbox drift`
- `manual bbox guess`
- `auto-wrap linebreak drift`
- `single-character wrap`
- `line-level trace missing`
- `full-slide background disguised as reconstruction`
- `reconstruction missing plan`
- `reconstruction native proof missing`
- `hybrid fallback not accepted`
- `hybrid baseline mislabeled final`
- `complex visual approximate redraw`
- `unwanted native shadow/effect`
- `oversized crop selection box`
- `native shape drift`
- `table rebuilt as lines`
- `dashed guide not native`
- `editability report missing`
- `powerpoint-open-fail`
- `multi-page input mislabeled stable deck conversion`
- `raw ocr accepted without review`
- `structured page forced into hybrid`
- `rotated text rendered horizontally`
- `icon or badge text duplicated`
- `visual qa skipped`
