#!/bin/bash
# validate-basic.sh - Syntax check all C64 BASIC lesson files
# Uses petcat to verify BASIC V2 syntax without running the code

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CODE_SAMPLES_DIR="$PROJECT_ROOT/code-samples/commodore-64/phase-0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Validating Commodore 64 BASIC lesson files (Phase 0)..."
echo ""

TOTAL=0
PASSED=0
FAILED=0

# Check if petcat is available
if ! command -v petcat &> /dev/null; then
    echo -e "${RED}❌ Error: petcat not found${NC}"
    echo "   Install VICE emulator to get petcat"
    echo "   macOS: brew install vice"
    echo "   Linux: apt-get install vice"
    exit 1
fi

# Find all .bas files in code-samples/commodore-64/phase-0
while IFS= read -r file; do
    TOTAL=$((TOTAL + 1))

    # Get relative path for cleaner output
    REL_PATH="${file#$PROJECT_ROOT/}"

    # Try to parse the file with petcat
    if petcat -w2 -text "$file" > /dev/null 2>&1; then
        echo -e "${GREEN}[PASS]${NC} $REL_PATH"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}[FAIL]${NC} $REL_PATH"
        echo -e "${YELLOW}  Error details:${NC}"
        petcat -w2 -text "$file" 2>&1 | sed 's/^/    /' || true
        echo ""
        FAILED=$((FAILED + 1))
    fi
done < <(find "$CODE_SAMPLES_DIR" -name "*.bas" -type f | sort)

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary: $PASSED/$TOTAL files passed syntax validation"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All BASIC files are syntactically correct${NC}"
    exit 0
else
    echo -e "${RED}$FAILED file(s) have syntax errors${NC}"
    exit 1
fi
