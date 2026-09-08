"""7.0.1 — Break app.py on purpose (comment out the empty-name check), like 5.5.

Run from the vibe-chat folder:   python agent/break_app.py
"""

from pathlib import Path

APP = Path(__file__).resolve().parent.parent / "app.py"
NEEDLE = [
    '    if name == "":\n',
    '        return _render(error="User name cannot be empty.", status_code=400)\n',
]

src = APP.read_text(encoding="utf-8")
block = "".join(NEEDLE)
if block not in src:
    print("The empty-name check was not found (already commented out?). Nothing changed.")
else:
    APP.write_text(src.replace(block, "".join("# " + line for line in NEEDLE)), encoding="utf-8")
    print("Commented out the empty-name check in app.py. Now run: pytest")
