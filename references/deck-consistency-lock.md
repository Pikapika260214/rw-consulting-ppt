# Deck Consistency Lock

Use this reference for every multi-page deck after the sample page is approved and before batch generation begins.

Image-only generation can make each page individually acceptable while the deck fails as a system. This lock prevents deck-level drift: title scale changes, page markers appear on only some pages, subtitles move, source notes change weight, or bottom synthesis mutates across pages.

## Deck System Contract

After the first approved sample and before writing batch prompts, extract a short `Deck System Contract` from the approved sample and user feedback. Reuse it verbatim in every slide prompt.

Sample approval preserves the proof-object direction and visual quality bar. It does not automatically approve missing deck-system elements. If the approved sample lacks a deck-level element that the system requires, normalize the sample or regenerate it before batch generation.

The contract must decide:

- Header system: title x/y position, title width, title weight, and whether it may wrap.
- Page marker system: either no page marker on any slide, or one identical marker on every slide.
- Subtitle system: position directly below title, consistent size and weight.
- Motif system: top-left rule, accent bar, section label, or none; do not let the image model invent variants.
- Source note system: same bottom position, tiny gray weight, same source-note style.
- Bottom synthesis system: no bottom synthesis anywhere, a light bottom synthesis on every slide, or a defined subset of slides that use it.
- Material treatment: flat 2D, subtle depth, or 3D; choose once and keep it.

Do not globally lock page-local proof-object elements such as icons, diagrams, badges, evidence chips, or visual motifs unless they are part of a repeated deck-level component. Proof objects should vary when the page logic requires it; deck-system elements should not drift.

## Header And Page Marker Rules

Use one of these systems for the whole deck:

1. No page markers anywhere.
2. A small plain text marker such as `01 / 06` at the same top-left position on every page.
3. A small compact badge such as `1 / 6` at the same top-left position on every page.

Never mix marker systems. Reject the deck if some slides have markers and others do not.

If markers are used:

- specify the exact marker text for each slide;
- specify the marker style once;
- forbid alternative marker treatments such as vertical badges, green squares, underline-only labels, or large section tabs unless that exact treatment is used on every slide.

## Bottom Synthesis Rules

Bottom synthesis is a deck-level choice, not a local accident.

Choose one policy after sample approval:

1. No bottom synthesis anywhere; use only a low-weight source note.
2. Light bottom synthesis on every slide; one concise so-what line, same position and visual weight.
3. Bottom synthesis only on named judgment slides; other slides omit it, but the pattern must be documented in the Deck System Contract.

Do not delete bottom synthesis from the whole deck only because one sample had duplicate bottom conclusions. Fix the duplicate page by removing the redundant evidence callout, rewriting the takeaway so it does not repeat the action title, or demoting the source note.

Reject a page when:

- it has both an evidence callout and a bottom takeaway styled as conclusions;
- the bottom synthesis repeats the action title rather than translating evidence into implication;
- the source note looks like a second takeaway;
- the Deck System Contract says bottom synthesis is present, but the slide omits it without being in the named exception subset.

## Title Scale Rules

The action title is part of the deck system, not a per-slide design choice.

- Use the same title scale, weight, and top alignment across slides.
- Long titles may wrap, but they should wrap within the same title block width rather than shrink dramatically.
- Reject pages where the title looks materially larger or smaller than the rest of the deck.
- Reject pages where the title starts at a different horizontal position unless the deck intentionally has separate cover and body templates.

## Batch Prompt Block

Add a deck-level block to every batch prompt:

```text
Deck System Contract, repeat exactly:
- Flat 2D management-report style; no 3D, no perspective.
- Same header system on every slide: <page marker choice>, action title top-aligned at <relative position>, same large title scale and weight, subtitle directly below.
- Same source-note system: tiny gray note at bottom-left.
- Same bottom synthesis system: <none / every slide / named judgment slides only>, with one light line and no duplicate conclusion.
- Same accent system: <green vertical bar / no bar / thin rule>, identical across slides.
- Do not invent different page-number badges, title sizes, header motifs, source-note treatments, or bottom banners.
- Do not reject page-local icons or diagrams just because they differ from another slide; reject them only when they alter a repeated deck-level component.
```

## Contact-Sheet Consistency QA

After batch generation and before packaging:

1. Build a contact sheet.
2. Compare slides at thumbnail size for deck-level consistency.
3. Check:
   - page markers are present on all slides or absent on all slides;
   - page marker shape, size, and position match;
   - action titles have the same apparent scale and top alignment;
   - subtitles sit in the same relationship to the title;
   - source notes share the same bottom position and visual weight;
   - bottom synthesis policy is followed: absent everywhere, present everywhere, or present only on the named subset;
   - bottom synthesis, when present, does not repeat the action title or compete with the source note;
   - deck-level accent bars and section labels use the same visual grammar;
   - page-local proof-object icons, diagrams, badges, or motifs may differ when the page logic requires it;
   - no slide introduces a new header/footer motif, source-note treatment, bottom-synthesis treatment, or material style not present in the approved Deck System Contract.

If any deck-system check fails, regenerate or edit the affected slide before packaging. Packaging validation is not enough; a deck can pass image-only object checks and still fail visual consistency.

## Failure Labels

Use these labels in QA reports:

- `inconsistent page marker`
- `missing page marker`
- `title scale drift`
- `header alignment drift`
- `source-note drift`
- `bottom-synthesis drift`
- `overcorrected no-takeaway`
- `duplicate bottom conclusion`
- `visual motif drift`
- `material-treatment drift`
