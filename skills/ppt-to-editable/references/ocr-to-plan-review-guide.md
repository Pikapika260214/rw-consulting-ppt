# OCR To Reconstruction Plan Review

Use `scripts/ocr_to_reconstruction_plan_scaffold.py` only to create a review-required text scaffold. Do not treat its output as a final reconstruction plan.

## Command

```powershell
python scripts/ocr_to_reconstruction_plan_scaffold.py path\to\ocr_results.json --source-image path\to\source.png --out path\to\source_reconstruction_plan.ocr-scaffold.json --review-manifest path\to\ocr_review_manifest.json
```

## What The Script Does

- Reads OCR records and source text boxes.
- Converts OCR pixel boxes into slide-inch text boxes.
- Marks every generated text element as `review_status: "needs_review"`.
- Writes a separate review manifest for accept/correct/omit/merge decisions.

## What It Does Not Do

- It does not correct OCR text.
- It does not infer native shapes, tables, icons, or source crop boundaries.
- It does not decide line-level versus semantic paragraph grouping.
- It does not make the output acceptable for final packaging.

## Review Rules

Before packaging:

- Correct mixed Chinese/English OCR errors.
- Omit accidental icon glyphs, decorative numbers, and low-value fragments.
- Merge true multiline semantic blocks when same-style adjacent lines should remain one editable text box.
- Merge conservatively: require the same font face, font size, bold/italic state, color, alignment, column/region, and tight vertical spacing.
- Keep labels, legends, axis labels, badge numbers, step numbers, table cells, mixed-style phrases, and visually separate regions as line-level text.
- When a line-level split is intentional for text that otherwise looks mergeable, add `line_level_trace_required: true`, `do_not_merge: true`, or a clear role such as `legend_label`, `axis_label`, `table_cell`, `badge_number`, or `step_label`.
- Run `check_reconstruction_plan_text_fit.py` and fix `candidate_multiline_split` warnings before packaging.
- Add native shapes and source crops separately; the OCR scaffold contains text only.
