#!/usr/bin/env zsh
#
# Amiga Screenshot Capture Automation
#
# Captures screenshots from Amiga programs using FS-UAE emulator
# with automatic screenshot triggering
#
# Usage:
#   ./capture-amiga-screenshots.sh disk.adf [seconds] [screenshots]
#   ./capture-amiga-screenshots.sh amos-demo.adf 10 3
#
# Arguments:
#   disk.adf    - Path to ADF disk image (required)
#   seconds     - Delay before first screenshot (default: 5)
#   screenshots - Number of screenshots to capture (default: 1)
#
# Output:
#   PNG screenshots in ~/Documents/FS-UAE/Screenshots/
#
# Requirements:
#   - fs-uae (Amiga emulator)
#   - Install: brew install fs-uae

set -euo pipefail

# Color output
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'
CYAN=$'\033[0;36m'
NC=$'\033[0m' # No Color

# Check dependencies
check_dependencies() {
    if ! command -v fs-uae &> /dev/null; then
        echo -e "${RED}Error: fs-uae not found${NC}"
        echo ""
        echo "Install on macOS with:"
        echo "  brew install fs-uae"
        exit 1
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 <disk-image> [seconds] [screenshots]"
    echo ""
    echo "Arguments:"
    echo "  disk-image   Path to ADF disk image (required)"
    echo "  seconds      Delay before first screenshot (default: 5)"
    echo "  screenshots  Number of screenshots to capture (default: 1)"
    echo ""
    echo "Examples:"
    echo "  $0 demo.adf"
    echo "  $0 demo.adf 10"
    echo "  $0 demo.adf 10 3"
}

# Parse arguments
if [[ $# -eq 0 ]]; then
    show_usage
    exit 1
fi

DISK_IMAGE="$1"
DELAY_SECONDS="${2:-5}"
SCREENSHOT_COUNT="${3:-1}"

# Validate disk image
if [[ ! -f "$DISK_IMAGE" ]]; then
    echo -e "${RED}Error: Disk image not found: $DISK_IMAGE${NC}"
    exit 1
fi

# Get absolute path
DISK_IMAGE=$(cd "$(dirname "$DISK_IMAGE")" && pwd)/$(basename "$DISK_IMAGE")

# FS-UAE screenshots directory
SCREENSHOTS_DIR="$HOME/Documents/FS-UAE/Screenshots"

# Create temporary configuration file
create_config() {
    local config=$(mktemp /tmp/fsuae-capture-XXXXXX.conf)

    cat > "$config" << EOF
# Auto-generated FS-UAE Configuration for Screenshot Capture
# Code Like It's 198x

# Amiga model (A500 with 1MB Chip RAM)
amiga_model = A500
chip_memory = 1024

# Floppy drive
floppy_drive_0 = $DISK_IMAGE
floppy_drive_speed = 100

# Video settings
fullscreen = 0
window_width = 960
window_height = 540

# Audio
accuracy = 0

# Screenshot settings
screenshots_output_mask = 7
# Bind F12 key to screenshot action
keyboard_key_f12 = action_screenshot

# Performance
automatic_input_grab = 0
EOF

    echo "$config"
}

# Send keystroke to FS-UAE window using osascript
trigger_screenshot() {
    # Wait for delay
    sleep 1

    # Use AppleScript to send F12 key to FS-UAE
    osascript <<EOF
tell application "System Events"
    tell process "fs-uae"
        keystroke (ASCII character 127) using {command down}
    end tell
end tell
EOF
}

# Main execution
main() {
    check_dependencies

    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  Amiga Screenshot Capture (FS-UAE)                         ║"
    echo "║  Code Like It's 198x                                       ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${BLUE}Disk image: ${YELLOW}$DISK_IMAGE${NC}"
    echo -e "${BLUE}Delay: ${YELLOW}${DELAY_SECONDS} seconds${NC}"
    echo -e "${BLUE}Screenshots: ${YELLOW}${SCREENSHOT_COUNT}${NC}"
    echo ""

    # Create output directory
    mkdir -p "$SCREENSHOTS_DIR"

    # Create configuration
    echo -e "${CYAN}Creating FS-UAE configuration...${NC}"
    CONFIG_FILE=$(create_config)

    echo -e "${CYAN}Launching FS-UAE...${NC}"
    echo ""
    echo -e "${YELLOW}Instructions:${NC}"
    echo "  1. FS-UAE will open with your disk image"
    echo "  2. After $DELAY_SECONDS seconds, screenshots will be captured automatically"
    echo "  3. Screenshots are saved with Cmd+Del (Delete key)"
    echo "  4. Close FS-UAE when finished"
    echo ""
    echo -e "${YELLOW}Press any key when ready to start...${NC}"
    read -k1

    # Launch FS-UAE in background
    echo ""
    echo -e "${CYAN}Starting emulator...${NC}"
    fs-uae "$CONFIG_FILE" &
    FSUAE_PID=$!

    # Wait for emulator to start
    sleep 3

    # Wait for delay before first screenshot
    echo -e "${CYAN}Waiting ${DELAY_SECONDS} seconds...${NC}"
    sleep "$DELAY_SECONDS"

    # Capture screenshots
    for i in $(seq 1 $SCREENSHOT_COUNT); do
        echo -e "${CYAN}Capturing screenshot $i / $SCREENSHOT_COUNT...${NC}"

        # Send screenshot command (Cmd+Delete in FS-UAE)
        osascript <<EOF 2>/dev/null
tell application "System Events"
    tell process "fs-uae"
        set frontmost to true
        key code 51 using {command down}
    end tell
end tell
EOF

        # Wait between screenshots if more than one
        if [[ $i -lt $SCREENSHOT_COUNT ]]; then
            sleep 2
        fi
    done

    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Screenshot capture complete!${NC}"
    echo ""
    echo -e "${YELLOW}Note: FS-UAE is still running. Close it manually when done.${NC}"
    echo ""
    echo -e "${BLUE}Screenshots saved to:${NC}"
    echo -e "${YELLOW}$SCREENSHOTS_DIR${NC}"
    echo ""

    # List recent screenshots
    echo "Recent screenshots:"
    ls -lt "$SCREENSHOTS_DIR" | head -n $((SCREENSHOT_COUNT + 1)) | tail -n $SCREENSHOT_COUNT | awk '{print "  " $9 " (" $5 " bytes)"}'
    echo ""

    echo "To view:"
    echo "  open \"$SCREENSHOTS_DIR\""
    echo ""

    # Wait for user to close FS-UAE
    echo -e "${CYAN}Waiting for FS-UAE to close...${NC}"
    wait $FSUAE_PID 2>/dev/null || true

    # Clean up
    rm -f "$CONFIG_FILE"

    echo -e "${GREEN}Done!${NC}"
}

# Run main function
main "$@"
