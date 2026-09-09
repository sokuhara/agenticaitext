"""6.1 — The smallest possible agent, in plain Python.

Run from the vibe-chat folder:   python agent/agent_plain.py

The loop below is the whole idea of an agent:
  1. we give the model a list of tools (SCHEMA)
  2. the model answers with tool calls (or a final message)
  3. WE run the tool and send the result back
  4. repeat, with a hard limit on the number of steps
"""

import json

import requests

from config import BASE_URL, MODEL, HEADERS, API_KEY
from tools import TOOLS

SCHEMA = [
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Read a file inside the project. Use it to look at app.py and tests/test_app.py.",
        "parameters": {"type": "object",
                       "properties": {"path": {"type": "string"}},
                       "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "write_file",
        "description": "Overwrite a .py file inside the project with new content.",
        "parameters": {"type": "object",
                       "properties": {"path": {"type": "string"},
                                      "content": {"type": "string"}},
                       "required": ["path", "content"]}}},
    {"type": "function", "function": {
        "name": "run_tests",
        "description": "Run pytest and return the result.",
        "parameters": {"type": "object", "properties": {}}}},
]

SYSTEM = (
    "You are a careful coding agent working inside a small Flask project. "
    "Use the tools to read files, edit files and run the tests. "
    "Fix the failing test by fixing the application code, not by changing the test. "
    "When the tests pass, reply with a short summary of what you changed."
)


def chat(messages):
    """One call to the OpenAI-compatible endpoint of the shared server."""
    r = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={**HEADERS, "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": MODEL, "messages": messages, "tools": SCHEMA, "temperature": 0},
        timeout=300,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]


def agent(goal: str, max_steps: int = 12) -> str:
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": goal}]
    for step in range(max_steps):
        msg = chat(messages)
        messages.append(msg)
        calls = msg.get("tool_calls") or []
        if not calls:
            return msg.get("content") or "(no content)"       # no tool call: the model is done
        for call in calls:
            name = call["function"]["name"]
            args = json.loads(call["function"].get("arguments") or "{}")
            shown = {k: (v[:60] + "…" if isinstance(v, str) and len(v) > 60 else v) for k, v in args.items()}
            print(f"[{step}] {name}({shown})")
            try:
                result = TOOLS[name](**args)
            except Exception as e:                              # a failure is also a result
                result = f"ERROR: {e}"
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": str(result)})
    return "Stopped: reached the maximum number of steps."


if __name__ == "__main__":
    print(agent("Run the tests, find out why one of them fails, and fix it."))
