#!/usr/bin/env zsh
#
# Batch NES Screenshot Capture using nes-screenshot-gui.sh
# Uses screencapture to grab FCEUX window
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CAPTURE_SCRIPT="$SCRIPT_DIR/nes-screenshot-gui.sh"
CODE_SAMPLES="/Users/stevehill/Projects/Code198x/code-samples/nintendo-entertainment-system/phase-1/tier-1"
WEBSITE_IMAGES="/Users/stevehill/Projects/Code198x/website/public/images/nintendo-entertainment-system/phase-1/tier-1"

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
echo "${BLUE}║  NES Screenshot Batch Capture (GUI)        ║${NC}"
echo "${BLUE}║  Using screencapture + FCEUX               ║${NC}"
echo "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Process each lesson
for lesson_dir in "$CODE_SAMPLES"/lesson-*(N); do
    if [[ ! -d "$lesson_dir" ]]; then
        continue
    fi

    lesson_num=$(basename "$lesson_dir")

    # Find .nes file
    nes_file=$(find "$lesson_dir" -name "*.nes" -type f 2>/dev/null | head -1)

    if [[ -z "$nes_file" ]]; then
        echo "${RED}✗ $lesson_num: No .nes file found${NC}"
        FAILED=$((FAILED + 1))
        TOTAL=$((TOTAL + 1))
        continue
    fi

    # Determine output path
    base_name=$(basename "$nes_file" .nes)
    output_dir="$WEBSITE_IMAGES/$lesson_num"
    output_file="$output_dir/${base_name}.png"

    # Skip if exists
    if [[ -f "$output_file" ]]; then
        echo "${GREEN}✓ $lesson_num: Screenshot exists, skipping${NC}"
        SKIPPED=$((SKIPPED + 1))
        TOTAL=$((TOTAL + 1))
        continue
    fi

    # Create output directory
    mkdir -p "$output_dir"

    # Capture screenshot
    echo "${YELLOW}📸 Capturing $lesson_num ($base_name)...${NC}"

    if "$CAPTURE_SCRIPT" "$nes_file" "$output_file" 5 2>&1; then
        SUCCESS=$((SUCCESS + 1))
    else
        echo "${RED}✗ $lesson_num: Capture failed${NC}"
        FAILED=$((FAILED + 1))
    fi

    TOTAL=$((TOTAL + 1))

    # Small delay between captures
    sleep 1
done

echo ""
echo "${BLUE}════════════════════════════════════════════${NC}"
echo "${GREEN}Batch capture complete!${NC}"
echo ""
echo "Total lessons: $TOTAL"
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
