#!/usr/bin/env zsh
#
# Compile all NES lesson assembly files to .nes ROMs
#
# Uses ca65 (assembler) and ld65 (linker) from cc65 toolchain
#

set -e

# Colors
GREEN=$'\033[0;32m'
RED=$'\033[0;31m'
YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'
NC=$'\033[0m'

# Base directory
BASE_DIR="/Users/stevehill/Projects/Code198x/code-samples/nintendo-entertainment-system/phase-1/tier-1"

# Check for ca65/ld65
if ! command -v ca65 &> /dev/null; then
    echo "${RED}Error: ca65 not found${NC}"
    echo "Install with: brew install cc65"
    exit 1
fi

echo ""
echo "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo "${BLUE}║  NES Lesson Compiler                       ║${NC}"
echo "${BLUE}║  Compiling all .asm files to .nes ROMs     ║${NC}"
echo "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Stats
TOTAL=0
SUCCESS=0
FAILED=0

# Find all .asm files
while IFS= read -r asm_file; do
    TOTAL=$((TOTAL + 1))

        # Get directory and base name
        dir=$(dirname "$asm_file")
        base=$(basename "$asm_file" .asm)
        obj_file="$dir/$base.o"
        nes_file="$dir/$base.nes"

        lesson=$(basename "$dir")

        echo "${YELLOW}Compiling $lesson/$base.asm...${NC}"

        # Assemble
        if ca65 -o "$obj_file" "$asm_file" 2>&1; then
            # Link
            if ld65 -C nes.cfg -o "$nes_file" "$obj_file" 2>&1; then
                echo "${GREEN}✓ $nes_file${NC}"
                SUCCESS=$((SUCCESS + 1))
                rm -f "$obj_file"
            else
                echo "${RED}✗ Link failed: $base.asm${NC}"
                FAILED=$((FAILED + 1))
            fi
        else
            echo "${RED}✗ Assembly failed: $base.asm${NC}"
            FAILED=$((FAILED + 1))
        fi

        echo ""
done < <(find "$BASE_DIR" -name "*.asm" -type f | sort)

echo ""
echo "${BLUE}════════════════════════════════════════════${NC}"
echo "${GREEN}Compilation complete!${NC}"
echo ""
echo "Total files: $TOTAL"
echo "${GREEN}Success: $SUCCESS${NC}"
if [[ $FAILED -gt 0 ]]; then
    echo "${RED}Failed: $FAILED${NC}"
fi
echo ""
