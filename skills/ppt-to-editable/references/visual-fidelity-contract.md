# Visual Fidelity Contract

Use this reference before converting any structured consulting slide image into editable PowerPoint.

For ppt-to-editable v3.1 preview multi-page and delegated per-slide Agent work, also read `visual-fidelity-execution.md` before conversion. That file contains execution-time rules for PowerPoint rendered PNG review, Microsoft YaHei font enforcement, clearing unwanted shape effects, 3-5 region textless crop planning, and high-risk crop-first gates.

## Non-Negotiable Outcome

The goal is not only to create editable objects. The output must remain visually close enough to the source slide that a user can accept it after inspection.

Structural counts such as `editableTextBodies`, `nativeShapes`, and `pictures` do not prove visual quality.

## Text Rules

- Convert meaningful visible text into editable PowerPoint text whenever practical.
- Default generated Chinese and mixed Chinese-English text to Microsoft YaHei; do not rely on PowerPoint theme fallback.
- Preserve the source slide's relative font size hierarchy. Do not shrink body, callout, or panel text into tiny outliers just to make a guessed layout fit.
- Preserve semantic text groups conservatively. If adjacent lines have the same font, size, weight, color, alignment, local region, and tight spacing, keep them as one multiline text box unless line-level fidelity clearly requires otherwise.
- Do not split one original multi-line text block into many isolated text boxes just because OCR detected separate lines.
- Do not force-merge titles, labels, legends, axis labels, badge numbers, step labels, table cells, mixed-style text, or cross-column text.
- Never put raw OCR text into the final PPTX without review. Correct mojibake, mixed Chinese/English errors, duplicated symbols, and low-confidence fragments.
- Avoid one-character wraps. Widen the text box, reduce font size slightly, or use no-wrap.
- Text boxes should stay transparent unless the source itself has a visible card, bar, pill, or label background behind that text. Do not add invented pale rectangles or generic backing fills to hide old source text.

## Crop vs Rebuild

- Rebuild simple flat geometry as native PowerPoint objects: cards, rectangles, circles, dividers, simple arrows, straight connectors, dashed guides, badges, and simple tables.
- Keep complex visuals as tight source crops: icons, shaded badges, gradients, shadows, photographs, detailed diagrams, screenshots, textured symbols, and source-specific arrow bands.
- Do not force native reconstruction for complex shapes. When native redraw would make a bespoke arrow, icon group, shaded module, or dense callout look unnatural, keep that region as a source-derived crop or textless crop and overlay reviewed editable text.
- Use crop-first judgment for complex artwork regions. Product photos, detailed icons, curved paths, gradient arrows, textured modules, layered card stacks, and source-specific process visuals should remain source-derived unless a native redraw clearly matches the original.
- For complex structured pages, prefer semantic region-level textless crops plus editable text over full-native redraw when native redraw would drift. Do not use one whole-slide textless background crop unless the user explicitly accepts that fallback.
- Do not approximate-redraw complex icons when a faithful crop would look better.
- A lower native-shape count is acceptable if it avoids an unnatural redraw.

## Crop Quality Rules

- Crops must be complete, centered, and visually natural.
- Same-size repeated icons or badges must use consistent crop boxes and spacing.
- For circular icon badges, measure the visible badge center and crop a square around the full white/colored badge, not only the dark glyph.
- Reject crops that are clipped, oval due to wrong aspect ratio, contain neighboring text, or leave text residue that should be editable.
- If a crop contains readable text that should be editable, create a textless crop and overlay reviewed editable text.
- Textless crop cleanup must preserve non-text anchors: arrows, arrowheads, route lines, connectors, step markers, card edges, cut corners, dividers, and icons.

## Visual QA Gate

Before marking a slide as passed:

- Compare source image and output preview side by side.
- Check text placement, font weight, color, and line breaks.
- Check that body/callout font sizes are not obviously smaller than the source role or surrounding same-role text.
- Check icon completeness, crop boundaries, and spacing.
- Check that arrows, arrowheads, route lines, connectors, step markers, card edges, dividers, and icons are still present and not clipped after textless crop cleanup.
- Check that source text is not duplicated underneath editable text.
- Check that native shapes do not introduce unwanted shadows, effects, or PowerPoint theme styling.
- Check that editable text was not made readable by invented pale rectangles or generic fills.

If there is no PowerPoint or LibreOffice rendered output, do not claim final visual QA passed. Use `accepted-with-limitations` at most.

## Reject Labels

Use these labels in `qa_summary.json` when applicable:

- `visual-qa-skipped`
- `rendered-qa-missing`
- `crop-clipped`
- `crop-contains-neighbor-text`
- `icon-redraw-drift`
- `text-group-split`
- `ocr-mojibake`
- `source-text-residue`
- `native-shape-drift`
- `manual-layout-guess`
- `tiny-font-outlier`
- `font-size-hierarchy-drift`
- `native-redraw-complex-artwork`
- `invented-text-background`
- `missing-non-text-anchor`
- `missing-arrowhead`
- `broken-route-line`
- `cropped-icon`
