#!/usr/bin/env python3
"""
NES Screenshot Capture using nes-py
Runs a NES ROM for specified frames and saves a screenshot
"""

import sys
import os
from nes_py import NESEnv
from PIL import Image

def capture_screenshot(rom_path, output_path, frames=300):
    """
    Run NES ROM and capture screenshot after specified frames
    
    Args:
        rom_path: Path to .nes ROM file
        output_path: Path to save PNG screenshot
        frames: Number of frames to run before capturing (default 300 = 5 seconds)
    """
    try:
        # Create NES environment
        env = NESEnv(rom_path)
        env.reset()
        
        # Run for specified number of frames
        for frame in range(frames):
            state, reward, done, info = env.step(0)  # Action 0 = no input
            
            if done:
                break
        
        # Get current screen
        screen = env.screen
        
        # Convert to PIL Image and save
        img = Image.fromarray(screen)
        
        # Create output directory if needed
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        # Save screenshot
        img.save(output_path)
        
        # Close environment
        env.close()
        
        # Verify file was created
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            print(f"✓ Screenshot saved: {output_path}")
            return True
        else:
            print(f"✗ Screenshot file too small or missing")
            return False
            
    except Exception as e:
        print(f"✗ Error capturing screenshot: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: nes-screenshot.py <rom_file> <output_file> [frames]")
        sys.exit(1)
    
    rom_file = sys.argv[1]
    output_file = sys.argv[2]
    frames = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    
    if not os.path.exists(rom_file):
        print(f"✗ ROM file not found: {rom_file}")
        sys.exit(1)
    
    success = capture_screenshot(rom_file, output_file, frames)
    sys.exit(0 if success else 1)
