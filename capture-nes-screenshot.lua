-- NES Screenshot Capture Script for FCEUX
--
-- Loads a ROM, runs for specified frames, captures screenshot, and exits
--
-- Usage:
--   fceux --loadlua capture-nes-screenshot.lua game.nes
--
-- Configuration:
--   FRAMES_TO_RUN: Number of frames to advance before screenshot
--   OUTPUT_NAME: Optional custom filename (defaults to ROM name)

-- Configuration
local FRAMES_TO_RUN = 300  -- ~5 seconds at 60 FPS
local OUTPUT_NAME = nil    -- nil = use ROM name, or set to "custom-name"

-- Get ROM name for default output
local rom_name = emu.romname()
print("NES Screenshot Capture Script")
print("ROM: " .. rom_name)
print("Will capture screenshot after " .. FRAMES_TO_RUN .. " frames")

-- Advance frames
for i = 1, FRAMES_TO_RUN do
    emu.frameadvance()

    -- Show progress every 60 frames (1 second)
    if i % 60 == 0 then
        print("Frame " .. i .. " / " .. FRAMES_TO_RUN)
    end
end

-- Capture screenshot
if OUTPUT_NAME then
    gui.savescreenshotas(OUTPUT_NAME)
    print("Screenshot saved: " .. OUTPUT_NAME .. ".png")
else
    gui.savescreenshot()
    print("Screenshot saved to FCEUX snaps directory")
end

-- Exit emulator
print("Capture complete, exiting...")
emu.exit()
