---
name: macos-productivity
description: Use this skill when the user wants to boost productivity, manage their workspace, create documents, set up projects, or automate repetitive macOS workflows. Covers document creation, code projects, system management, and multi-app workflows.
triggers: productivity, workflow, automate, document, project, workspace, setup, template, batch, morning routine, daily
platform: darwin
---

# macOS Productivity Skill

Combine WishCraft's 230+ macOS automation actions into powerful multi-step workflows.

## Quick Workflows

### Morning Routine
1. `calendar_today_events` — Check today's schedule
2. `reminders_list` — Review pending tasks
3. `mail_open` — Open email for review
4. `system_get_battery` / `system_get_disk_space` — System health check

### Document Creation (Word)
1. `word_open` → `word_new_document`
2. Use `word_write_formatted_document({title, sections})` for structured docs
3. Or manual: `word_heading_1` → `word_write` → `word_new_line` → `word_normal_text` → `word_write`
4. `word_save({filename})`

### Code Project Setup (VS Code)
1. `finder_create_folder({path: "~/Projects/my-app"})`
2. `vscode_open_folder({path: "~/Projects/my-app"})`
3. `vscode_create_file_with_code({folder_path, filename, code})`
4. `vscode_run_in_terminal({command: "npm init -y"})`

### Research & Notes
1. Google Search (built-in grounding) for real-time info
2. `notes_create({title, body})` to save findings
3. `safari_new_tab({url})` to open reference pages
4. `clipboard_write` / `clipboard_read` for quick data transfer

### File Management
1. `finder_list_folder` — See what's in a directory
2. `finder_search({query, folder})` — Find specific files
3. `organize_suggest_plan({path})` — Smart cleanup analysis
4. `organize_by_type` / `organize_by_date` — Organize files

## Multi-App Patterns

- **Screenshot → Note**: `system_screenshot_full` → `notes_create({title: "Screenshot note"})`
- **Web → Document**: Browse with Safari → `clipboard_read` → `word_write({text})`
- **Code → Test**: `vscode_write_code` → `vscode_save` → `vscode_run_code`
- **Email summary**: `calendar_today_events` → `mail_compose({subject: "Daily Summary", body: ...})`
