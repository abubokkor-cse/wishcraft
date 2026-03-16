#!/usr/bin/env python3
"""
WishCraft Linux Automation — LibreOffice Writer Control via PyAutoGUI
Mirrors all word_* functions from macos_automation.py using LibreOffice Writer keyboard shortcuts.

Key differences from MS Word:
  - Heading 1/2/3: Ctrl+1/2/3 (not Ctrl+Alt+1/2/3)
  - Normal text (Body Text): Ctrl+0 (not Ctrl+Shift+N)
  - Bullet list: Shift+F12 (not Ctrl+Shift+L)
  - Save As: Ctrl+Shift+S (not F12)
  - Paste plain: Ctrl+Alt+Shift+V (not Ctrl+Shift+V)
  - Strikethrough: via Format > Character dialog (Alt+H, then navigate)
  - Line spacing: via Format > Paragraph (no direct shortcut like Word)

Shortcuts verified against:
https://help.libreoffice.org/latest/en-US/text/swriter/04/01020000.html
"""

import subprocess
import time
import os
import sys
import json
import platform

SYSTEM = platform.system()
IS_LINUX = SYSTEM == 'Linux'

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.1
except ImportError:
    pyautogui = None


# Helpers

def _run_shell(cmd, timeout=10):
    """Run a shell command. Returns (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd if isinstance(cmd, list) else cmd,
            shell=isinstance(cmd, str),
            capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)


def _writer_activate():
    """Bring LibreOffice Writer to the foreground on Linux."""
    if IS_LINUX:
        _run_shell('xdotool search --name "Writer" windowactivate 2>/dev/null || '
                   'xdotool search --name "LibreOffice" windowactivate 2>/dev/null')
    time.sleep(0.5)
    return True


def _clipboard_write(text):
    """Write text to the Linux clipboard using xclip or xsel."""
    try:
        process = subprocess.Popen(
            ['xclip', '-selection', 'clipboard'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        process.communicate(text.encode('utf-8'), timeout=5)
        return True
    except (FileNotFoundError, Exception):
        try:
            process = subprocess.Popen(
                ['xsel', '--clipboard', '--input'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            process.communicate(text.encode('utf-8'), timeout=5)
            return True
        except Exception:
            return False


def _clipboard_read():
    """Read text from the Linux clipboard."""
    ok, out, _ = _run_shell('xclip -selection clipboard -o 2>/dev/null || xsel --clipboard --output 2>/dev/null')
    return out if ok else ""


def _clipboard_type(text):
    """Type text by writing to clipboard then pasting with Ctrl+V."""
    if _clipboard_write(text):
        time.sleep(0.15)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.2)
        return True
    return False


# Writer Functions — matching macos_automation.py word_* actions
# Using LibreOffice Writer shortcuts

def word_get_document_path():
    """Get the path of the active Writer document (via window title)."""
    ok, out, _ = _run_shell(
        'xdotool getactivewindow getwindowname 2>/dev/null'
    )
    if ok and out:
        title = out.replace(' - LibreOffice Writer', '').replace(' — LibreOffice Writer', '').strip()
        return {"success": True, "path": title, "note": "Window title"}
    return {"success": True, "path": None, "note": "Writer not running or no document open"}


def word_open():
    """Open LibreOffice Writer."""
    try:
        subprocess.Popen(['libreoffice', '--writer'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        subprocess.Popen(['soffice', '--writer'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.0)
    return {"success": True}


def word_new_document():
    """Create a new blank document (Ctrl+N)."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'n')
    time.sleep(1.0)
    return {"success": True}


def word_write(text):
    """Write text into Writer at cursor position using clipboard paste."""
    _writer_activate()
    time.sleep(0.2)
    success = _clipboard_type(text)
    return {"success": success, "length": len(text)}


def word_keystroke(text, delay_per_char=0.03):
    """Type text character-by-character. Slower but works in dialogs."""
    _writer_activate()
    time.sleep(0.2)
    pyautogui.typewrite(text, interval=delay_per_char) if text.isascii() else _clipboard_type(text)
    return {"success": True, "length": len(text), "method": "keystroke"}


def word_new_line(count=1):
    """Press Enter N times."""
    _writer_activate()
    for _ in range(count):
        pyautogui.press('enter')
        time.sleep(0.1)
    return {"success": True, "lines": count}


def word_heading_1():
    """Apply Heading 1 style (Ctrl+1) — LibreOffice shortcut."""
    _writer_activate()
    pyautogui.hotkey('ctrl', '1')
    return {"success": True, "style": "Heading 1"}


def word_heading_2():
    """Apply Heading 2 style (Ctrl+2) — LibreOffice shortcut."""
    _writer_activate()
    pyautogui.hotkey('ctrl', '2')
    return {"success": True, "style": "Heading 2"}


def word_heading_3():
    """Apply Heading 3 style (Ctrl+3) — LibreOffice shortcut."""
    _writer_activate()
    pyautogui.hotkey('ctrl', '3')
    return {"success": True, "style": "Heading 3"}


def word_normal_text():
    """Apply Body Text / Default style (Ctrl+0) — LibreOffice shortcut."""
    _writer_activate()
    pyautogui.hotkey('ctrl', '0')
    return {"success": True, "style": "Body Text"}


def word_bold():
    """Toggle bold (Ctrl+B)."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'b')
    return {"success": True, "format": "bold"}


def word_italic():
    """Toggle italic (Ctrl+I)."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'i')
    return {"success": True, "format": "italic"}


def word_underline():
    """Toggle underline (Ctrl+U)."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'u')
    return {"success": True, "format": "underline"}


def word_bullet_list():
    """Toggle unordered (bullet) list (Shift+F12) — LibreOffice shortcut."""
    _writer_activate()
    pyautogui.hotkey('shift', 'f12')
    return {"success": True, "format": "bullet_list"}


def word_center_text():
    """Center align text (Ctrl+E)."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'e')
    return {"success": True, "align": "center"}


def word_left_text():
    """Left align text (Ctrl+L)."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'l')
    return {"success": True, "align": "left"}


def word_right_text():
    """Right align text (Ctrl+R)."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'r')
    return {"success": True, "align": "right"}


def word_justify():
    """Justify text (Ctrl+J)."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'j')
    return {"success": True, "align": "justify"}


def word_single_space():
    """Single line spacing — via Format > Paragraph > Spacing.
    LibreOffice uses Ctrl+1 for Heading 1, so we use menu approach."""
    _writer_activate()
    # Format > Paragraph > Indents & Spacing tab
    pyautogui.hotkey('alt', 'o')  # Format menu
    time.sleep(0.3)
    pyautogui.press('p')          # Paragraph
    time.sleep(0.5)
    # Navigate to line spacing dropdown and set Single
    pyautogui.hotkey('alt', 'n')  # Line spacing dropdown (mnemonic)
    time.sleep(0.2)
    pyautogui.press('home')       # Go to first option (Single)
    time.sleep(0.1)
    pyautogui.press('enter')      # Select
    time.sleep(0.2)
    pyautogui.press('enter')      # OK
    return {"success": True, "spacing": "single"}


def word_double_space():
    """Double line spacing — via Format > Paragraph."""
    _writer_activate()
    pyautogui.hotkey('alt', 'o')  # Format menu
    time.sleep(0.3)
    pyautogui.press('p')          # Paragraph
    time.sleep(0.5)
    pyautogui.hotkey('alt', 'n')  # Line spacing dropdown
    time.sleep(0.2)
    pyautogui.press('home')
    pyautogui.press('down')       # Double is 2nd option
    time.sleep(0.1)
    pyautogui.press('enter')
    time.sleep(0.2)
    pyautogui.press('enter')      # OK
    return {"success": True, "spacing": "double"}


def word_1_5_space():
    """1.5 line spacing — via Format > Paragraph."""
    _writer_activate()
    pyautogui.hotkey('alt', 'o')  # Format menu
    time.sleep(0.3)
    pyautogui.press('p')          # Paragraph
    time.sleep(0.5)
    pyautogui.hotkey('alt', 'n')  # Line spacing dropdown
    time.sleep(0.2)
    pyautogui.press('home')
    pyautogui.press('down')
    pyautogui.press('down')       # 1.5 lines is 3rd option
    time.sleep(0.1)
    pyautogui.press('enter')
    time.sleep(0.2)
    pyautogui.press('enter')      # OK
    return {"success": True, "spacing": "1.5"}


def word_increase_font():
    """Increase font size (Ctrl+])  — LibreOffice shortcut."""
    _writer_activate()
    pyautogui.hotkey('ctrl', ']')
    return {"success": True, "action": "increase_font"}


def word_decrease_font():
    """Decrease font size (Ctrl+[) — LibreOffice shortcut."""
    _writer_activate()
    pyautogui.hotkey('ctrl', '[')
    return {"success": True, "action": "decrease_font"}


def word_select_all():
    """Select all text (Ctrl+A)."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    return {"success": True}


def word_copy():
    """Copy selected text (Ctrl+C)."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.2)
    return {"success": True}


def word_paste():
    """Paste from clipboard (Ctrl+V)."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.2)
    return {"success": True}


def word_undo():
    """Undo (Ctrl+Z)."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'z')
    return {"success": True}


def word_redo():
    """Redo (Ctrl+Y)."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'y')
    return {"success": True}


def word_find(text):
    """Open Find toolbar and search for text (Ctrl+F)."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(0.5)
    _clipboard_type(text)
    time.sleep(0.2)
    pyautogui.press('enter')
    return {"success": True, "find": text}


def word_find_replace(find_text, replace_text):
    """Find and Replace (Ctrl+H)."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'h')
    time.sleep(0.5)
    _clipboard_type(find_text)
    time.sleep(0.2)
    pyautogui.press('tab')
    time.sleep(0.2)
    _clipboard_type(replace_text)
    return {"success": True, "find": find_text, "replace": replace_text}


def word_save(filename=None):
    """Save document. If filename given, uses Save As (Ctrl+Shift+S)."""
    _writer_activate()
    if filename:
        pyautogui.hotkey('ctrl', 'shift', 's')
        time.sleep(1.0)
        _clipboard_type(filename)
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(0.5)
        # Handle "replace?" or format dialogs
        pyautogui.press('enter')
        time.sleep(0.5)
        return {"success": True, "saved_as": filename}
    else:
        pyautogui.hotkey('ctrl', 's')
        time.sleep(0.3)
        # Handle "Keep Current Format" dialog if saving .docx
        pyautogui.press('enter')
        time.sleep(0.3)
        return {"success": True}


def word_close():
    """Quit LibreOffice Writer."""
    _run_shell('pkill -f "soffice.*writer" 2>/dev/null; pkill -f libreoffice 2>/dev/null')
    return {"success": True}


def word_close_document():
    """Close current document (Ctrl+W)."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'w')
    time.sleep(0.3)
    # Handle "Save changes?" dialog — press Don't Save (Tab then Enter or D)
    pyautogui.press('tab')
    time.sleep(0.1)
    pyautogui.press('enter')
    return {"success": True}


def word_print():
    """Open print dialog (Ctrl+P)."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'p')
    return {"success": True}


def word_clear_all():
    """Clear ALL content — Select All then Delete."""
    _writer_activate()
    time.sleep(0.3)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.press('delete')
    time.sleep(0.2)
    return {"success": True, "action": "cleared all content"}


def word_cut():
    """Cut selected text (Ctrl+X)."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'x')
    time.sleep(0.2)
    return {"success": True}


def word_read_content():
    """Read ALL content — Select All, Copy, read clipboard."""
    _writer_activate()
    time.sleep(0.3)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.3)
    content = _clipboard_read()
    pyautogui.press('right')
    return {"success": True, "content": content, "length": len(content)}


def word_move_to_end():
    """Move cursor to end of document (Ctrl+End)."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'end')
    return {"success": True}


def word_move_to_start():
    """Move cursor to beginning of document (Ctrl+Home)."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'home')
    return {"success": True}


def word_toggle_case():
    """Cycle case — via Format > Text > Change Case > Cycle.
    LibreOffice has no direct Shift+F3 like Word. Uses menu."""
    _writer_activate()
    pyautogui.hotkey('alt', 'o')  # Format menu
    time.sleep(0.3)
    pyautogui.press('x')          # Text submenu
    time.sleep(0.3)
    pyautogui.press('c')          # Cycle Case
    return {"success": True, "action": "toggle_case"}


def word_upper_case():
    """Convert to UPPERCASE — via Format > Text > UPPERCASE."""
    _writer_activate()
    pyautogui.hotkey('alt', 'o')  # Format menu
    time.sleep(0.3)
    pyautogui.press('x')          # Text submenu
    time.sleep(0.3)
    pyautogui.press('u')          # UPPERCASE
    return {"success": True, "format": "upper_case"}


def word_strikethrough():
    """Toggle strikethrough — via Format > Character > Font Effects tab."""
    _writer_activate()
    pyautogui.hotkey('alt', 'o')  # Format menu
    time.sleep(0.3)
    pyautogui.press('h')          # Character
    time.sleep(0.5)
    # Switch to Font Effects tab
    pyautogui.hotkey('alt', 'e')  # Font Effects tab (if not already)
    time.sleep(0.3)
    # Tab to Strikethrough dropdown and toggle
    pyautogui.hotkey('alt', 'k')  # Strikethrough field
    time.sleep(0.2)
    pyautogui.press('down')       # Select Single strikethrough
    time.sleep(0.1)
    pyautogui.press('enter')      # Apply
    time.sleep(0.2)
    pyautogui.press('enter')      # OK
    return {"success": True, "format": "strikethrough"}


def word_paste_plain():
    """Paste text without formatting (Ctrl+Alt+Shift+V) — LibreOffice shortcut."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'alt', 'shift', 'v')
    return {"success": True, "action": "paste_plain"}


def word_indent():
    """Increase indent (Tab key in list context, or Format > Paragraph)."""
    _writer_activate()
    pyautogui.press('tab')
    return {"success": True, "action": "indent"}


def word_outdent():
    """Decrease indent (Shift+Tab)."""
    _writer_activate()
    pyautogui.hotkey('shift', 'tab')
    return {"success": True, "action": "outdent"}


def word_page_break():
    """Insert manual page break (Ctrl+Enter) — LibreOffice shortcut."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'enter')
    return {"success": True, "action": "page_break"}


def word_line_break():
    """Insert soft line break without paragraph change (Shift+Enter)."""
    _writer_activate()
    pyautogui.hotkey('shift', 'enter')
    return {"success": True, "action": "line_break"}


def word_ordered_list():
    """Toggle ordered (numbered) list (F12) — LibreOffice-specific."""
    _writer_activate()
    pyautogui.press('f12')
    return {"success": True, "format": "ordered_list"}


def word_superscript():
    """Toggle superscript (Ctrl+Shift+P) — LibreOffice shortcut."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'shift', 'p')
    return {"success": True, "format": "superscript"}


def word_subscript():
    """Toggle subscript (Ctrl+Shift+B) — LibreOffice shortcut."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'shift', 'b')
    return {"success": True, "format": "subscript"}


def word_double_underline():
    """Toggle double underline (Ctrl+D) — LibreOffice-specific shortcut."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'd')
    return {"success": True, "format": "double_underline"}


def word_spelling():
    """Open spell check (F7)."""
    _writer_activate()
    pyautogui.press('f7')
    return {"success": True, "action": "spelling"}


def word_thesaurus():
    """Open thesaurus (Ctrl+F7)."""
    _writer_activate()
    pyautogui.hotkey('ctrl', 'f7')
    return {"success": True, "action": "thesaurus"}


def word_write_formatted_document(title, sections):
    """
    Write a complete formatted document in one call.
    title: string — document title (Heading 1)
    sections: list of dicts, each with:
      - heading: str (optional, becomes Heading 2)
      - text: str (body text, Normal style)
      - bullet_items: list of str (optional, each becomes a bullet point)
      - center: bool (optional, center the text/heading)
      - bold_text: str (optional, bold text on its own line)
      - separator: bool (optional, adds a horizontal line)
      - items: list of dicts (optional, for structured entries like CV)
        Each item: {left: str, right: str, subleft: str, subright: str, details: [str]}
    """
    _writer_activate()
    time.sleep(0.3)

    def _enter():
        pyautogui.press('enter')
        time.sleep(0.1)

    def _write(text):
        _clipboard_type(text)
        time.sleep(0.1)

    def _separator():
        word_normal_text()
        time.sleep(0.1)
        _write("\u2014" * 50)
        _enter()

    # Title as Heading 1, centered
    word_heading_1()
    time.sleep(0.1)
    word_center_text()
    time.sleep(0.1)
    _write(title.upper() if title == title.lower() else title)
    _enter()

    for section in sections:
        if section.get("center") and section.get("text") and not section.get("heading"):
            word_normal_text()
            time.sleep(0.1)
            word_center_text()
            time.sleep(0.1)
            _write(section["text"])
            _enter()
            word_left_text()
            time.sleep(0.1)
            continue

        if section.get("separator"):
            _separator()
            continue

        if section.get("heading"):
            word_heading_2()
            time.sleep(0.1)
            word_left_text()
            time.sleep(0.1)
            _write(section["heading"].upper())
            _enter()

        if section.get("bold_text"):
            word_normal_text()
            time.sleep(0.1)
            word_bold()
            time.sleep(0.1)
            _write(section["bold_text"])
            word_bold()
            time.sleep(0.1)
            _enter()

        if section.get("text") and not section.get("center"):
            word_normal_text()
            time.sleep(0.1)
            _write(section["text"])
            _enter()

        if section.get("items"):
            for item in section["items"]:
                word_normal_text()
                time.sleep(0.1)

                left = item.get("left", "")
                right = item.get("right", "")
                if left and right:
                    word_bold()
                    time.sleep(0.1)
                    _write(left)
                    word_bold()
                    time.sleep(0.1)
                    _write("  |  " + right)
                    _enter()
                elif left:
                    word_bold()
                    time.sleep(0.1)
                    _write(left)
                    word_bold()
                    time.sleep(0.1)
                    _enter()

                subleft = item.get("subleft", "")
                subright = item.get("subright", "")
                if subleft:
                    word_italic()
                    time.sleep(0.1)
                    line = subleft
                    if subright:
                        line += "  |  " + subright
                    _write(line)
                    word_italic()
                    time.sleep(0.1)
                    _enter()

                if item.get("details"):
                    word_bullet_list()
                    time.sleep(0.1)
                    for detail in item["details"]:
                        _write(detail)
                        _enter()
                    word_bullet_list()
                    time.sleep(0.1)

        if section.get("bullet_items"):
            word_normal_text()
            time.sleep(0.1)
            word_bullet_list()
            time.sleep(0.1)
            for item in section["bullet_items"]:
                _write(item)
                _enter()
            word_bullet_list()
            time.sleep(0.1)

    return {"success": True, "title": title, "sections": len(sections)}


# Dispatcher — same pattern as macos_automation.py / windows_automation.py

AUTOMATION_ACTIONS = {
    "word_get_document_path": lambda args: word_get_document_path(),
    "word_open": lambda args: word_open(),
    "word_new_document": lambda args: word_new_document(),
    "word_write": lambda args: word_write(args.get("text", "")),
    "word_new_line": lambda args: word_new_line(args.get("count", 1)),
    "word_heading_1": lambda args: word_heading_1(),
    "word_heading_2": lambda args: word_heading_2(),
    "word_heading_3": lambda args: word_heading_3(),
    "word_normal_text": lambda args: word_normal_text(),
    "word_bold": lambda args: word_bold(),
    "word_italic": lambda args: word_italic(),
    "word_underline": lambda args: word_underline(),
    "word_bullet_list": lambda args: word_bullet_list(),
    "word_center_text": lambda args: word_center_text(),
    "word_left_text": lambda args: word_left_text(),
    "word_right_text": lambda args: word_right_text(),
    "word_justify": lambda args: word_justify(),
    "word_single_space": lambda args: word_single_space(),
    "word_double_space": lambda args: word_double_space(),
    "word_1_5_space": lambda args: word_1_5_space(),
    "word_increase_font": lambda args: word_increase_font(),
    "word_decrease_font": lambda args: word_decrease_font(),
    "word_select_all": lambda args: word_select_all(),
    "word_copy": lambda args: word_copy(),
    "word_paste": lambda args: word_paste(),
    "word_undo": lambda args: word_undo(),
    "word_redo": lambda args: word_redo(),
    "word_find": lambda args: word_find(args.get("text", "")),
    "word_find_replace": lambda args: word_find_replace(args.get("find_text", ""), args.get("replace_text", "")),
    "word_save": lambda args: word_save(args.get("filename")),
    "word_close": lambda args: word_close(),
    "word_close_document": lambda args: word_close_document(),
    "word_print": lambda args: word_print(),
    "word_clear_all": lambda args: word_clear_all(),
    "word_cut": lambda args: word_cut(),
    "word_read_content": lambda args: word_read_content(),
    "word_move_to_end": lambda args: word_move_to_end(),
    "word_move_to_start": lambda args: word_move_to_start(),
    "word_write_formatted_document": lambda args: word_write_formatted_document(args.get("title", ""), args.get("sections", [])),
    "word_keystroke": lambda args: word_keystroke(args.get("text", ""), args.get("delay_per_char", 0.03)),
    "word_toggle_case": lambda args: word_toggle_case(),
    "word_upper_case": lambda args: word_upper_case(),
    "word_strikethrough": lambda args: word_strikethrough(),
    "word_paste_plain": lambda args: word_paste_plain(),
    "word_indent": lambda args: word_indent(),
    "word_outdent": lambda args: word_outdent(),
    "word_page_break": lambda args: word_page_break(),
    "word_line_break": lambda args: word_line_break(),
    # LibreOffice-specific extras
    "word_ordered_list": lambda args: word_ordered_list(),
    "word_superscript": lambda args: word_superscript(),
    "word_subscript": lambda args: word_subscript(),
    "word_double_underline": lambda args: word_double_underline(),
    "word_spelling": lambda args: word_spelling(),
    "word_thesaurus": lambda args: word_thesaurus(),
}


def execute_automation(action, args=None):
    """Execute a Linux automation action by name."""
    if args is None:
        args = {}

    handler = AUTOMATION_ACTIONS.get(action)
    if handler:
        try:
            return handler(args)
        except Exception as e:
            return {"success": False, "action": action, "error": str(e)}

    return {"success": False, "error": f"Unknown Linux automation action: {action}"}


def list_available_actions():
    """Return all available action names."""
    return sorted(AUTOMATION_ACTIONS.keys())


if __name__ == '__main__':
    if len(sys.argv) > 1:
        action = sys.argv[1]
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
        result = execute_automation(action, args)
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"Linux Automation (LibreOffice Writer) — {len(AUTOMATION_ACTIONS)} actions available:")
        for name in list_available_actions():
            print(f"  {name}")
