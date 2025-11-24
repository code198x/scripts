#!/usr/bin/env zsh
#
# ZX Spectrum Screenshot Capture Automation
#
# Captures screenshots from ZX Spectrum programs using Fuse emulator
# with FMF movie recording and frame extraction
#
# Usage:
#   ./capture-spectrum-screenshots.sh program.tap [seconds] [frame-numbers]
#   ./capture-spectrum-screenshots.sh hello.tap 5 "100,150,200"
#   ./capture-spectrum-screenshots.sh game.tap 10        # Extract all frames
#
# Arguments:
#   program.tap     - Path to tape/snapshot file (required)
#   seconds         - Seconds to record (default: 5)
#   frame-numbers   - Comma-delimited frame numbers to extract (default: all)
#                     Examples: "100" or "100-200" or "100,150,200"
#
# Output:
#   PNG screenshots in current directory
#
# Requirements:
#   - fuse (ZX Spectrum emulator)
#   - fuse-emulator-utils (for fmfconv)
#   - Install: brew install fuse-emulator fuse-emulator-utils

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
    local missing=()

    if ! command -v fuse &> /dev/null; then
        missing+=("fuse")
    fi

    if ! command -v fmfconv &> /dev/null; then
        missing+=("fuse-emulator-utils")
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        echo -e "${RED}Error: Missing dependencies: ${missing[*]}${NC}"
        echo ""
        echo "Install on macOS with:"
        echo "  brew install fuse-emulator fuse-emulator-utils"
        echo ""
        echo -e "${YELLOW}Note: fuse-emulator-utils may need to be built from source${NC}"
        echo "See: https://sourceforge.net/projects/fuse-emulator/files/fuse-utils/"
        exit 1
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 <program-file> [seconds] [frame-numbers]"
    echo ""
    echo "Arguments:"
    echo "  program-file    Tape/snapshot file (.tap, .tzx, .z80, .sna, .szx)"
    echo "  seconds         Recording duration (default: 5)"
    echo "  frame-numbers   Frames to extract: \"100\" or \"100-200\" or \"100,150\""
    echo ""
    echo "Examples:"
    echo "  $0 hello.tap"
    echo "  $0 hello.tap 5"
    echo "  $0 hello.tap 5 \"100,150,200\""
    echo "  $0 game.z80 10 \"200-300\""
}

# Parse arguments
if [[ $# -eq 0 ]]; then
    show_usage
    exit 1
fi

PROGRAM_FILE="$1"
SECONDS="${2:-5}"
FRAME_NUMBERS="${3:-}"

# Validate program file
if [[ ! -f "$PROGRAM_FILE" ]]; then
    echo -e "${RED}Error: Program file not found: $PROGRAM_FILE${NC}"
    exit 1
fi

# Get base filename without extension
BASENAME=$(basename "$PROGRAM_FILE" | sed 's/\.[^.]*$//')
OUTPUT_DIR="$(pwd)/spectrum-captures"
FMF_FILE="$OUTPUT_DIR/$BASENAME.fmf"

# Main execution
main() {
    check_dependencies

    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  ZX Spectrum Screenshot Capture (Fuse + FMF)               ║"
    echo "║  Code Like It's 198x                                       ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${BLUE}Program: ${YELLOW}$PROGRAM_FILE${NC}"
    echo -e "${BLUE}Recording duration: ${YELLOW}${SECONDS} seconds${NC}"

    if [[ -n "$FRAME_NUMBERS" ]]; then
        echo -e "${BLUE}Extracting frames: ${YELLOW}$FRAME_NUMBERS${NC}"
    else
        echo -e "${BLUE}Extracting: ${YELLOW}All frames${NC}"
    fi

    echo ""

    # Create output directory
    mkdir -p "$OUTPUT_DIR"

    echo -e "${CYAN}Step 1: Recording FMF movie...${NC}"
    echo ""
    echo -e "${YELLOW}Instructions:${NC}"
    echo "  1. Fuse will open and load your program"
    echo "  2. Recording will start automatically"
    echo "  3. Let the program run for $SECONDS seconds"
    echo "  4. Movie will be saved to: $FMF_FILE"
    echo ""
    echo -e "${YELLOW}Press any key when ready to start recording...${NC}"
    read -k1

    # Calculate frames (50 Hz PAL = 50 frames per second)
    local frames=$((SECONDS * 50))

    # Run Fuse with movie recording
    # Note: This will open Fuse GUI - user needs to let it run
    echo ""
    echo -e "${CYAN}Launching Fuse (will record for ~$SECONDS seconds)...${NC}"

    # Run Fuse with tape autoload and movie recording
    fuse --tape "$PROGRAM_FILE" --auto-load --movie-start "$FMF_FILE" &
    FUSE_PID=$!

    # Wait for recording duration
    echo -e "${CYAN}Recording... (waiting $SECONDS seconds)${NC}"
    sleep "$SECONDS"

    # Close Fuse
    echo -e "${CYAN}Stopping recording...${NC}"
    kill -TERM "$FUSE_PID" 2>/dev/null || true
    sleep 1

    # Check if FMF was created
    if [[ ! -f "$FMF_FILE" ]]; then
        echo -e "${RED}Error: FMF file not created${NC}"
        echo -e "${YELLOW}Recording may have failed. Try running manually:${NC}"
        echo "  fuse --tape \"$PROGRAM_FILE\" --auto-load --movie-start \"$FMF_FILE\""
        exit 1
    fi

    echo -e "${GREEN}✓ Recording saved: $FMF_FILE${NC}"
    echo ""

    # Extract frames
    echo -e "${CYAN}Step 2: Extracting PNG frames...${NC}"

    local output_pattern="$OUTPUT_DIR/$BASENAME-frame"

    if [[ -n "$FRAME_NUMBERS" ]]; then
        # Extract specific frames
        fmfconv --png --out-cut "$FRAME_NUMBERS" "$FMF_FILE" "$output_pattern"
    else
        # Extract all frames
        fmfconv --png "$FMF_FILE" "$output_pattern"
    fi

    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Screenshot extraction complete!${NC}"
    echo ""
    echo -e "${BLUE}Output directory: ${YELLOW}$OUTPUT_DIR${NC}"
    echo ""

    # Count extracted frames
    local frame_count=$(ls "$OUTPUT_DIR"/$BASENAME-frame*.png 2>/dev/null | wc -l)
    echo -e "${GREEN}Extracted ${frame_count} frame(s)${NC}"
    echo ""

    # List files
    echo "Files:"
    ls -lh "$OUTPUT_DIR"/$BASENAME* | awk '{print "  " $9 " (" $5 ")"}'
    echo ""

    echo "To view:"
    echo "  open $OUTPUT_DIR"
    echo ""
}

# Run main function
main "$@"
