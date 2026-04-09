#!/usr/bin/env bash
# Capture a ZX Spectrum screenshot using the Emu198x emulator.
#
# Loads a snapshot or tape file, advances N frames, then writes a
# PNG screenshot to the output path. Uses the script bin's fast
# path for one-line operation.
#
# Usage: ./emu-screenshot-spectrum.sh <input.sna|.tap|.tzx|.z80> <output.png> [--frames N] [--model MODEL]

set -euo pipefail

EMU="${EMU_SPECTRUM:-/Users/stevehill/Projects/Emu198x/target/release/emu198x-script-spectrum}"
INPUT="${1:?Usage: $0 <input> <output.png> [--frames N] [--model MODEL]}"
OUTPUT="${2:?Usage: $0 <input> <output.png> [--frames N] [--model MODEL]}"
FRAMES=250
MODEL=48k

shift 2
while [[ $# -gt 0 ]]; do
  case "$1" in
    --frames) FRAMES="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

mkdir -p "$(dirname "$OUTPUT")"

"$EMU" "$INPUT" \
  --model "$MODEL" \
  --frames "$FRAMES" \
  --screenshot "$OUTPUT"

echo "Screenshot saved: $OUTPUT"
