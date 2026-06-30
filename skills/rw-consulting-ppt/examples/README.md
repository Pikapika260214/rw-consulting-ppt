# Bilingual Example Plan

This folder keeps the original Chinese examples and defines the next English example target.

## Current Chinese Examples

- `ai-companion-toys-management-deck/`
- `ai-glasses-market-deck/`

Keep one of these as the Chinese reference example for public users who want to inspect the original output density and visual system.

## English Example

`ai-glasses-market-deck-en/` was generated from `ai-glasses-market-deck/` with Image2/img2img by changing only the slide text while preserving the visual system, information density, composition, and page rhythm.

Generated files:

```text
ai-glasses-market-deck-en/page-01-demand-funnel.png
ai-glasses-market-deck-en/page-02-route-map.png
ai-glasses-market-deck-en/page-03-price-ladder.png
ai-glasses-market-deck-en/page-04-demand-matrix.png
ai-glasses-market-deck-en/page-05-risk-bridge.png
ai-glasses-market-deck-en/page-06-capability-stack.png
ai-glasses-market-deck-en/contact_sheet.png
```

The image-only PPTX can be regenerated locally with `scripts/package_image_deck.py`. The repository intentionally ignores `*.pptx` to keep the main branch lightweight.

Editing rule: preserve the slide design. Change only the readable slide text from Chinese to English. Do not simplify the layout, change the proof object, redraw the page in a generic template style, or reduce the consulting density.

Image2 prompt skeleton:

```text
Use the provided source slide as the strict visual reference.

Create one complete 16:9 consulting slide PNG.

Task: convert this Chinese slide into an English slide.

Hard constraint:
- Keep the same composition, modules, visual hierarchy, color palette, chart geometry, icons, spacing, and information density.
- Change only the readable Chinese slide text into natural English.
- Do not redesign the slide.
- Do not turn the slide into a generic PowerPoint template.
- Do not add new logos, watermarks, UI chrome, decorative stock imagery, or unrelated content.
- Preserve the existing consulting-report feel.

Text quality:
- Use concise executive English.
- Preserve the business meaning of the original page.
- Keep title and section labels readable.
- If small body text is too dense for reliable generation, shorten it while preserving the message.

Output:
- One full-slide PNG only.
- No editable PowerPoint objects.
```

Sample gate used for this example:

1. Generate only `page-01-demand-funnel.png` in English first.
2. Proofread the visible English and visually compare it with the Chinese source for layout drift and text errors.
3. After approval, generate the remaining pages and rebuild the contact sheet plus image-only PPTX.

## Optional Fresh English Brief

If a new English-native example is preferred instead of translating the Chinese one, use this brief:

```text
Use rw-consulting-ppt to create a 6-page executive consulting deck.

Audience: founder and strategy team
Core question: should a consumer electronics company enter AI wearables this year?
Working thesis: demand is real but category adoption depends on use-case clarity, price accessibility, battery life, and distribution partnerships.
Delivery mode: standalone report deck
Page count: 6
Detail level: standard consulting density
Visual style: management-report style, white base, deep green accent, sharp charts, no generic SaaS template look
Output format: PNG first, then image-only PPTX after sample approval
```

Suggested page list:

1. Demand signal map
2. Use-case adoption funnel
3. Price and margin ladder
4. Channel readiness matrix
5. Risk bridge
6. Entry recommendation
