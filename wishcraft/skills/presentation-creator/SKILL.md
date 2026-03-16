---
name: presentation-creator
description: "Use this skill when the user wants to create a PowerPoint presentation (.pptx). This includes: creating slide decks, pitch decks, thesis defenses, lecture slides, or any presentation from scratch. User can provide topic verbally, supply a content file (text/PDF), and/or provide images to embed. Generates professional slides with colors, shapes, charts, tables, cards, stat boxes, embedded images, and styled layouts using Gemini AI + PptxGenJS. Saves to Desktop and opens automatically."
triggers: presentation, slides, powerpoint, pptx, deck, pitch deck, slideshow, lecture slides, make slides, create presentation, thesis defense, slide deck
platform: all
---

# Presentation Creator Skill

AI-powered PPTX presentation generator. Gemini designs structured slide content and layout, PptxGenJS builds the real PowerPoint file. Users can provide text content from files and images to embed.

## Quick Reference

| Task | Guide |
|------|-------|
| Create presentation from topic | Use `create_presentation` tool (see below) |
| Create from content file | Pass `content_file` parameter with text/PDF path |
| Embed user images | Pass `images_folder` or `image_files` parameter |
| PptxGenJS element reference | Read [pptxgenjs-reference.md](pptxgenjs-reference.md) |
| Browse themes | See [themes/](themes/) directory — 10 pre-built color themes |

---

## How It Works

1. User describes what they want: topic, audience, number of slides, style
2. Optionally provides a content file (text/PDF) and/or images folder
3. Gemini AI reads the content, designs a full slide layout incorporating the images
4. PptxGenJS builds the `.pptx` file with shapes, text, bullets, charts, tables, images
5. File saves to `~/Desktop` and opens automatically

## Tool

Use `create_presentation` with these parameters:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Detailed instructions: topic, audience, slide count, specific content |
| `content_file` | string | No | Path to text/PDF file to use as content source |
| `images_folder` | string | No | Path to folder of images to embed in slides |
| `image_files` | array | No | Array of specific image file paths to embed |
| `filename` | string | No | Output filename (no extension). Default: "Presentation" |
| `style` | string | No | "professional", "creative", "minimal", "academic". Default: "professional" |

## Examples

**Basic (voice only):**
```
create_presentation({
  prompt: "Create a 5-slide presentation about artificial intelligence",
  filename: "AI_Presentation"
})
```

**From a text file:**
```
create_presentation({
  prompt: "Create a thesis defense presentation from this content, 15 slides",
  content_file: "~/Desktop/thesis_content.txt",
  filename: "Thesis_Defense",
  style: "academic"
})
```

**With images folder:**
```
create_presentation({
  prompt: "Create a research presentation with these figures embedded",
  content_file: "~/Desktop/paper.txt",
  images_folder: "~/Desktop/figures",
  filename: "Research_Presentation"
})
```

**Specific image files:**
```
create_presentation({
  prompt: "Create a product pitch deck. Include the logo and screenshots.",
  image_files: ["~/Desktop/logo.png", "~/Desktop/app_screenshot.png", "~/Desktop/dashboard.png"],
  filename: "Product_Pitch",
  style: "creative"
})
```

---

## Content Input Modes

| Mode | How |
|------|-----|
| Voice only | User describes the topic verbally |
| Text file | User provides .txt or .md file path |
| PDF file | User provides .pdf — AI extracts text from all pages |
| Images folder | All images in a folder get embedded into relevant slides |
| Specific images | Array of image paths for targeted embedding |
| Combined | Content file + images + voice instructions together |

---

## Design Ideas

**Don't create boring slides.** Plain bullets on a white background won't impress anyone. Consider ideas from this list for each slide.

### Before Starting

- **Pick a bold, content-informed color palette**: The palette should feel designed for THIS topic. If swapping your colors into a completely different presentation would still "work," you haven't made specific enough choices.
- **Dominance over equality**: One color should dominate (60-70% visual weight), with 1-2 supporting tones and one sharp accent. Never give all colors equal weight.
- **Dark/light sandwich**: Dark backgrounds for title + conclusion slides, light for content slides. This creates a professional "sandwich" structure.
- **Commit to a visual motif**: Pick ONE distinctive element and repeat it — accent bars on cards, colored stat boxes, section header bars. Carry it across every slide.

### Color Palettes

Choose colors that match your topic — don't default to generic blue. All colors are 6-char hex WITHOUT `#` prefix.

Each theme has a full specification in the [themes/](themes/) directory with detailed color roles and font pairings.

| Theme | Primary | Secondary | Accent | Best For |
|-------|---------|-----------|--------|----------|
| **Midnight Executive** | `1E2761` (navy) | `CADCFC` (ice blue) | `F9A825` (gold) | Business, corporate, finance |
| **Forest & Moss** | `2C5F2D` (forest) | `97BC62` (moss) | `F5F5F5` (cream) | Nature, sustainability, health |
| **Coral Energy** | `F96167` (coral) | `F9E795` (gold) | `2F3C7E` (navy) | Marketing, creative, youth |
| **Ocean Gradient** | `065A82` (deep blue) | `1C7293` (teal) | `21295C` (midnight) | Technology, science, data |
| **Charcoal Minimal** | `36454F` (charcoal) | `F2F2F2` (off-white) | `212121` (black) | Minimal, elegant, luxury |
| **Teal Trust** | `028090` (teal) | `00A896` (seafoam) | `02C39A` (mint) | Healthcare, consulting, trust |
| **Berry & Cream** | `6D2E46` (berry) | `A26769` (dusty rose) | `ECE2D0` (cream) | Fashion, beauty, lifestyle |
| **Cherry Bold** | `990011` (cherry) | `FCF6F5` (off-white) | `2F3C7E` (navy) | Bold statements, alerts, startups |
| **Golden Hour** | `F4A900` (amber) | `C1666B` (terracotta) | `4A403A` (chocolate) | Food, hospitality, autumn themes |
| **Cosmic Night** | `2B1E3E` (purple) | `4A4E8F` (cosmic blue) | `A490C2` (lavender) | Entertainment, gaming, creative |

You can also create custom themes on-the-fly based on the topic if none of these fit.

### Typography

**Choose an interesting font pairing** — don't default to plain Arial for everything.

| Header Font | Body Font | Feel |
|-------------|-----------|------|
| Georgia | Calibri | Classic professional |
| Arial Black | Arial | Bold modern |
| Calibri | Calibri Light | Clean corporate |
| Cambria | Calibri | Elegant formal |
| Trebuchet MS | Calibri | Friendly modern |

| Element | Size | Style |
|---------|------|-------|
| Slide title | 36-44pt | Bold |
| Section header bar | 16-20pt | Bold, white on color |
| Body text | 11-14pt | Regular |
| Captions / footnotes | 9-10pt | Italic, muted color |
| Stat box number | 28-36pt | Bold, accent color |
| Stat box label | 10-12pt | Regular |
| Card title | 14-16pt | Bold |
| Card body | 11-12pt | Regular |

### Spacing

- Slide dimensions: 10" wide x 5.625" tall (LAYOUT_16x9)
- All x/y/w/h coordinates in INCHES
- 0.5" minimum margins from slide edges
- 0.3-0.5" between content blocks
- Footer auto-added on slides 2+, so keep content above y=5.3"
- Leave breathing room — don't fill every inch

---

## Slide Element Types

Every slide is built from these building blocks. Use a MIX — not just text and bullets.

### 1. `text`
Plain text block with full formatting control.
```json
{ "type": "text", "text": "Title Here", "x": 0.5, "y": 0.5, "w": 9, "h": 1, "fontSize": 44, "fontFace": "Georgia", "color": "FFFFFF", "bold": true, "italic": false, "align": "center", "valign": "middle" }
```

### 2. `bullets`
Bulleted list with proper PowerPoint formatting.
```json
{ "type": "bullets", "items": ["Point one", "Point two", "Point three"], "x": 0.5, "y": 1.5, "w": 4, "h": 3, "fontSize": 14, "color": "333333" }
```

### 3. `shape`
Decorative rectangles, ovals, lines — for accent bars, dividers, backgrounds.
```json
{ "type": "shape", "shape": "RECTANGLE", "x": 0, "y": 0, "w": 10, "h": 0.05, "fill": "F9A825", "lineColor": "", "lineWidth": 0, "transparency": 0, "shadow": false }
```
Shapes: `RECTANGLE`, `OVAL`, `LINE`

### 4. `card`
Rounded card with shadow and optional accent top bar. Great for grouping content.
```json
{ "type": "card", "x": 0.5, "y": 1.5, "w": 2.8, "h": 3, "fill": "FFFFFF", "borderColor": "E0E0E0", "accentColor": "1E2761", "title": "Card Title", "titleColor": "1E2761", "text": "Card body text goes here", "color": "555555", "fontSize": 11 }
```

### 5. `section_header`
Full-width colored header bar across the top of a slide.
```json
{ "type": "section_header", "text": "Section Title", "y": 0, "h": 0.6, "fill": "1E2761", "color": "FFFFFF", "fontSize": 18 }
```

### 6. `stat_box`
Large number + label in a bordered box — perfect for metrics and KPIs.
```json
{ "type": "stat_box", "x": 0.5, "y": 1.5, "w": 2, "h": 1.8, "value": "98%", "label": "Accuracy Rate", "accentColor": "F9A825", "valueColor": "1E2761", "borderColor": "E0E0E0" }
```

### 7. `table`
Data table with header row and custom styling.
```json
{ "type": "table", "rows": [["Header 1", "Header 2"], ["Data 1", "Data 2"]], "x": 0.5, "y": 1.5, "w": 9, "h": 3, "headerFill": "1E2761", "borderColor": "E0E0E0", "colW": [4.5, 4.5] }
```

### 8. `chart`
Bar, line, pie, or doughnut chart with data.
```json
{ "type": "chart", "chartType": "BAR", "data": [{ "name": "Series 1", "labels": ["A", "B", "C"], "values": [10, 20, 30] }], "x": 0.5, "y": 1.5, "w": 9, "h": 3.5, "colors": ["1E2761", "CADCFC", "F9A825"], "showLegend": true, "showValue": false }
```
Chart types: `BAR`, `PIE`, `LINE`, `DOUGHNUT`

### 9. `image`
Embedded image from user-provided file (EXACT file path required).
```json
{ "type": "image", "path": "/Users/name/Desktop/figures/chart.png", "x": 5, "y": 1, "w": 4.5, "h": 3.5, "shadow": true, "caption": "Figure 1: Results" }
```

---

## Layout Patterns

**NEVER repeat the same layout twice.** Vary these across slides:

### Pattern A — Section Header + Cards Row
Section header bar at top, 3 cards in a row below. Good for features, categories, pillars.

### Pattern B — Two Column (Text + Image)
Section header → left side: bullets or cards (w:4.5), right side: image (w:4.5). Good for explanations with visuals.

### Pattern C — Stats Row
Section header → 3-4 stat_boxes in a row showing key numbers. Good for metrics, KPIs, results.

### Pattern D — Comparison (Left vs Right)
Two colored cards side by side with contrasting colors. Good for before/after, pros/cons, options.

### Pattern E — Full Image + Caption
Section header → large image centered (w:9, h:3.5) → caption below. Good for screenshots, diagrams, photos.

### Pattern F — Table Slide
Section header → table with headerFill matching theme. Good for data, comparisons, schedules.

---

## Mandatory Slide Structure

1. **Slide 1** = Title slide (dark bg, `"footer": false`, large title 44pt, subtitle, accent shapes)
2. **Slides 2-N** = Content slides (USE DIFFERENT PATTERNS — not all the same!)
3. **Last slide** = Thank You / Summary (dark bg, call to action)

---

## Image Rules

When user provides images:
- Place images in two-column layouts: text on left (w:4.5), image on right (w:4.5)
- Or full-width (w:9, h:3.5) with caption below
- Add `shadow: true` and `caption` for professional look
- Use the EXACT file path provided — do not modify paths

## Content File Rules

When user provides source content:
- Organize into clear sections
- Summarize into slide-friendly points — do NOT copy verbatim
- Extract key data/stats and present as stat_boxes
- Maintain the narrative flow of the original

---

## Avoid (Common Mistakes)

- **Don't repeat the same layout** — vary cards, stats, tables, columns across slides
- **Don't create text-only slides** — every slide MUST have shapes, cards, stat_boxes, or images
- **Don't center body text** — left-align paragraphs and lists; center only titles
- **Don't skimp on size contrast** — titles need 36pt+ to stand out from 11-14pt body
- **Don't default to blue** — pick colors that reflect the specific topic
- **Don't mix spacing randomly** — choose 0.3" or 0.5" gaps and use consistently
- **Don't style one slide and leave the rest plain** — commit fully throughout
- **NEVER use accent lines under titles** — these are a hallmark of AI-generated slides; use section_header bars instead
- **Don't forget about the footer** — auto-footer appears on slides 2+; keep content above y=5.3"
- **Don't use low-contrast combinations** — text MUST be readable against its background
- **Don't put too many elements on one slide** — 4-6 elements max per slide
- **All colors must be 6-char hex WITHOUT `#` prefix** — e.g., `1E2761` not `#1E2761`

---

## Output Format

Return ONLY valid JSON (no markdown, no backticks, no explanation):

```json
{
  "title": "Presentation Title",
  "theme": {
    "primary": "HEX",
    "secondary": "HEX",
    "accent": "HEX",
    "fontHeader": "Georgia",
    "fontBody": "Calibri"
  },
  "slides": [
    {
      "background": "HEX",
      "footer": false,
      "elements": [...]
    }
  ]
}
```

---

## Supported Image Formats

PNG, JPG, JPEG, GIF, WebP, BMP

## Dependencies

- `pptxgenjs` (npm) — PowerPoint file generation
- Gemini 3 Flash Preview — AI slide design
