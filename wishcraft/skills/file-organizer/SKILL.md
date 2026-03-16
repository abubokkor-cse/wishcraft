---
name: file-organizer
description: Use this skill when the user wants to organize, clean up, deduplicate, or analyze files and folders. Covers scanning directories, finding duplicates, sorting by type or date, archiving old files, renaming patterns, and generating size reports.
triggers: organize, clean up, cleanup, duplicates, sort files, tidy, messy folder, downloads, declutter, file management, disk space, old files, rename files
platform: all
---

# File Organizer Skill

Smart file organization powered by WishCraft's automation engine. Analyze, organize, deduplicate, and clean up any folder.

## Available Actions

All actions are called via `desktop_automation("action_name", {params})`.

### 1. `organize_scan_directory` — Analyze a folder
Scans a directory and returns detailed statistics: file counts by type, total size, largest/oldest/newest files, empty folders.

**Parameters:**
- `path` (string): Folder to scan. Default: `~`
- `max_depth` (integer): How deep to scan. Default: `2`

**Example:** `desktop_automation("organize_scan_directory", {path: "~/Downloads", max_depth: 2})`

### 2. `organize_find_duplicates` — Find duplicate files
Uses SHA-256 hashing to find exact duplicate files. Groups by hash, shows wasted space.

**Parameters:**
- `path` (string): Folder to scan
- `max_depth` (integer): Scan depth. Default: `2`
- `min_size_kb` (integer): Minimum file size to check (skip tiny files). Default: `1`

**Example:** `desktop_automation("organize_find_duplicates", {path: "~/Downloads", min_size_kb: 100})`

### 3. `organize_by_type` — Sort files into category folders
Moves files into subfolders by type: Documents, Images, Videos, Audio, Archives, Code, Apps, Fonts, Design, Data, Other.

**Parameters:**
- `path` (string): Folder to organize
- `dry_run` (boolean): `true` = preview plan, `false` = execute. Default: `true`

**Example:**
```
// First preview:
desktop_automation("organize_by_type", {path: "~/Downloads", dry_run: true})
// Then execute:
desktop_automation("organize_by_type", {path: "~/Downloads", dry_run: false})
```

### 4. `organize_by_date` — Sort files into date folders
Organizes files into year/month subfolders based on modification date.

**Parameters:**
- `path` (string): Folder to organize
- `date_format` (string): `"year"`, `"year_month"`, or `"year_month_day"`. Default: `"year_month"`
- `dry_run` (boolean): Preview or execute. Default: `true`

### 5. `organize_cleanup_old` — Find/archive stale files
Finds files not modified in N days. Can archive them to a dated subfolder (safe, not deleting).

**Parameters:**
- `path` (string): Folder to check
- `older_than_days` (integer): Age threshold. Default: `180`
- `dry_run` (boolean): Preview or execute. Default: `true`

### 6. `organize_remove_duplicates` — Clean up duplicate files
Finds duplicates and archives the copies (keeps the oldest/original). Moves duplicates to a `_duplicates_YYYYMMDD` folder.

**Parameters:**
- `path` (string): Folder to clean
- `max_depth`, `min_size_kb`: Same as find_duplicates
- `dry_run` (boolean): Preview or execute. Default: `true`

### 7. `organize_suggest_plan` — Smart analysis with recommendations
Analyzes a folder and suggests the best organization actions with estimated impact.

**Parameters:**
- `path` (string): Folder to analyze

**Example:** `desktop_automation("organize_suggest_plan", {path: "~/Downloads"})`

### 8. `organize_flatten_folder` — Un-nest deep structures
Moves all files from nested subfolders up to the top level. Useful for cleaning up deeply nested download structures.

**Parameters:**
- `path` (string): Folder to flatten
- `dry_run` (boolean): Preview or execute. Default: `true`

### 9. `organize_rename_pattern` — Batch rename files
Rename files with consistent patterns.

**Parameters:**
- `path` (string): Folder with files to rename
- `pattern` (string): `"date_prefix"` (adds YYYY-MM-DD_), `"lowercase"`, `"no_spaces"` (underscores), `"clean"` (normalize names)
- `dry_run` (boolean): Preview or execute. Default: `true`

### 10. `organize_size_report` — Disk usage report
Shows which folders consume the most space (like ncdu/WinDirStat).

**Parameters:**
- `path` (string): Root folder to analyze
- `max_depth` (integer): Depth. Default: `3`

## Best Practices

1. **Always preview first**: Use `dry_run: true` before any destructive action, then show the user the plan.
2. **Start with suggest_plan**: When user says "organize my files" or "clean up Downloads", start with `organize_suggest_plan` to understand the situation.
3. **Confirm before executing**: After showing the dry run plan, ask the user before running with `dry_run: false`.
4. **Safe archiving**: `cleanup_old` and `remove_duplicates` move files to archive folders, never delete them permanently.
5. **Combine actions**: A full cleanup workflow might be: scan → find duplicates → remove duplicates → organize by type → cleanup old files.

## File Type Categories

| Category | Extensions |
|----------|-----------|
| Documents | pdf, doc, docx, txt, rtf, odt, pages, tex, md, csv, xls, xlsx, ppt, pptx |
| Images | jpg, jpeg, png, gif, bmp, tiff, svg, webp, heic, ico, raw, cr2, nef |
| Videos | mp4, mov, avi, mkv, wmv, flv, webm, m4v, mpg, mpeg |
| Audio | mp3, wav, aac, flac, ogg, wma, m4a, aiff |
| Archives | zip, rar, 7z, tar, gz, bz2, xz, dmg, iso |
| Code | py, js, ts, html, css, java, c, cpp, swift, go, rs, rb, php, sh, json, yaml |
| Apps | app, exe, msi, pkg, deb, rpm |
| Fonts | ttf, otf, woff, woff2 |
| Design | psd, ai, sketch, fig, xd, indd |
| Data | db, sqlite, json, xml, csv, tsv, parquet |
