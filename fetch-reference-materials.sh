#!/usr/bin/env zsh
#
# Fetch Reference Materials from Internet Archive
# 
# Downloads authoritative reference manuals for retro computing platforms
# and extracts text content for searchability.
#
# Usage: ./fetch-reference-materials.sh [--no-extract]
#
# Requirements:
#   - wget (for downloads)
#   - pdftotext (from poppler-utils, for text extraction)
#   - Internet connection
#
# Install dependencies on macOS:
#   brew install wget poppler

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_DIR="$PROJECT_ROOT/docs/source-materials"

# Parse arguments
EXTRACT_TEXT=true
if [[ "${1:-}" == "--no-extract" ]]; then
    EXTRACT_TEXT=false
fi

# Check dependencies
check_dependencies() {
    local missing=()
    
    if ! command -v wget &> /dev/null; then
        missing+=("wget")
    fi
    
    if [[ "$EXTRACT_TEXT" == true ]] && ! command -v pdftotext &> /dev/null; then
        missing+=("pdftotext (from poppler)")
    fi
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo -e "${RED}Error: Missing dependencies: ${missing[*]}${NC}"
        echo ""
        echo "Install on macOS with:"
        echo "  brew install wget poppler"
        echo ""
        echo "Or run with --no-extract to skip text extraction"
        exit 1
    fi
}

# Create directory structure
setup_directories() {
    echo -e "${BLUE}Creating directory structure...${NC}"
    mkdir -p "$SOURCE_DIR"/{nes,zx-spectrum,amiga,c64}
    echo -e "${GREEN}✓ Directories created${NC}"
}

# Download with progress and error handling
download_file() {
    local url="$1"
    local output="$2"
    local description="$3"
    
    echo ""
    echo -e "${YELLOW}Downloading: ${description}${NC}"
    echo -e "${BLUE}URL: ${url}${NC}"
    echo -e "${BLUE}Saving to: ${output}${NC}"
    
    # Check if file already exists
    if [[ -f "$output" ]]; then
        echo -e "${YELLOW}⚠ File already exists, skipping download${NC}"
        return 0
    fi
    
    # Download with progress bar
    if wget --show-progress -q -O "$output" "$url"; then
        echo -e "${GREEN}✓ Downloaded successfully${NC}"
        
        # Show file size
        local size=$(du -h "$output" | cut -f1)
        echo -e "${GREEN}  File size: ${size}${NC}"
        
        return 0
    else
        echo -e "${RED}✗ Download failed${NC}"
        # Clean up partial download
        rm -f "$output"
        return 1
    fi
}

# Extract text from PDF
extract_text() {
    local pdf="$1"
    local txt="${pdf%.pdf}.txt"
    
    if [[ "$EXTRACT_TEXT" != true ]]; then
        return 0
    fi
    
    if [[ -f "$txt" ]]; then
        echo -e "${YELLOW}  ⚠ Text file already exists, skipping extraction${NC}"
        return 0
    fi
    
    echo -e "${BLUE}  Extracting text...${NC}"
    
    if pdftotext -layout "$pdf" "$txt" 2>/dev/null; then
        echo -e "${GREEN}  ✓ Text extracted to: $(basename "$txt")${NC}"
        
        # Show line count
        local lines=$(wc -l < "$txt")
        echo -e "${GREEN}    Lines: ${lines}${NC}"
        
        return 0
    else
        echo -e "${RED}  ✗ Text extraction failed${NC}"
        return 1
    fi
}

# Main download sequence
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  Reference Materials Fetcher                               ║"
    echo "║  Code Like It's 198x                                       ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    
    check_dependencies
    setup_directories
    
    local success_count=0
    local fail_count=0
    local extract_count=0
    
    # Track which downloads succeed for summary
    local -a downloaded_files
    
    # ========================================
    # NES Materials
    # ========================================
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  NES (Nintendo Entertainment System)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # NES Programmers Reference Guide (EA 1989)
    if download_file \
        "https://archive.org/download/nes-programmers-reference-guide-by-electronic-arts-1989/nes-programmers-reference-guide-by-electronic-arts-1989.pdf" \
        "$SOURCE_DIR/nes/NES-Programmers-Reference-Guide-EA-1989.pdf" \
        "NES Programmers Reference Guide (Electronic Arts, 1989)"; then
        ((success_count++))
        downloaded_files+=("$SOURCE_DIR/nes/NES-Programmers-Reference-Guide-EA-1989.pdf")
        if extract_text "$SOURCE_DIR/nes/NES-Programmers-Reference-Guide-EA-1989.pdf"; then
            ((extract_count++))
        fi
    else
        ((fail_count++))
    fi
    
    # NES Programmers Reference Guide (Sculptured Software)
    if download_file \
        "https://archive.org/download/nes-programmers-reference-guide-reverse-engineered-by-arti-haroutunian/nes-programmers-reference-guide-reverse-engineered-by-arti-haroutunian.pdf" \
        "$SOURCE_DIR/nes/NES-Programmers-Reference-Guide-Sculptured-Software.pdf" \
        "NES Programmers Reference Guide (Sculptured Software)"; then
        ((success_count++))
        downloaded_files+=("$SOURCE_DIR/nes/NES-Programmers-Reference-Guide-Sculptured-Software.pdf")
        if extract_text "$SOURCE_DIR/nes/NES-Programmers-Reference-Guide-Sculptured-Software.pdf"; then
            ((extract_count++))
        fi
    else
        ((fail_count++))
    fi
    
    # ========================================
    # ZX Spectrum Materials
    # ========================================
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  ZX Spectrum${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # ZX Spectrum BASIC Programming Manual
    if download_file \
        "https://archive.org/download/ZXSpectrumBASICProgramming/ZX%20Spectrum%20BASIC%20Programming.pdf" \
        "$SOURCE_DIR/zx-spectrum/ZX-Spectrum-BASIC-Programming.pdf" \
        "ZX Spectrum BASIC Programming Manual"; then
        ((success_count++))
        downloaded_files+=("$SOURCE_DIR/zx-spectrum/ZX-Spectrum-BASIC-Programming.pdf")
        if extract_text "$SOURCE_DIR/zx-spectrum/ZX-Spectrum-BASIC-Programming.pdf"; then
            ((extract_count++))
        fi
    else
        ((fail_count++))
    fi
    
    # ========================================
    # Amiga Materials
    # ========================================
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  Commodore Amiga${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # AMOS Professional Manual
    if download_file \
        "https://archive.org/download/AmosProfessionalManual/Amos%20Professional%20Manual.pdf" \
        "$SOURCE_DIR/amiga/AMOS-Professional-Manual.pdf" \
        "AMOS Professional Manual"; then
        ((success_count++))
        downloaded_files+=("$SOURCE_DIR/amiga/AMOS-Professional-Manual.pdf")
        if extract_text "$SOURCE_DIR/amiga/AMOS-Professional-Manual.pdf"; then
            ((extract_count++))
        fi
    else
        ((fail_count++))
    fi
    
    # Amiga Hardware Reference Manual (3rd Edition)
    if download_file \
        "https://archive.org/download/amiga-hardware-reference-manual-3rd-edition/Amiga_Hardware_Reference_Manual_3rd_edition.pdf" \
        "$SOURCE_DIR/amiga/Amiga-Hardware-Reference-Manual-3rd-Ed.pdf" \
        "Amiga Hardware Reference Manual (3rd Edition)"; then
        ((success_count++))
        downloaded_files+=("$SOURCE_DIR/amiga/Amiga-Hardware-Reference-Manual-3rd-Ed.pdf")
        if extract_text "$SOURCE_DIR/amiga/Amiga-Hardware-Reference-Manual-3rd-Ed.pdf"; then
            ((extract_count++))
        fi
    else
        ((fail_count++))
    fi
    
    # ========================================
    # Commodore 64 Materials
    # ========================================
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  Commodore 64${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # C64 Programmer's Reference Guide
    if download_file \
        "https://archive.org/download/c64-programmer-ref/c64-programmer-ref.pdf" \
        "$SOURCE_DIR/c64/C64-Programmers-Reference-Guide.pdf" \
        "Commodore 64 Programmer's Reference Guide"; then
        ((success_count++))
        downloaded_files+=("$SOURCE_DIR/c64/C64-Programmers-Reference-Guide.pdf")
        if extract_text "$SOURCE_DIR/c64/C64-Programmers-Reference-Guide.pdf"; then
            ((extract_count++))
        fi
    else
        ((fail_count++))
    fi
    
    # ========================================
    # Summary
    # ========================================
    echo ""
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  Summary${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${GREEN}✓ Successfully downloaded: ${success_count}${NC}"
    
    if [[ "$EXTRACT_TEXT" == true ]]; then
        echo -e "${GREEN}✓ Text files extracted: ${extract_count}${NC}"
    fi
    
    if [[ $fail_count -gt 0 ]]; then
        echo -e "${RED}✗ Failed downloads: ${fail_count}${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}Files saved to:${NC}"
    echo -e "${BLUE}  ${SOURCE_DIR}${NC}"
    
    if [[ ${#downloaded_files[@]} -gt 0 ]]; then
        echo ""
        echo -e "${GREEN}Downloaded files:${NC}"
        for file in "${downloaded_files[@]}"; do
            local basename=$(basename "$file")
            local size=$(du -h "$file" | cut -f1)
            echo -e "${GREEN}  • ${basename} (${size})${NC}"
        done
    fi
    
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo -e "${YELLOW}  1. Review PDFs for relevant technical details${NC}"
    echo -e "${YELLOW}  2. Search extracted .txt files for specific topics${NC}"
    echo -e "${YELLOW}  3. Update quick references with additional findings${NC}"
    
    if [[ "$EXTRACT_TEXT" == true ]]; then
        echo ""
        echo -e "${BLUE}Tip: Search extracted text with:${NC}"
        echo -e "${BLUE}  grep -i 'sprite' ${SOURCE_DIR}/**/*.txt${NC}"
    fi
    
    echo ""
}

# Run main function
main "$@"
