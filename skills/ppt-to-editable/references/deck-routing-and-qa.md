# Experimental Multi-page Routing And QA

Use this reference only for manually split multi-page sources, experimental deck conversion work, or any single slide where the best output mode is not obvious. The public stable scope remains single image input to single-slide editable PPTX output.

The goal is not to maximize editable text box count. The goal is to choose the right conversion method per slide and reject OCR or mode choices that make the slide visually worse.

## Experimental Multi-page Workflow

Treat a multi-page source as a set of independent slide jobs, not one stable automatic batch job.

1. Extract each source slide/page to an unchanged PNG.
2. Create a per-slide run folder with source image, OCR artifacts, review manifest, selected mode, preview, and QA report.
3. Run OCR on each source image.
4. Build `ocr_review_manifest.json` before creating final text boxes.
5. Route each slide independently to `clean-background`, `reconstruction`, or mixed reconstruction.
6. Preview and QA each slide before deck assembly.
7. Assemble reviewed slide outputs only when the user explicitly accepts the experimental multi-page limitation.

Do not use one global route across a multi-page source unless the user explicitly asks for that limitation.

## Default Policy

For structured business slides, reconstruction is the default. Clean-background is allowed for complex visual pages, but it must not become the default route for pages that are mostly editable structure.

If a slide is reconstruction-friendly and no reconstruction implementation exists yet, stop at `requires_reconstruction_plan` rather than silently shipping a hybrid output. A hybrid PPTX can be useful as an interim baseline, but it must be labeled as such and must not be described as a reconstruction deliverable unless the user explicitly accepts the fallback.

## Mode Router

Use `clean-background` when:

- the slide has complex visual texture, screenshots, photos, illustrations, shadows, gradients, or proof-object imagery;
- the user mainly needs text editing while preserving visual feel;
- native reconstruction would visibly drift or require many approximate shapes.

Use `reconstruction` when:

- the slide is dominated by cards, tables, grids, rows, columns, process steps, lanes, timelines, product pills, decision matrices, simple funnels, or flow diagrams;
- most visual elements are rectangles, rounded rectangles, circles, badges, straight lines, dashed guides, arrows, or simple labels;
- the slide has repeated modules where native shapes will be more editable and cleaner than text removal.

Use mixed reconstruction when:

- simple layout should be native but icons, photos, screenshots, gradients, shadows, or detailed illustrations should remain source crops;
- a page has native-friendly cards and lines plus complex proof visuals.

If a slide is routed to reconstruction but no reconstruction implementation is available, mark the slide as `requires_reconstruction`. Do not silently ship a poor clean-background hybrid as if it were the best output.

Use `requires_reconstruction_plan` when the missing piece is the layer plan or page-specific implementation. The required next artifact is `source_reconstruction_plan.json` or an equivalent plan listing native text, native shapes, native lines, native tables, tight crops, omissions, and limitations.

## OCR Review Manifest

Raw OCR is a proposal, not final content.

For every OCR record, assign one of:

- `accepted`: becomes editable text;
- `corrected`: becomes editable text after a recorded text correction;
- `needs_review`: not safe for final output yet;
- `omit`: removed from output because it is noise or irrelevant;
- `keep_in_background`: left as part of a non-editable visual layer;
- `reconstruct_as_native`: used to rebuild a native object such as a badge, number, or label.

Flag these before packaging:

- low-confidence single characters;
- isolated symbols such as `x`, `<>`, punctuation, or stray OCR fragments;
- vertical or rotated text when the current packager cannot rotate text boxes;
- numeric badges, counters, and icon labels that are better native shapes or background graphics;
- OCR boxes whose height/width ratio suggests rotated text;
- unusually large font inference from a narrow bbox;
- overlapping text boxes that would collide after rendering;
- OCR in icons, logos, decorative glyphs, or screenshots that should remain source crops;
- title or large-text masks that would over-erase adjacent brand bars, icons, or structural shapes.

Do not count `keep_in_background` as a failure when the item is graphical, decorative, rotated, or outside the agreed editability target. Do record the limitation.

## Clean-Background Risks

Clean-background hybrid can pass structure checks while failing visually.

Reject or reroute when preview shows:

- dirty inpaint patches inside product pills, badges, dark headers, or gradient shapes;
- ghost text or black/white glyph residue behind editable text;
- source badge numbers duplicated by editable numbers;
- text over complex fills where erasing damages the object more than editing helps;
- a structured table/card page flattened into one background image with only text editable.

If these appear on a structured page, reroute to reconstruction.

## Reconstruction Expectations

For reconstruction-friendly pages, rebuild simple elements natively:

- cards, panels, row bands, and headers as native rectangles or rounded rectangles;
- product pills as native rounded rectangles plus editable text;
- numbered badges as native circles/chevrons plus editable numbers;
- tables and real grids as native PowerPoint tables where practical;
- divider rules, dashed guides, connectors, and arrows as native lines;
- simple icon containers as native circles/cards with tight icon crops.

Keep only complex visuals as tight source-derived crops. Do not use a full-slide background to disguise reconstruction.

Minimum reconstruction proof:

- `source_reconstruction_plan.json` exists, or an equivalent plan is embedded in the run notes.
- `editability_report.json` separates editable text, native shapes, native lines, native tables, source crops, and limitations.
- `nativeShapes > 0` for card, process, funnel, lane, badge, line, or diagram pages.
- `nativeTables > 0` for semantic table or row-column grid pages, unless a non-table fallback is explicitly accepted.
- `pictures` are tight crops for complex visuals, not one full-slide background.
- If the output is only clean background plus editable text, label it `clean-background` or `hybrid baseline`, not `reconstruction`.

## Preview QA

Structure counts are necessary but not sufficient. `editableTextBodies`, `noWrapTextBodies`, ZIP validity, and `python-pptx` readability prove the file is structurally editable; they do not prove visual fidelity.

For each slide, inspect a composite preview and record:

- source text residue;
- inpaint scars;
- text collisions or overflow;
- wrong orientation, especially vertical text rendered horizontally;
- OCR false positives;
- color/style mismatch that changes meaning;
- native shape drift or crop boxes that are too large.

For experimental multi-page outputs, summarize per slide:

- selected mode;
- accepted OCR count;
- omitted/kept-background/reconstructed OCR count and reasons;
- native shape/table/line/crop counts where applicable;
- preview QA result;
- known limitations.

## Acceptance Policy

Accept an experimental multi-page conversion only when:

- each slide has a selected mode and QA report;
- every final editable text box comes from accepted/corrected OCR or an explicitly reviewed manual text source;
- reconstruction-friendly slides are rebuilt as reconstruction/mixed reconstruction or are explicitly marked `requires_reconstruction_plan`;
- clean-background fallback on reconstruction-friendly slides has explicit user acceptance and is labeled as a fallback/baseline;
- unsupported rotated text, badges, symbols, and icon text are handled intentionally;
- the final PPTX structure passes inspection;
- visual preview defects are either fixed or documented as limitations.

## Failure Labels

- `deck forced through one mode`
- `structured page forced into hybrid`
- `raw ocr accepted without review`
- `rotated text rendered horizontally`
- `icon text promoted to editable`
- `badge duplicated`
- `dirty inpaint inside simple shape`
- `preview quality worse than source`
- `requires reconstruction`
- `requires_reconstruction_plan`
- `hybrid fallback not accepted`
- `hybrid baseline mislabeled final`
- `reconstruction native proof missing`
