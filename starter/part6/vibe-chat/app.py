"""Vibe Chat — Flask version.

Starter file for PART 6: the app as it stands at the end of PART 5.
Messages live only in a Python list (no database, no persistence).
"""

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

MAX_MESSAGE_LENGTH = 200
STATUSES = ("Present", "Away", "Focus")

# All messages live only in this list. Each item: {"id": int, "name": str, "status": str, "message": str}
messages = []
_next_id = 1


def _render(error=None, status_code=200):
    return render_template("index.html", messages=messages, error=error), status_code


@app.route("/", methods=["GET"])
def index():
    return _render()


@app.route("/", methods=["POST"])
def post_message():
    global _next_id

    name = request.form.get("name", "").strip()
    status = request.form.get("status", "Present")
    message = request.form.get("message", "").strip()

    if name == "":
        return _render(error="User name cannot be empty.", status_code=400)

    if message == "":
        return _render(error="Message cannot be empty.", status_code=400)

    if len(message) > MAX_MESSAGE_LENGTH:
        return _render(
            error=f"Message is too long ({len(message)} characters). Maximum is {MAX_MESSAGE_LENGTH}.",
            status_code=400,
        )

    if status not in STATUSES:
        status = "Present"

    messages.append({"id": _next_id, "name": name, "status": status, "message": message})
    _next_id += 1
    return redirect(url_for("index"))


@app.route("/delete/<int:message_id>", methods=["POST"])
def delete_message(message_id):
    # Delete only the message with this id. Unknown ids are ignored.
    for i, entry in enumerate(messages):
        if entry["id"] == message_id:
            del messages[i]
            break
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
