#!/bin/bash
# Batch NES Screenshot Capture
# This script processes all NES lessons and captures screenshots
# 
# MANUAL MODE: Opens each ROM, waits, user presses F12, then closes
# This is the most reliable method due to FCEUX limitations

set -e

CODE_SAMPLES="/Users/stevehill/Projects/Code198x/code-samples/nintendo-entertainment-system/phase-1/tier-1"
WEBSITE_IMAGES="/Users/stevehill/Projects/Code198x/website/public/images/nintendo-entertainment-system/phase-1/tier-1"

SUCCESS=0
FAILURE=0
TOTAL=0

echo "========================================"
echo "NES Screenshot Batch Capture"
echo "========================================"
echo ""
echo "Mode: Semi-automated (F12 after ROM loads)"
echo ""

for lesson_dir in "$CODE_SAMPLES"/lesson-*; do
    if [ ! -d "$lesson_dir" ]; then
        continue
    fi
    
    lesson_num=$(basename "$lesson_dir")
    nes_file=$(find "$lesson_dir" -name "*.nes" -type f | head -1)
    
    if [ -z "$nes_file" ]; then
        echo "⚠️  $lesson_num: No .nes file found"
        ((FAILURE++))
        ((TOTAL++))
        continue
    fi
    
    base_name=$(basename "$nes_file" .nes)
    output_dir="$WEBSITE_IMAGES/$lesson_num"
    output_file="$output_dir/${base_name}.png"
    
    # Skip if already exists
    if [ -f "$output_file" ]; then
        echo "✓ $lesson_num: Screenshot exists, skipping"
        ((SUCCESS++))
        ((TOTAL++))
        continue
    fi
    
    mkdir -p "$output_dir"
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Processing: $lesson_num"
    echo "ROM: $(basename "$nes_file")"
    echo ""
    echo "Instructions:"
    echo "  1. ROM will launch in FCEUX"
    echo "  2. Wait for it to run (~5 seconds)"
    echo "  3. Press F12 to take screenshot"
    echo "  4. Close FCEUX window"
    echo ""
    read -p "Press ENTER to launch ROM..." 
    
    # Clear old snaps
    rm -f ~/.fceux/snaps/*.png 2>/dev/null
    
    # Launch FCEUX
    fceux "$nes_file" 2>/dev/null
    
    # Check for screenshot
    latest=$(ls -t ~/.fceux/snaps/*.png 2>/dev/null | head -1)
    
    if [ -n "$latest" ] && [ -f "$latest" ]; then
        mv "$latest" "$output_file"
        size=$(stat -f%z "$output_file")
        echo "✓ Success: $output_file ($size bytes)"
        ((SUCCESS++))
    else
        echo "✗ Failed: No screenshot found"
        ((FAILURE++))
    fi
    
    ((TOTAL++))
    echo ""
done

echo "========================================"
echo "Summary"
echo "========================================"
echo "Total: $TOTAL"
echo "Success: $SUCCESS"
echo "Failed: $FAILURE"
echo ""

if [ "$SUCCESS" -gt 0 ]; then
    echo "Screenshots saved to:"
    echo "  $WEBSITE_IMAGES"
    echo ""
    find "$WEBSITE_IMAGES" -name "*.png" -type f -exec ls -lh {} \; | head -10
fi
