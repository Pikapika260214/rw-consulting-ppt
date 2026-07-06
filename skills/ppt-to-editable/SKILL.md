---
name: ppt-to-editable
description: Use when converting image-only PPTX decks, full-slide PNGs, screenshots, or raster slide images into editable PowerPoint; supports single-page and multi-page .pptx workflows with OCR, reconstruction, source crops, render QA, and fallback stickers.
---

# PPT to Editable v3 Two-Mode Preview

This is the two-mode preview package for the `ppt-to-editable` skill. It keeps the proven v3.1 single-page engine and supports high-quality multi-page PPTX conversion through independent per-slide workers.

This release intentionally exposes only two product modes: single-page PNG/sample-slide conversion, and multi-page multi-Agent high-quality conversion. The previous multi-page sequential token-saving experiment is retired because its output quality was unstable. A valid multi-page run should use this folder's own `scripts/` and `references/`, not a separate local development folder.

Convert an existing visual slide master into a more editable PowerPoint file. This skill starts from an already visible page: image-only PPTX, full-slide PNGs, screenshots, scanned/PDF pages, or approved generated slide images.

This skill does not generate a new consulting deck from notes, bullets, research, or page outlines. Use the separate deck-generation skill for that. This skill is a conversion layer.

## Core Rule

Do not ship a visible text-overlay result where the original text-bearing image remains underneath editable text. That is duplicate text, not useful editability.

The final PPTX must either:

- use a clean/textless background plus editable PowerPoint text; or
- reconstruct simple elements as native PPT objects and keep only complex visuals as tight source-derived crops.

OCR is required for quality runs that start from images. OCR is not only for reading words; it provides source text geometry for text removal, editable text placement, line breaks, and QA.

For a multi-slide deck, do not run one mode over the whole deck by default. Use `scripts/deck_controller.py` to split the deck into per-slide jobs, route each slide independently, run OCR review gates per slide, and assemble only reviewed slide outputs into the final deck.

## Preflight Gate Sequence

Before a quality conversion run, complete the gate sequence and preserve the user's answers in a `gates.json` file. The controller enforces this file before it creates slide jobs.

### Step 1: Probe

Run the read-only probe first. It creates no run directory, extracts no source images, and installs nothing.

```text
python scripts/deck_controller.py SOURCE.pptx --probe --ocr-python OCR_PYTHON --ocr-deps OCR_DEPS
```

Use the probe output to explain OCR status, show slide count, and copy the included `gates_file_template` into `gates.json`.

### Step 2: Conversion Mode Gate

Before asking about workers or page scope, give the user the two product modes:

```text
你可以选择两种转换方式：

1. 单页省 token 模式
适合：你只想先转一页、测试效果，或者想继续发单张 PNG 变成可编辑 PPT。
消耗：较低。
结果：输出一页可编辑 PPT。

2. 多页多 Agent 高质量模式
适合：你想转换整份 PPTX、质量优先，并且你能接受较高的 token 消耗。
消耗：较高；每页会交给独立转换任务处理。
结果：输出完整可编辑 PPT；失败页会保留原图并加提示。

如果你更想省 token，建议先选单页省 token 模式。
如果要转换整份 PPTX，则使用多页多 Agent 高质量模式；页数越多，token 消耗越高。

请告诉我你的选择。
```

Record the user's answer in `gates.json` under `conversion_mode_gate`:

- `single-page-token-saving`: one PNG or exactly one selected sample slide;
- `multi-agent-high-quality`: multi-page PPTX conversion with independent per-slide workers, all pages or selected pages.

`full-deck-convenience` is accepted only as a backward-compatible alias for older gates; do not present it as a user-facing option.

`multi-page-sequential-token-saving` is retired. Do not present it, recommend it, or accept it as a fresh user choice.

If the user sends a single PNG and chooses single-page mode, continue with the single-page reconstruction/clean-background workflow and do not initialize the deck controller or dispatch multi-agent workers.

If the user sends a PPTX and chooses single-page mode, initialize exactly one slide with `--slides "N"` and `scope_and_worker_gate.user_choice: "sample"`. Do not run `--all-slides`.

### Step 3: OCR Runtime Gate

Before the first OCR-dependent run in a user environment, explain in plain language that OCR reads the source slide image and gives the conversion chain source text, text positions, line breaks, and Chinese text usability checks. OCR is needed for reliable text removal, editable text placement, and QA.

If OCR is already `passed-text-usable`, do not ask the user to approve setup again. Record the probe result in `gates.json` under `ocr_runtime_gate` with `setup_required: false`, `auto_passed_existing_runtime: true`, and `probe_ocr_runtime_status: "passed-text-usable"`.

If OCR is not already set up, tell the user the first setup may take longer because dependencies or OCR model files may be installed or downloaded. Record the user's answer in `gates.json` under `ocr_runtime_gate`. A user's request to convert a deck is not consent to install, download, or configure OCR.

Only after the user confirms setup, run:

```text
python scripts/setup_ocr_runtime.py --gates-file GATES.json --runtime-dir OCR_RUNTIME_DIR --yes
python scripts/check_ocr_runtime.py --json --output-dir OCR_CHECK_DIR
```

Require `ocr_runtime_status: "passed-text-usable"` for quality editable output. If OCR is already `passed-text-usable` for the current run, record that check result in the run artifacts and do not ask setup consent again in the same run.

If OCR is not `passed-text-usable`, stop before creating slide jobs unless the user explicitly accepts a diagnostic or fallback-only run. Only use `--user-accepted-ocr-limited-run` after `gates.json` records `ocr_runtime_gate.user_accepted_limited_run: true`.

### Step 4: Scope + Worker Gate

For `.pptx` inputs, apply the scope gate according to the selected conversion mode.

If `conversion_mode_gate.user_choice` is `single-page-token-saving`, ask which one slide to test and record `scope_and_worker_gate.user_choice: "sample"` with exactly one slide number. Do not offer full-deck conversion inside this mode, and do not initialize with `--all-slides`.

If `conversion_mode_gate.user_choice` is `multi-agent-high-quality`, ask one combined question before creating slide jobs:

```text
这份 PPT 一共有 N 页。

你想怎么转换？
1. 转换全部 N 页
2. 只转换指定页
3. 先转换 1 页看看效果

说明：转换页数越多，消耗的 token 越多；多页多 Agent 高质量模式会把每一页交给独立转换任务处理，质量检查更独立，但 token 消耗更高。

请告诉我你的选择。
```

Do not ask the user to approve `app-native`, `worker_mode`, `scope_and_worker_gate`, or `Codex worker runtime`. Those are implementation details. The user-facing decision is only:

- how many pages to convert;
- whether they accept more token cost as page count increases;
- in multi-agent mode only, whether each page may be read by a separate conversion task for this conversion.

After the user answers, record the answer in `gates.json` under `scope_and_worker_gate`, including:

- `user_choice`: `all`, `selected`, or `sample`;
- `slides`: selected slide numbers when needed;
- `worker_mode`: `app-native`, `external-codex`, or `manual`;
- `worker_execution_approved: true`;
- `token_cost_acknowledged: true`;
- `content_sharing_acknowledged: true` for multi-agent or external-worker modes;
- `external_codex_worker_approved: true` only when `worker_mode` is `external-codex`.

For normal in-app multi-agent execution, use `worker_mode: "app-native"` internally. Do not make the user say that term. If the user is unsure, recommend one sample page first before spending tokens on the full deck. Do not infer full-deck conversion from a generic request such as "convert this PPTX."

Initialize only after conversion mode, OCR, and scope/worker gates are recorded:

```text
python scripts/deck_controller.py SOURCE.pptx --run-dir RUN_DIR --gates-file GATES.json --all-slides --ocr-python OCR_PYTHON --ocr-deps OCR_DEPS
python scripts/deck_controller.py SOURCE.pptx --run-dir RUN_DIR --gates-file GATES.json --slides "1,3,5" --ocr-python OCR_PYTHON --ocr-deps OCR_DEPS
```

After initialization, run the dispatch report before starting workers:

```text
python scripts/prepare_worker_dispatch.py RUN_DIR --worker-mode app-native
python scripts/prepare_worker_dispatch.py RUN_DIR --worker-mode external-codex
python scripts/prepare_worker_dispatch.py RUN_DIR --worker-mode manual
```

This script does not launch workers. It reports which `AGENT_TASK.md` files are ready and whether external Codex worker execution is allowed by `gates.json`. Do not run `codex exec` or any external worker launcher when the dispatch report says `blocked-external-worker-not-approved`.

The resulting deck manifest and final deck should contain only the selected pages, in the requested order. The controller requires `--gates-file` plus either `--all-slides` or `--slides`.

## Prior Output Reuse

Do not reuse existing `baseline`, `key-text`, `text_layout_manifest.json`, textless backgrounds, old run outputs, or source-directory artifacts unless the user explicitly asks to reuse them. For a fresh conversion, start from the provided source PPTX or image, create a new run directory, and produce per-slide worker outputs under that run. Existing artifacts may be inspected for diagnosis only; they are not valid final conversion evidence.

## Per-Slide Contract Hardening

Every deck-controller slide job writes two small execution contracts next to `slide_job_manifest.json`:

- `page_conversion_contract.json`: the per-slide execution lock for default font, no invented effects, no invented text backing fills, complex-visual crop-first judgment, and the fidelity-over-extra-native-shapes fallback decision.
- `crop_manifest_contract.json`: the crop planning contract for `crop_manifest.json`, textless crop review gates, semantic region planning, protected non-text anchors, and accepted crop strategies.

Per-slide workers must read both contracts before writing `source_reconstruction_plan.json`. These files are intentionally short so workers do not have to re-summarize long references from memory.

Before packaging, classify regions with the generated `routing_decision_table`:

- pure meaningful text -> native editable text;
- simple flat geometry -> native shape when faithful;
- complex visual modules -> source crop;
- text inside complex visual modules -> textless crop plus editable text;
- unusable OCR -> failed-retryable or image fallback, not a fake quality conversion.

Keep context small. For a fresh multi-page run, read `AGENT_TASK.md`, `slide_job_manifest.json`, `WORKER_COMPACT_PROTOCOL.md`, `page_conversion_contract.json`, and `crop_manifest_contract.json` first. Read full `SKILL.md` or long references only when blocked, when a QA gate fails, or when the compact protocol is ambiguous. Do not read historical test reports, old round outputs, prior visual QA HTML, or baseline artifacts unless the user explicitly asks to reuse them for diagnosis.

## 3.1 High-Risk Crop-First Gate

Reconstruction-first does not mean all-native. The standard path for a high-risk visual region is:

1. keep simple text editable;
2. keep simple flat geometry native only when it remains source-faithful;
3. keep complex source-specific visuals as bounded source crops or textless crops;
4. overlay reviewed editable text on top of textless crops;
5. run `check_reconstruction_visual_strategy.py`, text fit, packaging, editability, and rendered PNG QA before marking success.

High-risk visual types include curved connectors, stepped or bracket arrows, side funnels, icon-connected paths, complex process-card groups, bridge/risk modules, product-photo/detail-icon groups, gradient or textured arrow bars, layered card stacks, complex matrix backgrounds, and source-specific process matrices.

For high-risk regions, `actual_strategy` must be crop-first: `source_crop`, `source_textless_crop`, `local_textless_crop`, `textless_crop`, `source_icon_crop`, `tight_source_crop`, `clean_badge_composite`, or `textless_crop_plus_editable_text`. `native_redraw`, `native_lines`, `native_shapes`, and `native_reconstruction` are rejected for high-risk regions even when `override_reason` is present.

Each `region_crop_plan` entry must be a real object with `id`, `strategy`, `source_bbox_px`, and `reason`. Do not pad missing region plans with strings or `not-reported` placeholders.

Stop and revise the strategy before packaging if you write or see any of these red flags:

- "main structure native reconstruction";
- "native reconstruction is acceptable for this low-download run";
- "not pursuing pixel-perfect reconstruction";
- "fixed strategy review then reran" while the plan still uses native redraw for a high-risk region;
- a high-risk slide has `pictures=0`, `croppedPictures=0`, and many native shapes/lines;
- the visual strategy report says `native_redraw_used_for_high_risk_region`.

## Multi-Page Workflow

For image-only `.pptx` deck inputs:

1. Run `scripts/deck_controller.py --probe`.
2. Ask the Conversion Mode Gate. If the user chooses single-page mode, choose one sample slide and do not run `--all-slides`.
3. If OCR is already `passed-text-usable`, record the auto-pass in `gates.json`; if not, ask the OCR Runtime Gate before setup or limited fallback.
4. Apply the Scope + Worker Gate according to the selected mode and write `scope_and_worker_gate` into `gates.json`. In single-page mode, select exactly one sample slide. In multi-page multi-Agent mode, ask whether to convert all pages or selected pages. Do not start deck initialization or dispatch before the user chooses page scope and acknowledges token implications.
5. If setup is needed and confirmed, run `scripts/setup_ocr_runtime.py --gates-file GATES.json --yes`, then run `scripts/check_ocr_runtime.py --json`.
6. Run `scripts/deck_controller.py` on the source deck with `--gates-file` to validate image-only structure, extract unchanged per-slide source images, write `deck_manifest.json`, and create one `slide_job_manifest.json` plus `AGENT_TASK.md` per selected slide. If the run uses an external OCR runtime, pass `--ocr-python` and `--ocr-deps` during this initialization step. Do not initialize with system Python and expect per-slide workers to repair the deck-level OCR state later.
7. Run `scripts/prepare_worker_dispatch.py RUN_DIR --worker-mode app-native|external-codex|manual`. If it blocks external worker use, do not launch `codex exec`.
8. In `multi-agent-high-quality`, dispatch each slide job to a real separate per-slide worker. The controller/test thread must not build multiple slide outputs itself.
9. Each slide task reads the generated `AGENT_TASK.md`, `slide_job_manifest.json`, `WORKER_COMPACT_PROTOCOL.md`, `page_conversion_contract.json`, and `crop_manifest_contract.json`, then processes exactly one source PNG using this skill's integrated v3.1 single-page scripts. Full `SKILL.md` and long references are fallback reading, not default reading.
10. Each slide task runs the appropriate deterministic single-page chain, normally `run_reconstruction_qa.py` for reconstruction/mixed reconstruction, plus OCR, crop, editability, and PowerPoint render QA scripts as needed.
11. Each slide task runs `scripts/write_slide_qa_summary_from_single_page.py` to convert the single-page QA output into the deck-controller `qa_summary.json` contract.
12. The controller runs `scripts/deck_controller.py --finalize` to assemble accepted editable slide PPTXs and image-fallback pages with a top-right yellow sticker for failed pages. Finalize must reuse the existing `deck_manifest.json`; it must not rebuild deck preflight, recreate slide jobs, or overwrite the OCR runtime state recorded at dispatch.

Controller command shape:

```text
python scripts/deck_controller.py SOURCE.pptx --probe --ocr-python OCR_PYTHON --ocr-deps OCR_DEPS
python scripts/deck_controller.py SOURCE.pptx --run-dir RUN_DIR --gates-file GATES.json --all-slides --ocr-python OCR_PYTHON --ocr-deps OCR_DEPS
python scripts/deck_controller.py SOURCE.pptx --run-dir RUN_DIR --gates-file GATES.json --slides "1,3,5" --ocr-python OCR_PYTHON --ocr-deps OCR_DEPS
python scripts/prepare_worker_dispatch.py RUN_DIR --worker-mode app-native
python scripts/deck_controller.py SOURCE.pptx --run-dir RUN_DIR --finalize
```

If `deck_manifest.json` says `ocr_runtime_status` is not `passed-text-usable`, stop before dispatching workers unless the user explicitly accepts a fallback-only run. A quality editable run should not continue with a deck-level OCR failure.

For quality tests, successful pages must report `single_page_engine_used: "ppt-to-editable-v3-1-preview"` and list the v3.1 scripts actually called. They must also report `fallback_references_read`, using an empty list when no long reference was needed. A page that calls any external development folder as its primary engine should be marked `failed-retryable`, not accepted.

Sequential token-saving is retired and should not be used for release workflows. If a gates file or dispatch request uses `multi-page-sequential-token-saving` or `worker_mode: "sequential"`, stop and ask the user to choose either single-page token-saving mode or multi-page multi-Agent high-quality mode.

## Reconstruction-First Hard Gate

For structured business slides, default to `reconstruction` or mixed reconstruction. Reconstruction is plan-driven once a reviewed `source_reconstruction_plan.json` exists: use `scripts/package_reconstruction_deck.py` to mechanically package native shapes, lines, editable text, and tight source crops into PPTX.

Hard constraints:

- If a slide is dominated by cards, rows, columns, real tables, process steps, funnels, timelines, lanes, badges, simple arrows, or repeated modules, route it to `reconstruction` or mixed reconstruction first.
- Do not silently downgrade a reconstruction-friendly slide to `clean-background` just because a generic reconstruction packager is unavailable.
- If reconstruction is the right route but no reconstruction plan or implementation exists yet, stop and mark the slide `requires_reconstruction_plan`. A clean-background PPTX may be produced only as a clearly labeled interim baseline, not as the final conversion.
- If a reviewed reconstruction plan exists, do not rewrite a one-off build script. Run the deterministic packager and QA scripts first.
- A PPTX labeled `reconstruction` must include `source_reconstruction_plan.json` or an equivalent layer plan, plus `editability_report.json`.
- A reconstruction report must prove native reconstruction: `nativeShapes > 0` for shape/card/line pages, `nativeTables > 0` for semantic table pages, and tight `pictures` only for complex source crops. `editableTextBodies` alone is not reconstruction.
- A reconstruction PPTX must not contain a full-slide background disguised as reconstruction unless the user explicitly accepted that fallback.
- In mixed reconstruction, a single whole-slide/background picture cannot count as evidence for multiple semantic regions. Region crop plans must map to bounded local crop/native objects.
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
- Rebuild simple geometry as native shapes: rectangles, rounded cards, circles, badges, rules, native line arrows, and true dashed lines.
- Rebuild table regions as native PowerPoint tables when the source is a real row/column grid; do not fake tables with separate lines, rectangles, or grouped boxes unless the user explicitly accepts that fallback.
- Keep complex visual regions as tight transparent PNG crops from the original source image: photos, product screenshots, gradients, shadows, curved translucent paths, dense diagrams, complex icons, and detailed illustrations.
- Do not approximate-redraw complex visuals just because a clean redraw looks close.
- For complex icon modules, gradient pills/bars, arrow-ended bands, shaded circular icon badges, and other source-specific visual modules, prefer a tight source-derived crop plus native editable text over a visibly drifting native redraw.
- When a source crop contains readable text that should be editable, remove that text from the crop first, then place reviewed native text above it. Do not leave duplicate source text under editable text.
- Preserve relative font size hierarchy. Do not shrink readable body, callout, or panel text into tiny outliers just to make a guessed layout fit.
- Do not add invented pale rectangles or generic backing fills behind editable text. Use transparent text over source-matched native backgrounds or textless source crops.
- Preserve non-text visual anchors when removing source text from crops. Textless crops must not erase arrows, arrowheads, route lines, connectors, step markers, card edges, cut corners, dividers, or icons.
- Write a layer plan and editability report before delivery.

Read `references/reconstruction-contract.md` and `references/ocr-layout-recovery.md`.

Use reconstruction first for structured business slides: tables, repeated cards, layer diagrams, numbered process rows, product-pill matrices, decision grids, flowcharts, roadmaps, simple funnels, and pages where most visual objects are rectangles, lines, circles, badges, arrows, and labels.

### Native Shape Styling

For native reconstruction, default to flat PowerPoint objects. Do not introduce shadows, glow, bevel, reflection, soft edges, or theme effect styles unless the source image clearly uses that effect and it is necessary for fidelity. Simple cards, metric panels, bars, badges, separators, list rows, and chart scaffolds should be flat by default.

When building with python-pptx or direct OOXML, explicitly clear inherited `effectRef`, `effectLst`, and `effectDag` styling on generated native shapes, connectors, text boxes, and source-crop pictures. Do not add decorative shadows to make the output look more designed.

### Mixed Reconstruction Fidelity Decisions

Use native objects where they preserve the source visual without drift. Do not maximize `nativeShapes` at the expense of recognizable source fidelity.

- Rebuild flat containers, simple dividers, plain circles, plain rounded rectangles, and true dashed guides as native PowerPoint objects.
- Rebuild simple axis arrows, flow arrows, and direction indicators as native line elements with `start_arrow` or `end_arrow`; do not approximate them with editable arrow glyph text such as `←`, `→`, `↑`, or `↓`.
- Keep detailed icons, shaded icon badges, gradients, shadows, arrow-ended bands, and source-specific pill/bar backgrounds as tight source crops when a native redraw changes the style.
- Keep curved connector paths, thick stepped connectors, bracket arrows, side funnels, side path modules, and icon-connected navigation paths as local source crops when native line reconstruction looks like a PowerPoint template.
- For side modules that combine icons, paths, arrows, and explanatory text, create a local textless module crop and overlay editable text. Do not split the module into many native lines unless the result visually matches the source.
- For bridge/risk pages that combine multi-column cards, icons, connector ribbons, risk rows, or takeaway strips, prefer bounded local textless module crops plus editable text. Split the page into semantic crops such as `main-bridge-module`, `risk-row`, and `takeaway-strip`; do not use one full-slide picture as a shortcut.
- If a textless module crop creates visible cleanup patches inside flat header bars or solid labels, cover only those small bars with native flat rectangles and editable text instead of expanding the crop or accepting patch residue.
- Do not treat a low `nativeShapes` count as failure when `fullSlidePictures=0`, local crops are bounded to semantic modules, meaningful text is editable, multiline semantic text remains grouped, and `visual_strategy_report.json` explains why native redraw would drift.
- For repeated icon rows, crop from the original source image, use consistent square crop sizes for same-size modules, align by measured center points, and create a debug sheet for visual QA.
- For circular icon badges, crop the full badge including the white circular base, border, subtle shadow, and minimal safe padding. Do not use a crop that touches or clips the circle edge, even if the central icon glyph is complete.
- If a full circular badge crop shows a visible halo or background ring after rendering, reduce the crop size while keeping the circle complete; do not fall back to a too-tight crop.
- If the full circular badge area is too close to a source card edge, shadow, or connector and every complete crop brings in dirty gray residue, crop the source icon glyph from the original image and place it on a clean, source-matched circular badge base. Record this as a clean badge composite, not as a fully native icon redraw.
- For clean badge composites, reject pale gray source badge-edge residue inside the circle. Filter the glyph extraction to keep visible icon ink and remove leftover badge arcs before packaging.
- Do not derive icon glyph crop centers only from repeated row spacing or assumed badge centers. For each badge, start from a complete source badge crop, detect the visible icon glyph bounding box, expand it with safe padding, and reject the crop if visible icon ink touches the glyph crop edge. Use `scripts/make_clean_badge_composites.py` for this workflow instead of writing one-off badge crop scripts.
- For gradient or arrow-ended bars with text, create a textless bar background crop, then overlay editable PowerPoint text using the reviewed source text bbox. Reject the crop if text residue remains visible.
- In v3.1 preview, use `scripts/extract_source_crops.py` and `scripts/make_textless_crops.py` for reviewed crop manifests before writing one-off crop code.
- A lower native shape count is acceptable when it replaces a visibly wrong native redraw with a faithful tight source crop; record this tradeoff in the editability report.
- Do not treat `nativeLines` count as proof of quality. A complex connector that becomes visually clumsy after native redraw should be rejected as `complex connector approximate redraw`.
- Product photos, detailed icons, curved paths, gradient arrows, textured modules, layered card stacks, and source-specific process visuals use crop-first judgment; high-risk native redraw is blocked by 3.1 gates unless the region is reclassified out of high risk with real rendered evidence.
- Editable text boxes remain transparent unless the source already has a visible card, bar, pill, or label background behind that text.
- Textless crop quality includes structure preservation. If a crop removes a visible arrowhead, breaks a route line, clips an icon, drops a step marker, or erases a card edge/cut corner, redo that crop or keep the affected anchor as a source-derived element before claiming success.

### Visual Strategy Review

Before packaging a mixed reconstruction plan, explicitly mark high-risk visual regions in `strategy_review.regions`. This is required when the slide contains curved connector modules, thick stepped connectors, bracket arrows, side path modules, side funnels, icon-connected navigation paths, complex process-card groups, bridge/risk modules, or grouped icon-card-connector systems.

For each high-risk region, record:

- `visual_type`: what kind of risky visual it is.
- `expected_strategy`: usually `source_textless_crop` for text-bearing complex modules.
- `actual_strategy`: the chosen implementation.
- `evidence_element_ids`: the picture/native elements that implement the region.
- `text_overlay_element_ids`: editable text boxes placed above the textless crop.
- `reason`: why the strategy was chosen.

Run `scripts/check_reconstruction_visual_strategy.py` before text fit and packaging when strategy review is present. Use `--require-strategy-review` for regression cases or when the page has obvious high-risk visual modules. Do not treat a plan as visually reviewed just because it has many native lines or shapes.

For v3.1 preview multi-page workers, the final `qa_summary.json` must also report `font_size_consistency_review`, `complex_visual_strategy_review`, `text_background_policy`, and `non_text_anchor_preservation_review`. Success is rejected when these fields are missing or report tiny-font drift, unresolved complex native redraw drift, invented text backing fills, or missing/broken/cropped non-text anchors.

## Routing

If the input contains extractable native PPT text or vector objects, inspect them before OCR. Preserve native objects where they are correct.

If the input is image-only, scanned, screenshot-based, or has rasterized text, OCR first.

For deck inputs:

1. Extract each slide/page to an unchanged source image.
2. Create one slide job per source image.
3. Run OCR and review gates per slide.
4. Choose `clean-background`, `reconstruction`, or a mixed route per slide.
5. Build and preview each slide independently.
6. Assemble the final deck only from slide outputs that pass their gates or are explicitly marked with limitations.

If the user does not choose a mode:

- choose `reconstruction` for pages dominated by simple geometry, cards, tables, labels, and lines;
- use mixed reconstruction inside a page when appropriate: native simple layers plus tight crops for complex regions.
- choose `clean-background` only for visually complex slides where preserving look matters most and native reconstruction would visibly drift.

Read `references/deck-routing-and-qa.md` before converting any multi-slide deck or whenever a single slide has both hybrid-friendly visuals and reconstruction-friendly structure.

Never promise full-native conversion unless the user provides the original PPT, vector design file, or chart/source data.

## Required Artifacts

For image-source quality runs, keep:

- original source image(s), unchanged;
- `ocr_runtime_report.json` before OCR-dependent runs;
- `ocr_results.json`;
- `ocr_overlay_debug.png` when practical;
- `ocr_review_manifest.json` or equivalent per-slide QA report before packaging OCR text;
- `text_mask_debug.png` for clean-background text removal;
- `text_layout_manifest.json` for clean-background output, or `source_reconstruction_plan.json` for reconstruction;
- `page_conversion_contract.json` and `crop_manifest_contract.json` for deck-controller slide jobs;
- `crop_manifest.json` when source crops, textless crops, clean badge composites, or complex visual regions are used;
- `visual_strategy_report.json` for mixed reconstruction plans with high-risk visual regions;
- `text_fit_report.json` for reconstruction text fit review;
- preview image or rendered inspection artifact;
- PowerPoint/LibreOffice-rendered PNG when the local runtime supports it;
- `editability_report.json`.
- crop manifest, crop report, and crop debug sheet when source-derived crops are used.

## Text Rules

Default to conservative semantic grouping, not maximum text-box count and not forced paragraph merging.

Use one editable multiline text box when adjacent lines clearly belong to the same semantic text block and share all key style signals:

- same font face, normally Microsoft YaHei;
- same font size;
- same bold/italic state;
- same color;
- same alignment;
- same column or local visual region;
- tight vertical spacing with no icon, divider, shape, table boundary, or cross-column break between the lines.

For these blocks, write one `type: "text"` element with newline-preserved text, `trace_level: "paragraph"`, `semantic_block: true`, `word_wrap: true` when needed, and provenance such as `source_line_bboxes_px` or `source_element_ids`.

Keep line-level trace for short labels, card captions, legend labels, chart labels, axis labels, badge numbers, step numbers, table cells, one-line callouts, mixed-style text, and any text where visual placement requires separate boxes:

- one editable text box per accepted OCR line;
- `trace_level: "line"`;
- `semantic_block: false`;
- `no_wrap: true`;
- OCR `source_bbox_px`;
- OCR confidence and review status.

Do not merge across different font sizes, weights, colors, alignments, table cells, columns, labels, or visual regions. If a group looks mergeable but must remain line-level, mark the elements with `line_level_trace_required: true`, `do_not_merge: true`, or a clear role such as `legend_label`, `axis_label`, `table_cell`, `badge_number`, or `step_label`.

Before packaging, run `scripts/check_reconstruction_plan_text_fit.py`. Treat `candidate_multiline_split` as a review gate: either merge the candidate into one semantic text block or explicitly mark why line-level trace is required.

For short labels, card captions, legend labels, badge numbers, and one-line conclusion snippets, avoid PowerPoint auto-wrap when a single trailing Chinese character or punctuation would fall to a new line. Widen the text box, reduce font size within the readable range, or set `no_wrap: true`; do not accept one-character orphan wraps as a valid reconstruction.

Never send raw OCR directly to the final PPTX. Classify each OCR record first as `accepted`, `corrected`, `needs_review`, `omit`, `keep_in_background`, or `reconstruct_as_native`. Low-confidence single glyphs, icon text, numeric badges, decorative symbols, and unsupported vertical/rotated text should not become accidental horizontal editable text.

## Packaging And QA

For reconstruction output:

```powershell
python scripts/run_reconstruction_qa.py path\to\source_reconstruction_plan.json --source path\to\source.png --out-dir path\to\qa --require-strategy-review
```

Use `run_reconstruction_qa.py` as the default QA entrypoint for reviewed reconstruction plans. It runs visual strategy check, text fit check, deterministic packaging, editability inspect, PowerPoint render QA, comparison HTML generation, and `qa_summary.md/json`.

When debugging a single stage, run the steps separately:

```powershell
python scripts/check_reconstruction_visual_strategy.py path\to\source_reconstruction_plan.json --out path\to\visual_strategy_report.json --require-strategy-review
python scripts/check_reconstruction_plan_text_fit.py path\to\source_reconstruction_plan.json --out path\to\text_fit_report.json
python scripts/package_reconstruction_deck.py path\to\source_reconstruction_plan.json --out path\to\editable.pptx --report path\to\packaging_report.json
python scripts/inspect_pptx_editability.py path\to\editable.pptx --out path\to\editability_report.json
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\render_pptx_qa.ps1 -Pptx path\to\editable.pptx -OutDir path\to\render -Source path\to\source.png -Report path\to\render_report.json
```

Read `references/source-reconstruction-plan-schema.md` before writing or reviewing a reconstruction plan. Read `references/reconstruction-qa.md` before deciding whether a reconstruction output is acceptable.

For source-derived crop preparation:

```powershell
python scripts/extract_source_crops.py path\to\source-crops.json --out-dir path\to\crops --report path\to\crop_report.json --debug path\to\crop_debug_sheet.png --ocr-results path\to\ocr_results.json
python scripts/make_clean_badge_composites.py path\to\clean-badge-composites.json --out-dir path\to\badge-composites --report path\to\badge_composite_report.json --debug path\to\badge_composite_debug.png
python scripts/make_textless_crops.py path\to\textless-crops.json --out-dir path\to\textless --report path\to\textless_report.json --debug path\to\textless_debug_sheet.png
python scripts/build_crop_debug_sheet.py --from-report path\to\crop_report.json --out path\to\crop_debug_sheet.png
python scripts/apply_crop_report_to_plan.py path\to\source_reconstruction_plan.json --crop-report path\to\crop_report.json --out path\to\source_reconstruction_plan.with-crops.json --report path\to\crop_plan_sync_report.json
```

Read `references/source-crop-tools.md` before creating icon crop manifests, clean badge composite manifests, fixed-center icon grids, or textless source crops.

For textless crops, prefer `ocr_mask_ids` or `ocr_mask_mode: "intersecting"` when the text to remove already exists in `ocr_results.json`. Use manual `text_masks` only for OCR misses, extra padding, or deliberately adjusted cleanup regions.

Treat `ocr_text_overlap` in `crop_report.json` as a review gate. Fix the crop, use a textless crop, or explicitly mark the crop with `allow_text_overlap: true` only when the crop intentionally preserves source text.

For OCR-derived reconstruction plan scaffolds:

```powershell
python scripts/preflight_ocr_runtime.py --out path\to\ocr_runtime_report.json
python scripts/ocr_to_reconstruction_plan_scaffold.py path\to\ocr_results.json --source-image path\to\source.png --out path\to\source_reconstruction_plan.ocr-scaffold.json --review-manifest path\to\ocr_review_manifest.json
```

Read `references/ocr-to-plan-review-guide.md` before using OCR scaffold output. Never package an OCR scaffold as final until every generated text element is reviewed or omitted.

For clean-background output:

```powershell
python scripts/preflight_ocr_runtime.py --out path\to\ocr_runtime_report.json
python scripts/run_rapidocr.py path\to\source.png --out path\to\ocr_results.json --overlay path\to\ocr_overlay_debug.png
python scripts/package_clean_background_deck.py path\to\text_layout_manifest.json --out path\to\editable.pptx
python scripts/inspect_pptx_editability.py path\to\editable.pptx --out path\to\editability_report.json
```

For line-level trace fitting:

```powershell
python scripts/preflight_ocr_runtime.py --out path\to\ocr_runtime_report.json
python scripts/run_rapidocr.py path\to\source.png --out path\to\ocr_results.json --overlay path\to\ocr_overlay_debug.png
python scripts/apply_manifest_role_presets.py path\to\text_layout_manifest.json --out path\to\text_layout_manifest.roles.json
python scripts/fit_manifest_to_source_bboxes.py path\to\text_layout_manifest.roles.json --source path\to\source.png --out path\to\text_layout_manifest.bboxes.json
python scripts/fit_manifest_typography.py path\to\text_layout_manifest.bboxes.json --source path\to\source.png --out path\to\text_layout_manifest.fit.json
python scripts/judge_line_alignment.py path\to\text_layout_manifest.fit.json --source path\to\source.png --out path\to\line_alignment_judge.json
python scripts/apply_line_alignment_patch.py path\to\text_layout_manifest.fit.json path\to\line_alignment_judge.json --out path\to\text_layout_manifest.patched.json
```

Use `scripts/render_manifest_first_preview.py` or `scripts/render_manifest_alignment_preview.py` when a visual preview of source image plus editable text boxes is needed before packaging. Use `scripts/trace_manifest_to_line_boxes.py` when paragraph or block boxes fail to preserve source line breaks.

For reconstruction text fitting before packaging:

```powershell
python scripts/check_reconstruction_plan_text_fit.py path\to\source_reconstruction_plan.json --out path\to\text_fit_report.json
```

Treat `text_overflow_risk`, `punctuation_orphan_line`, and `single_character_line` as review gates. Fix the text box size, font size, line breaks, or no-wrap settings before packaging unless the limitation is explicitly accepted.

For mixed reconstruction visual strategy before packaging:

```powershell
python scripts/check_reconstruction_visual_strategy.py path\to\source_reconstruction_plan.json --out path\to\visual_strategy_report.json --require-strategy-review
```

Treat `native_redraw_used_for_high_risk_region`, `expected_textless_crop_missing`, and `textless_crop_text_overlay_missing` as review gates. Fix the strategy review or add the missing crop/textless crop before packaging. In v3.1, `override_reason` does not bypass a high-risk native redraw warning.

Before delivery, verify:

- final visible background has no source text residue;
- every meaningful text line is editable or explicitly omitted with a reason;
- deck outputs were routed per slide rather than forced through one mode unless explicitly requested;
- every OCR line included in the PPTX passed review or has a recorded correction;
- clean-background PPTX has one full-slide background per slide plus editable text boxes;
- reconstruction PPTX does not use a disguised full-slide background unless explicitly accepted as a fallback;
- simple shapes are native where practical;
- source tables are native PowerPoint tables, with row/column structure preserved in the editability report;
- complex regions are tight source-derived transparent crops;
- reconstructed native objects do not introduce new shadows or PowerPoint effects unless source-matched;
- high-risk visual modules have a passing `visual_strategy_report.json`; `override_reason` is not enough when the region is still high-risk native redraw;
- no-wrap and no-autofit are present for line-level trace text boxes;
- the editability report separates editable text, native shapes, source crops, OCR corrections, omitted lines, and limitations.
- preview QA catches visual failures, not only structure counts. `editableTextBodies` and ZIP/XML validity do not prove visual quality.
- the PPTX opens or renders in PowerPoint/LibreOffice when those apps are available; ZIP/XML validity alone is not enough for delivery.
- if PowerPoint COM reports `PowerPoint could not open the file` for an image-heavy deck opened headlessly, retry with a visible/windowed open before labeling the PPTX as corrupt.

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
- `complex icon approximate redraw`
- `gradient bar native drift`
- `source crop text residue`
- `icon grid uneven spacing`
- `text arrow glyph used for native arrow`
- `complex connector approximate redraw`
- `side module approximate redraw`
- `native count over fidelity`
- `visual module should be textless crop`
- `unwanted native shadow/effect`
- `oversized crop selection box`
- `native shape drift`
- `table rebuilt as lines`
- `dashed guide not native`
- `editability report missing`
- `powerpoint-open-fail`
- `deck forced through one mode`
- `raw ocr accepted without review`
- `structured page forced into hybrid`
- `rotated text rendered horizontally`
- `icon or badge text duplicated`
- `visual qa skipped`
- `ocr runtime preflight failed`
- `source crop overlaps OCR text`
- `text fit preflight warning ignored`
- `punctuation orphan line`
