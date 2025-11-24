#!/usr/bin/env zsh
#
# Search Reference Materials
#
# Search extracted text from reference manuals for specific terms or topics
#
# Usage: 
#   ./search-reference-materials.sh "sprite"
#   ./search-reference-materials.sh "sprite" --platform nes
#   ./search-reference-materials.sh "POKE" --platform zx-spectrum --context 3
#
# Options:
#   --platform <name>   Search only specific platform (nes, zx-spectrum, amiga, c64)
#   --context <n>       Show n lines of context (default: 2)
#   --ignore-case       Case-insensitive search (default)
#   --case-sensitive    Case-sensitive search

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_DIR="$PROJECT_ROOT/docs/source-materials"

# Default settings
CONTEXT_LINES=2
CASE_FLAG="-i"
PLATFORM=""
SEARCH_TERM=""

# Parse arguments
parse_args() {
    if [[ $# -eq 0 ]]; then
        show_usage
        exit 1
    fi
    
    SEARCH_TERM="$1"
    shift
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --platform)
                PLATFORM="$2"
                shift 2
                ;;
            --context)
                CONTEXT_LINES="$2"
                shift 2
                ;;
            --ignore-case)
                CASE_FLAG="-i"
                shift
                ;;
            --case-sensitive)
                CASE_FLAG=""
                shift
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                show_usage
                exit 1
                ;;
        esac
    done
}

show_usage() {
    echo "Usage: $0 <search-term> [options]"
    echo ""
    echo "Options:"
    echo "  --platform <name>      Search only specific platform"
    echo "                         (nes, zx-spectrum, amiga, c64)"
    echo "  --context <n>          Show n lines of context (default: 2)"
    echo "  --ignore-case          Case-insensitive search (default)"
    echo "  --case-sensitive       Case-sensitive search"
    echo ""
    echo "Examples:"
    echo "  $0 'sprite'"
    echo "  $0 'sprite' --platform nes"
    echo "  $0 'POKE' --platform zx-spectrum --context 5"
    echo "  $0 'blitter' --platform amiga --case-sensitive"
}

# Check if text files exist
check_text_files() {
    local platform_dir="$SOURCE_DIR/$1"
    
    if [[ ! -d "$platform_dir" ]]; then
        return 1
    fi
    
    local txt_count=$(find "$platform_dir" -name "*.txt" 2>/dev/null | wc -l)
    
    if [[ $txt_count -eq 0 ]]; then
        return 1
    fi
    
    return 0
}

# Search in platform
search_platform() {
    local platform_name="$1"
    local platform_dir="$SOURCE_DIR/$platform_name"
    
    if ! check_text_files "$platform_name"; then
        echo -e "${YELLOW}⚠ No text files found for ${platform_name}${NC}"
        return 1
    fi
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $(echo $platform_name | tr '[:lower:]' '[:upper:]' | tr '-' ' ')${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    local found_any=false
    
    for txtfile in "$platform_dir"/*.txt; do
        if [[ ! -f "$txtfile" ]]; then
            continue
        fi
        
        local matches=$(grep $CASE_FLAG -c "$SEARCH_TERM" "$txtfile" 2>/dev/null || echo "0")
        
        if [[ $matches -gt 0 ]]; then
            found_any=true
            local basename=$(basename "$txtfile" .txt)
            
            echo ""
            echo -e "${GREEN}📄 ${basename}${NC}"
            echo -e "${CYAN}   Found ${matches} match(es)${NC}"
            echo ""
            
            # Show matches with context
            grep $CASE_FLAG -C "$CONTEXT_LINES" --color=always "$SEARCH_TERM" "$txtfile" | head -n 100
            
            if [[ $matches -gt 10 ]]; then
                echo ""
                echo -e "${YELLOW}   ... (showing first 100 lines, ${matches} total matches)${NC}"
            fi
        fi
    done
    
    if [[ "$found_any" == false ]]; then
        echo -e "${YELLOW}  No matches found${NC}"
    fi
    
    return 0
}

# Main search function
main() {
    parse_args "$@"
    
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  Reference Materials Search                                ║"
    echo "║  Code Like It's 198x                                       ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${BLUE}Search term: ${YELLOW}${SEARCH_TERM}${NC}"
    
    if [[ -n "$PLATFORM" ]]; then
        echo -e "${BLUE}Platform: ${YELLOW}${PLATFORM}${NC}"
    else
        echo -e "${BLUE}Platform: ${YELLOW}All platforms${NC}"
    fi
    
    echo -e "${BLUE}Context lines: ${YELLOW}${CONTEXT_LINES}${NC}"
    echo -e "${BLUE}Case-sensitive: ${YELLOW}$([ -z "$CASE_FLAG" ] && echo "Yes" || echo "No")${NC}"
    
    # Check if source directory exists
    if [[ ! -d "$SOURCE_DIR" ]]; then
        echo ""
        echo -e "${RED}Error: Source materials directory not found${NC}"
        echo -e "${YELLOW}Run fetch-reference-materials.sh first to download materials${NC}"
        exit 1
    fi
    
    # Search in specified platform or all platforms
    if [[ -n "$PLATFORM" ]]; then
        search_platform "$PLATFORM"
    else
        for platform in nes zx-spectrum amiga c64; do
            search_platform "$platform"
        done
    fi
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${GREEN}Search complete${NC}"
    echo ""
}

# Run main function
main "$@"
