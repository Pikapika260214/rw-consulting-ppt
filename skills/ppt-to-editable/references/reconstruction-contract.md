# Reconstruction Contract

Use this reference when the output mode is `reconstruction`.

Reconstruction creates a layered editable PPTX from a source slide image. It is not full-native redrawing and not a full-slide background trick.

Prefer this mode for structured business slides: cards, tables, grids, repeated modules, product pills, numbered steps, timelines, lanes, process diagrams, decision matrices, and pages where most objects are simple shapes and editable text. For manually split or experimental multi-page inputs, choose this per slide with `references/deck-routing-and-qa.md` instead of forcing every slide through clean-background hybrid.

## Principle

Use three layers:

1. Editable text layer: all readable text becomes native PowerPoint text.
2. Native simple layer: simple geometry becomes native shapes and lines.
3. Source crop layer: complex visuals remain faithful as tight transparent PNG crops from the original source image.

Do not promise full-native conversion unless the user provides the original PPT, vector file, or chart/source data.

## Source Crop Layer

Use tight source-image crops for:

- photos, product screenshots, illustrations, detailed icons;
- gradient funnels, beams, translucent paths, shadows, texture, particles;
- complex curved connectors or convergence arrows where native lines would drift;
- dense charts or diagrams whose data cannot be reconstructed reliably.

Crop rules:

- crop from the original source image, not an approximated redraw;
- remove readable text from crops when text should be editable;
- trim transparent margins so selection boxes remain practical;
- do not include cards, badges, labels, dashed guides, endpoint circles, or simple shapes in a crop when those can be native;
- for overlapping path systems, create one crop per semantic path, with ownership recorded in the layer plan;
- place path crops under native cards, endpoint circles, labels, and target rings when native objects should cover crop residue.

Known limitation: PowerPoint image selection boxes remain rectangular even for transparent PNGs. The contract is a tight enough selection box, not invisible selection bounds.

## Native Shape Layer

Rebuild as native PowerPoint objects when practical:

- rectangles, rounded rectangles, cards, panels, headers;
- circles, dots, numbered badges, markers;
- straight arrows, chevrons, simple connectors;
- vertical and horizontal rules;
- true dashed guide lines;
- simple tables or grids when their content is editable text.

Native dashed lines must be true dash styles, not many tiny rectangle fragments.

Composite objects such as numbered badges should usually become a native circle/ring plus editable number. Remove source badge residue before placing the native replacement.

Avoid over-native reconstruction. If the native redraw visibly changes a complex proof object, use a source crop.

## Editable Text Layer

Run OCR before rebuilding text.

Text reconstruction should preserve:

- source text content, with corrections recorded;
- source line breaks when they are visually meaningful;
- approximate position and width;
- text color, boldness, hierarchy, and alignment;
- Chinese punctuation and terminology.

Default to line-level trace:

- one text box per accepted OCR line;
- `trace_level: "line"`;
- `no_wrap: true`;
- OCR `source_bbox_px`;
- per-line font fitting before character spacing.

Use paragraph groups only when the user explicitly prioritizes editing convenience over visual matching.

## Workflow

1. Save the original source image unchanged.
2. Run OCR and save `ocr_results.json`.
3. Create `ocr_overlay_debug.png` when practical.
4. Create `ocr_review_manifest.json` and classify OCR as accepted, corrected, omitted, kept in background, or reconstructed as native.
5. Create `source_reconstruction_plan.json` with inventories for source crops, native shapes/lines, editable text, and omissions.
6. Build text removal masks from accepted/corrected OCR bboxes and manual OCR-miss regions only.
7. Extract tight source crops for complex visuals.
8. Rebuild simple geometry as native PPT objects.
9. Rebuild readable text as native PPT text boxes.
10. Render or export a preview and compare with the source image.
11. Inspect PPTX structure and write `editability_report.json`.
12. Iterate based on visible drift and editability defects.

## Layer Plan Schema

Use `source_reconstruction_plan.json` or an equivalent JSON plan.

Text elements should include OCR provenance:

- `ocr_id`;
- `ocr_confidence`;
- `source_bbox_px`;
- `source_line_bboxes_px` for paragraph groups;
- `trace_level`;
- `no_wrap`;
- `review_status`;
- `correction_reason` or `omit_reason`.

Example:

```json
{
  "slide_size": { "width": 1600, "height": 900 },
  "source_image": "source/slide_01.png",
  "elements": [
    {
      "id": "main_visual",
      "type": "image_crop",
      "policy": "source_crop",
      "source_bbox_px": [80, 260, 900, 310],
      "slide_bbox_px": [80, 260, 900, 310],
      "reason": "gradient funnel and shadow field would drift if redrawn"
    },
    {
      "id": "card_01",
      "type": "shape",
      "policy": "native_shape",
      "geometry": "roundRect",
      "slide_bbox_px": [80, 610, 220, 150],
      "style": { "fill": "#FFFFFF", "stroke": "#D9DEE8", "radius": 8 }
    },
    {
      "id": "title_line_01",
      "type": "text",
      "policy": "native_text",
      "ocr_id": "ocr_line_001",
      "text": "AI search is shifting from links to answer workflows",
      "source_bbox_px": [70, 42, 1120, 48],
      "trace_level": "line",
      "no_wrap": true,
      "review_status": "accepted"
    }
  ]
}
```

For complex path crops, add ownership fields:

```json
{
  "id": "route_path_03",
  "type": "image_crop",
  "policy": "source_crop",
  "owner": "complex_path_stroke_only",
  "mask_method": "path_corridor_nearest_path_ownership",
  "layer": "under_native_shapes",
  "source_bbox_px": [930, 480, 260, 180],
  "reason": "curved translucent path would drift as a native connector"
}
```

## Editability Report

The final report must separate:

- editable text body count;
- accepted OCR line count;
- omitted OCR lines and reasons;
- OCR corrections and reasons;
- native shape count;
- native dashed line count;
- picture/crop count;
- oversized crop selection boxes;
- complex regions that remain non-editable and why;
- known visual drift.

## Acceptance Checks

Accept reconstruction only if:

- OCR artifacts exist for image-source quality runs;
- every meaningful text line is editable or explicitly omitted;
- raw OCR was reviewed before becoming editable text;
- simple cards, circles, badges, arrows, panels, divider lines, and dashed guides are native when practical;
- complex visuals are source-derived tight crops, not approximate redraws;
- no full-slide background is used to fake reconstruction unless explicitly accepted as a fallback;
- dashed guides are native dashed lines;
- crop boxes are tight enough for practical editing;
- preview fidelity is close enough and limitations are documented.

## Failure Modes

- `full-slide background disguised as reconstruction`
- `complex visual approximate redraw`
- `oversized crop selection box`
- `shared connector crop conflict`
- `path crop layered above native shapes`
- `ocr skipped`
- `ocr text error`
- `auto-wrap linebreak drift`
- `dashed guide not native`
- `native badge duplicated`
- `native shape drift`
- `editability report missing`
- `raw ocr accepted without review`
- `reconstruction-friendly page flattened to hybrid`
