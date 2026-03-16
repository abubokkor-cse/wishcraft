# PptxGenJS Builder Reference

Technical reference for how WishCraft's main.js builds slides from Gemini's JSON output using PptxGenJS.

## Setup

```javascript
const PptxGenJS = require('pptxgenjs');
const pres = new PptxGenJS();
pres.layout = 'LAYOUT_16x9';  // 10" × 5.625"
```

## Layout Dimensions

| Layout | Width | Height |
|--------|-------|--------|
| LAYOUT_16x9 | 10" | 5.625" |

All coordinates (x, y, w, h) are in **inches**. Origin (0,0) is top-left corner.

---

## Element Building

### Text

```javascript
slide.addText("Title", {
  x: 0.5, y: 0.5, w: 9, h: 1,
  fontSize: 44, fontFace: "Georgia",
  color: "FFFFFF", bold: true,
  align: "center", valign: "middle"
});
```

### Bullets

```javascript
// Uses PptxGenJS bullet: true — NEVER unicode "•"
slide.addText([
  { text: "Point 1", options: { bullet: true, breakLine: true } },
  { text: "Point 2", options: { bullet: true, breakLine: true } },
  { text: "Point 3", options: { bullet: true } }
], { x: 0.5, y: 1.5, w: 4, h: 3, fontSize: 14, color: "333333" });
```

### Shapes

```javascript
// Rectangle accent bar
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.05,
  fill: { color: "F9A825" }
});

// With shadow
slide.addShape(pres.shapes.RECTANGLE, {
  x: 1, y: 1, w: 3, h: 2,
  fill: { color: "FFFFFF" },
  shadow: { type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.15 }
});
```

### Cards (Custom Element)

Built from shape + text. Creates a white card with shadow and optional colored accent bar at top.

```javascript
// Background rectangle with shadow
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.5, w: 2.8, h: 3,
  fill: { color: "FFFFFF" },
  shadow: { type: "outer", color: "000000", blur: 4, offset: 2, opacity: 0.15 }
});

// Accent bar at top
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.5, w: 2.8, h: 0.06,
  fill: { color: "1E2761" }
});

// Title text
slide.addText("Card Title", {
  x: 0.7, y: 1.7, w: 2.4, h: 0.4,
  fontSize: 14, bold: true, color: "1E2761"
});

// Body text
slide.addText("Card body content", {
  x: 0.7, y: 2.1, w: 2.4, h: 2.2,
  fontSize: 11, color: "555555", valign: "top"
});
```

### Section Headers (Custom Element)

Full-width colored bar across the top of a slide.

```javascript
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.6,
  fill: { color: "1E2761" }
});
slide.addText("Section Title", {
  x: 0.5, y: 0, w: 9, h: 0.6,
  fontSize: 18, bold: true, color: "FFFFFF", valign: "middle"
});
```

### Stat Boxes (Custom Element)

Large number + label in a bordered box with shadow.

```javascript
// Box with border and shadow
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.5, w: 2, h: 1.8,
  fill: { color: "FFFFFF" },
  line: { color: "E0E0E0", width: 1 },
  shadow: { type: "outer", color: "000000", blur: 3, offset: 1, opacity: 0.1 }
});

// Accent bar at top
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.5, w: 2, h: 0.06,
  fill: { color: "F9A825" }
});

// Large number
slide.addText("98%", {
  x: 0.5, y: 1.7, w: 2, h: 0.8,
  fontSize: 32, bold: true, color: "1E2761", align: "center"
});

// Label
slide.addText("Accuracy Rate", {
  x: 0.5, y: 2.5, w: 2, h: 0.5,
  fontSize: 11, color: "666666", align: "center"
});
```

### Tables

```javascript
const tableRows = rows.map((row, i) =>
  row.map(cell => ({
    text: cell,
    options: i === 0
      ? { fill: { color: "1E2761" }, color: "FFFFFF", bold: true, fontSize: 11 }
      : { fill: { color: i % 2 === 0 ? "F5F5F5" : "FFFFFF" }, fontSize: 10 }
  }))
);
slide.addTable(tableRows, { x: 0.5, y: 1.5, w: 9, colW: [4.5, 4.5] });
```

### Charts

```javascript
slide.addChart(pres.charts.BAR, chartData, {
  x: 0.5, y: 1.5, w: 9, h: 3.5,
  barDir: "col",
  chartColors: ["1E2761", "CADCFC", "F9A825"],
  chartArea: { fill: { color: "FFFFFF" }, roundedCorners: true },
  valGridLine: { color: "E2E8F0", size: 0.5 },
  catGridLine: { style: "none" },
  showValue: true,
  showLegend: true
});
```

Chart types: `pres.charts.BAR`, `pres.charts.PIE`, `pres.charts.LINE`, `pres.charts.DOUGHNUT`

### Images

```javascript
// Read file, convert to base64
const imgData = fs.readFileSync(resolvedPath);
const base64 = `image/${ext};base64,${imgData.toString('base64')}`;

slide.addImage({
  data: base64,
  x: 5, y: 1, w: 4.5, h: 3.5,
  shadow: { type: "outer", color: "000000", blur: 4, offset: 2, opacity: 0.15 }
});

// Caption below image
slide.addText("Figure 1: Results", {
  x: 5, y: 4.6, w: 4.5, h: 0.3,
  fontSize: 9, italic: true, color: "999999", align: "center"
});
```

---

## Auto-Footer

Added automatically to slides 2+ (when `footer !== false`):

```javascript
// Navy bar at bottom
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 5.25, w: 10, h: 0.375,
  fill: { color: "1E2761" }
});

// Title on left
slide.addText(presentationTitle, {
  x: 0.5, y: 5.25, w: 7, h: 0.375,
  fontSize: 8, color: "FFFFFF", valign: "middle"
});

// Slide number on right
slide.addText(`${slideIndex + 1}`, {
  x: 8.5, y: 5.25, w: 1, h: 0.375,
  fontSize: 8, color: "FFFFFF", align: "right", valign: "middle"
});
```

---

## Common Pitfalls

⚠️ These cause file corruption, visual bugs, or broken output:

1. **NEVER use "#" with hex colors** — causes file corruption
   - ✅ `color: "FF0000"`
   - ❌ `color: "#FF0000"`

2. **NEVER encode opacity in hex string** — 8-char colors corrupt the file
   - ✅ `shadow: { color: "000000", opacity: 0.15 }`
   - ❌ `shadow: { color: "00000020" }`

3. **NEVER use unicode bullets** — creates double bullets
   - ✅ `{ text: "Item", options: { bullet: true } }`
   - ❌ `"• Item"`

4. **NEVER reuse option objects** — PptxGenJS mutates objects in-place
   - ✅ Create fresh shadow object for each call
   - ❌ Share same shadow object between elements

5. **Use `breakLine: true`** between bullet array items

6. **Negative shadow offset corrupts file** — use `angle: 270` instead

7. **ROUNDED_RECTANGLE + accent bars don't align** — use RECTANGLE instead
