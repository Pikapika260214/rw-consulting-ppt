# English Publication Style Guide

This repository should read like an opinionated Codex skill package for turning rough business material into consulting-grade slide outputs. It should not read like a literal translation of a private workflow note.

## Positioning

Lead with a narrow, credible promise:

- `rw-consulting-ppt` is the image-first consulting slide workflow. It owns storyline, proof-object thinking, sample approval, full-slide PNG quality, and image-only PPTX packaging.
- `ppt-to-editable` is the post-confirmation conversion layer. It owns OCR, clean-background or reconstruction routing, editable text and simple native-object recovery, source crops, and editability reporting.

Never imply that the package creates a fully editable, all-native PowerPoint deck from rough notes in one step.

## Voice

Use clear product documentation prose:

- direct and concrete;
- honest about tradeoffs;
- workflow-oriented rather than hype-oriented;
- precise about inputs, outputs, and stop conditions.

Avoid casual China-local community wording, vague "AI PPT magic" claims, and translated internal process labels.

## Terminology

| Concept | Preferred English | Definition | Avoid |
| --- | --- | --- | --- |
| proof object | `proof object` | The main visual exhibit that carries the argument on a slide. | `evidence object` unless the whole repo changes |
| storyline | `storyline` | The logical sequence of claims across the deck. | `story line`, vague `narrative` |
| alignment gate | `alignment gate` | User confirmation of audience, mode, page count, density, style, output format, and evidence boundary. | `preference alignment` without explaining it is a gate |
| image-only deck | `image-only deck`; `image-only PPTX` | One full-slide image per slide; zero editable text objects. | `picture PPT`, `editable deck` |
| explicitly accepted hybrid fallback | `hybrid fallback` or `hybrid baseline` | Full-slide background image plus editable PowerPoint text boxes, used only when accepted as a fallback or interim baseline. | `editable PPT` without limits |
| source-image reconstruction | `source-image reconstruction` | Rebuild text and simple shapes while preserving complex visuals as tight source crops. | `full-native conversion`, `magic image-to-PPT` |
| source reconstruction plan | `source reconstruction plan` | A hard gate describing native text, native shapes, source crops, omissions, and limits. | `reconstruction notes` if it gates delivery |
| core visual concept | `core visual concept` | The memorable composition that makes the proof object visible. | literal calques for the core idea |
| editability report | `editability report`; `editability_report.json` | The verification artifact showing editable text, native shapes/tables, source crops, and limitations. | unsupported claims of full editability |

## Public QA Checklist

Before publication:

- The root README explains the two-skill split in the first screen.
- Quick-start prompts are English-native and runnable by an overseas Codex user.
- No public-facing Markdown, YAML, or Python help text contains unintended Chinese, mojibake, single-channel China-only calls to action, or local absolute paths.
- Chinese slide examples are either replaced with English-visible examples or explicitly labeled as CJK demo assets.
- `rw-consulting-ppt` remains image-first and approval-gated.
- `ppt-to-editable` remains a conversion layer and does not promise full-native reconstruction.
- Any CJK-specific OCR, font, or line-wrap guidance is labeled as CJK-specific.
