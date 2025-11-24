-- Simplified FCEUX Screenshot Capture
-- Takes screenshot after specified frames and saves

local frames_to_wait = 300
local frame_count = 0
local done = false

local function on_frame()
    if done then
        return
    end

    frame_count = frame_count + 1

    if frame_count >= frames_to_wait then
        -- Take the screenshot
        gui.savescreenshot()
        done = true
        -- Force exit - may not work, that's OK
        os.exit(0)
    end
end

emu.registerafter(on_frame)
