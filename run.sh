#!/usr/bin/env bash
# Full pipeline: music -> preview frames -> render -> QA gate.
set -euo pipefail
cd "$(dirname "$0")"
python3 music.py
python3 render.py preview 2 5 10.8
python3 render.py video out/showreel.mp4 out/music.wav
python3 check.py out/showreel.mp4
