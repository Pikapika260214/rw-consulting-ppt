# Source Reconstruction Plan Schema

Use this reference when writing or reviewing `source_reconstruction_plan.json` for `scripts/package_reconstruction_deck.py`.

## Top-Level Fields

Required:

- `slide_width_in`: slide width in inches.
- `slide_height_in`: slide height in inches.
- `source_image`: source image filename relative to the plan folder.
- `slides`: array of slide objects.

Recommended:

- `title`: human-readable run title.
- `mode`: `reconstruction` or `mixed_reconstruction`.
- `source_ocr`: OCR results filename when available.
- `notes`: short list of conversion decisions.
- `limitations`: explicit visual or editability tradeoffs.
- `strategy_review`: native-vs-crop decisions for high-risk visual modules.
- `protected_visual_anchors`: non-text structural elements that must survive reconstruction and textless crop cleanup.

## Slide Object

Each slide object contains:

- `id`: stable slide id.
- `elements`: ordered list of visual elements from back to front.

A slide may also contain its own `strategy_review`, but prefer top-level `strategy_review` for single-slide plans.

Element coordinates use inches unless a field explicitly ends in `_px`.

## Shape Element

```json
{
  "id": "panel-bg",
  "type": "shape",
  "shape": "roundRect",
  "x": 0.25,
  "y": 1.2,
  "w": 4.0,
  "h": 0.8,
  "fill": "#FFFFFF",
  "stroke": "#D1D5DB",
  "stroke_width": 1.0,
  "radius": 0.04,
  "source": {
    "kind": "native_shape",
    "source_bbox_px": [30, 150, 530, 250]
  }
}
```

Supported shapes include common PowerPoint shapes such as `rect`, `roundRect`, `oval`, `chevron`, and other shapes mapped by the packager.

## Line Element

```json
{
  "id": "guide-1",
  "type": "line",
  "x1": 1.0,
  "y1": 2.0,
  "x2": 1.0,
  "y2": 4.0,
  "color": "#174EA6",
  "width": 1.0,
  "dash": true,
  "end_arrow": true,
  "source": {
    "kind": "native_line",
    "source_bbox_px": [120, 240, 120, 520]
  }
}
```

Use native lines for simple straight rules, dividers, true dashed guides, and simple axis or flow arrows.

Arrow fields:

- `start_arrow: true`: add a native PowerPoint arrowhead at the line start.
- `end_arrow: true`: add a native PowerPoint arrowhead at the line end.
- `arrow_type`: optional DrawingML arrowhead type, default `triangle`.
- `start_arrow_width`, `end_arrow_width`, `start_arrow_length`, `end_arrow_length`: optional DrawingML values such as `sm`, `med`, or `lg`.

Do not use editable text glyphs such as `←`, `→`, `↑`, or `↓` to approximate simple axis or flow arrows when a native line arrow can represent the source.

## Text Element

```json
{
  "id": "module-title",
  "type": "text",
  "x": 1.4,
  "y": 2.1,
  "w": 1.8,
  "h": 0.3,
  "text": "Repo context",
  "font_size": 12,
  "font_face": "Microsoft YaHei",
  "color": "#111111",
  "bold": true,
  "align": "left",
  "valign": "top",
  "margin": 0.01,
  "word_wrap": false,
  "trace_level": "line",
  "semantic_block": false,
  "source": {
    "kind": "manual_reviewed_text",
    "source_bbox_px": [180, 260, 360, 295],
    "review_status": "corrected"
  }
}
```

Use `trace_level: "line"` for labels and one-line text. Use `trace_level: "paragraph"` and `semantic_block: true` for meaningful multiline blocks that should remain one editable text box.

For conservative multiline grouping, merge only when adjacent lines have the same font face, font size, bold/italic state, color, alignment, and local column/region, with tight vertical spacing and no visual boundary between them. Do not merge titles with body text, labels with explanations, table cells, legends, axis labels, badge numbers, step numbers, cross-column text, or mixed-style text.

Grouped multiline text should keep the source line breaks inside one `text` string and preserve provenance:

```json
{
  "id": "body-paragraph-1",
  "type": "text",
  "x": 1.4,
  "y": 4.8,
  "w": 3.2,
  "h": 0.55,
  "text": "需要稳定的识别与显示能力，\n对续航、散热和交互准确性要求更高。",
  "font_size": 11,
  "font_face": "Microsoft YaHei",
  "color": "#111111",
  "bold": false,
  "align": "left",
  "word_wrap": true,
  "trace_level": "paragraph",
  "semantic_block": true,
  "source_element_ids": ["ocr_041_text", "ocr_042_text"],
  "source": {
    "kind": "manual_reviewed_text",
    "source_line_bboxes_px": [[910, 680, 1110, 704], [910, 710, 1210, 734]],
    "review_status": "corrected"
  }
}
```

If same-style adjacent line boxes are intentionally not merged, mark them with `line_level_trace_required: true`, `do_not_merge: true`, `preserve_line_level: true`, or a clear role such as `legend_label`, `axis_label`, `table_cell`, `badge_number`, or `step_label`.

Before packaging, run:

```powershell
python scripts/check_reconstruction_plan_text_fit.py path\to\source_reconstruction_plan.json --out path\to\text_fit_report.json
```

Text fit warnings are review gates:

- `text_overflow_risk`: widen the box, reduce font size, fix line breaks, or change wrap settings before packaging.
- `punctuation_orphan_line`: do not leave Chinese or English punctuation alone at the start of a rendered line.
- `single_character_line`: check whether an unintended one-character wrap happened.
- `candidate_multiline_split`: adjacent same-style line-level boxes likely belong to one semantic multiline text block. Merge them or explicitly mark why line-level trace is required.

Font-size hierarchy is also a review gate. Do not shrink body, callout, or panel text into tiny outliers to force a guessed layout to fit. If text does not fit, first adjust the box, region crop, line breaks, or semantic grouping. Record unresolved tiny text as `tiny-font-outlier` or `font-size-hierarchy-drift`.

Text elements should not carry invented background fills. If readable source text remains underneath, repair the local visual area as a textless crop and overlay transparent editable text. Only create native background shapes behind text when the source slide already has that visible card, bar, pill, or label.

## Picture Element

```json
{
  "id": "icon-crop",
  "type": "picture",
  "path": "icons/icon-crop.png",
  "x": 2.0,
  "y": 3.0,
  "w": 0.5,
  "h": 0.5,
  "source": {
    "kind": "source_icon_crop",
    "source_crop_px": [240, 360, 300, 420],
    "reason": "Complex icon preserved as source crop"
  }
}
```

Use picture elements for complex icons, gradient bars, arrow-ended bands, shadows, dense diagrams, screenshots, and textless crops. Do not leave readable source text inside a picture when that text should be editable.

## Strategy Review

Use `strategy_review.regions` when a mixed reconstruction plan contains complex visual regions where native redraw may drift.

```json
{
  "strategy_review": {
    "regions": [
      {
        "id": "left-capability-path-module",
        "visual_type": "curved_connector_side_module",
        "source_bbox_px": [20, 200, 520, 675],
        "expected_strategy": "source_textless_crop",
        "actual_strategy": "source_textless_crop",
        "evidence_element_ids": ["left-module-bg-picture"],
        "text_overlay_element_ids": ["row-1-label", "row-2-label", "left-title", "left-body"],
        "reason": "Curved connector/path module looked template-like when redrawn as native lines."
      }
    ]
  }
}
```

High-risk `visual_type` values include:

- `curved_connector`
- `curved_connector_side_module`
- `thick_stepped_connector`
- `bracket_arrow`
- `side_path_module`
- `side_funnel_module`
- `icon_connected_navigation_path`
- `complex_process_card_group`
- `bridge_risk_module`
- `grouped_icon_card_connector_system`
- `product_photo_or_detailed_icon_group`
- `gradient_arrow_or_textured_band`
- `layered_card_stack`
- `complex_table_or_flow_matrix`
- `complex_matrix_background`
- `source_specific_process_matrix`

Common strategies:

- `native_reconstruction`: simple native shapes or lines that preserve the source for non-high-risk regions.
- `source_icon_crop`: tight source crop for complex icon artwork.
- `source_textless_crop`: local source crop with readable text removed and editable text overlaid.
- `native_redraw`: acceptable only for simple non-high-risk visuals. It is not a valid high-risk fallback in v3.1.

For high-risk visual regions, choose crop-first by default. In v3.1, `override_reason` does not bypass a high-risk native redraw warning. If a complex region looks like a generic PowerPoint template after redraw, change it to `source_textless_crop` plus editable text before packaging.

Each strategy review region should include `source_bbox_px` and `reason`. Do not use `not-reported` placeholders in `region_crop_plan`; controller finalization rejects them.

## Protected Visual Anchors

Use `protected_visual_anchors` when a slide contains visual structure that readers use to understand the page, especially arrows, arrowheads, route lines, connectors, step markers, card edges, cut corners, dividers, or icons.

```json
{
  "protected_visual_anchors": [
    {
      "id": "p3-upper-right-route-arrow",
      "kind": "arrowhead",
      "source_bbox_px": [1330, 260, 1510, 330],
      "preservation_status": "reviewed",
      "strategy": "source_textless_crop",
      "reason": "Arrowhead and route line are part of the source process-card structure."
    }
  ],
  "non_text_anchor_preservation_review": {
    "status": "reviewed",
    "missing_required_anchors": false,
    "issues": []
  }
}
```

If rendered QA shows a protected anchor is missing, broken, clipped, or erased, mark `preservation_status` or `non_text_anchor_preservation_review.status` as `failed` and do not claim success. Fix the crop/native element first.

Before packaging a plan with strategy review, run:

```powershell
python scripts/check_reconstruction_visual_strategy.py path\to\source_reconstruction_plan.json --out path\to\visual_strategy_report.json --require-strategy-review
```

## Required QA Signals

Every reconstruction run should produce:

- `visual_strategy_report.json` when high-risk visual modules are present
- `packaging_report.json`
- `editability_report.json`
- PowerPoint-rendered preview PNG
- `render_report.json`

Reject outputs with `fullSlidePictures > 0` unless the limitation is explicitly accepted.
