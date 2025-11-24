-- NES Screenshot Capture - 300 frames (~5 seconds)
print("NES Screenshot Capture - 300 frames")

for i = 1, 300 do
    emu.frameadvance()
    if i % 60 == 0 then
        print("Frame " .. i .. " / 300")
    end
end

print("Capturing screenshot...")
gui.savescreenshot()
print("Done!")
emu.exit()
