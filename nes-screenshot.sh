#!/bin/bash
# NES Screenshot Capture using FCEUX + Lua (working version)
# This version uses a simpler approach with frame counting

ROM_FILE="$1"
OUTPUT_FILE="$2"
FRAMES=${3:-300}

if [ -z "$ROM_FILE" ] || [ -z "$OUTPUT_FILE" ]; then
    echo "Usage: $0 <rom_file> <output_file> [frames_to_run]"
    exit 1
fi

# Create temp Lua script
LUA_SCRIPT="/tmp/fceux_capture_$$.lua"
cat > "$LUA_SCRIPT" << LUAEOF
local target_frame = $FRAMES
local screenshot_taken = false

emu.registerafter(function()
    local current_frame = emu.framecount()
    
    if current_frame >= target_frame and not screenshot_taken then
        gui.savescreenshot()
        screenshot_taken = true
    end
    
    if current_frame >= target_frame + 10 then
        os.exit(0)
    end
end)
LUAEOF

# Create output directory
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Clear old snaps
rm -f ~/.fceux/snaps/*.png 2>/dev/null

# Run FCEUX with timeout
( fceux --nogui --loadlua "$LUA_SCRIPT" "$ROM_FILE" > /dev/null 2>&1 ) &
PID=$!

# Wait with timeout
for i in {1..15}; do
    sleep 1
    if ! kill -0 $PID 2>/dev/null; then
        break
    fi
done

# Kill if still running
kill -9 $PID 2>/dev/null || true

# Clean up lua script
rm -f "$LUA_SCRIPT"

# Find screenshot
SNAP=$(ls -t ~/.fceux/snaps/*.png 2>/dev/null | head -1)

if [ -n "$SNAP" ] && [ -f "$SNAP" ]; then
    cp "$SNAP" "$OUTPUT_FILE"
    echo "✓ Screenshot saved: $OUTPUT_FILE"
    exit 0
else
    echo "✗ Failed to capture screenshot"
    exit 1
fi
