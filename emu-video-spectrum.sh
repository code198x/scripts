#!/usr/bin/env bash
# Capture a ZX Spectrum video using the Emu198x emulator.
#
# Loads a snapshot or tape file, advances `--wait` frames to reach a
# steady state, then records `--frames` worth of video to an MP4
# file. ffmpeg must be on PATH.
#
# Usage: ./emu-video-spectrum.sh <input.sna|.tap|.tzx|.z80> <output.mp4> [--wait N] [--frames N] [--model MODEL]

set -euo pipefail

EMU="${EMU_SPECTRUM:-/Users/stevehill/Projects/Emu198x/target/release/emu198x-script-spectrum}"
INPUT="${1:?Usage: $0 <input> <output.mp4> [--wait N] [--frames N] [--model MODEL]}"
OUTPUT="${2:?Usage: $0 <input> <output.mp4> [--wait N] [--frames N] [--model MODEL]}"
WAIT=250
FRAMES=500
MODEL=48k

shift 2
while [[ $# -gt 0 ]]; do
  case "$1" in
    --wait) WAIT="$2"; shift 2 ;;
    --frames) FRAMES="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

mkdir -p "$(dirname "$OUTPUT")"

# The script bin's fast path runs `--frames` frames AFTER the load,
# then captures over the same number for video. So pass --frames =
# (wait + record) and rely on the recording to start at frame WAIT.
# In practice, this records `WAIT + FRAMES` total frames, with the
# first WAIT being the steady-state warmup. For the simple case of
# "wait then record", use the JSON script path instead.

cat > /tmp/emu-video-spectrum-$$.json <<EOF
[
  {"method": "load", "params": {"path": "$INPUT"}},
  {"method": "run_frames", "params": {"count": $WAIT}},
  {"method": "record_video", "params": {"save_path": "$OUTPUT", "frames": $FRAMES}}
]
EOF

"$EMU" --model "$MODEL" --script /tmp/emu-video-spectrum-$$.json
rm -f /tmp/emu-video-spectrum-$$.json

echo "Video saved: $OUTPUT"
