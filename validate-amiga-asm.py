#!/usr/bin/env python3
"""
Amiga 68000 Assembly Semantic Validator

Performs static analysis on 68000 assembly code to catch common errors
that would compile but fail at runtime or produce unexpected behavior.

Usage:
    python3 validate-68k-asm.py <file.asm>

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

def parse_address(addr_str: str) -> Optional[int]:
    """Parse hex or decimal address string to integer."""
    addr_str = addr_str.strip().upper()

    # Remove $ prefix
    if addr_str.startswith('$'):
        try:
            return int(addr_str[1:], 16)
        except ValueError:
            return None

    # Try hex with 0x prefix
    if addr_str.startswith('0X'):
        try:
            return int(addr_str, 16)
        except ValueError:
            return None

    # Try decimal
    try:
        return int(addr_str, 10)
    except ValueError:
        return None

def check_chip_ram_requirement(lines: List[str]) -> List[ValidationWarning]:
    """Warn about operations that require Chip RAM."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # Check for copper list references
        if 'COPPER' in line_upper or 'COP1LC' in line_upper or 'COP2LC' in line_upper:
            warnings.append(ValidationWarning(
                line_num,
                "Copper lists must be in Chip RAM - ensure data is in Chip RAM range"
            ))

        # Check for bitplane pointers
        if 'BPL' in line_upper and 'PTR' in line_upper:
            warnings.append(ValidationWarning(
                line_num,
                "Bitplane data must be in Chip RAM - ensure graphics data allocated in Chip RAM"
            ))

        # Check for audio sample references
        if 'AUD' in line_upper and ('PTR' in line_upper or 'LC' in line_upper):
            warnings.append(ValidationWarning(
                line_num,
                "Audio samples must be in Chip RAM - Paula can only DMA from Chip RAM"
            ))

    return warnings

def check_word_alignment(lines: List[str]) -> List[ValidationWarning]:
    """Check for data that should be word-aligned."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # Check for EVEN directive usage
        # Look for DC.L or DC.W after odd-sized data
        if 'DC.B' in line_upper:
            # Next non-comment line should check for EVEN
            for offset in range(1, 5):
                if line_num + offset <= len(lines):
                    next_line = lines[line_num + offset - 1]
                    if ';' in next_line:
                        next_line = next_line[:next_line.index(';')]
                    next_upper = next_line.strip().upper()

                    if not next_upper:
                        continue
                    if 'EVEN' in next_upper or 'CNOP' in next_upper:
                        break
                    if 'DC.W' in next_upper or 'DC.L' in next_upper:
                        warnings.append(ValidationWarning(
                            line_num,
                            "DC.B before DC.W/DC.L without EVEN - may cause address error on 68000"
                        ))
                        break
                    break

    return warnings

def check_register_usage(lines: List[str]) -> List[ValidationWarning]:
    """Check for potentially problematic register usage."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # Check for A7 usage (stack pointer)
        if re.search(r'\bA7\b', line_upper):
            if not re.search(r'\bMOVE\s+.*,\s*A7\b', line_upper):
                warnings.append(ValidationWarning(
                    line_num,
                    "Using A7 directly - A7 is the stack pointer (SP), ensure intentional"
                ))

        # Check for D7/A6 in tight loops (common scratch registers)
        if 'DBF' in line_upper or 'DBRA' in line_upper:
            # In a loop, check if using D7/A6 which might be modified
            pass  # Could expand this check

    return warnings

def check_supervisor_mode(lines: List[str]) -> List[ValidationWarning]:
    """Warn about supervisor-mode instructions."""
    warnings = []

    supervisor_instructions = ['MOVE', 'USP', 'RTE', 'RESET', 'STOP']

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # Check for privileged instructions
        if 'MOVE' in line_upper and 'USP' in line_upper:
            warnings.append(ValidationWarning(
                line_num,
                "MOVE USP is privileged - requires supervisor mode (will trap in user mode)"
            ))

        if re.search(r'\bRTE\b', line_upper):
            warnings.append(ValidationWarning(
                line_num,
                "RTE is privileged - requires supervisor mode (use RTS for normal subroutines)"
            ))

    return warnings

def check_dbcc_loop_structure(lines: List[str]) -> List[ValidationWarning]:
    """Check for proper DBcc loop structure."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # Check for DBF/DBRA usage
        dbf_match = re.search(r'\b(DBF|DBRA)\b\s+D(\d)', line_upper)
        if dbf_match:
            reg_num = dbf_match.group(2)
            # Check if register was initialized
            # Look back up to 20 lines
            found_init = False
            for offset in range(1, min(20, line_num)):
                prev_line = lines[line_num - offset - 1]
                if ';' in prev_line:
                    prev_line = prev_line[:prev_line.index(';')]
                prev_upper = prev_line.upper()

                if f'MOVE' in prev_upper and f'D{reg_num}' in prev_upper:
                    found_init = True
                    break

            if not found_init:
                warnings.append(ValidationWarning(
                    line_num,
                    f"DBF D{reg_num} without visible initialization - ensure counter initialized before loop"
                ))

    return warnings

def check_custom_chip_registers(lines: List[str]) -> List[ValidationWarning]:
    """Check for custom chip register access."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # Check for direct $DFF addresses
        if '$DFF' in line_upper:
            # Writing to custom chips
            if 'MOVE' in line_upper:
                warnings.append(ValidationWarning(
                    line_num,
                    "Direct custom chip access ($DFF...) - ensure correct register and blitter/copper state"
                ))

    return warnings

def check_lea_vs_move(lines: List[str]) -> List[ValidationWarning]:
    """Suggest using LEA instead of MOVE for address loading."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # Check for MOVE.L #address,An patterns (could use LEA)
        if re.search(r'MOVE\.L\s+#\$[0-9A-F]+\s*,\s*A\d', line_upper):
            warnings.append(ValidationWarning(
                line_num,
                "MOVE.L #address,An can be replaced with LEA for better performance (4 bytes vs 6 bytes)"
            ))

    return warnings

def check_bsr_range(lines: List[str]) -> List[ValidationWarning]:
    """Check for BSR vs JSR usage."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # BSR has limited range (16-bit displacement on 68000)
        if re.search(r'\bBSR\b', line_upper):
            warnings.append(ValidationWarning(
                line_num,
                "BSR has 16-bit range limit (±32KB) - use JSR for far calls or if unsure"
            ))

    return warnings

def validate_68k_asm(filepath: str) -> Tuple[List[ValidationError], List[ValidationWarning]]:
    """Run all validation checks on 68000 assembly file."""
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
    warnings.extend(check_chip_ram_requirement(lines))
    warnings.extend(check_word_alignment(lines))
    warnings.extend(check_register_usage(lines))
    warnings.extend(check_supervisor_mode(lines))
    warnings.extend(check_dbcc_loop_structure(lines))
    warnings.extend(check_custom_chip_registers(lines))
    warnings.extend(check_lea_vs_move(lines))
    warnings.extend(check_bsr_range(lines))

    return errors, warnings

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 validate-68k-asm.py <file.asm>")
        sys.exit(1)

    filepath = sys.argv[1]

    print(f"\n🔍 Validating 68000 Assembly: {filepath}\n")

    errors, warnings = validate_68k_asm(filepath)

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
