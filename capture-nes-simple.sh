#!/usr/bin/env zsh
# Simple NES Screenshot Capture
# Usage: ./capture-nes-simple.sh rom.nes [frames]

set -e

ROM="$1"
FRAMES="${2:-300}"

if [[ -z "$ROM" ]]; then
    echo "Usage: $0 <rom-file> [frames]"
    exit 1
fi

if [[ ! -f "$ROM" ]]; then
    echo "Error: ROM not found: $ROM"
    exit 1
fi

# Create temp Lua script
LUA=$(mktemp /tmp/fceux-XXXXXX.lua)

cat > "$LUA" << 'EOLUA'
local frames = tonumber(arg[1]) or 300
print("Capturing screenshot after " .. frames .. " frames")

for i = 1, frames do
    emu.frameadvance()
    if i % 60 == 0 then
        print("Frame " .. i)
    end
end

gui.savescreenshot()
print("Screenshot saved")
emu.exit()
EOLUA

echo "Running FCEUX..."
fceux --loadlua "$LUA" "$ROM" -- "$FRAMES"

rm "$LUA"
echo "Done! Check ~/.fceux/snaps/"
