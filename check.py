"""QA gate for a rendered video - "let it check itself, then look with your own eyes".
Usage: python check.py [out/showreel.mp4]
Checks: video+audio streams, duration, keyframe spacing (<= 1.1 s), black frames mid-video,
sudden brightness flashes. Writes out/contact-sheet.jpg (1 frame/second) to review by eye.
Exit code 0 = pass, 1 = fail.
"""
import json, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
video = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "out" / "showreel.mp4"
BLACK_YAVG, FLASH_DELTA, MAX_KEY_GAP = 20.0, 12.0, 1.1

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"command failed: {' '.join(cmd)}\n{r.stderr}")
    return r.stdout

for tool in ("ffmpeg", "ffprobe"):
    if shutil.which(tool) is None:
        sys.exit(f"{tool} not found on PATH")
if not video.exists():
    sys.exit(f"{video} not found - render it first")

problems = []
info = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
                       "-of", "json", str(video)]))
kinds = {s["codec_type"] for s in info["streams"]}
duration = float(info["format"]["duration"])
for k in ("video", "audio"):
    if k not in kinds:
        problems.append(f"missing {k} stream")

raw = run(["ffprobe", "-v", "error", "-select_streams", "v", "-skip_frame", "nokey",
           "-show_entries", "frame=pts_time", "-of", "csv=p=0", str(video)])
keys = [float(x) for x in raw.replace(",", " ").split()]
gaps = [b - a for a, b in zip(keys, keys[1:] + [duration])]
if gaps and max(gaps) > MAX_KEY_GAP:
    problems.append(f"keyframe gap {max(gaps):.2f}s > {MAX_KEY_GAP}s - re-encode with -g FPS")

stats = run(["ffmpeg", "-v", "error", "-i", str(video), "-vf",
             "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-", "-f", "null", "-"])
yavg = [float(line.split("=")[1]) for line in stats.splitlines() if "YAVG" in line]
edge = 20  # ignore intentional fade in/out
black = [i for i, v in enumerate(yavg) if v < BLACK_YAVG and edge < i < len(yavg) - edge]
flash = [i for i in range(1, len(yavg)) if abs(yavg[i] - yavg[i - 1]) > FLASH_DELTA]
if black:
    problems.append(f"black frames mid-video at {black[:10]}")
if flash:
    problems.append(f"brightness flashes at frames {flash[:10]}")

sheet = video.parent / "contact-sheet.jpg"
run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", "fps=1,scale=426:-1,tile=4x3",
     "-frames:v", "1", str(sheet)])

print(f"{video.name}: {duration:.2f}s, {len(yavg)} frames, {len(keys)} keyframes, streams={sorted(kinds)}")
print(f"contact sheet -> {sheet}  (open it and look before publishing)")
if problems:
    print("FAIL:\n  - " + "\n  - ".join(problems))
    sys.exit(1)
print("PASS")
