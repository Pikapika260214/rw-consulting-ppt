# Example Lessons

Use this reference when the user provides a good or bad slide example, asks to remember a lesson, or wants the deck to inherit a known visual standard.

This public version stores desensitized reusable patterns only.

## Storage Convention

If example assets are included in a private local version, keep them out of the public repo unless they are synthetic, licensed, or explicitly approved for release.

For text-only public examples, use:

- `[Company A]`
- `[Company B]`
- `[Retailer A]`
- `[AI vendor]`
- `[Product line]`
- `[Region X]`

## Good Example Template

```markdown
### <date> | <neutral project label> | <slide name>

- Type: good example
- Context: what audience and slide role
- Page claim: one sentence
- Proof object: what proves the claim visually
- Why it works:
  - <message clarity>
  - <evidence hierarchy>
  - <visual treatment>
  - <text discipline>
- Reusable pattern: what future slides can copy
- Do not overgeneralize: what is case-specific
```

## Bad Example Template

```markdown
### <date> | <neutral project label> | <slide name>

- Type: bad example
- Observed issue: what feels wrong at first glance
- Root cause: message, evidence carrier, hierarchy, visual balance, color, text, or routing
- Fix that worked / likely fix: keep the explanatory sentence, but rewrite the visible label as `证据锚点`, `战略含义`, `关键判断`, `商业启示`, `深层风险`, `约束条件`, `备注`, or remove the label entirely.
- Reusable caution: what future slides should avoid
```

## Desensitized Good Patterns

### Clear Report Exhibit / Dense Standalone Report Deck

- Type: good pattern
- Context: standalone industry-research deck or GitHub portfolio artifact where the reader must understand the argument without a presenter.
- Page claim: a market judgment is credible when each page has a conclusion title, a visible proof object, and enough structured explanation to stand alone.
- Proof object: route maps, ladders, matrices, funnels, risk bridges, timelines, and decompositions used as evidence carriers rather than decoration.
- Why it works:
  - The page is readable at preview size because title, subtitle, proof object, and bottom takeaway have clear jobs.
  - The deck can handle more text than a live-presentation deck without turning into paragraphs.
  - The visual system feels like a management report: white base, restrained theme color, light evidence bands, and disciplined separators.
  - The proof object carries the argument, so the page does not need a 3D hero object to feel consulting-grade.
- Reusable pattern: default to Clear Report Exhibit for standalone reports, dense industry research, player landscape pages, pricing routes, demand diagnosis, and GitHub showcase decks.
- Do not overgeneralize: when the user asks for live presentation impact, opening thesis drama, or a strong memory hook, upgrade selected pages to Hero Concept Exhibit.

### Pricing Architecture Page

- Type: good pattern
- Context: strategy deck comparing multiple providers' public pricing systems.
- Page claim: the market is not only competing on low prices; it is forming a layered price architecture from entry tier to production tier to enterprise assurance.
- Proof object: a price ladder split by model role, with a short judgment rail that turns the ladder into strategic implications.
- Why it works:
  - Competitors are aligned by comparable layers, so gaps are visible.
  - The strongest numbers are used as anchors, not scattered everywhere.
  - The judgment rail makes the implication explicit without overcrowding the ladder.
- Reusable pattern: use a layered ladder plus a judgment rail when the message is about architecture, not just who is cheaper.
- Do not overgeneralize: exact prices, vendor names, and model labels must be re-verified for each project.

### Assortment / Portfolio Decomposition Page

- Type: good pattern
- Context: management deck comparing two operating models across regions or customer segments.
- Page claim: `[Company A]` shows stable replication, while `[Company B]` shows local adaptation around a common core.
- Proof object: common-core module plus segment-specific modules, with representative examples.
- Why it works:
  - The visual proof object appears before supporting metrics.
  - Representative examples make abstract strategy tangible.
  - Auxiliary metrics stay near their proof object instead of becoming the headline.
- Reusable pattern: use decomposition and overlap when the claim is about replication versus adaptation.
- Do not overgeneralize: only label examples as top-selling, benchmark, or market-leading when sources support that label.

### Decision Path Page

- Type: good pattern
- Context: discussion deck for choosing a go-to-market, pricing, or product route.
- Page claim: the right path depends on target customer, buying reason, and proof strength.
- Proof object: a three-question decision matrix plus a bottom path from entry option to scale option to custom option.
- Why it works:
  - The page turns vague discussion into a decision structure.
  - The matrix frames judgment; the path shows action.
  - The bottom takeaway synthesizes without becoming a separate heavy module.
- Reusable pattern: use a decision matrix plus path map when the user needs a meeting-ready discussion page.
- Do not overgeneralize: the specific criteria must come from the project's business question.

### Management Report Style Master Rhythm

- Type: good pattern
- Context: executive standalone report slide where the reader must understand the page without a presenter.
- Page claim: a high-stakes risk or strategy judgment is clearest when the page has one action title, one central proof object, one supporting evidence band, and one final takeaway.
- Proof object: a structured gate, route map, ladder, capability stack, or decision path that carries the argument before the viewer reads every label.
- Why it works:
  - The action title owns the main conclusion; no second title-like claim competes elsewhere.
  - The central proof object is the first visual object after the title.
  - Large numbers sit inside an evidence band or directly on the proof object, not in a detached KPI rail.
  - The source note is small and quiet; the bottom takeaway, if used, is the only final synthesis.
  - The theme color gives orientation and status, not an all-over color wash.
- Reusable pattern: use `Action title -> subtitle -> dominant proof object -> evidence band -> one takeaway` for management-report samples that need authority and density.
- Do not overgeneralize: some live-presentation or hero pages may omit the evidence band or bottom takeaway.

## Failure Patterns

- Over-directed wireframe: the model follows boxes mechanically and loses visual intelligence.
- Generic card dashboard: the page looks polished but the proof object is not visible.
- Wrong route: creating editable-style cards/tables and rasterizing them afterward.
- Wrong delivery mode: a standalone report deck uses presentation-style sparse text, so the page looks good but cannot be understood without a speaker.
- Repeated conclusion: title, subtitle, headers, and footer all say the same thing.
- Distracting true metric: a real number pulls attention toward a secondary story.
- Detached large metric: a real number appears in a side KPI block and becomes a second headline.
- Multiple conclusion zones: action title, central ribbon, KPI rail, and bottom banner all compete.
- Source note competing with takeaway: caveat or source text is styled with the same weight as the final implication.
- All-filled or all-outline layout: too much fill feels heavy; too many frames feel skeletal.
- Case-specific rule leakage: wording from one successful page gets reused where it does not belong.
- Unverified labels: terms like top-selling, benchmark, or market leader appear without source support.

### Plain Image2 Sample That Still Looks Like Editable PPT

- Type: bad pattern
- Context: an image-only consulting deck sample generated after raw research notes were converted into slide prompts.
- Observed issue: the sample is technically a PNG, but the page looks like a normal editable PPT or HTML wireframe: thin green outlines, small card/table modules, generic icons, and no dominant proof object.
- Root cause: the prompt preserved the blueprint structure too literally and did not force a visual mother concept. The image model was asked to render a layout instead of to create a consulting exhibit that proves the claim.
- Fix that worked / likely fix: keep the explanatory sentence, but rewrite the visible label as `证据锚点`, `战略含义`, `关键判断`, `商业启示`, `深层风险`, `约束条件`, `备注`, or remove the label entirely.
  - Replace generic cards/tables with a named proof object such as route map, ladder, decomposition, decision matrix, capability stack, or timeline.
  - Limit must-keep text to the few terms and numbers that anchor the proof object.
  - Use color as an orientation system, not as all-green/all-teal line art.
  - Regenerate the sample before batch output; do not ask the user to approve a weak sample.
- Reusable caution: image-only output is not enough. A PNG can still fail if it looks like a screenshot of an ordinary editable slide.

### Overloaded Trust-Gate Sample

- Type: bad pattern
- Context: a sample page generated before the storyline, blueprint, and sample page brief were user-approved.
- Observed issue: the page has a long heavy title, large side metrics, a central multi-gate proof object, side panels, a middle takeaway, and a bottom banner all competing for attention.
- Root cause: the workflow skipped user-facing storyline / blueprint approval and allowed the sample prompt to preserve too many claims, evidence anchors, caveats, and conclusions on one page.
- Fix that worked / likely fix:
  - First confirm the governing message and decide what the page must prove.
  - Pick one proof object and demote large side metrics into small evidence chips or move them to another page.
  - Keep one bottom takeaway, not multiple competing conclusions.
  - Show and approve the sample page brief before generation.
- Reusable caution: a page can have a valid proof object and still fail if it has too many visual centers. Sample generation must be blocked until storyline, blueprint, and sample brief are approved.

### Multiple Conclusion Zones In A Trust-Gate Slide

- Type: bad pattern
- Context: management-report risk page with a valid six-gate proof object and real evidence numbers.
- Observed issue: the action title is already the main conclusion, but large metrics on the side read like a second conclusion; the subtitle restates the claim; the bottom area includes both a takeaway and a source/caveat line with too much visual weight.
- Root cause:
  - The prompt treated action title, core message, explanatory sentence, evidence numbers, source note, and bottom implication as parallel visible layers.
  - The evidence numbers were marked as large/readable without saying they must attach to the proof object.
  - The source note was not explicitly demoted below the takeaway.
- Fix that worked / likely fix:
  - Collapse the prompt into one hierarchy: action title, subtitle, central proof object, evidence anchors attached to the object, one optional takeaway, low-weight source note.
  - Move large numbers into the evidence band or gate labels, not a detached KPI rail.
  - Use one bottom takeaway only. If source note is needed, make it small and quiet.
  - Write an omit/demote list before prompting.
- Reusable caution: real evidence can still damage the slide if it is placed where it competes with the governing message.

### AI Glasses Sample Failure

- Type: bad pattern
- Context: a strategy deck testing whether AI glasses are real demand or another hardware bubble.
- Observed issue: early samples were clean but underpowered. One page used a central gate and small side cards; another used a table-like value-chain comparison. Both were legible but lacked the authority and visual force of prior approved examples.
- Root cause:
  - The slide brief did not choose a strong enough proof object for the industry question.
  - The prompt over-specified boxes and labels instead of asking for a memorable evidence carrier.
  - The style drifted into a one-note green analytical theme rather than the established high-authority blue/black consulting system.
  - The content was too generic: "real demand" vs "not phone replacement" was asserted more than proven through player routes, price bands, consumer use cases, and Google Glass failure conditions.
- Fix that worked / likely fix: keep the explanatory sentence, but rewrite the visible label as `证据锚点`, `战略含义`, `关键判断`, `商业启示`, `深层风险`, `约束条件`, `备注`, or remove the label entirely.
  - Page 1 should use a "demand validation funnel" or "three-market-test gate" showing buyer pain, daily-wear feasibility, and ecosystem closure.
  - Page 2 should use a "player route map" across ecosystem entry, phone accessory, display assistant, camera glasses, and XR platform, with price/route anchors.
  - Keep the public-report detail, but make the proof object visually dominant before explanatory labels.
- Reusable caution: for industry-research topics, do not let the opening pages become abstract logic diagrams. The proof object must carry market evidence.

### Report Deck Text-Density Caution

- Type: bad pattern
- Context: a public portfolio or GitHub showcase deck meant to be read without the creator presenting it.
- Observed issue: opening thesis and architecture pages look visually clean, but the reader cannot fully recover the argument from the slide alone.
- Root cause: the workflow used live-presentation text density for a standalone report artifact.
- Fix that worked / likely fix: keep the explanatory sentence, but rewrite the visible label as `证据锚点`, `战略含义`, `关键判断`, `商业启示`, `深层风险`, `约束条件`, `备注`, or remove the label entirely.
- Reusable caution: for report decks, do not rely on oral narration. Slides like timeline migration, architecture stack, and strategy framework pages need more written explanation than live presentation samples.

### Meta-Label Leakage

- Type: bad pattern
- Context: a standalone report page where internal prompt scaffolding leaked into the final design.
- Observed issue: labels such as `如何阅读这一页`, `读图说明`, or `Explanation block` appear on the slide.
- Root cause: the prompt asked for a reader explanation but did not separate internal design instructions from final page copy.
- Fix that worked / likely fix: keep the explanatory sentence, but rewrite the visible label as `证据锚点`, `战略含义`, `关键判断`, `商业启示`, `深层风险`, `约束条件`, `备注`, or remove the label entirely.
- Reusable caution: client-facing slides should never reveal the production scaffold. They should read like intentional business writing.

### Research-Process Label Leakage

- Type: bad pattern
- Context: a standalone report page where research audit language appears as a visible client-facing label.
- Observed issue: `璇佹嵁杈圭晫` appears on the slide. The meaning is useful internally, but the wording feels like process documentation rather than consulting writing.
- Root cause: the skill preserved the internal evidence-boundary concept as final visible copy.
- Fix that worked / likely fix: keep the explanatory sentence, but rewrite the visible label as `证据锚点`, `战略含义`, `关键判断`, `商业启示`, `深层风险`, `约束条件`, `备注`, or remove the label entirely.
- Reusable caution: evidence discipline should be visible through precise wording, not through internal research-process labels.
