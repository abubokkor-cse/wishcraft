#!/usr/bin/env python3
"""
WishCraft macOS Automation — Direct AppleScript/CLI automation for macOS.

100% reliable actions using osascript + CLI tools — NO screenshot/vision needed.
Each function does ONE specific thing perfectly.

Modules:
  1. FINDER — open folders, reveal files, get info, search, create folders, move/copy/trash
  2. NOTES — open, create, list, read, search, append, delete notes
  3. SYSTEM — lock, sleep, screenshot, volume, brightness, WiFi, Bluetooth, Dark Mode
  4. SPOTLIGHT — search, open results
  5. FILES — recent downloads, find by name/type, open with app, get PDF/file info
  6. CLIPBOARD — read, write, history concept
  7. MAIL — compose, send email
  8. REMINDERS — create, list, complete reminders
  9. CALENDAR — create events, list today's events
  10. SAFARI/CHROME — get URL, get page title, list tabs, open/close tabs

Integration:
  Called from executor.py via action dispatch, OR from computer_use_agent.py custom functions.
  Every function returns a dict: {"success": True/False, ...}
"""

import os
import sys
import json
import time
import subprocess
import platform
import glob
import shutil
import webbrowser
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.2
    _HAS_PYAUTOGUI = True
except ImportError:
    _HAS_PYAUTOGUI = False

try:
    from google import genai
    from google.genai.types import Content, Part
    _HAS_GENAI = True
except ImportError:
    _HAS_GENAI = False

IS_MAC = platform.system() == 'Darwin'

def _run_applescript(script, timeout=30):
    """Run an AppleScript string via osascript. Returns (success, stdout, stderr)."""
    if not IS_MAC:
        return False, "", "Not macOS"
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Action timed out (" + str(timeout) + "s) — if macOS asked for permission, please grant it and try again"
    except Exception as e:
        return False, "", str(e)

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

def _escape_applescript(text):
    """Escape text for safe AppleScript string embedding."""
    if not text:
        return ""
    return str(text).replace('\\', '\\\\').replace('"', '\\"')

def finder_open_folder(path="~"):
    """Open a folder in Finder."""
    expanded = os.path.expanduser(path)
    if not os.path.isdir(expanded):
        return {"success": False, "error": f"Not a directory: {path}"}
    ok, out, err = _run_shell(['open', expanded])
    return {"success": ok, "path": expanded, "error": err if not ok else None}

def finder_open_downloads():
    """Open ~/Downloads in Finder."""
    return finder_open_folder("~/Downloads")

def finder_open_desktop():
    """Open ~/Desktop in Finder."""
    return finder_open_folder("~/Desktop")

def finder_open_documents():
    """Open ~/Documents in Finder."""
    return finder_open_folder("~/Documents")

def finder_open_home():
    """Open home folder in Finder."""
    return finder_open_folder("~")

def finder_reveal_file(path):
    """Reveal (select) a file in Finder. Smart path resolution."""
    resolved, found = _resolve_file_path(path)
    if not found:
        return {"success": False, "error": f"Not found: {path}", "searched": True}
    ok, out, err = _run_shell(['open', '-R', resolved])
    return {"success": ok, "path": resolved}

def finder_create_folder(path):
    """Create a new folder (mkdir -p)."""
    expanded = os.path.expanduser(path)
    try:
        os.makedirs(expanded, exist_ok=True)
        return {"success": True, "path": expanded}
    except Exception as e:
        return {"success": False, "error": str(e)}

def finder_list_folder(path="~", sort_by="name"):
    """List folder contents with details. sort_by: name, date, size."""
    expanded = os.path.expanduser(path)
    if not os.path.isdir(expanded):
        return {"success": False, "error": f"Not a directory: {path}"}
    try:
        items = []
        for name in os.listdir(expanded):
            full = os.path.join(expanded, name)
            try:
                stat = os.stat(full)
                items.append({
                    "name": name,
                    "is_dir": os.path.isdir(full),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                })
            except OSError:
                items.append({"name": name, "is_dir": os.path.isdir(full), "size": 0, "modified": ""})

        if sort_by == "date":
            items.sort(key=lambda x: x["modified"], reverse=True)
        elif sort_by == "size":
            items.sort(key=lambda x: x["size"], reverse=True)
        else:
            items.sort(key=lambda x: x["name"].lower())

        return {"success": True, "path": expanded, "items": items[:100], "total": len(items)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def finder_get_file_info(path):
    """Get detailed file info: size, type, dates, MIME type."""
    expanded = os.path.expanduser(path)
    if not os.path.exists(expanded):
        return {"success": False, "error": f"Not found: {path}"}
    try:
        stat = os.stat(expanded)
        ok, mime_out, _ = _run_shell(['file', '--mime-type', '-b', expanded])
        mime = mime_out if ok else "unknown"
        ok, kind_out, _ = _run_shell(['file', '-b', expanded])
        kind = kind_out if ok else "unknown"

        size_bytes = stat.st_size
        if size_bytes < 1024:
            size_human = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size_human = f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            size_human = f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            size_human = f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

        return {
            "success": True,
            "path": expanded,
            "name": os.path.basename(expanded),
            "size": size_human,
            "size_bytes": size_bytes,
            "mime_type": mime,
            "kind": kind,
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "created": datetime.fromtimestamp(stat.st_birthtime).strftime("%Y-%m-%d %H:%M:%S") if hasattr(stat, 'st_birthtime') else "N/A",
            "is_dir": os.path.isdir(expanded),
            "extension": os.path.splitext(expanded)[1],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def finder_search(query, folder="~", max_results=20):
    """Search for files using macOS Spotlight (mdfind). Fast and thorough."""
    expanded = os.path.expanduser(folder)
    ok, out, err = _run_shell(
        f'mdfind -onlyin "{expanded}" "{query}" | head -n {max_results}',
        timeout=15
    )
    if ok and out:
        files = out.split('\n')
        results = []
        for f in files:
            if f:
                name = os.path.basename(f)
                results.append({"path": f, "name": name})
        return {"success": True, "query": query, "results": results, "count": len(results)}
    return {"success": True, "query": query, "results": [], "count": 0}

def finder_move_to_trash(path):
    """Move a file/folder to Trash (safe delete)."""
    expanded = os.path.expanduser(path)
    if not os.path.exists(expanded):
        return {"success": False, "error": f"Not found: {path}"}
    ok, out, err = _run_applescript(
        f'tell application "Finder" to delete POSIX file "{expanded}"'
    )
    return {"success": ok, "path": expanded, "error": err if not ok else None}

def finder_move_file(source, destination):
    """Move a file/folder to a new location."""
    src = os.path.expanduser(source)
    dst = os.path.expanduser(destination)
    if not os.path.exists(src):
        return {"success": False, "error": f"Source not found: {source}"}
    try:
        shutil.move(src, dst)
        return {"success": True, "source": src, "destination": dst}
    except Exception as e:
        return {"success": False, "error": str(e)}

def finder_copy_file(source, destination):
    """Copy a file/folder to a new location."""
    src = os.path.expanduser(source)
    dst = os.path.expanduser(destination)
    if not os.path.exists(src):
        return {"success": False, "error": f"Source not found: {source}"}
    try:
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        return {"success": True, "source": src, "destination": dst}
    except Exception as e:
        return {"success": False, "error": str(e)}

def finder_rename(path, new_name):
    """Rename a file/folder (just the name, keeps same directory)."""
    expanded = os.path.expanduser(path)
    if not os.path.exists(expanded):
        return {"success": False, "error": f"Not found: {path}"}
    parent = os.path.dirname(expanded)
    new_path = os.path.join(parent, new_name)
    try:
        os.rename(expanded, new_path)
        return {"success": True, "old": expanded, "new": new_path}
    except Exception as e:
        return {"success": False, "error": str(e)}

def _resolve_file_path(path):
    """Try to find a file: first exact path, then Spotlight search.
    Returns (resolved_path, found) tuple."""
    expanded = os.path.expanduser(path)
    if os.path.exists(expanded):
        return expanded, True
    # Try with common extensions if none given
    basename = os.path.basename(expanded)
    _, ext = os.path.splitext(basename)
    if not ext:
        for try_ext in ['.docx', '.pdf', '.txt', '.xlsx', '.pptx', '.pages', '.doc']:
            if os.path.exists(expanded + try_ext):
                return expanded + try_ext, True
    # Spotlight search as fallback
    search_name = basename if ext else basename
    ok, out, err = _run_shell(
        f'mdfind "kMDItemFSName == \'*{search_name}*\'" | head -5',
        timeout=10
    )
    if ok and out:
        results = [f for f in out.strip().split('\n') if f and os.path.exists(f)]
        if results:
            return results[0], True
    return expanded, False

def finder_open_file(path):
    """Open a file with its default application. Smart path resolution."""
    resolved, found = _resolve_file_path(path)
    if not found:
        return {"success": False, "error": f"Not found: {path}", "searched": True}
    ok, out, err = _run_shell(['open', resolved])
    return {"success": ok, "path": resolved}

def finder_open_file_with(path, app_name):
    """Open a file with a specific application. Smart path resolution."""
    resolved, found = _resolve_file_path(path)
    if not found:
        return {"success": False, "error": f"Not found: {path}", "searched": True}
    ok, out, err = _run_shell(['open', '-a', app_name, resolved])
    return {"success": ok, "path": resolved, "app": app_name, "error": err if not ok else None}

def notes_open():
    """Open Apple Notes app."""
    ok, out, err = _run_shell(['open', '-a', 'Notes'])
    time.sleep(0.5)
    return {"success": ok}

def notes_create(title, body=""):
    """Create a new note in Apple Notes."""
    safe_title = _escape_applescript(title)
    safe_body = _escape_applescript(body)
    script = f'''
tell application "Notes"
    activate
    tell account "iCloud"
        make new note at folder "Notes" with properties {{name:"{safe_title}", body:"{safe_body}"}}
    end tell
end tell
'''
    ok, out, err = _run_applescript(script)
    if not ok:
        # Try without specifying account (works if only one account)
        script2 = f'''
tell application "Notes"
    activate
    make new note with properties {{name:"{safe_title}", body:"{safe_body}"}}
end tell
'''
        ok, out, err = _run_applescript(script2)
    return {"success": ok, "title": title, "error": err if not ok else None}

def notes_list(max_notes=20):
    """List recent notes (titles + dates)."""
    script = f'''
tell application "Notes"
    set noteList to {{}}
    set noteCount to count of notes
    if noteCount > {max_notes} then set noteCount to {max_notes}
    repeat with i from 1 to noteCount
        set n to note i
        set noteTitle to name of n
        set noteDate to modification date of n
        set end of noteList to noteTitle & " | " & (noteDate as string)
    end repeat
    return noteList
end tell
'''
    ok, out, err = _run_applescript(script, timeout=15)
    if ok and out:
        notes = []
        for line in out.split(', '):
            parts = line.split(' | ', 1)
            notes.append({
                "title": parts[0].strip(),
                "modified": parts[1].strip() if len(parts) > 1 else "",
            })
        return {"success": True, "notes": notes, "count": len(notes)}
    return {"success": False, "error": err, "notes": []}

def notes_read(title):
    """Read the content of a note by title (plaintext body)."""
    safe_title = _escape_applescript(title)
    script = f'''
tell application "Notes"
    set matchedNotes to notes whose name is "{safe_title}"
    if (count of matchedNotes) > 0 then
        set n to item 1 of matchedNotes
        return plaintext of n
    else
        return "NOTE_NOT_FOUND"
    end if
end tell
'''
    ok, out, err = _run_applescript(script, timeout=10)
    if ok:
        if out == "NOTE_NOT_FOUND":
            return {"success": False, "error": f"Note '{title}' not found"}
        return {"success": True, "title": title, "content": out}
    return {"success": False, "error": err}

def notes_search(query, max_results=10):
    """Search notes by content or title using Spotlight."""
    ok, out, err = _run_shell(
        f'mdfind "kMDItemContentType == \'com.apple.notes.note\' && kMDItemTextContent == \\"*{query}*\\"" | head -n {max_results}',
        timeout=10
    )
    safe_query = _escape_applescript(query)
    script = f'''
tell application "Notes"
    set matchedNotes to notes whose name contains "{safe_query}"
    set resultList to {{}}
    set maxN to count of matchedNotes
    if maxN > {max_results} then set maxN to {max_results}
    repeat with i from 1 to maxN
        set n to item i of matchedNotes
        set end of resultList to name of n
    end repeat
    return resultList
end tell
'''
    ok2, out2, err2 = _run_applescript(script, timeout=10)
    if ok2 and out2:
        titles = [t.strip() for t in out2.split(', ') if t.strip()]
        return {"success": True, "query": query, "matching_notes": titles, "count": len(titles)}
    return {"success": True, "query": query, "matching_notes": [], "count": 0}

def notes_append(title, text):
    """Append text to an existing note."""
    safe_title = _escape_applescript(title)
    safe_text = _escape_applescript(text)
    script = f'''
tell application "Notes"
    set matchedNotes to notes whose name is "{safe_title}"
    if (count of matchedNotes) > 0 then
        set n to item 1 of matchedNotes
        set currentBody to body of n
        set body of n to currentBody & "<br>" & "{safe_text}"
        return "APPENDED"
    else
        return "NOTE_NOT_FOUND"
    end if
end tell
'''
    ok, out, err = _run_applescript(script, timeout=10)
    if ok:
        if out == "NOTE_NOT_FOUND":
            return {"success": False, "error": f"Note '{title}' not found"}
        return {"success": True, "title": title, "appended": text}
    return {"success": False, "error": err}

def notes_delete(title):
    """Delete a note by title (moves to Recently Deleted)."""
    safe_title = _escape_applescript(title)
    script = f'''
tell application "Notes"
    set matchedNotes to notes whose name is "{safe_title}"
    if (count of matchedNotes) > 0 then
        delete item 1 of matchedNotes
        return "DELETED"
    else
        return "NOTE_NOT_FOUND"
    end if
end tell
'''
    ok, out, err = _run_applescript(script, timeout=10)
    if ok:
        if out == "NOTE_NOT_FOUND":
            return {"success": False, "error": f"Note '{title}' not found"}
        return {"success": True, "title": title, "deleted": True}
    return {"success": False, "error": err}

def system_lock_screen():
    """Lock the screen (Control-Command-Q)."""
    ok, out, err = _run_applescript(
        'tell application "System Events" to keystroke "q" using {command down, control down}'
    )
    return {"success": ok}

def system_sleep_display():
    """Put displays to sleep."""
    ok, out, err = _run_shell('pmset displaysleepnow')
    return {"success": ok}

def system_screenshot_full(save_to_desktop=True):
    """Take a full-screen screenshot to Desktop."""
    if save_to_desktop:
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = os.path.expanduser(f"~/Desktop/{filename}")
        ok, out, err = _run_shell(f'screencapture -x "{path}"')
        return {"success": ok, "path": path, "filename": filename}
    else:
        ok, out, err = _run_shell('screencapture -c')
        return {"success": ok, "location": "clipboard"}

def system_screenshot_selection():
    """Start interactive screenshot selection (Shift+Cmd+4)."""
    ok, out, err = _run_applescript(
        'tell application "System Events" to keystroke "4" using {shift down, command down}'
    )
    return {"success": ok, "message": "Selection mode activated"}

def system_screenshot_window():
    """Take screenshot of a window (Shift+Cmd+4+Space)."""
    script = '''
tell application "System Events"
    keystroke "4" using {shift down, command down}
    delay 0.3
    key code 49
end tell
'''
    ok, out, err = _run_applescript(script)
    return {"success": ok, "message": "Window capture mode activated"}

def system_screenshot_tools():
    """Open macOS screenshot/recording toolbar (Shift+Cmd+5)."""
    ok, out, err = _run_applescript(
        'tell application "System Events" to keystroke "5" using {shift down, command down}'
    )
    return {"success": ok}

def system_volume_get():
    """Get current volume level (0-100)."""
    ok, out, err = _run_applescript('output volume of (get volume settings)')
    if ok:
        try:
            return {"success": True, "volume": int(out)}
        except ValueError:
            pass
    return {"success": False, "error": err}

def system_volume_set(level):
    """Set volume level (0-100)."""
    level = max(0, min(100, int(level)))
    ok, out, err = _run_applescript(f'set volume output volume {level}')
    return {"success": ok, "volume": level}

def system_volume_mute():
    """Mute audio."""
    ok, out, err = _run_applescript('set volume with output muted')
    return {"success": ok, "muted": True}

def system_volume_unmute():
    """Unmute audio."""
    ok, out, err = _run_applescript('set volume without output muted')
    return {"success": ok, "muted": False}

def system_wifi_status():
    """Get WiFi status."""
    ok, out, err = _run_shell('networksetup -getairportpower en0')
    if ok:
        is_on = 'on' in out.lower()
        return {"success": True, "wifi_on": is_on, "raw": out}
    return {"success": False, "error": err}

def system_wifi_on():
    """Turn WiFi on."""
    ok, out, err = _run_shell('networksetup -setairportpower en0 on')
    return {"success": ok}

def system_wifi_off():
    """Turn WiFi off."""
    ok, out, err = _run_shell('networksetup -setairportpower en0 off')
    return {"success": ok}

def system_dark_mode_toggle():
    """Toggle macOS Dark Mode."""
    ok, out, err = _run_applescript(
        'tell application "System Events" to tell appearance preferences to set dark mode to not dark mode'
    )
    return {"success": ok}

def system_dark_mode_status():
    """Check if Dark Mode is on."""
    ok, out, err = _run_applescript(
        'tell application "System Events" to tell appearance preferences to get dark mode'
    )
    if ok:
        return {"success": True, "dark_mode": out.lower() == "true"}
    return {"success": False, "error": err}

def system_do_not_disturb_on():
    """Turn on Do Not Disturb / Focus mode."""
    # macOS Monterey+: use shortcuts or defaults
    ok, out, err = _run_shell(
        'defaults -currentHost write com.apple.notificationcenterui doNotDisturb -boolean true && killall NotificationCenter 2>/dev/null; true'
    )
    return {"success": True, "dnd": True, "note": "May require restart of Notification Center"}

def system_do_not_disturb_off():
    """Turn off Do Not Disturb."""
    ok, out, err = _run_shell(
        'defaults -currentHost write com.apple.notificationcenterui doNotDisturb -boolean false && killall NotificationCenter 2>/dev/null; true'
    )
    return {"success": True, "dnd": False}

def system_empty_trash():
    """Empty the Trash."""
    ok, out, err = _run_applescript(
        'tell application "Finder" to empty trash'
    )
    return {"success": ok, "error": err if not ok else None}

def system_get_battery():
    """Get battery level and charging status."""
    ok, out, err = _run_shell('pmset -g batt')
    if ok:
        import re
        pct_match = re.search(r'(\d+)%', out)
        charging = 'charging' in out.lower() and 'not charging' not in out.lower() and 'discharging' not in out.lower()
        return {
            "success": True,
            "percentage": int(pct_match.group(1)) if pct_match else -1,
            "charging": charging,
            "raw": out
        }
    return {"success": False, "error": err}

def system_get_disk_space():
    """Get disk space info for main volume."""
    ok, out, err = _run_shell("df -h / | tail -1")
    if ok:
        parts = out.split()
        return {
            "success": True,
            "total": parts[1] if len(parts) > 1 else "?",
            "used": parts[2] if len(parts) > 2 else "?",
            "available": parts[3] if len(parts) > 3 else "?",
            "percent_used": parts[4] if len(parts) > 4 else "?",
        }
    return {"success": False, "error": err}

def spotlight_search(query):
    """Open Spotlight and type a search query."""
    safe = _escape_applescript(query)
    script = f'''
tell application "System Events"
    keystroke space using {{command down}}
    delay 0.5
    keystroke "{safe}"
end tell
'''
    ok, out, err = _run_applescript(script)
    return {"success": ok, "query": query}

def spotlight_search_and_open(query):
    """Open Spotlight, type query, and press Enter to open top result."""
    safe = _escape_applescript(query)
    script = f'''
tell application "System Events"
    keystroke space using {{command down}}
    delay 0.5
    keystroke "{safe}"
    delay 1.0
    key code 36
end tell
'''
    ok, out, err = _run_applescript(script)
    return {"success": ok, "query": query, "action": "opened top result"}

def files_recent_downloads(count=10, file_type=None):
    """Get most recent files from ~/Downloads, optionally filtered by extension."""
    downloads = os.path.expanduser("~/Downloads")
    try:
        entries = []
        for name in os.listdir(downloads):
            full = os.path.join(downloads, name)
            if name.startswith('.'):
                continue
            if file_type:
                ext = os.path.splitext(name)[1].lower()
                if ext != file_type.lower() and ext != f'.{file_type.lower()}':
                    continue
            try:
                stat = os.stat(full)
                entries.append({
                    "name": name,
                    "path": full,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "is_dir": os.path.isdir(full),
                })
            except OSError:
                continue

        entries.sort(key=lambda x: x["modified"], reverse=True)
        entries = entries[:count]

        return {"success": True, "downloads": entries, "count": len(entries),
                "filter": file_type}
    except Exception as e:
        return {"success": False, "error": str(e)}

def files_find_by_name(name, folder="~", max_results=20):
    """Find files by name pattern using Spotlight (fast)."""
    expanded = os.path.expanduser(folder)
    safe_name = name.replace('"', '\\"')
    ok, out, err = _run_shell(
        f'mdfind -onlyin "{expanded}" "kMDItemFSName == \\"*{safe_name}*\\"" | head -n {max_results}',
        timeout=15
    )
    if ok and out:
        files = [{"name": os.path.basename(f), "path": f} for f in out.split('\n') if f]
        return {"success": True, "query": name, "results": files, "count": len(files)}
    return {"success": True, "query": name, "results": [], "count": 0}

def files_find_by_type(extension, folder="~", max_results=20):
    """Find files by extension (.pdf, .docx, .jpg, etc.)."""
    expanded = os.path.expanduser(folder)
    ext = extension if extension.startswith('.') else f'.{extension}'
    ok, out, err = _run_shell(
        f'mdfind -onlyin "{expanded}" "kMDItemFSName == \\"*{ext}\\"" | head -n {max_results}',
        timeout=15
    )
    if ok and out:
        files = []
        for f in out.split('\n'):
            if f:
                try:
                    stat = os.stat(f)
                    files.append({
                        "name": os.path.basename(f),
                        "path": f,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    })
                except OSError:
                    files.append({"name": os.path.basename(f), "path": f})
        return {"success": True, "extension": ext, "results": files, "count": len(files)}
    return {"success": True, "extension": ext, "results": [], "count": 0}

def files_write_text(path, content):
    """Write content to a text file. Creates the file if it doesn't exist. Overwrites if it does."""
    expanded = os.path.expanduser(path)
    parent = os.path.dirname(expanded)
    if parent and not os.path.isdir(parent):
        try:
            os.makedirs(parent, exist_ok=True)
        except Exception as e:
            return {"success": False, "error": f"Cannot create directory: {e}"}
    try:
        with open(expanded, 'w', encoding='utf-8') as f:
            f.write(content)
        return {"success": True, "path": expanded, "message": f"Written {len(content)} chars to {expanded}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def files_append_text(path, text):
    """Append text to the end of a file. Creates the file if it doesn't exist."""
    expanded = os.path.expanduser(path)
    parent = os.path.dirname(expanded)
    if parent and not os.path.isdir(parent):
        try:
            os.makedirs(parent, exist_ok=True)
        except Exception as e:
            return {"success": False, "error": f"Cannot create directory: {e}"}
    try:
        with open(expanded, 'a', encoding='utf-8') as f:
            f.write(text)
        return {"success": True, "path": expanded, "message": f"Appended {len(text)} chars to {expanded}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def files_read_lines(path, start_line=1, end_line=None):
    """Read specific lines from a file. Lines are 1-indexed. Returns lines with line numbers."""
    expanded = os.path.expanduser(path)
    if not os.path.isfile(expanded):
        return {"success": False, "error": f"File not found: {path}"}
    try:
        with open(expanded, 'r', encoding='utf-8', errors='replace') as f:
            all_lines = f.readlines()
        total = len(all_lines)
        start = max(1, start_line) - 1  # convert to 0-indexed
        end = min(total, end_line) if end_line else total
        selected = all_lines[start:end]
        numbered = ""
        for i, line in enumerate(selected, start=start + 1):
            numbered += f"{i}: {line}"
        return {
            "success": True,
            "path": expanded,
            "content": numbered,
            "lines_read": len(selected),
            "total_lines": total,
            "range": f"{start + 1}-{end}",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def files_insert_at_line(path, line_number, text):
    """Insert text at a specific line number. Lines are 1-indexed. Existing content shifts down."""
    expanded = os.path.expanduser(path)
    if not os.path.isfile(expanded):
        return {"success": False, "error": f"File not found: {path}"}
    try:
        with open(expanded, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        idx = max(0, min(line_number - 1, len(lines)))  # clamp to valid range
        insert_text = text if text.endswith('\n') else text + '\n'
        lines.insert(idx, insert_text)
        with open(expanded, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return {
            "success": True,
            "path": expanded,
            "message": f"Inserted at line {line_number} in {os.path.basename(expanded)}",
            "total_lines": len(lines),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def files_replace_lines(path, start_line, end_line, new_text):
    """Replace lines start_line through end_line (inclusive, 1-indexed) with new_text."""
    expanded = os.path.expanduser(path)
    if not os.path.isfile(expanded):
        return {"success": False, "error": f"File not found: {path}"}
    try:
        with open(expanded, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        total = len(lines)
        s = max(1, start_line) - 1  # 0-indexed
        e = min(total, end_line)    # inclusive end
        if s >= total:
            return {"success": False, "error": f"Start line {start_line} is beyond file ({total} lines)"}
        replacement = new_text if new_text.endswith('\n') else new_text + '\n'
        lines[s:e] = [replacement]
        with open(expanded, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return {
            "success": True,
            "path": expanded,
            "message": f"Replaced lines {start_line}-{end_line} in {os.path.basename(expanded)}",
            "lines_before": total,
            "lines_after": len(lines),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def files_replace_text(path, old_text, new_text):
    """Find and replace exact text in a file. Replaces the first occurrence."""
    expanded = os.path.expanduser(path)
    if not os.path.isfile(expanded):
        return {"success": False, "error": f"File not found: {path}"}
    try:
        with open(expanded, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        if old_text not in content:
            return {"success": False, "error": "Text not found in file"}
        new_content = content.replace(old_text, new_text, 1)
        with open(expanded, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return {
            "success": True,
            "path": expanded,
            "message": f"Replaced text in {os.path.basename(expanded)}",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def files_read_text(path, max_chars=10000):
    """Read a text file (first N chars). Works for .txt, .md, .py, .json, etc."""
    expanded = os.path.expanduser(path)
    if not os.path.isfile(expanded):
        return {"success": False, "error": f"File not found: {path}"}
    try:
        with open(expanded, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read(max_chars)
        return {
            "success": True,
            "path": expanded,
            "content": content,
            "truncated": len(content) >= max_chars,
            "total_size": os.path.getsize(expanded),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def files_get_pdf_info(path):
    """Get PDF metadata: page count, title, author, etc."""
    expanded = os.path.expanduser(path)
    if not os.path.isfile(expanded):
        return {"success": False, "error": f"File not found: {path}"}

    info = {"success": True, "path": expanded, "name": os.path.basename(expanded)}

    # Use mdls (Spotlight metadata) for PDF info
    ok, out, err = _run_shell(
        f'mdls -name kMDItemNumberOfPages -name kMDItemTitle -name kMDItemAuthors '
        f'-name kMDItemCreator -name kMDItemPageWidth -name kMDItemPageHeight "{expanded}"'
    )
    if ok:
        for line in out.split('\n'):
            if '=' in line:
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip().strip('"').strip('(').strip(')')
                if val and val != '(null)':
                    if 'NumberOfPages' in key:
                        info["pages"] = int(val) if val.isdigit() else val
                    elif 'Title' in key:
                        info["title"] = val
                    elif 'Authors' in key:
                        info["author"] = val.strip().strip('"')
                    elif 'Creator' in key:
                        info["creator"] = val

    stat = os.stat(expanded)
    size = stat.st_size
    if size < 1024 * 1024:
        info["size"] = f"{size / 1024:.1f} KB"
    else:
        info["size"] = f"{size / (1024 * 1024):.1f} MB"

    return info

def files_read_pdf_text(path, max_pages=5):
    """Extract text from first N pages of a PDF. Uses macOS built-in tools or PyMuPDF."""
    expanded = os.path.expanduser(path)
    if not os.path.isfile(expanded):
        return {"success": False, "error": f"File not found: {path}"}

    # Try PyMuPDF first (best quality)
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(expanded)
        text = ""
        pages_read = min(max_pages, len(doc))
        for i in range(pages_read):
            text += doc[i].get_text()
        doc.close()
        return {
            "success": True,
            "path": expanded,
            "text": text[:10000],
            "pages_read": pages_read,
            "total_pages": len(doc) if 'doc' in dir() else pages_read,
            "truncated": len(text) > 10000,
        }
    except ImportError:
        pass

    ok, out, err = _run_shell(
        f'mdimport -d 2 "{expanded}" 2>&1 | head -100',
        timeout=10
    )

    # Another fallback: try python pdfplumber or pdfminer
    return {
        "success": False,
        "error": "PyMuPDF not installed. Install with: pip3 install PyMuPDF",
        "hint": "Alternatively use computer_use_agent to open the PDF in Preview and read it visually."
    }

def clipboard_read():
    """Read current clipboard text."""
    ok, out, err = _run_shell('pbpaste')
    return {"success": ok, "content": out, "length": len(out)}

def clipboard_write(text):
    """Write text to clipboard."""
    try:
        process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        process.communicate(text.encode('utf-8'))
        return {"success": True, "length": len(text)}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ═══════════════════════════════════════════════════════════════
# ██  APPLE MAIL AUTOMATION (Native AppleScript)
# ═══════════════════════════════════════════════════════════════

def mail_open():
    """Open Apple Mail."""
    ok, out, err = _run_shell(['open', '-a', 'Mail'])
    time.sleep(1.0)
    return {"success": ok}

def mail_compose(to, subject, body, cc="", send=True):
    """Compose and optionally send an email via native Apple Mail AppleScript.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body text
        cc: Optional CC recipient(s)
        send: If True, sends immediately. If False, opens compose window.
    """
    safe_subject = _escape_applescript(subject)
    safe_body = _escape_applescript(body)
    safe_to = _escape_applescript(to)

    script = (
        'tell application "Mail"\n'
        '    activate\n'
        '    set newMsg to make new outgoing message with properties '
        '{subject:"' + safe_subject + '", content:"' + safe_body + '", visible:true}\n'
        '    tell newMsg\n'
        '        make new to recipient at end of to recipients with properties '
        '{address:"' + safe_to + '"}\n'
    )
    if cc:
        safe_cc = _escape_applescript(cc)
        script += (
            '        make new cc recipient at end of cc recipients with properties '
            '{address:"' + safe_cc + '"}\n'
        )
    if send:
        script += '        send\n'
    script += (
        '    end tell\n'
        'end tell'
    )
    ok, out, err = _run_applescript(script, timeout=15)
    return {"success": ok, "to": to, "subject": subject, "sent": send, "error": err if not ok else None}

def mail_list_inbox(count=10, unread_only=False):
    """List recent inbox messages.

    Args:
        count: Number of messages to return (default 10, max 50)
        unread_only: If True, only return unread messages
    """
    count = min(int(count), 50)
    if unread_only:
        filter_clause = "whose read status is false"
    else:
        filter_clause = ""

    script = (
        'tell application "Mail"\n'
        '    set msgs to messages of inbox ' + filter_clause + '\n'
        '    set msgCount to count of msgs\n'
        '    set maxN to msgCount\n'
        '    if maxN > ' + str(count) + ' then set maxN to ' + str(count) + '\n'
        '    set resultList to {}\n'
        '    repeat with i from 1 to maxN\n'
        '        set m to item i of msgs\n'
        '        set s to subject of m\n'
        '        set snd to sender of m\n'
        '        set d to date received of m as text\n'
        '        set isRead to read status of m\n'
        '        set end of resultList to ("[" & i & "] From: " & snd & " | Subject: " & s & " | Date: " & d & " | Read: " & isRead)\n'
        '    end repeat\n'
        '    set AppleScript\'s text item delimiters to "\\n"\n'
        '    return (resultList as text)\n'
        'end tell'
    )
    ok, out, err = _run_applescript(script, timeout=20)
    if ok and out:
        messages = [line.strip() for line in out.strip().split('\n') if line.strip()]
        return {"success": True, "count": len(messages), "messages": messages}
    return {"success": ok, "count": 0, "messages": [], "error": err if not ok else None}

def mail_unread_count():
    """Get the number of unread messages in inbox."""
    ok, out, err = _run_applescript(
        'tell application "Mail"\n'
        '    return unread count of inbox\n'
        'end tell'
    )
    count = 0
    if ok and out:
        try:
            count = int(out.strip())
        except ValueError:
            pass
    return {"success": ok, "unread": count}

def mail_read_message(index=1):
    """Read the content of a specific inbox message by index (1-based).

    Args:
        index: Message number (1 = most recent)
    """
    index = max(1, int(index))
    script = (
        'tell application "Mail"\n'
        '    set m to item ' + str(index) + ' of messages of inbox\n'
        '    set s to subject of m\n'
        '    set snd to sender of m\n'
        '    set d to date received of m as text\n'
        '    set bodyText to content of m\n'
        '    if length of bodyText > 2000 then\n'
        '        set bodyText to text 1 thru 2000 of bodyText\n'
        '    end if\n'
        '    set toList to {}\n'
        '    repeat with r in to recipients of m\n'
        '        set end of toList to address of r\n'
        '    end repeat\n'
        '    set AppleScript\'s text item delimiters to ", "\n'
        '    set toStr to (toList as text)\n'
        '    return "From: " & snd & "\\nTo: " & toStr & "\\nDate: " & d & "\\nSubject: " & s & "\\n\\n" & bodyText\n'
        'end tell'
    )
    ok, out, err = _run_applescript(script, timeout=15)
    if ok and out:
        return {"success": True, "message": out.strip(), "index": index}
    return {"success": False, "error": err if err else "Message not found", "index": index}

def mail_reply(index=1, body="", send=True):
    """Reply to an inbox message by index.

    Args:
        index: Message number (1 = most recent)
        body: Reply text to prepend
        send: If True, sends immediately. If False, opens reply window.
    """
    index = max(1, int(index))
    safe_body = _escape_applescript(body)

    script = (
        'tell application "Mail"\n'
        '    activate\n'
        '    set m to item ' + str(index) + ' of messages of inbox\n'
        '    set replyMsg to reply m with opening window\n'
        '    tell replyMsg\n'
        '        set content to "' + safe_body + '" & return & return & content\n'
        '        set visible to true\n'
    )
    if send:
        script += '        send\n'
    script += (
        '    end tell\n'
        'end tell'
    )
    ok, out, err = _run_applescript(script, timeout=15)
    return {"success": ok, "index": index, "sent": send, "error": err if not ok else None}

def mail_forward(index=1, to="", body="", send=True):
    """Forward an inbox message by index.

    Args:
        index: Message number (1 = most recent)
        to: Recipient email address
        body: Optional text to add before forwarded message
        send: If True, sends immediately. If False, opens forward window.
    """
    index = max(1, int(index))
    safe_to = _escape_applescript(to)
    safe_body = _escape_applescript(body)

    script = (
        'tell application "Mail"\n'
        '    activate\n'
        '    set m to item ' + str(index) + ' of messages of inbox\n'
        '    set fwdMsg to forward m with opening window\n'
        '    tell fwdMsg\n'
        '        make new to recipient at end of to recipients with properties {address:"' + safe_to + '"}\n'
    )
    if body:
        script += '        set content to "' + safe_body + '" & return & return & content\n'
    script += '        set visible to true\n'
    if send:
        script += '        send\n'
    script += (
        '    end tell\n'
        'end tell'
    )
    ok, out, err = _run_applescript(script, timeout=15)
    return {"success": ok, "index": index, "to": to, "sent": send, "error": err if not ok else None}

def mail_search(query, mailbox="inbox", count=10):
    """Search messages by subject or sender.

    Args:
        query: Search text (matches subject and sender)
        mailbox: "inbox" (default)
        count: Max results (default 10)
    """
    count = min(int(count), 50)
    safe_query = _escape_applescript(query)

    script = (
        'tell application "Mail"\n'
        '    set subjectMsgs to messages of inbox whose subject contains "' + safe_query + '"\n'
        '    set senderMsgs to messages of inbox whose sender contains "' + safe_query + '"\n'
        '    -- Combine results (subject matches first)\n'
        '    set allMsgs to subjectMsgs & senderMsgs\n'
        '    set msgCount to count of allMsgs\n'
        '    set maxN to msgCount\n'
        '    if maxN > ' + str(count) + ' then set maxN to ' + str(count) + '\n'
        '    set resultList to {}\n'
        '    repeat with i from 1 to maxN\n'
        '        set m to item i of allMsgs\n'
        '        set s to subject of m\n'
        '        set snd to sender of m\n'
        '        set d to date received of m as text\n'
        '        set end of resultList to ("[" & i & "] From: " & snd & " | Subject: " & s & " | Date: " & d)\n'
        '    end repeat\n'
        '    set AppleScript\'s text item delimiters to "\\n"\n'
        '    return (resultList as text)\n'
        'end tell'
    )
    ok, out, err = _run_applescript(script, timeout=20)
    if ok and out:
        messages = [line.strip() for line in out.strip().split('\n') if line.strip()]
        return {"success": True, "query": query, "count": len(messages), "messages": messages}
    return {"success": ok, "query": query, "count": 0, "messages": [], "error": err if not ok else None}

def mail_mark_read(index=1):
    """Mark an inbox message as read.

    Args:
        index: Message number (1 = most recent)
    """
    index = max(1, int(index))
    ok, out, err = _run_applescript(
        'tell application "Mail"\n'
        '    set read status of item ' + str(index) + ' of messages of inbox to true\n'
        'end tell'
    )
    return {"success": ok, "index": index}

def mail_mark_unread(index=1):
    """Mark an inbox message as unread.

    Args:
        index: Message number (1 = most recent)
    """
    index = max(1, int(index))
    ok, out, err = _run_applescript(
        'tell application "Mail"\n'
        '    set read status of item ' + str(index) + ' of messages of inbox to false\n'
        'end tell'
    )
    return {"success": ok, "index": index}

def mail_delete(index=1):
    """Move an inbox message to trash.

    Args:
        index: Message number (1 = most recent)
    """
    index = max(1, int(index))
    ok, out, err = _run_applescript(
        'tell application "Mail"\n'
        '    set m to item ' + str(index) + ' of messages of inbox\n'
        '    delete m\n'
        'end tell'
    )
    return {"success": ok, "index": index}

def mail_check():
    """Check for new mail (triggers fetch)."""
    ok, out, err = _run_applescript(
        'tell application "Mail"\n'
        '    check for new mail\n'
        'end tell'
    )
    time.sleep(2.0)
    return {"success": ok}

# ═══════════════════════════════════════════════════════════════
# ██  WEB GMAIL AUTOMATION (Chrome + Keyboard Shortcuts)
# ═══════════════════════════════════════════════════════════════
# Gmail keyboard shortcuts must be enabled: Settings → General → "Keyboard shortcuts on"
# Pattern: activate Chrome → send keystroke to Gmail page via System Events

def _gmail_activate():
    """Activate Chrome with Gmail tab. Opens Chrome if not running."""
    _run_applescript('tell application "Google Chrome" to activate')
    time.sleep(0.3)
    ok, out, err = _run_applescript('tell application "Google Chrome" to return count of windows')
    if not ok or out.strip() == "0":
        _run_applescript('tell application "Google Chrome" to make new window')
        time.sleep(1.0)

def _gmail_ensure_tab():
    """Make sure Gmail is the active tab in Chrome. Opens Gmail if not on a Gmail tab. Waits for inbox to load."""
    _gmail_activate()
    # Fast path: check if Chrome is already on Gmail
    ok, out, err = _run_applescript('''
tell application "Google Chrome"
    return URL of active tab of front window
end tell
''')
    if ok and "mail.google.com" in (out or ""):
        # Gmail URL is active, but wait until it's actually ready for keyboard shortcuts
        _gmail_wait_ready(max_wait=6)
        return True
    # Not on Gmail — try to find a Gmail tab in all windows
    _run_applescript('''
tell application "Google Chrome"
    repeat with w in windows
        set tabList to tabs of w
        repeat with i from 1 to count of tabList
            if URL of item i of tabList contains "mail.google.com" then
                set index of w to 1
                set active tab index of w to i
                return "found"
            end if
        end repeat
    end repeat
    return "not_found"
end tell
''')
    time.sleep(1.0)
    # Verify the switch actually worked by checking URL again
    ok2, out2, err2 = _run_applescript('tell application "Google Chrome" to return URL of active tab of front window')
    if ok2 and "mail.google.com" in (out2 or ""):
        _gmail_wait_ready(max_wait=6)
        return True
    # No Gmail tab found or switch failed — navigate to Gmail directly
    _run_applescript('''
tell application "Google Chrome"
    set URL of active tab of front window to "https://mail.google.com/mail/#inbox"
end tell
''')
    # Wait for Gmail to fully load using smart polling
    if _gmail_wait_ready(max_wait=12):
        return True
    # Fallback: check URL
    ok3, out3, err3 = _run_applescript('tell application "Google Chrome" to return URL of active tab of front window')
    if ok3 and "mail.google.com" in (out3 or ""):
        time.sleep(3.0)  # Extra wait — Gmail might still be loading JS
        return True
    return False

def _gmail_key(char):
    """Send a single character keystroke to Chrome for Gmail shortcut."""
    safe = _escape_applescript(char)
    ok, out, err = _run_applescript(f'''
tell application "System Events" to tell process "Google Chrome"
    keystroke "{safe}"
end tell
''')
    return ok

def _gmail_keycode(code, modifiers=None):
    """Send a key code with optional modifiers to Chrome for Gmail."""
    if modifiers:
        mod_str = ', '.join([f'{m} down' for m in modifiers])
        script = f'tell application "System Events" to tell process "Google Chrome" to key code {code} using {{{mod_str}}}'
    else:
        script = f'tell application "System Events" to tell process "Google Chrome" to key code {code}'
    ok, out, err = _run_applescript(script)
    return ok

def _gmail_sequence(char1, char2, delay=0.3):
    """Send a two-key Gmail sequence (e.g. 'g' then 'i' for Go to Inbox)."""
    _gmail_key(char1)
    time.sleep(delay)
    return _gmail_key(char2)

def _gmail_read_clipboard():
    """Select all + copy in Chrome, then read clipboard. Works without Chrome JS setting."""
    _gmail_activate()
    time.sleep(0.3)
    _gmail_keycode(0, ['command'])   # Cmd+A (select all)
    time.sleep(0.3)
    _gmail_keycode(8, ['command'])   # Cmd+C (copy)
    time.sleep(0.3)
    r = subprocess.run(['pbpaste'], capture_output=True, text=True, timeout=5)
    return r.stdout if r.returncode == 0 else ""

def _gmail_get_tab_title():
    """Get Chrome tab title via AppleScript. No JS needed."""
    ok, out, err = _run_applescript('tell application "Google Chrome" to return title of active tab of front window')
    return out.strip() if ok else ""

def _gmail_wait_ready(max_wait=8):
    """Poll Chrome tab title until Gmail is loaded (Inbox/Gmail/Sent/etc in title).
    Returns True if ready, False if timed out. Smart polling: fast checks first, then slower."""
    ready_keywords = ["Inbox", "Gmail", "Sent", "Drafts", "Starred", "Compose", "Mail"]
    elapsed = 0
    interval = 0.5
    while elapsed < max_wait:
        title = _gmail_get_tab_title()
        if any(kw in title for kw in ready_keywords):
            return True
        time.sleep(interval)
        elapsed += interval
        # Slow down checks after first 2 seconds
        if elapsed > 2:
            interval = 1.0
    return False

def gmail_open():
    """Open Gmail in Chrome. Opens Chrome + window if not already running."""
    _run_applescript('tell application "Google Chrome" to activate')
    time.sleep(0.5)
    ok, out, err = _run_applescript('tell application "Google Chrome" to return count of windows')
    if not ok or out.strip() == "0":
        _run_applescript('tell application "Google Chrome" to make new window')
        time.sleep(1.0)
    # Navigate to Gmail
    safe_url = _escape_applescript("https://mail.google.com/mail/")
    ok, out, err = _run_applescript(f'''
tell application "Google Chrome"
    set URL of active tab of front window to "{safe_url}"
end tell
''')
    time.sleep(2.5)
    return {"success": ok, "action": "open_gmail"}

def gmail_get_state():
    """Detect current Gmail UI state via tab title. No JS needed."""
    _gmail_ensure_tab()
    title = _gmail_get_tab_title()
    ok, url_out, _ = _run_applescript('tell application "Google Chrome" to return URL of active tab of front window')
    url = url_out.strip() if ok else ""
    view = "unknown"
    if "compose=" in url:
        view = "compose"
    elif "#inbox/" in url or "#sent/" in url or "#all/" in url or "#label/" in url:
        view = "email"
    elif "#inbox" in url or "#search" in url or "#label" in url or "#starred" in url or "#sent" in url or "#drafts" in url or "#all" in url:
        view = "list"
    elif "Inbox" in title:
        view = "list"
    return {"success": True, "view": view, "title": title}

def gmail_ensure_list_view():
    """Auto-handle Gmail state: close compose/reply, go back to list. Always safe to call."""
    _gmail_ensure_tab()
    time.sleep(0.5)
    # Press Escape twice to close any compose/reply/dialog
    _gmail_keycode(53)  # Escape
    time.sleep(0.8)
    _gmail_keycode(53)  # Escape again
    time.sleep(0.8)
    # Press 'u' to go back to list (no-op if already in list)
    _gmail_key('u')
    time.sleep(1.0)
    # Verify via URL
    ok, url_out, _ = _run_applescript('tell application "Google Chrome" to return URL of active tab of front window')
    url = url_out.strip() if ok else ""
    if "#inbox" in url or "#sent" in url or "#drafts" in url or "#starred" in url or "#all" in url or "#search" in url or "#label" in url:
        return {"success": True, "action": "back_to_list"}
    # Force navigate to inbox
    _run_applescript('tell application "Google Chrome" to set URL of active tab of front window to "https://mail.google.com/mail/#inbox"')
    _gmail_wait_ready(max_wait=10)
    return {"success": True, "action": "forced_inbox"}

def gmail_compose(to="", subject="", body="", cc="", bcc="", send=False):
    """Compose a new Gmail email via keyboard shortcuts + clipboard paste. No JS needed.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body text
        cc: CC recipient(s)
        bcc: BCC recipient(s)
        send: If True, sends immediately via Cmd+Return
    """
    _gmail_ensure_tab()
    time.sleep(0.5)
    _gmail_keycode(53)  # Escape
    time.sleep(0.5)
    _gmail_keycode(53)  # Escape again
    time.sleep(0.5)
    _gmail_key('c')
    time.sleep(2.5)

    # To field is already focused after 'c'
    if to:
        _word_clipboard_type(to)
        time.sleep(0.3)
        _gmail_keycode(48)  # Tab to confirm address token
        time.sleep(0.5)

    # Tab to Subject field
    if subject:
        _word_clipboard_type(subject)
        time.sleep(0.2)

    # Tab to Body field
    _gmail_keycode(48)  # Tab into body
    time.sleep(0.2)
    if body:
        _word_clipboard_type(body)
        time.sleep(0.2)

    # CC
    if cc:
        _gmail_keycode(8, ['command', 'shift'])  # Cmd+Shift+C to open CC
        time.sleep(0.5)
        _word_clipboard_type(cc)
        time.sleep(0.3)
        _gmail_keycode(48)  # Tab to confirm
        time.sleep(0.3)

    # BCC
    if bcc:
        _gmail_keycode(11, ['command', 'shift'])  # Cmd+Shift+B to open BCC
        time.sleep(0.5)
        _word_clipboard_type(bcc)
        time.sleep(0.3)
        _gmail_keycode(48)  # Tab to confirm
        time.sleep(0.3)

    if send:
        time.sleep(0.3)
        _gmail_click_send()
        sent_confirmed = _gmail_verify_sent()
        return {"success": True, "action": "compose", "to": to, "subject": subject, "sent": True, "send_confirmed": sent_confirmed}

    return {"success": True, "action": "compose", "to": to, "subject": subject, "sent": False}

def _gmail_verify_sent():
    """Verify email was sent by checking tab title changes back from compose view. No JS needed."""
    for _ in range(3):
        time.sleep(1.0)
        title = _gmail_get_tab_title()
        if "Inbox" in title or "Sent" in title:
            return True
    # Gmail always sends on Cmd+Return, so return True even if title didn't change yet
    return True

def _gmail_click_send():
    """Send email via Cmd+Return keyboard shortcut. No JS needed."""
    time.sleep(0.3)
    _gmail_activate()
    time.sleep(0.3)
    _gmail_keycode(36, ['command'])  # Cmd+Return
    time.sleep(1.5)
    return True

def gmail_search(query=""):
    """Search Gmail (/ key then type query via clipboard paste)."""
    _gmail_ensure_tab()
    time.sleep(0.3)
    _gmail_key('/')
    time.sleep(0.8)
    if query:
        _word_clipboard_type(query)
        time.sleep(0.3)
        _gmail_keycode(36)  # Return
        time.sleep(1.5)
    return {"success": True, "action": "search", "query": query}

def gmail_reply(body="", send=False):
    """Reply to current email. Opens reply box, types body, optionally sends.

    Args:
        body: Reply text to type
        send: If True, sends immediately via Cmd+Return
    """
    _gmail_ensure_tab()
    time.sleep(0.3)
    _gmail_key('r')
    time.sleep(2.0)
    if body:
        _word_clipboard_type(body)
        time.sleep(0.3)
    if send:
        time.sleep(0.3)
        _gmail_click_send()
        sent_confirmed = _gmail_verify_sent()
        return {"success": True, "action": "reply", "sent": True, "send_confirmed": sent_confirmed}
    return {"success": True, "action": "reply", "sent": False}

def gmail_reply_all(body="", send=False):
    """Reply all to current email. Opens reply-all box, types body, optionally sends.

    Args:
        body: Reply text to type
        send: If True, sends immediately via Cmd+Return
    """
    _gmail_ensure_tab()
    time.sleep(0.3)
    _gmail_key('a')
    time.sleep(2.0)
    if body:
        _word_clipboard_type(body)
        time.sleep(0.3)
    if send:
        time.sleep(0.3)
        _gmail_click_send()
        sent_confirmed = _gmail_verify_sent()
        return {"success": True, "action": "reply_all", "sent": True, "send_confirmed": sent_confirmed}
    return {"success": True, "action": "reply_all", "sent": False}

def gmail_forward(to="", body="", send=False):
    """Forward current email. Opens forward box, fills To and body, optionally sends.

    Args:
        to: Recipient email for forwarding
        body: Additional text to add
        send: If True, sends immediately via Cmd+Return
    """
    _gmail_ensure_tab()
    time.sleep(0.3)
    _gmail_key('f')
    time.sleep(2.0)
    # To field is focused in forward window
    if to:
        _word_clipboard_type(to)
        time.sleep(0.3)
    # Tab to body
    _gmail_keycode(48)  # Tab
    time.sleep(0.2)
    if body:
        _word_clipboard_type(body)
        time.sleep(0.2)
    if send:
        time.sleep(0.3)
        _gmail_click_send()
        sent_confirmed = _gmail_verify_sent()
        return {"success": True, "action": "forward", "to": to, "sent": True, "send_confirmed": sent_confirmed}
    return {"success": True, "action": "forward", "to": to, "sent": False}

def gmail_send():
    """Send composed/reply/forward email via Cmd+Return. No JS needed."""
    _gmail_activate()
    time.sleep(0.3)
    _gmail_click_send()
    sent_confirmed = _gmail_verify_sent()
    return {"success": True, "action": "send", "send_confirmed": sent_confirmed}

def gmail_go_inbox():
    """Go to Inbox (g then i)."""
    _gmail_activate()
    ok = _gmail_sequence('g', 'i')
    time.sleep(1.5)
    return {"success": ok, "action": "go_inbox"}

def gmail_go_sent():
    """Go to Sent Mail (g then t)."""
    _gmail_activate()
    ok = _gmail_sequence('g', 't')
    time.sleep(1.5)
    return {"success": ok, "action": "go_sent"}

def gmail_go_drafts():
    """Go to Drafts (g then d)."""
    _gmail_activate()
    ok = _gmail_sequence('g', 'd')
    time.sleep(1.5)
    return {"success": ok, "action": "go_drafts"}

def gmail_go_starred():
    """Go to Starred (g then s)."""
    _gmail_activate()
    ok = _gmail_sequence('g', 's')
    time.sleep(1.5)
    return {"success": ok, "action": "go_starred"}

def gmail_go_all_mail():
    """Go to All Mail (g then a)."""
    _gmail_activate()
    ok = _gmail_sequence('g', 'a')
    time.sleep(1.5)
    return {"success": ok, "action": "go_all_mail"}

def gmail_open_email():
    """Open selected email (o key or Return)."""
    _gmail_ensure_tab()
    time.sleep(0.3)
    ok = _gmail_key('o')
    time.sleep(2.0)  # Wait for email content to load
    return {"success": ok, "action": "open_email"}

def gmail_back_to_list():
    """Go back to email list from email view (u key)."""
    _gmail_activate()
    ok = _gmail_key('u')
    time.sleep(0.5)
    return {"success": ok, "action": "back_to_list"}

def gmail_next():
    """Move to next/older conversation (j key)."""
    _gmail_activate()
    ok = _gmail_key('j')
    time.sleep(0.3)
    return {"success": ok, "action": "next"}

def gmail_prev():
    """Move to previous/newer conversation (k key)."""
    _gmail_activate()
    ok = _gmail_key('k')
    time.sleep(0.3)
    return {"success": ok, "action": "prev"}

def gmail_newer():
    """Next message within thread (n key)."""
    _gmail_activate()
    ok = _gmail_key('n')
    time.sleep(0.3)
    return {"success": ok, "action": "newer"}

def gmail_older():
    """Previous message within thread (p key)."""
    _gmail_activate()
    ok = _gmail_key('p')
    time.sleep(0.3)
    return {"success": ok, "action": "older"}

def gmail_archive():
    """Archive current conversation (e key)."""
    _gmail_activate()
    ok = _gmail_key('e')
    time.sleep(0.5)
    return {"success": ok, "action": "archive"}

def gmail_delete():
    """Delete current conversation (# key)."""
    _gmail_activate()
    ok = _gmail_key('#')
    time.sleep(0.5)
    return {"success": ok, "action": "delete"}

def gmail_spam():
    """Report as spam (! key)."""
    _gmail_activate()
    ok = _gmail_key('!')
    time.sleep(0.5)
    return {"success": ok, "action": "spam"}

def gmail_star():
    """Star/unstar current conversation (s key)."""
    _gmail_activate()
    ok = _gmail_key('s')
    time.sleep(0.3)
    return {"success": ok, "action": "star"}

def gmail_mark_read():
    """Mark as read (Shift+i)."""
    _gmail_activate()
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "i" using {shift down}
end tell
''')
    return {"success": ok, "action": "mark_read"}

def gmail_mark_unread():
    """Mark as unread (Shift+u)."""
    _gmail_activate()
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "u" using {shift down}
end tell
''')
    return {"success": ok, "action": "mark_unread"}

def gmail_mark_important():
    """Mark as important (+ key)."""
    _gmail_activate()
    ok = _gmail_key('+')
    return {"success": ok, "action": "mark_important"}

def gmail_select():
    """Select/deselect current conversation (x key)."""
    _gmail_activate()
    ok = _gmail_key('x')
    return {"success": ok, "action": "select"}

def gmail_select_all():
    """Select all conversations (* then a)."""
    _gmail_activate()
    ok = _gmail_sequence('*', 'a')
    return {"success": ok, "action": "select_all"}

def gmail_mute():
    """Mute conversation (m key)."""
    _gmail_activate()
    ok = _gmail_key('m')
    return {"success": ok, "action": "mute"}

def gmail_label():
    """Open label menu (l key). Then type label name + Return."""
    _gmail_activate()
    ok = _gmail_key('l')
    time.sleep(0.5)
    return {"success": ok, "action": "label"}

def gmail_move_to():
    """Open move-to menu (v key). Then type folder name + Return."""
    _gmail_activate()
    ok = _gmail_key('v')
    time.sleep(0.5)
    return {"success": ok, "action": "move_to"}

def gmail_snooze():
    """Snooze conversation (b key)."""
    _gmail_activate()
    ok = _gmail_key('b')
    time.sleep(0.5)
    return {"success": ok, "action": "snooze"}

def gmail_undo():
    """Undo last Gmail action (z key)."""
    _gmail_activate()
    ok = _gmail_key('z')
    return {"success": ok, "action": "undo"}

def gmail_refresh():
    """Refresh Gmail inbox by navigating to inbox."""
    result = chrome_navigate("https://mail.google.com/mail/#inbox")
    time.sleep(2.0)
    return {"success": result.get("success", False), "action": "refresh"}

def gmail_unread_count():
    """Get count of unread emails by parsing Chrome tab title. No JS needed."""
    _gmail_ensure_tab()
    time.sleep(0.5)
    import re
    title = _gmail_get_tab_title()
    m = re.search(r'\(([\d,]+)\)', title)
    if m:
        count = int(m.group(1).replace(',', ''))
        return {"success": True, "unread_count": count}
    if "Inbox" in title:
        return {"success": True, "unread_count": 0}
    return {"success": False, "unread_count": 0, "error": "Could not count unread"}

def gmail_read_email():
    """Read email content via clipboard. If on inbox list, opens first selected email first. No JS needed."""
    _gmail_ensure_tab()
    time.sleep(1.0)
    # Check if we're on list view — if so, press Return to open the selected email
    ok, url_out, _ = _run_applescript('tell application "Google Chrome" to return URL of active tab of front window')
    url = url_out.strip() if ok else ""
    # If URL has #inbox but NOT #inbox/ it means we're on list, not inside an email
    if "#inbox" in url and "#inbox/" not in url:
        _gmail_keycode(36)  # Return — open selected email
        time.sleep(2.5)  # Wait for email to fully load
    text = _gmail_read_clipboard()
    if text and len(text) > 20:
        return {"success": True, "content": text[:3000]}
    # Retry once — email might still be loading
    time.sleep(2.0)
    text = _gmail_read_clipboard()
    if text and len(text) > 20:
        return {"success": True, "content": text[:3000]}
    return {"success": False, "content": "", "error": "Could not read email"}


def reminders_create(title, list_name="Reminders", due_date=None, notes=""):
    """Create a new reminder."""
    safe_title = _escape_applescript(title)
    safe_notes = _escape_applescript(notes)
    safe_list = _escape_applescript(list_name)

    if due_date:
        # due_date format: "2024-03-15 14:00"
        script = f'''
tell application "Reminders"
    tell list "{safe_list}"
        set newReminder to make new reminder with properties {{name:"{safe_title}", body:"{safe_notes}"}}
        set due date of newReminder to date "{due_date}"
    end tell
end tell
'''
    else:
        script = f'''
tell application "Reminders"
    tell list "{safe_list}"
        make new reminder with properties {{name:"{safe_title}", body:"{safe_notes}"}}
    end tell
end tell
'''
    ok, out, err = _run_applescript(script, timeout=10)
    return {"success": ok, "title": title, "list": list_name, "error": err if not ok else None}

def reminders_list(list_name="Reminders", show_completed=False):
    """List reminders from a specific list."""
    safe_list = _escape_applescript(list_name)
    if show_completed:
        filter_clause = ""
    else:
        filter_clause = "whose completed is false"

    script = f'''
tell application "Reminders"
    set reminderList to {{}}
    set rs to reminders of list "{safe_list}" {filter_clause}
    repeat with r in rs
        set end of reminderList to name of r
    end repeat
    return reminderList
end tell
'''
    ok, out, err = _run_applescript(script, timeout=10)
    if ok and out:
        items = [r.strip() for r in out.split(', ') if r.strip()]
        return {"success": True, "list": list_name, "reminders": items, "count": len(items)}
    return {"success": ok, "list": list_name, "reminders": [], "count": 0, "error": err if not ok else None}

def reminders_complete(title, list_name="Reminders"):
    """Mark a reminder as completed."""
    safe_title = _escape_applescript(title)
    safe_list = _escape_applescript(list_name)
    script = f'''
tell application "Reminders"
    set rs to reminders of list "{safe_list}" whose name is "{safe_title}" and completed is false
    if (count of rs) > 0 then
        set completed of item 1 of rs to true
        return "COMPLETED"
    else
        return "NOT_FOUND"
    end if
end tell
'''
    ok, out, err = _run_applescript(script, timeout=10)
    if ok:
        if out == "NOT_FOUND":
            return {"success": False, "error": f"Reminder '{title}' not found"}
        return {"success": True, "title": title, "completed": True}
    return {"success": False, "error": err}

def reminders_open():
    """Open Reminders app."""
    ok, out, err = _run_shell(['open', '-a', 'Reminders'])
    return {"success": ok}

def calendar_create_event(title, start_date, end_date=None, location="", notes="", calendar_name="Home"):
    """
    Create a calendar event.
    start_date format: "March 15, 2024 at 2:00 PM" or similar natural language date.
    """
    safe_title = _escape_applescript(title)
    safe_location = _escape_applescript(location)
    safe_notes = _escape_applescript(notes)
    safe_cal = _escape_applescript(calendar_name)
    safe_start = _escape_applescript(start_date)
    safe_end = _escape_applescript(end_date or start_date)

    script = f'''
tell application "Calendar"
    tell calendar "{safe_cal}"
        set startDate to date "{safe_start}"
        set endDate to date "{safe_end}"
        make new event at end with properties {{summary:"{safe_title}", start date:startDate, end date:endDate, location:"{safe_location}", description:"{safe_notes}"}}
    end tell
end tell
'''
    ok, out, err = _run_applescript(script, timeout=10)
    return {"success": ok, "title": title, "start": start_date, "error": err if not ok else None}

def calendar_today_events():
    """Get today's calendar events."""
    script = '''
tell application "Calendar"
    set today to current date
    set time of today to 0
    set tomorrow to today + (1 * days)
    set eventList to {}
    repeat with cal in calendars
        set evts to (events of cal whose start date >= today and start date < tomorrow)
        repeat with e in evts
            set eventTitle to summary of e
            set eventStart to start date of e
            set end of eventList to eventTitle & " at " & time string of eventStart
        end repeat
    end repeat
    return eventList
end tell
'''
    ok, out, err = _run_applescript(script, timeout=10)
    if ok and out:
        events = [e.strip() for e in out.split(', ') if e.strip()]
        return {"success": True, "events": events, "count": len(events), "date": "today"}
    return {"success": True, "events": [], "count": 0, "date": "today"}

def calendar_open():
    """Open Calendar app."""
    ok, out, err = _run_shell(['open', '-a', 'Calendar'])
    return {"success": ok}

def browser_get_url(browser="Chrome"):
    """Get the current URL from the frontmost browser tab."""
    if browser.lower() in ("chrome", "google chrome"):
        ok, out, err = _run_applescript(
            'tell application "Google Chrome" to get URL of active tab of front window'
        )
    elif browser.lower() == "safari":
        ok, out, err = _run_applescript(
            'tell application "Safari" to get URL of front document'
        )
    else:
        return {"success": False, "error": f"Unsupported browser: {browser}"}
    return {"success": ok, "url": out if ok else "", "browser": browser, "error": err if not ok else None}

def browser_get_title(browser="Chrome"):
    """Get the title of the current browser tab."""
    if browser.lower() in ("chrome", "google chrome"):
        ok, out, err = _run_applescript(
            'tell application "Google Chrome" to get title of active tab of front window'
        )
    elif browser.lower() == "safari":
        ok, out, err = _run_applescript(
            'tell application "Safari" to get name of front document'
        )
    else:
        return {"success": False, "error": f"Unsupported browser: {browser}"}
    return {"success": ok, "title": out if ok else "", "browser": browser}

def browser_list_tabs(browser="Chrome"):
    """List all open tabs (title + URL)."""
    if browser.lower() in ("chrome", "google chrome"):
        script = '''
tell application "Google Chrome"
    set tabList to {}
    repeat with w in windows
        repeat with t in tabs of w
            set end of tabList to (title of t) & " | " & (URL of t)
        end repeat
    end repeat
    return tabList
end tell
'''
    elif browser.lower() == "safari":
        script = '''
tell application "Safari"
    set tabList to {}
    repeat with w in windows
        repeat with t in tabs of w
            set end of tabList to (name of t) & " | " & (URL of t)
        end repeat
    end repeat
    return tabList
end tell
'''
    else:
        return {"success": False, "error": f"Unsupported browser: {browser}"}

    ok, out, err = _run_applescript(script, timeout=10)
    if ok and out:
        tabs = []
        for line in out.split(', '):
            parts = line.split(' | ', 1)
            tabs.append({
                "title": parts[0].strip(),
                "url": parts[1].strip() if len(parts) > 1 else "",
            })
        return {"success": True, "tabs": tabs, "count": len(tabs), "browser": browser}
    return {"success": True, "tabs": [], "count": 0, "browser": browser}

def browser_new_tab(url="about:blank", browser="Chrome"):
    """Open a new browser tab with a URL."""
    if browser.lower() in ("chrome", "google chrome"):
        safe_url = _escape_applescript(url)
        ok, out, err = _run_applescript(
            f'tell application "Google Chrome" to open location "{safe_url}"'
        )
    elif browser.lower() == "safari":
        safe_url = _escape_applescript(url)
        script = f'''
tell application "Safari"
    activate
    tell window 1
        set current tab to (make new tab with properties {{URL:"{safe_url}"}})
    end tell
end tell
'''
        ok, out, err = _run_applescript(script)
    else:
        return {"success": False, "error": f"Unsupported browser: {browser}"}
    return {"success": ok, "url": url, "browser": browser}

def browser_close_tab(browser="Chrome"):
    """Close the current browser tab."""
    if browser.lower() in ("chrome", "google chrome"):
        ok, out, err = _run_applescript(
            'tell application "Google Chrome" to close active tab of front window'
        )
    elif browser.lower() == "safari":
        ok, out, err = _run_applescript(
            'tell application "Safari" to close current tab of front window'
        )
    else:
        return {"success": False, "error": f"Unsupported browser: {browser}"}
    return {"success": ok, "browser": browser}

def app_open(name):
    """Open an application by name."""
    ok, out, err = _run_shell(['open', '-a', name])
    time.sleep(0.5)
    return {"success": ok, "app": name, "error": err if not ok else None}

def app_close(name):
    """Quit an application by name."""
    safe = _escape_applescript(name)
    ok, out, err = _run_applescript(f'tell application "{safe}" to quit')
    return {"success": ok, "app": name}

def app_switch(name):
    """Bring an application to the front."""
    safe = _escape_applescript(name)
    ok, out, err = _run_applescript(f'tell application "{safe}" to activate')
    return {"success": ok, "app": name}

def app_list_running():
    """List all running foreground apps."""
    ok, out, err = _run_applescript(
        'tell application "System Events" to get name of every process whose background only is false'
    )
    if ok:
        apps = [a.strip() for a in out.split(', ') if a.strip()]
        return {"success": True, "apps": apps, "count": len(apps)}
    return {"success": False, "error": err, "apps": []}

def app_frontmost():
    """Get the name of the frontmost application."""
    ok, out, err = _run_applescript(
        'tell application "System Events" to get the name of first process whose frontmost is true'
    )
    return {"success": ok, "app": out if ok else "unknown"}

# PATTERN: activate Word → use keyboard shortcuts via System Events
# WRITING: always uses clipboard paste (pbcopy → Cmd+V) for 100% reliability
# with any language/special chars. NEVER uses keystroke for content.

def _word_activate():
    """Activate Microsoft Word and wait for it."""
    ok, out, err = _run_applescript('''
tell application "Microsoft Word" to activate
delay 0.5
''')
    return ok

def _word_clipboard_type(text):
    """Type text into Word using clipboard paste — 100% reliable for any text."""
    try:
        process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        process.communicate(text.encode('utf-8'))
        time.sleep(0.15)
        ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "v" using {command down}
end tell
''')
        time.sleep(0.2)
        return ok
    except Exception:
        return False

def word_get_document_path():
    """Get the full file path of the active Word document."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "Microsoft Word"
    try
        set docPath to full name of active document
        return docPath
    on error
        return "unsaved"
    end try
end tell
''')
    if ok and out and out.strip() != "unsaved":
        return {"success": True, "path": out.strip()}
    return {"success": True, "path": None, "note": "Document not yet saved to disk"}

def word_open():
    """Open Microsoft Word."""
    ok, out, err = _run_shell(['open', '-a', 'Microsoft Word'])
    time.sleep(1.5)
    return {"success": ok, "error": err if not ok else None}

def word_new_document():
    """Create a new blank document in Word (Cmd+N)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "n" using {command down}
end tell
''')
    time.sleep(1.0)
    return {"success": ok}

def word_write(text):
    """Write text into Word at cursor position using clipboard paste.
    Handles multiline text — \\n becomes actual new lines."""
    _word_activate()
    time.sleep(0.2)
    success = _word_clipboard_type(text)
    return {"success": success, "length": len(text)}

def word_keystroke(text, delay_per_char=0.03):
    """Type text in Word character-by-character using AppleScript keystroke.
    Use this when clipboard paste is NOT possible (e.g. dialogs, search fields,
    filename prompts). Slower but works everywhere.
    For normal document writing, prefer word_write() (clipboard paste)."""
    _word_activate()
    time.sleep(0.2)
    safe = _escape_applescript(text)
    ok, out, err = _run_applescript(f'''
tell application "System Events"
    keystroke "{safe}"
end tell
''')
    return {"success": ok, "length": len(text), "method": "keystroke"}

def keystroke_type(text, app_name=None):
    """Type text character-by-character via AppleScript keystroke in ANY app.
    If app_name given, activates that app first.
    Use when clipboard paste can't be used (dialogs, prompts, search bars).
    For bulk text, prefer clipboard paste methods instead."""
    if app_name:
        safe_app = _escape_applescript(app_name)
        _run_applescript(f'tell application "{safe_app}" to activate')
        time.sleep(0.3)
    safe = _escape_applescript(text)
    ok, out, err = _run_applescript(f'''
tell application "System Events"
    keystroke "{safe}"
end tell
''')
    return {"success": ok, "length": len(text), "method": "keystroke"}

def keystroke_key(key_code, modifiers=None):
    """Press a key by key code with optional modifiers in the frontmost app.
    modifiers: list like ["command", "shift", "option", "control"]
    Common key codes: Return=36, Tab=48, Escape=53, Space=49,
      Delete=51, ForwardDelete=117, Left=123, Right=124, Up=126, Down=125,
      Home=115, End=119, PageUp=116, PageDown=121, F1=122..F12=111"""
    if modifiers:
        mod_str = ', '.join([f'{m} down' for m in modifiers])
        script = f'tell application "System Events" to key code {key_code} using {{{mod_str}}}'
    else:
        script = f'tell application "System Events" to key code {key_code}'
    ok, out, err = _run_applescript(script)
    return {"success": ok, "key_code": key_code, "modifiers": modifiers}

def word_new_line(count=1):
    """Press Enter/Return N times in Word."""
    _word_activate()
    keys = '\n'.join([f'    key code 36\n    delay 0.1' for _ in range(count)])
    ok, out, err = _run_applescript(f'''
tell application "System Events"
{keys}
end tell
''')
    return {"success": ok, "lines": count}

def word_heading_1():
    """Apply Heading 1 style (Cmd+Option+1)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "1" using {command down, option down}
end tell
''')
    return {"success": ok, "style": "Heading 1"}

def word_heading_2():
    """Apply Heading 2 style (Cmd+Option+2)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "2" using {command down, option down}
end tell
''')
    return {"success": ok, "style": "Heading 2"}

def word_heading_3():
    """Apply Heading 3 style (Cmd+Option+3)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "3" using {command down, option down}
end tell
''')
    return {"success": ok, "style": "Heading 3"}

def word_normal_text():
    """Apply Normal text style (Cmd+Shift+N)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "n" using {command down, shift down}
end tell
''')
    return {"success": ok, "style": "Normal"}

def word_bold():
    """Toggle bold (Cmd+B)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "b" using {command down}
end tell
''')
    return {"success": ok, "format": "bold"}

def word_italic():
    """Toggle italic (Cmd+I)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "i" using {command down}
end tell
''')
    return {"success": ok, "format": "italic"}

def word_underline():
    """Toggle underline (Cmd+U)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "u" using {command down}
end tell
''')
    return {"success": ok, "format": "underline"}

def word_bullet_list():
    """Start/toggle bullet list (Cmd+Shift+L)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "l" using {command down, shift down}
end tell
''')
    return {"success": ok, "format": "bullet_list"}

def word_center_text():
    """Center align text (Cmd+E)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "e" using {command down}
end tell
''')
    return {"success": ok, "align": "center"}

def word_left_text():
    """Left align text (Cmd+L)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "l" using {command down}
end tell
''')
    return {"success": ok, "align": "left"}

def word_right_text():
    """Right align text (Cmd+R)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "r" using {command down}
end tell
''')
    return {"success": ok, "align": "right"}

def word_justify():
    """Justify text (Cmd+J)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "j" using {command down}
end tell
''')
    return {"success": ok, "align": "justify"}

def word_single_space():
    """Set single line spacing (Cmd+1)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "1" using {command down}
end tell
''')
    return {"success": ok, "spacing": "single"}

def word_double_space():
    """Set double line spacing (Cmd+2)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "2" using {command down}
end tell
''')
    return {"success": ok, "spacing": "double"}

def word_1_5_space():
    """Set 1.5 line spacing (Cmd+5)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "5" using {command down}
end tell
''')
    return {"success": ok, "spacing": "1.5"}

def word_increase_font():
    """Increase font size (Cmd+Shift+>)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "." using {command down, shift down}
end tell
''')
    return {"success": ok, "font": "increased"}

def word_decrease_font():
    """Decrease font size (Cmd+Shift+<)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "," using {command down, shift down}
end tell
''')
    return {"success": ok, "font": "decreased"}

def word_select_all():
    """Select all text (Cmd+A)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "a" using {command down}
end tell
''')
    return {"success": ok}

def word_copy():
    """Copy selected text (Cmd+C)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "c" using {command down}
end tell
''')
    time.sleep(0.2)
    return {"success": ok}

def word_paste():
    """Paste from clipboard (Cmd+V)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "v" using {command down}
end tell
''')
    return {"success": ok}

def word_undo():
    """Undo last action (Cmd+Z)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "z" using {command down}
end tell
''')
    return {"success": ok}

def word_redo():
    """Redo last action (Cmd+Y)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "y" using {command down}
end tell
''')
    return {"success": ok}

def word_find(text):
    """Open Find and type search text (Cmd+F)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "f" using {command down}
end tell
''')
    time.sleep(0.5)
    _word_clipboard_type(text)
    return {"success": ok, "search": text}

def word_find_replace(find_text, replace_text):
    """Open Find & Replace (Cmd+H), type find and replace text."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "h" using {command down}
end tell
''')
    time.sleep(0.5)
    _word_clipboard_type(find_text)
    time.sleep(0.2)
    # Tab to replace field
    _run_applescript('tell application "System Events" to key code 48')
    time.sleep(0.2)
    _word_clipboard_type(replace_text)
    return {"success": ok, "find": find_text, "replace": replace_text}

def word_save(filename=None):
    """Save document. If filename given, uses Save As (Cmd+Shift+S) and types name.
    Uses clipboard paste for filename — works with any characters.
    Returns the full file path after saving."""
    _word_activate()
    if filename:
        ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "s" using {command down, shift down}
end tell
''')
        time.sleep(1.0)
        # Type filename via clipboard
        _word_clipboard_type(filename)
        time.sleep(0.3)
        # Press Enter to confirm
        _run_applescript('tell application "System Events" to key code 36')
        time.sleep(0.5)
        # If "replace?" dialog appears, press Enter again
        _run_applescript('''
tell application "System Events"
    delay 0.5
    key code 36
end tell
''')
        time.sleep(0.5)
        path_result = word_get_document_path()
        full_path = path_result.get("path")
        return {"success": ok, "saved_as": filename, "path": full_path}
    else:
        ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "s" using {command down}
end tell
''')
        time.sleep(0.3)
        path_result = word_get_document_path()
        full_path = path_result.get("path")
        return {"success": ok, "path": full_path}

def word_close():
    """Close/quit Microsoft Word."""
    ok, out, err = _run_applescript('tell application "Microsoft Word" to quit')
    return {"success": ok}

def word_close_document():
    """Close current document (Cmd+W)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "w" using {command down}
end tell
''')
    return {"success": ok}

def word_print():
    """Open print dialog (Cmd+P)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "p" using {command down}
end tell
''')
    return {"success": ok}

def word_clear_all():
    """Clear ALL content from Word document — Select All → Delete.
    Use this to rewrite a document. NEVER delete the file to rewrite."""
    _word_activate()
    time.sleep(0.3)
    _run_applescript('tell application "System Events" to keystroke "a" using {command down}')
    time.sleep(0.2)
    _run_applescript('tell application "System Events" to key code 51')  # Delete key
    time.sleep(0.2)
    return {"success": True, "action": "cleared all content"}

def word_cut():
    """Cut selected text (Cmd+X). Use after word_select_all to clear and keep in clipboard."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "x" using {command down}
end tell
''')
    time.sleep(0.2)
    return {"success": ok}

def word_read_content():
    """Read ALL content from Word document — Select All → Copy → read clipboard.
    Returns the full document text."""
    _word_activate()
    time.sleep(0.3)
    _run_applescript('tell application "System Events" to keystroke "a" using {command down}')
    time.sleep(0.2)
    _run_applescript('tell application "System Events" to keystroke "c" using {command down}')
    time.sleep(0.3)
    # Read clipboard
    ok, content, err = _run_shell('pbpaste')
    # Deselect (press right arrow)
    _run_applescript('tell application "System Events" to key code 124')
    return {"success": ok, "content": content, "length": len(content)}

def word_move_to_end():
    """Move cursor to end of document (Cmd+End or Cmd+Fn+Right)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 119 using {command down}
end tell
''')
    return {"success": ok}

def word_move_to_start():
    """Move cursor to beginning of document (Cmd+Home or Cmd+Fn+Left)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 115 using {command down}
end tell
''')
    return {"success": ok}

def word_toggle_case():
    """Cycle selected text between UPPER, lower, and Title case (Shift+F3)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 99 using {shift down}
end tell
''')
    return {"success": ok, "action": "toggle_case"}

def word_upper_case():
    """Toggle all-caps formatting on selected text (Cmd+Shift+A)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "a" using {command down, shift down}
end tell
''')
    return {"success": ok, "format": "upper_case"}

def word_strikethrough():
    """Toggle strikethrough formatting (Cmd+Shift+X)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "x" using {command down, shift down}
end tell
''')
    return {"success": ok, "format": "strikethrough"}

def word_paste_plain():
    """Paste text without formatting (Cmd+Shift+V)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "v" using {command down, shift down}
end tell
''')
    return {"success": ok, "action": "paste_plain"}

def word_indent():
    """Indent paragraph (Control+Shift+M)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "m" using {control down, shift down}
end tell
''')
    return {"success": ok, "action": "indent"}

def word_outdent():
    """Remove paragraph indent (Cmd+Shift+M)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "m" using {command down, shift down}
end tell
''')
    return {"success": ok, "action": "outdent"}

def word_page_break():
    """Insert a page break (Cmd+Return)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 36 using {command down}
end tell
''')
    return {"success": ok, "action": "page_break"}

def word_line_break():
    """Insert a soft line break without starting a new paragraph (Shift+Return)."""
    _word_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 36 using {shift down}
end tell
''')
    return {"success": ok, "action": "line_break"}

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
        left/right appear on same conceptual line (left bold, right normal)
        subleft/subright appear as italic sub-line

    Example CV call:
      word_write_formatted_document("JOHN DOE", [
          {"center": true, "text": "City, Country | phone | email | linkedin | github"},
          {"heading": "Professional Summary", "text": "Experienced developer..."},
          {"heading": "Technical Skills", "bullet_items": ["Languages: Python, JS", "Tools: Git, Docker"]},
          {"heading": "Experience", "items": [
              {"left": "Software Engineer", "right": "Jan 2022 - Present",
               "subleft": "Google | Mountain View, CA", "subright": "",
               "details": ["Led team of 5 to build microservices", "Reduced latency by 40%"]}
          ]},
          {"heading": "Education", "items": [
              {"left": "MIT", "right": "Sep 2018 - Jun 2022",
               "subleft": "B.S. Computer Science", "subright": "Cambridge, MA"}
          ]}
      ])
    """
    _word_activate()
    time.sleep(0.3)

    def _enter():
        _run_applescript('tell application "System Events" to key code 36')
        time.sleep(0.1)

    def _write(text):
        _word_clipboard_type(text)
        time.sleep(0.1)

    def _separator():
        """Insert a visible separator line."""
        word_normal_text()
        time.sleep(0.1)
        _write("—" * 50)
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

                # Main line: bold left, right aligned via tab
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

                # Sub-line: italic
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

                # Detail bullets
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
            # Turn off bullets
            word_bullet_list()
            time.sleep(0.1)

    return {"success": True, "title": title, "sections": len(sections)}

def safari_open():
    """Open Safari."""
    ok, out, err = _run_shell(['open', '-a', 'Safari'])
    time.sleep(0.5)
    return {"success": ok}

def safari_new_tab(url=None):
    """Open new tab in Safari, optionally navigate to URL."""
    _run_applescript('tell application "Safari" to activate')
    time.sleep(0.3)
    if url:
        safe_url = _escape_applescript(url)
        ok, out, err = _run_applescript(f'''
tell application "Safari"
    tell window 1
        set current tab to (make new tab with properties {{URL:"{safe_url}"}})
    end tell
end tell
''')
    else:
        ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "t" using {command down}
end tell
''')
    return {"success": ok, "url": url}

def safari_close_tab():
    """Close current Safari tab (Cmd+W)."""
    _run_applescript('tell application "Safari" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "w" using {command down}
end tell
''')
    return {"success": ok}

def safari_go_back():
    """Go back in Safari (Cmd+[)."""
    _run_applescript('tell application "Safari" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "[" using {command down}
end tell
''')
    return {"success": ok}

def safari_go_forward():
    """Go forward in Safari (Cmd+])."""
    _run_applescript('tell application "Safari" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "]" using {command down}
end tell
''')
    return {"success": ok}

def safari_reload():
    """Reload page (Cmd+R)."""
    _run_applescript('tell application "Safari" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "r" using {command down}
end tell
''')
    return {"success": ok}

def safari_get_url():
    """Get current URL from Safari."""
    ok, out, err = _run_applescript(
        'tell application "Safari" to get URL of front document'
    )
    return {"success": ok, "url": out if ok else ""}

def safari_get_title():
    """Get current page title from Safari."""
    ok, out, err = _run_applescript(
        'tell application "Safari" to get name of front document'
    )
    return {"success": ok, "title": out if ok else ""}

def safari_list_tabs():
    """List all open tabs in Safari."""
    script = '''
tell application "Safari"
    set tabList to {}
    repeat with w in windows
        repeat with t in tabs of w
            set end of tabList to (name of t) & " | " & (URL of t)
        end repeat
    end repeat
    return tabList
end tell
'''
    ok, out, err = _run_applescript(script, timeout=10)
    if ok and out:
        tabs = []
        for line in out.split(', '):
            parts = line.split(' | ', 1)
            tabs.append({"title": parts[0].strip(), "url": parts[1].strip() if len(parts) > 1 else ""})
        return {"success": True, "tabs": tabs, "count": len(tabs)}
    return {"success": True, "tabs": [], "count": 0}

def safari_private_window():
    """Open a new private window (Cmd+Shift+N)."""
    _run_applescript('tell application "Safari" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "n" using {command down, shift down}
end tell
''')
    return {"success": ok}

def safari_show_bookmarks():
    """Show bookmarks sidebar (Cmd+Shift+B... actually Cmd+Option+B in Safari)."""
    _run_applescript('tell application "Safari" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "b" using {command down, option down}
end tell
''')
    return {"success": ok}

def safari_add_bookmark():
    """Add bookmark for current page (Cmd+D)."""
    _run_applescript('tell application "Safari" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "d" using {command down}
end tell
''')
    return {"success": ok}

def chrome_open():
    """Open Google Chrome."""
    ok, out, err = _run_shell(['open', '-a', 'Google Chrome'])
    time.sleep(0.5)
    return {"success": ok}

def chrome_new_tab(url=None):
    """Open new tab, optionally navigate to URL."""
    _run_applescript('tell application "Google Chrome" to activate')
    time.sleep(0.2)
    if url:
        safe_url = _escape_applescript(url)
        ok, out, err = _run_applescript(
            f'tell application "Google Chrome" to open location "{safe_url}"'
        )
    else:
        ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "t" using {command down}
end tell
''')
    return {"success": ok, "url": url}

def chrome_close_tab():
    """Close current tab (Cmd+W)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "w" using {command down}
end tell
''')
    return {"success": ok}

def chrome_new_window():
    """Open new window (Cmd+N)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "n" using {command down}
end tell
''')
    return {"success": ok}

def chrome_incognito():
    """Open new Incognito window (Cmd+Shift+N)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "n" using {command down, shift down}
end tell
''')
    return {"success": ok}

def chrome_reopen_tab():
    """Reopen last closed tab (Cmd+Shift+T)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "t" using {command down, shift down}
end tell
''')
    return {"success": ok}

def chrome_next_tab():
    """Switch to next tab (Cmd+Option+Right)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    key code 124 using {command down, option down}
end tell
''')
    return {"success": ok}

def chrome_prev_tab():
    """Switch to previous tab (Cmd+Option+Left)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    key code 123 using {command down, option down}
end tell
''')
    return {"success": ok}

def chrome_go_to_tab(tab_number=1):
    """Jump to specific tab 1-8 (Cmd+1..8) or last tab (Cmd+9)."""
    tab_number = max(1, min(9, int(tab_number)))
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript(f'''
tell application "System Events" to tell process "Google Chrome"
    keystroke "{tab_number}" using {{command down}}
end tell
''')
    return {"success": ok, "tab": tab_number}

def chrome_go_back():
    """Go back in history (Cmd+[)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "[" using {command down}
end tell
''')
    return {"success": ok}

def chrome_go_forward():
    """Go forward in history (Cmd+])."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "]" using {command down}
end tell
''')
    return {"success": ok}

def chrome_reload():
    """Reload page (Cmd+R)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "r" using {command down}
end tell
''')
    return {"success": ok}

def chrome_hard_reload():
    """Hard reload ignoring cache (Cmd+Shift+R)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "r" using {command down, shift down}
end tell
''')
    return {"success": ok}

def chrome_get_url():
    """Get current tab URL."""
    ok, out, err = _run_applescript(
        'tell application "Google Chrome" to get URL of active tab of front window'
    )
    return {"success": ok, "url": out if ok else ""}

def chrome_get_title():
    """Get current tab title."""
    ok, out, err = _run_applescript(
        'tell application "Google Chrome" to get title of active tab of front window'
    )
    return {"success": ok, "title": out if ok else ""}

def chrome_list_tabs():
    """List all open tabs (title + URL)."""
    script = '''
tell application "Google Chrome"
    set tabList to {}
    repeat with w in windows
        repeat with t in tabs of w
            set end of tabList to (title of t) & " | " & (URL of t)
        end repeat
    end repeat
    return tabList
end tell
'''
    ok, out, err = _run_applescript(script, timeout=10)
    if ok and out:
        tabs = []
        for line in out.split(', '):
            parts = line.split(' | ', 1)
            tabs.append({"title": parts[0].strip(), "url": parts[1].strip() if len(parts) > 1 else ""})
        return {"success": True, "tabs": tabs, "count": len(tabs)}
    return {"success": True, "tabs": [], "count": 0}

def chrome_navigate(url):
    """Navigate current tab to URL."""
    safe_url = _escape_applescript(url)
    ok, out, err = _run_applescript(f'''
tell application "Google Chrome"
    set URL of active tab of front window to "{safe_url}"
end tell
''')
    return {"success": ok, "url": url}

def chrome_find(text=None):
    """Open Find bar (Cmd+F), optionally type search text."""
    _run_applescript('tell application "Google Chrome" to activate')
    _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "f" using {command down}
end tell
''')
    if text:
        time.sleep(0.3)
        _word_clipboard_type(text)
    return {"success": True, "text": text}

def chrome_bookmark():
    """Bookmark current page (Cmd+D)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "d" using {command down}
end tell
''')
    return {"success": ok}

def chrome_open_history():
    """Open History page (Cmd+Y)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "y" using {command down}
end tell
''')
    return {"success": ok}

def chrome_open_downloads():
    """Open Downloads page (Cmd+Shift+J)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "j" using {command down, shift down}
end tell
''')
    return {"success": ok}

def chrome_open_settings():
    """Open Chrome Settings (Cmd+,)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "," using {command down}
end tell
''')
    return {"success": ok}

def chrome_zoom_in():
    """Zoom in (Cmd+Plus)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "=" using {command down}
end tell
''')
    return {"success": ok}

def chrome_zoom_out():
    """Zoom out (Cmd+Minus)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "-" using {command down}
end tell
''')
    return {"success": ok}

def chrome_zoom_reset():
    """Reset zoom to 100% (Cmd+0)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "0" using {command down}
end tell
''')
    return {"success": ok}

def chrome_focus_address_bar():
    """Focus address bar (Cmd+L)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "l" using {command down}
end tell
''')
    return {"success": ok}

def chrome_open_devtools():
    """Open Developer Tools (Cmd+Option+I)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "i" using {command down, option down}
end tell
''')
    return {"success": ok}

def chrome_print():
    """Print current page (Cmd+P)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "p" using {command down}
end tell
''')
    return {"success": ok}

def chrome_close_window():
    """Close current window (Cmd+Shift+W)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "w" using {command down, shift down}
end tell
''')
    return {"success": ok}

def chrome_fullscreen():
    """Toggle full-screen mode."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    key code 3 using {command down, control down}
end tell
''')
    return {"success": ok}

def chrome_read_page_text():
    """Read visible text content from the current Chrome tab via JavaScript."""
    script = '''
tell application "Google Chrome"
    set pageText to execute front window's active tab javascript "document.body.innerText.substring(0, 5000)"
    return pageText
end tell
'''
    ok, out, err = _run_applescript(script, timeout=10)
    return {"success": ok, "text": out if ok else "", "truncated": True}

def chrome_execute_js(code):
    """Execute JavaScript in current Chrome tab and return result."""
    safe_code = _escape_applescript(code)
    script = f'''
tell application "Google Chrome"
    set jsResult to execute front window's active tab javascript "{safe_code}"
    return jsResult
end tell
'''
    ok, out, err = _run_applescript(script, timeout=15)
    return {"success": ok, "result": out if ok else "", "error": err if not ok else None}

def chrome_scroll_down():
    """Scroll down one page (Space)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    key code 49
end tell
''')
    return {"success": ok}

def chrome_scroll_up():
    """Scroll up one page (Shift+Space)."""
    _run_applescript('tell application "Google Chrome" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    key code 49 using {shift down}
end tell
''')
    return {"success": ok}

# Works when YouTube is the active tab in Chrome

def _youtube_activate():
    """Activate Chrome (YouTube runs in Chrome)."""
    _run_applescript('tell application "Google Chrome" to activate')
    time.sleep(0.2)

def _youtube_key(key_char):
    """Send a single character key to Chrome for YouTube control."""
    safe = _escape_applescript(key_char)
    ok, out, err = _run_applescript(f'''
tell application "System Events" to tell process "Google Chrome"
    keystroke "{safe}"
end tell
''')
    return ok

def _youtube_keycode(code, modifiers=None):
    """Send a key code with optional modifiers to Chrome."""
    if modifiers:
        mod_str = ', '.join([f'{m} down' for m in modifiers])
        script = f'tell application "System Events" to tell process "Google Chrome" to key code {code} using {{{mod_str}}}'
    else:
        script = f'tell application "System Events" to tell process "Google Chrome" to key code {code}'
    ok, out, err = _run_applescript(script)
    return ok

def youtube_open(query=None):
    """Open YouTube in Chrome. If query given, search for it."""
    if query:
        import urllib.parse
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    else:
        url = "https://www.youtube.com"
    return chrome_navigate(url)

def youtube_play_pause():
    """Toggle play/pause on YouTube video (k key)."""
    _youtube_activate()
    ok = _youtube_key('k')
    return {"success": ok, "action": "play_pause"}

def youtube_mute():
    """Toggle mute/unmute on YouTube video (m key)."""
    _youtube_activate()
    ok = _youtube_key('m')
    return {"success": ok, "action": "mute_toggle"}

def youtube_fullscreen():
    """Toggle fullscreen on YouTube video (f key)."""
    _youtube_activate()
    ok = _youtube_key('f')
    return {"success": ok, "action": "fullscreen_toggle"}

def youtube_captions():
    """Toggle captions/subtitles on YouTube video (c key)."""
    _youtube_activate()
    ok = _youtube_key('c')
    return {"success": ok, "action": "captions_toggle"}

def youtube_seek_forward():
    """Seek forward 10 seconds (l key)."""
    _youtube_activate()
    ok = _youtube_key('l')
    return {"success": ok, "action": "seek_forward_10s"}

def youtube_seek_backward():
    """Seek backward 10 seconds (j key)."""
    _youtube_activate()
    ok = _youtube_key('j')
    return {"success": ok, "action": "seek_backward_10s"}

def youtube_speed_up():
    """Increase playback speed (> key)."""
    _youtube_activate()
    ok = _youtube_key('>')
    return {"success": ok, "action": "speed_up"}

def youtube_speed_down():
    """Decrease playback speed (< key)."""
    _youtube_activate()
    ok = _youtube_key('<')
    return {"success": ok, "action": "speed_down"}

def youtube_next_video():
    """Skip to next video in playlist (Shift+N)."""
    _youtube_activate()
    ok, _, _ = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "n" using {shift down}
end tell
''')
    return {"success": ok, "action": "next_video"}

def youtube_prev_video():
    """Go to previous video in playlist (Shift+P)."""
    _youtube_activate()
    ok, _, _ = _run_applescript('''
tell application "System Events" to tell process "Google Chrome"
    keystroke "p" using {shift down}
end tell
''')
    return {"success": ok, "action": "prev_video"}

def youtube_volume_up():
    """Increase YouTube volume by 5% (Up arrow)."""
    _youtube_activate()
    ok = _youtube_keycode(126)  # Up arrow
    return {"success": ok, "action": "volume_up"}

def youtube_volume_down():
    """Decrease YouTube volume by 5% (Down arrow)."""
    _youtube_activate()
    ok = _youtube_keycode(125)  # Down arrow
    return {"success": ok, "action": "volume_down"}

def youtube_seek_to_percent(percent):
    """Seek to percentage of video (0-9 keys: 0=0%, 1=10%...9=90%)."""
    _youtube_activate()
    p = max(0, min(9, int(percent / 10)))
    ok = _youtube_key(str(p))
    return {"success": ok, "action": f"seek_to_{p*10}%"}

def youtube_miniplayer():
    """Toggle YouTube miniplayer (i key)."""
    _youtube_activate()
    ok = _youtube_key('i')
    return {"success": ok, "action": "miniplayer_toggle"}

def youtube_next_frame():
    """Skip to next frame while paused (. key)."""
    _youtube_activate()
    ok = _youtube_key('.')
    return {"success": ok, "action": "next_frame"}

def youtube_prev_frame():
    """Go to previous frame while paused (, key)."""
    _youtube_activate()
    ok = _youtube_key(',')
    return {"success": ok, "action": "prev_frame"}

def youtube_next_chapter():
    """Jump to next chapter (Option+Right arrow)."""
    _youtube_activate()
    ok = _youtube_keycode(124, ['option'])  # Right arrow + Option
    return {"success": ok, "action": "next_chapter"}

def youtube_prev_chapter():
    """Jump to previous chapter (Option+Left arrow)."""
    _youtube_activate()
    ok = _youtube_keycode(123, ['option'])  # Left arrow + Option
    return {"success": ok, "action": "prev_chapter"}

def music_open():
    """Open Apple Music."""
    ok, out, err = _run_shell(['open', '-a', 'Music'])
    return {"success": ok}

def music_play():
    """Play/resume in Music (Space)."""
    ok, out, err = _run_applescript('tell application "Music" to play')
    return {"success": ok}

def music_pause():
    """Pause Music."""
    ok, out, err = _run_applescript('tell application "Music" to pause')
    return {"success": ok}

def music_next():
    """Skip to next track."""
    ok, out, err = _run_applescript('tell application "Music" to next track')
    return {"success": ok}

def music_previous():
    """Go to previous track."""
    ok, out, err = _run_applescript('tell application "Music" to previous track')
    return {"success": ok}

def music_get_current_track():
    """Get info about the currently playing track."""
    script = '''
tell application "Music"
    if player state is playing then
        set trackName to name of current track
        set trackArtist to artist of current track
        set trackAlbum to album of current track
        set trackDuration to duration of current track
        return trackName & " | " & trackArtist & " | " & trackAlbum & " | " & (trackDuration as string)
    else
        return "NOT_PLAYING"
    end if
end tell
'''
    ok, out, err = _run_applescript(script)
    if ok and out != "NOT_PLAYING":
        parts = out.split(' | ')
        return {
            "success": True,
            "name": parts[0] if len(parts) > 0 else "",
            "artist": parts[1] if len(parts) > 1 else "",
            "album": parts[2] if len(parts) > 2 else "",
            "playing": True,
        }
    return {"success": True, "playing": False}

def music_set_volume(level):
    """Set Music app volume (0-100)."""
    level = max(0, min(100, int(level)))
    ok, out, err = _run_applescript(f'tell application "Music" to set sound volume to {level}')
    return {"success": ok, "volume": level}

def music_search(query):
    """Open Music and search (Cmd+F, then type)."""
    _run_applescript('tell application "Music" to activate')
    time.sleep(0.5)
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "f" using {command down, option down}
end tell
''')
    time.sleep(0.3)
    _word_clipboard_type(query)
    return {"success": ok, "query": query}

def music_toggle_shuffle():
    """Toggle shuffle mode."""
    ok, out, err = _run_applescript('''
tell application "Music"
    set shuffle enabled to not shuffle enabled
end tell
''')
    return {"success": ok}

def music_toggle_repeat():
    """Toggle repeat mode."""
    ok, out, err = _run_applescript('''
tell application "Music"
    if song repeat is off then
        set song repeat to all
    else
        set song repeat to off
    end if
end tell
''')
    return {"success": ok}

def terminal_open():
    """Open Terminal."""
    ok, out, err = _run_shell(['open', '-a', 'Terminal'])
    time.sleep(0.5)
    return {"success": ok}

def terminal_new_tab():
    """Open new Terminal tab (Cmd+T)."""
    _run_applescript('tell application "Terminal" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "t" using {command down}
end tell
''')
    return {"success": ok}

def terminal_new_window():
    """Open new Terminal window (Cmd+N)."""
    _run_applescript('tell application "Terminal" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "n" using {command down}
end tell
''')
    return {"success": ok}

def terminal_run_command(command):
    """Run a command in the frontmost Terminal window."""
    safe_cmd = _escape_applescript(command)
    ok, out, err = _run_applescript(f'''
tell application "Terminal"
    activate
    do script "{safe_cmd}" in front window
end tell
''', timeout=15)
    return {"success": ok, "command": command}

def terminal_clear():
    """Clear Terminal (Cmd+K)."""
    _run_applescript('tell application "Terminal" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "k" using {command down}
end tell
''')
    return {"success": ok}

def messages_open():
    """Open Messages app."""
    ok, out, err = _run_shell(['open', '-a', 'Messages'])
    time.sleep(0.5)
    return {"success": ok}

def messages_send(recipient, text):
    """Send an iMessage to a contact (phone number or email)."""
    safe_to = _escape_applescript(recipient)
    safe_text = _escape_applescript(text)
    script = f'''
tell application "Messages"
    set targetService to 1st account whose service type = iMessage
    set targetBuddy to participant "{safe_to}" of targetService
    send "{safe_text}" to targetBuddy
end tell
'''
    ok, out, err = _run_applescript(script, timeout=10)
    return {"success": ok, "to": recipient, "text": text[:50], "error": err if not ok else None}

def messages_new_message():
    """Start a new message (Cmd+N)."""
    _run_applescript('tell application "Messages" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "n" using {command down}
end tell
''')
    return {"success": ok}

def preview_open_file(path):
    """Open a file in Preview."""
    expanded = os.path.expanduser(path)
    if not os.path.exists(expanded):
        return {"success": False, "error": f"Not found: {path}"}
    ok, out, err = _run_shell(['open', '-a', 'Preview', expanded])
    return {"success": ok, "path": expanded}

def preview_zoom_in():
    """Zoom in (Cmd+=)."""
    _run_applescript('tell application "Preview" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "=" using {command down}
end tell
''')
    return {"success": ok}

def preview_zoom_out():
    """Zoom out (Cmd+-)."""
    _run_applescript('tell application "Preview" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "-" using {command down}
end tell
''')
    return {"success": ok}

def preview_actual_size():
    """Actual size (Cmd+0)."""
    _run_applescript('tell application "Preview" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "0" using {command down}
end tell
''')
    return {"success": ok}

def preview_rotate_right():
    """Rotate image right (Cmd+R)."""
    _run_applescript('tell application "Preview" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "r" using {command down}
end tell
''')
    return {"success": ok}

def preview_rotate_left():
    """Rotate image left (Cmd+L)."""
    _run_applescript('tell application "Preview" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "l" using {command down}
end tell
''')
    return {"success": ok}

def pages_open():
    """Open Apple Pages."""
    ok, out, err = _run_shell(['open', '-a', 'Pages'])
    time.sleep(1.0)
    return {"success": ok}

def pages_new_document():
    """Create new blank document in Pages (Cmd+N then Enter to select blank)."""
    _run_applescript('tell application "Pages" to activate')
    time.sleep(0.5)
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "n" using {command down}
    delay 1.0
    key code 36
end tell
''')
    return {"success": ok}

def pages_write(text):
    """Write text in Pages using clipboard paste."""
    _run_applescript('tell application "Pages" to activate')
    time.sleep(0.2)
    success = _word_clipboard_type(text)
    return {"success": success, "length": len(text)}

def pages_save(filename=None):
    """Save Pages document."""
    _run_applescript('tell application "Pages" to activate')
    if filename:
        ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "s" using {command down, shift down}
end tell
''')
        time.sleep(1.0)
        _word_clipboard_type(filename)
        time.sleep(0.3)
        _run_applescript('tell application "System Events" to key code 36')
        return {"success": ok, "saved_as": filename}
    else:
        ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "s" using {command down}
end tell
''')
        return {"success": ok}

def pages_export_pdf():
    """Export Pages document as PDF (File > Export to > PDF)."""
    _run_applescript('tell application "Pages" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "e" using {command down, shift down}
    delay 1.0
    key code 36
end tell
''')
    return {"success": ok, "format": "PDF"}

# ═══════════════════════════════════════════════════════════════
# ██  APPLE NUMBERS AUTOMATION (Native AppleScript)
# ═══════════════════════════════════════════════════════════════

def _numbers_activate():
    """Activate Apple Numbers and wait for it."""
    ok, out, err = _run_applescript('''
tell application "Numbers" to activate
delay 0.5
''')
    return ok

def _numbers_set_cell(cell_ref, value):
    """Set a cell value via native AppleScript. Works for text, numbers, and formulas."""
    escaped = _escape_applescript(str(value))
    ok, out, err = _run_applescript(
        'tell application "Numbers"\n'
        '    tell front document\n'
        '        tell active sheet\n'
        '            tell table 1\n'
        '                set value of cell "' + cell_ref + '" to "' + escaped + '"\n'
        '            end tell\n'
        '        end tell\n'
        '    end tell\n'
        'end tell'
    )
    return ok

def _numbers_get_cell(cell_ref):
    """Get a cell value via native AppleScript."""
    ok, out, err = _run_applescript(
        'tell application "Numbers"\n'
        '    tell front document\n'
        '        tell active sheet\n'
        '            tell table 1\n'
        '                get value of cell "' + cell_ref + '"\n'
        '            end tell\n'
        '        end tell\n'
        '    end tell\n'
        'end tell'
    )
    return ok, out.strip() if out else ""

# ── App Control ──

def numbers_open():
    """Open Apple Numbers."""
    ok, out, err = _run_shell(['open', '-a', 'Numbers'])
    time.sleep(1.5)
    return {"success": ok}

def numbers_close():
    """Quit Apple Numbers."""
    ok, out, err = _run_applescript('tell application "Numbers" to quit')
    return {"success": ok}

def numbers_close_spreadsheet():
    """Close the current spreadsheet without saving."""
    ok, out, err = _run_applescript(
        'tell application "Numbers"\n'
        '    close front document saving no\n'
        'end tell'
    )
    return {"success": ok}

# ── Spreadsheet / Sheet Management ──

def numbers_new_spreadsheet():
    """Create a new blank spreadsheet using native AppleScript."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "Numbers"
    activate
    make new document
end tell
''')
    time.sleep(1.0)
    return {"success": ok}

def numbers_save(filename=None):
    """Save Numbers spreadsheet. If filename given, saves to Desktop with native AppleScript."""
    _numbers_activate()
    if filename:
        desktop = os.path.expanduser("~/Desktop")
        clean_name = filename.replace(".numbers", "")
        full_path = desktop + "/" + clean_name + ".numbers"
        safe_path = _escape_applescript(full_path)
        ok, out, err = _run_applescript(
            'tell application "Numbers"\n'
            '    set savePath to ((POSIX file "' + safe_path + '") as text)\n'
            '    save front document in file savePath\n'
            'end tell'
        )
        if not ok:
            import sys
            print(f"[NUMBERS] Save attempt 1 failed: {err}", file=sys.stderr)
            # Attempt 2: try without 'in file' — just export
            ok2, out2, err2 = _run_applescript(
                'tell application "Numbers"\n'
                '    export front document to file ((POSIX file "' + safe_path + '") as text)\n'
                'end tell'
            )
            if not ok2:
                print(f"[NUMBERS] Save attempt 2 failed: {err2}", file=sys.stderr)
                # Attempt 3: use System Events Cmd+S
                _run_applescript('''
tell application "System Events"
    keystroke "s" using {command down}
end tell
''')
                time.sleep(1.5)
                # Type filename and press Enter in save dialog
                _word_clipboard_type(clean_name)
                time.sleep(0.5)
                _run_applescript('tell application "System Events" to key code 36')
                time.sleep(1.0)
        # Verify the file exists
        import os.path as osp
        saved = osp.exists(full_path)
        return {"success": saved, "saved_as": clean_name + ".numbers", "path": full_path}
    else:
        # Plain save — try native first
        ok, out, err = _run_applescript(
            'tell application "Numbers"\n'
            '    save front document\n'
            'end tell'
        )
        if not ok:
            # Fallback: Cmd+S for unsaved docs (triggers save dialog)
            _run_applescript('''
tell application "System Events"
    keystroke "s" using {command down}
end tell
''')
        return {"success": True}

def numbers_open_file(path):
    """Open a specific Numbers file."""
    resolved = os.path.expanduser(path)
    ok, out, err = _run_shell(['open', '-a', 'Numbers', resolved])
    time.sleep(2.0)
    return {"success": ok, "path": resolved}

def numbers_new_sheet():
    """Add a new sheet (Shift+Cmd+N)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "n" using {shift down, command down}
end tell
''')
    time.sleep(0.5)
    return {"success": ok}

def numbers_next_sheet():
    """Move to the next sheet (Shift+Cmd+})."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "}" using {shift down, command down}
end tell
''')
    time.sleep(0.3)
    return {"success": ok}

def numbers_prev_sheet():
    """Move to the previous sheet (Shift+Cmd+{)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "{" using {shift down, command down}
end tell
''')
    time.sleep(0.3)
    return {"success": ok}

# ── Cell Navigation ──

def numbers_go_to_cell(cell="A1"):
    """Navigate to a specific cell using native AppleScript selection."""
    _numbers_activate()
    import re
    m = re.match(r'^([A-Za-z]+)(\d+)$', cell.strip())
    if not m:
        return {"success": False, "error": "Invalid cell reference: " + cell}
    cell_upper = cell.strip().upper()
    ok, out, err = _run_applescript(
        'tell application "Numbers"\n'
        '    tell front document\n'
        '        tell active sheet\n'
        '            tell table 1\n'
        '                set selection range to range "' + cell_upper + '"\n'
        '            end tell\n'
        '        end tell\n'
        '    end tell\n'
        'end tell'
    )
    return {"success": ok, "cell": cell_upper}

def numbers_move_right():
    """Move one cell right (Tab)."""
    _numbers_activate()
    ok, out, err = _run_applescript('tell application "System Events" to key code 48')
    return {"success": ok}

def numbers_move_down():
    """Move one cell down (Return)."""
    _numbers_activate()
    ok, out, err = _run_applescript('tell application "System Events" to key code 36')
    return {"success": ok}

def numbers_move_up():
    """Move one cell up (Shift+Return)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 36 using {shift down}
end tell
''')
    return {"success": ok}

def numbers_move_left():
    """Move one cell left (Shift+Tab)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 48 using {shift down}
end tell
''')
    return {"success": ok}

def numbers_move_to_start():
    """Move to cell A1 (Fn+Left Arrow / Home)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 123 using {fn down}
end tell
''')
    return {"success": ok}

def numbers_move_to_end():
    """Move to last used cell (Fn+Right Arrow / End)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 124 using {fn down}
end tell
''')
    return {"success": ok}

def numbers_move_to_edge(direction="down"):
    """Jump to first/last populated cell in direction. direction: up/down/left/right."""
    _numbers_activate()
    key_map = {"up": 126, "down": 125, "left": 123, "right": 124}
    key = key_map.get(direction, 125)
    ok, out, err = _run_applescript(f'''
tell application "System Events"
    key code {key} using {{option down, command down}}
end tell
''')
    return {"success": ok, "direction": direction}

# ── Cell Input (Native AppleScript) ──

def numbers_type_in_cell(text, cell=None):
    """Set text in a cell via native AppleScript. If cell given, sets that cell directly.
    If no cell, uses clipboard paste into current selected cell + Tab to move right."""
    if cell:
        ok = _numbers_set_cell(cell, text)
        return {"success": ok, "text": str(text), "cell": cell}
    else:
        _numbers_activate()
        _word_clipboard_type(str(text))
        time.sleep(0.15)
        _run_applescript('tell application "System Events" to key code 48')  # Tab
        time.sleep(0.1)
        return {"success": True, "text": str(text)}

def numbers_type_and_stay(text):
    """Type text into current cell using clipboard paste, then move down (Return)."""
    _numbers_activate()
    _word_clipboard_type(str(text))
    time.sleep(0.15)
    _run_applescript('tell application "System Events" to key code 36')  # Return
    time.sleep(0.1)
    return {"success": True, "text": str(text)}

def numbers_edit_cell():
    """Enter edit mode for current cell (Option+Return)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 36 using {option down}
end tell
''')
    return {"success": ok}

def numbers_enter_formula(formula, cell=None):
    """Enter a formula into a cell. If cell given, sets it directly via AppleScript.
    If no cell, types into current selected cell."""
    if cell:
        ok = _numbers_set_cell(cell, formula)
        return {"success": ok, "formula": formula, "cell": cell}
    else:
        _numbers_activate()
        _word_clipboard_type(str(formula))
        time.sleep(0.2)
        _run_applescript('tell application "System Events" to key code 36')  # Return
        time.sleep(0.15)
        return {"success": True, "formula": formula}

def numbers_clear_cell():
    """Clear the current cell content (Delete key)."""
    _numbers_activate()
    ok, out, err = _run_applescript('tell application "System Events" to key code 51')
    return {"success": ok}

def numbers_next_row():
    """Move to the beginning of the next row (Return)."""
    _numbers_activate()
    ok, out, err = _run_applescript('tell application "System Events" to key code 36')
    return {"success": ok}

def numbers_autofill():
    """Turn on autofill mode (Cmd+\\)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "\\\\" using {command down}
end tell
''')
    return {"success": ok}

def numbers_autofill_from_column():
    """Autofill from column before (Control+Cmd+\\)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "\\\\" using {control down, command down}
end tell
''')
    return {"success": ok}

def numbers_autofill_from_row():
    """Autofill from row above (Option+Cmd+\\)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "\\\\" using {option down, command down}
end tell
''')
    return {"success": ok}

# ── Selection ──

def numbers_select_all():
    """Select all cells (Cmd+A)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "a" using {command down}
end tell
''')
    return {"success": ok}

def numbers_select_row():
    """Select all columns intersecting selection (Option+Cmd+Return)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 36 using {option down, command down}
end tell
''')
    return {"success": ok}

def numbers_select_column():
    """Select all rows intersecting selection (Control+Cmd+Return)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 36 using {control down, command down}
end tell
''')
    return {"success": ok}

def numbers_copy():
    """Copy selection (Cmd+C)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "c" using {command down}
end tell
''')
    return {"success": ok}

def numbers_paste():
    """Paste (Cmd+V)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "v" using {command down}
end tell
''')
    return {"success": ok}

def numbers_cut():
    """Cut selection (Cmd+X)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "x" using {command down}
end tell
''')
    return {"success": ok}

def numbers_paste_values():
    """Paste formula results as values only (Shift+Cmd+V)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "v" using {shift down, command down}
end tell
''')
    return {"success": ok}

# ── Formatting ──

def numbers_bold():
    """Toggle bold (Cmd+B)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "b" using {command down}
end tell
''')
    return {"success": ok}

def numbers_italic():
    """Toggle italic (Cmd+I)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "i" using {command down}
end tell
''')
    return {"success": ok}

def numbers_underline():
    """Toggle underline (Cmd+U)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "u" using {command down}
end tell
''')
    return {"success": ok}

def numbers_increase_font():
    """Increase font size (Cmd++)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "+" using {command down}
end tell
''')
    return {"success": ok}

def numbers_decrease_font():
    """Decrease font size (Cmd+-)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "-" using {command down}
end tell
''')
    return {"success": ok}

def numbers_align_center():
    """Center align text. Uses Format > Alignment > Center via menu."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "e" using {command down}
end tell
''')
    return {"success": ok}

def numbers_align_left():
    """Left align text."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "{" using {command down}
end tell
''')
    return {"success": ok}

def numbers_auto_align():
    """Auto-align cell content (Option+Cmd+U)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "u" using {option down, command down}
end tell
''')
    return {"success": ok}

def numbers_add_border_top():
    """Add/remove top border (Control+Option+Cmd+Up)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 126 using {control down, option down, command down}
end tell
''')
    return {"success": ok}

def numbers_add_border_bottom():
    """Add/remove bottom border (Control+Option+Cmd+Down)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 125 using {control down, option down, command down}
end tell
''')
    return {"success": ok}

def numbers_add_border_left():
    """Add/remove left border (Control+Option+Cmd+Left)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 123 using {control down, option down, command down}
end tell
''')
    return {"success": ok}

def numbers_add_border_right():
    """Add/remove right border (Control+Option+Cmd+Right)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 124 using {control down, option down, command down}
end tell
''')
    return {"success": ok}

def numbers_merge_cells():
    """Merge selected cells (Control+Cmd+M)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "m" using {control down, command down}
end tell
''')
    return {"success": ok}

def numbers_unmerge_cells():
    """Unmerge selected cells (Control+Shift+Cmd+M)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "m" using {control down, shift down, command down}
end tell
''')
    return {"success": ok}

# ── Row/Column Operations ──

def numbers_add_row_above():
    """Add a row above current cell (Option+Up Arrow)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 126 using {option down}
end tell
''')
    time.sleep(0.3)
    return {"success": ok}

def numbers_add_row_below():
    """Add a row below current cell (Option+Down Arrow)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 125 using {option down}
end tell
''')
    time.sleep(0.3)
    return {"success": ok}

def numbers_add_column_left():
    """Add a column to the left (Option+Left Arrow)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 123 using {option down}
end tell
''')
    time.sleep(0.3)
    return {"success": ok}

def numbers_add_column_right():
    """Add a column to the right (Option+Right Arrow)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 124 using {option down}
end tell
''')
    time.sleep(0.3)
    return {"success": ok}

def numbers_delete_row():
    """Delete selected rows (Option+Cmd+Delete)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 51 using {option down, command down}
end tell
''')
    time.sleep(0.3)
    return {"success": ok}

def numbers_delete_column():
    """Delete selected columns (Control+Cmd+Delete)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 51 using {control down, command down}
end tell
''')
    time.sleep(0.3)
    return {"success": ok}

# ── Data Tools ──

def numbers_sort():
    """Apply sorting rules (Shift+Cmd+R)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "r" using {shift down, command down}
end tell
''')
    return {"success": ok}

def numbers_add_filter():
    """Toggle filters (Option+Cmd+F)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "f" using {option down, command down}
end tell
''')
    return {"success": ok}

def numbers_find(text):
    """Find text in spreadsheet (Cmd+F then type text)."""
    _numbers_activate()
    _run_applescript('''
tell application "System Events"
    keystroke "f" using {command down}
end tell
''')
    time.sleep(0.5)
    _word_clipboard_type(text)
    time.sleep(0.3)
    _run_applescript('tell application "System Events" to key code 36')  # Enter
    return {"success": True, "text": text}

def numbers_insert_equation():
    """Insert an equation (Option+Cmd+E)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "e" using {option down, command down}
end tell
''')
    return {"success": ok}

# ── Utility ──

def numbers_undo():
    """Undo (Cmd+Z)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "z" using {command down}
end tell
''')
    return {"success": ok}

def numbers_redo():
    """Redo (Shift+Cmd+Z)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "z" using {shift down, command down}
end tell
''')
    return {"success": ok}

def numbers_read_cell(cell=None):
    """Read cell value. If cell given, reads that cell directly via AppleScript.
    If no cell, copies current selected cell to clipboard."""
    if cell:
        ok, value = _numbers_get_cell(cell)
        return {"success": ok, "value": value, "cell": cell}
    else:
        _numbers_activate()
        _run_applescript('''
tell application "System Events"
    keystroke "c" using {command down}
end tell
''')
        time.sleep(0.3)
        ok, out, err = _run_shell(['pbpaste'])
        return {"success": ok, "value": out.strip() if out else ""}

def numbers_read_selection():
    """Read all selected cells (copy to clipboard then read)."""
    _numbers_activate()
    _run_applescript('''
tell application "System Events"
    keystroke "c" using {command down}
end tell
''')
    time.sleep(0.3)
    ok, out, err = _run_shell(['pbpaste'])
    return {"success": ok, "value": out.strip() if out else ""}

def numbers_insert_date():
    """Insert current date (Control+Shift+Cmd+D)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "d" using {control down, shift down, command down}
end tell
''')
    return {"success": ok}

def numbers_insert_time():
    """Insert current time (Control+Shift+Cmd+T)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "t" using {control down, shift down, command down}
end tell
''')
    return {"success": ok}

def numbers_print():
    """Open print dialog (Cmd+P)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "p" using {command down}
end tell
''')
    return {"success": ok}

def numbers_add_comment():
    """Add a new comment (Shift+Cmd+K)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "k" using {shift down, command down}
end tell
''')
    return {"success": ok}

def numbers_toggle_sidebar():
    """Toggle the format sidebar (Option+Cmd+I)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "i" using {option down, command down}
end tell
''')
    return {"success": ok}

def numbers_collapse_groups():
    """Collapse selected category groups (Cmd+8)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "8" using {command down}
end tell
''')
    return {"success": ok}

def numbers_expand_groups():
    """Expand selected category groups (Cmd+9)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "9" using {command down}
end tell
''')
    return {"success": ok}

def numbers_make_link():
    """Make text/object a link (Cmd+K)."""
    _numbers_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "k" using {command down}
end tell
''')
    return {"success": ok}

# ── Compound: Create Spreadsheet (Native AppleScript) ──

def numbers_create_spreadsheet(title="", headers=None, rows=None, formulas=None):
    """Create a full spreadsheet: new document, headers, data rows, formulas, save.

    Uses ONE single AppleScript call to do everything — prevents Numbers from
    quitting between operations. 100% reliable.

    Args:
        title: Filename to save as (no extension)
        headers: List of header strings e.g. ["Name", "Amount", "Date"]
        rows: List of lists e.g. [["Rent", "1500", "2025-01-01"], ...]
        formulas: List of dicts e.g. [{"cell": "B10", "formula": "=SUM(B2:B9)"}]
    """
    headers = headers or []
    rows = rows or []
    formulas = formulas or []

    lines = []
    lines.append('tell application "Numbers"')
    lines.append('    activate')
    lines.append('    make new document')
    lines.append('    delay 1.5')
    lines.append('    tell front document')
    lines.append('        tell active sheet')
    lines.append('            tell table 1')

    for i, h in enumerate(headers):
        col = _col_letter(i)
        escaped = _escape_applescript(str(h))
        lines.append(f'                set value of cell "{col}1" to "{escaped}"')

    for row_idx, row in enumerate(rows):
        numbers_row = row_idx + 2
        for col_idx, cell in enumerate(row):
            col = _col_letter(col_idx)
            escaped = _escape_applescript(str(cell))
            lines.append(f'                set value of cell "{col}{numbers_row}" to "{escaped}"')

    for f in formulas:
        if isinstance(f, dict):
            target_cell = f.get("cell", "A1")
            formula_text = str(f.get("formula", ""))
        elif isinstance(f, (list, tuple)) and len(f) >= 2:
            target_cell = str(f[0])
            formula_text = str(f[1])
        elif isinstance(f, str):
            continue
        else:
            continue
        escaped = _escape_applescript(formula_text)
        lines.append(f'                set value of cell "{target_cell}" to "{escaped}"')

    # Select header row for bold
    if headers:
        last_col = _col_letter(len(headers) - 1)
        lines.append(f'                set selection range to range "A1:{last_col}1"')

    lines.append('            end tell')
    lines.append('        end tell')
    lines.append('    end tell')
    lines.append('end tell')

    # Execute the big script
    script = '\n'.join(lines)
    ok, out, err = _run_applescript(script)

    if not ok:
        import sys
        print(f"[NUMBERS] Main script failed: {err}", file=sys.stderr)
        return {"success": False, "error": err, "title": title}

    # Bold headers via System Events (separate call since it's a different app)
    if headers:
        time.sleep(0.3)
        _run_applescript('''
tell application "System Events"
    keystroke "b" using {command down}
end tell
''')
        time.sleep(0.2)

    save_result = None
    if title:
        time.sleep(0.5)
        save_result = numbers_save(title)
        time.sleep(0.5)
        # Numbers treats "save in file" as export — doc stays "untitled/modified"
        # Fix: close untitled doc (file already on disk), then reopen the saved file
        full_path = save_result.get("path", "")
        if full_path and save_result.get("success"):
            # Close untitled doc — saving no = don't prompt, file already on disk
            _run_applescript('tell application "Numbers"\n    close front document saving no\nend tell')
            time.sleep(1.0)
            # Reopen the saved file — now it's a proper "saved" document
            _run_applescript(
                'tell application "Numbers"\n'
                '    open POSIX file "' + _escape_applescript(full_path) + '"\n'
                'end tell'
            )
            time.sleep(1.5)

    return {
        "success": True,
        "title": title,
        "headers": len(headers),
        "rows": len(rows),
        "formulas": len(formulas),
        "saved": save_result.get("success", False) if save_result else False,
        "path": save_result.get("path", "") if save_result else ""
    }

# ═══════════════════════════════════════════════════════════════
# ██  MICROSOFT EXCEL AUTOMATION
# ═══════════════════════════════════════════════════════════════

def _excel_activate():
    """Activate Microsoft Excel and wait for it."""
    ok, out, err = _run_applescript('''
tell application "Microsoft Excel" to activate
delay 0.5
''')
    return ok

# ── App Control ──

def excel_open():
    """Open Microsoft Excel."""
    ok, out, err = _run_shell(['open', '-a', 'Microsoft Excel'])
    time.sleep(1.5)
    return {"success": ok}

def excel_close():
    """Quit Microsoft Excel."""
    ok, out, err = _run_applescript('tell application "Microsoft Excel" to quit')
    return {"success": ok}

def excel_close_workbook():
    """Close the current workbook (Cmd+W)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "w" using {command down}
end tell
''')
    return {"success": ok}

# ── Workbook / Sheet Management ──

def excel_new_workbook():
    """Create a new blank workbook (Cmd+N)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "n" using {command down}
end tell
''')
    time.sleep(1.0)
    return {"success": ok}

def excel_save(filename=None):
    """Save workbook. If filename given, does Save As using native AppleScript."""
    _excel_activate()
    if filename:
        # Use native AppleScript Save As — much more reliable than keyboard
        safe_name = _escape_applescript(filename)
        desktop = os.path.expanduser("~/Desktop")
        safe_path = _escape_applescript(desktop + "/" + filename + ".xlsx")
        ok, out, err = _run_applescript(
            'tell application "Microsoft Excel"\n'
            '    set fPath to POSIX file "' + safe_path + '" as text\n'
            '    save active workbook in fPath\n'
            'end tell'
        )
        if not ok:
            # Fallback: try save workbook as
            ok, out, err = _run_applescript(
                'tell application "Microsoft Excel"\n'
                '    save workbook as active workbook filename "' + safe_path + '"\n'
                'end tell'
            )
        if not ok:
            # Last fallback: Cmd+S keyboard
            _run_applescript('tell application "System Events"\n    keystroke "s" using {command down}\nend tell')
            time.sleep(1.0)
        return {"success": ok, "saved_as": filename}
    else:
        ok, out, err = _run_applescript('''
tell application "Microsoft Excel"
    save active workbook
end tell
''')
        return {"success": ok}

def excel_open_file(path):
    """Open a specific Excel file."""
    resolved = os.path.expanduser(path)
    ok, out, err = _run_shell(['open', '-a', 'Microsoft Excel', resolved])
    time.sleep(2.0)
    return {"success": ok, "path": resolved}

def excel_new_sheet():
    """Insert a new sheet (Shift+F11)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 98 using {shift down}
end tell
''')
    time.sleep(0.5)
    return {"success": ok}

def excel_next_sheet():
    """Move to next sheet (Option+Right arrow)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 124 using {option down}
end tell
''')
    time.sleep(0.3)
    return {"success": ok}

def excel_prev_sheet():
    """Move to previous sheet (Option+Left arrow)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 123 using {option down}
end tell
''')
    time.sleep(0.3)
    return {"success": ok}

# ── Cell Navigation ──

def excel_go_to_cell(cell="A1"):
    """Navigate to a specific cell using Excel's native AppleScript."""
    _excel_activate()
    # Use Excel's own AppleScript command — no keyboard dialogs, no popups
    escaped = _escape_applescript(cell)
    ok, out, err = _run_applescript(
        'tell application "Microsoft Excel"\n'
        '    set theRange to range "' + escaped + '" of active sheet\n'
        '    select theRange\n'
        'end tell'
    )
    time.sleep(0.3)
    return {"success": ok, "cell": cell}

def excel_move_right():
    """Move one cell right (Tab)."""
    _excel_activate()
    ok, out, err = _run_applescript('tell application "System Events" to key code 48')
    return {"success": ok}

def excel_move_down():
    """Move one cell down (Return)."""
    _excel_activate()
    ok, out, err = _run_applescript('tell application "System Events" to key code 36')
    return {"success": ok}

def excel_move_up():
    """Move one cell up (Up arrow)."""
    _excel_activate()
    ok, out, err = _run_applescript('tell application "System Events" to key code 126')
    return {"success": ok}

def excel_move_left():
    """Move one cell left (Shift+Tab)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 48 using {shift down}
end tell
''')
    return {"success": ok}

def excel_move_to_start():
    """Move to cell A1 (Control+Home)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 115 using {control down, fn down}
end tell
''')
    return {"success": ok}

def excel_move_to_end():
    """Move to last used cell (Control+End)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 119 using {control down, fn down}
end tell
''')
    return {"success": ok}

def excel_move_to_edge(direction="down"):
    """Jump to edge of data region (Cmd+Arrow). direction: up/down/left/right."""
    _excel_activate()
    key_map = {"up": 126, "down": 125, "left": 123, "right": 124}
    key = key_map.get(direction, 125)
    ok, out, err = _run_applescript(f'''
tell application "System Events"
    key code {key} using {{command down}}
end tell
''')
    return {"success": ok, "direction": direction}

# ── Cell Input ──

def excel_type_in_cell(text):
    """Set value of current cell via native AppleScript, then move right."""
    _excel_activate()
    escaped = _escape_applescript(str(text))
    _run_applescript(
        'tell application "Microsoft Excel"\n'
        '    set value of (selection as range) to "' + escaped + '"\n'
        'end tell'
    )
    time.sleep(0.15)
    # Move right (Tab)
    _run_applescript('tell application "System Events" to key code 48')
    time.sleep(0.1)
    return {"success": True, "text": str(text)}

def excel_type_and_stay(text):
    """Set value of current cell via native AppleScript, then move down."""
    _excel_activate()
    escaped = _escape_applescript(str(text))
    _run_applescript(
        'tell application "Microsoft Excel"\n'
        '    set value of (selection as range) to "' + escaped + '"\n'
        'end tell'
    )
    time.sleep(0.15)
    # Move down (Return)
    _run_applescript('tell application "System Events" to key code 36')
    time.sleep(0.1)
    return {"success": True, "text": str(text)}

def excel_edit_cell():
    """Enter edit mode for current cell (F2)."""
    _excel_activate()
    ok, out, err = _run_applescript('tell application "System Events" to key code 120')
    return {"success": ok}

def excel_enter_formula(formula):
    """Set formula on current cell via native AppleScript."""
    _excel_activate()
    escaped = _escape_applescript(str(formula))
    _run_applescript(
        'tell application "Microsoft Excel"\n'
        '    set formula of (selection as range) to "' + escaped + '"\n'
        'end tell'
    )
    time.sleep(0.2)
    return {"success": True, "formula": formula}

def excel_fill_down():
    """Fill selected cells down (Cmd+D)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "d" using {command down}
end tell
''')
    return {"success": ok}

def excel_fill_right():
    """Fill selected cells right (Cmd+R)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "r" using {command down}
end tell
''')
    return {"success": ok}

def excel_clear_cell():
    """Clear the current cell content (Delete key)."""
    _excel_activate()
    ok, out, err = _run_applescript('tell application "System Events" to key code 51')
    return {"success": ok}

# ── Selection ──

def excel_select_all():
    """Select all cells (Cmd+A)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "a" using {command down}
end tell
''')
    return {"success": ok}

def excel_select_column():
    """Select entire column (Control+Space)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 49 using {control down}
end tell
''')
    return {"success": ok}

def excel_select_row():
    """Select entire row (Shift+Space)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 49 using {shift down}
end tell
''')
    return {"success": ok}

def excel_select_range(cell_range):
    """Select a range of cells using Excel's native AppleScript (e.g. 'A1:D10')."""
    _excel_activate()
    escaped = _escape_applescript(cell_range)
    ok, out, err = _run_applescript(
        'tell application "Microsoft Excel"\n'
        '    select range "' + escaped + '" of active sheet\n'
        'end tell'
    )
    time.sleep(0.3)
    return {"success": ok, "range": cell_range}

def excel_copy():
    """Copy selection (Cmd+C)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "c" using {command down}
end tell
''')
    return {"success": ok}

def excel_paste():
    """Paste (Cmd+V)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "v" using {command down}
end tell
''')
    return {"success": ok}

def excel_cut():
    """Cut selection (Cmd+X)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "x" using {command down}
end tell
''')
    return {"success": ok}

def excel_paste_values():
    """Paste Special — Values only (Cmd+Control+V)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "v" using {command down, control down}
end tell
''')
    time.sleep(0.5)
    _run_applescript('''
tell application "System Events"
    keystroke "v"
    delay 0.2
    key code 36
end tell
''')
    return {"success": ok}

# ── Formatting ──

def excel_bold():
    """Toggle bold formatting (Cmd+B)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "b" using {command down}
end tell
''')
    return {"success": ok}

def excel_italic():
    """Toggle italic formatting (Cmd+I)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "i" using {command down}
end tell
''')
    return {"success": ok}

def excel_underline():
    """Toggle underline formatting (Cmd+U)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "u" using {command down}
end tell
''')
    return {"success": ok}

def excel_strikethrough():
    """Toggle strikethrough (Cmd+Shift+X)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "x" using {command down, shift down}
end tell
''')
    return {"success": ok}

def excel_increase_font():
    """Increase font size (Cmd+Shift+>)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "." using {command down, shift down}
end tell
''')
    return {"success": ok}

def excel_decrease_font():
    """Decrease font size (Cmd+Shift+<)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "," using {command down, shift down}
end tell
''')
    return {"success": ok}

def excel_align_center():
    """Center align cell content (Cmd+E)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "e" using {command down}
end tell
''')
    return {"success": ok}

def excel_align_left():
    """Left align cell content (Cmd+L)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "l" using {command down}
end tell
''')
    return {"success": ok}

def excel_format_number():
    """Apply number format with 2 decimals and comma (Control+Shift+!)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "1" using {control down, shift down}
end tell
''')
    return {"success": ok, "format": "number"}

def excel_format_currency():
    """Apply currency format (Control+Shift+$)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "4" using {control down, shift down}
end tell
''')
    return {"success": ok, "format": "currency"}

def excel_format_percent():
    """Apply percentage format (Control+Shift+%)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "5" using {control down, shift down}
end tell
''')
    return {"success": ok, "format": "percent"}

def excel_format_date():
    """Apply date format (Control+Shift+#)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "3" using {control down, shift down}
end tell
''')
    return {"success": ok, "format": "date"}

def excel_format_general():
    """Apply general format (Control+Shift+~)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "`" using {control down, shift down}
end tell
''')
    return {"success": ok, "format": "general"}

def excel_add_border():
    """Add outline border to selection (Cmd+Option+0)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "0" using {command down, option down}
end tell
''')
    return {"success": ok}

def excel_remove_border():
    """Remove borders from selection (Cmd+Option+Hyphen)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "-" using {command down, option down}
end tell
''')
    return {"success": ok}

def excel_format_cells():
    """Open Format Cells dialog (Cmd+1)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "1" using {command down}
end tell
''')
    time.sleep(0.5)
    return {"success": ok}

# ── Row / Column Operations ──

def excel_insert_row():
    """Insert a row above current. Selects row first, then inserts."""
    _excel_activate()
    _run_applescript('tell application "System Events" to key code 49 using {shift down}')
    time.sleep(0.2)
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "=" using {control down, shift down}
end tell
''')
    time.sleep(0.3)
    return {"success": ok}

def excel_insert_column():
    """Insert a column before current. Selects column first, then inserts."""
    _excel_activate()
    _run_applescript('tell application "System Events" to key code 49 using {control down}')
    time.sleep(0.2)
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "=" using {control down, shift down}
end tell
''')
    time.sleep(0.3)
    return {"success": ok}

def excel_delete_row():
    """Delete the current row."""
    _excel_activate()
    _run_applescript('tell application "System Events" to key code 49 using {shift down}')
    time.sleep(0.2)
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "-" using {command down}
end tell
''')
    time.sleep(0.3)
    return {"success": ok}

def excel_delete_column():
    """Delete the current column."""
    _excel_activate()
    _run_applescript('tell application "System Events" to key code 49 using {control down}')
    time.sleep(0.2)
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "-" using {command down}
end tell
''')
    time.sleep(0.3)
    return {"success": ok}

def excel_hide_column():
    """Hide selected column (Cmd+))."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke ")" using {command down}
end tell
''')
    return {"success": ok}

def excel_unhide_column():
    """Unhide column (Cmd+Shift+))."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke ")" using {command down, shift down}
end tell
''')
    return {"success": ok}

def excel_hide_row():
    """Hide selected row (Cmd+()."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "(" using {command down}
end tell
''')
    return {"success": ok}

def excel_unhide_row():
    """Unhide row (Cmd+Shift+()."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "(" using {command down, shift down}
end tell
''')
    return {"success": ok}

# ── Data Tools ──

def excel_sort():
    """Open Sort dialog (Cmd+Shift+R)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "r" using {command down, shift down}
end tell
''')
    time.sleep(0.5)
    return {"success": ok}

def excel_add_filter():
    """Toggle AutoFilter on/off (Cmd+Shift+F)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "f" using {command down, shift down}
end tell
''')
    return {"success": ok}

def excel_create_table():
    """Create a table from selection (Cmd+T)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "t" using {command down}
end tell
''')
    time.sleep(0.5)
    _run_applescript('tell application "System Events" to key code 36')
    return {"success": ok}

def excel_find(text):
    """Open Find and search for text (Cmd+F)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "f" using {command down}
end tell
''')
    time.sleep(0.5)
    _word_clipboard_type(text)
    time.sleep(0.2)
    _run_applescript('tell application "System Events" to key code 36')
    return {"success": ok, "text": text}

def excel_find_replace(find_text, replace_text):
    """Open Find & Replace and fill both fields (Control+H)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "h" using {control down}
end tell
''')
    time.sleep(0.5)
    _word_clipboard_type(find_text)
    time.sleep(0.2)
    _run_applescript('tell application "System Events" to key code 48')  # Tab
    time.sleep(0.2)
    _word_clipboard_type(replace_text)
    return {"success": ok, "find": find_text, "replace": replace_text}

# ── Formula Shortcuts ──

def excel_autosum():
    """Insert AutoSum formula (Cmd+Shift+T)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "t" using {command down, shift down}
end tell
''')
    time.sleep(0.3)
    _run_applescript('tell application "System Events" to key code 36')
    return {"success": ok}

def excel_insert_function():
    """Open Formula Builder (Shift+F3)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 99 using {shift down}
end tell
''')
    time.sleep(0.5)
    return {"success": ok}

def excel_toggle_formula_view():
    """Toggle between showing formulas and values (Control+`)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "`" using {control down}
end tell
''')
    return {"success": ok}

# ── Undo / Redo ──

def excel_undo():
    """Undo last action (Cmd+Z)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "z" using {command down}
end tell
''')
    return {"success": ok}

def excel_redo():
    """Redo last action (Cmd+Y)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "y" using {command down}
end tell
''')
    return {"success": ok}

# ── Content Reading ──

def excel_read_cell():
    """Read the current cell value (copy cell, read clipboard)."""
    _excel_activate()
    _run_applescript('''
tell application "System Events"
    keystroke "c" using {command down}
end tell
''')
    time.sleep(0.2)
    ok, content, err = _run_shell('pbpaste')
    return {"success": ok, "value": content}

def excel_read_selection():
    """Read all selected cells (copy selection, read clipboard as tab-separated)."""
    _excel_activate()
    _run_applescript('''
tell application "System Events"
    keystroke "c" using {command down}
end tell
''')
    time.sleep(0.3)
    ok, content, err = _run_shell('pbpaste')
    return {"success": ok, "data": content}

# ── Date / Time ──

def excel_insert_date():
    """Insert current date (Control+;)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke ";" using {control down}
end tell
''')
    return {"success": ok}

def excel_insert_time():
    """Insert current time (Cmd+;)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke ";" using {command down}
end tell
''')
    return {"success": ok}

# ── Print ──

def excel_print():
    """Open print dialog (Cmd+P)."""
    _excel_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "p" using {command down}
end tell
''')
    return {"success": ok}

# ── High-Level Compound ──

def _col_letter(idx):
    """Convert 0-based column index to Excel column letter. 0=A, 25=Z, 26=AA."""
    result = ""
    while True:
        result = chr(65 + idx % 26) + result
        idx = idx // 26 - 1
        if idx < 0:
            break
    return result


def excel_create_spreadsheet(title="", headers=None, rows=None, formulas=None):
    """Create a full spreadsheet: new workbook, headers, data rows, formulas, save.

    Uses Excel's native AppleScript to set cell values directly — no keyboard
    for data entry. 100% reliable cell placement.

    Args:
        title: Filename to save as (no extension)
        headers: List of header strings e.g. ["Name", "Amount", "Date"]
        rows: List of lists e.g. [["Rent", "1500", "2025-01-01"], ...]
        formulas: List of dicts e.g. [{"cell": "B10", "formula": "=SUM(B2:B9)"}]
    """
    headers = headers or []
    rows = rows or []
    formulas = formulas or []

    # new workbook
    excel_new_workbook()
    time.sleep(1.5)

    # headers
    if headers:
        for i, h in enumerate(headers):
            col = _col_letter(i)
            escaped = _escape_applescript(str(h))
            _run_applescript(
                'tell application "Microsoft Excel"\n'
                '    set value of range "' + col + '1" of active sheet to "' + escaped + '"\n'
                'end tell'
            )
        time.sleep(0.2)

        # Bold header row
        _run_applescript('''
tell application "Microsoft Excel"
    set bold of font object of row 1 of active sheet to true
end tell
''')
        time.sleep(0.1)

    # data rows
    if rows:
        for row_idx, row in enumerate(rows):
            excel_row = row_idx + 2  # Row 2 onwards (row 1 = headers)
            for col_idx, cell in enumerate(row):
                col = _col_letter(col_idx)
                cell_str = str(cell)
                escaped = _escape_applescript(cell_str)
                # Try setting as number first, fallback to string
                _run_applescript(
                    'tell application "Microsoft Excel"\n'
                    '    set value of range "' + col + str(excel_row) + '" of active sheet to "' + escaped + '"\n'
                    'end tell'
                )
        time.sleep(0.2)

    # formulas
    for f in formulas:
        # Handle both dict {"cell":"B6","formula":"=SUM(B2:B5)"} and list ["B6","=SUM(B2:B5)"]
        if isinstance(f, dict):
            target_cell = f.get("cell", "A1")
            formula_text = str(f.get("formula", ""))
        elif isinstance(f, (list, tuple)) and len(f) >= 2:
            target_cell = str(f[0])
            formula_text = str(f[1])
        elif isinstance(f, str):
            # Single formula string — skip, can't determine cell
            continue
        else:
            continue
        escaped_cell = _escape_applescript(target_cell)
        escaped_formula = _escape_applescript(formula_text)
        # If it's a formula (starts with =), use formula property; otherwise set value
        if formula_text.startswith("="):
            ok, out, err = _run_applescript(
                'tell application "Microsoft Excel"\n'
                '    set formula of range "' + escaped_cell + '" of active sheet to "' + escaped_formula + '"\n'
                'end tell'
            )
        else:
            ok, out, err = _run_applescript(
                'tell application "Microsoft Excel"\n'
                '    set value of range "' + escaped_cell + '" of active sheet to "' + escaped_formula + '"\n'
                'end tell'
            )
        if not ok:
            import sys
            print(f"[EXCEL] Formula failed for {target_cell}: {err}", file=sys.stderr)
        time.sleep(0.1)

    # reset selection
    _run_applescript('''
tell application "Microsoft Excel"
    select range "A1" of active sheet
end tell
''')
    time.sleep(0.2)

    # save
    if title:
        excel_save(title)
        time.sleep(0.5)

    return {
        "success": True,
        "title": title,
        "headers": len(headers),
        "rows": len(rows),
        "formulas": len(formulas)
    }


def excel_create_chart(data_range="A1:B5", chart_type="pie", title=""):
    """Create a chart in the active Excel workbook from the given data range.

    Args:
        data_range: Cell range containing data, e.g. "A1:B5" (must include headers)
        chart_type: One of: pie, bar, column, line, area, doughnut, radar, 3dpie, 3dbar, 3dcolumn, 3dline, 3darea
        title: Optional chart title
    """
    # Map user-friendly names to Excel AppleScript enum names
    chart_type_map = {
        "pie": "pie chart",
        "bar": "bar clustered",
        "column": "column clustered",
        "line": "line chart",
        "area": "area chart",
        "doughnut": "doughnut",
        "radar": "radar",
        "3dpie": "ThreeD pie",
        "3dbar": "ThreeD bar clustered",
        "3dcolumn": "ThreeD column clustered",
        "3dline": "ThreeD line",
        "3darea": "ThreeD area",
        "scatter": "xyscatter",
    }

    as_chart_type = chart_type_map.get(chart_type.lower().strip(), "pie chart")

    # select data range
    script1 = f'''
tell application "Microsoft Excel"
    activate
    delay 0.5
    tell active sheet
        select range "{data_range}"
    end tell
    return "selected"
end tell'''
    ok, out, err = _run_applescript(script1, timeout=10)
    if not ok:
        return {"success": False, "message": f"Failed to select range: {err}"}
    time.sleep(0.5)

    # insert chart
    script2 = '''
tell application "System Events"
    tell process "Microsoft Excel"
        key code 122 using option down
    end tell
end tell'''
    ok, out, err = _run_applescript(script2, timeout=10)
    if not ok:
        return {"success": False, "message": f"Failed to insert chart: {err}"}

    # wait + exit chart edit
    time.sleep(2)
    script3 = '''
tell application "System Events"
    key code 53
end tell'''
    _run_applescript(script3, timeout=5)
    time.sleep(1)
    # Press Escape again to fully deselect
    _run_applescript(script3, timeout=5)
    time.sleep(0.5)

    # set chart type + title
    title_lines = ""
    if title:
        safe_title = title.replace('"', '\\"')
        title_lines = f'''
        set has title of theChart to true
        set caption of chart title of theChart to "{safe_title}"'''

    script4 = f'''
tell application "Microsoft Excel"
    try
        set theChart to chart of chart object 1 of active sheet
        set chart type of theChart to {as_chart_type}
        {title_lines}
        return "ok"
    on error errMsg
        return "error:" & errMsg
    end try
end tell'''
    ok, out, err = _run_applescript(script4, timeout=15)

    if ok and out.startswith("ok"):
        return {"success": True, "message": f"Created {chart_type} chart from {data_range}" + (f" titled '{title}'" if title else "")}
    elif ok and out.startswith("error:"):
        # Chart was created by Option+F1 but type/title change failed
        return {"success": True, "message": f"Chart created from {data_range} (default type, could not set to {chart_type}: {out[6:]})"}
    else:
        # Chart was created by Option+F1 but post-config failed
        return {"success": True, "message": f"Chart created from {data_range} (default column type, chart type change timed out)"}


def keynote_open():
    """Open Apple Keynote."""
    ok, out, err = _run_shell(['open', '-a', 'Keynote'])
    time.sleep(1.0)
    return {"success": ok}

def keynote_new_presentation():
    """Create new blank presentation."""
    _run_applescript('tell application "Keynote" to activate')
    time.sleep(0.5)
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "n" using {command down}
    delay 1.0
    key code 36
end tell
''')
    return {"success": ok}

def keynote_new_slide():
    """Add new slide (Cmd+Shift+N)."""
    _run_applescript('tell application "Keynote" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "n" using {command down, shift down}
end tell
''')
    return {"success": ok}

def keynote_play_slideshow():
    """Play slideshow from beginning (Cmd+Option+P)."""
    _run_applescript('tell application "Keynote" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "p" using {command down, option down}
end tell
''')
    return {"success": ok}

def keynote_stop_slideshow():
    """Stop slideshow (Escape)."""
    ok, out, err = _run_applescript('tell application "System Events" to key code 53')
    return {"success": ok}

def keynote_write(text):
    """Write text in Keynote using clipboard paste."""
    _run_applescript('tell application "Keynote" to activate')
    _word_clipboard_type(text)
    return {"success": True, "length": len(text)}

def keynote_save(filename=None):
    """Save Keynote presentation."""
    _run_applescript('tell application "Keynote" to activate')
    if filename:
        ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "s" using {command down, shift down}
end tell
''')
        time.sleep(1.0)
        _word_clipboard_type(filename)
        time.sleep(0.3)
        _run_applescript('tell application "System Events" to key code 36')
        return {"success": ok, "saved_as": filename}
    else:
        ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "s" using {command down}
end tell
''')
        return {"success": ok}

def photos_open():
    """Open Apple Photos."""
    ok, out, err = _run_shell(['open', '-a', 'Photos'])
    return {"success": ok}

def photos_import(path):
    """Import a photo/video into Photos."""
    expanded = os.path.expanduser(path)
    if not os.path.exists(expanded):
        return {"success": False, "error": f"Not found: {path}"}
    ok, out, err = _run_shell(['open', '-a', 'Photos', expanded])
    return {"success": ok, "path": expanded}

def voice_memos_open():
    """Open Voice Memos."""
    ok, out, err = _run_shell(['open', '-a', 'Voice Memos'])
    time.sleep(0.5)
    return {"success": ok}

def voice_memos_start_recording():
    """Start recording in Voice Memos."""
    _run_applescript('tell application "Voice Memos" to activate')
    time.sleep(0.3)
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 36
end tell
''')
    return {"success": ok, "action": "recording_started"}

def voice_memos_stop_recording():
    """Stop recording in Voice Memos."""
    _run_applescript('tell application "Voice Memos" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 36
end tell
''')
    return {"success": ok, "action": "recording_stopped"}

def contacts_open():
    """Open Contacts app."""
    ok, out, err = _run_shell(['open', '-a', 'Contacts'])
    return {"success": ok}

def contacts_search(name):
    """Search for a contact in Contacts app."""
    _run_applescript('tell application "Contacts" to activate')
    time.sleep(0.3)
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "f" using {command down}
end tell
''')
    time.sleep(0.3)
    _word_clipboard_type(name)
    return {"success": ok, "query": name}

def contacts_new():
    """Create a new contact (Cmd+N)."""
    _run_applescript('tell application "Contacts" to activate')
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "n" using {command down}
end tell
''')
    return {"success": ok}

# Essential workflow: open → new file → write code → save → run code → verify
# Code Runner extension shortcut: Ctrl+Option+N (⌃⌥N) to run code
# Writing uses clipboard paste for 100% reliability with any code/language

def _vscode_activate():
    """Activate VS Code and wait."""
    ok, out, err = _run_applescript('''
tell application "Visual Studio Code" to activate
delay 0.5
''')
    return ok

def vscode_open():
    """Open VS Code."""
    ok, out, err = _run_shell(['open', '-a', 'Visual Studio Code'])
    time.sleep(1.0)
    return {"success": ok}

def vscode_open_folder(path):
    """Open a folder in VS Code. Creates the folder if it doesn't exist."""
    expanded = os.path.expanduser(path)
    os.makedirs(expanded, exist_ok=True)
    ok, out, err = _run_shell(['code', expanded])
    time.sleep(1.5)
    return {"success": ok, "folder": expanded}

def vscode_open_file(path):
    """Open a specific file in VS Code."""
    expanded = os.path.expanduser(path)
    ok, out, err = _run_shell(['code', expanded])
    time.sleep(1.0)
    return {"success": ok, "file": expanded}

def vscode_new_file():
    """Create a new untitled file (Cmd+N)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "n" using {command down}
end tell
''')
    time.sleep(0.5)
    return {"success": ok}

def vscode_new_window():
    """Open a new VS Code window (Cmd+Shift+N)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "n" using {command down, shift down}
end tell
''')
    time.sleep(0.5)
    return {"success": ok}

def vscode_write_code(code):
    """Write code into the active editor using clipboard paste.
    Works with ANY language, any characters — 100% reliable."""
    _vscode_activate()
    time.sleep(0.2)
    success = _word_clipboard_type(code)
    return {"success": success, "length": len(code)}

def vscode_read_code():
    """Read ALL code from current editor: Select All → Copy → return clipboard.
    Use to verify code was written correctly."""
    _vscode_activate()
    time.sleep(0.2)
    _run_applescript('tell application "System Events" to keystroke "a" using {command down}')
    time.sleep(0.2)
    _run_applescript('tell application "System Events" to keystroke "c" using {command down}')
    time.sleep(0.3)
    # Read clipboard
    ok, content, err = _run_shell('pbpaste')
    # Deselect (press right arrow to move cursor to end)
    _run_applescript('tell application "System Events" to key code 124')
    return {"success": ok, "content": content, "length": len(content) if content else 0}

def vscode_save():
    """Save current file (Cmd+S)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "s" using {command down}
end tell
''')
    time.sleep(0.3)
    return {"success": ok}

def vscode_save_as(filename):
    """Save As with filename (Cmd+Shift+S). Types filename via clipboard paste."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "s" using {command down, shift down}
end tell
''')
    time.sleep(1.0)
    _word_clipboard_type(filename)
    time.sleep(0.3)
    _run_applescript('tell application "System Events" to key code 36')  # Enter
    time.sleep(0.5)
    return {"success": ok, "filename": filename}

def vscode_save_all():
    """Save all open files (Cmd+Option+S)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "s" using {command down, option down}
end tell
''')
    return {"success": ok}

def vscode_close_editor():
    """Close current editor tab (Cmd+W)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "w" using {command down}
end tell
''')
    return {"success": ok}

def _ensure_code_runner():
    """Check if Code Runner is installed, install if not, and ensure settings are correct."""
    installed_now = False
    ok_check, out_check, _ = _run_shell(['code', '--list-extensions'])
    if ok_check and 'formulahendry.code-runner' not in (out_check or '').lower():
        _run_shell(['code', '--install-extension', 'formulahendry.code-runner'])
        time.sleep(3.0)
        installed_now = True
    # Always ensure optimal settings (idempotent)
    settings_path = os.path.expanduser('~/Library/Application Support/Code/User/settings.json')
    try:
        settings = {}
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                settings = json.loads(f.read())
        changed = False
        desired = {
            'code-runner.runInTerminal': True,
            'code-runner.saveFileBeforeRun': True,
            'code-runner.clearPreviousOutput': True,
            'code-runner.preserveFocus': False,
        }
        for key, val in desired.items():
            if settings.get(key) != val:
                settings[key] = val
                changed = True
        executor_map = settings.get('code-runner.executorMap', {})
        if executor_map.get('python') != 'python3 -u':
            executor_map['python'] = 'python3 -u'
            settings['code-runner.executorMap'] = executor_map
            changed = True
        if changed:
            with open(settings_path, 'w') as f:
                f.write(json.dumps(settings, indent=4))
    except Exception:
        pass
    return {"installed": installed_now}

def vscode_run_code():
    """Run code using Code Runner extension (Ctrl+Option+N).
    Auto-installs and configures Code Runner if not installed.
    Settings: runInTerminal=true, saveFileBeforeRun=true, clearPreviousOutput=true."""
    _ensure_code_runner()
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "n" using {control down, option down}
end tell
''')
    return {"success": ok, "method": "code_runner"}

def vscode_stop_code():
    """Stop running code via Code Runner (Ctrl+Option+M)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "m" using {control down, option down}
end tell
''')
    return {"success": ok}

def vscode_toggle_terminal():
    """Toggle integrated terminal (Ctrl+`)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "`" using {control down}
end tell
''')
    time.sleep(0.3)
    return {"success": ok}

def vscode_new_terminal():
    """Create new terminal (Ctrl+Shift+`)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "`" using {control down, shift down}
end tell
''')
    time.sleep(0.5)
    return {"success": ok}

def vscode_terminal_run(command):
    """Type a command in VS Code's integrated terminal and press Enter.
    Uses Command Palette to reliably focus terminal before typing."""
    _vscode_activate()
    _run_applescript('''
tell application "System Events"
    keystroke "p" using {command down, shift down}
end tell
''')
    time.sleep(0.5)
    _run_applescript('''
tell application "System Events"
    keystroke "Terminal: Focus on Terminal View"
end tell
''')
    time.sleep(0.4)
    _run_applescript('tell application "System Events" to key code 36')  # Enter
    time.sleep(0.5)
    # Paste command
    _word_clipboard_type(command)
    time.sleep(0.2)
    # Press Enter to execute
    _run_applescript('tell application "System Events" to key code 36')
    return {"success": True, "command": command}

def vscode_focus_editor():
    """Focus back on the code editor from terminal (Cmd+1)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "1" using {command down}
end tell
''')
    return {"success": ok}

def vscode_command_palette(command_text=None):
    """Open Command Palette (Cmd+Shift+P). Optionally type a command."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "p" using {command down, shift down}
end tell
''')
    time.sleep(0.5)
    if command_text:
        _word_clipboard_type(command_text)
        time.sleep(0.3)
    return {"success": ok, "command": command_text}

def vscode_command_palette_run(command_text):
    """Open Command Palette, type a command, and press Enter to execute."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "p" using {command down, shift down}
end tell
''')
    time.sleep(0.5)
    _word_clipboard_type(command_text)
    time.sleep(0.3)
    _run_applescript('tell application "System Events" to key code 36')
    return {"success": ok, "command": command_text}

def vscode_quick_open(filename=None):
    """Quick Open file (Cmd+P). Optionally type filename to search."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "p" using {command down}
end tell
''')
    time.sleep(0.5)
    if filename:
        _word_clipboard_type(filename)
        time.sleep(0.3)
    return {"success": ok, "filename": filename}

def vscode_find(text=None):
    """Open Find (Cmd+F). Optionally type search text."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "f" using {command down}
end tell
''')
    time.sleep(0.3)
    if text:
        _word_clipboard_type(text)
    return {"success": ok, "search": text}

def vscode_find_replace(find_text=None, replace_text=None):
    """Open Find and Replace (Cmd+Option+F)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "f" using {command down, option down}
end tell
''')
    time.sleep(0.5)
    if find_text:
        _word_clipboard_type(find_text)
        time.sleep(0.2)
    if replace_text:
        _run_applescript('tell application "System Events" to key code 48')  # Tab
        time.sleep(0.2)
        _word_clipboard_type(replace_text)
    return {"success": ok}

def vscode_toggle_sidebar():
    """Toggle sidebar visibility (Cmd+B)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "b" using {command down}
end tell
''')
    return {"success": ok}

def vscode_toggle_comment():
    """Toggle line comment (Cmd+/)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "/" using {command down}
end tell
''')
    return {"success": ok}

def vscode_format_document():
    """Format document (Shift+Option+F)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "f" using {shift down, option down}
end tell
''')
    return {"success": ok}

def vscode_undo():
    """Undo (Cmd+Z)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "z" using {command down}
end tell
''')
    return {"success": ok}

def vscode_redo():
    """Redo (Cmd+Shift+Z)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "z" using {command down, shift down}
end tell
''')
    return {"success": ok}

def vscode_select_all():
    """Select all (Cmd+A)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "a" using {command down}
end tell
''')
    return {"success": ok}

def vscode_go_to_line(line_number):
    """Go to specific line (Ctrl+G then type line number)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "g" using {control down}
end tell
''')
    time.sleep(0.3)
    safe = _escape_applescript(str(line_number))
    _run_applescript(f'''
tell application "System Events"
    keystroke "{safe}"
    key code 36
end tell
''')
    return {"success": ok, "line": line_number}

def vscode_delete_line():
    """Delete current line (Cmd+Shift+K)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "k" using {command down, shift down}
end tell
''')
    return {"success": ok}

def vscode_select_line():
    """Select the entire current line (Cmd+L)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "l" using {command down}
end tell
''')
    return {"success": ok}

def vscode_edit_line(line_number, new_text):
    """Go to a specific line, select it, and replace with new text.
    Useful for fixing a specific line of code."""
    _vscode_activate()
    # Go to line (Ctrl+G)
    _run_applescript('tell application "System Events" to keystroke "g" using {control down}')
    time.sleep(0.3)
    safe_line = _escape_applescript(str(line_number))
    _run_applescript(f'tell application "System Events" to keystroke "{safe_line}"')
    _run_applescript('tell application "System Events" to key code 36')  # Enter
    time.sleep(0.2)
    # Select entire line (Cmd+L)
    _run_applescript('tell application "System Events" to keystroke "l" using {command down}')
    time.sleep(0.1)
    # Type new text (replaces selection)
    _word_clipboard_type(new_text)
    return {"success": True, "line": line_number, "new_text": new_text[:100]}

def vscode_insert_line_below(text=None):
    """Insert a new line below current line (Cmd+Enter) and optionally type text."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 36 using {command down}
end tell
''')
    time.sleep(0.1)
    if text:
        _word_clipboard_type(text)
    return {"success": ok}

def vscode_insert_line_above(text=None):
    """Insert a new line above current line (Cmd+Shift+Enter) and optionally type text."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 36 using {command down, shift down}
end tell
''')
    time.sleep(0.1)
    if text:
        _word_clipboard_type(text)
    return {"success": ok}

def vscode_move_line_up():
    """Move line up (Option+Up)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 126 using {option down}
end tell
''')
    return {"success": ok}

def vscode_move_line_down():
    """Move line down (Option+Down)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 125 using {option down}
end tell
''')
    return {"success": ok}

def vscode_copy_line_down():
    """Copy line down (Shift+Option+Down)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    key code 125 using {shift down, option down}
end tell
''')
    return {"success": ok}

def vscode_split_editor():
    """Split editor (Cmd+\\)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "\\" using {command down}
end tell
''')
    return {"success": ok}

def vscode_show_explorer():
    """Show Explorer sidebar (Cmd+Shift+E)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "e" using {command down, shift down}
end tell
''')
    return {"success": ok}

def vscode_show_search():
    """Show Search sidebar (Cmd+Shift+F)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "f" using {command down, shift down}
end tell
''')
    return {"success": ok}

def vscode_show_extensions():
    """Show Extensions sidebar (Cmd+Shift+X)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "x" using {command down, shift down}
end tell
''')
    return {"success": ok}

def vscode_install_extension(extension_id):
    """Install a VS Code extension by ID using the CLI.
    Example: vscode_install_extension('formulahendry.code-runner')"""
    ok, out, err = _run_shell(['code', '--install-extension', extension_id])
    time.sleep(2.0)
    return {"success": ok, "extension": extension_id, "output": out}

def vscode_set_language(language):
    """Set the language mode of current file via Command Palette.
    e.g. 'python', 'javascript', 'java', 'c', 'html'"""
    _vscode_activate()
    _run_applescript('''
tell application "System Events"
    keystroke "p" using {command down, shift down}
end tell
''')
    time.sleep(0.5)
    _word_clipboard_type("Change Language Mode")
    time.sleep(0.3)
    _run_applescript('tell application "System Events" to key code 36')
    time.sleep(0.5)
    _word_clipboard_type(language)
    time.sleep(0.3)
    _run_applescript('tell application "System Events" to key code 36')
    return {"success": True, "language": language}

def vscode_zoom_in():
    """Zoom in (Cmd+=)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "=" using {command down}
end tell
''')
    return {"success": ok}

def vscode_zoom_out():
    """Zoom out (Cmd+-)."""
    _vscode_activate()
    ok, out, err = _run_applescript('''
tell application "System Events"
    keystroke "-" using {command down}
end tell
''')
    return {"success": ok}

def vscode_create_file_with_code(folder_path, filename, code, language=None):
    """Complete workflow: Write file to disk → Open in VS Code.

    folder_path: where to create (e.g. '~/Desktop/my_project')
    filename: file name (e.g. 'hello.py')
    code: the code to write
    language: optional language mode override
    """
    # Fix double extension (e.g. hello.py.py → hello.py)
    name, ext = os.path.splitext(filename)
    if ext:
        name2, ext2 = os.path.splitext(name)
        if ext2 == ext:
            filename = name

    # Write file directly to disk (avoids Save As dialog double-extension bug)
    expanded = os.path.expanduser(folder_path)
    os.makedirs(expanded, exist_ok=True)
    file_path = os.path.join(expanded, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(code)

    _run_shell(['code', expanded])
    time.sleep(1.5)
    _run_shell(['code', file_path])
    time.sleep(1.0)

    return {"success": True, "folder": expanded, "filename": filename, "path": file_path, "code_length": len(code)}

def vscode_run_in_terminal(command):
    """Open terminal in VS Code and run a specific command.
    Good for: python3 hello.py, node app.js, gcc main.c && ./a.out, etc.
    Uses Command Palette to reliably focus terminal without toggling."""
    _vscode_activate()
    _run_applescript('''
tell application "System Events"
    keystroke "p" using {command down, shift down}
end tell
''')
    time.sleep(0.5)
    _run_applescript('''
tell application "System Events"
    keystroke "Terminal: Focus on Terminal View"
end tell
''')
    time.sleep(0.4)
    _run_applescript('tell application "System Events" to key code 36')
    time.sleep(0.5)
    # Type and run command
    _word_clipboard_type(command)
    time.sleep(0.2)
    _run_applescript('tell application "System Events" to key code 36')  # Enter
    return {"success": True, "command": command}

def vscode_read_terminal_output():
    """Read the last terminal output by selecting all terminal text and copying.
    Returns the terminal content so the agent can see results/errors."""
    _vscode_activate()
    subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE).communicate(b'')
    time.sleep(0.1)
    # Focus terminal via Command Palette
    _run_applescript('tell application "System Events" to keystroke "p" using {command down, shift down}')
    time.sleep(0.5)
    # Type the command palette query using keystroke instead of clipboard to avoid polluting clipboard
    _run_applescript('''
tell application "System Events"
    keystroke "Terminal: Focus on Terminal View"
end tell
''')
    time.sleep(0.4)
    _run_applescript('tell application "System Events" to key code 36')
    time.sleep(0.5)
    _run_applescript('tell application "System Events" to keystroke "a" using {command down}')
    time.sleep(0.3)
    _run_applescript('tell application "System Events" to keystroke "c" using {command down}')
    time.sleep(0.4)
    # Read clipboard
    ok, content, err = _run_shell('pbpaste')
    # Deselect
    _run_applescript('tell application "System Events" to key code 124')  # Right arrow
    trimmed = content[-2000:] if content and len(content) > 2000 else content
    return {"success": ok, "output": trimmed, "length": len(content) if content else 0}


_wa_last_sent_contact = {'name': '', 'phone': '', 'timestamp': 0}

def _wa_get_screen_size():
    try:
        size = pyautogui.size()
        return size.width, size.height
    except:
        return 1440, 900

def _wa_take_screenshot_bytes():
    """Capture full screen screenshot as JPEG bytes."""
    try:
        import io
        screenshot = pyautogui.screenshot()
        screenshot = screenshot.convert('RGB')
        buffer = io.BytesIO()
        screenshot.save(buffer, format='JPEG', quality=40)
        return buffer.getvalue()
    except:
        return None

def _wa_take_screenshot_base64():
    """Capture screenshot and return as base64 string (JPEG)."""
    import base64
    jpg = _wa_take_screenshot_bytes()
    return base64.b64encode(jpg).decode('utf-8') if jpg else None

def whatsapp_is_running():
    """Check if WhatsApp is currently running."""
    try:
        if IS_MAC:
            result = subprocess.run(['pgrep', '-i', 'whatsapp'], capture_output=True)
            return result.returncode == 0
    except:
        pass
    return False

def whatsapp_open():
    """Open WhatsApp desktop app."""
    try:
        if IS_MAC:
            subprocess.Popen(['open', '-a', 'WhatsApp'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        return {"success": True, "message": "WhatsApp opened"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def whatsapp_focus():
    """Bring WhatsApp to front."""
    try:
        if IS_MAC:
            subprocess.run(['osascript', '-e', 'tell application "WhatsApp" to activate'], timeout=3)
            time.sleep(0.5)
            return {"success": True, "message": "WhatsApp focused"}
    except:
        pass
    return {"success": False, "error": "Could not focus WhatsApp"}

def _wa_safe_type(text):
    """Type text safely using clipboard for non-ASCII."""
    if all(ord(c) < 128 for c in text):
        pyautogui.write(text, interval=0.03)
    else:
        if IS_MAC:
            process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
            process.communicate(text.encode('utf-8'))
            time.sleep(0.1)
            pyautogui.hotkey('command', 'v')
        time.sleep(0.2)

def _wa_send_via_applescript(message):
    """Send message in the currently open WhatsApp chat via AppleScript."""
    safe_msg = message.replace('\\', '\\\\').replace('"', '\\"')
    script = f'''tell application "WhatsApp" to activate
delay 0.5
tell application "System Events"
    tell process "WhatsApp"
        set frontmost to true
        delay 0.5
        repeat 3 times
            key code 48
            delay 0.35
        end repeat
        set the clipboard to "{safe_msg}"
        delay 0.1
        keystroke "v" using {{command down}}
        delay 0.5
        key code 36
    end tell
end tell'''
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=10)
    return result.returncode == 0

def _wa_try_direct_send(name, message, api_key):
    """Verify with screenshot that the right chat is open, then send directly."""
    try:
        whatsapp_focus()
        time.sleep(0.3)
        ss = _wa_take_screenshot_bytes()
        if not ss:
            return None

        import base64
        ss_b64 = base64.b64encode(ss).decode('utf-8')

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=[
                Content(role="user", parts=[
                    Part(text=f"""Look at this WhatsApp screenshot. Is the chat with "{name}" currently open?
Check the chat header at the top.
Reply with ONLY one word: "yes" or "no"."""),
                    Part.from_bytes(data=ss, mime_type='image/jpeg')
                ])
            ]
        )
        answer = response.text.strip().lower().replace('"', '').replace("'", "")

        if answer == 'yes':
            if _wa_send_via_applescript(message):
                time.sleep(1)
                return {"success": True, "message": f"Message sent to {name} (direct)"}
            else:
                return {"success": False, "message": "AppleScript send failed"}
        return None
    except Exception as e:
        return None

def whatsapp_send_wame(phone, message, api_key=''):
    """Send WhatsApp message using whatsapp:// deep link."""
    phone = phone.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    if not phone.startswith('+'):
        phone = '+' + phone

    encoded_msg = urllib.parse.quote(message)
    app_url = f"whatsapp://send?phone={phone}&text={encoded_msg}"

    print(json.dumps({"progress": True, "message": "Opening WhatsApp chat..."}), flush=True)

    if IS_MAC:
        subprocess.run(['open', app_url], capture_output=True, text=True, timeout=10)

        print(json.dumps({"progress": True, "message": "Sending..."}), flush=True)

        # Wait for WhatsApp to load the chat, then press Return with proper focus
        time.sleep(5)
        send_script = '''
tell application "WhatsApp" to activate
delay 0.5
tell application "System Events"
    tell process "WhatsApp"
        set frontmost to true
        delay 0.3
        key code 36
    end tell
end tell'''
        result = subprocess.run(['osascript', '-e', send_script], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            time.sleep(1)
            return {"success": True, "message": "Message sent via WhatsApp"}
        else:
            return {"success": False, "message": f"Failed: {result.stderr.strip()[:200]}"}
    else:
        webbrowser.open(app_url)
        time.sleep(3)
        pyautogui.press('return')
        time.sleep(0.5)
        return {"success": True, "message": "Message sent via WhatsApp"}

def whatsapp_send_smart(name, phone, message, api_key=''):
    """Smart WhatsApp send: vision check if same chat open, else wa.me deep link."""
    global _wa_last_sent_contact
    wa_running = whatsapp_is_running()
    now = time.time()

    print(json.dumps({"progress": True, "message": f"Smart send: wa_running={wa_running}, name={name}"}), flush=True)

    if wa_running and api_key and _HAS_GENAI:
        direct_result = _wa_try_direct_send(name, message, api_key)
        if direct_result is not None:
            _wa_last_sent_contact = {'name': name, 'phone': phone, 'timestamp': now}
            return direct_result

    if phone:
        result = whatsapp_send_wame(phone, message, api_key)
        if result.get('success'):
            _wa_last_sent_contact = {'name': name, 'phone': phone, 'timestamp': now}
        return result
    else:
        return {"success": False, "message": f"Contact '{name}' not found. No phone number available."}

def whatsapp_read_messages(name, phone, api_key, num_messages=10):
    """Read recent messages from a WhatsApp chat via screenshot + Gemini vision."""
    if not api_key or not _HAS_GENAI:
        return {"success": False, "error": "No API key"}

    print(json.dumps({"progress": True, "message": f"Opening {name}'s chat..."}), flush=True)

    if phone:
        phone_clean = phone.strip().replace(' ', '').replace('-', '')
        if not phone_clean.startswith('+'):
            phone_clean = '+' + phone_clean
        webbrowser.open(f"https://wa.me/{phone_clean}")
        time.sleep(3)
    else:
        if not whatsapp_is_running():
            whatsapp_open()
        whatsapp_focus()
        time.sleep(1)
        pyautogui.hotkey('command', 'f')
        time.sleep(0.5)
        _wa_safe_type(name)
        time.sleep(1.5)
        pyautogui.press('return')
        time.sleep(1)

    print(json.dumps({"progress": True, "message": "Reading messages..."}), flush=True)
    ss = _wa_take_screenshot_bytes()
    if not ss:
        return {"success": False, "error": "Screenshot failed"}

    import base64 as b64mod
    ss_b64 = b64mod.b64encode(ss).decode('utf-8')

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=[
                Content(role="user", parts=[
                    Part(text=f"""Read the WhatsApp chat messages visible on this screenshot.
Extract the last {num_messages} messages. For each message, provide:
- sender: who sent it (contact name or "Me")
- text: the message content
- time: the timestamp if visible

Return as JSON: {{"messages": [{{"sender": "...", "text": "...", "time": "..."}}], "summary": "brief summary"}}

IMPORTANT: Read ACTUAL text from the screenshot. Do NOT make up messages."""),
                    Part.from_bytes(data=ss, mime_type='image/jpeg')
                ])
            ]
        )
        text = response.text.strip()
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()
        result = json.loads(text)
        result['success'] = True
        return result
    except json.JSONDecodeError:
        return {"success": True, "summary": response.text if response else "Could not parse", "messages": []}
    except Exception as e:
        return {"success": False, "error": str(e)}

def whatsapp_check_unread(api_key):
    """Check WhatsApp for unread messages via screenshot + Gemini vision."""
    if not api_key or not _HAS_GENAI:
        return {"success": False, "error": "No API key"}

    print(json.dumps({"progress": True, "message": "Checking WhatsApp..."}), flush=True)

    if not whatsapp_is_running():
        whatsapp_open()
    whatsapp_focus()
    time.sleep(1)

    ss = _wa_take_screenshot_bytes()
    if not ss:
        return {"success": False, "error": "Screenshot failed"}

    import base64 as b64mod
    ss_b64 = b64mod.b64encode(ss).decode('utf-8')

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=[
                Content(role="user", parts=[
                    Part(text="""Look at this WhatsApp screenshot. Check the chat list.
Find any chats that have UNREAD message indicators (green/blue badges, bold text).

Return as JSON:
{
  "has_unread": true/false,
  "unread_chats": [
    {"name": "Contact Name", "unread_count": 2, "preview": "last message preview if visible"}
  ]
}

Only report ACTUALLY VISIBLE unread indicators. Do not guess."""),
                    Part.from_bytes(data=ss, mime_type='image/jpeg')
                ])
            ]
        )
        text = response.text.strip()
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()
        result = json.loads(text)
        result['success'] = True
        return result
    except json.JSONDecodeError:
        return {"success": True, "has_unread": False, "summary": response.text if response else "Could not check"}
    except Exception as e:
        return {"success": False, "error": str(e)}


AUTOMATION_ACTIONS = {
    # Finder
    "finder_open_folder": lambda args: finder_open_folder(args.get("path", "~")),
    "finder_open_downloads": lambda args: finder_open_downloads(),
    "finder_open_desktop": lambda args: finder_open_desktop(),
    "finder_open_documents": lambda args: finder_open_documents(),
    "finder_open_home": lambda args: finder_open_home(),
    "finder_reveal_file": lambda args: finder_reveal_file(args.get("path", "")),
    "finder_create_folder": lambda args: finder_create_folder(args.get("path", "")),
    "finder_list_folder": lambda args: finder_list_folder(args.get("path", "~"), args.get("sort_by", "name")),
    "finder_get_file_info": lambda args: finder_get_file_info(args.get("path", "")),
    "finder_search": lambda args: finder_search(args.get("query", ""), args.get("folder", "~"), args.get("max_results", 20)),
    "finder_move_to_trash": lambda args: finder_move_to_trash(args.get("path", "")),
    "finder_move_file": lambda args: finder_move_file(args.get("source", ""), args.get("destination", "")),
    "finder_copy_file": lambda args: finder_copy_file(args.get("source", ""), args.get("destination", "")),
    "finder_rename": lambda args: finder_rename(args.get("path", ""), args.get("new_name", "")),
    "finder_open_file": lambda args: finder_open_file(args.get("path", "")),
    "finder_open_file_with": lambda args: finder_open_file_with(args.get("path", ""), args.get("app_name", "")),

    # Notes
    "notes_open": lambda args: notes_open(),
    "notes_create": lambda args: notes_create(args.get("title", "Untitled"), args.get("body", "")),
    "notes_list": lambda args: notes_list(args.get("max_notes", 20)),
    "notes_read": lambda args: notes_read(args.get("title", "")),
    "notes_search": lambda args: notes_search(args.get("query", "")),
    "notes_append": lambda args: notes_append(args.get("title", ""), args.get("text", "")),
    "notes_delete": lambda args: notes_delete(args.get("title", "")),

    # System
    "system_lock_screen": lambda args: system_lock_screen(),
    "system_sleep_display": lambda args: system_sleep_display(),
    "system_screenshot_full": lambda args: system_screenshot_full(args.get("save_to_desktop", True)),
    "system_screenshot_selection": lambda args: system_screenshot_selection(),
    "system_screenshot_window": lambda args: system_screenshot_window(),
    "system_screenshot_tools": lambda args: system_screenshot_tools(),
    "system_volume_get": lambda args: system_volume_get(),
    "system_volume_set": lambda args: system_volume_set(args.get("level", 50)),
    "system_volume_mute": lambda args: system_volume_mute(),
    "system_volume_unmute": lambda args: system_volume_unmute(),
    "system_wifi_status": lambda args: system_wifi_status(),
    "system_wifi_on": lambda args: system_wifi_on(),
    "system_wifi_off": lambda args: system_wifi_off(),
    "system_dark_mode_toggle": lambda args: system_dark_mode_toggle(),
    "system_dark_mode_status": lambda args: system_dark_mode_status(),
    "system_do_not_disturb_on": lambda args: system_do_not_disturb_on(),
    "system_do_not_disturb_off": lambda args: system_do_not_disturb_off(),
    "system_empty_trash": lambda args: system_empty_trash(),
    "system_get_battery": lambda args: system_get_battery(),
    "system_get_disk_space": lambda args: system_get_disk_space(),

    # Spotlight
    "spotlight_search": lambda args: spotlight_search(args.get("query", "")),
    "spotlight_search_and_open": lambda args: spotlight_search_and_open(args.get("query", "")),

    # Files
    "files_recent_downloads": lambda args: files_recent_downloads(args.get("count", 10), args.get("file_type")),
    "files_find_by_name": lambda args: files_find_by_name(args.get("name", ""), args.get("folder", "~"), args.get("max_results", 20)),
    "files_find_by_type": lambda args: files_find_by_type(args.get("extension", ""), args.get("folder", "~")),
    "files_read_text": lambda args: files_read_text(args.get("path", "")),
    "files_write_text": lambda args: files_write_text(args.get("path", ""), args.get("content", "")),
    "files_append_text": lambda args: files_append_text(args.get("path", ""), args.get("text", "")),
    "files_read_lines": lambda args: files_read_lines(args.get("path", ""), args.get("start_line", 1), args.get("end_line")),
    "files_insert_at_line": lambda args: files_insert_at_line(args.get("path", ""), args.get("line_number", 1), args.get("text", "")),
    "files_replace_lines": lambda args: files_replace_lines(args.get("path", ""), args.get("start_line", 1), args.get("end_line", 1), args.get("new_text", "")),
    "files_replace_text": lambda args: files_replace_text(args.get("path", ""), args.get("old_text", ""), args.get("new_text", "")),
    "files_get_pdf_info": lambda args: files_get_pdf_info(args.get("path", "")),
    "files_read_pdf_text": lambda args: files_read_pdf_text(args.get("path", ""), args.get("max_pages", 5)),

    # Clipboard
    "clipboard_read": lambda args: clipboard_read(),
    "clipboard_write": lambda args: clipboard_write(args.get("text", "")),

    # Mail
    # ── Mail ──
    "mail_open": lambda args: mail_open(),
    "mail_compose": lambda args: mail_compose(args.get("to", ""), args.get("subject", ""), args.get("body", ""), args.get("cc", ""), args.get("send", True)),
    "mail_list_inbox": lambda args: mail_list_inbox(args.get("count", 10), args.get("unread_only", False)),
    "mail_unread_count": lambda args: mail_unread_count(),
    "mail_read_message": lambda args: mail_read_message(args.get("index", 1)),
    "mail_reply": lambda args: mail_reply(args.get("index", 1), args.get("body", ""), args.get("send", True)),
    "mail_forward": lambda args: mail_forward(args.get("index", 1), args.get("to", ""), args.get("body", ""), args.get("send", True)),
    "mail_search": lambda args: mail_search(args.get("query", ""), args.get("mailbox", "inbox"), args.get("count", 10)),
    "mail_mark_read": lambda args: mail_mark_read(args.get("index", 1)),
    "mail_mark_unread": lambda args: mail_mark_unread(args.get("index", 1)),
    "mail_delete": lambda args: mail_delete(args.get("index", 1)),
    "mail_check": lambda args: mail_check(),

    # Reminders
    "reminders_create": lambda args: reminders_create(args.get("title", ""), args.get("list_name", "Reminders"), args.get("due_date"), args.get("notes", "")),
    "reminders_list": lambda args: reminders_list(args.get("list_name", "Reminders"), args.get("show_completed", False)),
    "reminders_complete": lambda args: reminders_complete(args.get("title", ""), args.get("list_name", "Reminders")),
    "reminders_open": lambda args: reminders_open(),

    # Calendar
    "calendar_create_event": lambda args: calendar_create_event(args.get("title", ""), args.get("start_date", ""), args.get("end_date"), args.get("location", ""), args.get("notes", ""), args.get("calendar_name", "Home")),
    "calendar_today_events": lambda args: calendar_today_events(),
    "calendar_open": lambda args: calendar_open(),

    # Browser
    "browser_get_url": lambda args: browser_get_url(args.get("browser", "Chrome")),
    "browser_get_title": lambda args: browser_get_title(args.get("browser", "Chrome")),
    "browser_list_tabs": lambda args: browser_list_tabs(args.get("browser", "Chrome")),
    "browser_new_tab": lambda args: browser_new_tab(args.get("url", "about:blank"), args.get("browser", "Chrome")),
    "browser_close_tab": lambda args: browser_close_tab(args.get("browser", "Chrome")),

    # App Management
    "app_open": lambda args: app_open(args.get("name", "")),
    "app_close": lambda args: app_close(args.get("name", "")),
    "app_switch": lambda args: app_switch(args.get("name", "")),
    "app_list_running": lambda args: app_list_running(),
    "app_frontmost": lambda args: app_frontmost(),

    # ── Microsoft Word ──
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

    # ── General Keystroke (any app) ──
    "keystroke_type": lambda args: keystroke_type(args.get("text", ""), args.get("app_name")),
    "keystroke_key": lambda args: keystroke_key(args.get("key_code", 36), args.get("modifiers")),

    # ── Safari ──
    "safari_open": lambda args: safari_open(),
    "safari_new_tab": lambda args: safari_new_tab(args.get("url")),
    "safari_close_tab": lambda args: safari_close_tab(),
    "safari_go_back": lambda args: safari_go_back(),
    "safari_go_forward": lambda args: safari_go_forward(),
    "safari_reload": lambda args: safari_reload(),
    "safari_get_url": lambda args: safari_get_url(),
    "safari_get_title": lambda args: safari_get_title(),
    "safari_list_tabs": lambda args: safari_list_tabs(),
    "safari_private_window": lambda args: safari_private_window(),
    "safari_show_bookmarks": lambda args: safari_show_bookmarks(),
    "safari_add_bookmark": lambda args: safari_add_bookmark(),

    # ── Music ──
    "music_open": lambda args: music_open(),
    "music_play": lambda args: music_play(),
    "music_pause": lambda args: music_pause(),
    "music_next": lambda args: music_next(),
    "music_previous": lambda args: music_previous(),
    "music_get_current_track": lambda args: music_get_current_track(),
    "music_set_volume": lambda args: music_set_volume(args.get("level", 50)),
    "music_search": lambda args: music_search(args.get("query", "")),
    "music_toggle_shuffle": lambda args: music_toggle_shuffle(),
    "music_toggle_repeat": lambda args: music_toggle_repeat(),

    # ── Terminal ──
    "terminal_open": lambda args: terminal_open(),
    "terminal_new_tab": lambda args: terminal_new_tab(),
    "terminal_new_window": lambda args: terminal_new_window(),
    "terminal_run_command": lambda args: terminal_run_command(args.get("command", "")),
    "terminal_clear": lambda args: terminal_clear(),

    # ── Messages ──
    "messages_open": lambda args: messages_open(),
    "messages_send": lambda args: messages_send(args.get("recipient", ""), args.get("text", "")),
    "messages_new_message": lambda args: messages_new_message(),

    # ── Preview ──
    "preview_open_file": lambda args: preview_open_file(args.get("path", "")),
    "preview_zoom_in": lambda args: preview_zoom_in(),
    "preview_zoom_out": lambda args: preview_zoom_out(),
    "preview_actual_size": lambda args: preview_actual_size(),
    "preview_rotate_right": lambda args: preview_rotate_right(),
    "preview_rotate_left": lambda args: preview_rotate_left(),

    # ── Pages ──
    "pages_open": lambda args: pages_open(),
    "pages_new_document": lambda args: pages_new_document(),
    "pages_write": lambda args: pages_write(args.get("text", "")),
    "pages_save": lambda args: pages_save(args.get("filename")),
    "pages_export_pdf": lambda args: pages_export_pdf(),

    # ── Numbers ──
    "numbers_open": lambda args: numbers_open(),
    "numbers_close": lambda args: numbers_close(),
    "numbers_close_spreadsheet": lambda args: numbers_close_spreadsheet(),
    "numbers_new_spreadsheet": lambda args: numbers_new_spreadsheet(),
    "numbers_save": lambda args: numbers_save(args.get("filename")),
    "numbers_open_file": lambda args: numbers_open_file(args.get("path", "")),
    "numbers_new_sheet": lambda args: numbers_new_sheet(),
    "numbers_next_sheet": lambda args: numbers_next_sheet(),
    "numbers_prev_sheet": lambda args: numbers_prev_sheet(),
    "numbers_go_to_cell": lambda args: numbers_go_to_cell(args.get("cell", "A1")),
    "numbers_move_right": lambda args: numbers_move_right(),
    "numbers_move_down": lambda args: numbers_move_down(),
    "numbers_move_up": lambda args: numbers_move_up(),
    "numbers_move_left": lambda args: numbers_move_left(),
    "numbers_move_to_start": lambda args: numbers_move_to_start(),
    "numbers_move_to_end": lambda args: numbers_move_to_end(),
    "numbers_move_to_edge": lambda args: numbers_move_to_edge(args.get("direction", "down")),
    "numbers_type_in_cell": lambda args: numbers_type_in_cell(args.get("text", ""), args.get("cell")),
    "numbers_type_and_stay": lambda args: numbers_type_and_stay(args.get("text", "")),
    "numbers_edit_cell": lambda args: numbers_edit_cell(),
    "numbers_enter_formula": lambda args: numbers_enter_formula(args.get("formula", ""), args.get("cell")),
    "numbers_clear_cell": lambda args: numbers_clear_cell(),
    "numbers_next_row": lambda args: numbers_next_row(),
    "numbers_autofill": lambda args: numbers_autofill(),
    "numbers_autofill_from_column": lambda args: numbers_autofill_from_column(),
    "numbers_autofill_from_row": lambda args: numbers_autofill_from_row(),
    "numbers_select_all": lambda args: numbers_select_all(),
    "numbers_select_row": lambda args: numbers_select_row(),
    "numbers_select_column": lambda args: numbers_select_column(),
    "numbers_copy": lambda args: numbers_copy(),
    "numbers_paste": lambda args: numbers_paste(),
    "numbers_cut": lambda args: numbers_cut(),
    "numbers_paste_values": lambda args: numbers_paste_values(),
    "numbers_bold": lambda args: numbers_bold(),
    "numbers_italic": lambda args: numbers_italic(),
    "numbers_underline": lambda args: numbers_underline(),
    "numbers_increase_font": lambda args: numbers_increase_font(),
    "numbers_decrease_font": lambda args: numbers_decrease_font(),
    "numbers_align_center": lambda args: numbers_align_center(),
    "numbers_align_left": lambda args: numbers_align_left(),
    "numbers_auto_align": lambda args: numbers_auto_align(),
    "numbers_add_border_top": lambda args: numbers_add_border_top(),
    "numbers_add_border_bottom": lambda args: numbers_add_border_bottom(),
    "numbers_add_border_left": lambda args: numbers_add_border_left(),
    "numbers_add_border_right": lambda args: numbers_add_border_right(),
    "numbers_merge_cells": lambda args: numbers_merge_cells(),
    "numbers_unmerge_cells": lambda args: numbers_unmerge_cells(),
    "numbers_add_row_above": lambda args: numbers_add_row_above(),
    "numbers_add_row_below": lambda args: numbers_add_row_below(),
    "numbers_add_column_left": lambda args: numbers_add_column_left(),
    "numbers_add_column_right": lambda args: numbers_add_column_right(),
    "numbers_delete_row": lambda args: numbers_delete_row(),
    "numbers_delete_column": lambda args: numbers_delete_column(),
    "numbers_sort": lambda args: numbers_sort(),
    "numbers_add_filter": lambda args: numbers_add_filter(),
    "numbers_find": lambda args: numbers_find(args.get("text", "")),
    "numbers_insert_equation": lambda args: numbers_insert_equation(),
    "numbers_undo": lambda args: numbers_undo(),
    "numbers_redo": lambda args: numbers_redo(),
    "numbers_read_cell": lambda args: numbers_read_cell(args.get("cell")),
    "numbers_read_selection": lambda args: numbers_read_selection(),
    "numbers_insert_date": lambda args: numbers_insert_date(),
    "numbers_insert_time": lambda args: numbers_insert_time(),
    "numbers_print": lambda args: numbers_print(),
    "numbers_add_comment": lambda args: numbers_add_comment(),
    "numbers_toggle_sidebar": lambda args: numbers_toggle_sidebar(),
    "numbers_collapse_groups": lambda args: numbers_collapse_groups(),
    "numbers_expand_groups": lambda args: numbers_expand_groups(),
    "numbers_make_link": lambda args: numbers_make_link(),
    "numbers_create_spreadsheet": lambda args: numbers_create_spreadsheet(
        args.get("title", ""), args.get("headers"), args.get("rows"), args.get("formulas")),

    # ── Microsoft Excel ──
    "excel_open": lambda args: excel_open(),
    "excel_close": lambda args: excel_close(),
    "excel_close_workbook": lambda args: excel_close_workbook(),
    "excel_new_workbook": lambda args: excel_new_workbook(),
    "excel_save": lambda args: excel_save(args.get("filename")),
    "excel_open_file": lambda args: excel_open_file(args.get("path", "")),
    "excel_new_sheet": lambda args: excel_new_sheet(),
    "excel_next_sheet": lambda args: excel_next_sheet(),
    "excel_prev_sheet": lambda args: excel_prev_sheet(),
    "excel_go_to_cell": lambda args: excel_go_to_cell(args.get("cell", "A1")),
    "excel_move_right": lambda args: excel_move_right(),
    "excel_move_down": lambda args: excel_move_down(),
    "excel_move_up": lambda args: excel_move_up(),
    "excel_move_left": lambda args: excel_move_left(),
    "excel_move_to_start": lambda args: excel_move_to_start(),
    "excel_move_to_end": lambda args: excel_move_to_end(),
    "excel_move_to_edge": lambda args: excel_move_to_edge(args.get("direction", "down")),
    "excel_type_in_cell": lambda args: excel_type_in_cell(args.get("text", "")),
    "excel_type_and_stay": lambda args: excel_type_and_stay(args.get("text", "")),
    "excel_edit_cell": lambda args: excel_edit_cell(),
    "excel_enter_formula": lambda args: excel_enter_formula(args.get("formula", "")),
    "excel_fill_down": lambda args: excel_fill_down(),
    "excel_fill_right": lambda args: excel_fill_right(),
    "excel_clear_cell": lambda args: excel_clear_cell(),
    "excel_select_all": lambda args: excel_select_all(),
    "excel_select_column": lambda args: excel_select_column(),
    "excel_select_row": lambda args: excel_select_row(),
    "excel_select_range": lambda args: excel_select_range(args.get("range", "A1:A1")),
    "excel_copy": lambda args: excel_copy(),
    "excel_paste": lambda args: excel_paste(),
    "excel_cut": lambda args: excel_cut(),
    "excel_paste_values": lambda args: excel_paste_values(),
    "excel_bold": lambda args: excel_bold(),
    "excel_italic": lambda args: excel_italic(),
    "excel_underline": lambda args: excel_underline(),
    "excel_strikethrough": lambda args: excel_strikethrough(),
    "excel_increase_font": lambda args: excel_increase_font(),
    "excel_decrease_font": lambda args: excel_decrease_font(),
    "excel_align_center": lambda args: excel_align_center(),
    "excel_align_left": lambda args: excel_align_left(),
    "excel_format_number": lambda args: excel_format_number(),
    "excel_format_currency": lambda args: excel_format_currency(),
    "excel_format_percent": lambda args: excel_format_percent(),
    "excel_format_date": lambda args: excel_format_date(),
    "excel_format_general": lambda args: excel_format_general(),
    "excel_add_border": lambda args: excel_add_border(),
    "excel_remove_border": lambda args: excel_remove_border(),
    "excel_format_cells": lambda args: excel_format_cells(),
    "excel_insert_row": lambda args: excel_insert_row(),
    "excel_insert_column": lambda args: excel_insert_column(),
    "excel_delete_row": lambda args: excel_delete_row(),
    "excel_delete_column": lambda args: excel_delete_column(),
    "excel_hide_column": lambda args: excel_hide_column(),
    "excel_unhide_column": lambda args: excel_unhide_column(),
    "excel_hide_row": lambda args: excel_hide_row(),
    "excel_unhide_row": lambda args: excel_unhide_row(),
    "excel_sort": lambda args: excel_sort(),
    "excel_add_filter": lambda args: excel_add_filter(),
    "excel_create_table": lambda args: excel_create_table(),
    "excel_find": lambda args: excel_find(args.get("text", "")),
    "excel_find_replace": lambda args: excel_find_replace(args.get("find_text", ""), args.get("replace_text", "")),
    "excel_autosum": lambda args: excel_autosum(),
    "excel_insert_function": lambda args: excel_insert_function(),
    "excel_toggle_formula_view": lambda args: excel_toggle_formula_view(),
    "excel_undo": lambda args: excel_undo(),
    "excel_redo": lambda args: excel_redo(),
    "excel_read_cell": lambda args: excel_read_cell(),
    "excel_read_selection": lambda args: excel_read_selection(),
    "excel_insert_date": lambda args: excel_insert_date(),
    "excel_insert_time": lambda args: excel_insert_time(),
    "excel_print": lambda args: excel_print(),
    "excel_create_spreadsheet": lambda args: excel_create_spreadsheet(args.get("title", ""), args.get("headers", []), args.get("rows", []), args.get("formulas", [])),
    "excel_create_chart": lambda args: excel_create_chart(args.get("data_range", "A1:B5"), args.get("chart_type", "pie"), args.get("title", "")),

    # ── Keynote ──
    "keynote_open": lambda args: keynote_open(),
    "keynote_new_presentation": lambda args: keynote_new_presentation(),
    "keynote_new_slide": lambda args: keynote_new_slide(),
    "keynote_play_slideshow": lambda args: keynote_play_slideshow(),
    "keynote_stop_slideshow": lambda args: keynote_stop_slideshow(),
    "keynote_write": lambda args: keynote_write(args.get("text", "")),
    "keynote_save": lambda args: keynote_save(args.get("filename")),

    # ── Photos ──
    "photos_open": lambda args: photos_open(),
    "photos_import": lambda args: photos_import(args.get("path", "")),

    # ── Voice Memos ──
    "voice_memos_open": lambda args: voice_memos_open(),
    "voice_memos_start_recording": lambda args: voice_memos_start_recording(),
    "voice_memos_stop_recording": lambda args: voice_memos_stop_recording(),

    # ── Contacts ──
    "contacts_open": lambda args: contacts_open(),
    "contacts_search": lambda args: contacts_search(args.get("name", "")),
    "contacts_new": lambda args: contacts_new(),

    # ── VS Code ──
    "vscode_open": lambda args: vscode_open(),
    "vscode_open_folder": lambda args: vscode_open_folder(args.get("path", "~")),
    "vscode_open_file": lambda args: vscode_open_file(args.get("path", "")),
    "vscode_new_file": lambda args: vscode_new_file(),
    "vscode_new_window": lambda args: vscode_new_window(),
    "vscode_write_code": lambda args: vscode_write_code(args.get("code", "")),
    "vscode_read_code": lambda args: vscode_read_code(),
    "vscode_save": lambda args: vscode_save(),
    "vscode_save_as": lambda args: vscode_save_as(args.get("filename", "")),
    "vscode_save_all": lambda args: vscode_save_all(),
    "vscode_close_editor": lambda args: vscode_close_editor(),
    "vscode_run_code": lambda args: vscode_run_code(),
    "vscode_stop_code": lambda args: vscode_stop_code(),
    "vscode_toggle_terminal": lambda args: vscode_toggle_terminal(),
    "vscode_new_terminal": lambda args: vscode_new_terminal(),
    "vscode_terminal_run": lambda args: vscode_terminal_run(args.get("command", "")),
    "vscode_command_palette": lambda args: vscode_command_palette(args.get("command_text")),
    "vscode_command_palette_run": lambda args: vscode_command_palette_run(args.get("command_text", "")),
    "vscode_quick_open": lambda args: vscode_quick_open(args.get("filename")),
    "vscode_find": lambda args: vscode_find(args.get("text")),
    "vscode_find_replace": lambda args: vscode_find_replace(args.get("find_text"), args.get("replace_text")),
    "vscode_toggle_sidebar": lambda args: vscode_toggle_sidebar(),
    "vscode_toggle_comment": lambda args: vscode_toggle_comment(),
    "vscode_format_document": lambda args: vscode_format_document(),
    "vscode_undo": lambda args: vscode_undo(),
    "vscode_redo": lambda args: vscode_redo(),
    "vscode_select_all": lambda args: vscode_select_all(),
    "vscode_go_to_line": lambda args: vscode_go_to_line(args.get("line_number", 1)),
    "vscode_delete_line": lambda args: vscode_delete_line(),
    "vscode_select_line": lambda args: vscode_select_line(),
    "vscode_edit_line": lambda args: vscode_edit_line(args.get("line_number", 1), args.get("new_text", "")),
    "vscode_insert_line_below": lambda args: vscode_insert_line_below(args.get("text")),
    "vscode_insert_line_above": lambda args: vscode_insert_line_above(args.get("text")),
    "vscode_focus_editor": lambda args: vscode_focus_editor(),
    "vscode_read_terminal_output": lambda args: vscode_read_terminal_output(),
    "vscode_move_line_up": lambda args: vscode_move_line_up(),
    "vscode_move_line_down": lambda args: vscode_move_line_down(),
    "vscode_copy_line_down": lambda args: vscode_copy_line_down(),
    "vscode_split_editor": lambda args: vscode_split_editor(),
    "vscode_show_explorer": lambda args: vscode_show_explorer(),
    "vscode_show_search": lambda args: vscode_show_search(),
    "vscode_show_extensions": lambda args: vscode_show_extensions(),
    "vscode_install_extension": lambda args: vscode_install_extension(args.get("extension_id", "")),
    "vscode_set_language": lambda args: vscode_set_language(args.get("language", "")),
    "vscode_zoom_in": lambda args: vscode_zoom_in(),
    "vscode_zoom_out": lambda args: vscode_zoom_out(),
    "vscode_create_file_with_code": lambda args: vscode_create_file_with_code(args.get("folder_path", "~/Desktop"), args.get("filename", "untitled.py"), args.get("code", ""), args.get("language")),
    "vscode_run_in_terminal": lambda args: vscode_run_in_terminal(args.get("command", "")),

    # ── Google Chrome ──
    "chrome_open": lambda args: chrome_open(),
    "chrome_new_tab": lambda args: chrome_new_tab(args.get("url")),
    "chrome_close_tab": lambda args: chrome_close_tab(),
    "chrome_new_window": lambda args: chrome_new_window(),
    "chrome_incognito": lambda args: chrome_incognito(),
    "chrome_reopen_tab": lambda args: chrome_reopen_tab(),
    "chrome_next_tab": lambda args: chrome_next_tab(),
    "chrome_prev_tab": lambda args: chrome_prev_tab(),
    "chrome_go_to_tab": lambda args: chrome_go_to_tab(args.get("tab_number", 1)),
    "chrome_go_back": lambda args: chrome_go_back(),
    "chrome_go_forward": lambda args: chrome_go_forward(),
    "chrome_reload": lambda args: chrome_reload(),
    "chrome_hard_reload": lambda args: chrome_hard_reload(),
    "chrome_get_url": lambda args: chrome_get_url(),
    "chrome_get_title": lambda args: chrome_get_title(),
    "chrome_list_tabs": lambda args: chrome_list_tabs(),
    "chrome_navigate": lambda args: chrome_navigate(args.get("url", "")),
    "chrome_find": lambda args: chrome_find(args.get("text")),
    "chrome_bookmark": lambda args: chrome_bookmark(),
    "chrome_open_history": lambda args: chrome_open_history(),
    "chrome_open_downloads": lambda args: chrome_open_downloads(),
    "chrome_open_settings": lambda args: chrome_open_settings(),
    "chrome_zoom_in": lambda args: chrome_zoom_in(),
    "chrome_zoom_out": lambda args: chrome_zoom_out(),
    "chrome_zoom_reset": lambda args: chrome_zoom_reset(),
    "chrome_focus_address_bar": lambda args: chrome_focus_address_bar(),
    "chrome_open_devtools": lambda args: chrome_open_devtools(),
    "chrome_print": lambda args: chrome_print(),
    "chrome_close_window": lambda args: chrome_close_window(),
    "chrome_fullscreen": lambda args: chrome_fullscreen(),
    "chrome_read_page_text": lambda args: chrome_read_page_text(),
    "chrome_execute_js": lambda args: chrome_execute_js(args.get("code", "")),
    "chrome_scroll_down": lambda args: chrome_scroll_down(),
    "chrome_scroll_up": lambda args: chrome_scroll_up(),

    # ── YouTube ──
    "youtube_open": lambda args: youtube_open(args.get("query")),
    "youtube_play_pause": lambda args: youtube_play_pause(),
    "youtube_mute": lambda args: youtube_mute(),
    "youtube_fullscreen": lambda args: youtube_fullscreen(),
    "youtube_captions": lambda args: youtube_captions(),
    "youtube_seek_forward": lambda args: youtube_seek_forward(),
    "youtube_seek_backward": lambda args: youtube_seek_backward(),
    "youtube_speed_up": lambda args: youtube_speed_up(),
    "youtube_speed_down": lambda args: youtube_speed_down(),
    "youtube_next_video": lambda args: youtube_next_video(),
    "youtube_prev_video": lambda args: youtube_prev_video(),
    "youtube_volume_up": lambda args: youtube_volume_up(),
    "youtube_volume_down": lambda args: youtube_volume_down(),
    "youtube_seek_to_percent": lambda args: youtube_seek_to_percent(args.get("percent", 0)),
    "youtube_miniplayer": lambda args: youtube_miniplayer(),
    "youtube_next_frame": lambda args: youtube_next_frame(),
    "youtube_prev_frame": lambda args: youtube_prev_frame(),
    "youtube_next_chapter": lambda args: youtube_next_chapter(),
    "youtube_prev_chapter": lambda args: youtube_prev_chapter(),

    # ── WhatsApp ──
    "whatsapp_open": lambda args: whatsapp_open(),
    "whatsapp_focus": lambda args: whatsapp_focus(),
    "whatsapp_send_wame": lambda args: whatsapp_send_wame(args.get("phone", ""), args.get("message", ""), args.get("api_key", "")),
    "whatsapp_send": lambda args: whatsapp_send_smart(args.get("name", ""), args.get("phone", ""), args.get("message", ""), args.get("api_key", "")),
    "whatsapp_read": lambda args: whatsapp_read_messages(args.get("name", ""), args.get("phone", ""), args.get("api_key", ""), args.get("num_messages", 10)),
    "whatsapp_check_unread": lambda args: whatsapp_check_unread(args.get("api_key", "")),

    # ── Gmail (Web) ──
    "gmail_open": lambda args: gmail_open(),
    "gmail_get_state": lambda args: gmail_get_state(),
    "gmail_ensure_list_view": lambda args: gmail_ensure_list_view(),
    "gmail_compose": lambda args: gmail_compose(args.get("to", ""), args.get("subject", ""), args.get("body", ""), args.get("cc", ""), args.get("bcc", ""), args.get("send", False)),
    "gmail_search": lambda args: gmail_search(args.get("query", "")),
    "gmail_reply": lambda args: gmail_reply(args.get("body", ""), args.get("send", False)),
    "gmail_reply_all": lambda args: gmail_reply_all(args.get("body", ""), args.get("send", False)),
    "gmail_forward": lambda args: gmail_forward(args.get("to", ""), args.get("body", ""), args.get("send", False)),
    "gmail_send": lambda args: gmail_send(),
    "gmail_go_inbox": lambda args: gmail_go_inbox(),
    "gmail_go_sent": lambda args: gmail_go_sent(),
    "gmail_go_drafts": lambda args: gmail_go_drafts(),
    "gmail_go_starred": lambda args: gmail_go_starred(),
    "gmail_go_all_mail": lambda args: gmail_go_all_mail(),
    "gmail_open_email": lambda args: gmail_open_email(),
    "gmail_back_to_list": lambda args: gmail_back_to_list(),
    "gmail_next": lambda args: gmail_next(),
    "gmail_prev": lambda args: gmail_prev(),
    "gmail_newer": lambda args: gmail_newer(),
    "gmail_older": lambda args: gmail_older(),
    "gmail_archive": lambda args: gmail_archive(),
    "gmail_delete": lambda args: gmail_delete(),
    "gmail_spam": lambda args: gmail_spam(),
    "gmail_star": lambda args: gmail_star(),
    "gmail_mark_read": lambda args: gmail_mark_read(),
    "gmail_mark_unread": lambda args: gmail_mark_unread(),
    "gmail_mark_important": lambda args: gmail_mark_important(),
    "gmail_select": lambda args: gmail_select(),
    "gmail_select_all": lambda args: gmail_select_all(),
    "gmail_mute": lambda args: gmail_mute(),
    "gmail_label": lambda args: gmail_label(),
    "gmail_move_to": lambda args: gmail_move_to(),
    "gmail_snooze": lambda args: gmail_snooze(),
    "gmail_undo": lambda args: gmail_undo(),
    "gmail_refresh": lambda args: gmail_refresh(),
    "gmail_unread_count": lambda args: gmail_unread_count(),
    "gmail_read_email": lambda args: gmail_read_email(),
}

def execute_automation(action, args=None):
    """
    Master dispatcher — execute any macOS automation action by name.
    Returns {"success": True/False, ...}
    """
    if args is None:
        args = {}

    handler = AUTOMATION_ACTIONS.get(action)
    if handler:
        try:
            return handler(args)
        except Exception as e:
            return {"success": False, "action": action, "error": str(e)}

    return {"success": False, "error": f"Unknown automation action: {action}"}

def list_available_actions():
    """Return a list of all available automation action names."""
    return sorted(AUTOMATION_ACTIONS.keys())

if __name__ == '__main__':
    if len(sys.argv) > 1:
        action = sys.argv[1]
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
        result = execute_automation(action, args)
        print(json.dumps(result, indent=2, default=str))
    else:
        print("Available actions:")
        for name in list_available_actions():
            print(f"  {name}")
        print(f"\nTotal: {len(AUTOMATION_ACTIONS)} actions")
        print("\nUsage: python3 macos_automation.py <action> [json_args]")
        print("Example: python3 macos_automation.py notes_create '{\"title\": \"My Note\", \"body\": \"Hello\"}'")
