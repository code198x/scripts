-- FCEUX Screenshot Capture Script
-- Runs ROM for specified frames and captures screenshot

-- Configuration
local FRAMES_TO_RUN = 300  -- 5 seconds at 60 fps

-- Frame counter
local frame_count = 0
local screenshot_taken = false

-- Main loop function
local function captureFrame()
    frame_count = frame_count + 1

    if frame_count >= FRAMES_TO_RUN and not screenshot_taken then
        -- Take screenshot using default FCEUX snapshot functionality
        gui.savescreenshot()
        screenshot_taken = true

        -- Give it a moment to save, then exit
        emu.frameadvance()
        emu.frameadvance()
        emu.exit()
    end
end

-- Register frame advance callback
emu.registerafter(captureFrame)
