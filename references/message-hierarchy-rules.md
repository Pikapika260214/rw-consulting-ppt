# Message Hierarchy Rules

Use this reference before writing Image2-style prompts. The goal is to prevent a slide from becoming a stack of competing conclusions.

## One Governing Message

Every slide needs one governing message. Everything else either proves it, explains it, qualifies it, or is removed.

If a page appears to need multiple governing messages, split the page or demote secondary claims.

## Layer Jobs

| Layer | Job | Failure Mode |
|---|---|---|
| Action title | States the sharp page judgment | Another claim elsewhere becomes a second title |
| Subtitle | Explains why the title is true | Repeats the title in softer words |
| Main proof object | Carries the evidence visually | Becomes decoration behind labels |
| Main numbers | Anchor the proof object | Float as detached KPI blocks |
| Panel headers | Name evidence objects | Restate the conclusion |
| Examples | Make the proof object tangible | Turn into a product list |
| Bottom takeaway | Synthesizes once | Becomes a third competing module |
| Source note / caveat | Sets evidence boundary quietly | Competes with the takeaway |

## Hard Rules

- One highest-priority conclusion zone per slide.
- One action title.
- One main proof object.
- At most one bottom takeaway.
- Source note and caveat must be visibly low-weight.
- Large numbers must be attached to the proof object.
- Evidence anchors must support the proof object, not form a separate dashboard.

## How To Collapse Prompt Fields

Bad flat prompt fields:

```text
Exact title
Subtitle
Core message
Required explanatory sentence
Source note
Bottom implication
Large evidence numbers
```

This tells the model that every layer is important.

Collapse into:

```text
Action title: the main conclusion.
Subtitle: the explanatory sentence.
Main proof object: the evidence carrier.
Evidence anchors: numbers and labels attached to the proof object.
Bottom takeaway: one line, optional.
Source note: low-weight, optional.
```

## Metric Placement

Numbers can be large only when they are part of the proof object.

Good:

- A price number on a price ladder.
- A percentage inside a funnel stage.
- A risk count inside a risk gate.
- A market share inside a landscape map.

Bad:

- Two giant numbers on the side of a page whose proof object is a gate.
- Metrics in a right rail that visually compete with the action title.
- A metric block that is true but pulls attention to a secondary story.

## Bottom Takeaway Discipline

Use a bottom takeaway when it resolves the proof object into an implication.

For a multi-page standalone report deck, decide the bottom-synthesis policy after sample approval and before batch generation:

1. No bottom synthesis anywhere.
2. One light bottom synthesis on every slide.
3. Bottom synthesis only on named judgment slides.

This is a deck-level decision. Do not remove all bottom takeaways just because one page had duplicate bottom conclusions. Fix the duplicate page by rewriting or removing the redundant evidence callout, not by banning so-what lines across the deck.

Do not use it when:

- The action title already says the implication clearly.
- The page already has a strong central conclusion ribbon.
- A source note is also needed and would create two bottom bands.

When both takeaway and source note are needed:

- Takeaway gets one clear line.
- Source note becomes small, quiet, and peripheral.
- They must not be the same size, color, or weight.
- The source note may sit below or beside the takeaway, but it must read as evidence boundary, not implication.

## Pre-Prompt Checklist

Before sending a prompt to image generation, answer:

1. What is the one governing message?
2. What is the one visual proof object?
3. Which numbers are attached to that proof object?
4. Is there only one bottom takeaway?
5. Is the source note low-weight?
6. Does this page follow the deck-level bottom-synthesis policy?
7. What will be omitted or demoted to prevent clutter?

If any answer is unclear, revise the slide brief first.
