#!/usr/bin/env python3
"""
WishCraft Computer Use Agent — Production Ready
Uses Gemini Computer Use API + Custom Functions to perform desktop tasks.

Architecture (per official docs: https://ai.google.dev/gemini-api/docs/computer-use):
  - Computer Use: 13 predefined screen actions (click, type, scroll, navigate, etc.)
  - Custom Functions: system-level tools (clipboard, apps, shell, file ops)
  - Multi-turn agent loop with screenshot feedback, memory management, retries

Note: Google Search & Code Execution are handled by the Live API, not this agent.
Only computer_use + function_declarations are compatible tools for this model.
"""

import sys
import json
import time
import base64
import io
import os
import platform
import subprocess

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

try:
    from google import genai
    from google.genai import types
    from google.genai.types import (
        Content, Part, GenerateContentConfig,
        FunctionResponse as GFunctionResponse,
        FinishReason,
    )
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# Screen size — auto-detected at startup, fallback to 1440x900
try:
    if HAS_PYAUTOGUI:
        _sz = pyautogui.size()
        SCREEN_WIDTH = _sz.width
        SCREEN_HEIGHT = _sz.height
    else:
        SCREEN_WIDTH = 1440
        SCREEN_HEIGHT = 900
except Exception:
    SCREEN_WIDTH = 1440
    SCREEN_HEIGHT = 900
IS_MAC = platform.system() == 'Darwin'
IS_WIN = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

# Model for Computer Use tasks
COMPUTER_USE_MODEL = 'gemini-2.5-computer-use-preview-10-2025'

MAX_RECENT_TURN_WITH_SCREENSHOTS = 3

# Max retries for API calls with exponential backoff
MAX_API_RETRIES = 5

# Predefined Computer Use functions (for screenshot memory cleanup)
PREDEFINED_COMPUTER_USE_FUNCTIONS = [
    "open_web_browser", "click_at", "hover_at", "type_text_at",
    "scroll_document", "scroll_at", "wait_5_seconds", "go_back",
    "go_forward", "search", "navigate", "key_combination", "drag_and_drop",
]

def get_screen_size():
    """Get actual screen dimensions."""
    try:
        if HAS_PYAUTOGUI:
            size = pyautogui.size()
            return size.width, size.height
    except Exception:
        pass
    return SCREEN_WIDTH, SCREEN_HEIGHT

def take_screenshot_bytes():
    """Capture screenshot and return as PNG bytes."""
    try:
        screenshot = pyautogui.screenshot()
        buffer = io.BytesIO()
        screenshot.save(buffer, format='PNG')
        return buffer.getvalue()
    except Exception as e:
        _log({"error": f"Screenshot failed: {e}"})
        return None

def take_screenshot_base64():
    """Capture screenshot and return as base64 string."""
    png_bytes = take_screenshot_bytes()
    if png_bytes:
        return base64.b64encode(png_bytes).decode('utf-8')
    return None

def _log(data):
    """Print structured JSON log to stdout for the Electron frontend."""
    print(json.dumps(data), flush=True)

def _denormalize_x(x, screen_width):
    """Convert normalized x coordinate (0-999) to actual pixel."""
    return int(int(x) / 1000 * screen_width)

def _denormalize_y(y, screen_height):
    """Convert normalized y coordinate (0-999) to actual pixel."""
    return int(int(y) / 1000 * screen_height)

# Legacy aliases for executor.py compatibility
denormalize_x = _denormalize_x
denormalize_y = _denormalize_y

def execute_computer_action(fname, args, screen_w, screen_h):
    """
    Execute a single Computer Use action via PyAutoGUI.
    Coordinates come normalized 0-999 from the model.
    Returns a dict with status info.
    """
    result = {}

    try:
        if fname == "click_at":
            x = _denormalize_x(args.get("x", 0), screen_w)
            y = _denormalize_y(args.get("y", 0), screen_h)
            pyautogui.click(x, y)
            result = {"status": "clicked", "x": x, "y": y}

        elif fname == "hover_at":
            x = _denormalize_x(args.get("x", 0), screen_w)
            y = _denormalize_y(args.get("y", 0), screen_h)
            pyautogui.moveTo(x, y, duration=0.3)
            result = {"status": "hovered", "x": x, "y": y}

        elif fname == "type_text_at":
            x = _denormalize_x(args.get("x", 0), screen_w)
            y = _denormalize_y(args.get("y", 0), screen_h)
            text = args.get("text", "")
            press_enter = args.get("press_enter", False)
            clear_before = args.get("clear_before_typing", True)

            pyautogui.click(x, y)
            time.sleep(0.2)

            if clear_before:
                pyautogui.hotkey('command' if IS_MAC else 'ctrl', 'a')
                time.sleep(0.1)
                pyautogui.press('backspace')
                time.sleep(0.1)

            if text and all(ord(c) < 128 for c in text):
                pyautogui.write(text, interval=0.03)
            elif text:
                _clipboard_paste(text)

            if press_enter:
                time.sleep(0.1)
                pyautogui.press('enter')

            result = {"status": "typed", "text": text[:50]}

        elif fname == "key_combination":
            keys_raw = args.get("keys", "")
            if isinstance(keys_raw, str):
                key_list = keys_raw.replace('+', ' ').split()
                key_map = {
                    'control': 'command' if IS_MAC else 'ctrl',
                    'ctrl': 'command' if IS_MAC else 'ctrl',
                    'alt': 'option' if IS_MAC else 'alt',
                    'meta': 'command' if IS_MAC else 'win',
                    'command': 'command',
                }
                mapped = [key_map.get(k.lower(), k.lower()) for k in key_list]
                pyautogui.hotkey(*mapped)
                result = {"status": "pressed", "keys": mapped}

        elif fname == "scroll_document":
            direction = args.get("direction", "down")
            clicks = -5 if direction in ("down", "right") else 5
            pyautogui.scroll(clicks)
            result = {"status": "scrolled", "direction": direction}

        elif fname == "scroll_at":
            x = _denormalize_x(args.get("x", 0), screen_w)
            y = _denormalize_y(args.get("y", 0), screen_h)
            direction = args.get("direction", "down")
            magnitude = int(args.get("magnitude", 3))
            pyautogui.moveTo(x, y)
            scroll_amount = magnitude if direction in ("up", "left") else -magnitude
            pyautogui.scroll(scroll_amount)
            result = {"status": "scrolled", "direction": direction}

        elif fname == "drag_and_drop":
            x = _denormalize_x(args.get("x", 0), screen_w)
            y = _denormalize_y(args.get("y", 0), screen_h)
            dx = _denormalize_x(args.get("destination_x", 0), screen_w)
            dy = _denormalize_y(args.get("destination_y", 0), screen_h)
            pyautogui.moveTo(x, y, duration=0.2)
            pyautogui.drag(dx - x, dy - y, duration=0.5)
            result = {"status": "dragged"}

        elif fname == "open_web_browser":
            import webbrowser
            webbrowser.open('https://www.google.com')
            result = {"status": "browser_opened"}

        elif fname == "navigate":
            url = args.get("url", "https://www.google.com")
            import webbrowser
            webbrowser.open(url)
            result = {"status": "navigated", "url": url}

        elif fname == "search":
            query = args.get("query", "")
            if query:
                import webbrowser
                import urllib.parse
                webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
                result = {"status": "searched", "query": query}
            else:
                pyautogui.hotkey('command' if IS_MAC else 'ctrl', 'l')
                result = {"status": "search_bar_opened"}

        elif fname == "go_back":
            pyautogui.hotkey('command' if IS_MAC else 'alt', 'left')
            result = {"status": "went_back"}

        elif fname == "go_forward":
            pyautogui.hotkey('command' if IS_MAC else 'alt', 'right')
            result = {"status": "went_forward"}

        elif fname == "wait_5_seconds":
            time.sleep(1.5)
            result = {"status": "waited"}

        else:
            result = {"status": "unknown_action", "name": fname}

    except Exception as e:
        result = {"status": "error", "error": str(e)}

    return result

def _clipboard_paste(text):
    """Paste text via clipboard — works for Unicode (Bangla, Arabic, emoji). Cross-platform."""
    if IS_MAC:
        process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        process.communicate(text.encode('utf-8'))
        time.sleep(0.1)
        pyautogui.hotkey('command', 'v')
        time.sleep(0.2)
    elif IS_WIN:
        process = subprocess.Popen(
            ['powershell', '-Command', 'Set-Clipboard -Value $input'],
            stdin=subprocess.PIPE
        )
        process.communicate(text.encode('utf-8'))
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.2)
    else:
        # Linux: xclip or xsel
        try:
            process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
            process.communicate(text.encode('utf-8'))
        except FileNotFoundError:
            process = subprocess.Popen(['xsel', '--clipboard', '--input'], stdin=subprocess.PIPE)
            process.communicate(text.encode('utf-8'))
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.2)

def _get_running_apps() -> dict:
    """Get list of currently running foreground applications. Cross-platform."""
    try:
        if IS_MAC:
            result = subprocess.run(
                ['osascript', '-e',
                 'tell application "System Events" to get name of every process whose background only is false'],
                capture_output=True, text=True, timeout=3
            )
            apps = [a.strip() for a in result.stdout.strip().split(',') if a.strip()]
            return {"apps": apps, "count": len(apps)}
        elif IS_WIN:
            result = subprocess.run(
                ['powershell', '-Command',
                 'Get-Process | Where-Object {$_.MainWindowTitle -ne ""} | Select-Object -ExpandProperty ProcessName | Sort-Object -Unique'],
                capture_output=True, text=True, timeout=5
            )
            apps = [a.strip() for a in result.stdout.strip().split('\n') if a.strip()]
            return {"apps": apps, "count": len(apps)}
        else:
            # Linux: wmctrl or xdotool
            try:
                result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True, timeout=3)
                apps = list(set(line.split(None, 3)[-1] for line in result.stdout.strip().split('\n') if line.strip()))
                return {"apps": apps, "count": len(apps)}
            except FileNotFoundError:
                result = subprocess.run(
                    ['xdotool', 'search', '--onlyvisible', '--name', ''],
                    capture_output=True, text=True, timeout=3
                )
                apps = []
                for wid in result.stdout.strip().split('\n')[:20]:
                    if wid.strip():
                        name_r = subprocess.run(['xdotool', 'getwindowname', wid.strip()],
                            capture_output=True, text=True, timeout=1)
                        if name_r.stdout.strip():
                            apps.append(name_r.stdout.strip())
                return {"apps": list(set(apps)), "count": len(set(apps))}
    except Exception as e:
        return {"apps": [], "error": str(e)}

def _get_frontmost_app() -> dict:
    """Get the name of the currently active/frontmost application. Cross-platform."""
    try:
        if IS_MAC:
            result = subprocess.run(
                ['osascript', '-e',
                 'tell application "System Events" to get the name of first process whose frontmost is true'],
                capture_output=True, text=True, timeout=2
            )
            return {"app": result.stdout.strip()}
        elif IS_WIN:
            result = subprocess.run(
                ['powershell', '-Command',
                 '(Get-Process | Where-Object {$_.MainWindowHandle -eq '
                 '(Add-Type -MemberDefinition \'[DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();\' '
                 '-Name W -Namespace N -PassThru)::GetForegroundWindow()}).ProcessName'],
                capture_output=True, text=True, timeout=3
            )
            return {"app": result.stdout.strip() or "unknown"}
        else:
            # Linux: xdotool
            result = subprocess.run(
                ['xdotool', 'getactivewindow', 'getwindowname'],
                capture_output=True, text=True, timeout=2
            )
            return {"app": result.stdout.strip() or "unknown"}
    except Exception as e:
        return {"app": "unknown", "error": str(e)}

def _read_clipboard() -> dict:
    """Read the current clipboard contents. Cross-platform."""
    try:
        if IS_MAC:
            result = subprocess.run(['pbpaste'], capture_output=True, text=True, timeout=2)
            return {"clipboard": result.stdout[:2000]}
        elif IS_WIN:
            result = subprocess.run(
                ['powershell', '-Command', 'Get-Clipboard'],
                capture_output=True, text=True, timeout=2
            )
            return {"clipboard": result.stdout[:2000]}
        else:
            # Linux: xclip or xsel
            try:
                result = subprocess.run(
                    ['xclip', '-selection', 'clipboard', '-o'],
                    capture_output=True, text=True, timeout=2
                )
                return {"clipboard": result.stdout[:2000]}
            except FileNotFoundError:
                result = subprocess.run(
                    ['xsel', '--clipboard', '--output'],
                    capture_output=True, text=True, timeout=2
                )
                return {"clipboard": result.stdout[:2000]}
    except Exception as e:
        return {"clipboard": "", "error": str(e)}

def _write_clipboard(text: str) -> dict:
    """Write text to the clipboard. Cross-platform."""
    try:
        if IS_MAC:
            process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
            process.communicate(text.encode('utf-8'))
            return {"status": "copied", "length": len(text)}
        elif IS_WIN:
            process = subprocess.Popen(
                ['powershell', '-Command', 'Set-Clipboard -Value $input'],
                stdin=subprocess.PIPE
            )
            process.communicate(text.encode('utf-8'))
            return {"status": "copied", "length": len(text)}
        else:
            # Linux: xclip or xsel
            try:
                process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
                process.communicate(text.encode('utf-8'))
            except FileNotFoundError:
                process = subprocess.Popen(['xsel', '--clipboard', '--input'], stdin=subprocess.PIPE)
                process.communicate(text.encode('utf-8'))
            return {"status": "copied", "length": len(text)}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def _open_application(app_name: str) -> dict:
    """Open an application by name. Cross-platform."""
    try:
        if IS_MAC:
            subprocess.run(['open', '-a', app_name], timeout=5)
        elif IS_WIN:
            subprocess.run(['start', '', app_name], shell=True, timeout=5)
        else:
            # Linux: try common launchers
            subprocess.Popen(
                [app_name.lower()],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        time.sleep(1)
        return {"status": "opened", "app": app_name}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def _get_browser_url() -> dict:
    """Get the current URL from the frontmost browser tab. Cross-platform."""
    try:
        if IS_MAC:
            result = subprocess.run(
                ['osascript', '-e',
                 'tell application "Google Chrome" to get URL of active tab of front window'],
                capture_output=True, text=True, timeout=2
            )
            if result.stdout.strip():
                return {"url": result.stdout.strip(), "browser": "Chrome"}
            result = subprocess.run(
                ['osascript', '-e',
                 'tell application "Safari" to get URL of front document'],
                capture_output=True, text=True, timeout=2
            )
            if result.stdout.strip():
                return {"url": result.stdout.strip(), "browser": "Safari"}
        elif IS_WIN:
            # Windows: try UI Automation for Chrome address bar
            try:
                result = subprocess.run(
                    ['powershell', '-Command',
                     'Add-Type -AssemblyName UIAutomationClient;'
                     '$root=[System.Windows.Automation.AutomationElement]::RootElement;'
                     '$cond=New-Object System.Windows.Automation.PropertyCondition('
                     '[System.Windows.Automation.AutomationElement]::NameProperty,"Google Chrome");'
                     '$chrome=$root.FindFirst([System.Windows.Automation.TreeScope]::Children,$cond);'
                     'if($chrome){$edit=$chrome.FindFirst([System.Windows.Automation.TreeScope]::Descendants,'
                     '(New-Object System.Windows.Automation.PropertyCondition('
                     '[System.Windows.Automation.AutomationElement]::ControlTypeProperty,'
                     '[System.Windows.Automation.ControlType]::Edit)));'
                     'if($edit){$edit.GetCurrentPropertyValue('
                     '[System.Windows.Automation.ValuePattern]::ValueProperty)}}'],
                    capture_output=True, text=True, timeout=5
                )
                if result.stdout.strip():
                    return {"url": result.stdout.strip(), "browser": "Chrome"}
            except Exception:
                pass
        else:
            # Linux: use xdotool to get window title (often contains URL info)
            try:
                result = subprocess.run(
                    ['xdotool', 'getactivewindow', 'getwindowname'],
                    capture_output=True, text=True, timeout=2
                )
                title = result.stdout.strip()
                if 'Chrome' in title or 'Firefox' in title:
                    return {"url": title, "browser": "from_title"}
            except Exception:
                pass
        return {"url": "", "error": "No browser URL detected"}
    except Exception as e:
        return {"url": "", "error": str(e)}

def _get_system_info() -> dict:
    """Get system information."""
    screen_w, screen_h = get_screen_size()
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "screen_width": screen_w,
        "screen_height": screen_h,
        "python_version": platform.python_version(),
    }

def _list_directory(path: str) -> dict:
    """List files in a directory."""
    try:
        expanded = os.path.expanduser(path)
        if not os.path.isdir(expanded):
            return {"error": f"Not a directory: {path}"}
        items = os.listdir(expanded)[:100]
        return {"path": expanded, "items": items, "count": len(items)}
    except Exception as e:
        return {"error": str(e)}

def _read_text_file(path: str) -> dict:
    """Read a text file (first 5000 chars)."""
    try:
        expanded = os.path.expanduser(path)
        if not os.path.isfile(expanded):
            return {"error": f"File not found: {path}"}
        with open(expanded, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read(5000)
        return {"path": expanded, "content": content, "truncated": len(content) >= 5000}
    except Exception as e:
        return {"error": str(e)}

def _build_custom_function_declarations():
    """Build the custom function declarations for Gemini."""
    return [
        {
            "name": "get_running_apps",
            "description": "Get list of all currently running foreground desktop applications. Use to check which apps are open before trying to interact with them.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "get_frontmost_app",
            "description": "Get the name of the currently active/focused application.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "read_clipboard",
            "description": "Read the current clipboard text contents. Useful after copying text with key_combination Cmd+C.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "write_clipboard",
            "description": "Write text to the system clipboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to copy to clipboard."}
                },
                "required": ["text"],
            },
        },
        {
            "name": "open_application",
            "description": "Open a desktop application by name (e.g. 'WhatsApp', 'Safari', 'Spotify', 'Finder', 'Terminal', 'Notes').",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Application name to open."}
                },
                "required": ["app_name"],
            },
        },
        {
            "name": "get_browser_url",
            "description": "Get the current URL from the frontmost browser tab (Chrome or Safari).",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "get_system_info",
            "description": "Get system info: OS, screen resolution, Python version.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "list_directory",
            "description": "List files and folders in a directory. Use ~ for home directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path to list (e.g. '~/Desktop')."}
                },
                "required": ["path"],
            },
        },
        {
            "name": "read_text_file",
            "description": "Read a text file contents (first 5000 chars). For checking config files, logs, notes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to read (e.g. '~/notes.txt')."}
                },
                "required": ["path"],
            },
        },
    ]

def _execute_custom_function(fname, args):
    """Execute a custom function and return result dict."""
    dispatch = {
        "get_running_apps": lambda a: _get_running_apps(),
        "get_frontmost_app": lambda a: _get_frontmost_app(),
        "read_clipboard": lambda a: _read_clipboard(),
        "write_clipboard": lambda a: _write_clipboard(a.get("text", "")),
        "open_application": lambda a: _open_application(a.get("app_name", "")),
        "get_browser_url": lambda a: _get_browser_url(),
        "get_system_info": lambda a: _get_system_info(),
        "list_directory": lambda a: _list_directory(a.get("path", "~")),
        "read_text_file": lambda a: _read_text_file(a.get("path", "")),
    }
    handler = dispatch.get(fname)
    if handler:
        return handler(args)
    return {"error": f"Unknown custom function: {fname}"}

CUSTOM_FUNCTION_NAMES = [
    "get_running_apps", "get_frontmost_app", "read_clipboard", "write_clipboard",
    "open_application", "get_browser_url", "get_system_info", "list_directory",
    "read_text_file",
]

def _api_call_with_retry(client, model, contents, config, max_retries=MAX_API_RETRIES):
    """Call Gemini API with exponential backoff retry for transient errors."""
    import warnings
    import contextlib

    for attempt in range(max_retries):
        try:
            # (expected when combining computer_use + function_declarations)
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', message='.*AFC.*')
                warnings.filterwarnings('ignore', message='.*automatic function calling.*')
                # Also suppress stderr AFC noise from the SDK
                old_stderr = sys.stderr
                sys.stderr = open(os.devnull, 'w')
                try:
                    response = client.models.generate_content(
                        model=model,
                        contents=contents,
                        config=config,
                    )
                finally:
                    sys.stderr.close()
                    sys.stderr = old_stderr
            return response
        except Exception as e:
            error_str = str(e)
            is_retryable = any(code in error_str for code in [
                '503', '429', '500', '502', '504', 'UNAVAILABLE',
                'RESOURCE_EXHAUSTED', 'INTERNAL', 'timeout', 'Timeout',
                'ConnectionError', 'Connection reset'
            ])
            if not is_retryable:
                raise RuntimeError(f"API error (non-retryable): {e}")
            if attempt < max_retries - 1:
                delay = 1 * (2 ** attempt)
                _log({"progress": True, "message": f"API retry {attempt + 1}/{max_retries} in {delay}s ({error_str[:80]})..."})
                time.sleep(delay)
            else:
                raise RuntimeError(f"API failed after {max_retries} retries: {e}")

def _cleanup_screenshot_memory(contents):
    """
    Keep only N most recent turns with screenshots to prevent context overflow.
    Strips FunctionResponseBlob from older turns (matches reference agent.py).
    """
    turn_with_screenshots_found = 0
    for content in reversed(contents):
        if content.role == "user" and content.parts:
            has_screenshot = False
            for part in content.parts:
                if (part.function_response
                        and part.function_response.parts
                        and part.function_response.name in PREDEFINED_COMPUTER_USE_FUNCTIONS):
                    has_screenshot = True
                    break
            if has_screenshot:
                turn_with_screenshots_found += 1
                if turn_with_screenshots_found > MAX_RECENT_TURN_WITH_SCREENSHOTS:
                    for part in content.parts:
                        if (part.function_response
                                and part.function_response.parts
                                and part.function_response.name in PREDEFINED_COMPUTER_USE_FUNCTIONS):
                            part.function_response.parts = None

def _build_function_response_part(fname, response_dict, screenshot_bytes=None, safety_ack=False):
    """
    Build a Part containing FunctionResponse with optional screenshot.
    Uses FunctionResponseBlob for screenshots (matches reference agent.py).
    """
    if safety_ack:
        response_dict["safety_acknowledgement"] = "true"

    fr_parts = None
    if screenshot_bytes and fname in PREDEFINED_COMPUTER_USE_FUNCTIONS:
        fr_parts = [
            types.FunctionResponsePart(
                inline_data=types.FunctionResponseBlob(
                    mime_type="image/png", data=screenshot_bytes
                )
            )
        ]

    return Part(function_response=types.FunctionResponse(
        name=fname,
        response=response_dict,
        parts=fr_parts,
    ))

def _detect_app_and_url(current_url="about:blank"):
    """Detect the frontmost app and browser URL (fast, with timeouts). Cross-platform."""
    app_info = _get_frontmost_app()
    app_name = app_info.get("app", "unknown")
    url = current_url

    # If a browser is focused, try to get URL
    if any(b in app_name.lower() for b in ['chrome', 'safari', 'firefox', 'edge', 'brave']):
        url_info = _get_browser_url()
        if url_info.get("url"):
            url = url_info["url"]

    return app_name, url

def _build_tools_config(include_custom_functions=True):
    """
    Build the tools list for Computer Use agent.
    Per docs: only computer_use + function_declarations are compatible.
    Google Search & Code Execution are handled by the Live API, not here.
    """
    tools = [
        types.Tool(
            computer_use=types.ComputerUse(
                environment=types.Environment.ENVIRONMENT_BROWSER
            )
        ),
    ]

    if include_custom_functions:
        # Custom user-defined functions (system-level tools)
        tools.append(types.Tool(
            function_declarations=_build_custom_function_declarations()
        ))

    return tools

def _build_generation_config(system_instruction, tools,
                             temperature=1, top_p=0.95, top_k=40,
                             max_output_tokens=8192):
    """Build the GenerateContentConfig with all settings."""
    return GenerateContentConfig(
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        max_output_tokens=max_output_tokens,
        system_instruction=system_instruction,
        tools=tools,
        thinking_config=types.ThinkingConfig(include_thoughts=True),
    )

def _process_turn(candidate, client, screen_w, screen_h, current_url, actions_taken):
    """
    Process a model response turn:
    - Extract function calls and text
    - Execute Computer Use actions + custom functions
    - Build function responses with screenshots
    Returns (status, function_response_content_or_None, summary, new_url)
    status: "CONTINUE" | "COMPLETE" | "MALFORMED"
    """
    if not candidate.content or not candidate.content.parts:
        return "COMPLETE", None, "Empty response", current_url

    function_calls = []
    text_parts = []
    for part in candidate.content.parts:
        if part.function_call:
            function_calls.append(part.function_call)
        if part.text:
            text_parts.append(part.text)

    if (not function_calls and not text_parts
            and candidate.finish_reason == FinishReason.MALFORMED_FUNCTION_CALL):
        return "MALFORMED", None, "", current_url

    if not function_calls:
        summary = " ".join(text_parts) if text_parts else "Task completed"
        return "COMPLETE", None, summary, current_url

    # Execute each function call
    function_response_parts = []
    url = current_url

    for fc in function_calls:
        fname = fc.name
        args = dict(fc.args) if fc.args else {}

        safety_ack = False
        safety_decision = args.pop('safety_decision', None)
        if safety_decision and safety_decision.get('decision') == 'require_confirmation':
            _log({"safety_confirmation": True,
                  "explanation": safety_decision.get('explanation', 'Action requires confirmation')})
            safety_ack = True

        _log({"executing": fname, "args": {k: v for k, v in args.items()
                                            if k != 'text' or len(str(v)) < 100}})
        actions_taken.append(fname)

        if fname in PREDEFINED_COMPUTER_USE_FUNCTIONS:
            if fname == "navigate":
                url = args.get("url", url)
            elif fname == "search" and args.get("query"):
                import urllib.parse
                url = f"https://www.google.com/search?q={urllib.parse.quote(args['query'])}"
            elif fname == "open_web_browser":
                url = "https://www.google.com"

            action_result = execute_computer_action(fname, args, screen_w, screen_h)
            time.sleep(0.3)

            app_name, url = _detect_app_and_url(url)
            new_ss = take_screenshot_bytes()

            fr_response = {"url": url, "current_app": app_name}
            fr_response.update(action_result)

            function_response_parts.append(
                _build_function_response_part(fname, fr_response, new_ss, safety_ack)
            )

        elif fname in CUSTOM_FUNCTION_NAMES:
            custom_result = _execute_custom_function(fname, args)
            function_response_parts.append(
                _build_function_response_part(fname, custom_result, safety_ack=safety_ack)
            )

        else:
            function_response_parts.append(
                _build_function_response_part(fname, {"error": f"Unknown function: {fname}"},
                                             safety_ack=safety_ack)
            )

    response_content = Content(role="user", parts=function_response_parts)
    return "CONTINUE", response_content, "", url

def run_agent_loop(goal, api_key, max_turns=15):
    """
    Run the full-power Computer Use agent loop.

    Capabilities:
    - Computer Use: click, type, scroll, navigate, drag, key combos on ANY app
    - Google Search: real-time web info without opening a browser
    - Code Execution: model can write & run Python for calculations
    - Custom Tools: clipboard, app control, file system, system info
    - Screenshot feedback with memory management
    - Exponential backoff retries, MALFORMED_FUNCTION_CALL auto-retry

    Returns: {success, summary, actions, turns}
    """
    if not HAS_GENAI:
        return {"success": False, "error": "google-genai not installed. Run: pip3 install google-genai"}
    if not api_key:
        return {"success": False, "error": "No GEMINI_API_KEY provided"}

    try:
        client = genai.Client(api_key=api_key)
        screen_w, screen_h = get_screen_size()

        # Detect running apps for context
        running_apps_info = ""
        try:
            apps_data = _get_running_apps()
            if apps_data.get("apps"):
                running_apps_info = f"\nCurrently running desktop apps: {', '.join(apps_data['apps'])}"
        except Exception:
            pass

        # Detect frontmost app and browser URL for context (saves 2-3 turns)
        current_app_info = ""
        try:
            app_name, browser_url = _detect_app_and_url()
            current_app_info = f"\nCurrently active app: {app_name}"
            if browser_url and browser_url != "about:blank":
                current_app_info += f"\nCurrent browser URL: {browser_url}"
        except Exception:
            pass

        system_instruction = f"""You are a powerful desktop automation agent controlling a real {platform.system()} computer.
You can see the FULL DESKTOP screen and interact with ANY application — browsers, desktop apps, system controls, everything.
Screen resolution: {screen_w}x{screen_h}. Computer Use coordinates are normalized 0-999.

YOU HAVE 2 TYPES OF TOOLS:

1. COMPUTER USE (13 screen actions): click_at, type_text_at, scroll_at, scroll_document, key_combination, navigate, go_back, go_forward, search, hover_at, drag_and_drop, open_web_browser, wait_5_seconds
   → For interacting with what's on screen. Coordinates are normalized 0-999.

2. CUSTOM FUNCTIONS (system-level, no screenshot needed):
   - get_running_apps() → see what apps are open
   - get_frontmost_app() → which app is active
   - read_clipboard() → read clipboard text (after Cmd+C)
   - write_clipboard(text) → write to clipboard
   - open_application(app_name) → open any app by name
   - get_browser_url() → get current browser tab URL
   - get_system_info() → OS, screen size, etc.
   - list_directory(path) → list files in a folder
   - read_text_file(path) → read a text file

CRITICAL RULES:
1. ALWAYS COMPLETE THE FULL TASK. Do NOT stop halfway.
2. You control a REAL desktop. You CAN click videos, buttons, links. NEVER say "I cannot do that".
3. PREFER desktop apps over browser when the app is installed and running.
4. Look at the CURRENT SCREEN first. If content is already visible, interact directly — do NOT re-open apps or re-navigate to pages you can already see.
5. If you see a login screen (QR code, password), STOP and tell the user.
6. Be FAST — NEVER use wait_5_seconds unless a page is visibly still loading. Skip waits if content is already loaded.
7. Do NOT call get_running_apps or get_frontmost_app or get_browser_url — this info is already given above. Do NOT call open_application if the app is already active/frontmost.
8. Use read_clipboard after Cmd+C to extract text reliably.
9. When done, respond with a clear text summary of what you accomplished.
10. SPEED: Use the FEWEST actions possible. Navigate directly to URLs instead of searching. Click targets you can see on screen immediately.
{running_apps_info}{current_app_info}"""

        # (Google Search & Code Execution are handled by the Live API)
        tools = _build_tools_config(include_custom_functions=True)
        config = _build_generation_config(system_instruction, tools)

        # Take initial screenshot
        initial_ss = take_screenshot_bytes()
        if not initial_ss:
            return {"success": False, "error": "Failed to capture initial screenshot"}

        cancel_file = '/tmp/wishcraft_cancel' if not IS_WIN else os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'wishcraft_cancel')
        if os.path.exists(cancel_file):
            os.remove(cancel_file)

        # Enhanced goal
        enhanced_goal = (
            goal +
            "\n\nIMPORTANT: Always type search terms in English. "
            "ALWAYS click to play/open/send — complete the full task. "
            "You are controlling a REAL desktop — you CAN click anything. "
            "Use custom tools (get_running_apps, open_application, read_clipboard, etc.) when faster than screen interaction."
        )

        contents = [
            Content(
                role="user",
                parts=[
                    Part(text=enhanced_goal),
                    Part.from_bytes(data=initial_ss, mime_type='image/png')
                ]
            )
        ]

        actions_taken = []
        summary = ""
        current_url = "about:blank"

        # Double-clean cancel file right before loop (in case of race condition)
        if os.path.exists(cancel_file):
            os.remove(cancel_file)

        # Agent loop
        for turn in range(max_turns):
            if os.path.exists(cancel_file):
                os.remove(cancel_file)
                return {"success": True, "summary": "Task cancelled by user",
                        "actions": actions_taken, "turns": turn}

            _log({"progress": True, "turn": turn + 1, "max_turns": max_turns,
                  "message": f"Thinking... (turn {turn + 1}/{max_turns})"})

            try:
                response = _api_call_with_retry(client, COMPUTER_USE_MODEL, contents, config)
            except RuntimeError as e:
                return {"success": False, "error": str(e)}

            if not response or not response.candidates:
                return {"success": False, "error": "Empty response from model"}

            candidate = response.candidates[0]
            if candidate.content:
                contents.append(candidate.content)

            status, response_content, turn_summary, current_url = _process_turn(
                candidate, client, screen_w, screen_h, current_url, actions_taken
            )

            if status == "COMPLETE":
                summary = turn_summary
                break
            elif status == "MALFORMED":
                continue
            elif status == "CONTINUE" and response_content:
                contents.append(response_content)
                _cleanup_screenshot_memory(contents)

        return {
            "success": True,
            "summary": summary or f"Completed {len(actions_taken)} actions",
            "actions": actions_taken,
            "turns": turn + 1 if 'turn' in dir() else 0,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

def find_and_click(description, api_key, click=True):
    """
    ONE-TURN Computer Use: take screenshot, model returns action(s).
    Executes ALL actions the model returns (click, scroll, type, etc.).
    Returns {found: bool, message: str}
    """
    if not HAS_GENAI or not api_key:
        return {"found": False, "message": "No API key or google-genai not installed"}

    try:
        client = genai.Client(api_key=api_key)
        screen_w, screen_h = get_screen_size()

        ss = take_screenshot_bytes()
        if not ss:
            return {"found": False, "message": "Screenshot failed"}

        config = GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            system_instruction=f"""You are looking at a screenshot ({screen_w}x{screen_h}).
You can perform ANY action needed: click, scroll, type, press keys, drag, navigate, etc.
Do what the user asks. If you need to scroll, use scroll_at. If you need to click, use click_at.
If the task requires multiple steps, do the FIRST step now.""",
            tools=[
                types.Tool(
                    computer_use=types.ComputerUse(
                        environment=types.Environment.ENVIRONMENT_BROWSER
                    )
                )
            ],
            thinking_config=types.ThinkingConfig(include_thoughts=True),
        )

        contents = [
            Content(
                role="user",
                parts=[
                    Part(text=description),
                    Part.from_bytes(data=ss, mime_type='image/png')
                ]
            )
        ]

        response = _api_call_with_retry(client, COMPUTER_USE_MODEL, contents, config)
        candidate = response.candidates[0]

        function_calls = [p.function_call for p in candidate.content.parts if p.function_call]
        text_parts = [p.text for p in candidate.content.parts if p.text]

        if function_calls:
            executed = []
            # Actions that should be skipped inside find_and_click (only skip opening NEW browser)
            skip_actions = {"open_web_browser"}
            for fc in function_calls:
                if fc.name in skip_actions:
                    continue
                execute_computer_action(fc.name, dict(fc.args), screen_w, screen_h)
                executed.append(fc.name)
                time.sleep(0.3)

            # If all actions were skipped, treat as not found
            if not executed:
                msg = " ".join(text_parts) if text_parts else "Model returned only browser actions (skipped)"
                return {"found": False, "message": msg}

            msg = " ".join(text_parts) if text_parts else f"Executed: {', '.join(executed)}"
            return {"found": True, "message": msg, "actions": executed, "what": description}
        else:
            msg = " ".join(text_parts) if text_parts else "Could not find what was requested"
            return {"found": False, "message": msg}

    except Exception as e:
        return {"found": False, "message": f"Error: {str(e)}"}

def send_whatsapp_message(name, message_text, api_key):
    """
    Send WhatsApp message:
    1. Opens WhatsApp desktop
    2. Computer Use agent searches, finds contact, types, sends
    """
    try:
        _log({"progress": True, "message": "Opening WhatsApp..."})
        if IS_MAC:
            subprocess.run(['open', '-a', 'WhatsApp'], timeout=3)
        elif IS_WIN:
            subprocess.run(['start', 'whatsapp:'], shell=True, timeout=3)
        elif IS_LINUX:
            subprocess.Popen(['whatsapp-for-linux'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.5)

        goal = f"""Send "{message_text}" to "{name}" in WhatsApp.
If {name}'s chat is already open, just type and send.
Otherwise search for "{name}", click the contact, type the message, and send it."""

        _log({"progress": True, "message": f"Sending to {name}..."})
        result = _run_whatsapp_agent(goal, api_key, max_turns=8)
        return result

    except Exception as e:
        return {"success": False, "error": str(e)}

def _run_whatsapp_agent(goal, api_key, max_turns=8):
    """Mini Computer Use agent loop for WhatsApp tasks."""
    if not HAS_GENAI or not api_key:
        return {"success": False, "error": "No API key"}

    try:
        client = genai.Client(api_key=api_key)
        screen_w, screen_h = get_screen_size()

        config = GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            system_instruction=f"""You are a WhatsApp automation agent controlling a real {platform.system()} desktop.
Screen resolution: {screen_w}x{screen_h}. Coordinates are normalized 0-999.

WhatsApp is ALREADY OPEN on screen. Look at the screenshot carefully.

WHATSAPP UI GUIDE:
- LEFT SIDE: chat list with recent conversations.
- TOP LEFT: search/filter bar — click and type a contact name.
- RIGHT SIDE: active chat with message history.
- BOTTOM RIGHT: message input field — click, type, press Enter.

HOW TO SEND:
1. If contact visible in chat list, click them directly. Skip to step 3.
2. If NOT visible: click search bar, type name, click matching result.
3. Click message input field at bottom.
4. Type message using type_text_at (set press_enter=true to send).
5. DONE — respond with text summary.

SMART SEARCH: Try full name first. If no results, try first 3-4 letters.
RULES: Do NOT open browser. WhatsApp desktop is open. Be FAST.""",
            tools=[
                types.Tool(
                    computer_use=types.ComputerUse(
                        environment=types.Environment.ENVIRONMENT_BROWSER
                    )
                )
            ],
            thinking_config=types.ThinkingConfig(include_thoughts=True),
        )

        initial_ss = take_screenshot_bytes()
        if not initial_ss:
            return {"success": False, "error": "Screenshot failed"}

        contents = [
            Content(
                role="user",
                parts=[
                    Part(text=goal),
                    Part.from_bytes(data=initial_ss, mime_type='image/png')
                ]
            )
        ]

        actions_taken = []

        for turn in range(max_turns):
            _log({"progress": True, "turn": turn + 1, "max_turns": max_turns,
                  "message": f"Working... (step {turn + 1}/{max_turns})"})

            try:
                response = _api_call_with_retry(client, COMPUTER_USE_MODEL, contents, config)
            except RuntimeError as e:
                return {"success": False, "error": str(e)}

            if not response or not response.candidates:
                return {"success": False, "error": "Empty response"}

            candidate = response.candidates[0]
            if candidate.content:
                contents.append(candidate.content)

            function_calls = []
            text_parts = []
            for part in candidate.content.parts:
                if part.function_call:
                    function_calls.append(part.function_call)
                if part.text:
                    text_parts.append(part.text)

            if (not function_calls and not text_parts
                    and candidate.finish_reason == FinishReason.MALFORMED_FUNCTION_CALL):
                continue

            if not function_calls:
                summary = " ".join(text_parts) if text_parts else "Task completed"
                return {"success": True, "message": summary,
                        "actions": actions_taken, "turns": turn + 1}

            function_response_parts = []
            for fc in function_calls:
                fname = fc.name
                args = dict(fc.args) if fc.args else {}

                safety_ack = False
                safety_decision = args.pop('safety_decision', None)
                if safety_decision and safety_decision.get('decision') == 'require_confirmation':
                    _log({"safety_confirmation": True,
                          "explanation": safety_decision.get('explanation', '')})
                    safety_ack = True

                _log({"executing": fname, "args": args})
                actions_taken.append(fname)

                action_result = execute_computer_action(fname, args, screen_w, screen_h)
                time.sleep(0.5)
                new_ss = take_screenshot_bytes()

                fr_response = {"status": "ok", "url": "about:screen"}
                fr_response.update(action_result)

                function_response_parts.append(
                    _build_function_response_part(fname, fr_response, new_ss, safety_ack)
                )

            contents.append(Content(role="user", parts=function_response_parts))
            _cleanup_screenshot_memory(contents)

        return {"success": True, "message": "Completed",
                "actions": actions_taken, "turns": max_turns}

    except Exception as e:
        return {"success": False, "error": str(e)}

def _extract_youtube_id(url):
    """Extract 11-char YouTube video ID from a URL. Returns ID or None."""
    import re
    # youtube.com/watch?v=ID
    m = re.search(r'youtube\.com/watch\?v=([A-Za-z0-9_-]{11})', url)
    if m:
        return m.group(1)
    # youtu.be/ID
    m = re.search(r'youtu\.be/([A-Za-z0-9_-]{11})', url)
    if m:
        return m.group(1)
    return None

def _follow_redirect(url, timeout=5):
    """Follow a redirect URL and return the final destination URL."""
    import urllib.request
    try:
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0')
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.url
    except Exception:
        # Some servers don't support HEAD, try GET with no body
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            resp = urllib.request.urlopen(req, timeout=timeout)
            return resp.url
        except Exception:
            pass
    return None

def _search_youtube_url(query, api_key):
    """Use Gemini with Google Search grounding to get a direct YouTube video URL.
    Extracts URLs from grounding_metadata, follows Google redirect URLs.
    Returns a youtube.com/watch?v=... URL or None."""

    if not HAS_GENAI or not api_key:
        return None

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=f"Find a YouTube video for: {query}",
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.0,
            )
        )

        candidate = response.candidates[0] if response.candidates else None
        if candidate and hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
            gm = candidate.grounding_metadata

            if hasattr(gm, 'grounding_chunks') and gm.grounding_chunks:
                for chunk in gm.grounding_chunks:
                    if hasattr(chunk, 'web') and chunk.web:
                        uri = getattr(chunk.web, 'uri', None)
                        title = getattr(chunk.web, 'title', '') or ''

                        # Direct YouTube URL in URI
                        if uri:
                            vid = _extract_youtube_id(uri)
                            if vid:
                                url = f"https://www.youtube.com/watch?v={vid}"
                                _log({"progress": True, "message": f"Direct grounding URL: {url}"})
                                return url

                        if uri and 'grounding-api-redirect' in uri and 'youtube' in title.lower():
                            _log({"progress": True, "message": "Following Google redirect..."})
                            final_url = _follow_redirect(uri)
                            if final_url:
                                _log({"progress": True, "message": f"Redirect resolved: {final_url[:100]}"})
                                vid = _extract_youtube_id(final_url)
                                if vid:
                                    url = f"https://www.youtube.com/watch?v={vid}"
                                    _log({"progress": True, "message": f"Found via redirect: {url}"})
                                    return url

    except Exception as e:
        _log({"progress": True, "message": f"Search grounding failed: {e}"})

    return None

def play_youtube(query, api_key):
    """Fast YouTube: first tries direct URL via Google Search grounding,
    falls back to search page + Computer Use clicking."""
    import webbrowser
    import urllib.parse

    try:
        _log({"progress": True, "message": f"Searching for '{query}' video link..."})
        direct_url = _search_youtube_url(query, api_key)

        if direct_url:
            _log({"progress": True, "message": f"Found direct link, opening..."})
            webbrowser.open(direct_url)
            return {"success": True, "message": f"Playing: {query}", "url": direct_url}

        _log({"progress": True, "message": f"No direct link, searching YouTube..."})
        search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        webbrowser.open(search_url)

        # Wait for page to load, then scroll past ads
        time.sleep(4)
        pyautogui.scroll(-5)
        time.sleep(1)
        _log({"progress": True, "message": "Finding video to play..."})

        find_result = find_and_click(
            "Click the FIRST non-ad video thumbnail on this YouTube search results page. "
            "Skip any results that say 'Ad' or 'Sponsored'. Click the actual video thumbnail image, NOT text.",
            api_key, click=True
        )

        if find_result.get("found") and find_result.get("actions"):
            return {"success": True, "message": f"Playing: {query}"}

        # Last resort: click center-left area where first real video usually is
        _log({"progress": True, "message": "Clicking first video directly..."})
        screen_w, screen_h = get_screen_size()
        pyautogui.click(int(screen_w * 0.35), int(screen_h * 0.45))
        time.sleep(1)
        return {"success": True, "message": f"Playing: {query}"}

    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == '__main__':
    if len(sys.argv) > 1:
        goal = sys.argv[1]
        api_key = sys.argv[2] if len(sys.argv) > 2 else ""
        result = run_agent_loop(goal, api_key)
        print(json.dumps(result), flush=True)
    else:
        print("Usage: python3 computer_use_agent.py 'goal' 'api_key'")
