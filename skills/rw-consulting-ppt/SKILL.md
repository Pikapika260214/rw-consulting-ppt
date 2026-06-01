---
name: rw-consulting-ppt
description: Use when the user wants to turn bullet points, rough notes, research findings, or a page outline into an image-only consulting-grade PPT deck, especially standalone report exhibits, live-presentation concept slides, full-slide PNGs, or PNG plus image-only PPTX. Use when editable PPTX or code-rendered slide pages are not allowed.
---

# RW Consulting PPT

Use this skill to convert bullet points, research notes, and rough outlines into a polished consulting-style deck made from full-slide images.

This is a sanitized public version of a message-first, proof-object-first PPT workflow. Preserve the method; do not preserve private names, local file paths, client context, real project examples, or personal branding.

## Routing Lock: Image-Only Consulting Slides

Default to image-only full-slide output.

- Build one complete 16:9 PNG per slide.
- Use Image2-style full-slide generation as the default route: native image generation of a complete text-heavy consulting slide from the approved slide brief, not generic image asset generation.
- If Image2 is unavailable, use only an equivalent full-slide image-generation backend that can generate complete consulting slide pages. If no such backend exists, stop after prompts.
- If a PPTX is delivered, each slide contains exactly one full-slide image.
- Do not create editable PowerPoint text boxes, chart objects, tables, shapes, SmartArt, or card grids.
- Do not satisfy this skill with HTML/CSS/React screenshots, SVG/canvas drawings, or Python/Pillow-rendered slide pages.
- Code may be used for file copying, contact sheets, validation, compression, and PPTX packaging only.
- If the user asks for editable PPTX, say this skill is image-only and offer to switch to a different workflow.

### Generation Backend Lock

RW Consulting PPT is the strategy, input-production, briefing, full-slide image contract, and QA layer. It is not a code-rendered slide engine.

When slide generation begins:

1. Use Image2-style full-slide generation: one native image-generation output per complete 16:9 consulting slide.
2. Generate only 1-2 representative full-slide PNG samples, show them, and wait for user approval.
3. After approval, batch-generate one complete full-slide PNG per slide through the same route.
4. Only after accepted PNGs exist, use `scripts/package_image_deck.py` or an equivalent mechanical packager to create an image-only PPTX.

Hard stop: if Image2-style full-slide generation or an equivalent image-generation path is unavailable, stop after slide briefs or image prompts and tell the user that image generation cannot continue in this environment. Do not fall back to HTML, CSS, React, SVG, canvas, Python, Pillow, browser screenshots, native PowerPoint layouts, or the Presentations plugin to create the slide design.

Acceptance check:

- `slidesWithEditableText = 0` when a PPTX is packaged.
- Every source image is 16:9 and visually inspected.
- The deck includes either representative PNG previews or a contact-sheet preview.
- The output looks like a consulting exhibit, not a generic poster or normal editable deck rasterized afterward.

## Reference Loading

Load only the references needed for the current task, but do not skip the visual governance references when they apply:

- Fresh project, ambiguous taste, or quality comparable to prior consulting-image work: read `references/consulting-image-context.md`.
- User provides a reference image, approved sample, good/bad example, or asks for style continuity: read `references/visual-style-master.md` and `references/example-lessons.md`.
- Before writing any Image2-style full-slide prompt: read `references/concept-image-director.md` and `references/message-hierarchy-rules.md`.
- When a page uses company examples, player categories, metrics, risks, gates, or validation claims: read `references/message-proof-mapping.md`.
- Before evaluating any generated sample: read `references/sample-rejection-rubric.md`.
- Multi-page deck after sample approval and before batch generation: read `references/deck-consistency-lock.md`.
- Packaging or validation questions: read `references/image-only-output-contract.md`.

If a required visual governance reference cannot be loaded, stop before image prompting and say which reference is unavailable.

When creating a production pack, record the loaded references in the pack or run notes so later runs can audit whether the visual rules were applied.

Do not copy private example assets into a public repo. If examples are needed, use bracketed neutral names such as `[Company A]`, `[Retailer B]`, or `[AI vendor]`.

## Visual Governance Locks

These rules are part of the core skill, not optional reference material. Apply them even if no reference file is loaded.

### Style Master Lock

If the user supplies a reference image, approved sample, good slide, bad slide, or previous successful output, treat it as the style master unless the user explicitly says not to.

Style master means the full-page rhythm, not just palette:

- action-title scale and placement;
- subtitle weight and proximity to the title;
- proof-object dominance and placement;
- evidence band structure;
- bottom-takeaway treatment;
- information density;
- typography mood, line weight, icon treatment, texture, and visual motifs.

If the style master conflicts with a new user request, state the tradeoff before prompting. If there is no style master, use RW's default consulting visual system.

### Deck Consistency Lock

For every multi-page deck, treat the approved sample as the basis for a deck-level system, not only as a single-page visual reference. Sample approval preserves the proof-object direction and quality bar; it does not automatically approve missing or drifting deck-system elements.

Before batch generation, write a `Deck System Contract` and reuse it verbatim in every slide prompt. The contract must lock only deck-level system elements:

- page marker choice: no markers anywhere, or one identical marker system on every slide;
- action-title scale, weight, top alignment, and title-block width;
- subtitle position and weight relative to the title;
- top-left motif or accent treatment, if any;
- source-note style;
- bottom-synthesis policy: none, every slide, or named judgment slides only;
- material treatment such as flat 2D, subtle depth, or 3D.

Do not globally lock page-local proof-object elements such as icons, diagrams, badges, or visual motifs unless they are part of a repeated deck-level component. Proof objects should vary when the page logic requires it; header, subtitle, source note, page marker, and bottom-synthesis systems must not drift.

Do not allow the image model to invent per-slide header or footer systems. Reject a batch if some pages have page markers and others do not, if marker styles differ, if title sizes materially drift, if a sample page lacks a deck-system element used elsewhere, or if only some pages acquire extra header badges, bottom banners, or source-note treatments.

Bottom synthesis is also a deck-level choice. Do not globally remove all bottom takeaways just because one sample had duplicate bottom conclusions. After sample approval, choose one policy: no bottom synthesis anywhere, one light bottom synthesis on every slide, or bottom synthesis only on named judgment slides. The chosen policy must be included in every batch prompt and checked in the contact sheet.

### Message Hierarchy Lock

Every slide must have one governing message and one highest-priority conclusion zone.

- Action title is the highest-priority conclusion. Do not create another title-like claim elsewhere.
- Subtitle explains why the title is true; it must not restate the title in different words.
- The main proof object is the visual protagonist.
- Main numbers must anchor the proof object. Do not place large KPI blocks where they read as a second title or second conclusion.
- Panel headers name evidence objects, not the same conclusion again.
- Bottom takeaway is optional at slide level but governed at deck level. It must appear at most once on a slide, synthesize the implication, and not become a third competing module.
- Source notes, caveats, and evidence-boundary lines must be low-weight. They cannot share the same visual weight as the action title or bottom takeaway.
- If a draft prompt contains action title, core message, explanatory sentence, source note, and bottom implication as separate visible layers, collapse them into the hierarchy before sending it to the image model.

### Claim-Evidence-Visual Lock

Every slide must map evidence to the exact claim it supports before visual design begins.

- Company, product, and metric examples must not remain as bare labels when the audience needs explanation. Turn them into short evidence sentences that say what market movement they indicate.
- Separate what is already evidenced from what remains pending, unproven, or only a hypothesis. The final slide does not need to say "does not prove", but the brief must know it.
- Lines, arrows, rings, gates, checkmarks, and color status are semantic claims. Do not connect an evidence item to an outcome, risk, gate, or trust claim it does not prove.
- If the message is "observed speed but pending trust", show observed signals and validation requirements as separate layers. Do not let a flywheel visually imply that safety, retention, or trust has already been solved.
- If the message is "players compete around different control points", use a control-point map or layered ecosystem instead of forcing a 2x2 with weak dimensions.

### Density Preservation Lock

For standalone report decks, treat information density as part of the style system, not as an after-the-fact preference.

- The design job is not to reduce evidence. The design job is to reduce reading friction while preserving the evidence structure.
- When the user approves a sample page, inherit its page rhythm, readable Chinese text density, annotation depth, evidence-band structure, and source-boundary treatment as part of the style master.
- Do not fix text-accuracy risk by turning a standalone report page into a sparse concept poster. Shorten text chunks when needed, but keep enough proof-object annotation, evidence anchors, business implications, and source boundaries for the page to be read without a presenter.
- If the output is clean but too empty for the approved delivery mode, reject it as a density failure, not as a visual success.

### Prompt Shape Lock

Do not feed the image model a flat list of equally important fields. Use this hierarchy:

1. Action title.
2. Subtitle, if needed.
3. Main proof object.
4. Evidence anchors attached to the proof object.
5. One bottom takeaway, if needed.
6. Low-weight source note or caveat, only when needed.

### Sample Rejection Lock

Reject and revise the prompt before asking for user approval if a sample has any of these issues:

- multiple conclusion zones;
- large numbers detached from the proof object and competing with the action title;
- bottom takeaway competing with the main visual;
- source note or caveat competing with the takeaway;
- generic dashboard, card grid, or ordinary PPT template feel;
- proof object not visible before supporting metrics;
- sparse concept-poster feel in standalone report mode: the page is clean but too empty to explain the argument without a presenter;
- one-note theme color such as all-green, all-teal, or all-blue line art;
- too many claims, caveats, and takeaways on one page.
- evidence misattribution: visual links imply that a company fact or metric proves a claim it does not support;
- label-only player evidence: company examples are too terse for a management reader to understand what they show;
- false precision chart: a 2x2 or axis map imposes dimensions that do not fairly apply to all plotted players;
- linework overload: boxes, borders, connectors, and pale fills make every module look equally important.

## Alignment Gate

Before creating any production artifact, run an alignment conversation.

This is a hard gate. If the user asks "generate a consulting PPT from this document" but has not explicitly provided the required preferences, the first response must be an alignment question, not an output file or production pack.

This skill has three separate approval gates. Do not collapse them:

1. Preference alignment: audience/use case, mode, page count, detail level, style/color, output format.
2. Storyline / blueprint approval: core question, working thesis, storyline, page list, and which page(s) will be sampled.
3. Sample brief approval: for the first 1-2 sample pages, visual mode, proof object, visual mother concept, must-keep text, bottom-synthesis policy, and prompt summary.

Do not create any of the following before alignment is confirmed:

- `Inputs for PPT Production`;
- deck blueprint;
- page outline;
- slide brief;
- Image2-style full-slide prompt;
- sample-generation prompt;
- production pack Markdown;
- PPTX packaging plan;
- generated images.

If the user already supplied some answers, summarize them and ask only for missing high-impact inputs. Do not force a long questionnaire when the direction is already clear. But do not infer user-controlled preferences silently unless the user has explicitly said to use defaults.

Minimum required user-controlled preferences:

1. Delivery mode: live presentation deck or standalone report deck.
2. Theme color / visual tone.
3. Page count or image count: exact count or acceptable range.
4. Detail level: concise, standard, or dense.
5. Visual style: boardroom strategy, management report, investor memo, product strategy, technical strategy, Xiaohongshu-readable, or user-supplied reference.
6. Delivery format: PNG images only, or PNG images plus image-only PPTX.

If any minimum item is missing, ask a concise alignment question first. Recommended shape:

```markdown
请确认下面 6 个偏好，我再开始产出，不然很容易跑偏：
1. 受众 / 使用场景：
2. 交付模式：presentation / 独立阅读型报告？
3. 页数 / 图片数：
4. 信息密度：简洁 / 标准 / 密集？
5. 视觉风格 / 主题色：
6. 输出格式：PNG / PNG + 图片型 PPTX
```

Required alignment items:

1. Audience and use case: who reads it, and what decision or impression should it create?
2. Core question: what should the deck answer?
3. Delivery mode: live presentation deck or standalone report deck.
4. Theme color: brand color, neutral analytical blue, black-white, green, warm neutral, or user-supplied palette.
5. Detail level: executive concise, standard consulting, or dense working deck.
6. Page count: exact count or acceptable range.
7. Page outline: user-provided page-by-page outline, or permission for Codex to propose one.
8. Language: Chinese, English, or bilingual.
9. Visual style: boardroom strategy, management report, investor memo, product strategy, technical strategy, or other.
10. Evidence boundary: which facts, numbers, screenshots, or source materials may be used?
11. Delivery format: PNG images only, or PNG images plus image-only PPTX.
12. Input-production mode: expand, compress, rewrite, sharpen, or preserve.

Stop condition: do not proceed to input production, blueprinting, slide briefs, image prompts, production pack creation, sample prompts, or generation until the user confirms the alignment summary or explicitly says "use defaults".

After preference alignment is confirmed, the next user-facing output must be `Inputs for PPT Production` or a deck blueprint. Do not generate image prompts, sample prompts, sample PNGs, or PPTX files until the user explicitly approves the storyline / blueprint.

Approval handoff is a user-visible gate, not a file-system checkpoint. If you save `Inputs for PPT Production`, a blueprint, or a production-pack file locally, the chat reply still must directly show the approval content. Do not only say "written to file", do not only provide file paths, and do not ask for approval without showing what is being approved.

For the storyline / blueprint approval gate, the chat reply must include this compact handoff block:

```markdown
需要你批准的是这套故事线 / 蓝图：

Core question:
<one sentence>

Working thesis:
<one paragraph>

Page list:
1. <page title> — <page role / proof object>
2. <page title> — <page role / proof object>
...

Recommended sample pages:
- <page number and why it tests the deck>

请回复“批准”或指出要改哪几页；批准前我不会创建 slide briefs、image prompts、sample PNGs 或 PPTX packaging plan。
```

Self-check before ending the turn: if the user could reasonably ask "what story am I approving?", the handoff failed. Add the block before ending the turn.

After storyline / blueprint approval, do not generate sample PNGs until the sample page brief has been shown and approved, including visual mode, proof object, visual mother concept, must-keep text, and prompt summary.

## Delivery Mode Choice

At the start, require the user to choose one of two modes. Do not treat this as a minor style preference, because it changes text density, layout, and QA.

### Mode A: Live Presentation Deck

Use when the deck will be presented by a speaker in a meeting, interview, classroom, roadshow, or live walkthrough.

- Priority: visual proof object, first-glance message, strong memory hook.
- Text density: lower to medium.
- Speaker can explain evidence, caveats, and implications verbally.
- Prompt target: large title, short subtitle, dominant proof object, few labels, clear takeaway.
- Typical must-keep text: title, 1 subtitle, 3-6 labels or numbers, 1 takeaway.
- QA focus: legibility from distance, visual hierarchy, no clutter, strong proof object.

Use this mode when the user says: "现场讲", "presentation", "roadshow", "interview presentation", "面试展示", or "讲给别人听".

### Mode B: Standalone Report Deck

Use when the deck must be read without a presenter, sent as a PDF/PPT attachment, published to GitHub, shared in a workstream, or used as a portfolio artifact.

- Priority: self-contained explanation, evidence boundary, and reasoning chain.
- Text density: medium to high, while still preserving a clear proof object.
- The page must answer "so what?" on its own.
- Prompt target: action title, explanatory subtitle, dominant proof object, evidence anchors attached to that object, one optional bottom takeaway, and low-weight source/caveat line.
- Typical must-keep text: title, 1-2 sentence subtitle, 3-8 evidence labels or numbers, 1 caveat line, 1 takeaway.
- QA focus: a reader can understand the argument without oral narration.

Use this mode when the user says: "独立阅读", "报告", "send as PDF", "GitHub showcase", "portfolio", "reader should understand without me", or "发给别人看".

If the user does not choose a mode, ask once. If they still do not choose, default to standalone report deck for public or portfolio use, and live presentation deck for meeting-only use.

## Visual Mode Selection

Choose a visual mode before writing prompts. Consulting style is not one fixed look.

### Clear Report Exhibit

Default for standalone reports, GitHub portfolio decks, dense industry research, player landscape, pricing route, demand diagnosis, and evidence-heavy pages.

- Use clean consulting report pages: large conclusion title, short explanatory subtitle, visible proof object, structured evidence bands, route maps, ladders, matrices, timelines, light rules, restrained color, and a bottom takeaway band.
- 3D is optional and usually not required.
- A page may feel PowerPoint-buildable and still be good if the proof object is clear, the hierarchy is strong, and the reading order is self-contained.

### Hero Concept Exhibit

Use selectively for opening thesis, closing judgment, live presentation, demand breakthrough, future winner, or abstract strategic claims that need a strong memory hook.

- Use a dominant proof object such as a 3D stack, gate, flywheel, bridge, funnel, or capability tower.
- Add side evidence rails and a stronger visual metaphor only when they make the claim easier to understand.
- Do not force this mode on standalone report pages where clarity and evidence density matter more.

### Evidence Architecture Exhibit

Use when the proof object is the structure itself: route map, price ladder, capability stack, matrix, decomposition, risk bridge, ecosystem map, or timeline.

- Preserve the evidence skeleton while reducing reading friction.
- Avoid turning structured evidence into generic equal-weight cards or a plain table.

## Core Principle

Manage the image model at the level of intent, evidence, boundaries, and priority.

Do not over-manage exact coordinates, chip positions, icon counts, or tiny decorative details unless the user asks for strict reproduction.

For strong image models:

- Define what the page must prove.
- Define the proof object that makes the claim credible.
- Define the visual mother concept that makes the proof object memorable.
- Define non-negotiable text, numbers, and brand constraints.
- Let the model choose composition, visual rhythm, and hierarchy within those constraints.

## Built-In Concept Image Director

This public RW skill must include the concept-image judgment needed for strong full-slide outputs. Do not assume the user has a private style skill installed.

RW's concept-image layer is responsible for:

- converting each page claim into a named proof object;
- choosing the visual mode: Clear Report Exhibit, Hero Concept Exhibit, or Evidence Architecture Exhibit;
- choosing a visual mother concept stronger than cards, tables, or wireframes;
- keeping message layers distinct;
- enforcing a high-authority consulting visual system;
- rejecting samples that look like generic editable PPT templates rather than deliberate consulting exhibits.

Before any Image2-style full-slide prompt, run a Concept Image Director pass using `references/concept-image-director.md`.
Also run the Message Hierarchy Lock before prompting. If the page has multiple conclusion zones, detached large metrics, or competing bottom/source-note bands, revise the brief before writing the prompt.

Required output inside each slide brief:

- Visual mode: Clear Report Exhibit, Hero Concept Exhibit, or Evidence Architecture Exhibit.
- Proof object type: route map, ladder, matrix, decomposition, stack, funnel, timeline, comparison object, or a clearly named alternative.
- Visual mother concept: one sentence describing the memorable exhibit.
- Evidence anchors: 3-6 must-keep text or number items, each attached to the proof object rather than floating as independent KPI blocks.
- Claim-evidence map: what each evidence anchor supports, and what important claim remains pending or unproven.
- Visual implication guardrails: which lines, arrows, gates, checks, rings, colors, or groupings must not imply unsupported proof.
- Message hierarchy: action title, subtitle if needed, proof-object labels, one optional bottom takeaway, and low-weight source note if needed.
- Omit list: what will be intentionally left out or demoted to prevent clutter.
- Rejection risks: what would make this page look like a generic PPT.

Hard stop: if a page only has topic bullets, cards, or a table but no proof object, do not write an Image2-style full-slide prompt. Improve the slide brief first.
Hard stop: if the page needs more than one action title, more than one bottom takeaway, or large detached metrics, split or compress the page before prompting.

## Workflow

### 1. Input Production Pass

Before deck blueprinting, convert the user's existing analysis into `Inputs for PPT Production`.

Use this pass when the user already has thinking, bullets, rough analysis, research notes, or a partial storyline. This is a required handoff layer between raw user thinking and slide production.

Ask the user which transformation they want, unless it is already clear:

- Expand: the user's input is too thin; add missing reasoning, implications, examples, and page-level detail without inventing unsupported facts.
- Compress: the user's input is too long; reduce it to the strongest storyline, claims, and evidence for the target page count.
- Rewrite: the user's input has useful ideas but the wording is not deck-ready; rewrite into consulting-style claims and proof-oriented bullets.
- Sharpen: the user's input is mostly good; improve the core question, storyline, page claims, senior-challenge points, and takeaways.
- Preserve: the user's input is already structured; keep wording mostly intact and only normalize fields.

Output a single `Inputs for PPT Production` block before building the deck blueprint.

Required format:

```markdown
## Inputs for PPT Production

### Context
- Audience:
- Use case:
- Delivery mode:
- Page count:
- Language:
- Theme / visual tone:

### Core Question
<one question the deck must answer>

### Working Thesis
<one-sentence answer or judgment>

### Storyline
1. <logic step>
2. <logic step>
3. <logic step>

### Page-Level Inputs

#### Page 1: <draft page title>
- Claim:
- Why it matters:
- Proof object:
- Evidence available:
- Evidence needed:
- Caveats / source notes:
- Takeaway:

#### Page 2: <draft page title>
...

### Open Questions
- <items that require user confirmation or source verification>
```

Do not hide major gaps. If a claim lacks support, mark it under `Evidence needed` or `Open Questions`.

Hard stop: show `Inputs for PPT Production` and ask the user to approve the core question, working thesis, storyline, and page-level structure before blueprinting. Do not treat this as an internal step. If the user explicitly provided a complete storyline, still summarize it and ask for confirmation before slide briefs or samples.

### 2. Normalize The Inputs

Convert the user's bullets into a message inventory:

- core question;
- draft answer or recommendation;
- supporting arguments;
- evidence, examples, and numbers;
- user assumptions;
- Codex inferences;
- open uncertainties.

If the source is expert calls, interviews, transcripts, or messy research notes, synthesize themes, tensions, evidence, and 1-3 slide-ready claims first. Do not send raw notes directly into image generation.

### 3. Build The Deck Blueprint

Create a blueprint from the approved `Inputs for PPT Production` before image generation:
- deck title;
- one-sentence storyline;
- target audience and use case;
- page count;
- delivery mode and text density target;
- page-by-page structure;
- each slide's governing message;
- each slide's proof object;
- suggested visual mother concept;
- required evidence still missing.

Every slide title should be a conclusion, not only a topic label.

Prefer:

- "Workflow ROI is replacing model price as the real buying criterion"

Avoid:

- "Pricing Overview"

### 4. Confirm The Blueprint

Ask the user to approve or edit the blueprint.

The approval request must be self-contained in the chat. Include the core question, working thesis, page list, and recommended sample pages even when the full blueprint was saved as a local Markdown file. File paths may be provided as supporting context, but they cannot replace the visible approval block.

Hard stop: do not create slide briefs, image prompts, sample prompts, sample PNGs, or PPTX packaging plans before the user approves the blueprint. If the user changes page count, color, detail level, audience, or storyline, revise the blueprint first. Do not jump straight to sample generation or batch generation.

### 5. Create Slide Briefs

For each confirmed slide, create a slide brief:

- page number;
- page claim as one complete sentence;
- evidence boundary: confirmed facts, user assumptions, Codex inference, and open uncertainties;
- claim-evidence map: what each fact/example/metric supports, and what it must not visually imply;
- proof object;
- visual mother concept;
- must-keep text and numbers, ideally 3-6 items;
- delivery mode: live presentation or standalone report;
- natural reader-facing body copy: required only for standalone report mode;
- source note or caveat line: required for standalone report mode when claims could be overread;
- text hierarchy: action title, subtitle if needed, proof-object labels, examples, one optional bottom takeaway, and low-weight source note if needed;
- avoid list: repeated claims, distracting metrics, generic cards, unnecessary process arrows;
- image prompt.

If the brief is weak, improve the brief before prompting the image model.

### 5.5 Concept Image Director Pass

Before writing Image2-style full-slide prompts, upgrade each slide brief into a concept-image direction.

For each page, decide:

- visual mode;
- strongest proof object;
- visual mother concept;
- evidence anchors;
- claim-evidence fit;
- visual implication guardrails;
- text hierarchy;
- bad-output risks;
- prompt exclusions.

Use the proof-object picker in `references/concept-image-director.md`. Use `references/message-proof-mapping.md` when the page includes players, companies, metrics, risks, gates, or validation claims.

Do not send a slide to the image model if its main visual is "cards", "comparison table", "three columns", or "process arrows" unless that structure is truly the proof object. Replace weak structures with route maps, ladders, funnels, stacks, matrices, timelines, decompositions, or decision paths where they better prove the claim.

For the first 1-2 sample pages, show the user a compact sample brief before generation:

- slide title and page role;
- visual mode;
- proof object;
- visual mother concept;
- must-keep text and numbers;
- what is already evidenced vs. what remains pending or unproven;
- how player/company/product examples support the page message;
- visual guardrails for lines, arrows, rings, gates, checks, color status, and grouping;
- what will be intentionally left out to avoid clutter.

Hard stop: do not generate sample PNGs until the user approves this sample brief or explicitly says to skip sample-brief approval.

### 6. Write Image Prompts As Content Scripts

Give the image model a content script, not a rigid wireframe.

Include:

- 16:9 full-slide image requirement;
- slide role in the storyline;
- action title and subtitle, with one highest-priority conclusion zone;
- proof object;
- visual mode;
- visual mother concept;
- evidence anchors attached to the proof object;
- one optional bottom takeaway;
- low-weight source note or caveat only if needed;
- theme color and visual tone;
- text budget;
- delivery mode and resulting text-density target;
- explicit exclusions.

For live presentation mode, avoid long paragraphs, dense tables, and small-font footnotes. If exact text fidelity is critical, reduce text per slide or split the content across more slides.

For standalone report mode, include enough explanation for the page to be read without a presenter, but do not create parallel conclusion zones. Natural body copy must either become the subtitle, a small proof-object annotation, or a low-weight source/caveat line. The bottom takeaway appears at most once.

Do not expose internal scaffolding labels in the final slide. Avoid labels such as `How to read this page`, `如何阅读这一页`, `读图说明`, `Reader note`, `Explanation block`, `Interpretation`, or `研究过程`. Replace them with natural business labels such as `证据锚点`, `战略含义`, `关键判断`, `商业启示`, `深层风险`, `约束条件`, `备注`, or no label at all.

### 7. Generate Samples First

Generate only 1-2 representative full-slide PNG samples before batch output.

Use Image2-style full-slide generation for this step. Do not create sample pages with Python, HTML, CSS, SVG, canvas, browser screenshots, or native PowerPoint layouts.

Choose samples that test:

- the cover or opening thesis page;
- one dense body page with the highest evidence load.
- if standalone report mode is chosen, include at least one sample that tests explanatory text density, not only visual beauty.

Show the samples and wait for user confirmation before generating the full deck.

### 7.5 Sample Rejection Gate

Do not treat every generated PNG as acceptable. If the sample resembles a generic editable PPT template rather than a deliberate consulting exhibit, reject it and revise the prompt before asking the user to approve.

Reject and regenerate when any of these are true:

- The page is mostly thin-line boxes, generic cards, or a simple table with small icons.
- The proof object is not visible before the supporting labels.
- The page has no governing proof object, weak hierarchy, unreadable text, or no clear takeaway.
- The page has more than two competing visual centers, such as title, large metrics, main proof object, side panels, and multiple takeaway bands all fighting for attention.
- The page tries to keep too many claims, numbers, caveats, and takeaways on one slide instead of choosing one governing message.
- Large numbers appear as a detached side KPI block and compete with the action title instead of anchoring the proof object.
- A source note or caveat line has the same visual weight as the bottom takeaway or title.
- The bottom takeaway becomes a third competing module rather than a light synthesis.
- The visual system is a one-note color theme, such as all green/teal outlines, with no high-authority hierarchy.
- The title is acceptable but the body is tiny, low-contrast, or hard to read at preview size.
- The page has many labels but no dominant route map, ladder, decomposition, matrix, timeline, or comparison object.
- It feels like a generic template rather than an Image2-style full-slide consulting exhibit.
- Company or product examples are only labels, so the reader cannot tell what market movement they evidence.
- Visual connections imply a company, metric, or observed signal proves safety, retention, trust, compliance, or another validation claim without support.
- A 2x2 or axis map creates false precision because the dimensions do not apply cleanly to all player types.
- Borders, pale fills, and connectors make every module look equally important.

When a sample fails, name the failure precisely:

- "generic card/table dashboard";
- "weak proof object";
- "over-directed wireframe";
- "text too small";
- "one-note color";
- "competing visual centers";
- "multiple conclusion zones";
- "distracting detached metric";
- "source note competing with takeaway";
- "too many claims on one page";
- "evidence misattribution";
- "label-only player evidence";
- "false precision chart";
- "linework overload";
- "editable-PPT screenshot feel".

Then revise the slide brief and prompt around a stronger proof object, not around cosmetic decoration.

### 8. Batch Generate And Package

After sample approval:

- continue with the same Image2-style full-slide generation route;
- create a deck-level `Deck System Contract` from the approved sample and user feedback before writing batch prompts;
- include the same Deck System Contract block in every slide prompt;
- choose and record the bottom-synthesis policy before batch generation;
- generate one complete PNG per slide;
- keep the style system consistent across the deck;
- vary only slide-specific title, proof object, content modules, and emphasis;
- save images with stable names such as `slide_01.png`, `slide_02.png`;
- create a contact sheet and run deck-level consistency QA before packaging;
- regenerate affected slides before packaging if page markers, action-title scale, header alignment, source notes, bottom synthesis, or material treatment drift across pages;
- optionally package accepted PNGs into an image-only PPTX;
- create a contact sheet when useful for review.

## Consulting Image Rubric

Use this as the acceptance standard:

- First-glance message: a viewer understands the page claim within a few seconds.
- Visible proof object: the main visual object proves the claim; it is not generic decoration.
- Evidence before ornament: visual polish supports the data, quote, comparison, mechanism, or operating model.
- Few but accurate words: text and numbers are limited, intentional, and prioritized.
- Mode fit: live presentation pages can rely on oral narration; standalone report pages must explain the logic on the page itself.
- Density fit: standalone report pages preserve enough readable evidence structure to be understood without narration; a clean but empty page is a failure.
- Visual mode fit: choose Clear Report Exhibit, Hero Concept Exhibit, or Evidence Architecture Exhibit based on delivery mode and page role. Do not force 3D or hero composition on standalone report pages.
- Consulting authority: clear claim, visible proof object, disciplined typography, restrained color, light separators, and enough whitespace.
- Hard visual floor: no broken layout, no text overflow or overlap, no ugly title break, no single-character orphan line, no scattered story.
- Deck consistency floor: multi-page decks must have a consistent header system, action-title scale, page-marker treatment, source-note treatment, and material style across all slides.
- Bottom-synthesis floor: standalone report decks must deliberately choose no bottom synthesis, light synthesis on every slide, or synthesis on named judgment slides only; accidental omission across the whole deck is a failure when pages need a so-what layer.
- Exhibit bar: the slide should feel closer to a route map, price ladder, decision matrix, capability stack, funnel, bridge, or decomposition exhibit than to a plain table/card page.

If the output fails, revise one target at a time: claim, proof object, evidence hierarchy, text accuracy, or visual authority.

## Message Architecture

Assign each text layer a distinct job:

- Title: sharp page angle or conclusion.
- Subtitle: why the evidence supports the page angle in one complete sentence.
- Panel headers: name evidence objects, not the same conclusion again.
- Main numbers: anchor the proof object.
- Examples: make abstract proof tangible.
- Bottom takeaway: synthesize the implication once.
- Source note or caveat: state evidence boundary in a low-weight form only when needed.

Do not let title, subtitle, panel headers, panel footers, and takeaway repeat the same action word or claim.
Do not let main numbers or source notes become standalone conclusion blocks. If a number is important enough to be large, it must sit inside or directly next to the proof object it supports.

For standalone report mode, add one more layer when needed:

- Natural body copy: 1-2 short consulting sentences that explain the implication of the proof object.
- Source note or caveat line: source type, caveat, or "company-reported / directional signal" note, written as reader-facing business copy.

Use these layers to make the slide self-contained, but collapse them into one visual hierarchy before prompting. Do not label them with meta language such as `如何阅读这一页` or research-audit labels such as `研究过程`; write them as if a consultant placed them intentionally on a client-facing page. Do not add them to live presentation mode unless the user requests more text.

## Proof Object Rules

Use image generation to amplify the proof object, not to decorate the page.

Good proof objects include:

- overlap or near-overlap: paired fingerprints, matching matrices, mirrored shelves;
- decomposition: common core plus segment-specific modules;
- contrast: two operating models, two buying missions, two price architectures;
- concentration: ranked bars, packed dots, heat maps, portfolio universe;
- sequence: customer journey, operating flow, maturity ladder;
- decision logic: 2x2, decision tree, path map, criteria matrix.

Avoid process arrows when the claim is better proven by overlap, composition, difference, concentration, or ranking.

## High-Density Evidence Pages

Use this rule for competitor comparison, pricing architecture, product portfolio, user segmentation, channel structure, cost structure, capability matrix, or other evidence-heavy pages.

The design job is not to reduce evidence. The design job is to reduce reading friction while preserving the evidence skeleton.

- Start from the evidence structure, then choose the visual form.
- Separate information volume from visual weight.
- Keep hard evidence, but remove heavy borders, repeated labels, decorative containers, and redundant explanation.
- Use callouts for anchors, gaps, anomalies, inflection points, or decisions.
- For multi-object comparison, give each object a stable recognition anchor such as color, column header, icon, bottom rule, or label system.
- Replace heavy grids with pale bands, whitespace, typography hierarchy, and very light separators.
- State units, definitions, and evidence boundaries whenever numbers can be misread.

## Default Visual System

Use a neutral high-authority consulting system unless the user supplies a palette:

- Base: white background, charcoal typography, pale blue-gray information layers.
- Anchor: project brand color, or restrained analytical blue such as `#1E5BFF`.
- Accent: a small warm marker color used only for dots, sparks, or callout emphasis.
- Mood: crisp, modern, analytical, boardroom-ready.
- Use brand color as an anchor, not a large filled surface.

Avoid:

- dark blue/slate-dominant pages unless requested;
- generic SaaS dashboard cards;
- stock photos, people, decorative gradient blobs, random icons;
- template-like two-column layouts when the claim needs a stronger visual metaphor.

## Prompt Pattern

Adapt this structure for each slide:

```text
Create one complete 16:9 consulting-style slide image, not an editable PowerPoint layout.

Slide role: <cover / thesis / evidence / comparison / decision / roadmap / closing>
Action title: <one sharp conclusion; the only highest-priority conclusion zone>
Subtitle: <one short explanatory sentence, if needed; do not repeat the title>

Main proof object:
<the visible evidence carrier that proves the claim>

Visual mother concept:
<memorable composition that makes the proof object visible>

Evidence anchors attached to the proof object:
1. <item or number and where it belongs in the proof object>
2. <item or number and where it belongs in the proof object>
3. <item or number and where it belongs in the proof object>

Bottom takeaway:
<follow the deck bottom-synthesis policy; one line only; omit only when the policy says omit or the title already carries the implication>

Low-weight source note / caveat:
<optional; small and visually quiet; never equal to the takeaway>

Style:
White base, charcoal text, pale blue-gray information layers, restrained analytical blue as anchor, small warm accent only if useful. High-end management consulting, crisp typography, generous margins, light rules, subtle shadows. Avoid stock photos, people, decorative blobs, generic dashboards, web UI look, and normal PPT template feel.

Deck System Contract:
<repeat exactly on every slide in a multi-page deck: page marker system, action-title scale and placement, subtitle placement, top-left motif, bottom-synthesis policy, source-note style, and material treatment. Do not invent different page-number badges, title sizes, header motifs, source-note treatments, or bottom banners. Page-local proof-object icons, diagrams, badges, and evidence chips may vary when the page logic requires it.>

Text rule:
Use only the provided key terms and numbers. Keep text short and legible. Prioritize action title, proof-object labels, main numbers, and the single bottom takeaway if present. Do not create detached KPI blocks or multiple conclusion bands.

Output:
One fully generated full-slide PNG. No editable objects.
```

For standalone report mode, extend the prompt with:

```text
Delivery mode: standalone report deck. The reader must understand the page without a presenter.

Standalone report notes:
- Preserve report-page density as part of the style: do not turn the page into a sparse concept poster when shortening text for accuracy.
- Keep the evidence structure visible while reducing reading friction.
- Use 1-2 natural consulting sentences only if they can be absorbed into the subtitle, proof-object annotation, or a low-weight note.
- Add a small source-note or caveat line when claims could be overread, but keep it visually quiet.
- Keep text structured and legible; do not turn the page into a paragraph document.
- Keep at most one bottom takeaway. Do not add a second conclusion band or detached KPI rail. Do not overcorrect one duplicated-bottom page by forbidding bottom synthesis across the whole deck; choose the policy explicitly.
- Do not use meta labels such as "How to read this page", "如何阅读这一页", "读图说明", "Reader note", or "Explanation block". Also avoid research-process labels such as "研究过程" on the final slide. Use normal business labels such as "证据锚点", "战略含义", "商业启示", "深层风险", "约束条件", "备注", or no label.
```

For live presentation mode, extend the prompt with:

```text
Delivery mode: live presentation deck. The speaker will explain details verbally.

Visual priority:
- Make the proof object dominant and memorable.
- Keep text sparse enough to be read quickly from a distance.
- Do not add explanatory paragraphs or footnotes unless explicitly required.
```

## Iteration Lessons

When a generated slide feels close but not right, diagnose in this order:

1. Is the proof object visible before supporting metrics?
2. Are the text layers doing different jobs?
3. Is one side visually heavier than the other?
4. Is a real metric pulling attention to the wrong story?
5. Is the theme color anchoring the page, or has it become the layout?
6. Are examples adding credibility without turning the page into a product list?

Prefer one targeted prompt change per iteration. Name the problem explicitly: repeated wording, weak proof object, heavy color, asymmetric panel weight, distracting auxiliary metric, unclear segment meaning, or bottom takeaway competing with the main visual.

## Anti-Slop Gate

Before adding or preserving any reusable rule, example, prompt, or visual lesson, check whether it contains at least one of:

- trigger condition;
- acceptance test;
- good or bad example;
- non-negotiable constraint;
- stop condition.

If a sentence only says to be more professional, beautiful, premium, polished, or consulting-like, rewrite it into concrete visible checks or leave it out.
