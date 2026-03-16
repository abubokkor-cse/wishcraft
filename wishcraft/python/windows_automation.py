#!/usr/bin/env python3
"""
WishCraft Windows Automation — Microsoft Word Control via PyAutoGUI
Mirrors all 49 word_* functions from macos_automation.py using Windows keyboard shortcuts.

macOS uses AppleScript (System Events keystroke) → Windows uses PyAutoGUI hotkey().
Key mapping: Cmd → Ctrl, Option → Alt. All shortcuts verified against:
https://support.microsoft.com/en-us/office/keyboard-shortcuts-in-word-95ef89dd-7142-4b50-afb2-f762f663ceb2
"""

import subprocess
import time
import os
import sys
import json
import platform

IS_WIN = platform.system() == 'Windows'

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


def _word_activate():
    """Bring Microsoft Word to the foreground on Windows."""
    if IS_WIN:
        # Use PowerShell to activate Word window
        _run_shell(
            'powershell -Command "'
            '$w = Get-Process WINWORD -ErrorAction SilentlyContinue; '
            'if ($w) { '
            '  Add-Type -TypeDefinition \'using System; using System.Runtime.InteropServices; '
            '  public class W { [DllImport(\"user32.dll\")] public static extern bool SetForegroundWindow(IntPtr h); }\'; '
            '  [W]::SetForegroundWindow($w[0].MainWindowHandle) '
            '}"'
        )
    else:
        # Fallback: use pyautogui to click on Word if it's open
        pass
    time.sleep(0.5)
    return True


def _clipboard_write(text):
    """Write text to the Windows clipboard."""
    if IS_WIN:
        # Use clip.exe via PowerShell for proper Unicode support
        try:
            process = subprocess.Popen(
                ['powershell', '-Command', 'Set-Clipboard', '-Value', text],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            process.communicate(timeout=5)
            return True
        except Exception:
            return False
    else:
        # Linux fallback: xclip
        try:
            process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
            process.communicate(text.encode('utf-8'))
            return True
        except Exception:
            return False


def _clipboard_read():
    """Read text from the Windows clipboard."""
    if IS_WIN:
        ok, out, _ = _run_shell('powershell -Command "Get-Clipboard"')
        return out if ok else ""
    else:
        ok, out, _ = _run_shell('xclip -selection clipboard -o')
        return out if ok else ""


def _clipboard_type(text):
    """Type text by writing to clipboard then pasting with Ctrl+V."""
    if _clipboard_write(text):
        time.sleep(0.15)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.2)
        return True
    return False


# Word Functions — 49 functions matching macos_automation.py

def word_get_document_path():
    """Get the path of the active Word document (via window title)."""
    if IS_WIN:
        ok, out, _ = _run_shell(
            'powershell -Command "'
            '$w = Get-Process WINWORD -ErrorAction SilentlyContinue; '
            'if ($w) { $w[0].MainWindowTitle } else { \'not running\' }"'
        )
        if ok and out and out != 'not running':
            # Window title is usually "Document Name - Word"
            title = out.replace(' - Word', '').replace(' - Microsoft Word', '').strip()
            return {"success": True, "path": title, "note": "Window title (full path requires COM)"}
        return {"success": True, "path": None, "note": "Word not running or no document open"}
    return {"success": False, "error": "Not Windows"}


def word_open():
    """Open Microsoft Word."""
    if IS_WIN:
        ok, out, err = _run_shell('start winword')
    else:
        ok, out, err = _run_shell('xdg-open /usr/bin/libreoffice --writer')
    time.sleep(2.0)
    return {"success": ok, "error": err if not ok else None}


def word_new_document():
    """Create a new blank document (Ctrl+N)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'n')
    time.sleep(1.0)
    return {"success": True}


def word_write(text):
    """Write text into Word at cursor position using clipboard paste."""
    _word_activate()
    time.sleep(0.2)
    success = _clipboard_type(text)
    return {"success": success, "length": len(text)}


def word_keystroke(text, delay_per_char=0.03):
    """Type text character-by-character. Slower but works in dialogs/prompts."""
    _word_activate()
    time.sleep(0.2)
    pyautogui.typewrite(text, interval=delay_per_char) if text.isascii() else _clipboard_type(text)
    return {"success": True, "length": len(text), "method": "keystroke"}


def word_new_line(count=1):
    """Press Enter N times."""
    _word_activate()
    for _ in range(count):
        pyautogui.press('enter')
        time.sleep(0.1)
    return {"success": True, "lines": count}


def word_heading_1():
    """Apply Heading 1 style (Ctrl+Alt+1)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'alt', '1')
    return {"success": True, "style": "Heading 1"}


def word_heading_2():
    """Apply Heading 2 style (Ctrl+Alt+2)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'alt', '2')
    return {"success": True, "style": "Heading 2"}


def word_heading_3():
    """Apply Heading 3 style (Ctrl+Alt+3)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'alt', '3')
    return {"success": True, "style": "Heading 3"}


def word_normal_text():
    """Apply Normal text style (Ctrl+Shift+N)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'shift', 'n')
    return {"success": True, "style": "Normal"}


def word_bold():
    """Toggle bold (Ctrl+B)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'b')
    return {"success": True, "format": "bold"}


def word_italic():
    """Toggle italic (Ctrl+I)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'i')
    return {"success": True, "format": "italic"}


def word_underline():
    """Toggle underline (Ctrl+U)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'u')
    return {"success": True, "format": "underline"}


def word_bullet_list():
    """Toggle bullet list (Ctrl+Shift+L)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'shift', 'l')
    return {"success": True, "format": "bullet_list"}


def word_center_text():
    """Center align text (Ctrl+E)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'e')
    return {"success": True, "align": "center"}


def word_left_text():
    """Left align text (Ctrl+L)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'l')
    return {"success": True, "align": "left"}


def word_right_text():
    """Right align text (Ctrl+R)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'r')
    return {"success": True, "align": "right"}


def word_justify():
    """Justify text (Ctrl+J)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'j')
    return {"success": True, "align": "justify"}


def word_single_space():
    """Single line spacing (Ctrl+1)."""
    _word_activate()
    pyautogui.hotkey('ctrl', '1')
    return {"success": True, "spacing": "single"}


def word_double_space():
    """Double line spacing (Ctrl+2)."""
    _word_activate()
    pyautogui.hotkey('ctrl', '2')
    return {"success": True, "spacing": "double"}


def word_1_5_space():
    """1.5 line spacing (Ctrl+5)."""
    _word_activate()
    pyautogui.hotkey('ctrl', '5')
    return {"success": True, "spacing": "1.5"}


def word_increase_font():
    """Increase font size (Ctrl+Shift+>)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'shift', '.')
    return {"success": True, "action": "increase_font"}


def word_decrease_font():
    """Decrease font size (Ctrl+Shift+<)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'shift', ',')
    return {"success": True, "action": "decrease_font"}


def word_select_all():
    """Select all text (Ctrl+A)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    return {"success": True}


def word_copy():
    """Copy selected text (Ctrl+C)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.2)
    return {"success": True}


def word_paste():
    """Paste from clipboard (Ctrl+V)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.2)
    return {"success": True}


def word_undo():
    """Undo (Ctrl+Z)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'z')
    return {"success": True}


def word_redo():
    """Redo (Ctrl+Y)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'y')
    return {"success": True}


def word_find(text):
    """Open Find and search for text (Ctrl+F)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(0.5)
    _clipboard_type(text)
    time.sleep(0.2)
    pyautogui.press('enter')
    return {"success": True, "find": text}


def word_find_replace(find_text, replace_text):
    """Find and Replace (Ctrl+H)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'h')
    time.sleep(0.5)
    # Find field (should be focused)
    _clipboard_type(find_text)
    time.sleep(0.2)
    # Tab to Replace field
    pyautogui.press('tab')
    time.sleep(0.2)
    _clipboard_type(replace_text)
    return {"success": True, "find": find_text, "replace": replace_text}


def word_save(filename=None):
    """Save document. If filename given, uses Save As (F12)."""
    _word_activate()
    if filename:
        pyautogui.press('f12')
        time.sleep(1.0)
        # Type filename via clipboard
        _clipboard_type(filename)
        time.sleep(0.3)
        # Press Enter to confirm
        pyautogui.press('enter')
        time.sleep(0.5)
        # Handle "replace?" dialog — press Enter again
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(0.5)
        return {"success": True, "saved_as": filename}
    else:
        pyautogui.hotkey('ctrl', 's')
        time.sleep(0.3)
        return {"success": True}


def word_close():
    """Quit Microsoft Word."""
    if IS_WIN:
        _run_shell('taskkill /IM WINWORD.EXE /F')
    else:
        _run_shell('pkill -f "libreoffice.*writer"')
    return {"success": True}


def word_close_document():
    """Close current document (Ctrl+W)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'w')
    return {"success": True}


def word_print():
    """Open print dialog (Ctrl+P)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'p')
    return {"success": True}


def word_clear_all():
    """Clear ALL content — Select All → Delete."""
    _word_activate()
    time.sleep(0.3)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.press('delete')
    time.sleep(0.2)
    return {"success": True, "action": "cleared all content"}


def word_cut():
    """Cut selected text (Ctrl+X)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'x')
    time.sleep(0.2)
    return {"success": True}


def word_read_content():
    """Read ALL content — Select All → Copy → read clipboard."""
    _word_activate()
    time.sleep(0.3)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.3)
    content = _clipboard_read()
    # Deselect by pressing right arrow
    pyautogui.press('right')
    return {"success": True, "content": content, "length": len(content)}


def word_move_to_end():
    """Move cursor to end of document (Ctrl+End)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'end')
    return {"success": True}


def word_move_to_start():
    """Move cursor to beginning of document (Ctrl+Home)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'home')
    return {"success": True}


def word_toggle_case():
    """Cycle case: UPPER → lower → Title (Shift+F3)."""
    _word_activate()
    pyautogui.hotkey('shift', 'f3')
    return {"success": True, "action": "toggle_case"}


def word_upper_case():
    """Toggle all-caps formatting (Ctrl+Shift+A)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'shift', 'a')
    return {"success": True, "format": "upper_case"}


def word_strikethrough():
    """Toggle strikethrough — uses Font dialog (Ctrl+D), Alt+K to toggle, Enter to apply."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'd')
    time.sleep(0.5)
    pyautogui.hotkey('alt', 'k')   # Strikethrough checkbox
    time.sleep(0.2)
    pyautogui.press('enter')       # Apply
    return {"success": True, "format": "strikethrough"}


def word_paste_plain():
    """Paste text without formatting (Ctrl+Shift+V)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'shift', 'v')
    return {"success": True, "action": "paste_plain"}


def word_indent():
    """Indent paragraph (Ctrl+M)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'm')
    return {"success": True, "action": "indent"}


def word_outdent():
    """Remove paragraph indent (Ctrl+Shift+M)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'shift', 'm')
    return {"success": True, "action": "outdent"}


def word_page_break():
    """Insert page break (Ctrl+Enter)."""
    _word_activate()
    pyautogui.hotkey('ctrl', 'enter')
    return {"success": True, "action": "page_break"}


def word_line_break():
    """Insert soft line break (Shift+Enter)."""
    _word_activate()
    pyautogui.hotkey('shift', 'enter')
    return {"success": True, "action": "line_break"}


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
    _word_activate()
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
        _write("\u2014" * 50)  # em dash
        _enter()

    # Title as Heading 1, centered
    word_heading_1()
    time.sleep(0.1)
    word_center_text()
    time.sleep(0.1)
    _write(title.upper() if title == title.lower() else title)
    _enter()

    for section in sections:
        # Centered text (e.g. contact info line)
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

        # Separator line
        if section.get("separator"):
            _separator()
            continue

        # Section heading as Heading 2
        if section.get("heading"):
            word_heading_2()
            time.sleep(0.1)
            word_left_text()
            time.sleep(0.1)
            _write(section["heading"].upper())
            _enter()

        # Bold standalone text
        if section.get("bold_text"):
            word_normal_text()
            time.sleep(0.1)
            word_bold()
            time.sleep(0.1)
            _write(section["bold_text"])
            word_bold()
            time.sleep(0.1)
            _enter()

        # Body text as Normal
        if section.get("text") and not section.get("center"):
            word_normal_text()
            time.sleep(0.1)
            _write(section["text"])
            _enter()

        # Structured items (CV entries: experience, education, projects)
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

        # Bullet items
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


# Dispatcher — same pattern as macos_automation.py

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
}


def execute_automation(action, args=None):
    """Execute a Windows automation action by name."""
    if args is None:
        args = {}

    handler = AUTOMATION_ACTIONS.get(action)
    if handler:
        try:
            return handler(args)
        except Exception as e:
            return {"success": False, "action": action, "error": str(e)}

    return {"success": False, "error": f"Unknown Windows automation action: {action}"}


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
        print(f"Windows Automation — {len(AUTOMATION_ACTIONS)} actions available:")
        for name in list_available_actions():
            print(f"  {name}")
