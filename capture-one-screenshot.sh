#!/bin/bash
# Capture single NES screenshot using FCEUX

ROM_PATH="$1"
OUTPUT_PATH="$2"
FRAMES_TO_WAIT=${3:-300}

if [ -z "$ROM_PATH" ] || [ -z "$OUTPUT_PATH" ]; then
    echo "Usage: $0 <rom_path> <output_path> [frames_to_wait]"
    exit 1
fi

# Clean up any old screenshots
rm -f ~/.fceux/snaps/*.png 2>/dev/null

# Launch FCEUX in background with ROM
fceux "$ROM_PATH" > /dev/null 2>&1 &
FCEUX_PID=$!

# Wait for ROM to load and run
sleep 1

# Calculate wait time (frames / 60fps)
WAIT_TIME=$(echo "scale=2; $FRAMES_TO_WAIT / 60" | bc)
sleep $WAIT_TIME

# Take screenshot using F12 key (FCEUX default)
osascript -e 'tell application "System Events" to keystroke "2" using {function down, shift down}'

# Wait for screenshot to save
sleep 0.5

# Kill FCEUX
kill -9 $FCEUX_PID 2>/dev/null || true

# Find the most recent screenshot
LATEST_SNAP=$(ls -t ~/.fceux/snaps/*.png 2>/dev/null | head -1)

if [ -n "$LATEST_SNAP" ] && [ -f "$LATEST_SNAP" ]; then
    # Move to destination
    mkdir -p "$(dirname "$OUTPUT_PATH")"
    cp "$LATEST_SNAP" "$OUTPUT_PATH"
    echo "Screenshot saved to: $OUTPUT_PATH"
    exit 0
else
    echo "ERROR: No screenshot generated"
    exit 1
fi
