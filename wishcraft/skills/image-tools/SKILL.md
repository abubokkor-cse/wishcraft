---
name: image-tools
description: "Use this skill when the user wants to process images — remove backgrounds, convert formats, or batch process multiple images. Supports single image, multiple images, or entire folder processing. AI-powered background removal using rembg + U2Net. Cross-platform (Windows/macOS/Linux). Outputs transparent PNG."
triggers: remove background, background removal, transparent, png, batch images, resize image, convert image, image processing, no background, cut out, transparent background, product photo
platform: all
---

# Image Tools Skill

AI-powered image processing tools. Cross-platform (Windows/macOS/Linux). Uses rembg with U2Net model for precise background removal.

## How It Works

1. User provides image path(s) or folder path
2. Python loads rembg + U2Net AI model (auto-installs on first use)
3. AI removes background, outputs transparent PNG
4. Processed files saved next to originals (or in `no_bg/` subfolder for folders)

## Available Tools

### `remove_background` — Remove image background

Removes background from images using AI (rembg + U2Net model). Outputs transparent PNG.

**Modes:**

| Mode | Description | Key Parameter | Output |
|------|-------------|---------------|--------|
| `single` | One image | `path`: image file path | `{name}_no_bg.png` next to original |
| `batch` | Multiple images | `paths`: array of file paths | `{name}_no_bg.png` next to each original |
| `folder` | All images in folder | `path`: folder path | `no_bg/` subfolder with all processed |

---

## Tool Parameters

Use `remove_background` with these parameters:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `mode` | string | Yes | `"single"`, `"batch"`, or `"folder"` |
| `path` | string | Yes (single/folder) | File or folder path (supports `~`) |
| `paths` | array | Yes (batch) | Array of image file paths |

---

## Examples

**Single image:**
```
remove_background({
  mode: "single",
  path: "~/Desktop/photo.jpg"
})
```

**Multiple specific images:**
```
remove_background({
  mode: "batch",
  paths: ["~/Desktop/photo1.jpg", "~/Desktop/photo2.png", "~/Desktop/photo3.webp"]
})
```

**Entire folder:**
```
remove_background({
  mode: "folder",
  path: "~/Desktop/product_photos"
})
```

---

## Choosing the Right Mode

| User Says | Mode to Use |
|-----------|-------------|
| "Remove background from this photo" | `single` |
| "Remove background from photo.jpg" | `single` |
| "Remove backgrounds from these 3 images" | `batch` |
| "Process all images in this folder" | `folder` |
| "Make all product photos transparent" | `folder` |
| "Remove background from photo1 and photo2" | `batch` |

---

## Supported Formats

| Format | Extensions |
|--------|-----------|
| JPEG | `.jpg`, `.jpeg` |
| PNG | `.png` |
| WebP | `.webp` |
| BMP | `.bmp` |
| TIFF | `.tiff`, `.tif` |

Output is always transparent **PNG** regardless of input format.

---

## Output Details

- **Single mode**: Creates `{filename}_no_bg.png` in the same directory as the original
- **Batch mode**: Creates `{filename}_no_bg.png` next to each original file
- **Folder mode**: Creates a `no_bg/` subfolder inside the source folder with all processed images

---

## Important Notes

- **First run**: Auto-installs `rembg` and downloads U2Net AI model (~170MB). Takes 1-2 minutes.
- **After first run**: Fast, fully offline processing. No internet needed.
- **Cross-platform**: Works on Windows, macOS, and Linux.
- **Quality**: Best results with clear subject-background separation. Product photos, portraits, and objects on solid backgrounds produce excellent results.
- **Large batches**: Folder mode processes all valid image files. Non-image files are skipped.

---

## Avoid (Common Mistakes)

- **Don't use `batch` mode with a folder path** — use `folder` mode instead
- **Don't use `single` mode with multiple paths** — use `batch` mode
- **Don't forget `~` expansion** — paths with `~` are supported and resolved automatically
- **Don't expect non-image files to work** — only image formats listed above are supported

---

## Dependencies

- `rembg` (pip) — AI background removal
- `Pillow` (pip) — Image I/O
- U2Net model — auto-downloaded on first use (~170MB)
