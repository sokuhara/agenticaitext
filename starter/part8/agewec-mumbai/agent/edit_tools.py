"""Tools the editing agent may call. Each one is small, deterministic, and logs what it did.

The agent decides WHICH of these to call, in what order, with what values.
The tools decide nothing; they render.
"""

import base64
import json
from pathlib import Path

from langchain_core.tools import tool
from PIL import Image

import video_tools as vt

LOG = []          # every tool call, in order. Shown to the human at review and saved for the report.
LAST_SUBTITLES = []   # the subtitle texts of the last add_subtitles call (the check reads these)
_timeline = []    # normalized clips, in the order the agent added them


def _log(entry):
    LOG.append(entry)
    print("  [tool]", entry)


@tool
def list_assets() -> str:
    """List the clips in assets/ with their length in seconds, width and height, and whether SOURCES.txt has a line for them."""
    sources = vt.read_sources()
    rows = []
    for p in sorted(vt.ASSETS.glob("cut*.mp4")):
        n = int(p.stem[3:])
        w, h = vt.probe_size(p)
        rows.append({"cut": n, "file": p.name, "seconds": round(vt.probe_duration(p), 1),
                     "width": w, "height": h, "has_source": n in sources})
    _log(f"list_assets -> {len(rows)} clips")
    return json.dumps(rows)


@tool
def contact_sheet() -> str:
    """Make one image with a frame from each clip (first, middle, last) so you can see what each cut shows. Returns the image path."""
    paths = sorted(vt.ASSETS.glob("cut*.mp4"))
    vt.BUILD.mkdir(exist_ok=True)
    tiles = []
    for p in paths:
        d = vt.probe_duration(p)
        for k, t in enumerate((0.2, d / 2, max(0.2, d - 0.3))):
            out = vt.BUILD / f"sheet_{p.stem}_{k}.png"
            vt.frame_at(p, t, out)
            tiles.append(Image.open(out).resize((320, 180)))
    cols = 3
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (320 * cols, 180 * rows), "black")
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % cols) * 320, (i // cols) * 180))
    out = vt.BUILD / "contact_sheet.png"
    sheet.save(out)
    _log("contact_sheet -> build/contact_sheet.png")
    return str(out)


@tool
def add_to_timeline(cut: int, seconds: float, start: float = 0.0) -> str:
    """Append a clip to the timeline: cut number, how many seconds to use, and where in the clip to start (seconds). Clips are normalized to 1280x720 here."""
    src = vt.ASSETS / f"cut{cut}.mp4"
    if not src.exists():
        return f"ERROR: {src.name} does not exist"
    dst = vt.BUILD / f"t{len(_timeline) + 1}_cut{cut}.mp4"
    vt.normalize_clip(src, dst, seconds, start=start)
    _timeline.append({"cut": cut, "seconds": seconds, "start": start, "file": str(dst)})
    _log(f"add_to_timeline(cut={cut}, seconds={seconds}, start={start})")
    return f"timeline now has {len(_timeline)} clips, total {sum(c['seconds'] for c in _timeline):.1f}s"


@tool
def clear_timeline() -> str:
    """Empty the timeline to start the order again."""
    _timeline.clear()
    _log("clear_timeline")
    return "timeline cleared"


@tool
def join_timeline(fade: float = 0.6) -> str:
    """Join the timeline clips in order with a crossfade of `fade` seconds between each pair. Writes build/joined.mp4 and returns its length."""
    if not _timeline:
        return "ERROR: timeline is empty"
    vt.concat_with_crossfade([c["file"] for c in _timeline], vt.BUILD / "joined.mp4", fade=fade)
    d = vt.probe_duration(vt.BUILD / "joined.mp4")
    _log(f"join_timeline(fade={fade}) -> {d:.1f}s")
    return f"joined.mp4 is {d:.1f}s"


@tool
def add_subtitles(subtitles_json: str) -> str:
    """Burn subtitles onto build/joined.mp4. subtitles_json is a JSON list of {"start": seconds, "end": seconds, "text": "..."}. Writes build/subtitled.mp4."""
    subs = json.loads(subtitles_json)
    LAST_SUBTITLES[:] = [s["text"] for s in subs]
    vt.burn_subtitles(vt.BUILD / "joined.mp4", vt.BUILD / "subtitled.mp4", subs)
    _log(f"add_subtitles({len(subs)} lines)")
    return f"{len(subs)} subtitles burned"


@tool
def add_narration(text: str) -> str:
    """Turn the narration text into speech and put it under build/subtitled.mp4. Writes output.mp4 and returns the audio and video lengths."""
    audio_len = vt.narrate(text, vt.BUILD / "narration.mp3")
    vt.mux_audio(vt.BUILD / "subtitled.mp4", vt.BUILD / "narration.mp3", vt.PROJECT_ROOT / "output.mp4")
    video_len = vt.probe_duration(vt.PROJECT_ROOT / "output.mp4")
    _log(f"add_narration({len(text.split())} words) -> audio {audio_len:.1f}s, video {video_len:.1f}s")
    return f"output.mp4 written. audio {audio_len:.1f}s, video {video_len:.1f}s"


EDIT_TOOLS = [list_assets, contact_sheet, add_to_timeline, clear_timeline, join_timeline, add_subtitles, add_narration]


def image_message(path) -> dict:
    """An image as a message part for a vision-capable model."""
    data = base64.b64encode(Path(path).read_bytes()).decode()
    return {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{data}"}}
