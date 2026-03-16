---
name: excel-automation
description: "Use this skill when the user wants to work with Microsoft Excel on macOS. Covers creating workbooks, typing data into cells, navigating to specific cells, entering formulas, formatting (bold, currency, percent, borders), inserting/deleting rows and columns, sorting, filtering, creating tables, find & replace, reading cell values, managing sheets, and building complete spreadsheets from scratch with headers, data rows, and formulas."
triggers: excel, spreadsheet, workbook, xlsx, cells, formula, budget, expenses, income, financial, data entry, pivot, filter, sort data, sum, average, column, row, table data, salary, tracker, inventory, grades, score, report, sales
platform: darwin
---

# Excel Automation Skill

Full Microsoft Excel automation on macOS via native AppleScript. 55+ actions for creating, editing, formatting, and analyzing spreadsheets.

---

## CRITICAL RULE — Creating New Spreadsheets

**ALWAYS use `excel_create_spreadsheet` as ONE single call with ALL parameters.**

It does EVERYTHING automatically:
1. Opens Excel
2. Creates new workbook
3. Types all headers in row 1
4. Bolds the header row
5. Types all data rows starting from row 2
6. Adds all formulas
7. Saves the file to Desktop

**After `create_spreadsheet` returns → STOP. Do NOT call any other excel_ function.**
No `type_in_cell`. No `enter_formula`. No `save`. No `go_to_cell`. NOTHING. It's already done.

---

## Examples — What the User Says → What You Call

### Example 1: Budget Tracker
**User says:** "Create a budget spreadsheet with Rent 1500, Food 600, Transport 300, Entertainment 400 and total it up"

**You call ONE function:**
```json
desktop_automation("excel_create_spreadsheet", {
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
**Result in Excel:**

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
**User says:** "Make a grades spreadsheet with Math 85, Science 92, English 78 and average"

**You call:**
```json
desktop_automation("excel_create_spreadsheet", {
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
**User says:** "Make an expense tracker with Coffee 5, Lunch 12, Taxi 25, Gym 50 and show total"

**You call:**
```json
desktop_automation("excel_create_spreadsheet", {
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

### Example 4: Sales Report (3 columns)
**User says:** "Create a sales report with Product, Quantity, Price — Laptop 10 999, Phone 25 699, Tablet 15 499, and total revenue"

**You call:**
```json
desktop_automation("excel_create_spreadsheet", {
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
desktop_automation("excel_create_spreadsheet", {
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
**User says:** "Excel spreadsheet with salary breakdown — Basic 50000, HRA 20000, DA 15000, Tax 8500, show total earning and net salary"

**You call:**
```json
desktop_automation("excel_create_spreadsheet", {
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

For editing (NOT creating new), use individual functions:

### Change a cell value
```
desktop_automation("excel_go_to_cell", {"cell": "B3"})
desktop_automation("excel_type_in_cell", {"text": "750"})
```

### Add a formula to a cell
```
desktop_automation("excel_go_to_cell", {"cell": "C10"})
desktop_automation("excel_enter_formula", {"formula": "=SUM(C2:C9)"})
```

### Format cells as currency
```
desktop_automation("excel_select_range", {"range": "B2:B10"})
desktop_automation("excel_format_currency")
```

### Read data
```
desktop_automation("excel_go_to_cell", {"cell": "A1"})
desktop_automation("excel_read_cell")
```

### Find and replace
```
desktop_automation("excel_find_replace", {"find_text": "old", "replace_text": "new"})
```

---

## All Actions Reference (55 total)

All actions use `desktop_automation("excel_action_name", {args})`.

### App Control (3)
| Action | Args | Description |
|--------|------|-------------|
| `excel_open` | — | Open Microsoft Excel |
| `excel_close` | — | Quit Excel |
| `excel_close_workbook` | — | Close current workbook |

### Workbook & Sheet (6)
| Action | Args | Description |
|--------|------|-------------|
| `excel_new_workbook` | — | Create new blank workbook |
| `excel_save` | `filename` (optional) | Save (to Desktop as .xlsx) |
| `excel_open_file` | `path` | Open a specific .xlsx file |
| `excel_new_sheet` | — | Insert a new sheet |
| `excel_next_sheet` | — | Switch to next sheet tab |
| `excel_prev_sheet` | — | Switch to previous sheet tab |

### Cell Navigation (8)
| Action | Args | Description |
|--------|------|-------------|
| `excel_go_to_cell` | `cell` (e.g. "A1") | Jump to specific cell |
| `excel_move_right` | — | Move one cell right |
| `excel_move_down` | — | Move one cell down |
| `excel_move_up` | — | Move one cell up |
| `excel_move_left` | — | Move one cell left |
| `excel_move_to_start` | — | Jump to cell A1 |
| `excel_move_to_end` | — | Jump to last used cell |
| `excel_move_to_edge` | `direction` | Jump to edge of data region |

### Cell Input (7)
| Action | Args | Description |
|--------|------|-------------|
| `excel_type_in_cell` | `text` | Set cell value, move right |
| `excel_type_and_stay` | `text` | Set cell value, move down |
| `excel_edit_cell` | — | Enter edit mode (F2) |
| `excel_enter_formula` | `formula` | Set formula (e.g. "=SUM(A1:A10)") |
| `excel_fill_down` | — | Fill selection down |
| `excel_fill_right` | — | Fill selection right |
| `excel_clear_cell` | — | Clear current cell |

### Selection (8)
| Action | Args | Description |
|--------|------|-------------|
| `excel_select_all` | — | Select all cells |
| `excel_select_column` | — | Select entire column |
| `excel_select_row` | — | Select entire row |
| `excel_select_range` | `range` (e.g. "A1:D10") | Select a cell range |
| `excel_copy` | — | Copy selection |
| `excel_paste` | — | Paste |
| `excel_cut` | — | Cut selection |
| `excel_paste_values` | — | Paste values only |

### Formatting (14)
| Action | Args | Description |
|--------|------|-------------|
| `excel_bold` | — | Toggle bold |
| `excel_italic` | — | Toggle italic |
| `excel_underline` | — | Toggle underline |
| `excel_strikethrough` | — | Toggle strikethrough |
| `excel_increase_font` | — | Increase font size |
| `excel_decrease_font` | — | Decrease font size |
| `excel_align_center` | — | Center align |
| `excel_align_left` | — | Left align |
| `excel_format_number` | — | Number format (1,000.00) |
| `excel_format_currency` | — | Currency ($1,000.00) |
| `excel_format_percent` | — | Percentage (85%) |
| `excel_format_date` | — | Date format |
| `excel_format_general` | — | General format |
| `excel_add_border` | — | Add border |
| `excel_remove_border` | — | Remove border |

### Row/Column (8)
| Action | Args | Description |
|--------|------|-------------|
| `excel_insert_row` | — | Insert row above |
| `excel_insert_column` | — | Insert column before |
| `excel_delete_row` | — | Delete current row |
| `excel_delete_column` | — | Delete current column |
| `excel_hide_column` | — | Hide column |
| `excel_unhide_column` | — | Unhide column |
| `excel_hide_row` | — | Hide row |
| `excel_unhide_row` | — | Unhide row |

### Data Tools (5)
| Action | Args | Description |
|--------|------|-------------|
| `excel_sort` | — | Open Sort dialog |
| `excel_add_filter` | — | Toggle AutoFilter |
| `excel_create_table` | — | Create table from selection |
| `excel_find` | `text` | Find text |
| `excel_find_replace` | `find_text`, `replace_text` | Find and replace |

### Utility (7)
| Action | Args | Description |
|--------|------|-------------|
| `excel_undo` | — | Undo |
| `excel_redo` | — | Redo |
| `excel_read_cell` | — | Read current cell value |
| `excel_read_selection` | — | Read all selected cells |
| `excel_insert_date` | — | Insert current date |
| `excel_insert_time` | — | Insert current time |
| `excel_print` | — | Print dialog |

### Compound — THE POWER FUNCTION (1)
| Action | Args | Description |
|--------|------|-------------|
| `excel_create_spreadsheet` | `title`, `headers`, `rows`, `formulas` | Build COMPLETE spreadsheet in ONE call |

---

## Common Formulas

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

---

## NEVER DO THIS (Common Mistakes)

- **NEVER call type_in_cell/enter_formula/save AFTER create_spreadsheet** — it duplicates work and breaks the layout
- **NEVER create spreadsheet in multiple calls** — always ONE `create_spreadsheet` call with ALL data
- **NEVER forget formulas** — if user says "total" or "sum" or "average", include it in the formulas array
- **NEVER use type_in_cell for formulas** — use `enter_formula` instead
- **NEVER forget the title** — always include title so the file gets saved
- **NEVER split create + save** — `create_spreadsheet` saves automatically when title is provided

---

## Dependencies

- Microsoft Excel for Mac (must be installed)
- macOS Accessibility permissions (System Settings → Privacy → Accessibility)
