-- Debug Lua script
print("===== LUA SCRIPT STARTED =====")

local function on_frame()
    if emu.framecount() == 1 then
        print("Frame 1 reached")
    end
    
    if emu.framecount() == 300 then
        print("Frame 300 reached - taking screenshot")
        gui.savescreenshot()
        print("Screenshot command executed")
    end
    
    if emu.framecount() == 310 then
        print("Frame 310 - exiting")
        os.exit(0)
    end
end

emu.registerafter(on_frame)
print("===== REGISTERED FRAME CALLBACK =====")
