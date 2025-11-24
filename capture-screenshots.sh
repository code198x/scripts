#!/usr/bin/env bash
# Automated screenshot capture for C64 BASIC code samples
# Usage: ./scripts/capture-screenshots.sh <lesson-directory> [cycles]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <lesson-directory> [cycles]"
    echo "Example: $0 code-samples/commodore-64/phase-0/tier-1/lesson-001"
    echo "         $0 code-samples/commodore-64/phase-0/tier-1/lesson-002 10000000"
    exit 1
fi

LESSON_DIR="$1"
CYCLES="${2:-5000000}"  # Default 5 million cycles

if [[ ! -d "$LESSON_DIR" ]]; then
    echo -e "${RED}Error:${NC} Directory not found: $LESSON_DIR"
    exit 1
fi

# Extract lesson path components for image directory
# e.g., code-samples/commodore-64/phase-0/tier-1/lesson-001
#    -> c64/phase-0/tier-1/lesson-001
LESSON_PATH=$(echo "$LESSON_DIR" | gsed 's|^code-samples/commodore-64/|c64/|')

# Create output directory
IMG_DIR="website/public/images/${LESSON_PATH}"
mkdir -p "$IMG_DIR"

echo "=== Screenshot Capture ==="
echo "Lesson directory: $LESSON_DIR"
echo "Output directory: $IMG_DIR"
echo "Cycle limit: $CYCLES"
echo

# Find all .prg files in lesson directory
shopt -s nullglob
PRG_FILES=("$LESSON_DIR"/*.prg)

if [[ ${#PRG_FILES[@]} -eq 0 ]]; then
    echo -e "${YELLOW}Warning:${NC} No .prg files found in $LESSON_DIR"
    echo "Run petcat first to generate .prg files from .bas sources"
    exit 1
fi

for prgfile in "${PRG_FILES[@]}"; do
    basename=$(basename "$prgfile" .prg)
    output_png="$IMG_DIR/${basename}.png"

    echo -n "Capturing $basename... "

    # Run VICE with cycle limit and exitscreenshot
    if x64sc -autostart "$prgfile" \
            -limitcycles "$CYCLES" \
            -VICIIdsize \
            -exitscreenshot "$output_png" \
            +sound \
            2>/dev/null; then
        if [[ -f "$output_png" ]]; then
            size=$(du -h "$output_png" | cut -f1)
            echo -e "${GREEN}OK${NC} ($size)"
        else
            echo -e "${RED}FAIL${NC} (screenshot not created)"
        fi
    else
        echo -e "${RED}FAIL${NC} (VICE error)"
    fi
done

echo
echo "=== Summary ==="
echo "Screenshots saved to: $IMG_DIR"
ls -lh "$IMG_DIR"/*.png 2>/dev/null | awk '{print $9, "("$5")"}'
