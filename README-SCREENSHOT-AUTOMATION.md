# Screenshot Automation for Retro Platforms

**Purpose:** Automate screenshot capture for NES, ZX Spectrum, and Amiga lesson content using platform-specific emulators.

---

## Quick Start

### NES (FCEUX)
```bash
cd /Users/stevehill/Projects/Code198x/scripts
./capture-nes-screenshots.sh game.nes 180 mario-level1
```

### ZX Spectrum (Fuse + FMF)
```bash
./capture-spectrum-screenshots.sh hello.tap 5 "100,150,200"
```

### Amiga (FS-UAE)
```bash
./capture-amiga-screenshots.sh demo.adf 10 3
```

---

## Installation Requirements

### NES
```bash
brew install fceux
```

### ZX Spectrum
```bash
brew install fuse-emulator

# fuse-emulator-utils (fmfconv) may need manual installation
# Download from: https://sourceforge.net/projects/fuse-emulator/files/fuse-utils/
```

### Amiga
```bash
brew install fs-uae
```

---

## NES Screenshot Automation

### Script: `capture-nes-screenshots.sh`

**Method:** Lua scripting via FCEUX emulator

**Features:**
- ✅ Fully automated (load ROM, run, screenshot, exit)
- ✅ Configurable frame count (default: 300 frames = ~5 seconds at 60 FPS)
- ✅ Custom output filenames
- ✅ Headless operation

**Usage:**
```bash
./capture-nes-screenshots.sh <rom-file> [frames] [output-name]

# Examples
./capture-nes-screenshots.sh mario.nes
./capture-nes-screenshots.sh mario.nes 180
./capture-nes-screenshots.sh mario.nes 180 mario-level1
```

**Arguments:**
- `rom-file` - Path to NES ROM file (required)
- `frames` - Number of frames to advance before screenshot (default: 300)
  - 60 frames = 1 second (NTSC)
  - 180 frames = 3 seconds
  - 300 frames = 5 seconds
- `output-name` - Custom filename without extension (optional)

**Output Location:**
```
~/.fceux/snaps/
├── mario-level1.png
├── game-001.png
└── ...
```

**How It Works:**
1. Creates temporary Lua script with specified parameters
2. Launches FCEUX with `--loadlua` and ROM
3. Lua script advances frames and captures screenshot
4. Emulator exits automatically
5. Screenshot saved to FCEUX snaps directory

**Lua API Used:**
- `emu.frameadvance()` - Advance one frame
- `gui.savescreenshot()` - Save screenshot with auto-name
- `gui.savescreenshotas(name)` - Save with custom name
- `emu.exit()` - Close emulator

---

## ZX Spectrum Screenshot Automation

### Script: `capture-spectrum-screenshots.sh`

**Method:** FMF movie recording + frame extraction via Fuse emulator

**Features:**
- ✅ Records entire emulation session as FMF movie
- ✅ Extracts specific frames or frame ranges as PNG
- ✅ Supports multiple file formats (.tap, .tzx, .z80, .sna, .szx)
- ⚠️ Requires GUI interaction (recording duration)

**Usage:**
```bash
./capture-spectrum-screenshots.sh <program-file> [seconds] [frame-numbers]

# Examples
./capture-spectrum-screenshots.sh hello.tap
./capture-spectrum-screenshots.sh hello.tap 5
./capture-spectrum-screenshots.sh hello.tap 5 "100,150,200"
./capture-spectrum-screenshots.sh game.z80 10 "200-300"
```

**Arguments:**
- `program-file` - Tape or snapshot file (required)
- `seconds` - Recording duration (default: 5 seconds)
- `frame-numbers` - Frames to extract (optional)
  - Single: `"100"`
  - Range: `"100-200"`
  - Multiple: `"100,150,200"`
  - Omit to extract all frames

**Output Location:**
```
./spectrum-captures/
├── hello.fmf                 # Recorded movie
├── hello-frame-0100.png
├── hello-frame-0150.png
└── hello-frame-0200.png
```

**How It Works:**
1. Launches Fuse with tape/snapshot and `--movie-start`
2. Records emulation for specified duration (50 FPS PAL)
3. Saves FMF movie file
4. Uses `fmfconv --png --out-cut` to extract specific frames
5. Saves PNG screenshots with frame numbers

**Frame Rate:**
- ZX Spectrum runs at 50 Hz (PAL)
- 50 frames = 1 second
- 250 frames = 5 seconds
- 500 frames = 10 seconds

**fmfconv Commands:**
```bash
# Extract specific frames
fmfconv --png --out-cut "100,150,200" input.fmf output

# Extract range
fmfconv --png --out-cut "100-200" input.fmf output

# Extract all frames
fmfconv --png input.fmf output
```

---

## Amiga Screenshot Automation

### Script: `capture-amiga-screenshots.sh`

**Method:** AppleScript automation + FS-UAE emulator

**Features:**
- ✅ Automated screenshot triggering via keyboard shortcuts
- ✅ Multiple screenshots with delays
- ✅ Configurable timing
- ⚠️ Requires GUI (AppleScript sends keystrokes)

**Usage:**
```bash
./capture-amiga-screenshots.sh <disk-image> [seconds] [screenshots]

# Examples
./capture-amiga-screenshots.sh demo.adf
./capture-amiga-screenshots.sh demo.adf 10
./capture-amiga-screenshots.sh demo.adf 10 3
```

**Arguments:**
- `disk-image` - Path to ADF disk image (required)
- `seconds` - Delay before first screenshot (default: 5)
- `screenshots` - Number of screenshots to capture (default: 1)

**Output Location:**
```
~/Documents/FS-UAE/Screenshots/
├── Screenshot-2025-01-20-15-30-45.png
├── Screenshot-2025-01-20-15-30-47.png
└── ...
```

**How It Works:**
1. Creates temporary FS-UAE configuration file
2. Launches FS-UAE with ADF disk image
3. Waits specified delay
4. Uses AppleScript to send Cmd+Delete (screenshot shortcut)
5. Repeats for multiple screenshots
6. FS-UAE remains open for manual inspection

**Configuration Options:**
- Amiga model: A500
- Chip memory: 1MB
- Floppy speed: 100% (turbo)
- Window size: 960×540
- Screenshot mask: 7 (all types)

**Screenshot Shortcut:**
- macOS: Cmd+Delete
- Linux/Windows: Mod+S or Print Screen

---

## Comparison Matrix

| Platform | Automation Level | Method | Headless | Multi-Screenshot | Frame Control |
|----------|-----------------|--------|----------|------------------|---------------|
| **NES** | ✅✅✅ Excellent | Lua scripting | ✅ Yes | ✅ Yes | ✅ Precise |
| **ZX Spectrum** | ✅✅ Good | FMF + fmfconv | ⚠️ Partial | ✅ Yes | ✅ Precise |
| **Amiga** | ✅ Moderate | AppleScript | ❌ No | ✅ Yes | ⚠️ Timing-based |

---

## Workflow Recommendations

### For Lesson Screenshots

**Single screenshot at specific point:**
- **NES**: Use frame count (e.g., 180 frames = 3 seconds)
- **ZX Spectrum**: Record 5 seconds, extract specific frame
- **Amiga**: Set delay in seconds

**Multiple screenshots from same program:**
- **NES**: Run script multiple times with different frame counts
- **ZX Spectrum**: Record once, extract multiple frames (efficient!)
- **Amiga**: Set multiple screenshot count

**Before/after comparison:**
- **All platforms**: Capture at early frame, then later frame

### For Animation Sequences

**ZX Spectrum is ideal:**
```bash
# Record 10 seconds, extract every 10th frame
./capture-spectrum-screenshots.sh animation.tap 10 "0-500:10"
```

**NES/Amiga:**
- Requires multiple script runs with different delays

---

## Troubleshooting

### NES (FCEUX)

**"fceux not found"**
```bash
brew install fceux
```

**"Lua script failed"**
- Check ROM file exists and is valid
- Verify FCEUX has Lua support: `fceux --help | grep lua`

**Screenshots not appearing**
- Check: `~/.fceux/snaps/`
- Verify write permissions

### ZX Spectrum (Fuse)

**"fuse not found"**
```bash
brew install fuse-emulator
```

**"fmfconv not found"**
- Install fuse-emulator-utils (may require manual build)
- Download: https://sourceforge.net/projects/fuse-emulator/files/fuse-utils/

**"FMF file not created"**
- Ensure Fuse opened successfully
- Check program file is valid
- Try longer recording duration

**"No frames extracted"**
- Check FMF file exists
- Verify frame numbers are within recording (50 FPS × seconds)
- Try extracting all frames first (omit frame-numbers)

### Amiga (FS-UAE)

**"fs-uae not found"**
```bash
brew install fs-uae
```

**"AppleScript error"**
- Ensure FS-UAE is running and focused
- Grant Terminal accessibility permissions in System Preferences
- Try manual screenshot: Cmd+Delete in FS-UAE window

**"Screenshots not appearing"**
- Check: `~/Documents/FS-UAE/Screenshots/`
- Verify FS-UAE has write permissions

---

## Advanced Usage

### NES: Custom Lua Scripts

Create your own Lua scripts for complex scenarios:

```lua
-- custom-capture.lua
local frames = {60, 120, 180}  -- Multiple timestamps

for i, frame in ipairs(frames) do
    for j = 1, frame do
        emu.frameadvance()
    end
    gui.savescreenshotas("screenshot-" .. i)
end

emu.exit()
```

Run with:
```bash
fceux --loadlua custom-capture.lua game.nes
```

### ZX Spectrum: Batch Frame Extraction

Extract frames at regular intervals:

```bash
# Every 50 frames (1 second intervals) for 10 seconds
fmfconv --png --out-cut "0-500:50" movie.fmf output
```

### Amiga: Multiple Disks

Capture from disk 2:

```bash
# Modify script or use fs-uae directly
fs-uae --floppy-drive-0=disk1.adf --floppy-drive-1=disk2.adf
```

---

## Integration with Lesson Workflow

### Standard Lesson Screenshot Process

1. **Create code sample** in `/code-samples/[platform]/phase-0/tier-1/lesson-NNN/`
2. **Run automation script** to capture screenshots
3. **Copy screenshots** to `/website/public/images/[platform]/phase-0/tier-1/lesson-NNN/`
4. **Reference in MDX** with relative paths

### Naming Convention

```
[platform]/phase-0/tier-1/lesson-NNN/
├── example-1-start.png      # Initial state
├── example-1-running.png    # Mid-execution
├── example-1-result.png     # Final result
└── example-2-demo.png       # Second example
```

### Screenshot Quality Standards

- **Resolution**: Native emulator output (don't upscale)
- **Format**: PNG (lossless)
- **Size**: Optimize with `pngcrush` or `optipng` if >100KB
- **Cropping**: Keep native aspect ratio, crop borders only if excessive

---

## Manual Fallback Procedures

If automation scripts fail, use these manual methods:

### NES (Manual)
1. Open ROM in FCEUX
2. Emulation → Run for N frames
3. Screenshot → Save Screenshot (F12)

### ZX Spectrum (Manual)
1. Open program in Fuse
2. File → Record Movie → Start Recording
3. Let run for desired duration
4. File → Record Movie → Stop Recording
5. Use fmfconv to extract frames

### Amiga (Manual)
1. Open ADF in FS-UAE
2. Run program
3. Press Cmd+Delete (macOS) to capture screenshot
4. Find in ~/Documents/FS-UAE/Screenshots/

---

## Future Enhancements

### Potential Improvements

**NES:**
- [ ] Savestates for exact game positions
- [ ] Controller input automation
- [ ] Batch ROM processing

**ZX Spectrum:**
- [ ] Automated FMF cleanup after extraction
- [ ] Time-based frame selection (seconds instead of frames)
- [ ] Automatic tape fast-forward to specific points

**Amiga:**
- [ ] True headless mode (if FS-UAE adds support)
- [ ] Mouse click automation for AMOS programs
- [ ] Multi-disk swapping automation

---

## Version History

- **1.0** (2025-01-20) - Initial automation scripts for all three platforms
- NES: Lua scripting via FCEUX
- ZX Spectrum: FMF recording + frame extraction
- Amiga: AppleScript + FS-UAE

---

**For:** Code Like It's 198x curriculum development
**Created:** 2025-01-20
