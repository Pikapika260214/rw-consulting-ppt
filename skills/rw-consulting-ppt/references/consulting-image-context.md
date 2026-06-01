# Consulting Image Context

Load this reference when the project is new, the user's taste is ambiguous, or the requested output needs to match a high-authority consulting-image standard.

This file is a sanitized public context pack. It preserves reusable workflow judgment, not private examples.

## Start Protocol

Before creating inputs, a blueprint, slide briefs, image prompts, or image generation, confirm alignment.

If the user has not explicitly provided delivery mode, theme color / visual tone, page or image count, detail level, visual style, and output format, ask a concise alignment question first. Do not create `Inputs for PPT Production`, a production pack, slide briefs, or Image2-style full-slide prompts until the user confirms the alignment summary or explicitly says to use defaults.

Minimum first-response alignment checklist:

- Audience / use case.
- Delivery mode: live presentation or standalone report.
- Page count / image count.
- Detail level: concise, standard, or dense.
- Theme color / visual style.
- Output format: PNG only, or PNG plus image-only PPTX.

After preference alignment is confirmed, show `Inputs for PPT Production` and a storyline / blueprint for user approval. Do not internally confirm the storyline, blueprint, slide brief, or sample page. User-facing approval is required before prompts or generated samples.

Required approval sequence:

1. Preference alignment: audience/use case, delivery mode, page count, detail level, theme/style, output format.
2. Storyline / blueprint approval: core question, working thesis, storyline, page list, and sample page choice.
3. Sample brief approval: visual mode, proof object, visual mother concept, must-keep text, and what is intentionally left out.

Only after these approvals should the agent run the Concept Image Director pass from `references/concept-image-director.md` and write Image2-style full-slide prompts.

Slide brief schema:

- Page claim: one complete sentence with a clear consulting judgment.
- Evidence boundary: confirmed facts, user assumptions, Codex inference, and open uncertainties.
- Delivery mode: live presentation or standalone report.
- Visual mode: Clear Report Exhibit, Hero Concept Exhibit, or Evidence Architecture Exhibit.
- Proof object: the visual evidence carrier that proves the claim. It must be named as a route map, ladder, matrix, decomposition, stack, funnel, timeline, comparison object, or another concrete exhibit type.
- Visual mother concept: the memorable composition that makes the proof object visible.
- Must-keep text and numbers: 3-6 non-negotiable items only, attached to the proof object rather than floating as KPI blocks.
- Text hierarchy: action title, subtitle if needed, proof-object labels, examples, one optional bottom takeaway, and low-weight source note if needed.
- Omit list: claims, caveats, metrics, or labels intentionally removed or demoted to avoid clutter.
- Avoid list: repeated claims, distracting metrics, generic cards, unnecessary process arrows, over-specified wireframes.
- Output mode: image-only full-slide PNG generated through Image2-style full-slide generation, optionally packaged into image-only PPTX.

RW Consulting PPT is the thinking, briefing, image-contract, and QA layer. It must not render slide pages with Python, Pillow, HTML, CSS, React, SVG, canvas, browser screenshots, native PowerPoint objects, or the Presentations plugin. If Image2-style full-slide generation or an equivalent full-slide image backend is unavailable, stop after briefs/prompts instead of switching to a code-rendered slide route.

If the brief is weak, improve the brief before prompting the image model.

## Concept Image Director Layer

This public RW skill must carry its own concept-image judgment. It should not depend on a private style skill or private examples.

Before Image2-style full-slide prompting:

1. Choose the proof object from the business question.
2. Choose the visual mode: Clear Report Exhibit, Hero Concept Exhibit, or Evidence Architecture Exhibit.
3. Translate the proof object into a visual mother concept.
4. Limit must-keep text to the anchors that make the proof credible.
5. Collapse action title, subtitle, evidence anchors, bottom takeaway, and source note into one hierarchy.
6. Add rejection risks: generic cards, plain table, over-directed wireframe, one-note color, detached KPI rail, multiple conclusion zones, small unreadable text, or no visible proof object.
7. Use `references/concept-image-director.md` and `references/message-hierarchy-rules.md` when the page needs high-authority consulting-image output quality.

If the page still sounds like a normal PowerPoint layout, revise the brief before prompting.

## Input Production Pass

Before deck blueprinting, convert raw user analysis into `Inputs for PPT Production`.

This pass is for users who already have some analysis. It is not research generation. It makes their thinking ready for slide production.

Available transformations:

- Expand: add missing reasoning and page detail while preserving evidence limits.
- Compress: reduce long notes into the strongest claims, evidence, and storyline.
- Rewrite: convert rough wording into consulting-style claims and proof-oriented bullets.
- Sharpen: strengthen the core question, thesis, page claims, challenges, and takeaways.
- Preserve: normalize fields without changing wording much.

The output should include:

- context;
- core question;
- working thesis;
- storyline;
- page-level inputs with claim, why it matters, proof object, evidence available, evidence needed, source notes, and takeaway;
- open questions.

Always ask for approval before deck blueprinting. Show the core question, working thesis, storyline, and page-level structure even when the user input already looks structured. Do not treat input production as an internal cleanup step.

## Delivery Mode Split

Always separate the deck's delivery mode before prompting.

### Live Presentation

Use when a speaker will explain the page live.

- Keep text sparse and visual hierarchy strong.
- Prioritize a memorable proof object over complete written explanation.
- Use title, short subtitle, labels, and takeaway.
- Treat supporting detail as speaker notes, not slide text.

### Standalone Report

Use when the deck is read without a speaker.

- Increase text density in a structured way.
- Add 1-2 natural consulting sentences only when they fit into the subtitle, proof-object annotation, or a low-weight note.
- Add source-note or caveat lines where a claim could be overread, but keep them visually quieter than the takeaway.
- Keep the page self-contained: the reader should know what the chart/diagram means, why it matters, and what conclusion to take away.
- Do not expose internal scaffolding labels such as `How to read this page`, `如何阅读这一页`, `读图说明`, `Reader note`, or `Explanation block`. Also avoid research-process labels such as `研究过程` on the final page.

For public GitHub or portfolio artifacts, default to standalone report unless the user explicitly says the deck is for live presentation.

## Visual Mode Split

Always choose a visual mode before prompting.

### Clear Report Exhibit

Default for standalone report decks, GitHub portfolio decks, dense industry research, player landscape, pricing route, demand diagnosis, and evidence-heavy pages.

- Prioritize readable report structure over dramatic metaphor.
- Use large conclusion title, short subtitle, visible proof object, structured evidence bands, light separators, restrained color, and a bottom takeaway band.
- Use route maps, ladders, matrices, funnels, risk bridges, timelines, and decompositions as first-class consulting exhibits.
- Do not reject a page only because it could be built in PowerPoint; reject it only if it is generic, proof-object weak, or unreadable.
- Reject a page if it has competing visual centers, overloaded metrics, multiple takeaway bands, or too many claims fighting on one slide.

### Hero Concept Exhibit

Use selectively for opening thesis, closing judgment, live presentation, demand breakthrough, future winner, or abstract strategic claims that need a memory hook.

- Use a dominant 3D or metaphorical proof object only when it improves the argument.
- Do not force hero composition on standalone report pages where evidence density and reading order matter more.

### Evidence Architecture Exhibit

Use when the structure itself is the proof: route map, price ladder, capability stack, matrix, decomposition, risk bridge, ecosystem map, or timeline.

- Preserve the evidence skeleton while making the page easier to scan.
- Avoid generic equal-weight cards and plain tables unless the table itself is the evidence.

## Visual Style Contract

Default to a high-authority consulting exhibit, not a marketing poster, social-media card, or SaaS dashboard.

Reusable visual choices:

- white base with pale blue-gray information bands;
- brand color as an anchor, not as the whole layout;
- Clear Report Exhibit for standalone report pages that need self-contained reading clarity;
- Hero Concept Exhibit only for selected pages that need a stronger memory hook;
- Evidence Architecture Exhibit for route maps, ladders, matrices, risk bridges, timelines, and decompositions;
- fewer borders, with tinted evidence zones to reduce wireframe feeling;
- crisp typography, generous margins, light rules, subtle shadows, and clear hierarchy;
- balanced visual weight for comparison pages;
- full-width bottom hairline when the takeaway should close the argument lightly;
- no decorative blobs, people, stock photos, generic icons, or arbitrary dashboards.

## Prompt Discipline

Write prompts as content scripts.

Constrain:

- what the page must prove;
- the proof object;
- action title, proof-object labels, and must-keep numbers attached to the proof object;
- delivery mode and text-density target;
- what must not appear;
- desired consulting tone.

Leave composition and rhythm to the image model unless the user asks for strict reproduction, but do not leave message hierarchy ambiguous. The prompt must specify one action title, one main proof object, one optional bottom takeaway, and low-weight source notes.

Before generating the first sample, present a compact sample brief and ask for approval. The brief must name the one governing message, visual mode, proof object, visual mother concept, must-keep text, and what will be removed or deferred to avoid clutter.

## Message Layer Rules

- Title: sharp page angle or conclusion.
- Subtitle: one complete sentence explaining why the evidence supports the page angle.
- Panel headers: evidence objects, not the same conclusion again.
- Examples: concrete support without becoming a product list.
- Main numbers: anchors for the proof object.
- Bottom takeaway: one synthesized implication.
- Source note or caveat: low-weight evidence boundary only.

If all layers repeat the same claim, cut wording until each layer has a distinct job.
If a large number is not attached to the proof object, shrink it, move it, or remove it before prompting.

For standalone report pages, use natural section labels such as `证据锚点`, `战略含义`, `关键判断`, `商业启示`, `深层风险`, `约束条件`, `备注`, or no label. Do not use meta labels that describe the act of reading the page, and avoid research-process labels such as `研究过程`.

## New-Project Invocation Pattern

1. Load this context pack.
2. Run the alignment gate as the first user-facing response if any required preference is missing.
3. Wait for user confirmation or explicit permission to use defaults.
4. Confirm delivery mode: live presentation or standalone report.
5. Run the input-production pass: expand, compress, rewrite, sharpen, or preserve.
6. Confirm the `Inputs for PPT Production` in all cases: core question, working thesis, storyline, and page-level structure.
7. Convert approved inputs into a deck blueprint.
8. Confirm the blueprint.
9. Create slide briefs.
10. Show and confirm the sample page brief before generation.
11. Run the Concept Image Director pass and strengthen proof objects before writing prompts.
12. Use Image2-style full-slide generation to generate 1-2 sample images. For standalone report mode, at least one sample must test explanatory text density.
13. Inspect the samples against the hard visual floor, delivery-mode fit, and sample rejection gate.
14. After approval, continue with the same Image2-style full-slide generation route to generate the full image deck and package if requested.
