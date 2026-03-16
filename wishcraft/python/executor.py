#!/usr/bin/env python3
"""
WishCraft PyAutoGUI Executor
Receives JSON commands via stdin, executes desktop actions, returns results via stdout.

Communication protocol:
  IN:  {"action": "click", "x": 500, "y": 300, "screenWidth": 1440, "screenHeight": 900}
  OUT: {"success": true, "action": "click", "message": "Clicked at (720, 450)"}
"""

import sys
import json
import time
import os
import platform

SYSTEM = platform.system()  # 'Windows', 'Darwin', 'Linux'

try:
    import pyautogui
    pyautogui.FAILSAFE = True  # Move mouse to corner to abort
    pyautogui.PAUSE = 0.3  # Small delay between actions
except ImportError:
    print(json.dumps({"error": "PyAutoGUI not installed. Run: pip install pyautogui"}), flush=True)
    sys.exit(1)

try:
    from PIL import Image
    import io
    import base64
except ImportError:
    print(json.dumps({"error": "Pillow not installed. Run: pip install pillow"}), flush=True)

def get_api_key(cmd=None):
    """Get API key from environment variable (set by Electron main process).
    Never reads from action payload to prevent key leakage in logs."""
    return os.environ.get('GEMINI_API_KEY', '')

def get_screen_size():
    """Get actual screen dimensions."""
    size = pyautogui.size()
    return size.width, size.height

def denormalize_coords(x, y, screen_width=None, screen_height=None):
    """
    Convert Computer Use normalized coordinates (0-999) to actual screen pixels.
    Per Gemini docs: model outputs coordinates scaled 0-999 regardless of screen size.
    Formula: actual = normalized / 1000 * screen_dimension
    """
    actual_w, actual_h = get_screen_size()
    if screen_width and screen_height:
        actual_x = int(x / 1000 * actual_w)
        actual_y = int(y / 1000 * actual_h)
    else:
        actual_x = int(x)
        actual_y = int(y)
    return actual_x, actual_y

def execute_action(cmd):
    """Execute a single action command."""
    action = cmd.get('action', '')

    try:
        from commands import execute_command
        universal_result = execute_command(cmd)
        if universal_result is not None:
            return universal_result
    except ImportError:
        pass

    result = {"success": False, "action": action}

    try:

        if action == 'click' or action == 'click_at':
            x, y = denormalize_coords(
                cmd.get('x', 0), cmd.get('y', 0),
                cmd.get('screenWidth'), cmd.get('screenHeight')
            )
            pyautogui.click(x, y)
            result = {"success": True, "action": "click_at", "message": f"Clicked at ({x}, {y})"}

        elif action == 'double_click':
            x, y = denormalize_coords(
                cmd.get('x', 0), cmd.get('y', 0),
                cmd.get('screenWidth'), cmd.get('screenHeight')
            )
            pyautogui.doubleClick(x, y)
            result = {"success": True, "action": "double_click", "message": f"Double-clicked at ({x}, {y})"}

        elif action == 'right_click':
            x, y = denormalize_coords(
                cmd.get('x', 0), cmd.get('y', 0),
                cmd.get('screenWidth'), cmd.get('screenHeight')
            )
            pyautogui.rightClick(x, y)
            result = {"success": True, "action": "right_click", "message": f"Right-clicked at ({x}, {y})"}

        elif action == 'type' or action == 'type_text_at':
            text = cmd.get('text', '')
            x = cmd.get('x')
            y = cmd.get('y')
            if x is not None and y is not None:
                ax, ay = denormalize_coords(x, y, cmd.get('screenWidth'), cmd.get('screenHeight'))
                pyautogui.click(ax, ay)
                time.sleep(0.2)
            if cmd.get('clear_before_typing', False):
                pyautogui.hotkey('command' if SYSTEM == 'Darwin' else 'ctrl', 'a')
                time.sleep(0.1)
                pyautogui.press('backspace')
                time.sleep(0.1)
            if all(ord(c) < 128 for c in text):
                pyautogui.write(text, interval=0.03)
            else:
                import subprocess
                if SYSTEM == 'Darwin':
                    process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
                    process.communicate(text.encode('utf-8'))
                elif SYSTEM == 'Windows':
                    subprocess.run(['powershell', '-Command', f'Set-Clipboard -Value "{text}"'],
                                 capture_output=True, timeout=5)
                else:
                    process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
                    process.communicate(text.encode('utf-8'))
                time.sleep(0.1)
                pyautogui.hotkey('command' if SYSTEM == 'Darwin' else 'ctrl', 'v')
                time.sleep(0.2)
            if cmd.get('press_enter', False):
                pyautogui.press('enter')
            result = {"success": True, "action": "type_text_at", "message": f"Typed: '{text[:50]}'"}

        elif action == 'hotkey' or action == 'key_combination':
            keys = cmd.get('keys', '')
            if isinstance(keys, str):
                key_list = keys.replace('+', ' ').split()
                key_list = ['command' if k.lower() == 'control' and SYSTEM == 'Darwin' else k.lower() for k in key_list]
                pyautogui.hotkey(*key_list)
            result = {"success": True, "action": "key_combination", "message": f"Pressed: {keys}"}

        elif action == 'scroll' or action == 'scroll_at' or action == 'scroll_document':
            direction = cmd.get('direction', 'down')
            magnitude = cmd.get('magnitude', 3)
            x = cmd.get('x')
            y = cmd.get('y')
            clicks = -magnitude if direction in ('down', 'right') else magnitude
            if x is not None and y is not None:
                ax, ay = denormalize_coords(x, y, cmd.get('screenWidth'), cmd.get('screenHeight'))
                pyautogui.scroll(clicks, ax, ay)
            else:
                pyautogui.scroll(clicks)
            result = {"success": True, "action": action, "message": f"Scrolled {direction}"}

        elif action == 'hover' or action == 'hover_at':
            x, y = denormalize_coords(
                cmd.get('x', 0), cmd.get('y', 0),
                cmd.get('screenWidth'), cmd.get('screenHeight')
            )
            pyautogui.moveTo(x, y, duration=0.3)
            result = {"success": True, "action": "hover_at", "message": f"Hovered at ({x}, {y})"}

        elif action == 'drag_and_drop':
            x, y = denormalize_coords(
                cmd.get('x', 0), cmd.get('y', 0),
                cmd.get('screenWidth'), cmd.get('screenHeight')
            )
            dx, dy = denormalize_coords(
                cmd.get('destination_x', 0), cmd.get('destination_y', 0),
                cmd.get('screenWidth'), cmd.get('screenHeight')
            )
            pyautogui.moveTo(x, y, duration=0.2)
            pyautogui.drag(dx - x, dy - y, duration=0.5)
            result = {"success": True, "action": "drag_and_drop", "message": f"Dragged ({x},{y}) to ({dx},{dy})"}

        elif action == 'open_web_browser':
            import webbrowser
            webbrowser.open('https://www.google.com')
            result = {"success": True, "action": "open_web_browser", "message": "Opened web browser"}

        elif action == 'navigate':
            import webbrowser
            url = cmd.get('url', 'https://www.google.com')
            webbrowser.open(url)
            result = {"success": True, "action": "navigate", "message": f"Navigated to {url}"}

        elif action == 'search':
            import webbrowser
            import urllib.parse
            query = cmd.get('query', '')
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            webbrowser.open(url)
            result = {"success": True, "action": "search", "message": f"Searched: {query}"}

        elif action == 'go_back':
            pyautogui.hotkey('command' if SYSTEM == 'Darwin' else 'alt', 'left')
            result = {"success": True, "action": "go_back", "message": "Went back"}

        elif action == 'go_forward':
            pyautogui.hotkey('command' if SYSTEM == 'Darwin' else 'alt', 'right')
            result = {"success": True, "action": "go_forward", "message": "Went forward"}

        elif action == 'wait_5_seconds':
            time.sleep(5)
            result = {"success": True, "action": "wait_5_seconds", "message": "Waited 5 seconds"}

        elif action == 'send_whatsapp_message' or action.startswith('whatsapp_'):
            args = {k: v for k, v in cmd.items() if k != 'action'}
            if 'api_key' not in args:
                args['api_key'] = get_api_key()
            wa_action = 'whatsapp_send' if action == 'send_whatsapp_message' else action
            if SYSTEM == 'Darwin':
                from macos_automation import execute_automation
                return execute_automation(wa_action, args)
            else:
                try:
                    from windows_automation import execute_automation as win_execute
                    return win_execute(wa_action, args)
                except (ImportError, Exception):
                    result = {"success": False, "action": wa_action, "error": f"WhatsApp automation not available on {SYSTEM}"}

        elif action == 'find_and_click':
            description = cmd.get('description', '')
            do_click = cmd.get('click', True)
            from computer_use_agent import find_and_click
            return find_and_click(description, get_api_key(), click=do_click)

        elif action == 'play_youtube':
            query = cmd.get('query', '')
            from computer_use_agent import play_youtube
            return play_youtube(query, get_api_key())

        elif action == 'computer_use_task':
            goal = cmd.get('goal', '')
            max_turns = cmd.get('max_turns', 10)
            from computer_use_agent import run_agent_loop
            return run_agent_loop(goal, get_api_key(), max_turns)

        elif action == 'cancel_computer_task':
            cancel_path = '/tmp/wishcraft_cancel' if SYSTEM != 'Windows' else os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'wishcraft_cancel')
            with open(cancel_path, 'w') as f:
                f.write('cancel')
            result = {"success": True, "action": "cancel", "message": "Task cancellation requested"}

        elif action == 'open_application':
            from commands import open_app
            return open_app(cmd.get('app_name', ''))

        elif action == 'screenshot':
            screenshot = pyautogui.screenshot()
            buffer = io.BytesIO()
            screenshot.save(buffer, format='PNG')
            b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            result = {"success": True, "action": "screenshot", "screenshot": b64}

        elif action == 'wait':
            duration = cmd.get('duration', 5)
            time.sleep(duration)
            result = {"success": True, "action": "wait", "message": f"Waited {duration}s"}

        elif action == 'press':
            key = cmd.get('key', 'enter')
            times = cmd.get('times', 1)
            pyautogui.press(key, presses=times, interval=0.1)
            result = {"success": True, "action": "press", "message": f"Pressed {key}" + (f" x{times}" if times > 1 else "")}

        elif action == 'mouse_down':
            button = cmd.get('button', 'left')
            pyautogui.mouseDown(button=button)
            result = {"success": True, "action": "mouse_down", "message": f"Mouse down ({button})"}

        elif action == 'mouse_up':
            button = cmd.get('button', 'left')
            pyautogui.mouseUp(button=button)
            result = {"success": True, "action": "mouse_up", "message": f"Mouse up ({button})"}

        elif action == 'triple_click':
            x, y = denormalize_coords(
                cmd.get('x', 0), cmd.get('y', 0),
                cmd.get('screenWidth'), cmd.get('screenHeight')
            )
            pyautogui.tripleClick(x, y)
            result = {"success": True, "action": "triple_click", "message": f"Triple-clicked at ({x}, {y})"}

        elif action == 'move_relative':
            pyautogui.move(cmd.get('x', 0), cmd.get('y', 0), duration=0.3)
            result = {"success": True, "action": "move_relative", "message": "Moved relative"}

        else:
            if SYSTEM == 'Darwin':
                from macos_automation import execute_automation
                mac_result = execute_automation(action, cmd)
                if mac_result and not (mac_result.get('error') or '').startswith('Unknown automation action'):
                    return mac_result
            elif SYSTEM == 'Windows':
                try:
                    from windows_automation import execute_automation as win_execute
                    win_result = win_execute(action, cmd)
                    if win_result and not (win_result.get('error') or '').startswith('Unknown'):
                        return win_result
                except ImportError:
                    pass
            elif SYSTEM == 'Linux':
                try:
                    from linux_automation import execute_automation as linux_execute
                    linux_result = linux_execute(action, cmd)
                    if linux_result and not (linux_result.get('error') or '').startswith('Unknown'):
                        return linux_result
                except ImportError:
                    pass

            result = {"success": False, "action": action, "error": f"Unknown action: {action}"}

    except Exception as e:
        result = {"success": False, "action": action, "error": str(e)}

    return result

def main():
    """Main loop: read JSON commands from stdin, execute, write results to stdout."""
    print(json.dumps({"status": "ready", "platform": SYSTEM, "screen": list(get_screen_size())}), flush=True)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            cmd = json.loads(line)
            result = execute_action(cmd)
            print(json.dumps(result), flush=True)
        except json.JSONDecodeError:
            print(json.dumps({"error": f"Invalid JSON: {line[:100]}"}), flush=True)
        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)

if __name__ == '__main__':
    main()
