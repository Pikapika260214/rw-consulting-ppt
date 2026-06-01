# Image-Only Output Contract

Use this reference when implementing or validating an RW Consulting PPT output.

## Core Contract

- Treat any approved reference image as the style master for full-page rhythm: color tone, texture, information density, typography mood, proof-object dominance, evidence-band structure, and bottom-takeaway treatment.
- Use Image2-style full-slide generation as the default route: native image generation of a complete text-heavy consulting slide from an approved slide brief, not generic image asset generation.
- If Image2 is unavailable, use only an equivalent full-slide image-generation backend that can generate complete consulting slide pages. If no such backend exists, stop after prompts.
- Generate each slide as one complete 16:9 PNG.
- For multi-page decks, generate all slides against one deck-level style contract: identical page-marker system, action-title scale and placement, subtitle relationship, bottom-synthesis policy, source-note treatment, and material treatment.
- Do not build the page by drawing boxes, charts, icons, or text with code.
- Do not crop a reference image into assets and re-layout those assets with code.
- Do not create a web page and screenshot it as a substitute for image generation.
- If text fidelity is risky, reduce text, generate a sample, or ask before changing artifact type.
- Packaging PNGs into PPTX is allowed because packaging does not alter slide design.

## Alignment Lock

Before creating production artifacts, confirm the user's output preferences.

Do not create `Inputs for PPT Production`, a deck blueprint, slide briefs, Image2-style full-slide prompts, production-pack Markdown, sample prompts, images, or a packaging plan until the user has confirmed:

- audience / use case;
- delivery mode: live presentation or standalone report;
- page count / image count;
- detail level;
- theme color / visual style;
- delivery format: PNG only or PNG plus image-only PPTX.

If any item is missing, ask for alignment first. Defaults may be used only when the user explicitly says to use defaults.

Preference alignment is not enough to start generation. After preferences are confirmed, require user approval for:

- `Inputs for PPT Production`: core question, working thesis, storyline, and page-level structure;
- deck blueprint: page list, governing message, proof object, visual mode, and sample page choice;
- sample page brief: visual mother concept, must-keep text, and what will be left out to avoid clutter.

Do not create Image2-style full-slide prompts, sample PNGs, generated images, or PPTX packaging plans before these approvals unless the user explicitly says to skip the approval gate.

## Backend Lock

RW Consulting PPT may create strategy, inputs, slide briefs, and prompts. It must not render the slide design itself.

Required route:

1. Run the Concept Image Director pass before Image2-style full-slide prompting.
2. Show and confirm the sample page brief before generation.
3. Generate 1-2 representative sample slides through Image2-style full-slide generation.
4. Reject weak samples that look like generic editable PPT templates, generic cards, plain tables without a governing proof object, overloaded pages with competing visual centers, detached large metrics, or source notes competing with takeaways.
5. Wait for user approval after acceptable samples exist.
6. Before batch generation, write a deck style contract from the approved sample and user feedback, including the bottom-synthesis policy, then repeat that contract in every slide prompt.
7. Generate the remaining slides through the same Image2-style full-slide generation route.
8. Build a contact sheet and inspect deck-level consistency before packaging.
9. Regenerate affected slides if title scale, page marker, header motif, bottom synthesis, evidence-chip style, source-note treatment, or material treatment drifts.
10. Package accepted PNGs into an image-only PPTX if requested.

If image generation is unavailable, stop after briefs/prompts. Do not substitute Python, Pillow, HTML, CSS, React, SVG, canvas, browser screenshots, native PowerPoint layouts, or the Presentations plugin.

## Allowed

- Full-slide 16:9 PNG generation.
- PPTX packaging with one image per slide.
- Contact sheets and preview images.
- Dimension checks and slide-object validation.
- Mechanical compression, renaming, and copying.

## Not Allowed

- Editable PPT text boxes.
- Native PowerPoint charts, tables, SmartArt, shapes, or grouped objects.
- HTML/CSS/React screenshots as the final slide-design route.
- Python/Pillow/canvas/SVG-drawn slide pages as the final design route.
- A clean editable-style deck that is simply rasterized afterward.
- Using code-rendered samples as a temporary stand-in for generated full-slide samples.

## Sample Gate

Generate only 1-2 representative samples first.

Use samples to test:

- visual system;
- title readability;
- dense text handling;
- proof-object strength;
- theme color balance.
- message hierarchy: one action title, one main proof object, one optional bottom takeaway, and low-weight source notes.

Wait for user approval before batch generation.

## Packaging Acceptance Test

For a packaged PPTX:

- slide count equals source PNG count;
- each slide has exactly one picture object;
- each slide has zero editable text objects;
- each picture fills the full 16:9 slide area;
- source PNGs are retained alongside the PPTX;
- a contact sheet or representative preview is available.
- deck-level contact-sheet review confirms page-marker consistency, action-title scale consistency, header alignment consistency, bottom-synthesis consistency, and source-note consistency.

## Text Density And Accuracy

- Match the approved density target; do not simplify a dense consulting exhibit into a sparse poster unless the user asks.
- Provide exact action title and 3-6 must-keep text/number items attached to the proof object.
- Inspect generated pages for title errors, fake text, wrong numbers, or illegible labels.
- If a page has major text errors, regenerate with shorter and clearer text chunks instead of rebuilding the slide with code.
