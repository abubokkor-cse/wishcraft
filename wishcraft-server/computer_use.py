#!/usr/bin/env python3
"""
WishCraft Computer Use Agent
Receives a goal + screenshot via stdin, runs Gemini Computer Use agent loop,
returns a list of desktop actions to execute.

Input (JSON via stdin):
{
    "goal": "Open Chrome and search for weather",
    "screenshot": "<base64 PNG>",
    "screen_width": 1440,
    "screen_height": 900,
    "scale_factor": 2,
    "api_key": "..."
}

Output (JSON via stdout):
{
    "actions": [
        {"action": "click_at", "x": 500, "y": 300},
        {"action": "type_text_at", "x": 400, "y": 250, "text": "weather forecast"}
    ],
    "summary": "Opened Chrome and searched for weather"
}
"""

import sys
import json
import base64
from typing import Any, Dict, List, Optional

try:
    from google import genai
    from google.genai import types
    from google.genai.types import Content, Part
except ImportError:
    print(json.dumps({"error": "google-genai not installed. Run: pip install google-genai"}))
    sys.exit(1)


# Custom Desktop Functions
# (Sent to Gemini Computer Use as additional tools)

def desktop_click(x: int, y: int) -> Dict[str, Any]:
    """Click at a specific screen coordinate."""
    return {"action": "click_at", "x": x, "y": y}

def desktop_type(x: int, y: int, text: str, press_enter: bool = False, clear_before_typing: bool = False) -> Dict[str, Any]:
    """Type text at a specific screen coordinate."""
    return {"action": "type_text_at", "x": x, "y": y, "text": text, "press_enter": press_enter, "clear_before_typing": clear_before_typing}

def desktop_hotkey(keys: str) -> Dict[str, Any]:
    """Press a keyboard shortcut (e.g., 'Control+C')."""
    return {"action": "key_combination", "keys": keys}

def desktop_scroll(x: int, y: int, direction: str = "down", magnitude: int = 3) -> Dict[str, Any]:
    """Scroll at a specific position."""
    return {"action": "scroll_at", "x": x, "y": y, "direction": direction, "magnitude": magnitude}

def open_application(app_name: str) -> Dict[str, Any]:
    """Open a desktop application by name."""
    return {"action": "open_application", "app_name": app_name}

def take_screenshot() -> Dict[str, Any]:
    """Request a new screenshot from the desktop client."""
    return {"action": "screenshot"}


# Agent Loop

def run_computer_use(goal: str, screenshot_b64: str, screen_width: int, screen_height: int,
                     scale_factor: float, api_key: str) -> Dict[str, Any]:
    """
    Run the Gemini Computer Use agent loop.
    Returns a list of actions for the desktop client to execute.
    """
    client = genai.Client(api_key=api_key)

    custom_functions = [
        types.FunctionDeclaration.from_callable(client=client, callable=open_application),
    ]

    # Exclude browser-only functions since we're controlling a desktop
    excluded_functions = [
        "open_web_browser",
        "navigate",
        "search",
        "go_back",
        "go_forward",
    ]

    # Computer Use config
    config = types.GenerateContentConfig(
        tools=[
            types.Tool(
                computer_use=types.ComputerUse(
                    environment=types.Environment.ENVIRONMENT_BROWSER,
                    excluded_predefined_functions=excluded_functions,
                )
            ),
            types.Tool(function_declarations=custom_functions),
        ],
    )

    # Decode screenshot
    screenshot_bytes = base64.b64decode(screenshot_b64)

    contents = [
        Content(
            role="user",
            parts=[
                Part(text=f"Desktop task: {goal}. Screen is {screen_width}x{screen_height} pixels (scale factor: {scale_factor})."),
                Part.from_bytes(data=screenshot_bytes, mime_type="image/png"),
            ],
        )
    ]

    collected_actions = []
    turn_limit = 5  # Max actions per task

    for turn in range(turn_limit):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-computer-use-preview-10-2025",
                contents=contents,
                config=config,
            )
        except Exception as e:
            return {
                "actions": collected_actions,
                "summary": f"Error on turn {turn + 1}: {str(e)}",
                "error": str(e)
            }

        candidate = response.candidates[0]
        contents.append(candidate.content)

        # Check for function calls
        has_function_calls = any(part.function_call for part in candidate.content.parts)

        if not has_function_calls:
            # Model is done — extract text response
            text_response = " ".join([
                part.text for part in candidate.content.parts
                if part.text and not getattr(part, 'thought', False)
            ])
            return {
                "actions": collected_actions,
                "summary": text_response or f"Completed {len(collected_actions)} action(s)",
                "textResponse": text_response
            }

        function_responses = []
        for part in candidate.content.parts:
            if not part.function_call:
                continue

            fc = part.function_call
            action_name = fc.name
            args = dict(fc.args) if fc.args else {}

            # Map Computer Use actions to desktop actions
            action = {
                "action": action_name,
                **args,
                "screenWidth": screen_width,
                "screenHeight": screen_height
            }
            collected_actions.append(action)

            # In a real loop, we'd execute and take a new screenshot here
            # For Wishcraft, we collect all actions and execute on the client
            function_responses.append(
                Part(function_response=types.FunctionResponse(
                    name=action_name,
                    response={"status": "executed", "message": f"Action {action_name} executed successfully"}
                ))
            )

        contents.append(Content(role="user", parts=function_responses))

    return {
        "actions": collected_actions,
        "summary": f"Completed {len(collected_actions)} action(s) (turn limit reached)"
    }


# Main: Read from stdin, run, write to stdout
def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON input: {str(e)}"}))
        sys.exit(1)

    goal = input_data.get("goal")
    screenshot = input_data.get("screenshot")
    screen_width = input_data.get("screen_width", 1440)
    screen_height = input_data.get("screen_height", 900)
    scale_factor = input_data.get("scale_factor", 1)
    api_key = input_data.get("api_key")

    if not goal:
        print(json.dumps({"error": "Missing 'goal' parameter"}))
        sys.exit(1)

    if not api_key:
        print(json.dumps({"error": "Missing 'api_key' parameter"}))
        sys.exit(1)

    if not screenshot:
        # No screenshot — return a default action to take one
        print(json.dumps({
            "actions": [{"action": "screenshot"}],
            "summary": "No screenshot provided. Please capture the screen first."
        }))
        sys.exit(0)

    result = run_computer_use(goal, screenshot, screen_width, screen_height, scale_factor, api_key)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
