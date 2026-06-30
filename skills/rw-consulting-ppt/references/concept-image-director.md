# Concept Image Director

Use this reference before writing Image2-style full-slide prompts. It turns a consulting slide brief into a high-authority concept image direction.

This file is public-safe. It preserves reusable visual judgment and prompt discipline, not private assets, client examples, or local project names.

## Core Job

RW Consulting PPT is not only a workflow for making PNG slides. It must make slides that feel like consulting exhibits, not screenshots of normal editable PPT pages.

Before full-slide image generation, every slide needs a concept-image direction:

- Page claim: one complete consulting judgment.
- Evidence boundary: confirmed facts, user assumptions, inference, and open uncertainties.
- Visual mode: Clear Report Exhibit, Hero Concept Exhibit, or Evidence Architecture Exhibit.
- Proof object: the visible evidence carrier that proves the claim.
- Visual mother concept: the memorable composition that makes the proof object visible.
- Must-keep text and numbers: 3-6 items only, unless the user explicitly chose a dense report page; numbers must attach to the proof object instead of floating as KPI blocks.
- Text hierarchy: action title, subtitle if needed, proof-object labels, examples, one optional bottom takeaway, and low-weight source note if needed.
- Avoid list: repeated claims, generic cards, process arrows, over-specified wireframes, decorative icons, and text that does not support the proof object.

If a slide lacks a named proof object, stop and improve the brief. Do not write an Image2-style prompt yet.
If a slide has multiple conclusion zones, detached large metrics, or competing bottom/source-note bands, stop and repair the hierarchy before prompting.
For multi-page standalone report decks, apply the deck-level bottom-synthesis policy from `references/deck-consistency-lock.md`; do not treat one duplicate-bottom failure as a reason to remove every so-what line.

## Proof Object Picker

Use the business question to choose the visual proof object. Do not default to cards or tables.

| Question Type | Strong Proof Object | Avoid |
|---|---|---|
| Price / monetization architecture | layered price ladder, route split, value staircase, pricing map plus judgment rail | vendor cards with prices scattered inside |
| Player landscape | route map, ecosystem stack, capability map, differentiated lanes, strategic battlefield map | logo grid or ordinary comparison table |
| Player control points | control-point map, layered ecosystem, value-chain ownership map | forced 2x2 when the dimensions mix unlike assets such as IP, trust, channel, and model capability |
| Demand validation | validation funnel, three-gate test, pain-frequency-willingness map, adoption friction stack | abstract arrows saying "real demand" |
| Product architecture | layered stack, control-point map, workflow runtime map, system boundary diagram | generic product-feature cards |
| Competitive wedge | entry wedge map, chain-control map, before/after operating model, maturity ladder | process arrows with equal-weight boxes |
| Failure analysis | failure-condition matrix, then-vs-now condition map, risk carryover bridge | a list of reasons with icons |
| Future winners | capability stack, winning formula map, 2x2 with capability thresholds, radar only if dimensions are clear | vague "trend" cards |
| Portfolio / assortment / category | common-core decomposition, overlap fingerprint, segment-specific modules, ranked concentration map | large tables of examples |

The proof object must appear before supporting text. A reader should know what the page is proving before reading every label.

Use a 2x2 only when both dimensions apply cleanly to every plotted item. If players are different roles in one value system, such as product makers, IP owners, model platforms, and channels, use a control-point map or layered ecosystem instead.

If a page contrasts observed activity with unproven requirements, do not make the observed mechanism the whole visual. Use a split structure such as evidence strips -> compact mechanism -> validation checklist.

## Message Layer Rules

Each text layer must do a different job:

- Title: the sharp page judgment or question answer.
- Subtitle: why the evidence supports the title in one complete sentence.
- Panel headers: name evidence objects, not the title again.
- Main numbers: anchor the proof object.
- Examples: make the proof object tangible without becoming a product list.
- Bottom takeaway: synthesize once; follow the deck-level bottom-synthesis policy; do not become a third competing module.
- Source note / caveat: stay low-weight; never compete with the takeaway.

If the title, subtitle, panel headers, and bottom takeaway all repeat the same claim, rewrite before prompting.
If a number is large, it must sit inside or directly next to the proof object. Do not place large side metrics where they read as another headline.

## Prompt Discipline

Write Image2-style full-slide prompts as content scripts, not rigid wireframes.

Constrain:

- what the page must prove;
- the proof object;
- the visual mother concept;
- action title and must-keep proof-object text;
- evidence hierarchy;
- visual tone and exclusions.

Avoid:

- exact x/y positions;
- every chip, divider, icon, or tiny label;
- telling the model to draw a table unless a table is the actual proof object;
- "make it professional" without visible checks;
- long wireframe instructions that make the image model behave like a layout renderer.

The prompt should give the image model enough freedom to compose a strong exhibit while keeping the consulting judgment and non-negotiable text intact.

## Visual Style Contract

Default to a high-authority analytical consulting system:

- Base: white background, charcoal typography, pale blue-gray information layers.
- Anchor: restrained analytical blue or user-supplied brand color, used as orientation and emphasis.
- Accent: a tiny warm marker color only for sparks, dots, or callout emphasis.
- Structure: light rules, subtle depth, generous margins, clear hierarchy.
- Density: enough evidence to prove the point, but with reduced reading friction.
- For standalone report decks, information density is part of the style master. If a sample is approved, preserve its readable Chinese text density, annotation depth, evidence-band rhythm, and source-boundary treatment unless the user asks for a lighter page.

Avoid:

- mint green or teal as the default theme unless requested;
- all-green/all-teal line art;
- dark blue/slate-dominant pages unless requested;
- generic SaaS dashboard cards;
- stock photos, people, decorative blobs, random icons;
- all-filled blocks or all-outline frames;
- template-like two-column layouts when the claim needs a stronger visual metaphor.

Color should orient the reader. It should not become the whole page.

## Visual Mode Selector

Choose one mode before prompting. Do not treat "consulting style" as always meaning a 3D hero page.

### Clear Report Exhibit

Use this as the default for standalone reports, GitHub portfolio decks, dense industry research, player landscapes, pricing routes, demand diagnosis, and evidence-heavy pages.

Visible DNA:

- Large conclusion title and short explanatory subtitle.
- Clean white base, charcoal type, restrained brand color, pale evidence bands, light rules, and generous margins.
- A visible proof object such as a route map, ladder, matrix, funnel, risk bridge, timeline, or decomposition.
- Structured evidence zones that preserve reading order without becoming equal-weight cards.
- Bottom takeaway band or light closing rule that turns evidence into the implication.
- Enough written explanation for the page to be understood without oral narration.

Accept this mode when the page is clear, self-contained, and proof-object led, even if it could technically be built in PowerPoint.

### Hero Concept Exhibit

Use this mode selectively for opening thesis, closing judgment, live-presentation pages, demand breakthrough, future winner, or abstract strategic claims that need a stronger memory hook.

Visible DNA:

- Oversized title and short accent rule.
- One dominant proof object such as a 3D stack, gate, flywheel, bridge, funnel, engine, or capability tower.
- Side evidence rails that explain the object without burying it.
- Stronger visual metaphor, depth, and material treatment when useful.

Do not force this mode on evidence-heavy standalone report pages.

### Evidence Architecture Exhibit

Use this mode when the proof object is the structure itself: route map, price ladder, capability stack, matrix, decomposition, risk bridge, ecosystem map, or timeline.

Visible DNA:

- The structure carries the argument before the labels do.
- The design reduces reading friction while preserving the evidence skeleton.
- The page avoids generic vendor cards and plain tables unless the table itself is the evidence.

### Claim-Evidence-Visual Fit

Use `message-proof-mapping.md` when a page includes company examples, player categories, metrics, risks, gates, or validation claims.

- Company facts must support only the claim they actually prove. Financing, shipments, price tests, and IP licenses show activity or experimentation; they do not prove safety, retention, compliance, or unit economics.
- Player examples should be readable evidence sentences in standalone decks, not just company names plus one-word tags.
- Visual connections are semantic claims. Lines, arrows, rings, gates, checks, and color status must not imply unsupported proof.
- If a risk or trust item is still pending validation, show it as an audit checklist, neutral gate, or separate validation layer, not as a passed check or a ring already controlled by the flywheel.

## High-Density Evidence Pages

For competitor comparison, pricing architecture, product portfolio, user segmentation, channel structure, cost structure, capability matrix, or market landscape:

- The design job is not to reduce evidence. The design job is to reduce reading friction while preserving the evidence structure.
- Start from the evidence structure, then choose the visual form.
- Separate information volume from visual weight.
- Keep hard evidence, but remove heavy borders, repeated labels, decorative containers, and redundant explanation.
- Use callouts for anchors, gaps, anomalies, inflection points, or decisions.
- Give each compared object a stable recognition anchor: color, column header, icon, bottom rule, or label system.
- Replace heavy grids with pale bands, whitespace, typography hierarchy, and very light separators.
- State units, definitions, and caveats when numbers can be misread.

Do not solve dense pages by turning them into plain tables. The point is to reduce reading friction while preserving the evidence skeleton.

## Slide Brief Gate

Before an Image2-style full-slide prompt is written, the slide brief must pass:

- Clear claim: one complete sentence, not a topic label.
- Named proof object: route map, ladder, matrix, decomposition, stack, funnel, timeline, or another evidence carrier.
- Evidence boundary: confirmed facts, user assumptions, inference, and open uncertainties are separated.
- Must-keep text: 3-6 items prioritized for text accuracy.
- Claim-evidence mapping: what is evidenced is separated from what remains pending or unproven.
- Visual guardrails: the brief states which arrows, lines, gates, rings, checks, or colors would create a false implication.
- Distinct layers: title, subtitle, panels, examples, and takeaway do not repeat the same wording.
- Avoid list: identifies what must not appear.

If any item is missing, improve the brief before prompting.

## Sample Rejection Gate

Reject and regenerate a sample when:

- It looks like a generic editable PPT template rather than a deliberate consulting exhibit.
- It is mostly thin-line boxes, generic cards, or a simple table with small icons.
- It has no governing proof object, weak hierarchy, unreadable text, or no clear takeaway.
- In standalone report mode, it is a clean but sparse concept poster that lacks enough evidence structure, interpretation labels, business implications, or source boundary to be read without a presenter.
- The proof object is not visible before the labels.
- It has more than two competing visual centers, such as title, large metric blocks, main proof object, side panels, and multiple takeaway bands all fighting for attention.
- It tries to keep too many claims, numbers, caveats, and conclusions on one page instead of choosing one governing message.
- Large numbers appear as detached KPI blocks rather than proof-object anchors.
- The source note or caveat competes with the bottom takeaway.
- The bottom takeaway is as heavy as the main visual or becomes a third conclusion zone.
- The body text is tiny, low-contrast, or hard to read in preview.
- The page is one-note color, especially all green/teal outlines.
- It has many labels but no dominant route map, ladder, decomposition, matrix, timeline, funnel, stack, or comparison object.

Name the failure precisely, then revise the governing message, proof object, or visual mother concept. Do not fix a weak sample by only changing colors or adding decoration.

## Reusable Good Patterns

### Layered Price Ladder

Use when the claim is about pricing architecture rather than who is cheaper.

- Align players or offers by comparable layers.
- Use 1-2 price anchors as large numbers.
- Add a short judgment rail to turn the ladder into implications.
- Keep the bottom takeaway as a synthesis, not a second chart.

### Route Split Map

Use when a market separates into two or more strategic routes.

- Show the routes as distinct lanes or pathways.
- Put concrete examples and price/feature anchors on the route.
- Add the decision tension in the center or bottom.
- Do not use a flat competitor table unless the table itself is the evidence.

### Decision Matrix Plus Path

Use when the page is for choosing a go-to-market, product, pricing, or investment path.

- Frame 2-4 decision questions.
- Show how answers lead to paths.
- End with a practical implication.
- Avoid making every option visually equal when the recommendation is directional.

### Decomposition / Common-Core Map

Use when the claim is about replication versus local adaptation, shared capability versus segment-specific modules, or portfolio structure.

- Make the common core visible.
- Attach segment-specific modules around it.
- Use representative examples and metrics to make the structure tangible.
- Keep auxiliary metrics near their proof object.

### Demand Validation Funnel

Use when the page asks whether a product is real demand or hype.

- Show the gates: pain frequency, alternative inadequacy, willingness to pay, daily-use feasibility, trust/privacy acceptance, ecosystem closure.
- Put supporting evidence or open risks under each gate.
- Make the failing or unproven gates visually clear.
- Avoid abstract "real demand" icons without market evidence.

## Failure Patterns

- Over-directed wireframe: the model follows boxes mechanically and loses visual intelligence.
- Generic card dashboard: the page looks polished but the proof object is not visible.
- Editable-style screenshot: the result is a PNG, but it looks like a screenshot of normal PowerPoint or HTML.
- Repeated conclusion: title, subtitle, headers, and footer all say the same thing.
- Distracting true metric: a real number pulls attention to a secondary story.
- Detached metric rail: large numbers are true but float away from the proof object and become a second headline.
- Source-note competition: a caveat/source note is styled like a second takeaway.
- Multiple conclusion zones: title, central ribbon, KPI rail, and bottom banner all compete.
- All-filled or all-outline layout: too much fill feels heavy; too many frames feel skeletal.
- Unverified labels: terms like top-selling, benchmark, market leader, or proven demand appear without source support.

## Prompt Skeleton

```text
Create one complete 16:9 consulting concept-slide image, not an editable PowerPoint layout and not a code-rendered wireframe.

Slide role: <cover / thesis / evidence / comparison / decision / roadmap / closing>
Visual mode: <Clear Report Exhibit / Hero Concept Exhibit / Evidence Architecture Exhibit>
Density target: <live-presentation sparse / standalone report standard / standalone report dense; preserve approved sample density if available>
Action title: <one sharp conclusion; the only highest-priority conclusion zone>
Subtitle: <one short explanatory sentence if needed; do not repeat the title>

Main proof object:
<named evidence carrier: route map / ladder / matrix / decomposition / stack / funnel / timeline / comparison object>

Visual mother concept:
<memorable composition that makes the proof object visible>

Evidence anchors attached to the proof object:
1. <must-keep text or number and where it belongs>
2. <must-keep text or number and where it belongs>
3. <must-keep text or number and where it belongs>

Text hierarchy:
- Action title: <exact>
- Subtitle: <exact or omit>
- Proof-object labels: <short labels>
- Bottom takeaway: <exact one line or omit>
- Source note / caveat: <low-weight line or omit>

Omit / demote:
<claims, caveats, metrics, or labels intentionally left out to preserve hierarchy>

Style:
High-authority consulting exhibit. White base, charcoal type, pale blue-gray information layers, restrained analytical blue or user-provided brand color as anchor, tiny warm accent only if useful. If the mode is Clear Report Exhibit, prioritize readable report structure, proof-object clarity, evidence bands, and a bottom takeaway. If the mode is Hero Concept Exhibit, use a stronger central proof object and memory hook. If the mode is Evidence Architecture Exhibit, let the route map, ladder, matrix, bridge, stack, or decomposition carry the argument. Light rules, subtle depth, generous margins, clear hierarchy.

Avoid:
Generic card dashboard, plain comparison table, thin-line wireframe, all-green/teal theme, detached KPI rail, multiple conclusion zones, source note competing with takeaway, stock photos, people, decorative blobs, random icons, fake English, watermark, web UI look, normal PPT template feel.

Output:
One fully generated full-slide PNG. Keep key Chinese text legible. Prioritize action title, proof-object labels, main numbers attached to the proof object, and the single bottom takeaway if present.
```
