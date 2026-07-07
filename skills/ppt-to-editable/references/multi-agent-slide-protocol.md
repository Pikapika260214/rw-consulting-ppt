# Multi-Agent Slide Protocol

Use this reference before processing a slide job in a multi-page PPT-to-editable run.

## Role

A per-slide Agent creates a slide draft. It is not the final judge of deck quality.

Per-slide output becomes final only after deck-level QA accepts it.

The controller/test Agent must not convert multiple slides by writing one batch script. A valid multi-page run requires real per-slide workers. Each worker processes exactly one slide and reports its worker identity.

Before dispatching workers, the controller/test Agent must run:

```text
python scripts/prepare_worker_dispatch.py RUN_DIR --worker-mode app-native|external-codex|manual
```

This report is the local authorization check for worker mode, token-cost acknowledgement, and content-sharing acknowledgement. It does not launch workers. If it reports `blocked-external-worker-not-approved`, do not run `codex exec` or any external worker launcher.

## Required Reading

For v3 preview multi-page runs, read the compact per-slide packet first:

1. `AGENT_TASK.md`.
2. `slide_job_manifest.json`.
3. `WORKER_COMPACT_PROTOCOL.md`.
4. `page_conversion_contract.json`, if listed in the slide job manifest.
5. `crop_manifest_contract.json`, if listed in the slide job manifest.

Record these compact files in `qa_summary.json` under `references_read`.

Read the full `SKILL.md` and long references only when blocked, when a QA gate
fails, or when the compact protocol is ambiguous. If a fallback reference is
read, record it in `qa_summary.json` under `fallback_references_read`.

The generated per-slide contract files are part of the task, not optional
background material. Read them before writing `source_reconstruction_plan.json`.
If either file is listed in `slide_job_manifest.json` but missing or unreadable,
stop with `failed-retryable`.

External local development folders are not the primary reference for this v3
preview package. If this package's scripts or references are missing or
unreadable, stop with `failed-retryable`; do not silently downgrade to another
skill folder.

For successful reconstruction or mixed reconstruction outputs, report:

```json
{
  "single_page_engine_used": "ppt-to-editable-v3-1-preview",
  "single_page_engine_scripts_used": [
    "run_reconstruction_qa.py"
  ]
}
```

The controller rejects a successful status if this evidence is missing or if a
reconstruction page does not report the integrated deterministic packager / QA path.

After the single-page QA chain writes its own `qa_summary.json`, run the v3 handoff
helper from the generated `AGENT_TASK.md`:

```text
python scripts/write_slide_qa_summary_from_single_page.py ...
```

This helper converts the single-page QA output into the full v3 controller
handoff format, preserves the original single-page summary as `qa_summary.single-page.json`,
normalizes render report paths, and appends the `qa_done` progress milestone.
Do not hand-write the final 3.0 `qa_summary.json` unless the helper fails; if
it fails, mark the slide `failed-retryable` and report the helper error.

## P1 Contract-First Execution

Before reconstructing a slide, treat the slide job manifest as the controller's
source of truth. Use these generated fields in order:

1. `page_conversion_contract`: execution rules for text, shapes, effects,
   fallback decisions, and source dimensions.
2. `crop_manifest_contract`: required evidence for source crops, textless
   crops, protected visual anchors, and semantic region splitting.
3. `routing_decision_table`: the default route for each region type.
4. `reference_loading_policy`: the minimum references to read and the historical
   artifacts that must stay out of context unless the user explicitly asks.

Use the routing decision table before drafting `source_reconstruction_plan.json`:

- pure readable text -> editable native text;
- simple flat geometry -> native shape;
- complex artwork, product images, shaded cards, detailed icon groups, route
  arrows, and source-specific panels -> source crop or textless crop plus
  editable text;
- OCR unusable -> retry or image fallback, not manual guessing disguised as
  success.

When any source crop, textless crop, or complex visual region is used, write
`crop_manifest.json` before packaging the slide. The manifest should list the
region id, bbox/source path, chosen strategy, protected anchors, text removal
scope, and reason. If no crop is needed, write an empty manifest with:

```json
{
  "regions": [],
  "reason": "no_source_crops_required"
}
```

Do not satisfy a semantic region crop plan with one whole-slide/background
picture. If multiple crop-first regions all cite the same full-slide picture,
the slide has not done region-level crop planning. Mark it `failed-retryable` or
`image-fallback` unless the user explicitly accepted a whole-slide fallback.

Do not load historical round outputs, old visual QA HTML, baseline artifacts, or
previous test reports to guide a new clean-context conversion unless the user
explicitly asks for that comparison. Those files can leak prior manual fixes into
what should be a fresh skill test.

## Progress Heartbeat

Write `progress.json` in the attempt directory at these milestones:

- `started`
- `ocr_done`
- `plan_done`
- `packaging_done`
- `qa_done`

Each progress update must include:

```json
{
  "status": "ocr_done",
  "updated_at": "ISO-8601 timestamp",
  "current_step": "short description",
  "outputs_created": ["relative/path"]
}
```

`progress.json` must preserve all milestones, not only the latest one. Use a list or an object with `history`, `events`, `milestones`, or `checkpoints`.

Example:

```json
{
  "history": [
    {"status": "started", "updated_at": "ISO-8601 timestamp", "current_step": "read required references", "outputs_created": []},
    {"status": "ocr_done", "updated_at": "ISO-8601 timestamp", "current_step": "OCR completed or failed with recorded reason", "outputs_created": ["ocr_results.json"]},
    {"status": "plan_done", "updated_at": "ISO-8601 timestamp", "current_step": "reconstruction plan written", "outputs_created": ["source_reconstruction_plan.json"]},
    {"status": "packaging_done", "updated_at": "ISO-8601 timestamp", "current_step": "slide.pptx written", "outputs_created": ["slide.pptx"]},
    {"status": "qa_done", "updated_at": "ISO-8601 timestamp", "current_step": "QA summary written", "outputs_created": ["qa_summary.json"]}
  ]
}
```

If the file only contains a final `qa_done` status, the controller treats the slide as `failed-retryable`.

## Render QA Helper

Use the bundled render helper instead of writing ad hoc PowerPoint export code:

```text
python scripts/render_pptx_qa.py slide.pptx --out-dir render --source source.png --report render_report.json
```

The helper creates:

- `render/rendered.png`
- `render_report.json`

`render_report.json` must have `status=rendered` for a slide to be eligible for `passed` or `accepted-with-limitations`.

If PowerPoint is unavailable, the helper reports `renderer-unavailable`. That is not a successful rendered QA loop. The worker should mark the slide `failed-retryable` or `image-fallback`, not claim rendered review.

## Worker Identity

`qa_summary.json` must include:

```json
{
  "worker_identity": {
    "worker_thread_id": "Codex thread id when available",
    "worker_agent_id": "runtime agent id when available",
    "execution_model": "delegated-real-per-slide-worker",
    "slide_scope": [1]
  }
}
```

Rules:

- At least one of `worker_thread_id` or `worker_agent_id` is required.
- `slide_scope` must contain exactly the current slide index.
- The same worker identity cannot be reused for multiple successful slides.
- A controller/test thread that creates multiple `slide.pptx` files itself must mark those pages `failed-retryable`; it must not invent different worker ids.

## Conversion Mode Gate

`deck_manifest.json` must include `user_confirmation_gates.conversion_mode_gate`.

The user-facing choice is:

- `single-page-token-saving`: use this for one PNG or exactly one selected sample slide. Do not dispatch all pages.
- `full-deck-convenience`: use this for multi-page PPTX conversion.

The user should see plain language:

- 单页省 token 模式：转一页或单张 PNG，消耗较低。
- 全量省力模式：转整份 image-only PPTX，消耗较高，因为会按页拆开处理。

Required fields:

```json
{
  "user_choice": "single-page-token-saving | full-deck-convenience",
  "user_response_quote": "actual user answer"
}
```

Rules:

- `single-page-token-saving` must map to exactly one slide when the input is PPTX.
- `single-page-token-saving` must not use `--all-slides`.
- `full-deck-convenience` must not silently run from a generic "convert this PPTX" request; the user still needs to confirm page scope.

## Worker Dispatch Gate

`deck_manifest.json` must include `user_confirmation_gates.scope_and_worker_gate`.

The user-facing question must be plain language. Ask the user how many pages to
convert and explain that more pages cost more tokens and that each page will be
read by a separate conversion task. Do not ask the user to approve
`app-native`, `worker_mode`, `scope_and_worker_gate`, or `Codex worker runtime`
directly; those terms are internal recording fields.

Required fields:

```json
{
  "user_choice": "all | selected | sample",
  "slides": "1,3,5 when selected or sample",
  "worker_mode": "app-native | external-codex | manual",
  "worker_execution_approved": true,
  "external_codex_worker_approved": false,
  "token_cost_acknowledged": true,
  "content_sharing_acknowledged": true,
  "user_response_quote": "actual user answer"
}
```

Rules:

- `worker_execution_approved` must be true before any per-slide worker starts.
- `token_cost_acknowledged` must be true because every selected slide is a separate worker task.
- `content_sharing_acknowledged` must be true because per-page task content is sent to the worker context.
- `external_codex_worker_approved` must be true before using `worker_mode: "external-codex"` or any `codex exec`-style external worker launcher.
- If the user did not approve external Codex workers, use app-native workers or manual clean-context worker prompts only.

## OCR Runtime

Use the `ocr_runtime` specified in `slide_job_manifest.json`.

Do not silently fall back to shared `.deps` or the system Python. If the specified OCR runtime fails, record the error and stop with `failed-retryable`.

The deck controller must receive the same OCR runtime during the initialization command that creates `deck_manifest.json` and the slide job manifests:

```text
python scripts/deck_controller.py SOURCE.pptx --probe --ocr-python OCR_PYTHON --ocr-deps OCR_DEPS
python scripts/deck_controller.py SOURCE.pptx --run-dir RUN_DIR --gates-file GATES.json --all-slides|--slides "..." --ocr-python OCR_PYTHON --ocr-deps OCR_DEPS
python scripts/prepare_worker_dispatch.py RUN_DIR --worker-mode app-native
```

The first command is read-only. The second command is allowed only after `gates.json` records the Python Runtime Gate, Conversion Mode Gate, OCR Runtime Gate state, and the combined Scope + Worker Gate answer. The dispatch report must pass before workers start. If Python dependencies are not ready, stop for dependency setup; do not replace the packaged script chain with a temporary PowerShell or one-off PPTX builder.

Do not start per-slide workers if `deck_manifest.json` records `ocr_runtime_status` other than `passed-text-usable`, unless the user explicitly asked for a fallback-only diagnostic run. Per-slide workers can prove their own OCR succeeded, but deck-level finalize still uses the dispatch-time OCR state as a quality gate.

During `--finalize`, the controller must reuse the existing `deck_manifest.json`. It must not recreate the manifest, regenerate slide jobs, or replace the dispatch-time OCR runtime state with the current shell Python.

OCR has three controller-level states:

- `passed-text-usable`: OCR dependencies run and the built-in Chinese sample is readable enough for text reconstruction.
- `passed-geometry-only`: OCR dependencies run, but Chinese text is not trustworthy; it may help find text positions but cannot be used as final text.
- `failed`: OCR cannot be used reliably.

Copy the dispatched `ocr_runtime.status` from `slide_job_manifest.json` into `qa_summary.json` as `ocr_runtime_status`, unless your slide-local check proves a stricter failure.

For quality forward tests, OCR unavailable or geometry-only OCR is not a minor limitation. A slide whose text placement depends on manual OCR/layout guessing should be `failed-retryable` or `image-fallback`, not `passed` or `accepted-with-limitations`.

## Output Status

Allowed `qa_summary.status` values:

- `draft`: produced but not self-approved.
- `passed`: passed required rendered visual QA and structural QA.
- `accepted-with-limitations`: structurally useful but missing some final QA or has recorded fidelity limits.
- `failed-retryable`: failed in a way a second attempt can address.
- `image-fallback`: should enter final deck as source PNG plus failure sticker.

Do not mark `passed` if:

- rendered PowerPoint/LibreOffice QA is missing;
- `render_report.json` is missing or does not have `status=rendered`;
- OCR text was not reviewed;
- `ocr_runtime_status` is not `passed-text-usable`;
- Microsoft YaHei font policy was not applied or not reported;
- unwanted PowerPoint shadows/effects were not cleared or not reported;
- a complex structured page lacks a semantic region crop plan;
- multiple semantic regions cite the same whole-slide/background picture instead
  of bounded local crop/native evidence;
- the slide contains known crop clipping, duplicated source text, or obvious layout drift;
- arrows, arrowheads, route lines, connectors, step markers, card edges, dividers, or icons are missing, broken, cropped, or erased after reconstruction;
- the output is a full-slide image disguised as reconstruction.

Do not mark `accepted-with-limitations` for blocking execution failures:

- OCR unavailable or manual text/layout guessing;
- text overlap or overflow;
- font fallback;
- unwanted native effects;
- major layout drift;
- obvious text-size drift versus source;
- complex page without a semantic 3-5 region plan.

`accepted-with-limitations` is for minor visual tradeoffs, such as non-editable source-crop icons or slight texture mismatch.

## Required `qa_summary.json`

Include at least:

```json
{
  "status": "accepted-with-limitations",
  "mode": "mixed-reconstruction",
  "references_read": [
    "single_page_engine_skill_3_0",
    "single_page_engine_source_crop_tools",
    "single_page_engine_reconstruction_qa",
    "single_page_engine_reconstruction_plan_schema",
    "single_page_engine_ocr_to_plan_review",
    "slide_job_manifest",
    "page_conversion_contract",
    "crop_manifest_contract",
    "visual_fidelity_contract",
    "visual_fidelity_execution",
    "multi_agent_slide_protocol"
  ],
  "font_policy_applied": "microsoft-yahei-all-runs",
  "effects_cleared": true,
  "rendered_png_reviewed": true,
  "render_report": "render_report.json",
  "region_crop_plan": [],
  "crop_manifest": {"status": "provided", "path": "crop_manifest.json"},
  "font_size_consistency_review": {"status": "reviewed", "issues": []},
  "complex_visual_strategy_review": {"status": "reviewed", "issues": []},
  "text_background_policy": {"status": "reviewed", "invented_text_backgrounds_added": false, "issues": []},
  "non_text_anchor_preservation_review": {"status": "reviewed", "missing_required_anchors": false, "issues": []},
  "editable_text_count": 0,
  "native_shapes_count": 0,
  "source_crop_count": 0,
  "visual_qa": {
    "rendered_qa_available": false,
    "preview_path": "",
    "known_visual_risks": []
  },
  "failure_reason": null,
  "limitations": [],
  "recommended_next_round_change": "",
  "worker_identity": {
    "worker_thread_id": "019...",
    "execution_model": "delegated-real-per-slide-worker",
    "slide_scope": [1]
  },
  "ocr_runtime_status": "passed-text-usable",
  "single_page_engine_used": "ppt-to-editable-v3-1-preview",
  "single_page_engine_scripts_used": ["run_reconstruction_qa.py"]
}
```

## Deck-Level QA Boundary

A controller may assemble a draft final deck for review, but final acceptance requires deck-level QA to review each slide output. `accepted-with-limitations` means "usable for review", not "approved by the user".
