#!/usr/bin/env bash
# One-time setup (also re-run to update yt-dlp when YouTube breaks things).
set -e
cd "$(dirname "$0")"
command -v ffmpeg >/dev/null || echo "WARNING: ffmpeg not found - install it: sudo apt install ffmpeg"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q --upgrade -r requirements.txt
echo "Ready. yt-dlp $(.venv/bin/yt-dlp --version)"
