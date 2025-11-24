#!/usr/bin/env python3
"""
ZX Spectrum BASIC Semantic Validator

Performs static analysis on ZX Spectrum BASIC code to catch common errors
that would compile but fail at runtime or produce unexpected behavior.

Usage:
    python3 validate-zx-basic.py <file.bas>

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
    """Parse numeric value from BASIC code."""
    num_str = num_str.strip()

    # Try decimal
    try:
        return int(num_str)
    except ValueError:
        pass

    # Try float (might be used in calculations)
    try:
        return int(float(num_str))
    except ValueError:
        return None

def check_colour_values(lines: List[str]) -> List[ValidationError]:
    """Check for colour values outside 0-7 range."""
    errors = []

    for line_num, line in enumerate(lines, 1):
        # Remove line number
        if re.match(r'^\s*\d+\s+', line):
            line = re.sub(r'^\s*\d+\s+', '', line)

        # Remove comments (REM)
        if 'REM' in line.upper():
            line = line.upper().split('REM')[0]

        # Check INK, PAPER, BORDER commands
        for cmd in ['INK', 'PAPER', 'BORDER']:
            pattern = rf'\b{cmd}\s+(\d+)'
            matches = re.finditer(pattern, line, re.IGNORECASE)

            for match in matches:
                value = parse_number(match.group(1))
                if value is not None and (value < 0 or value > 7):
                    errors.append(ValidationError(
                        line_num,
                        f"{cmd} colour value {value} outside valid range 0-7"
                    ))

    return errors

def check_bright_flash_values(lines: List[str]) -> List[ValidationError]:
    """Check for BRIGHT/FLASH values not 0 or 1."""
    errors = []

    for line_num, line in enumerate(lines, 1):
        # Remove line number
        if re.match(r'^\s*\d+\s+', line):
            line = re.sub(r'^\s*\d+\s+', '', line)

        # Remove comments
        if 'REM' in line.upper():
            line = line.upper().split('REM')[0]

        # Check BRIGHT and FLASH commands
        for cmd in ['BRIGHT', 'FLASH', 'INVERSE', 'OVER']:
            pattern = rf'\b{cmd}\s+(\d+)'
            matches = re.finditer(pattern, line, re.IGNORECASE)

            for match in matches:
                value = parse_number(match.group(1))
                if value is not None and value not in [0, 1]:
                    errors.append(ValidationError(
                        line_num,
                        f"{cmd} value {value} must be 0 or 1 only"
                    ))

    return errors

def check_plot_coordinates(lines: List[str]) -> List[ValidationWarning]:
    """Warn about PLOT coordinates outside visible range."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        # Remove line number
        if re.match(r'^\s*\d+\s+', line):
            line = re.sub(r'^\s*\d+\s+', '', line)

        # Remove comments
        if 'REM' in line.upper():
            line = line.upper().split('REM')[0]

        # Check PLOT commands with literal coordinates
        plot_pattern = r'\bPLOT\s+(\d+)\s*,\s*(\d+)'
        matches = re.finditer(plot_pattern, line, re.IGNORECASE)

        for match in matches:
            x = parse_number(match.group(1))
            y = parse_number(match.group(2))

            if x is not None and (x < 0 or x > 255):
                warnings.append(ValidationWarning(
                    line_num,
                    f"PLOT X coordinate {x} outside valid range 0-255"
                ))

            if y is not None and (y < 0 or y > 175):
                warnings.append(ValidationWarning(
                    line_num,
                    f"PLOT Y coordinate {y} outside valid range 0-175 (visible area)"
                ))

    return warnings

def check_print_at_values(lines: List[str]) -> List[ValidationWarning]:
    """Warn about PRINT AT values outside screen range."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        # Remove line number
        if re.match(r'^\s*\d+\s+', line):
            line = re.sub(r'^\s*\d+\s+', '', line)

        # Remove comments
        if 'REM' in line.upper():
            line = line.upper().split('REM')[0]

        # Check PRINT AT with literal values
        at_pattern = r'\bPRINT\s+AT\s+(\d+)\s*,\s*(\d+)'
        matches = re.finditer(at_pattern, line, re.IGNORECASE)

        for match in matches:
            row = parse_number(match.group(1))
            col = parse_number(match.group(2))

            if row is not None and (row < 0 or row > 21):
                warnings.append(ValidationWarning(
                    line_num,
                    f"PRINT AT row {row} outside valid range 0-21 (22 text rows)"
                ))

            if col is not None and (col < 0 or col > 31):
                warnings.append(ValidationWarning(
                    line_num,
                    f"PRINT AT column {col} outside valid range 0-31 (32 text columns)"
                ))

    return warnings

def check_screen_address_formula(lines: List[str]) -> List[ValidationWarning]:
    """Warn about potentially incorrect screen address calculations."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        # Look for screen bitmap base address (16384 or $4000)
        if '16384' in line or '4000' in line:
            code = line.upper()

            # Check if they're doing address calculations
            if 'POKE' in code or 'PEEK' in code:
                # Check for common wrong patterns (linear address calculation)
                # Correct formula includes: (y AND 7), (y AND 56), (y AND 192)
                if 'AND' not in code or ('AND 7' not in code and 'AND 56' not in code and 'AND 192' not in code):
                    # They might be calculating linearly (wrong!)
                    if '*' in code or '+' in code:
                        warnings.append(ValidationWarning(
                            line_num,
                            "Screen bitmap address calculation detected - ensure using thirds formula, not linear (see ZX-SPECTRUM-MEMORY-AND-GRAPHICS-REFERENCE.md)"
                        ))

    return warnings

def check_attribute_address(lines: List[str]) -> List[ValidationWarning]:
    """Check attribute address calculations."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        # Look for attribute base address (22528 or $5800)
        if '22528' in line or '5800' in line:
            code = line.upper()

            # Attributes are linear: 22528 + (row * 32) + col
            # Check if they're using wrong calculation
            if 'POKE' in code or 'PEEK' in code:
                # Should see row * 32 or equivalent
                # Wrong patterns: using thirds formula for attributes
                if 'AND 7' in code or 'AND 56' in code or 'AND 192' in code:
                    warnings.append(ValidationWarning(
                        line_num,
                        "Attribute address calculation using thirds formula - attributes are LINEAR, not like bitmap"
                    ))

    return warnings

def check_inkey_usage(lines: List[str]) -> List[ValidationWarning]:
    """Check for common INKEY$ mistakes."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        code = line.upper()

        # Check for INKEY$ without $
        if 'INKEY' in code and 'INKEY$' not in code:
            warnings.append(ValidationWarning(
                line_num,
                "Found 'INKEY' without '$' - correct syntax is INKEY$ (with dollar sign)"
            ))

        # Check for comparison without checking empty string first
        # Common bug: IF INKEY$="q" without checking if INKEY$<>""
        if 'IF' in code and 'INKEY$=' in code.replace(' ', ''):
            # Check if there's an empty string check
            if '""' not in line:
                warnings.append(ValidationWarning(
                    line_num,
                    "INKEY$ comparison without checking for empty string first - may miss key presses (check IF INKEY$<>\"\" first)"
                ))

    return warnings

def check_poke_values(lines: List[str]) -> List[ValidationError]:
    """Check for POKE values outside 0-255 range."""
    errors = []

    for line_num, line in enumerate(lines, 1):
        # Remove line number
        if re.match(r'^\s*\d+\s+', line):
            line = re.sub(r'^\s*\d+\s+', '', line)

        # Remove comments
        if 'REM' in line.upper():
            line = line.upper().split('REM')[0]

        # Find POKE statements with literal values
        # Pattern: POKE address, value
        poke_pattern = r'\bPOKE\s+\d+\s*,\s*(\d+)'
        matches = re.finditer(poke_pattern, line, re.IGNORECASE)

        for match in matches:
            value = parse_number(match.group(1))
            if value is not None and (value < 0 or value > 255):
                errors.append(ValidationError(
                    line_num,
                    f"POKE value {value} outside valid range 0-255 (single byte)"
                ))

    return errors

def check_array_dim(lines: List[str]) -> List[ValidationWarning]:
    """Check for array usage without DIM."""
    warnings = []

    # Track which arrays have been DIM'd
    dimmed_arrays = set()

    for line_num, line in enumerate(lines, 1):
        code = line.upper()

        # Find DIM statements
        dim_pattern = r'\bDIM\s+([A-Z][A-Z0-9]*\$?)\s*\('
        dim_matches = re.finditer(dim_pattern, code)
        for match in dim_matches:
            dimmed_arrays.add(match.group(1))

        # Find array usage (but not DIM)
        if 'DIM' not in code:
            array_pattern = r'\b([A-Z][A-Z0-9]*\$?)\s*\('
            array_matches = re.finditer(array_pattern, code)
            for match in array_matches:
                array_name = match.group(1)

                # Check if it's not a function call (like SIN, COS, etc.)
                if array_name not in ['SIN', 'COS', 'TAN', 'ATN', 'EXP', 'LN', 'SQR', 'ABS', 'INT', 'VAL', 'LEN', 'CODE', 'PEEK', 'POINT', 'CHR', 'STR', 'INKEY']:
                    if array_name not in dimmed_arrays:
                        warnings.append(ValidationWarning(
                            line_num,
                            f"Array '{array_name}' used without DIM declaration (ZX Spectrum auto-dims to size 10, but explicit DIM is better)"
                        ))
                        # Only warn once per array
                        dimmed_arrays.add(array_name)

    return warnings

def check_string_slicing(lines: List[str]) -> List[ValidationWarning]:
    """Check for common string slicing errors."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        # Check for string slicing syntax
        # Correct: string$(start TO end)
        # Common error: string$(start:end) or string$(start..end)

        if ':' in line and '$' in line and '(' in line:
            # Might be using wrong syntax
            if 'TO' not in line.upper():
                warnings.append(ValidationWarning(
                    line_num,
                    "Possible incorrect string slicing syntax - ZX Spectrum uses 'string$(start TO end)' not colons or dots"
                ))

    return warnings

def validate_zx_basic(filepath: str) -> Tuple[List[ValidationError], List[ValidationWarning]]:
    """Run all validation checks on ZX Spectrum BASIC file."""
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
    errors.extend(check_colour_values(lines))
    errors.extend(check_bright_flash_values(lines))
    errors.extend(check_poke_values(lines))

    warnings.extend(check_plot_coordinates(lines))
    warnings.extend(check_print_at_values(lines))
    warnings.extend(check_screen_address_formula(lines))
    warnings.extend(check_attribute_address(lines))
    warnings.extend(check_inkey_usage(lines))
    warnings.extend(check_array_dim(lines))
    warnings.extend(check_string_slicing(lines))

    return errors, warnings

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 validate-zx-basic.py <file.bas>")
        sys.exit(1)

    filepath = sys.argv[1]

    print(f"\n🔍 Validating ZX Spectrum BASIC: {filepath}\n")

    errors, warnings = validate_zx_basic(filepath)

    # Print errors
    if errors:
        print("❌ ERRORS found:\n")
        for error in errors:
            print(f"   ❌ Line {error.line_num}: {error.message}")
        print(f"\n{len(errors)} error(s) found. Fix these before committing.\n")

    # Print warnings
    if warnings:
        print("⚠️  WARNINGS found:\n")
        for warning in warnings:
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
