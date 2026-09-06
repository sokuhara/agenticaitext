"""PART 8 の動画パイプラインを、Colabの外で確かめる。

    python3 09_video_pipeline.py

必要なもの: ffmpeg, ffprobe, Pillow
このスクリプトは、この環境で実際に動作確認済みです。

確認すること:
  - スライドが作れるか（日本語フォントの有無）
  - 字幕が焼き込めるか（libassの有無）
  - ffprobe で尺と音声の有無が取れるか
  - 初期設定で 70 秒になり、検査に落ちるか
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
WORK = Path(tempfile.mkdtemp(prefix="video-check-"))
(WORK / "shots").mkdir()

FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "C:/Windows/Fonts/meiryo.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
FONT_PATH = next((p for p in FONT_CANDIDATES if Path(p).exists()), None)

SECONDS_PER_POINT = 23.5   # 3点で70.5秒。わざと落とす。
POINTS = ["要点1をここに書く", "Point two in English", "要点3をここに書く"]


def make_slide(i: int, text: str) -> str:
    img = Image.new("RGB", (W, H), (32, 34, 31))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, 54) if FONT_PATH else ImageFont.load_default()
    lines = textwrap.wrap(text, width=18) or [""]
    y = H // 2 - len(lines) * 36
    for line in lines:
        w = draw.textlength(line, font=font)
        draw.text(((W - w) / 2, y), line, font=font, fill=(247, 245, 238))
        y += 72
    p = WORK / "shots" / f"shot_{i:02d}.png"
    img.save(p)
    return str(p)


def make_subtitles(shots: list[dict]) -> str:
    def ts(sec: float) -> str:
        h, rem = divmod(int(sec), 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d},{int((sec - int(sec)) * 1000):03d}"

    out, t = [], 0.0
    for i, shot in enumerate(shots, start=1):
        end = t + shot["seconds"]
        out.append(f"{i}\n{ts(t)} --> {ts(end)}\n{shot['text']}\n")
        t = end
    p = WORK / "subtitles.srt"
    p.write_text("\n".join(out), encoding="utf-8")
    return str(p)


def assemble(shots: list[dict], sub: str) -> tuple[str, bool]:
    clips = []
    for i, shot in enumerate(shots):
        img = make_slide(i, shot["text"])
        clip = WORK / "shots" / f"clip_{i:02d}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", img,
                        "-t", str(shot["seconds"]), "-r", "30",
                        "-vf", f"scale={W}:{H}", "-pix_fmt", "yuv420p", str(clip)],
                       capture_output=True, check=True)
        clips.append(clip)

    lst = WORK / "shots.txt"
    lst.write_text("".join(f"file '{c}'\n" for c in clips), encoding="utf-8")
    joined = WORK / "joined.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c", "copy", str(joined)],
                   capture_output=True, check=True)

    out = WORK / "output.mp4"
    burned = True
    try:
        subprocess.run(["ffmpeg", "-y", "-i", str(joined), "-vf", f"subtitles={sub}",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)],
                       capture_output=True, check=True)
    except subprocess.CalledProcessError:
        burned = False
        subprocess.run(["ffmpeg", "-y", "-i", str(joined),
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)],
                       capture_output=True, check=True)
    return str(out), burned


def inspect(path: str) -> dict:
    r = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json",
                        "-show_format", "-show_streams", path],
                       capture_output=True, text=True, check=True)
    info = json.loads(r.stdout)
    streams = info.get("streams", [])
    return {"duration": float(info["format"]["duration"]),
            "has_audio": any(s["codec_type"] == "audio" for s in streams),
            "width": next((s.get("width") for s in streams
                           if s["codec_type"] == "video"), None)}


def main() -> int:
    for cmd in ("ffmpeg", "ffprobe"):
        if not shutil.which(cmd):
            print(f"{cmd} がありません。  apt-get install ffmpeg")
            return 1
    print("フォント:", FONT_PATH or "見つからず（英字のみになります）")
    if FONT_PATH and FONT_PATH.endswith("DejaVuSans.ttf"):
        print("  !! 日本語フォントが見つかりません。日本語は豆腐になります。")
        print("     apt-get install fonts-noto-cjk")

    shots = [{"text": p, "seconds": SECONDS_PER_POINT} for p in POINTS]
    sub = make_subtitles(shots)
    print("\n組み立て中...")
    out, burned = assemble(shots, sub)
    print("  字幕の焼き込み:", "OK" if burned else "失敗（スライドの文字だけ）")

    info = inspect(out)
    print("\n--- ffprobe ---")
    print(f"  尺       : {info['duration']:.1f} 秒")
    print(f"  解像度   : {info['width']}")
    print(f"  音声     : {'あり' if info['has_audio'] else 'なし'}")

    ok_range = 55 <= info["duration"] <= 65
    print("\n--- 検査（55〜65秒） ---")
    print("  duration_ok:", ok_range)
    print("\n=>", "仕込みどおり落ちました。学生はここから修正ループに入ります。"
          if not ok_range else "!! 落ちませんでした。SECONDS_PER_POINT を確認してください。")
    print("\n出力:", out)
    return 0 if not ok_range else 1


if __name__ == "__main__":
    raise SystemExit(main())
