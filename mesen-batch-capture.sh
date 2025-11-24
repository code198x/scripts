#!/usr/bin/env zsh
#
# Batch NES Screenshot Capture using Mesen
# Mesen has better automation support than FCEUX
#

set -e

MESEN="/Applications/Mesen.app/Contents/MacOS/Mesen"
CODE_SAMPLES="/Users/stevehill/Projects/Code198x/code-samples/nintendo-entertainment-system/phase-1/tier-1"
WEBSITE_IMAGES="/Users/stevehill/Projects/Code198x/website/public/images/nintendo-entertainment-system/phase-1/tier-1"
MESEN_SCREENSHOTS="$HOME/Pictures/Mesen"

# Colors
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
RED=$'\033[0;31m'
BLUE=$'\033[0;34m'
NC=$'\033[0m'

SUCCESS=0
SKIPPED=0
FAILED=0
TOTAL=0

echo ""
echo "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo "${BLUE}║  NES Screenshot Batch Capture (Mesen)      ║${NC}"
echo "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Check Mesen installation
if [[ ! -x "$MESEN" ]]; then
    echo "${RED}Error: Mesen not found at $MESEN${NC}"
    exit 1
fi

# Create Mesen screenshots directory if needed
mkdir -p "$MESEN_SCREENSHOTS"

# Process each lesson
for lesson_dir in "$CODE_SAMPLES"/lesson-*(N); do
    if [[ ! -d "$lesson_dir" ]]; then
        continue
    fi

    lesson_num=$(basename "$lesson_dir")
    nes_file=$(find "$lesson_dir" -name "*.nes" -type f 2>/dev/null | head -1)

    if [[ -z "$nes_file" ]]; then
        echo "${RED}✗ $lesson_num: No .nes file found${NC}"
        FAILED=$((FAILED + 1))
        TOTAL=$((TOTAL + 1))
        continue
    fi

    base_name=$(basename "$nes_file" .nes)
    output_dir="$WEBSITE_IMAGES/$lesson_num"
    output_file="$output_dir/${base_name}.png"

    # Skip if exists
    if [[ -f "$output_file" ]]; then
        echo "${GREEN}✓ $lesson_num: Screenshot exists${NC}"
        SKIPPED=$((SKIPPED + 1))
        TOTAL=$((TOTAL + 1))
        continue
    fi

    mkdir -p "$output_dir"

    echo "${YELLOW}📸 Capturing $lesson_num ($base_name)...${NC}"

    # Clear old Mesen screenshots
    rm -f "$MESEN_SCREENSHOTS"/*.png 2>/dev/null || true

    # Run ROM in Mesen with GUI for 5 seconds then close
    # Mesen doesn't have headless screenshot mode, so we use GUI briefly
    (
        timeout 6 "$MESEN" "$nes_file" &>/dev/null || true
    ) &
    MESEN_PID=$!

    # Wait for launch
    sleep 1

    # Send screenshot command via AppleScript (F12)
    osascript -e 'tell application "System Events"
        keystroke "2" using {function down, shift down}
    end tell' 2>/dev/null || true

    # Wait a bit
    sleep 1

    # Kill Mesen
    kill -9 $MESEN_PID 2>/dev/null || true
    killall -9 Mesen 2>/dev/null || true

    # Wait for cleanup
    sleep 0.5

    # Find latest screenshot
    latest=$(ls -t "$MESEN_SCREENSHOTS"/*.png 2>/dev/null | head -1)

    if [[ -n "$latest" ]] && [[ -f "$latest" ]]; then
        cp "$latest" "$output_file"
        size=$(stat -f%z "$output_file")

        if [[ $size -gt 1000 ]]; then
            echo "${GREEN}✓ $output_file ($size bytes)${NC}"
            SUCCESS=$((SUCCESS + 1))
        else
            echo "${RED}✗ $lesson_num: Screenshot too small ($size bytes)${NC}"
            rm -f "$output_file"
            FAILED=$((FAILED + 1))
        fi
    else
        echo "${RED}✗ $lesson_num: No screenshot captured${NC}"
        FAILED=$((FAILED + 1))
    fi

    TOTAL=$((TOTAL + 1))
done

echo ""
echo "${BLUE}════════════════════════════════════════════${NC}"
echo "${GREEN}Batch capture complete!${NC}"
echo ""
echo "Total: $TOTAL"
echo "${GREEN}Success: $SUCCESS${NC}"
echo "${YELLOW}Skipped: $SKIPPED${NC}"
if [[ $FAILED -gt 0 ]]; then
    echo "${RED}Failed: $FAILED${NC}"
fi
echo ""

if [[ $SUCCESS -gt 0 ]]; then
    echo "Screenshots saved to:"
    echo "  $WEBSITE_IMAGES"
    echo ""
    echo "Recent captures:"
    find "$WEBSITE_IMAGES" -name "*.png" -type f -exec ls -lh {} \; 2>/dev/null | tail -5
fi
echo ""
