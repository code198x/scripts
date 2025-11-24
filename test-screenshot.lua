-- Minimal screenshot test
print("Starting screenshot test")

local frame_target = 60  -- 1 second
local done = false

emu.registerafter(function()
    local frame = emu.framecount()
    
    if frame == 1 then
        print("Frame 1 - ROM started")
    end
    
    if frame == frame_target and not done then
        print("Taking screenshot at frame " .. frame)
        gui.savescreenshot()
        done = true
        print("Screenshot saved, waiting 60 more frames")
    end
    
    if frame == frame_target + 60 then
        print("Exiting")
        emu.exit()
    end
end)

print("Frame callback registered")
