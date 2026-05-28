# Message Proof Mapping

Use this reference before slide briefs, sample briefs, and Image2-style prompts when a page uses company examples, market facts, metrics, risks, or player categories to support a consulting judgment.

The job is to keep the slide honest: the visual should show what the evidence proves, and should not imply proof that the evidence does not support.

## Core Rule

Before designing the page, separate three layers:

1. **Message**: the one judgment the page wants the reader to take away.
2. **Proof**: the facts, examples, numbers, or observations that support the message.
3. **Visual semantics**: what each line, arrow, grouping, color, and emphasis implies.

If these three layers do not match, revise the slide brief before writing an image prompt.

## Claim-Evidence Map

For every page, write a compact map:

```markdown
Page message:
<one sentence>

Evidence supports:
- <fact/example> -> proves or indicates <specific part of the message>

Evidence does not prove:
- <fact/example> does not prove <unsupported conclusion>

Visual implication guardrails:
- Do not connect <evidence> to <unsupported gate / outcome>.
- Do not use checkmarks, passed gates, or green status for unverified claims.
```

The `Evidence does not prove` layer is for briefing discipline. It does not need to appear on the final slide unless the audience needs the caveat.

## Player Evidence Must Be Readable

Company and product examples should not appear as bare labels if the audience cannot infer the point.

Weak:

```text
Haivivi: financing / shipments / IP
FoloToy: hardware + subscription
Ropet: adult companion
```

Stronger:

```text
Haivivi
Series A financing, BubblePal shipment claims, and IP licenses show early productization and role/content experimentation.

FoloToy
The hardware price plus monthly fee shows an AI core / plush toy subscription model being tested.

Ropet / Fuzozo
Adult and all-age emotional companion positioning shows route diversification toward lighter regulatory pressure.
```

Use the stronger pattern in slide text when the deck is standalone or management-facing. Compress only when the page has already taught the reader what the labels mean.

## Visual Semantics Guardrails

Visual connections are claims.

- A line means "supports", "feeds", or "belongs to"; do not draw it casually.
- A gate means an item must pass before the next stage; do not show it as passed unless evidence proves it.
- A checkmark means verified; use locks, neutral dots, or audit icons for pending validation.
- A flywheel means a reinforcing mechanism; do not use it when the message is mainly "unproven risk".
- A 2x2 means dimensions can compare all included players; do not use it when player types are different roles in a value system.
- A ring around a mechanism can imply the mechanism already contains or controls the ring items. Use a separate gate/checklist when those items are independent validation requirements.

## Proven Vs. Pending

When a page contrasts observed market activity with future requirements, split the visual:

- **Observed / proven signals**: financing, shipments, price tests, IP partnerships, product routes, channel launches, public user behavior.
- **Pending validation**: safety, compliance, retention, repeat purchase, subscription renewal, unit economics, channel complaints, recall response.

Do not let observed signals visually prove pending validation. This was the failure mode in many attractive but misleading sample pages.

## Proof Object Selection

Choose the proof object from the evidence relationship, not from what would look impressive.

| Message type | Better proof object | Avoid |
|---|---|---|
| Players compete around different control points | control-point map, layered ecosystem, value-chain ownership map | forced 2x2 with mixed dimensions |
| Speed is observed but trust remains pending | observed-signal list -> compact mechanism -> validation checklist | dominant flywheel that makes speed look like the whole conclusion |
| Company facts illustrate route differences | evidence strips with concise interpretation | company-logo grid or one-word tags |
| Metrics prove stages of a funnel | funnel or gate sequence with metrics inside stages | detached KPI blocks |
| Risks must be independently verified | audit checklist, risk gate, validation ladder | checkmarks or green pass states |

## Sample Brief Additions

Before sample generation, the sample brief should include:

- page message;
- what is already evidenced;
- what is pending or not directly proven;
- how each company/product/metric supports the message;
- the main proof object and why it matches the evidence relationship;
- visual guardrails for lines, arrows, gates, checks, rings, and color status.

If the sample brief cannot answer these points, do not generate the sample yet.
