"""Video tools for PART 8. All ffmpeg calls go through imageio-ffmpeg, so no separate install is needed.

Everything works on a folder layout like this (PROJECT_ROOT = the agewec-mumbai folder):

    assets/cut1.mp4 ... cut8.mp4   clips you generated or shot yourself
    assets/SOURCES.txt             one line per clip: cut, how it was made, prompt, date
    build/                          intermediate files (created automatically)
    output.mp4                      the result
"""

import json
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS = PROJECT_ROOT / "assets"
BUILD = PROJECT_ROOT / "build"
W, H, FPS = 1280, 720, 25


def _run(args):
    r = subprocess.run([FFMPEG, "-y", "-loglevel", "error", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-2000:])


def probe_duration(path) -> float:
    """Length of a media file in seconds (read from ffmpeg's own output)."""
    r = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True)
    for line in r.stderr.splitlines():
        if "Duration:" in line:
            hms = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = hms.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    raise RuntimeError(f"Could not read duration of {path}")


def probe_size(path):
    """(width, height) of a video, read from ffmpeg's own output."""
    import re
    r = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", r.stderr)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def normalize_clip(src, dst, seconds: float, start: float = 0.0):
    """Make any clip 1280x720, 25 fps, H.264, silent, and exactly `seconds` long.

    Clips from different services differ in size, frame rate and codec. Everything is
    brought to one format first, otherwise concatenation fails or stutters.
    """
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
          f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps={FPS},setsar=1")
    _run(["-ss", str(start), "-i", str(src), "-t", str(seconds), "-vf", vf, "-an",
          "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(dst)])


def concat_with_crossfade(clips, dst, fade: float = 0.6):
    """Join normalized clips in order with a short crossfade between each pair."""
    clips = [str(c) for c in clips]
    if len(clips) == 1:
        _run(["-i", clips[0], "-c", "copy", str(dst)])
        return
    durs = [probe_duration(c) for c in clips]
    inputs = []
    for c in clips:
        inputs += ["-i", c]
    fc, prev, offset = "", "[0:v]", 0.0
    for i in range(1, len(clips)):
        offset += durs[i - 1] - fade
        out = "[v]" if i == len(clips) - 1 else f"[x{i}]"
        fc += f"{prev}[{i}:v]xfade=transition=fade:duration={fade}:offset={offset:.3f}{out};"
        prev = out
    _run([*inputs, "-filter_complex", fc.rstrip(";"), "-map", "[v]",
          "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(dst)])


def _subtitle_png(text: str, path: Path):
    """Draw one subtitle as a transparent PNG (PIL's bundled font, so it works everywhere)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=40)
    box = d.textbbox((0, 0), text, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    x, y = (W - tw) // 2, H - 110
    d.rectangle([x - 24, y - 14, x + tw + 24, y + th + 18], fill=(0, 0, 0, 150))
    d.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    img.save(path)


def burn_subtitles(src, dst, subtitles):
    """subtitles: list of {"start": s, "end": s, "text": "..."} -> overlaid on the video."""
    BUILD.mkdir(exist_ok=True)
    inputs = ["-i", str(src)]
    fc, prev = "", "[0:v]"
    for i, sub in enumerate(subtitles):
        png = BUILD / f"sub{i}.png"
        _subtitle_png(sub["text"], png)
        inputs += ["-i", str(png)]
        out = "[v]" if i == len(subtitles) - 1 else f"[s{i}]"
        fc += f"{prev}[{i + 1}:v]overlay=0:0:enable='between(t,{sub['start']},{sub['end']})'{out};"
        prev = out
    if not subtitles:
        _run(["-i", str(src), "-c", "copy", str(dst)])
        return
    _run([*inputs, "-filter_complex", fc.rstrip(";"), "-map", "[v]",
          "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(dst)])


def narrate(text: str, dst, voice: str = "en-IN-NeerjaNeural"):
    """Text -> mp3 with edge-tts (free, needs internet). Returns the audio length in seconds."""
    subprocess.run([sys.executable, "-m", "edge_tts", "--voice", voice, "--text", text,
                    "--write-media", str(dst)], check=True, capture_output=True)
    return probe_duration(dst)


def mux_audio(video, audio, dst):
    """Put the narration under the video. The video length wins; audio is cut if longer."""
    # Pad the audio with silence to the video length (short narration) or trim it (long narration).
    dur = probe_duration(video)
    _run(["-i", str(video), "-i", str(audio), "-filter_complex", f"[1:a]apad,atrim=end={dur:.3f}[a]",
          "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", str(dst)])


def read_sources():
    """assets/SOURCES.txt -> {cut_number: line}. Lines look like:  cut3 | Kling (free) | prompt... | 2026-09-10"""
    path = ASSETS / "SOURCES.txt"
    out = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3 and parts[0].lower().startswith("cut") and parts[0][3:].isdigit():
            out[int(parts[0][3:])] = line.strip()
    return out


def frame_at(video, seconds: float, dst):
    """One still frame, for a quick look without opening the video."""
    _run(["-ss", str(seconds), "-i", str(video), "-frames:v", "1", str(dst)])
