"""6.4 — Break app.py again on purpose (disable the empty-name check), like 5.5.

Run from the vibe-chat folder:   python agent/break_app.py

After the agent has fixed the check it may have written it in its own way, so this script
looks for the line that renders "User name cannot be empty." and comments out that line
together with the `if` line just above it.
"""

from pathlib import Path

APP = Path(__file__).resolve().parent.parent / "app.py"
lines = APP.read_text(encoding="utf-8").splitlines(keepends=True)

hit = next((i for i, l in enumerate(lines) if "User name cannot be empty" in l and not l.lstrip().startswith("#")), None)
if hit is None:
    print("No active empty-name check found in app.py (already disabled?). Nothing changed.")
else:
    start = hit
    while start > 0 and not lines[start].lstrip().startswith("if "):
        start -= 1
    for i in range(start, hit + 1):
        lines[i] = "# " + lines[i]
    APP.write_text("".join(lines), encoding="utf-8")
    print(f"Commented out lines {start + 1}-{hit + 1} of app.py (the empty-name check). Now run: pytest")
