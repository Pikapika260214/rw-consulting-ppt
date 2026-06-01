# OCR Layout Recovery

Use this reference whenever a task starts from a source slide image and the output contains editable text.

OCR is not only for reading words. Its highest-value output is source text geometry.

## Required OCR Artifacts

Create and keep:

- `ocr_results.json`: one record per OCR line or word group;
- `ocr_overlay_debug.png`: source image with OCR boxes and reading-order labels when practical;
- `text_mask_debug.png`: actual source-text removal mask for clean-background work;
- `text_layout_manifest.json` or `source_reconstruction_plan.json` with OCR provenance fields.

Each OCR record should include:

```json
{
  "id": "ocr_line_001",
  "text": "Search is moving from links to answer workflows",
  "confidence": 0.98,
  "bbox_px": [55, 37, 1275, 52],
  "polygon_px": [[55, 37], [1330, 37], [1330, 89], [55, 89]],
  "role": "title",
  "line_index": 1,
  "group_id": "title",
  "language": "en-US",
  "review_status": "accepted"
}
```

Chinese-capable OCR is required for Chinese source images. Keep confidence scores and raw OCR text. Do not silently rewrite uncertain text; mark it as `needs_review`.

If no OCR engine is available, stop before attempting high-fidelity source-image conversion. A manual transcript is acceptable only for a rough smoke test.

## Text Removal Policy

Use OCR geometry to drive text removal:

1. Build source text mask regions from OCR bboxes.
2. Add manual regions only for OCR misses and record the reason.
3. Within each region, remove ink-like pixels or locally inpaint the text zone.
4. Save `text_mask_debug.png`.
5. Inspect the textless result before placing editable text.

Region-aware policies:

- `dark_text_on_light`: mask dark or colored ink inside the OCR bbox.
- `light_text_on_dark_header`: inpaint the full title/header bbox when white-pixel masking leaves residue.
- `colored_label`: mask saturated colored ink without erasing pale rules or texture.
- `composite_badge`: remove source number/badge residue, rebuild simple ring/circle natively when practical, then overlay editable text.
- `complex_visual_text`: remove the text but keep the complex visual as a source crop or clean background.

Repeated elements must be measured per instance. Use OCR boxes, connected components, or source-image geometry for each badge, icon circle, marker, header, and label.

## Editable Text Placement

Use OCR bboxes as the first placement source.

### Fidelity Mode: Line-Level Trace

Use by default when visual matching matters:

- one editable text box per visible OCR line;
- `trace_level: "line"`;
- `no_wrap: true`;
- `source_bbox_px` from OCR;
- font height fit to the OCR bbox first;
- no-wrap width fitting with role-specific minimum font sizes;
- bounded `character_spacing` only after font height is acceptable.

This avoids PowerPoint auto-wrap and preserves source line breaks.

### Editability Mode: Paragraph Groups

Use only when the user cares more about editing paragraphs as units:

- group OCR lines into paragraph text boxes;
- preserve explicit hard line breaks;
- keep `source_line_bboxes_px`;
- disable auto-fit;
- label any visible line-break drift in the report.

If paragraph mode drifts too much, switch to line-level trace.

## QA Checks

Before packaging:

- OCR line count matches editable text box count in line-level trace mode, or every omitted line has an `omit_reason`;
- every text box has OCR provenance or a manual-region explanation;
- the clean background has no readable source text residue;
- overlay preview aligns with source layout;
- per-line alignment failures are recorded with suggested patches;
- the final report separates OCR errors, text-removal defects, and PowerPoint rendering drift.

## Failure Labels

- `ocr unavailable`
- `ocr text error`
- `ocr bbox drift`
- `manual bbox guess`
- `source text residual`
- `text mask over-erased non-text visual`
- `text mask under-erased source glyphs`
- `line-level trace missing`
- `auto-wrap linebreak drift`
