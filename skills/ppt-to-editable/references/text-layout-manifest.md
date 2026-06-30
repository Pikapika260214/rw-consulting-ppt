# Text Layout Manifest

Use this reference when packaging clean-background editable-text PPTX files or line-level OCR trace text.

`text_layout_manifest.json` is the contract between OCR/source-image geometry and the mechanical PPTX packager.

## Coordinate System

Default coordinates are inches on a 16:9 widescreen slide:

- width: `13.333`;
- height: `7.5`;
- origin: top-left.

The manifest may set `"units": "normalized"` to use 0-1 coordinates. Prefer inches for hand authoring.

## Minimal Structure

```json
{
  "title": "Example editable slide",
  "slide_size": { "width": 13.333, "height": 7.5 },
  "units": "inches",
  "slides": [
    {
      "slide": 1,
      "source_image": "source/slide_01.png",
      "background": "backgrounds/slide_01_clean.png",
      "text_boxes": [
        {
          "role": "title",
          "name": "Title line 1",
          "text": "Search is moving from links to answer workflows",
          "x": 0.45,
          "y": 0.32,
          "w": 12.1,
          "h": 0.55,
          "font_size": 26,
          "font_face": "Aptos Display",
          "east_asian_font": "Microsoft YaHei",
          "bold": true,
          "color": "111111",
          "align": "left",
          "source_bbox_px": [54, 38, 1210, 50],
          "ocr_id": "ocr_line_001",
          "ocr_confidence": 0.98,
          "trace_level": "line",
          "no_wrap": true,
          "review_status": "accepted"
        }
      ]
    }
  ]
}
```

## Required Fields

For every text box:

- `text`;
- `x`, `y`, `w`, `h`.

Recommended:

- `role`;
- `name`;
- `font_size`;
- `font_face`;
- `east_asian_font`;
- `bold`;
- `italic`;
- `color`;
- `align`;
- `valign`;
- `line_spacing`;
- `margin`.

For image-source conversion:

- `ocr_id`;
- `ocr_confidence`;
- `source_bbox_px`;
- `trace_level`;
- `no_wrap`;
- `review_status`;
- `correction_reason` or `omit_reason` when relevant.

For paragraph groups:

- `source_line_bboxes_px`;
- explicit `\n` line breaks in `text`;
- `trace_level: "paragraph_group"`.

For fitted line-level trace:

- `original_font_size`;
- `font_fit`;
- `render_anchor`;
- `character_spacing` when used;
- `alignment_status`.

## Authoring Rules

- Do not use one text box for mixed-style content. Split red headers, black body copy, numbers, and source notes.
- Do not use text boxes to redraw charts, tables, lines, or icons.
- Keep title and subtitle boxes generous enough for the source text.
- Preserve line breaks with line-level trace when visual fidelity matters.
- Avoid tiny type as a solution. If text must drop below a readable minimum, shorten text, split it, or redesign the local region.
- Use a low-weight source/caveat line if the source slide has one.
- For short captions, legend labels, badge numbers, and one-line takeaway fragments, prevent single-character orphan wraps. Prefer a slightly wider box, a small readable font reduction, or `no_wrap: true` over letting the last Chinese character or punctuation sit alone on a new line.

## Role Presets

Start with these role ranges, then fit against OCR bboxes:

- `title`: 24-34 pt, usually bold.
- `subtitle`: 11-16 pt.
- `section`: 12.5-18 pt.
- `badge-number`: 11-17 pt, centered.
- `label`: 9.5-12.5 pt.
- `card-header`: 9.5-12.8 pt.
- `body`: 8.8-12 pt.
- `panel-title`: 13-20 pt.
- `panel-copy`: 8.8-12.2 pt.
- `takeaway`: 15-21 pt.
- `source`: 6-8 pt.

For Chinese decks, prefer Microsoft YaHei, DengXian, or Source Han Sans. For English decks, prefer Aptos, Aptos Display, Arial, or Helvetica.

## Line-Level Trace Rules

PowerPoint auto-wrap cannot be trusted to reproduce source-image line breaks.

For each accepted OCR line:

1. create one text box;
2. set `trace_level: "line"`;
3. set `no_wrap: true`;
4. set `source_bbox_px`;
5. fit font height to the OCR bbox;
6. fit width by role-bounded font size and then bounded `character_spacing`;
7. record `font_fit`.

Patch policy:

- fix position first (`dx`, `dy`);
- fix font height second;
- fix horizontal density third with character spacing;
- do not use one global font multiplier to fix all lines;
- do not turn on auto-wrap or auto-fit to hide drift.
- reject `single-character wrap` when a short label or caption puts one trailing Chinese character or punctuation mark on its own line.

## QA

After packaging:

- count editable text bodies and compare with the manifest;
- inspect no-wrap and no-autofit counts for line-level text;
- render or preview the PPTX when practical;
- verify no visible source text remains in the clean background;
- record any OCR correction, omitted line, or visible drift.
