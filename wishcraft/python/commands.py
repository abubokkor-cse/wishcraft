#!/usr/bin/env python3
"""
WishCraft Universal Command System
Works on Windows, macOS, and Linux via stdin JSON protocol.
"""

import platform
import subprocess
import os
import sys
import json
import shutil
import time
import hashlib
import re
import webbrowser
import urllib.parse
from collections import defaultdict
from datetime import datetime
from pathlib import Path

SYSTEM = platform.system()  # 'Windows', 'Darwin', 'Linux'

# Common app name mappings per OS
APP_ALIASES = {
    'chrome': {
        'Darwin': 'Google Chrome',
        'Windows': 'chrome',
        'Linux': 'google-chrome'
    },
    'firefox': {
        'Darwin': 'Firefox',
        'Windows': 'firefox',
        'Linux': 'firefox'
    },
    'safari': {
        'Darwin': 'Safari',
        'Windows': None,
        'Linux': None
    },
    'vscode': {
        'Darwin': 'Visual Studio Code',
        'Windows': 'Code',
        'Linux': 'code'
    },
    'terminal': {
        'Darwin': 'Terminal',
        'Windows': 'cmd',
        'Linux': 'gnome-terminal'
    },
    'finder': {
        'Darwin': 'Finder',
        'Windows': 'explorer',
        'Linux': 'nautilus'
    },
    'calculator': {
        'Darwin': 'Calculator',
        'Windows': 'calc',
        'Linux': 'gnome-calculator'
    },
    'notepad': {
        'Darwin': 'TextEdit',
        'Windows': 'notepad',
        'Linux': 'gedit'
    },
    'music': {
        'Darwin': 'Music',
        'Windows': 'Groove Music',
        'Linux': 'rhythmbox'
    },
    'spotify': {
        'Darwin': 'Spotify',
        'Windows': 'Spotify',
        'Linux': 'spotify'
    },
    'slack': {
        'Darwin': 'Slack',
        'Windows': 'Slack',
        'Linux': 'slack'
    },
    'telegram': {
        'Darwin': 'Telegram',
        'Windows': 'Telegram',
        'Linux': 'telegram-desktop'
    },
    'whatsapp': {
        'Darwin': 'WhatsApp',
        'Windows': 'WhatsApp',
        'Linux': 'whatsapp-for-linux'
    },
    'discord': {
        'Darwin': 'Discord',
        'Windows': 'Discord',
        'Linux': 'discord'
    },
    'notes': {
        'Darwin': 'Notes',
        'Windows': 'notepad',
        'Linux': 'gedit'
    },
    'mail': {
        'Darwin': 'Mail',
        'Windows': 'outlook',
        'Linux': 'thunderbird'
    },
    'settings': {
        'Darwin': 'System Preferences',
        'Windows': 'ms-settings:',
        'Linux': 'gnome-control-center'
    },
    'photos': {
        'Darwin': 'Photos',
        'Windows': 'ms-photos:',
        'Linux': 'shotwell'
    }
}

def resolve_app_name(app_name):
    """Resolve common app name to OS-specific name."""
    key = app_name.lower().strip()
    if key in APP_ALIASES:
        resolved = APP_ALIASES[key].get(SYSTEM)
        if resolved:
            return resolved
    return app_name

def open_app(app_name):
    """Open an application."""
    resolved = resolve_app_name(app_name)
    try:
        if SYSTEM == 'Darwin':
            subprocess.Popen(['open', '-a', resolved], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif SYSTEM == 'Windows':
            if ':' in resolved:  # URI like ms-settings:
                os.system(f'start {resolved}')
            else:
                subprocess.Popen(['start', '', resolved], shell=True)
        elif SYSTEM == 'Linux':
            subprocess.Popen([resolved], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"success": True, "action": "open_app", "message": f"Opened {resolved}"}
    except Exception as e:
        return {"success": False, "action": "open_app", "error": str(e)}

def close_app(app_name):
    """Close/kill an application."""
    resolved = resolve_app_name(app_name)
    try:
        if SYSTEM == 'Darwin':
            # Try graceful quit first
            try:
                subprocess.run(['osascript', '-e', f'tell application "{resolved}" to quit'], 
                             timeout=3, capture_output=True)
            except subprocess.TimeoutExpired:
                subprocess.run(['pkill', '-f', resolved], capture_output=True, timeout=5)
        elif SYSTEM == 'Windows':
            subprocess.run(['taskkill', '/IM', f'{resolved}.exe', '/F'], 
                         capture_output=True, timeout=5)
        elif SYSTEM == 'Linux':
            subprocess.run(['pkill', '-f', resolved], capture_output=True, timeout=5)
        return {"success": True, "action": "close_app", "message": f"Closed {resolved}"}
    except Exception as e:
        return {"success": False, "action": "close_app", "error": str(e)}

def switch_app(app_name):
    """Bring an application to the foreground."""
    resolved = resolve_app_name(app_name)
    try:
        if SYSTEM == 'Darwin':
            subprocess.run(['osascript', '-e', f'tell application "{resolved}" to activate'], timeout=3)
        elif SYSTEM == 'Windows':
            import pyautogui
            pyautogui.hotkey('alt', 'tab')
        elif SYSTEM == 'Linux':
            subprocess.run(['xdotool', 'search', '--name', resolved, 'windowactivate'], timeout=3)
        return {"success": True, "action": "switch_app", "message": f"Switched to {resolved}"}
    except Exception as e:
        return {"success": False, "action": "switch_app", "error": str(e)}

def list_running_apps():
    """List all running GUI applications."""
    try:
        if SYSTEM == 'Darwin':
            result = subprocess.run(
                ['osascript', '-e', 'tell application "System Events" to get name of every process whose background only is false'],
                capture_output=True, text=True, timeout=5
            )
            apps = [a.strip() for a in result.stdout.strip().split(',')]
        elif SYSTEM == 'Windows':
            result = subprocess.run(['tasklist', '/FI', 'STATUS eq RUNNING', '/FO', 'CSV'], 
                                  capture_output=True, text=True, timeout=5)
            apps = [line.split(',')[0].strip('"') for line in result.stdout.strip().split('\n')[1:]]
        elif SYSTEM == 'Linux':
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True, timeout=5)
            apps = [' '.join(line.split()[3:]) for line in result.stdout.strip().split('\n') if line]
        return {"success": True, "action": "list_running_apps", "apps": apps, "message": f"Found {len(apps)} apps"}
    except Exception as e:
        return {"success": False, "action": "list_running_apps", "error": str(e)}

def open_url(url):
    """Open a URL in the default browser."""
    import webbrowser
    try:
        webbrowser.open(url)
        return {"success": True, "action": "open_url", "message": f"Opened {url}"}
    except Exception as e:
        return {"success": False, "action": "open_url", "error": str(e)}

def search_web(query):
    """Search Google in the default browser."""
    import webbrowser
    import urllib.parse
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    try:
        webbrowser.open(url)
        return {"success": True, "action": "search_web", "message": f"Searching: {query}"}
    except Exception as e:
        return {"success": False, "action": "search_web", "error": str(e)}

def volume_control(action='up', amount=10):
    """Control system volume: up, down, mute."""
    try:
        if SYSTEM == 'Darwin':
            if action == 'mute':
                subprocess.run(['osascript', '-e', 'set volume output muted true'])
            elif action == 'unmute':
                subprocess.run(['osascript', '-e', 'set volume output muted false'])
            elif action == 'up':
                subprocess.run(['osascript', '-e', f'set volume output volume ((output volume of (get volume settings)) + {amount})'])
            elif action == 'down':
                subprocess.run(['osascript', '-e', f'set volume output volume ((output volume of (get volume settings)) - {amount})'])
            elif action == 'set':
                subprocess.run(['osascript', '-e', f'set volume output volume {amount}'])
        elif SYSTEM == 'Windows':
            import pyautogui
            if action == 'up':
                for _ in range(amount // 2): pyautogui.press('volumeup')
            elif action == 'down':
                for _ in range(amount // 2): pyautogui.press('volumedown')
            elif action == 'mute':
                pyautogui.press('volumemute')
        elif SYSTEM == 'Linux':
            if action == 'mute':
                subprocess.run(['amixer', 'set', 'Master', 'toggle'])
            elif action == 'up':
                subprocess.run(['amixer', 'set', 'Master', f'{amount}%+'])
            elif action == 'down':
                subprocess.run(['amixer', 'set', 'Master', f'{amount}%-'])
        return {"success": True, "action": f"volume_{action}", "message": f"Volume {action}"}
    except Exception as e:
        return {"success": False, "action": f"volume_{action}", "error": str(e)}

def brightness_control(action='up', amount=10):
    """Control screen brightness."""
    try:
        if SYSTEM == 'Darwin':
            if action == 'up':
                subprocess.run(['osascript', '-e',
                    f'tell application "System Events" to repeat {amount // 5} times\nkey code 144\nend repeat'])
            elif action == 'down':
                subprocess.run(['osascript', '-e',
                    f'tell application "System Events" to repeat {amount // 5} times\nkey code 145\nend repeat'])
        elif SYSTEM == 'Windows':
            try:
                subprocess.run(['powershell', '-Command',
                    f'(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{amount})'],
                    capture_output=True, timeout=5)
            except Exception:
                import pyautogui
                key = 'brightnessup' if action == 'up' else 'brightnessdown'
                for _ in range(amount // 5):
                    pyautogui.press(key)
        elif SYSTEM == 'Linux':
            subprocess.run(['xbacklight', '-inc' if action == 'up' else '-dec', str(amount)])
        return {"success": True, "action": f"brightness_{action}", "message": f"Brightness {action}"}
    except Exception as e:
        return {"success": False, "action": f"brightness_{action}", "error": str(e)}

def lock_screen():
    """Lock the computer screen."""
    try:
        if SYSTEM == 'Darwin':
            subprocess.run(['pmset', 'displaysleepnow'])
        elif SYSTEM == 'Windows':
            subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'])
        elif SYSTEM == 'Linux':
            subprocess.run(['xdg-screensaver', 'lock'])
        return {"success": True, "action": "lock_screen", "message": "Screen locked"}
    except Exception as e:
        return {"success": False, "action": "lock_screen", "error": str(e)}

def minimize_all():
    """Minimize all windows / show desktop."""
    try:
        import pyautogui
        if SYSTEM == 'Darwin':
            pyautogui.hotkey('command', 'option', 'h', 'm')
            subprocess.run(['osascript', '-e', 
                'tell application "Finder" to set visible of every process to false'])
        elif SYSTEM == 'Windows':
            pyautogui.hotkey('win', 'd')
        elif SYSTEM == 'Linux':
            pyautogui.hotkey('super', 'd')
        return {"success": True, "action": "minimize_all", "message": "Minimized all windows"}
    except Exception as e:
        return {"success": False, "action": "minimize_all", "error": str(e)}

def sleep_computer():
    """Put the computer to sleep."""
    try:
        if SYSTEM == 'Darwin':
            subprocess.run(['pmset', 'sleepnow'])
        elif SYSTEM == 'Windows':
            subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0,1,0'])
        elif SYSTEM == 'Linux':
            subprocess.run(['systemctl', 'suspend'])
        return {"success": True, "action": "sleep", "message": "Computer sleeping"}
    except Exception as e:
        return {"success": False, "action": "sleep", "error": str(e)}

def empty_trash():
    """Empty the trash/recycle bin."""
    try:
        if SYSTEM == 'Darwin':
            subprocess.run(['osascript', '-e', 
                'tell application "Finder" to empty trash'])
        elif SYSTEM == 'Windows':
            subprocess.run(['PowerShell', '-Command', 'Clear-RecycleBin -Force'])
        elif SYSTEM == 'Linux':
            trash_path = os.path.expanduser('~/.local/share/Trash/files/')
            if os.path.exists(trash_path):
                shutil.rmtree(trash_path)
                os.makedirs(trash_path)
        return {"success": True, "action": "empty_trash", "message": "Trash emptied"}
    except Exception as e:
        return {"success": False, "action": "empty_trash", "error": str(e)}

def get_system_info():
    """Get system information."""
    info = {
        "os": SYSTEM,
        "os_version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "hostname": platform.node()
    }
    try:
        import psutil
        info["cpu_percent"] = psutil.cpu_percent(interval=0.5)
        info["memory_total_gb"] = round(psutil.virtual_memory().total / (1024**3), 1)
        info["memory_used_percent"] = psutil.virtual_memory().percent
        info["disk_used_percent"] = psutil.disk_usage('/').percent
        info["battery"] = psutil.sensors_battery().percent if psutil.sensors_battery() else "N/A"
    except ImportError:
        pass
    return {"success": True, "action": "system_info", "info": info, "message": f"{SYSTEM} {platform.version()}"}

def run_command(command):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout.strip() or result.stderr.strip()
        return {"success": result.returncode == 0, "action": "run_command", 
                "output": output[:2000], "message": f"Command executed"}
    except subprocess.TimeoutExpired:
        return {"success": False, "action": "run_command", "error": "Command timed out (30s)"}
    except Exception as e:
        return {"success": False, "action": "run_command", "error": str(e)}

def show_notification(title, message):
    """Show a system notification."""
    try:
        if SYSTEM == 'Darwin':
            subprocess.run(['osascript', '-e', 
                f'display notification "{message}" with title "{title}"'])
        elif SYSTEM == 'Windows':
            # Requires win10toast or similar
            subprocess.run(['PowerShell', '-Command', 
                f'[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null; '
                f'$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(0); '
                f'$template.GetElementsByTagName("text")[0].InnerText = "{title}: {message}"; '
                f'[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("WishCraft").Show($template)'])
        elif SYSTEM == 'Linux':
            subprocess.run(['notify-send', title, message])
        return {"success": True, "action": "notify", "message": f"Notification: {title}"}
    except Exception as e:
        return {"success": False, "action": "notify", "error": str(e)}

def file_search(query, directory=None):
    """Search for files by name."""
    search_dir = directory or os.path.expanduser('~')
    found = []
    try:
        for root, dirs, files in os.walk(search_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                if query.lower() in f.lower():
                    found.append(os.path.join(root, f))
                    if len(found) >= 20:
                        break
            if len(found) >= 20:
                break
        return {"success": True, "action": "file_search", "files": found,
                "message": f"Found {len(found)} files matching '{query}'"}
    except Exception as e:
        return {"success": False, "action": "file_search", "error": str(e)}


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'}

def _ensure_rembg():
    """Check if rembg is available, install if not."""
    try:
        from rembg import remove
        return True
    except ImportError:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'rembg'],
                         capture_output=True, timeout=120)
            from rembg import remove
            return True
        except:
            return False

def remove_background(path, output_path=None):
    """Remove background from a single image. Returns PNG with transparency."""
    path = os.path.expanduser(path)
    if not os.path.isfile(path):
        return {"success": False, "action": "remove_background", "error": f"File not found: {path}"}

    ext = os.path.splitext(path)[1].lower()
    if ext not in IMAGE_EXTENSIONS:
        return {"success": False, "action": "remove_background", "error": f"Not an image file: {ext}"}

    if not _ensure_rembg():
        return {"success": False, "action": "remove_background", "error": "Could not install rembg. Run: pip install rembg"}

    try:
        from rembg import remove
        from PIL import Image

        input_img = Image.open(path)
        output_img = remove(input_img)

        if not output_path:
            base, _ = os.path.splitext(path)
            output_path = base + '_no_bg.png'

        output_img.save(output_path)
        return {"success": True, "action": "remove_background",
                "output": output_path, "message": f"Background removed → {os.path.basename(output_path)}"}
    except Exception as e:
        return {"success": False, "action": "remove_background", "error": str(e)}

def remove_background_batch(paths):
    """Remove background from multiple image files."""
    if not _ensure_rembg():
        return {"success": False, "action": "remove_background_batch", "error": "Could not install rembg. Run: pip install rembg"}

    try:
        from rembg import remove
        from PIL import Image

        results = []
        for p in paths:
            p = os.path.expanduser(p)
            if not os.path.isfile(p):
                results.append({"file": p, "success": False, "error": "Not found"})
                continue
            ext = os.path.splitext(p)[1].lower()
            if ext not in IMAGE_EXTENSIONS:
                results.append({"file": p, "success": False, "error": f"Not an image: {ext}"})
                continue
            try:
                input_img = Image.open(p)
                output_img = remove(input_img)
                base, _ = os.path.splitext(p)
                out = base + '_no_bg.png'
                output_img.save(out)
                results.append({"file": p, "success": True, "output": out})
                print(json.dumps({"progress": True, "message": f"Done: {os.path.basename(p)}"}), flush=True)
            except Exception as e:
                results.append({"file": p, "success": False, "error": str(e)})

        done = sum(1 for r in results if r['success'])
        return {"success": True, "action": "remove_background_batch",
                "results": results, "message": f"Processed {done}/{len(results)} images"}
    except Exception as e:
        return {"success": False, "action": "remove_background_batch", "error": str(e)}

def remove_background_folder(folder, output_folder=None):
    """Remove background from all images in a folder."""
    folder = os.path.expanduser(folder)
    if not os.path.isdir(folder):
        return {"success": False, "action": "remove_background_folder", "error": f"Folder not found: {folder}"}

    if not _ensure_rembg():
        return {"success": False, "action": "remove_background_folder", "error": "Could not install rembg. Run: pip install rembg"}

    try:
        from rembg import remove
        from PIL import Image

        if not output_folder:
            output_folder = os.path.join(folder, 'no_bg')
        output_folder = os.path.expanduser(output_folder)
        os.makedirs(output_folder, exist_ok=True)

        images = [f for f in os.listdir(folder)
                  if os.path.isfile(os.path.join(folder, f)) and os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS]

        if not images:
            return {"success": False, "action": "remove_background_folder", "error": "No images found in folder"}

        results = []
        for fname in images:
            src = os.path.join(folder, fname)
            try:
                input_img = Image.open(src)
                output_img = remove(input_img)
                base, _ = os.path.splitext(fname)
                out = os.path.join(output_folder, base + '_no_bg.png')
                output_img.save(out)
                results.append({"file": fname, "success": True, "output": out})
                print(json.dumps({"progress": True, "message": f"Done: {fname} ({len(results)}/{len(images)})"}), flush=True)
            except Exception as e:
                results.append({"file": fname, "success": False, "error": str(e)})

        done = sum(1 for r in results if r['success'])
        return {"success": True, "action": "remove_background_folder",
                "output_folder": output_folder, "results": results,
                "message": f"Processed {done}/{len(images)} images → {output_folder}"}
    except Exception as e:
        return {"success": False, "action": "remove_background_folder", "error": str(e)}


# ────────────────────────────────────────
# File Organizer (pure Python)
# ────────────────────────────────────────

FILE_TYPE_CATEGORIES = {
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".pages", ".tex", ".md", ".csv", ".xls", ".xlsx", ".ppt", ".pptx", ".numbers", ".keynote"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".svg", ".webp", ".heic", ".heif", ".ico", ".raw", ".cr2", ".nef"],
    "Videos": [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".m4v", ".mpg", ".mpeg", ".3gp"],
    "Audio": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".wma", ".m4a", ".aiff", ".alac"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".dmg", ".iso"],
    "Code": [".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp", ".h", ".swift", ".go", ".rs", ".rb", ".php", ".sh", ".json", ".xml", ".yaml", ".yml", ".sql", ".r"],
    "Apps": [".app", ".exe", ".msi", ".pkg", ".deb", ".rpm"],
    "Fonts": [".ttf", ".otf", ".woff", ".woff2", ".eot"],
    "Design": [".psd", ".ai", ".sketch", ".fig", ".xd", ".indd"],
    "Data": [".db", ".sqlite", ".json", ".xml", ".csv", ".tsv", ".parquet"],
}

def _get_file_category(ext):
    ext = ext.lower()
    for category, extensions in FILE_TYPE_CATEGORIES.items():
        if ext in extensions:
            return category
    return "Other"

def _org_safe_path(path_str):
    return str(Path(os.path.expanduser(path_str)).resolve())

def _file_hash(filepath, chunk_size=8192):
    h = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError):
        return None

def organize_scan_directory(path="~", max_depth=2):
    """Analyze a directory — file count, types, sizes, age distribution."""
    path = _org_safe_path(path)
    if not os.path.isdir(path):
        return {"success": False, "error": f"Not a directory: {path}"}

    stats = {
        "path": path,
        "total_files": 0,
        "total_folders": 0,
        "total_size_bytes": 0,
        "categories": defaultdict(lambda: {"count": 0, "size_bytes": 0}),
        "largest_files": [],
        "oldest_files": [],
        "newest_files": [],
        "empty_folders": [],
        "hidden_files_count": 0,
    }

    all_files = []
    depth_base = path.rstrip(os.sep).count(os.sep)

    for root, dirs, files in os.walk(path):
        current_depth = root.rstrip(os.sep).count(os.sep) - depth_base
        if current_depth >= max_depth:
            dirs.clear()
            continue

        stats["total_folders"] += len(dirs)

        if not files and not dirs:
            stats["empty_folders"].append(root)

        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                fstat = os.stat(fpath, follow_symlinks=False)
                fsize = fstat.st_size
                fmtime = fstat.st_mtime
            except (OSError, PermissionError):
                continue

            stats["total_files"] += 1
            stats["total_size_bytes"] += fsize

            if fname.startswith('.'):
                stats["hidden_files_count"] += 1

            ext = os.path.splitext(fname)[1]
            cat = _get_file_category(ext)
            stats["categories"][cat]["count"] += 1
            stats["categories"][cat]["size_bytes"] += fsize

            all_files.append({"path": fpath, "name": fname, "size": fsize, "modified": fmtime})

    all_files.sort(key=lambda f: f["size"], reverse=True)
    stats["largest_files"] = [{"name": f["name"], "size_mb": round(f["size"] / 1048576, 2), "path": f["path"]} for f in all_files[:10]]

    all_files.sort(key=lambda f: f["modified"])
    stats["oldest_files"] = [{"name": f["name"], "modified": datetime.fromtimestamp(f["modified"]).strftime("%Y-%m-%d"), "path": f["path"]} for f in all_files[:10]]

    all_files.sort(key=lambda f: f["modified"], reverse=True)
    stats["newest_files"] = [{"name": f["name"], "modified": datetime.fromtimestamp(f["modified"]).strftime("%Y-%m-%d"), "path": f["path"]} for f in all_files[:10]]

    stats["categories"] = dict(stats["categories"])
    stats["total_size_mb"] = round(stats["total_size_bytes"] / 1048576, 2)
    stats["empty_folders"] = stats["empty_folders"][:20]
    stats["success"] = True
    return stats

def organize_find_duplicates(path="~", max_depth=2, min_size_kb=1):
    """Find duplicate files by SHA-256 hash."""
    path = _org_safe_path(path)
    if not os.path.isdir(path):
        return {"success": False, "error": f"Not a directory: {path}"}

    min_size = min_size_kb * 1024
    size_groups = defaultdict(list)
    depth_base = path.rstrip(os.sep).count(os.sep)

    for root, dirs, files in os.walk(path):
        current_depth = root.rstrip(os.sep).count(os.sep) - depth_base
        if current_depth >= max_depth:
            dirs.clear()
            continue
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                fsize = os.path.getsize(fpath)
                if fsize >= min_size:
                    size_groups[fsize].append(fpath)
            except (OSError, PermissionError):
                continue

    hash_groups = defaultdict(list)
    for fsize, fpaths in size_groups.items():
        if len(fpaths) < 2:
            continue
        for fpath in fpaths:
            fhash = _file_hash(fpath)
            if fhash:
                hash_groups[fhash].append(fpath)

    duplicates = []
    total_wasted = 0
    for fhash, fpaths in hash_groups.items():
        if len(fpaths) < 2:
            continue
        fsize = os.path.getsize(fpaths[0])
        wasted = fsize * (len(fpaths) - 1)
        total_wasted += wasted
        duplicates.append({
            "hash": fhash[:16],
            "count": len(fpaths),
            "size_each_mb": round(fsize / 1048576, 2),
            "wasted_mb": round(wasted / 1048576, 2),
            "files": fpaths
        })

    duplicates.sort(key=lambda d: d["wasted_mb"], reverse=True)

    return {
        "success": True,
        "path": path,
        "duplicate_groups": len(duplicates),
        "total_duplicate_files": sum(d["count"] - 1 for d in duplicates),
        "total_wasted_mb": round(total_wasted / 1048576, 2),
        "duplicates": duplicates[:50]
    }

def organize_by_type(path="~", dry_run=True):
    """Organize files into type-based subfolders (Documents, Images, Videos, etc.)."""
    path = _org_safe_path(path)
    if not os.path.isdir(path):
        return {"success": False, "error": f"Not a directory: {path}"}

    plan = []
    for fname in os.listdir(path):
        fpath = os.path.join(path, fname)
        if not os.path.isfile(fpath) or fname.startswith('.'):
            continue
        ext = os.path.splitext(fname)[1]
        if not ext:
            continue
        cat = _get_file_category(ext)
        dest_dir = os.path.join(path, cat)
        dest_path = os.path.join(dest_dir, fname)
        if fpath == dest_path:
            continue
        plan.append({"file": fname, "from": fpath, "to": dest_path, "category": cat})

    if dry_run:
        return {
            "success": True, "mode": "dry_run", "path": path,
            "moves_planned": len(plan), "plan": plan[:100],
            "categories_used": list(set(m["category"] for m in plan))
        }

    moved = 0
    errors = []
    for move in plan:
        try:
            os.makedirs(os.path.dirname(move["to"]), exist_ok=True)
            dest = move["to"]
            if os.path.exists(dest):
                base, ext_ = os.path.splitext(dest)
                counter = 1
                while os.path.exists(dest):
                    dest = f"{base}_{counter}{ext_}"
                    counter += 1
            shutil.move(move["from"], dest)
            moved += 1
        except (OSError, PermissionError) as e:
            errors.append({"file": move["file"], "error": str(e)})

    return {
        "success": True, "mode": "executed", "path": path,
        "files_moved": moved, "errors": errors[:20],
        "categories_created": list(set(m["category"] for m in plan))
    }

def organize_by_date(path="~", date_format="year_month", dry_run=True):
    """Organize files into date-based subfolders."""
    path = _org_safe_path(path)
    if not os.path.isdir(path):
        return {"success": False, "error": f"Not a directory: {path}"}

    plan = []
    for fname in os.listdir(path):
        fpath = os.path.join(path, fname)
        if not os.path.isfile(fpath) or fname.startswith('.'):
            continue
        try:
            mtime = os.path.getmtime(fpath)
        except (OSError, PermissionError):
            continue

        dt = datetime.fromtimestamp(mtime)
        if date_format == "year":
            subfolder = str(dt.year)
        elif date_format == "year_month_day":
            subfolder = os.path.join(str(dt.year), f"{dt.month:02d}", f"{dt.day:02d}")
        else:
            subfolder = os.path.join(str(dt.year), f"{dt.month:02d}")

        dest_dir = os.path.join(path, subfolder)
        dest_path = os.path.join(dest_dir, fname)
        if fpath == dest_path:
            continue
        plan.append({"file": fname, "from": fpath, "to": dest_path, "date_folder": subfolder})

    if dry_run:
        return {
            "success": True, "mode": "dry_run", "path": path,
            "moves_planned": len(plan), "plan": plan[:100],
            "date_folders": sorted(set(m["date_folder"] for m in plan))
        }

    moved = 0
    errors = []
    for move in plan:
        try:
            os.makedirs(os.path.dirname(move["to"]), exist_ok=True)
            dest = move["to"]
            if os.path.exists(dest):
                base, ext_ = os.path.splitext(dest)
                counter = 1
                while os.path.exists(dest):
                    dest = f"{base}_{counter}{ext_}"
                    counter += 1
            shutil.move(move["from"], dest)
            moved += 1
        except (OSError, PermissionError) as e:
            errors.append({"file": move["file"], "error": str(e)})

    return {
        "success": True, "mode": "executed", "path": path,
        "files_moved": moved, "errors": errors[:20],
        "date_folders_created": sorted(set(m["date_folder"] for m in plan))
    }

def organize_cleanup_old(path="~", older_than_days=180, dry_run=True):
    """Find files not modified in N days."""
    path = _org_safe_path(path)
    if not os.path.isdir(path):
        return {"success": False, "error": f"Not a directory: {path}"}

    cutoff = time.time() - (older_than_days * 86400)
    old_files = []

    for fname in os.listdir(path):
        fpath = os.path.join(path, fname)
        if not os.path.isfile(fpath) or fname.startswith('.'):
            continue
        try:
            mtime = os.path.getmtime(fpath)
            if mtime < cutoff:
                fsize = os.path.getsize(fpath)
                old_files.append({
                    "file": fname, "path": fpath,
                    "size_mb": round(fsize / 1048576, 2),
                    "last_modified": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d"),
                    "days_old": int((time.time() - mtime) / 86400)
                })
        except (OSError, PermissionError):
            continue

    old_files.sort(key=lambda f: f["days_old"], reverse=True)
    total_size = sum(f["size_mb"] for f in old_files)

    if dry_run:
        return {
            "success": True, "mode": "dry_run", "path": path,
            "older_than_days": older_than_days,
            "old_files_count": len(old_files),
            "total_size_mb": round(total_size, 2),
            "files": old_files[:100]
        }

    archive_dir = os.path.join(path, f"_archived_{datetime.now().strftime('%Y%m%d')}")
    os.makedirs(archive_dir, exist_ok=True)
    moved = 0
    errors = []
    for f in old_files:
        try:
            shutil.move(f["path"], os.path.join(archive_dir, f["file"]))
            moved += 1
        except (OSError, PermissionError) as e:
            errors.append({"file": f["file"], "error": str(e)})

    return {
        "success": True, "mode": "executed", "path": path,
        "files_archived": moved, "archive_folder": archive_dir,
        "total_size_mb": round(total_size, 2), "errors": errors[:20]
    }

def organize_remove_duplicates(path="~", max_depth=2, min_size_kb=1, dry_run=True):
    """Remove duplicate files, keeping the oldest (original) copy."""
    result = organize_find_duplicates(path, max_depth, min_size_kb)
    if not result["success"]:
        return result

    removals = []
    for group in result["duplicates"]:
        files_with_mtime = []
        for fpath in group["files"]:
            try:
                mtime = os.path.getmtime(fpath)
                files_with_mtime.append((fpath, mtime))
            except (OSError, PermissionError):
                continue
        files_with_mtime.sort(key=lambda x: x[1])
        if len(files_with_mtime) < 2:
            continue
        keep = files_with_mtime[0][0]
        for fpath, _ in files_with_mtime[1:]:
            removals.append({"path": fpath, "name": os.path.basename(fpath), "keep": keep})

    if dry_run:
        return {
            "success": True, "mode": "dry_run", "path": _org_safe_path(path),
            "duplicates_to_remove": len(removals),
            "space_freed_mb": result["total_wasted_mb"],
            "removals": removals[:100]
        }

    archive_dir = os.path.join(_org_safe_path(path), f"_duplicates_{datetime.now().strftime('%Y%m%d')}")
    os.makedirs(archive_dir, exist_ok=True)
    removed = 0
    errors = []
    for r in removals:
        try:
            shutil.move(r["path"], os.path.join(archive_dir, r["name"]))
            removed += 1
        except (OSError, PermissionError) as e:
            errors.append({"file": r["name"], "error": str(e)})

    return {
        "success": True, "mode": "executed",
        "files_removed": removed, "archive_folder": archive_dir,
        "space_freed_mb": result["total_wasted_mb"], "errors": errors[:20]
    }

def organize_suggest_plan(path="~"):
    """Analyze a directory and suggest an organization plan."""
    scan = organize_scan_directory(path, max_depth=1)
    if not scan["success"]:
        return scan

    suggestions = []
    categories = scan.get("categories", {})
    if len(categories) > 3:
        suggestions.append({
            "action": "organize_by_type",
            "reason": f"Top-level has {len(categories)} file categories mixed together",
            "impact": f"Would sort {scan['total_files']} files into {len(categories)} organized folders"
        })

    dups = organize_find_duplicates(path, max_depth=1, min_size_kb=100)
    if dups["success"] and dups["duplicate_groups"] > 0:
        suggestions.append({
            "action": "organize_remove_duplicates",
            "reason": f"Found {dups['duplicate_groups']} duplicate groups ({dups['total_duplicate_files']} extra files)",
            "impact": f"Could free {dups['total_wasted_mb']} MB"
        })

    old = organize_cleanup_old(path, older_than_days=180, dry_run=True)
    if old["success"] and old["old_files_count"] > 5:
        suggestions.append({
            "action": "organize_cleanup_old",
            "reason": f"Found {old['old_files_count']} files not modified in 6+ months",
            "impact": f"Could archive {old['total_size_mb']} MB"
        })

    if scan.get("empty_folders"):
        suggestions.append({
            "action": "manual_review",
            "reason": f"Found {len(scan['empty_folders'])} empty folders",
            "impact": "Consider removing empty directories"
        })

    return {
        "success": True, "path": scan["path"],
        "summary": {
            "total_files": scan["total_files"],
            "total_folders": scan["total_folders"],
            "total_size_mb": scan["total_size_mb"],
            "categories": {k: v["count"] for k, v in categories.items()}
        },
        "suggestions": suggestions, "suggestion_count": len(suggestions)
    }

def organize_flatten_folder(path="~", dry_run=True):
    """Flatten nested subfolders — move all files to the top-level directory."""
    path = _org_safe_path(path)
    if not os.path.isdir(path):
        return {"success": False, "error": f"Not a directory: {path}"}

    plan = []
    for root, dirs, files in os.walk(path):
        if root == path:
            continue
        for fname in files:
            fpath = os.path.join(root, fname)
            dest = os.path.join(path, fname)
            plan.append({"file": fname, "from": fpath, "to": dest})

    if dry_run:
        return {
            "success": True, "mode": "dry_run", "path": path,
            "files_to_move": len(plan), "plan": plan[:100]
        }

    moved = 0
    errors = []
    for move in plan:
        try:
            dest = move["to"]
            if os.path.exists(dest):
                base, ext_ = os.path.splitext(dest)
                counter = 1
                while os.path.exists(dest):
                    dest = f"{base}_{counter}{ext_}"
                    counter += 1
            shutil.move(move["from"], dest)
            moved += 1
        except (OSError, PermissionError) as e:
            errors.append({"file": move["file"], "error": str(e)})

    for root, dirs, files in os.walk(path, topdown=False):
        if root == path:
            continue
        try:
            if not os.listdir(root):
                os.rmdir(root)
        except OSError:
            pass

    return {"success": True, "mode": "executed", "files_moved": moved, "errors": errors[:20]}

def organize_rename_pattern(path="~", pattern="date_prefix", dry_run=True):
    """Rename files with a consistent pattern."""
    path = _org_safe_path(path)
    if not os.path.isdir(path):
        return {"success": False, "error": f"Not a directory: {path}"}

    plan = []
    for fname in os.listdir(path):
        fpath = os.path.join(path, fname)
        if not os.path.isfile(fpath) or fname.startswith('.'):
            continue

        new_name = fname
        if pattern == "date_prefix":
            try:
                mtime = os.path.getmtime(fpath)
                date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
                if not fname.startswith(date_str):
                    new_name = f"{date_str}_{fname}"
            except OSError:
                continue
        elif pattern == "lowercase":
            new_name = fname.lower()
        elif pattern == "no_spaces":
            new_name = fname.replace(" ", "_")
        elif pattern == "clean":
            base, ext_ = os.path.splitext(fname)
            cleaned = base.lower().replace(" ", "_")
            cleaned = ''.join(c for c in cleaned if c.isalnum() or c in ('_', '-', '.'))
            new_name = cleaned + ext_.lower()

        if new_name != fname:
            plan.append({"from": fname, "to": new_name, "path": fpath})

    if dry_run:
        return {
            "success": True, "mode": "dry_run", "path": path,
            "pattern": pattern, "renames_planned": len(plan), "plan": plan[:100]
        }

    renamed = 0
    errors = []
    for r in plan:
        try:
            new_path = os.path.join(path, r["to"])
            if os.path.exists(new_path):
                base, ext_ = os.path.splitext(new_path)
                counter = 1
                while os.path.exists(new_path):
                    new_path = f"{base}_{counter}{ext_}"
                    counter += 1
            os.rename(r["path"], new_path)
            renamed += 1
        except (OSError, PermissionError) as e:
            errors.append({"file": r["from"], "error": str(e)})

    return {"success": True, "mode": "executed", "files_renamed": renamed, "pattern": pattern, "errors": errors[:20]}

def organize_size_report(path="~", max_depth=3):
    """Generate a size report showing which folders use the most space."""
    path = _org_safe_path(path)
    if not os.path.isdir(path):
        return {"success": False, "error": f"Not a directory: {path}"}

    folder_sizes = {}
    depth_base = path.rstrip(os.sep).count(os.sep)

    for root, dirs, files in os.walk(path):
        current_depth = root.rstrip(os.sep).count(os.sep) - depth_base
        if current_depth >= max_depth:
            dirs.clear()
            continue

        folder_size = 0
        file_count = 0
        for fname in files:
            try:
                folder_size += os.path.getsize(os.path.join(root, fname))
                file_count += 1
            except (OSError, PermissionError):
                continue

        rel_path = os.path.relpath(root, path)
        if rel_path == '.':
            rel_path = os.sep
        folder_sizes[rel_path] = {"size_bytes": folder_size, "size_mb": round(folder_size / 1048576, 2), "file_count": file_count}

    sorted_folders = sorted(folder_sizes.items(), key=lambda x: x[1]["size_bytes"], reverse=True)

    return {
        "success": True, "path": path,
        "folders": [{"folder": k, **v} for k, v in sorted_folders[:50]],
        "total_folders_scanned": len(folder_sizes)
    }

# Cross-platform input helpers (pyautogui on Win/Linux, osascript on macOS)

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.05
except ImportError:
    pyautogui = None


def _mod():
    """Primary modifier key for the current OS."""
    return 'command' if SYSTEM == 'Darwin' else 'ctrl'


def _activate_app(name):
    """Bring an app window to the foreground."""
    if SYSTEM == 'Darwin':
        subprocess.run(['osascript', '-e', f'tell application "{name}" to activate'], capture_output=True, timeout=5)
    elif SYSTEM == 'Windows':
        subprocess.run(['powershell', '-c', f'(New-Object -Com WScript.Shell).AppActivate("{name}")'], capture_output=True, timeout=5)
    elif SYSTEM == 'Linux':
        subprocess.run(['xdotool', 'search', '--name', name, 'windowactivate'], capture_output=True, timeout=5)
    time.sleep(0.4)


def _is_running(name):
    """Check if a process is running by name."""
    try:
        if SYSTEM == 'Darwin':
            r = subprocess.run(['pgrep', '-ix', name], capture_output=True, timeout=5)
            return r.returncode == 0
        elif SYSTEM == 'Windows':
            r = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {name}.exe'], capture_output=True, text=True, timeout=5)
            return name.lower() in r.stdout.lower()
        else:
            r = subprocess.run(['pgrep', '-ix', name], capture_output=True, timeout=5)
            return r.returncode == 0
    except Exception:
        return False


def _open_app(name):
    """Launch an application if not already running."""
    if SYSTEM == 'Darwin':
        subprocess.Popen(['open', '-a', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif SYSTEM == 'Windows':
        subprocess.Popen(['start', '', name], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen([name.lower()], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)


def _copy_to_clipboard(text):
    """Put text on the system clipboard."""
    if SYSTEM == 'Darwin':
        p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        p.communicate(text.encode('utf-8'))
    elif SYSTEM == 'Windows':
        escaped = text.replace("'", "''")
        subprocess.run(['powershell', '-c', f"Set-Clipboard -Value '{escaped}'"], capture_output=True, timeout=5)
    else:
        p = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
        p.communicate(text.encode('utf-8'))


def _read_clipboard():
    """Read text from the system clipboard."""
    try:
        if SYSTEM == 'Darwin':
            r = subprocess.run(['pbpaste'], capture_output=True, text=True, timeout=5)
            return r.stdout
        elif SYSTEM == 'Windows':
            r = subprocess.run(['powershell', '-c', 'Get-Clipboard'], capture_output=True, text=True, timeout=5)
            return r.stdout.strip()
        else:
            r = subprocess.run(['xclip', '-selection', 'clipboard', '-o'], capture_output=True, text=True, timeout=5)
            return r.stdout
    except Exception:
        return ''


def _paste_from_clipboard():
    """Trigger Ctrl+V / Cmd+V to paste clipboard content."""
    if pyautogui:
        pyautogui.hotkey(_mod(), 'v')
        time.sleep(0.15)


def _key(k, pause=0.1):
    """Press a single key."""
    if pyautogui:
        pyautogui.press(k)
        time.sleep(pause)


def _hotkey(*keys, pause=0.15):
    """Press a key combo like ctrl+a or command+shift+c."""
    if pyautogui:
        pyautogui.hotkey(*keys)
        time.sleep(pause)


def _take_screenshot():
    """Capture the screen and return raw PNG bytes."""
    if pyautogui:
        img = pyautogui.screenshot()
        import io
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()
    return None


# Chrome browser helpers

def _chrome_focus():
    """Open Chrome if needed, then bring it to front."""
    chrome_name = APP_ALIASES['chrome'].get(SYSTEM, 'Google Chrome')
    if not _is_running(chrome_name.split()[0] if SYSTEM != 'Darwin' else 'Google Chrome'):
        _open_app(chrome_name)
    _activate_app(chrome_name)
    time.sleep(0.3)


def _chrome_navigate(url):
    """Navigate Chrome to a URL via the address bar."""
    _chrome_focus()
    _hotkey(_mod(), 'l')
    time.sleep(0.2)
    _copy_to_clipboard(url)
    _paste_from_clipboard()
    _key('return', pause=0.8)


def _chrome_url():
    """Read the current URL from Chrome's address bar."""
    _hotkey(_mod(), 'l')
    time.sleep(0.2)
    _hotkey(_mod(), 'c')
    time.sleep(0.2)
    _key('escape')
    return _read_clipboard()


def _chrome_title():
    """Get Chrome's window title (usually the page title)."""
    if SYSTEM == 'Darwin':
        r = subprocess.run(
            ['osascript', '-e', 'tell application "Google Chrome" to get title of active tab of front window'],
            capture_output=True, text=True, timeout=5
        )
        return r.stdout.strip()
    else:
        return _read_clipboard()


# Gmail automation (Chrome keyboard shortcuts)
# Requires: Gmail Settings > General > Keyboard shortcuts ON

def _delegate_mac(action, args=None):
    """On macOS, forward to the existing macos_automation module."""
    from macos_automation import execute_automation
    return execute_automation(action, args or {})


def gmail_open(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_open')
    _chrome_navigate('https://mail.google.com')
    time.sleep(2)
    return {"success": True, "action": "gmail_open", "message": "Gmail opened in Chrome"}


def gmail_get_state(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_get_state')
    title = _chrome_title()
    url = _chrome_url()
    state = "unknown"
    if 'inbox' in url.lower() or 'Inbox' in title:
        state = "list"
    elif '#compose' in url or 'compose' in url.lower():
        state = "compose"
    return {"success": True, "action": "gmail_get_state", "state": state, "title": title}


def gmail_ensure_list_view(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_ensure_list_view')
    _key('escape')
    time.sleep(0.3)
    _key('escape')
    time.sleep(0.3)
    _hotkey(_mod(), 'l')
    time.sleep(0.2)
    _copy_to_clipboard('https://mail.google.com/mail/u/0/#inbox')
    _paste_from_clipboard()
    _key('return', pause=1.5)
    return {"success": True, "action": "gmail_ensure_list_view", "message": "Returned to inbox list view"}


def gmail_unread_count(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_unread_count')
    title = _chrome_title()
    m = re.search(r'Inbox\s*\((\d+)\)', title)
    count = int(m.group(1)) if m else 0
    return {"success": True, "action": "gmail_unread_count", "unread_count": count}


def gmail_compose(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_compose', args)
    _chrome_focus()
    _key('c', pause=1.0)  # Gmail shortcut: compose
    to = args.get('to', '')
    if to:
        _copy_to_clipboard(to)
        _paste_from_clipboard()
    _key('tab', pause=0.2)  # skip CC
    _key('tab', pause=0.2)  # skip BCC
    subject = args.get('subject', '')
    if subject:
        _copy_to_clipboard(subject)
        _paste_from_clipboard()
    _key('tab', pause=0.3)  # move to body
    body = args.get('body', '')
    if body:
        _copy_to_clipboard(body)
        _paste_from_clipboard()
    if args.get('send'):
        time.sleep(0.3)
        _hotkey(_mod(), 'return')
        time.sleep(1)
        return {"success": True, "action": "gmail_compose", "send_confirmed": True, "message": "Email composed and sent"}
    return {"success": True, "action": "gmail_compose", "send_confirmed": False, "message": "Email composed, ready to review"}


def gmail_reply(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_reply', args)
    _chrome_focus()
    _key('r', pause=1.0)  # Gmail shortcut: reply
    body = args.get('body', '')
    if body:
        _copy_to_clipboard(body)
        _paste_from_clipboard()
    if args.get('send'):
        time.sleep(0.3)
        _hotkey(_mod(), 'return')
        time.sleep(1)
        return {"success": True, "action": "gmail_reply", "send_confirmed": True}
    return {"success": True, "action": "gmail_reply", "send_confirmed": False}


def gmail_reply_all(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_reply_all', args)
    _chrome_focus()
    _key('a', pause=1.0)  # Gmail shortcut: reply all
    body = args.get('body', '')
    if body:
        _copy_to_clipboard(body)
        _paste_from_clipboard()
    if args.get('send'):
        time.sleep(0.3)
        _hotkey(_mod(), 'return')
        time.sleep(1)
        return {"success": True, "action": "gmail_reply_all", "send_confirmed": True}
    return {"success": True, "action": "gmail_reply_all", "send_confirmed": False}


def gmail_forward(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_forward', args)
    _chrome_focus()
    _key('f', pause=1.0)  # Gmail shortcut: forward
    to = args.get('to', '')
    if to:
        _copy_to_clipboard(to)
        _paste_from_clipboard()
        _key('tab', pause=0.3)
    body = args.get('body', '')
    if body:
        _copy_to_clipboard(body)
        _paste_from_clipboard()
    if args.get('send'):
        time.sleep(0.3)
        _hotkey(_mod(), 'return')
        time.sleep(1)
        return {"success": True, "action": "gmail_forward", "send_confirmed": True}
    return {"success": True, "action": "gmail_forward", "send_confirmed": False}


def gmail_search(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_search', args)
    _chrome_focus()
    _key('/', pause=0.5)  # Gmail shortcut: search
    query = args.get('query', '')
    _copy_to_clipboard(query)
    _paste_from_clipboard()
    _key('return', pause=1.5)
    return {"success": True, "action": "gmail_search", "query": query}


def gmail_send(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_send')
    _chrome_focus()
    _hotkey(_mod(), 'return')
    time.sleep(1)
    return {"success": True, "action": "gmail_send", "message": "Send triggered"}


def gmail_open_email(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_open_email')
    _chrome_focus()
    _key('o', pause=1.0)  # Gmail shortcut: open conversation
    return {"success": True, "action": "gmail_open_email", "message": "Opened selected email"}


def gmail_read_email(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_read_email')
    _chrome_focus()
    # Select all visible text and grab via clipboard
    _hotkey(_mod(), 'a')
    time.sleep(0.2)
    _hotkey(_mod(), 'c')
    time.sleep(0.3)
    raw = _read_clipboard()
    _key('escape')  # deselect
    # Try to parse out subject, from, body
    subject = ""
    sender = ""
    body = raw[:3000] if raw else ""
    subject_match = re.search(r'Subject[:\s]+(.+)', raw or '')
    from_match = re.search(r'From[:\s]+(.+)', raw or '')
    if subject_match:
        subject = subject_match.group(1).strip()
    if from_match:
        sender = from_match.group(1).strip()
    return {
        "success": True, "action": "gmail_read_email",
        "subject": subject, "from": sender, "body": body
    }


def gmail_back_to_list(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_back_to_list')
    _chrome_focus()
    _key('u', pause=0.5)  # Gmail shortcut: back to list
    return {"success": True, "action": "gmail_back_to_list"}


def gmail_next(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_next')
    _chrome_focus()
    _key('j', pause=0.3)  # Gmail shortcut: next conversation
    return {"success": True, "action": "gmail_next"}


def gmail_prev(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_prev')
    _chrome_focus()
    _key('k', pause=0.3)  # Gmail shortcut: previous conversation
    return {"success": True, "action": "gmail_prev"}


def gmail_archive(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_archive')
    _chrome_focus()
    _key('e', pause=0.5)  # Gmail shortcut: archive
    return {"success": True, "action": "gmail_archive", "message": "Email archived"}


def gmail_delete(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_delete')
    _chrome_focus()
    _key('#', pause=0.5)  # Gmail shortcut: delete
    return {"success": True, "action": "gmail_delete", "message": "Email deleted"}


def gmail_star(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_star')
    _chrome_focus()
    _key('s', pause=0.3)  # Gmail shortcut: toggle star
    return {"success": True, "action": "gmail_star", "message": "Star toggled"}


def gmail_mark_read(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_mark_read')
    _chrome_focus()
    _hotkey('shift', 'i')  # Gmail shortcut: mark read
    return {"success": True, "action": "gmail_mark_read"}


def gmail_mark_unread(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_mark_unread')
    _chrome_focus()
    _hotkey('shift', 'u')  # Gmail shortcut: mark unread
    return {"success": True, "action": "gmail_mark_unread"}


def gmail_label(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_label')
    _chrome_focus()
    _key('l', pause=0.5)  # Gmail shortcut: label menu
    return {"success": True, "action": "gmail_label", "message": "Label menu opened"}


def gmail_go_inbox(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_go_inbox')
    _chrome_focus()
    _hotkey('g', 'i')  # Gmail shortcut: go to inbox
    time.sleep(1)
    return {"success": True, "action": "gmail_go_inbox"}


def gmail_go_sent(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_go_sent')
    _chrome_focus()
    _hotkey('g', 't')  # Gmail shortcut: go to sent
    time.sleep(1)
    return {"success": True, "action": "gmail_go_sent"}


def gmail_go_drafts(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_go_drafts')
    _chrome_focus()
    _hotkey('g', 'd')  # Gmail shortcut: go to drafts
    time.sleep(1)
    return {"success": True, "action": "gmail_go_drafts"}


def gmail_refresh(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_refresh')
    _chrome_focus()
    _hotkey('shift', 'n')  # trigger update; also Cmd+R works
    time.sleep(0.5)
    return {"success": True, "action": "gmail_refresh"}


def gmail_undo(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_undo')
    _chrome_focus()
    _key('z', pause=0.5)  # Gmail shortcut: undo
    return {"success": True, "action": "gmail_undo"}


def gmail_select(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_select')
    _chrome_focus()
    _key('x', pause=0.2)  # Gmail shortcut: select conversation
    return {"success": True, "action": "gmail_select"}


def gmail_select_all(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_select_all')
    _chrome_focus()
    _hotkey(_mod(), 'a')
    return {"success": True, "action": "gmail_select_all"}


def gmail_spam(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_spam')
    _chrome_focus()
    _hotkey('shift', '1')  # Gmail shortcut: report spam
    return {"success": True, "action": "gmail_spam"}


def gmail_mark_important(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_mark_important')
    _chrome_focus()
    _hotkey('shift', '=')  # Gmail shortcut: mark important
    return {"success": True, "action": "gmail_mark_important"}


def gmail_mute(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_mute')
    _chrome_focus()
    _key('m', pause=0.3)  # Gmail shortcut: mute
    return {"success": True, "action": "gmail_mute"}


def gmail_snooze(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_snooze')
    _chrome_focus()
    _key('b', pause=0.5)  # Gmail shortcut: snooze
    return {"success": True, "action": "gmail_snooze"}


def gmail_move_to(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_move_to')
    _chrome_focus()
    _key('v', pause=0.5)  # Gmail shortcut: move to
    return {"success": True, "action": "gmail_move_to"}


def gmail_newer(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_newer')
    _chrome_focus()
    _key('n', pause=0.3)  # Gmail shortcut: next message in thread
    return {"success": True, "action": "gmail_newer"}


def gmail_older(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_older')
    _chrome_focus()
    _key('p', pause=0.3)  # Gmail shortcut: prev message in thread
    return {"success": True, "action": "gmail_older"}


def gmail_go_starred(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_go_starred')
    _chrome_focus()
    _hotkey('g', 's')  # Gmail shortcut: go to starred
    time.sleep(1)
    return {"success": True, "action": "gmail_go_starred"}


def gmail_go_all_mail(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('gmail_go_all_mail')
    _chrome_focus()
    _hotkey('g', 'a')  # Gmail shortcut: go to all mail
    time.sleep(1)
    return {"success": True, "action": "gmail_go_all_mail"}


# WhatsApp automation (WhatsApp Web in Chrome)

def whatsapp_open(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('whatsapp_open')
    _chrome_navigate('https://web.whatsapp.com')
    time.sleep(3)
    return {"success": True, "action": "whatsapp_open", "message": "WhatsApp Web opened"}


def whatsapp_send(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('whatsapp_send', args)
    phone = args.get('phone', args.get('to', ''))
    message = args.get('message', args.get('text', ''))
    if not phone or not message:
        return {"success": False, "action": "whatsapp_send", "error": "Need phone and message"}
    phone = re.sub(r'[^\d+]', '', phone)
    encoded = urllib.parse.quote(message)
    url = f'https://web.whatsapp.com/send?phone={phone}&text={encoded}'
    _chrome_navigate(url)
    time.sleep(4)
    _key('return', pause=1)
    return {"success": True, "action": "whatsapp_send", "message": f"Sent to {phone}"}


def whatsapp_search(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('whatsapp_search', args)
    query = args.get('query', args.get('name', ''))
    _chrome_focus()
    _hotkey(_mod(), 'f')
    time.sleep(0.3)
    _copy_to_clipboard(query)
    _paste_from_clipboard()
    time.sleep(1)
    return {"success": True, "action": "whatsapp_search", "query": query}


def whatsapp_read_messages(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('whatsapp_read_messages', args)
    _chrome_focus()
    screenshot_bytes = _take_screenshot()
    if not screenshot_bytes:
        return {"success": False, "action": "whatsapp_read_messages", "error": "Could not capture screen"}
    api_key = args.get('api_key', '')
    if not api_key:
        return {"success": False, "action": "whatsapp_read_messages", "error": "API key required for vision"}
    import base64
    b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
    try:
        import requests
        resp = requests.post(
            f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={api_key}',
            json={
                "contents": [{"parts": [
                    {"text": "Read the WhatsApp messages visible on screen. Return a structured summary: sender name, message text, and time for each visible message."},
                    {"inline_data": {"mime_type": "image/png", "data": b64}}
                ]}]
            },
            timeout=30
        )
        data = resp.json()
        text = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
        return {"success": True, "action": "whatsapp_read_messages", "messages": text}
    except Exception as e:
        return {"success": False, "action": "whatsapp_read_messages", "error": str(e)}


def whatsapp_check_unread(args):
    if SYSTEM == 'Darwin':
        return _delegate_mac('whatsapp_check_unread', args)
    _chrome_focus()
    screenshot_bytes = _take_screenshot()
    if not screenshot_bytes:
        return {"success": False, "action": "whatsapp_check_unread", "error": "Could not capture screen"}
    api_key = args.get('api_key', '')
    if not api_key:
        return {"success": False, "action": "whatsapp_check_unread", "error": "API key required"}
    import base64
    b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
    try:
        import requests
        resp = requests.post(
            f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={api_key}',
            json={
                "contents": [{"parts": [
                    {"text": "Look at this WhatsApp screen. Count the unread message indicators (green circles with numbers). Return JSON: {\"unread_chats\": N, \"chats\": [{\"name\": \"...\", \"unread\": N}]}"},
                    {"inline_data": {"mime_type": "image/png", "data": b64}}
                ]}]
            },
            timeout=30
        )
        data = resp.json()
        text = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
        return {"success": True, "action": "whatsapp_check_unread", "result": text}
    except Exception as e:
        return {"success": False, "action": "whatsapp_check_unread", "error": str(e)}


def whatsapp_send_to_contact(args):
    """Send message by searching for a contact name instead of phone number."""
    if SYSTEM == 'Darwin':
        return _delegate_mac('whatsapp_send', args)
    name = args.get('name', args.get('contact', ''))
    message = args.get('message', args.get('text', ''))
    if not name or not message:
        return {"success": False, "action": "whatsapp_send_to_contact", "error": "Need contact name and message"}
    _chrome_navigate('https://web.whatsapp.com')
    time.sleep(3)
    # Use search to find the contact
    _hotkey(_mod(), 'f')
    time.sleep(0.3)
    _copy_to_clipboard(name)
    _paste_from_clipboard()
    time.sleep(1.5)
    _key('return', pause=1)
    # Now type the message
    _copy_to_clipboard(message)
    _paste_from_clipboard()
    time.sleep(0.3)
    _key('return', pause=1)
    return {"success": True, "action": "whatsapp_send_to_contact", "message": f"Sent to {name}"}


# Command dispatch table

COMMAND_MAP = {
    'open_app': lambda cmd: open_app(cmd.get('app_name', '')),
    'close_app': lambda cmd: close_app(cmd.get('app_name', '')),
    'switch_app': lambda cmd: switch_app(cmd.get('app_name', '')),
    'list_running_apps': lambda cmd: list_running_apps(),
    'open_url': lambda cmd: open_url(cmd.get('url', '')),
    'search_web': lambda cmd: search_web(cmd.get('query', '')),
    'volume_up': lambda cmd: volume_control('up', cmd.get('amount', 10)),
    'volume_down': lambda cmd: volume_control('down', cmd.get('amount', 10)),
    'volume_mute': lambda cmd: volume_control('mute'),
    'volume_unmute': lambda cmd: volume_control('unmute'),
    'volume_set': lambda cmd: volume_control('set', cmd.get('amount', 50)),
    'brightness_up': lambda cmd: brightness_control('up', cmd.get('amount', 10)),
    'brightness_down': lambda cmd: brightness_control('down', cmd.get('amount', 10)),
    'lock_screen': lambda cmd: lock_screen(),
    'minimize_all': lambda cmd: minimize_all(),
    'sleep_computer': lambda cmd: sleep_computer(),
    'empty_trash': lambda cmd: empty_trash(),
    'get_system_info': lambda cmd: get_system_info(),
    'run_command': lambda cmd: run_command(cmd.get('command', '')),
    'show_notification': lambda cmd: show_notification(cmd.get('title', 'WishCraft'), cmd.get('message', '')),
    'file_search': lambda cmd: file_search(cmd.get('query', ''), cmd.get('directory')),
    'remove_background': lambda cmd: remove_background(cmd.get('path', ''), cmd.get('output_path')),
    'remove_background_batch': lambda cmd: remove_background_batch(cmd.get('paths', [])),
    'remove_background_folder': lambda cmd: remove_background_folder(cmd.get('folder', ''), cmd.get('output_folder')),
    'organize_scan_directory': lambda cmd: organize_scan_directory(cmd.get('path', '~'), cmd.get('max_depth', 2)),
    'organize_find_duplicates': lambda cmd: organize_find_duplicates(cmd.get('path', '~'), cmd.get('max_depth', 2), cmd.get('min_size_kb', 1)),
    'organize_by_type': lambda cmd: organize_by_type(cmd.get('path', '~'), cmd.get('dry_run', True)),
    'organize_by_date': lambda cmd: organize_by_date(cmd.get('path', '~'), cmd.get('date_format', 'year_month'), cmd.get('dry_run', True)),
    'organize_cleanup_old': lambda cmd: organize_cleanup_old(cmd.get('path', '~'), cmd.get('older_than_days', 180), cmd.get('dry_run', True)),
    'organize_remove_duplicates': lambda cmd: organize_remove_duplicates(cmd.get('path', '~'), cmd.get('max_depth', 2), cmd.get('min_size_kb', 1), cmd.get('dry_run', True)),
    'organize_suggest_plan': lambda cmd: organize_suggest_plan(cmd.get('path', '~')),
    'organize_flatten_folder': lambda cmd: organize_flatten_folder(cmd.get('path', '~'), cmd.get('dry_run', True)),
    'organize_rename_pattern': lambda cmd: organize_rename_pattern(cmd.get('path', '~'), cmd.get('pattern', 'date_prefix'), cmd.get('dry_run', True)),
    'organize_size_report': lambda cmd: organize_size_report(cmd.get('path', '~'), cmd.get('max_depth', 3)),
    # Gmail
    'gmail_open': lambda cmd: gmail_open(cmd),
    'gmail_get_state': lambda cmd: gmail_get_state(cmd),
    'gmail_ensure_list_view': lambda cmd: gmail_ensure_list_view(cmd),
    'gmail_unread_count': lambda cmd: gmail_unread_count(cmd),
    'gmail_compose': lambda cmd: gmail_compose(cmd.get('args', cmd)),
    'gmail_reply': lambda cmd: gmail_reply(cmd.get('args', cmd)),
    'gmail_reply_all': lambda cmd: gmail_reply_all(cmd.get('args', cmd)),
    'gmail_forward': lambda cmd: gmail_forward(cmd.get('args', cmd)),
    'gmail_search': lambda cmd: gmail_search(cmd.get('args', cmd)),
    'gmail_send': lambda cmd: gmail_send(cmd),
    'gmail_open_email': lambda cmd: gmail_open_email(cmd),
    'gmail_read_email': lambda cmd: gmail_read_email(cmd),
    'gmail_back_to_list': lambda cmd: gmail_back_to_list(cmd),
    'gmail_next': lambda cmd: gmail_next(cmd),
    'gmail_prev': lambda cmd: gmail_prev(cmd),
    'gmail_archive': lambda cmd: gmail_archive(cmd),
    'gmail_delete': lambda cmd: gmail_delete(cmd),
    'gmail_star': lambda cmd: gmail_star(cmd),
    'gmail_mark_read': lambda cmd: gmail_mark_read(cmd),
    'gmail_mark_unread': lambda cmd: gmail_mark_unread(cmd),
    'gmail_label': lambda cmd: gmail_label(cmd),
    'gmail_go_inbox': lambda cmd: gmail_go_inbox(cmd),
    'gmail_go_sent': lambda cmd: gmail_go_sent(cmd),
    'gmail_go_drafts': lambda cmd: gmail_go_drafts(cmd),
    'gmail_go_starred': lambda cmd: gmail_go_starred(cmd),
    'gmail_go_all_mail': lambda cmd: gmail_go_all_mail(cmd),
    'gmail_refresh': lambda cmd: gmail_refresh(cmd),
    'gmail_undo': lambda cmd: gmail_undo(cmd),
    'gmail_select': lambda cmd: gmail_select(cmd),
    'gmail_select_all': lambda cmd: gmail_select_all(cmd),
    'gmail_spam': lambda cmd: gmail_spam(cmd),
    'gmail_mark_important': lambda cmd: gmail_mark_important(cmd),
    'gmail_mute': lambda cmd: gmail_mute(cmd),
    'gmail_snooze': lambda cmd: gmail_snooze(cmd),
    'gmail_move_to': lambda cmd: gmail_move_to(cmd),
    'gmail_newer': lambda cmd: gmail_newer(cmd),
    'gmail_older': lambda cmd: gmail_older(cmd),
    # WhatsApp
    'whatsapp_open': lambda cmd: whatsapp_open(cmd),
    'whatsapp_send': lambda cmd: whatsapp_send(cmd.get('args', cmd)),
    'send_whatsapp_message': lambda cmd: whatsapp_send(cmd.get('args', cmd)),
    'whatsapp_search': lambda cmd: whatsapp_search(cmd.get('args', cmd)),
    'whatsapp_read_messages': lambda cmd: whatsapp_read_messages(cmd.get('args', cmd)),
    'read_whatsapp_messages': lambda cmd: whatsapp_read_messages(cmd.get('args', cmd)),
    'whatsapp_check_unread': lambda cmd: whatsapp_check_unread(cmd.get('args', cmd)),
    'whatsapp_send_to_contact': lambda cmd: whatsapp_send_to_contact(cmd.get('args', cmd)),
}

def execute_command(cmd):
    """Execute a universal command."""
    action = cmd.get('action', '')
    if action in COMMAND_MAP:
        return COMMAND_MAP[action](cmd)
    return None  # Not a universal command, fall through to executor.py
