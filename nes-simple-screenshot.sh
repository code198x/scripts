#!/bin/bash
# Simple NES screenshot - just use FCEUX interactively

ROM_FILE="$1"
OUTPUT_FILE="$2"
FRAMES="${3:-300}"

if [ -z "$ROM_FILE" ] || [ -z "$OUTPUT_FILE" ]; then
    echo "Usage: $0 <rom_file> <output_file> [frames_to_wait]"
    exit 1
fi

# Calculate wait time (frames / 60 fps = seconds)
WAIT_TIME=$(awk "BEGIN {print $FRAMES / 60}")

echo "Launching FCEUX for $(basename "$ROM_FILE")..."
echo "Will wait ${WAIT_TIME}s then take screenshot..."

# Clear old snaps
rm -f ~/.fceux/snaps/*.png 2>/dev/null

# Launch FCEUX in background
open -a FCEUX "$ROM_FILE"

# Wait for launch
sleep 2

# Wait for frames
sleep "$WAIT_TIME"

# Try to send F12 via AppleScript
osascript -e 'tell application "System Events" to keystroke "2" using {function down, shift down}' 2>/dev/null || \
osascript -e 'tell application "System Events" to key code 111 using {function down}' 2>/dev/null

# Wait for save
sleep 1

# Close FCEUX
osascript -e 'tell application "FCEUX" to quit' 2>/dev/null

sleep 1

# Move screenshot
LATEST=$(ls -t ~/.fceux/snaps/*.png 2>/dev/null | head -1)

if [ -n "$LATEST" ]; then
    mkdir -p "$(dirname "$OUTPUT_FILE")"
    mv "$LATEST" "$OUTPUT_FILE"
    
    if [ -f "$OUTPUT_FILE" ]; then
        SIZE=$(stat -f%z "$OUTPUT_FILE")
        echo "✓ $OUTPUT_FILE ($SIZE bytes)"
        exit 0
    fi
fi

echo "✗ Failed"
exit 1
