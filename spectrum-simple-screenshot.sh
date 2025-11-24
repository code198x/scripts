#!/bin/bash
# Simple Spectrum screenshot using open -a Fuse

TAP_FILE="$1"
OUTPUT_FILE="$2"
WAIT_SECONDS="${3:-3}"

if [ -z "$TAP_FILE" ] || [ -z "$OUTPUT_FILE" ]; then
    echo "Usage: $0 <tap_file> <output_file> [wait_seconds]"
    exit 1
fi

if [ ! -f "$TAP_FILE" ]; then
    echo "Error: TAP file not found: $TAP_FILE"
    exit 1
fi

echo "Launching FUSE with $(basename "$TAP_FILE")..."

# Launch FUSE with TAP file
open -a "Fuse" "$TAP_FILE"

# Wait for FUSE to launch and autoload
sleep 3

echo "Typing RANDOMIZE USR 32768..."
# Type the command to execute the code
osascript <<EOF
tell application "System Events"
    keystroke "RANDOMIZE USR 32768"
    delay 0.2
    key code 36
end tell
EOF

# Wait for code execution
sleep "$WAIT_SECONDS"

echo "Attempting screenshot capture..."
# Try to trigger screenshot (F2 or Shift-F12 in FUSE)
osascript <<EOF
tell application "System Events"
    key code 120
end tell
EOF

sleep 1

# Look for screenshot file
# FUSE may save to different locations
LOCATIONS=(
    "$(pwd)/fuse*.png"
    "$(pwd)/screenshot*.png"
    "$HOME/fuse*.png"
    "$HOME/screenshot*.png"
    "$HOME/Desktop/fuse*.png"
)

FOUND=""
for pattern in "${LOCATIONS[@]}"; do
    LATEST=$(ls -t $pattern 2>/dev/null | head -1)
    if [ -n "$LATEST" ]; then
        FOUND="$LATEST"
        break
    fi
done

if [ -n "$FOUND" ]; then
    mkdir -p "$(dirname "$OUTPUT_FILE")"
    mv "$FOUND" "$OUTPUT_FILE"

    if [ -f "$OUTPUT_FILE" ]; then
        SIZE=$(stat -f%z "$OUTPUT_FILE")
        echo "✓ Screenshot saved: $OUTPUT_FILE ($SIZE bytes)"

        # Close FUSE
        osascript -e 'tell application "Fuse" to quit' 2>/dev/null
        exit 0
    fi
fi

echo ""
echo "⚠️  Automated screenshot capture may have failed."
echo "    FUSE is still running - please capture manually:"
echo ""
echo "    1. Switch to FUSE window"
echo "    2. Program should be running"
echo "    3. File → Save Screenshot"
echo "    4. Save to: $OUTPUT_FILE"
echo ""
echo "    Or press Q to quit this script and close FUSE"

read -n 1 -p "Press any key when done (or Q to quit)..." key
echo

if [ "$key" = "q" ] || [ "$key" = "Q" ]; then
    osascript -e 'tell application "Fuse" to quit' 2>/dev/null
    exit 1
fi

# Check if user saved manually
if [ -f "$OUTPUT_FILE" ]; then
    SIZE=$(stat -f%z "$OUTPUT_FILE")
    echo "✓ Screenshot found: $OUTPUT_FILE ($SIZE bytes)"
    osascript -e 'tell application "Fuse" to quit' 2>/dev/null
    exit 0
else
    echo "✗ Screenshot not found at expected location"
    exit 1
fi
