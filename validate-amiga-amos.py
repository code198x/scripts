#!/usr/bin/env python3
"""
Amiga AMOS Semantic Validator

Performs static analysis on AMOS BASIC code to catch common errors
that would compile but fail at runtime or produce unexpected behavior.

Usage:
    python3 validate-amos.py <file.amos>

Exit codes:
    0 - No errors (warnings are non-blocking)
    1 - Errors found (must be fixed)
"""

import sys
import re
from typing import List, Tuple, Optional

class ValidationError:
    def __init__(self, line_num: int, message: str):
        self.line_num = line_num
        self.message = message

class ValidationWarning:
    def __init__(self, line_num: int, message: str):
        self.line_num = line_num
        self.message = message

def parse_number(num_str: str) -> Optional[int]:
    """Parse numeric value from AMOS code."""
    num_str = num_str.strip()

    # Handle hex ($RGB format for colors)
    if num_str.startswith('$'):
        try:
            return int(num_str[1:], 16)
        except ValueError:
            return None

    # Try decimal
    try:
        return int(num_str)
    except ValueError:
        pass

    # Try float
    try:
        return int(float(num_str))
    except ValueError:
        return None

def check_sprite_numbers(lines: List[str]) -> List[ValidationError]:
    """Check for sprite numbers outside 0-7 range (hardware sprites)."""
    errors = []

    for line_num, line in enumerate(lines, 1):
        # Remove comments (Rem or ')
        code = line
        if 'Rem' in code or "'" in code:
            if 'Rem' in code:
                code = code.split('Rem')[0]
            if "'" in code:
                code = code.split("'")[0]

        code_upper = code.upper()

        # Check Sprite commands
        sprite_pattern = r'\bSPRITE\s+(\d+)'
        matches = re.finditer(sprite_pattern, code_upper)

        for match in matches:
            sprite_num = parse_number(match.group(1))
            if sprite_num is not None and (sprite_num < 0 or sprite_num > 7):
                errors.append(ValidationError(
                    line_num,
                    f"Hardware sprite number {sprite_num} outside valid range 0-7 (Amiga OCS has 8 sprites)"
                ))

    return errors

def check_audio_channels(lines: List[str]) -> List[ValidationError]:
    """Check for audio channel numbers outside 0-3 range."""
    errors = []

    for line_num, line in enumerate(lines, 1):
        code = line
        if 'Rem' in code or "'" in code:
            if 'Rem' in code:
                code = code.split('Rem')[0]
            if "'" in code:
                code = code.split("'")[0]

        code_upper = code.upper()

        # Check audio-related commands
        # Note: AMOS often uses implicit channels, so this is best-effort
        audio_patterns = [
            r'\bSAM PLAY\s+(\d+)',
            r'\bCHANNEL\s+(\d+)',
            r'\bVOICE\s+(\d+)',
        ]

        for pattern in audio_patterns:
            matches = re.finditer(pattern, code_upper)
            for match in matches:
                channel = parse_number(match.group(1))
                if channel is not None and (channel < 0 or channel > 3):
                    errors.append(ValidationError(
                        line_num,
                        f"Audio channel {channel} outside valid range 0-3 (Paula has 4 channels)"
                    ))

    return errors

def check_colour_values(lines: List[str]) -> List[ValidationWarning]:
    """Warn about colour values outside $000-$FFF range."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        code = line
        if 'Rem' in code or "'" in code:
            if 'Rem' in code:
                code = code.split('Rem')[0]
            if "'" in code:
                code = code.split("'")[0]

        code_upper = code.upper()

        # Check COLOUR command with $RGB values
        colour_pattern = r'\bCOLOUR\s+\d+\s*,\s*\$([0-9A-F]+)'
        matches = re.finditer(colour_pattern, code_upper)

        for match in matches:
            color_val = match.group(1)
            try:
                color_int = int(color_val, 16)
                if color_int > 0xFFF:
                    warnings.append(ValidationWarning(
                        line_num,
                        f"Colour value ${color_val} exceeds $FFF (Amiga OCS uses 12-bit RGB: $RGB format)"
                    ))
            except ValueError:
                pass

    return warnings

def check_screen_modes(lines: List[str]) -> List[ValidationWarning]:
    """Check for potentially invalid screen modes."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        code = line
        if 'Rem' in code or "'" in code:
            if 'Rem' in code:
                code = code.split('Rem')[0]
            if "'" in code:
                code = code.split("'")[0]

        code_upper = code.upper()

        # Check Screen Open command
        # Pattern: Screen Open screen,width,height,colours,mode
        screen_pattern = r'\bSCREEN\s+OPEN\s+\d+\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)'
        matches = re.finditer(screen_pattern, code_upper)

        for match in matches:
            width = parse_number(match.group(1))
            height = parse_number(match.group(2))
            colours = parse_number(match.group(3))

            # Check common valid modes
            if width is not None and width not in [320, 640]:
                warnings.append(ValidationWarning(
                    line_num,
                    f"Screen width {width} unusual - common widths are 320 (lowres) or 640 (hires)"
                ))

            if height is not None and height not in [200, 256, 400, 512]:
                warnings.append(ValidationWarning(
                    line_num,
                    f"Screen height {height} unusual - common heights are 200/256 (NTSC/PAL) or 400/512 (interlaced)"
                ))

            if colours is not None:
                # Check if colour count matches bitplane depth
                # 2, 4, 8, 16, 32, 64 are valid (2^n where n=1-6)
                if colours not in [2, 4, 8, 16, 32, 64]:
                    warnings.append(ValidationWarning(
                        line_num,
                        f"Colour count {colours} must be power of 2 (2, 4, 8, 16, 32, or 64 for OCS)"
                    ))

    return warnings

def check_palette_registers(lines: List[str]) -> List[ValidationWarning]:
    """Check for palette register access outside valid range."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        code = line
        if 'Rem' in code or "'" in code:
            if 'Rem' in code:
                code = code.split('Rem')[0]
            if "'" in code:
                code = code.split("'")[0]

        code_upper = code.upper()

        # Check COLOUR register,value pattern
        colour_pattern = r'\bCOLOUR\s+(\d+)\s*,'
        matches = re.finditer(colour_pattern, code_upper)

        for match in matches:
            register = parse_number(match.group(1))
            if register is not None and register > 31:
                warnings.append(ValidationWarning(
                    line_num,
                    f"Palette register {register} exceeds typical range - OCS screens use registers 0-31 (32 colours max in lowres)"
                ))

    return warnings

def check_bob_sprite_confusion(lines: List[str]) -> List[ValidationWarning]:
    """Warn about potential confusion between Bobs and Sprites."""
    warnings = []

    sprite_commands = set()
    bob_commands = set()

    for line_num, line in enumerate(lines, 1):
        code = line
        if 'Rem' in code or "'" in code:
            if 'Rem' in code:
                code = code.split('Rem')[0]
            if "'" in code:
                code = code.split("'")[0]

        code_upper = code.upper()

        # Track sprite usage
        if re.search(r'\bSPRITE\s+', code_upper):
            sprite_commands.add(line_num)

        # Track bob usage
        if re.search(r'\bBOB\s+', code_upper):
            bob_commands.add(line_num)

    # If mixing Sprites and Bobs, provide informational warning
    if sprite_commands and bob_commands:
        warnings.append(ValidationWarning(
            0,
            "Using both Sprites and Bobs - Remember: Sprites=hardware (8 max, 16px wide, fast), Bobs=software (unlimited, any size, slower)"
        ))

    return warnings

def check_screen_swap_without_double_buffer(lines: List[str]) -> List[ValidationWarning]:
    """Warn about Screen Swap without Double Buffer."""
    warnings = []

    has_double_buffer = False
    screen_swap_lines = []

    for line_num, line in enumerate(lines, 1):
        code = line
        if 'Rem' in code or "'" in code:
            if 'Rem' in code:
                code = code.split('Rem')[0]
            if "'" in code:
                code = code.split("'")[0]

        code_upper = code.upper()

        if 'DOUBLE BUFFER' in code_upper:
            has_double_buffer = True

        if 'SCREEN SWAP' in code_upper:
            screen_swap_lines.append(line_num)

    if screen_swap_lines and not has_double_buffer:
        for line_num in screen_swap_lines:
            warnings.append(ValidationWarning(
                line_num,
                "Screen Swap used without Double Buffer command - double buffering may not work correctly"
            ))

    return warnings

def check_wait_vbl_in_loop(lines: List[str]) -> List[ValidationWarning]:
    """Check for missing Wait Vbl in animation loops."""
    warnings = []

    # Look for loops without Wait Vbl
    in_loop = False
    loop_start = 0
    loop_lines = []
    has_wait_vbl = False

    for line_num, line in enumerate(lines, 1):
        code = line
        if 'Rem' in code or "'" in code:
            if 'Rem' in code:
                code = code.split('Rem')[0]
            if "'" in code:
                code = code.split("'")[0]

        code_upper = code.upper()

        # Detect loop starts
        if any(keyword in code_upper for keyword in ['FOR ', 'WHILE ', 'REPEAT', 'DO ']):
            in_loop = True
            loop_start = line_num
            loop_lines = [line_num]
            has_wait_vbl = False
        elif in_loop:
            loop_lines.append(line_num)

            # Check for Wait Vbl in loop
            if 'WAIT VBL' in code_upper or 'WAIT ' in code_upper:
                has_wait_vbl = True

            # Detect loop ends
            if any(keyword in code_upper for keyword in ['NEXT ', 'WEND', 'UNTIL ', 'LOOP']):
                # Check if this loop has graphics commands but no Wait Vbl
                has_graphics = any('PLOT' in lines[i-1].upper() or
                                    'DRAW' in lines[i-1].upper() or
                                    'BOX' in lines[i-1].upper() or
                                    'BAR' in lines[i-1].upper() or
                                    'SPRITE' in lines[i-1].upper() or
                                    'BOB' in lines[i-1].upper()
                                    for i in loop_lines if i <= len(lines))

                if has_graphics and not has_wait_vbl:
                    warnings.append(ValidationWarning(
                        loop_start,
                        "Animation loop without Wait Vbl - may run too fast or cause screen tearing"
                    ))

                in_loop = False

    return warnings

def validate_amos(filepath: str) -> Tuple[List[ValidationError], List[ValidationWarning]]:
    """Run all validation checks on AMOS file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    errors = []
    warnings = []

    # Run all checks
    errors.extend(check_sprite_numbers(lines))
    errors.extend(check_audio_channels(lines))

    warnings.extend(check_colour_values(lines))
    warnings.extend(check_screen_modes(lines))
    warnings.extend(check_palette_registers(lines))
    warnings.extend(check_bob_sprite_confusion(lines))
    warnings.extend(check_screen_swap_without_double_buffer(lines))
    warnings.extend(check_wait_vbl_in_loop(lines))

    return errors, warnings

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 validate-amos.py <file.amos>")
        sys.exit(1)

    filepath = sys.argv[1]

    print(f"\n🔍 Validating AMOS: {filepath}\n")

    errors, warnings = validate_amos(filepath)

    # Print errors
    if errors:
        print("❌ ERRORS found:\n")
        for error in errors:
            if error.line_num == 0:
                print(f"   ❌ {error.message}")
            else:
                print(f"   ❌ Line {error.line_num}: {error.message}")
        print(f"\n{len(errors)} error(s) found. Fix these before committing.\n")

    # Print warnings
    if warnings:
        print("⚠️  WARNINGS found:\n")
        for warning in warnings:
            if warning.line_num == 0:
                print(f"   ⚠️  {warning.message}")
            else:
                print(f"   ⚠️  Line {warning.line_num}: {warning.message}")
        print(f"\n{len(warnings)} warning(s) found (non-blocking).\n")

    # Success message
    if not errors and not warnings:
        print("✅ No issues found!\n")
    elif not errors:
        print("✅ No errors found (warnings are non-blocking).\n")

    # Exit code
    sys.exit(1 if errors else 0)

if __name__ == '__main__':
    main()
