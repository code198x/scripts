#!/bin/bash
# Automated NES screenshot capture
# Uses FCEUX with AppleScript automation

ROM_FILE="$1"
OUTPUT_FILE="$2"
WAIT_SECONDS="${3:-5}"

if [ -z "$ROM_FILE" ] || [ -z "$OUTPUT_FILE" ]; then
    echo "Usage: $0 <rom_file> <output_file> [wait_seconds]"
    exit 1
fi

# Full paths
ROM_FILE_ABS=$(cd "$(dirname "$ROM_FILE")" && pwd)/$(basename "$ROM_FILE")
OUTPUT_FILE_ABS=$(cd "$(dirname "$OUTPUT_FILE")" && pwd)/$(basename "$OUTPUT_FILE") 2>/dev/null || OUTPUT_FILE

# Clear old screenshots
rm -f ~/.fceux/snaps/*.png 2>/dev/null

# Create output directory
mkdir -p "$(dirname "$OUTPUT_FILE_ABS")"

# Launch FCEUX  and automate via AppleScript
osascript <<APPLESCRIPT
-- Launch FCEUX with ROM
do shell script "open -a FCEUX '$ROM_FILE_ABS'"

-- Wait for ROM to load
delay 2

-- Wait for specified time
delay $WAIT_SECONDS

-- Activate FCEUX
tell application "FCEUX" to activate

-- Send F12 (screenshot key in FCEUX)
tell application "System Events"
    keystroke "2" using {function down, shift down}
end tell

-- Wait for screenshot to save
delay 0.5

-- Quit FCEUX
tell application "FCEUX" to quit

delay 1
APPLESCRIPT

# Find the most recent screenshot
LATEST_SNAP=$(ls -t ~/.fceux/snaps/*.png 2>/dev/null | head -1)

if [ -n "$LATEST_SNAP" ] && [ -f "$LATEST_SNAP" ]; then
    mv "$LATEST_SNAP" "$OUTPUT_FILE_ABS"
    
    if [ -f "$OUTPUT_FILE_ABS" ]; then
        SIZE=$(stat -f%z "$OUTPUT_FILE_ABS")
        echo "✓ Screenshot saved: $OUTPUT_FILE_ABS ($SIZE bytes)"
        exit 0
    fi
fi

echo "✗ Failed to capture screenshot"
exit 1
