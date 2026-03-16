---
name: numbers-automation
description: "Use this skill when the user wants to work with Apple Numbers on macOS. Covers creating spreadsheets, typing data into cells, navigating to specific cells, entering formulas, formatting (bold, italic, underline, borders), inserting/deleting rows and columns, sorting, filtering, find, reading cell values, managing sheets, and building complete spreadsheets from scratch with headers, data rows, and formulas."
triggers: numbers, apple numbers, spreadsheet numbers, cells, formula, budget, expenses, income, financial, data entry, filter, sort data, sum, average, column, row, table data, salary, tracker, inventory, grades, score, report, sales
platform: darwin
---

# Apple Numbers Automation Skill

Full Apple Numbers automation on macOS via **native AppleScript** — direct cell access, no keyboard simulation for data entry. 55+ actions for creating, editing, formatting, and analyzing spreadsheets.

---

## CRITICAL RULE — Creating New Spreadsheets

**ALWAYS use `numbers_create_spreadsheet` as ONE single call with ALL parameters.**

It does EVERYTHING automatically via native AppleScript:
1. Opens Numbers
2. Creates new document (native `make new document`)
3. Sets all headers in row 1 (native `set value of cell`)
4. Bolds the header row (native `set selection range` + Cmd+B)
5. Sets all data rows starting from row 2 (native `set value of cell`)
6. Adds all formulas (native `set value of cell` — Numbers auto-evaluates)
7. Saves the file to Desktop (native `save front document in file`)

**After `create_spreadsheet` returns → STOP. Do NOT call any other numbers_ function.**
No `type_in_cell`. No `enter_formula`. No `save`. No `go_to_cell`. NOTHING. It's already done.

---

## Examples — What the User Says → What You Call

### Example 1: Budget Tracker
**User says:** "Create a budget spreadsheet in Numbers with Rent 1500, Food 600, Transport 300, Entertainment 400 and total it up"

**You call ONE function:**
```json
desktop_automation("numbers_create_spreadsheet", {
  "title": "Monthly Budget",
  "headers": ["Category", "Amount"],
  "rows": [
    ["Rent", "1500"],
    ["Food", "600"],
    ["Transport", "300"],
    ["Entertainment", "400"]
  ],
  "formulas": [
    {"cell": "A6", "formula": "Total"},
    {"cell": "B6", "formula": "=SUM(B2:B5)"}
  ]
})
```
**Result in Numbers:**

| | A | B |
|---|---|---|
| 1 | **Category** | **Amount** |
| 2 | Rent | 1500 |
| 3 | Food | 600 |
| 4 | Transport | 300 |
| 5 | Entertainment | 400 |
| 6 | Total | =SUM(B2:B5) → 2800 |

**Then STOP. Done. Say "Your budget is ready!"**

---

### Example 2: Student Grades
**User says:** "Make a grades spreadsheet in Numbers with Math 85, Science 92, English 78 and average"

**You call:**
```json
desktop_automation("numbers_create_spreadsheet", {
  "title": "Student Grades",
  "headers": ["Subject", "Score"],
  "rows": [
    ["Math", "85"],
    ["Science", "92"],
    ["English", "78"]
  ],
  "formulas": [
    {"cell": "A5", "formula": "Average"},
    {"cell": "B5", "formula": "=AVERAGE(B2:B4)"}
  ]
})
```

---

### Example 3: Expense Tracker
**User says:** "Make an expense tracker in Numbers with Coffee 5, Lunch 12, Taxi 25, Gym 50 and show total"

**You call:**
```json
desktop_automation("numbers_create_spreadsheet", {
  "title": "Expense Tracker",
  "headers": ["Item", "Cost"],
  "rows": [
    ["Coffee", "5"],
    ["Lunch", "12"],
    ["Taxi", "25"],
    ["Gym", "50"]
  ],
  "formulas": [
    {"cell": "A6", "formula": "Total"},
    {"cell": "B6", "formula": "=SUM(B2:B5)"}
  ]
})
```

---

### Example 4: Sales Report (3+ columns with calculated column)
**User says:** "Create a sales report in Numbers with Product, Quantity, Price — Laptop 10 999, Phone 25 699, Tablet 15 499, and total revenue"

**You call:**
```json
desktop_automation("numbers_create_spreadsheet", {
  "title": "Sales Report",
  "headers": ["Product", "Quantity", "Price", "Revenue"],
  "rows": [
    ["Laptop", "10", "999", ""],
    ["Phone", "25", "699", ""],
    ["Tablet", "15", "499", ""]
  ],
  "formulas": [
    {"cell": "D2", "formula": "=B2*C2"},
    {"cell": "D3", "formula": "=B3*C3"},
    {"cell": "D4", "formula": "=B4*C4"},
    {"cell": "A5", "formula": "Total"},
    {"cell": "D5", "formula": "=SUM(D2:D4)"}
  ]
})
```

---

### Example 5: Weekly Schedule
**User says:** "Make a weekly work hours tracker Mon to Fri with 8 hours each and total"

**You call:**
```json
desktop_automation("numbers_create_spreadsheet", {
  "title": "Weekly Hours",
  "headers": ["Day", "Hours"],
  "rows": [
    ["Monday", "8"],
    ["Tuesday", "8"],
    ["Wednesday", "8"],
    ["Thursday", "8"],
    ["Friday", "8"]
  ],
  "formulas": [
    {"cell": "A7", "formula": "Total"},
    {"cell": "B7", "formula": "=SUM(B2:B6)"}
  ]
})
```

---

### Example 6: Salary Breakdown
**User says:** "Numbers spreadsheet with salary breakdown — Basic 50000, HRA 20000, DA 15000, Tax 8500, show total earning and net salary"

**You call:**
```json
desktop_automation("numbers_create_spreadsheet", {
  "title": "Salary Breakdown",
  "headers": ["Component", "Amount"],
  "rows": [
    ["Basic Salary", "50000"],
    ["HRA", "20000"],
    ["DA", "15000"],
    ["Tax Deduction", "8500"]
  ],
  "formulas": [
    {"cell": "A6", "formula": "Total Earnings"},
    {"cell": "B6", "formula": "=SUM(B2:B4)"},
    {"cell": "A7", "formula": "Net Salary"},
    {"cell": "B7", "formula": "=B6-B5"}
  ]
})
```

---

## Formula Cell Calculation Guide

When building formulas, calculate the correct cell reference:
- **Row 1** = Headers (A1, B1, C1...)
- **Row 2** = First data row (A2, B2, C2...)
- **Row N+1** = Nth data row
- **Formula row** = skip one row after last data row

**Formula for "total" row:**
- If you have 4 data rows (rows 2-5), put formula in row 6 or 7
- `=SUM(B2:B5)` sums column B from first data to last data
- `=AVERAGE(B2:B5)` averages column B

**Formula for calculated columns:**
- Revenue = Quantity × Price: `=B2*C2` in cell D2, `=B3*C3` in D3, etc.
- Percentage: `=B2/B10*100`

---

## Editing an Existing Spreadsheet

For editing (NOT creating new), use individual functions with the **cell parameter** for direct native AppleScript access:

### Change a cell value (direct)
```
desktop_automation("numbers_type_in_cell", {"text": "750", "cell": "B3"})
```

### Add a formula to a cell (direct)
```
desktop_automation("numbers_enter_formula", {"formula": "=SUM(C2:C9)", "cell": "C10"})
```

### Read a cell value (direct)
```
desktop_automation("numbers_read_cell", {"cell": "A1"})
```

### Navigate to a cell
```
desktop_automation("numbers_go_to_cell", {"cell": "B5"})
```

### Find and replace (navigate + edit)
```
desktop_automation("numbers_find", {"text": "old value"})
```

---

## All Actions Reference (55+ total)

All actions use `desktop_automation("numbers_action_name", {args})`.

### App Control (3)
| Action | Args | Description |
|--------|------|-------------|
| `numbers_open` | — | Open Apple Numbers |
| `numbers_close` | — | Quit Numbers |
| `numbers_close_spreadsheet` | — | Close current spreadsheet |

### Spreadsheet & Sheet (6)
| Action | Args | Description |
|--------|------|-------------|
| `numbers_new_spreadsheet` | — | Create new blank document (native) |
| `numbers_save` | `filename` (optional) | Save to Desktop as .numbers (native) |
| `numbers_open_file` | `path` | Open a specific .numbers file |
| `numbers_new_sheet` | — | Add a new sheet |
| `numbers_next_sheet` | — | Switch to next sheet tab |
| `numbers_prev_sheet` | — | Switch to previous sheet tab |

### Cell Navigation (8)
| Action | Args | Description |
|--------|------|-------------|
| `numbers_go_to_cell` | `cell` (e.g. "A1") | Select cell via native AppleScript |
| `numbers_move_right` | — | Move one cell right |
| `numbers_move_down` | — | Move one cell down |
| `numbers_move_up` | — | Move one cell up |
| `numbers_move_left` | — | Move one cell left |
| `numbers_move_to_start` | — | Jump to cell A1 |
| `numbers_move_to_end` | — | Jump to last used cell |
| `numbers_move_to_edge` | `direction` | Jump to edge of data region |

### Cell Input (7)
| Action | Args | Description |
|--------|------|-------------|
| `numbers_type_in_cell` | `text`, `cell` (optional) | Set cell value (native if cell given) |
| `numbers_type_and_stay` | `text` | Set value, move down |
| `numbers_edit_cell` | — | Enter edit mode |
| `numbers_enter_formula` | `formula`, `cell` (optional) | Set formula (native if cell given) |
| `numbers_clear_cell` | — | Clear current cell |
| `numbers_autofill` | — | Turn on autofill |
| `numbers_autofill_from_column` | — | Autofill from column before |

### Selection (8)
| Action | Args | Description |
|--------|------|-------------|
| `numbers_select_all` | — | Select all cells |
| `numbers_select_column` | — | Select entire column |
| `numbers_select_row` | — | Select entire row |
| `numbers_copy` | — | Copy selection |
| `numbers_paste` | — | Paste |
| `numbers_cut` | — | Cut selection |
| `numbers_paste_values` | — | Paste values only |
| `numbers_read_selection` | — | Read selected cells |

### Formatting (12)
| Action | Args | Description |
|--------|------|-------------|
| `numbers_bold` | — | Toggle bold |
| `numbers_italic` | — | Toggle italic |
| `numbers_underline` | — | Toggle underline |
| `numbers_increase_font` | — | Increase font size |
| `numbers_decrease_font` | — | Decrease font size |
| `numbers_align_center` | — | Center align |
| `numbers_align_left` | — | Left align |
| `numbers_auto_align` | — | Auto-align content |
| `numbers_add_border_top` | — | Toggle top border |
| `numbers_add_border_bottom` | — | Toggle bottom border |
| `numbers_add_border_left` | — | Toggle left border |
| `numbers_add_border_right` | — | Toggle right border |

### Merge/Unmerge (2)
| Action | Args | Description |
|--------|------|-------------|
| `numbers_merge_cells` | — | Merge selected cells |
| `numbers_unmerge_cells` | — | Unmerge selected cells |

### Row/Column (6)
| Action | Args | Description |
|--------|------|-------------|
| `numbers_add_row_above` | — | Insert row above |
| `numbers_add_row_below` | — | Insert row below |
| `numbers_add_column_left` | — | Insert column left |
| `numbers_add_column_right` | — | Insert column right |
| `numbers_delete_row` | — | Delete selected rows |
| `numbers_delete_column` | — | Delete selected columns |

### Data Tools (4)
| Action | Args | Description |
|--------|------|-------------|
| `numbers_sort` | — | Apply sorting rules |
| `numbers_add_filter` | — | Toggle filters |
| `numbers_find` | `text` | Find text |
| `numbers_insert_equation` | — | Insert equation |

### Utility (8)
| Action | Args | Description |
|--------|------|-------------|
| `numbers_undo` | — | Undo |
| `numbers_redo` | — | Redo |
| `numbers_read_cell` | `cell` (optional) | Read cell value (native if cell given) |
| `numbers_insert_date` | — | Insert current date |
| `numbers_insert_time` | — | Insert current time |
| `numbers_print` | — | Print dialog |
| `numbers_add_comment` | — | Add comment |
| `numbers_toggle_sidebar` | — | Toggle format sidebar |

### Compound — THE POWER FUNCTION (1)
| Action | Args | Description |
|--------|------|-------------|
| `numbers_create_spreadsheet` | `title`, `headers`, `rows`, `formulas` | Build COMPLETE spreadsheet in ONE call |

---

## Common Formulas (Numbers compatible)

| Formula | Purpose | Example |
|---------|---------|---------|
| `=SUM(B2:B10)` | Sum a range | Total expenses |
| `=AVERAGE(B2:B10)` | Average | Average score |
| `=COUNT(B2:B10)` | Count numbers | Count entries |
| `=MAX(B2:B10)` | Maximum | Highest score |
| `=MIN(B2:B10)` | Minimum | Lowest price |
| `=IF(B2>100,"High","Low")` | Conditional | Pass/fail |
| `=B2*C2` | Multiply | Revenue = qty × price |
| `=B6-B5` | Subtract | Net = total - tax |
| `=ROUND(B2,2)` | Round | 2 decimal places |
| `=B2/B10*100` | Percentage | % of total |
| `=SUMIF(A2:A10,"Food",B2:B10)` | Conditional sum | Sum only "Food" rows |
| `=COUNTIF(B2:B10,">50")` | Conditional count | Count values > 50 |

---

## NEVER DO THIS (Common Mistakes)

- **NEVER call type_in_cell/enter_formula/save AFTER create_spreadsheet** — it duplicates work and breaks the layout
- **NEVER create spreadsheet in multiple calls** — always ONE `create_spreadsheet` call with ALL data
- **NEVER forget formulas** — if user says "total" or "sum" or "average", include it in the formulas array
- **NEVER use type_in_cell for formulas** — use `enter_formula` instead (or include in create_spreadsheet formulas)
- **NEVER forget the title** — always include title so the file gets saved
- **NEVER split create + save** — `create_spreadsheet` saves automatically when title is provided

---

## Dependencies

- Apple Numbers (pre-installed on macOS)
- macOS Accessibility permissions (System Settings → Privacy → Accessibility)
