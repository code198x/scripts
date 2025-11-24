#!/bin/bash
# NES Screenshot using FCEUX GUI + screencapture

ROM_FILE="$1"
OUTPUT_FILE="$2"
WAIT_SECONDS=${3:-5}

if [ -z "$ROM_FILE" ] || [ -z "$OUTPUT_FILE" ]; then
    echo "Usage: $0 <rom_file> <output_file> [wait_seconds]"
    exit 1
fi

# Create output directory
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Launch FCEUX in GUI mode
fceux "$ROM_FILE" > /dev/null 2>&1 &
PID=$!

# Wait for window to appear
sleep 2

# Wait for ROM to run
sleep $WAIT_SECONDS

# Capture the FCEUX window using screencapture
# Get the window ID
WINDOW_ID=$(osascript -e 'tell application "System Events" to get id of first window of (first process whose name contains "fceux")' 2>/dev/null)

if [ -n "$WINDOW_ID" ]; then
    # Capture window
    screencapture -l"$WINDOW_ID" "$OUTPUT_FILE" 2>/dev/null
    
    # Kill FCEUX
    kill -9 $PID 2>/dev/null || true
    
    # Check if file was created
    if [ -f "$OUTPUT_FILE" ] && [ $(stat -f%z "$OUTPUT_FILE") -gt 1000 ]; then
        echo "✓ Screenshot saved: $OUTPUT_FILE"
        exit 0
    fi
fi

# Fallback: kill and report failure
kill -9 $PID 2>/dev/null || true
echo "✗ Failed to capture screenshot"
exit 1
