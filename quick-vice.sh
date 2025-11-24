#!/bin/bash
# quick-vice.sh - Quickly load a Commodore 64 lesson in VICE for testing
# Usage: ./quick-vice.sh path/to/lesson.bas
#        ./quick-vice.sh path/to/lesson.prg
#        ./quick-vice.sh commodore-64/phase-0/tier-2/lesson-023  (finds main.bas automatically)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if VICE is installed
if ! command -v x64sc &> /dev/null; then
    echo -e "${RED}Error: x64sc (VICE) not found${NC}"
    echo "   macOS: brew install vice"
    echo "   Linux: apt-get install vice"
    exit 1
fi

# Parse arguments
FILE_OR_DIR="$1"
WARP_MODE="${2:-yes}"  # Default to warp mode for faster loading

if [ -z "$FILE_OR_DIR" ]; then
    echo "Usage: $0 <file.bas|file.prg|lesson-dir> [nowarp]"
    echo ""
    echo "Examples:"
    echo "  $0 code-samples/commodore-64/phase-0/tier-2/lesson-023/main.bas"
    echo "  $0 commodore-64/phase-0/tier-2/lesson-023"
    echo "  $0 path/to/lesson.prg nowarp"
    exit 1
fi

# Resolve file path
TARGET_FILE=""

# If it's a directory path, try to find main.bas or main.prg
if [ -d "$PROJECT_ROOT/code-samples/$FILE_OR_DIR" ]; then
    SEARCH_DIR="$PROJECT_ROOT/code-samples/$FILE_OR_DIR"
elif [ -d "$FILE_OR_DIR" ]; then
    SEARCH_DIR="$FILE_OR_DIR"
else
    SEARCH_DIR=""
fi

if [ -n "$SEARCH_DIR" ]; then
    # Look for main.bas or main.prg
    if [ -f "$SEARCH_DIR/main.bas" ]; then
        TARGET_FILE="$SEARCH_DIR/main.bas"
    elif [ -f "$SEARCH_DIR/main.prg" ]; then
        TARGET_FILE="$SEARCH_DIR/main.prg"
    else
        echo -e "${RED}Error: No main.bas or main.prg found in $SEARCH_DIR${NC}"
        exit 1
    fi
elif [ -f "$FILE_OR_DIR" ]; then
    TARGET_FILE="$FILE_OR_DIR"
elif [ -f "$PROJECT_ROOT/code-samples/$FILE_OR_DIR" ]; then
    TARGET_FILE="$PROJECT_ROOT/code-samples/$FILE_OR_DIR"
else
    echo -e "${RED}Error: File not found: $FILE_OR_DIR${NC}"
    exit 1
fi

# Determine file type
EXT="${TARGET_FILE##*.}"

echo -e "${GREEN}Loading Commodore 64 lesson in VICE...${NC}"
echo "   File: $TARGET_FILE"

# Launch VICE with appropriate options
if [ "$WARP_MODE" = "nowarp" ]; then
    echo "   Mode: Normal speed"
    x64sc -autostart "$TARGET_FILE" &
else
    echo "   Mode: Warp (fast loading)"
    x64sc -autostart "$TARGET_FILE" -autostart-warp &
fi

VICE_PID=$!
echo "   PID: $VICE_PID"
echo ""
echo -e "${YELLOW}Tip: Press Alt+W to toggle warp mode in VICE${NC}"
echo -e "${YELLOW}Tip: Use Cmd+Shift+4 (macOS) to capture screenshot${NC}"
