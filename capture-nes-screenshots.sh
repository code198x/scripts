#!/bin/bash

# NES Screenshot Capture Script for FCEUX
# Captures screenshots for all NES lessons

set -e

# Paths
CODE_SAMPLES_ROOT="/Users/stevehill/Projects/Code198x/code-samples/nintendo-entertainment-system/phase-1/tier-1"
WEBSITE_IMAGES_ROOT="/Users/stevehill/Projects/Code198x/website/public/images/nintendo-entertainment-system/phase-1/tier-1"
LUA_SCRIPT="/Users/stevehill/Projects/Code198x/scripts/fceux-capture.lua"

# Check for FCEUX
if ! command -v fceux &> /dev/null; then
    echo "ERROR: FCEUX not found. Please install FCEUX."
    exit 1
fi

# Statistics
SUCCESS_COUNT=0
FAILURE_COUNT=0
TOTAL_COUNT=0

echo "========================================"
echo "NES Screenshot Capture"
echo "========================================"
echo ""

# Process each lesson directory
for lesson_dir in "$CODE_SAMPLES_ROOT"/lesson-*; do
    if [ ! -d "$lesson_dir" ]; then
        continue
    fi

    lesson_num=$(basename "$lesson_dir")
    echo "Processing $lesson_num..."

    # Find .nes file
    nes_file=$(find "$lesson_dir" -name "*.nes" -type f | head -1)

    if [ -z "$nes_file" ]; then
        echo "  ⚠️  No .nes file found, skipping"
        ((TOTAL_COUNT++))
        ((FAILURE_COUNT++))
        continue
    fi

    # Get base filename for screenshot
    base_name=$(basename "$nes_file" .nes)

    # Create output directory
    output_dir="$WEBSITE_IMAGES_ROOT/$lesson_num"
    mkdir -p "$output_dir"

    # Output screenshot path
    output_file="$output_dir/${base_name}.png"

    echo "  ROM: $(basename "$nes_file")"
    echo "  Output: $output_file"

    # Run FCEUX with Lua script
    # Use default snapshot directory, then move file
    fceux --nogui --loadlua "$LUA_SCRIPT" "$nes_file" 2>/dev/null || true

    # FCEUX saves to ~/.fceux/snaps/ by default
    # Find the most recent screenshot
    latest_snap=$(find ~/.fceux/snaps -name "*.png" -type f -newermt "10 seconds ago" 2>/dev/null | head -1)

    if [ -n "$latest_snap" ] && [ -f "$latest_snap" ]; then
        # Move to destination
        mv "$latest_snap" "$output_file"

        # Check file size
        file_size=$(stat -f%z "$output_file" 2>/dev/null || stat -c%s "$output_file" 2>/dev/null)

        if [ "$file_size" -gt 1000 ]; then
            echo "  ✅ Success (${file_size} bytes)"
            ((SUCCESS_COUNT++))
        else
            echo "  ❌ Failed (file too small: ${file_size} bytes)"
            ((FAILURE_COUNT++))
        fi
    else
        echo "  ❌ Failed (no screenshot generated)"
        ((FAILURE_COUNT++))
    fi

    ((TOTAL_COUNT++))
    echo ""
done

echo "========================================"
echo "Summary"
echo "========================================"
echo "Total lessons processed: $TOTAL_COUNT"
echo "Successful captures: $SUCCESS_COUNT"
echo "Failed captures: $FAILURE_COUNT"
echo ""

# List all generated screenshots
if [ "$SUCCESS_COUNT" -gt 0 ]; then
    echo "Generated screenshots:"
    find "$WEBSITE_IMAGES_ROOT" -name "*.png" -type f -exec ls -lh {} \;
fi
