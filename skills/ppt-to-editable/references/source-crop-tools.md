# Source Crop Tools

Use these tools when reconstruction should keep source fidelity for complex visual modules while making text editable.

## Icon And Visual Crops

Create a reviewed manifest, then run:

```powershell
python scripts/extract_source_crops.py path\to\source-crops.json --out-dir path\to\crops --report path\to\crop_report.json --debug path\to\crop_debug_sheet.png --ocr-results path\to\ocr_results.json
```

Manifest shape:

```json
{
  "source_image": "source.png",
  "ocr_results": "ocr_results.json",
  "crops": [
    {
      "id": "bottom-chatgpt-codex",
      "bbox": [238, 666, 306, 734],
      "transparent": true,
      "expect_square": true
    },
    {
      "id": "top-openai-chatgpt",
      "center": [355.5, 283.5],
      "size": 72,
      "alpha": "circle"
    }
  ]
}
```

Rules:

- Use `bbox` for manually reviewed crop bounds.
- Use `center` + `size` for fixed square icon grids.
- Use `transparent: true` for source icons on a flat background when corner-color background removal is safe.
- Use `alpha: "circle"` for full circular icon badges.
- Use `alpha_inset_px` when a circular crop needs its alpha mask pulled slightly inward to remove edge antialiasing residue without changing the crop box.
- For full circular icon badges, crop the complete white circle, border, shadow/edge antialiasing, and a small amount of safe padding. A crop that cuts the circle edge is invalid even when the inner icon is intact.
- Prefer `center` + `size` for repeated circular badges so all icons share the same measured center and square crop size. Start with enough padding to avoid edge clipping, then reduce the size if the rendered crop creates a visible outer halo.
- If the complete circular badge crop inevitably includes nearby card-edge shadow, connector residue, or gray halo, do not keep shrinking until the badge becomes clipped. Instead, recrop the source icon glyph from the original image and place it on a clean, source-matched circular badge base; keep a debug sheet and record that the crop is a clean badge composite.
- For clean badge composites, inspect the glyph extraction itself. If pale gray badge-edge arcs or shadows are extracted with the icon glyph, filter the glyph to keep only visible icon ink such as red strokes or dark strokes before compositing it onto the clean badge base.
- Do not assume the glyph crop center from repeated row spacing. First crop the full badge, detect the visible icon glyph bbox inside it, then expand that bbox with safe padding. This catches cases where a fixed glyph center clips the icon even though the full badge crop looks complete.
- In the debug sheet for clean badge composites, record the full badge crop box, detected glyph bbox, final glyph crop box, and final badge preview. If glyph ink touches the crop edge, revise the detection or padding before packaging.
- Pass `--ocr-results` or set `ocr_results` so the report can warn when a crop box includes OCR-detected text.
- Treat `ocr_text_overlap` as a likely bad crop when the text should be editable. Fix the crop bounds, make a textless crop, or set `allow_text_overlap: true` only when the crop intentionally preserves source text.
- Use `allowed_ocr_ids` when a crop may contain specific accepted source text but should still reject other nearby OCR text.
- Inspect the debug sheet before using the crops in `source_reconstruction_plan.json`.
- Treat `nontransparent_pixels_touch_crop_edge` as a possible too-tight crop warning, not an automatic failure. For circular badges, visually inspect this warning carefully because it often means the white circle or its antialiasing was clipped.

## Clean Badge Composites

Use this when a circular icon badge should keep the original icon glyph, but a complete source crop brings in card-edge residue, gray halo, or nearby connector/background artifacts. This is not a native icon redraw. It is a source-derived glyph placed onto a clean, source-matched circular badge base.

```powershell
python scripts/make_clean_badge_composites.py path\to\clean-badge-composites.json --out-dir path\to\badge-composites --report path\to\badge_composite_report.json --debug path\to\badge_composite_debug.png
```

Manifest shape:

```json
{
  "source_image": "source.png",
  "badges": [
    {
      "id": "entry-globe",
      "plan_element_id": "row-5-icon-picture",
      "center": [99, 781],
      "size": 118,
      "target_max": 66,
      "output_size": 118,
      "output_name": "badge_05.png",
      "ink_mode": "dark",
      "glyph_padding": 6
    }
  ]
}
```

Fields:

- Use `bbox` or `center` + `size` to describe the complete source badge area. This box is only the search area; it is not the final glyph crop.
- Use `target_max` to normalize the extracted glyph size inside the clean badge.
- Use `output_size` to keep repeated badges visually aligned in the reconstruction plan.
- Use `ink_mode: "dark"` for black/gray line icons, `ink_mode: "red"` for red icons, and `ink_mode: "auto"` only when both may appear in the same badge.
- For red icons, the tool defaults to the largest red component so stray red residue is less likely to be preserved.
- Use `glyph_padding` to add safe pixels around the detected source glyph bbox after detection.
- Use optional `dx` / `dy` only for final visual centering after inspecting the debug sheet; do not use those fields to compensate for a wrong source crop.

Acceptance checks:

- The report must have no `glyph_ink_touches_crop_edge` warning.
- The debug sheet must show a complete icon glyph, especially for tall or top-heavy symbols such as globe icons.
- The clean circular base must not contain pale gray source badge arcs, card-edge residue, or clipped circle edges.
- If the glyph is incomplete, fix the complete source badge search area or glyph detection mode first. Do not guess a smaller fixed center crop.
- Record the output as a clean badge composite in the reconstruction plan or notes so reviewers know the badge is source-derived, not fully native.

Optional crop fields:

```json
{
  "allow_text_overlap": false,
  "allowed_ocr_ids": ["ocr_012"],
  "ocr_overlap_threshold": 0.2
}
```

## Textless Source Crops

Use this when a complex source visual contains text that should become editable PowerPoint text.

```powershell
python scripts/make_textless_crops.py path\to\textless-crops.json --out-dir path\to\textless --report path\to\textless_report.json --debug path\to\textless_debug_sheet.png
```

Manifest shape:

```json
{
  "source_image": "source.png",
  "ocr_results": "ocr_results.json",
  "crops": [
    {
      "id": "process-steps-1-6",
      "bbox": [34, 405, 1288, 586],
      "strategy": "sample-fill",
      "ocr_mask_ids": ["ocr_021", "ocr_022", "ocr_023"],
      "sample_margin": 18,
      "blend_radius": 6,
      "blend_blur": 2
    },
    {
      "id": "bottom-openai-bar",
      "bbox": [309, 737, 925, 774],
      "strategy": "horizontal-inpaint",
      "ocr_mask_mode": "intersecting",
      "exclude_ocr_ids": ["ocr_001"]
    }
  ]
}
```

Strategies:

- `sample-fill`: fill each text mask from surrounding pixels. Use for white or lightly shaded cards and panels.
- `horizontal-inpaint`: fill each text mask from same-row left/right pixels. Use for gradient bars and horizontal bands.

Mask sources:

- Use `ocr_mask_ids` when the text to remove already has known OCR ids.
- Use `ocr_mask_mode: "intersecting"` when the crop should remove every OCR record whose bbox overlaps the crop.
- Use `exclude_ocr_ids` with intersecting mode when a nearby OCR record should remain in the source crop.
- Use `ocr_mask_padding` or `mask_padding` to expand OCR bboxes before cleanup.
- Use manual `text_masks` only for OCR misses, OCR boxes that are too loose/tight, or extra cleanup outside detected text.

Acceptance checks:

- The cleaned crop must not contain readable source text residue.
- The crop must not show obvious patch rectangles when placed on the slide.
- The final PPTX must place reviewed native text above the cleaned crop.
- Keep the original source image and manifest with the output so crop choices remain auditable.
- The report should list the `ocr_mask_ids` used for each crop. If the wrong OCR ids are selected, fix the manifest rather than hiding the issue with a larger manual mask.

Use local textless module crops for complex visual modules where native redraw drifts:

- curved connector paths;
- thick stepped connectors;
- bracket arrows;
- side funnels and side path modules;
- icon-connected navigation paths;
- grouped icon + arrow + label modules.
- bridge/risk modules that combine multi-column cards, icons, connector ribbons, bottom risk rows, or takeaway strips.

For these modules, mask only the readable text that should become editable. Preserve non-text visual geometry from the source crop.

### Accepted Module Crop Pattern

For bridge/risk pages or dense strategy diagrams, use several bounded local textless crops instead of one full-slide image:

- one crop for the main bridge or connector module;
- one crop for a bottom risk/icon row when the row has complex badges, connectors, or backgrounds;
- one crop for a takeaway strip when the strip background is source-specific.

Use `ocr_mask_ids` when OCR has already identified the text to remove. If OCR falsely recognizes icon strokes or decorative marks as text, leave those OCR ids out of the mask list or put them in `exclude_ocr_ids`; do not damage the icon just to satisfy an automatic mask rule.

If text removal leaves patch rectangles in a flat header bar or solid label area, repair that small area with a native flat rectangle and editable text in the reconstruction plan. Do not enlarge the crop or accept visible patch residue.

## Applying Crop Reports To A Reconstruction Plan

After crop reports are reviewed, apply them to the picture elements in the reconstruction plan:

```powershell
python scripts/apply_crop_report_to_plan.py path\to\source_reconstruction_plan.json --crop-report path\to\crop_report.json --crop-report path\to\textless_report.json --out path\to\source_reconstruction_plan.with-crops.json --report path\to\crop_plan_sync_report.json
```

Matching rules:

- Prefer `plan_element_id` from the crop manifest when present.
- Otherwise match picture element ids by common suffixes: `<id>`, `<id>-icon`, `<id>-background`, `<id>-bg`, `<id>-flow-bg`, and `<id>-card-bg`.
- The script updates `path`, `source.source_crop_px`, and `source.crop_report`.
- Use `--strict` during regression if every crop output must match a plan element.
