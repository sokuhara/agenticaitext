"""Connection settings for the shared lab servers (same values as your Cline settings in PART 3).

Fill in the four values below, or set the environment variables of the same name.
Do NOT commit or share the two CF_ACCESS_* values.
"""

import os

# Base URL of YOUR server (see the table in PART 3, 3.1.3). Ends with /v1.
BASE_URL = os.environ.get("VIBE_BASE_URL", "https://pc11.okuharalab.com/v1")

# Model ID that matches YOUR server (pc11 -> qwen38_1, pc21 -> qwen38_2, ...).
MODEL = os.environ.get("VIBE_MODEL", "qwen38_1:latest")

# Cloudflare Access service token (handed out in class).
CF_ACCESS_CLIENT_ID = os.environ.get("CF_ACCESS_CLIENT_ID", "PASTE_CLIENT_ID_HERE")
CF_ACCESS_CLIENT_SECRET = os.environ.get("CF_ACCESS_CLIENT_SECRET", "PASTE_CLIENT_SECRET_HERE")

# Ollama ignores the API key, but the OpenAI-compatible clients require one.
API_KEY = "ollama"

HEADERS = {
    "CF-Access-Client-Id": CF_ACCESS_CLIENT_ID,
    "CF-Access-Client-Secret": CF_ACCESS_CLIENT_SECRET,
}
