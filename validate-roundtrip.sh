#!/usr/bin/env bash
# Roundtrip validation: .bas → .prg → .bas
# Ensures BASIC files can be converted to PRG and back without corruption

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

validate_file() {
    local basfile="$1"
    local basename=$(basename "$basfile" .bas)
    local dirname=$(dirname "$basfile")

    # Create temp files
    local tmpprg="${dirname}/.${basename}.tmp.prg"
    local tmpbas="${dirname}/.${basename}.tmp.bas"

    echo -n "Testing $basfile... "

    # Step 1: Convert .bas to .prg
    if ! petcat -w2 -o "$tmpprg" -- "$basfile" 2>/dev/null; then
        echo -e "${RED}FAIL${NC} (petcat -w2 failed)"
        return 1
    fi

    # Step 2: Convert .prg back to .bas
    if ! petcat -2 -- "$tmpprg" > "$tmpbas" 2>/dev/null; then
        echo -e "${RED}FAIL${NC} (petcat -2 failed)"
        rm -f "$tmpprg" "$tmpbas"
        return 1
    fi

    # Step 3: Extract clean content (remove header/footer)
    local cleanedfile="${dirname}/.${basename}.clean.bas"
    tail -n +4 "$tmpbas" | gsed '$ d' | gsed 's/^   //' > "$cleanedfile"

    # Step 4: Compare (ignoring whitespace differences)
    if diff -w "$basfile" "$cleanedfile" >/dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        rm -f "$tmpprg" "$tmpbas" "$cleanedfile"
        return 0
    else
        echo -e "${RED}FAIL${NC} (content differs after roundtrip)"
        echo "  Original: $basfile"
        echo "  Roundtripped: $cleanedfile"
        echo "  Differences:"
        diff -u "$basfile" "$cleanedfile" | head -20
        rm -f "$tmpprg" "$tmpbas"
        # Keep cleanedfile for inspection
        return 1
    fi
}

main() {
    local failed=0
    local passed=0

    echo "=== BASIC Roundtrip Validation ==="
    echo

    if [[ $# -eq 0 ]]; then
        echo "Usage: $0 <file.bas> [file.bas ...]"
        echo "   or: $0 <directory>  (validates all .bas files)"
        exit 1
    fi

    # If argument is a directory, find all .bas files
    if [[ -d "$1" ]]; then
        echo "Scanning directory: $1"
        echo
        while IFS= read -r -d '' basfile; do
            if validate_file "$basfile"; then
                ((passed++))
            else
                ((failed++))
            fi
        done < <(find "$1" -name "*.bas" -type f -print0 | sort -z)
    else
        # Validate specific files
        for basfile in "$@"; do
            if [[ ! -f "$basfile" ]]; then
                echo -e "${YELLOW}SKIP${NC} $basfile (not found)"
                continue
            fi
            if validate_file "$basfile"; then
                ((passed++))
            else
                ((failed++))
            fi
        done
    fi

    echo
    echo "=== Summary ==="
    echo -e "${GREEN}Passed: $passed${NC}"
    echo -e "${RED}Failed: $failed${NC}"

    if [[ $failed -gt 0 ]]; then
        exit 1
    fi
}

main "$@"
