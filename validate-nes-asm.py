#!/usr/bin/env python3
"""
NES Assembly Semantic Validator

Performs static analysis on NES 6502 assembly code to catch common errors
that would compile but fail at runtime or produce unexpected behavior.

Usage:
    python3 validate-nes-asm.py <file.asm>

Exit codes:
    0 - No errors (warnings are non-blocking)
    1 - Errors found (must be fixed)
"""

import sys
import re
from typing import List, Tuple, Optional

# Valid 6502 instructions (NES does not have decimal mode)
VALID_6502_INSTRUCTIONS = {
    # Load/Store
    'LDA', 'LDX', 'LDY', 'STA', 'STX', 'STY',
    # Transfer
    'TAX', 'TAY', 'TXA', 'TYA', 'TSX', 'TXS',
    # Stack
    'PHA', 'PHP', 'PLA', 'PLP',
    # Arithmetic
    'ADC', 'SBC', 'INC', 'INX', 'INY', 'DEC', 'DEX', 'DEY',
    # Logical
    'AND', 'ORA', 'EOR', 'BIT',
    # Shift/Rotate
    'ASL', 'LSR', 'ROL', 'ROR',
    # Branch
    'BCC', 'BCS', 'BEQ', 'BNE', 'BMI', 'BPL', 'BVC', 'BVS',
    # Jump
    'JMP', 'JSR', 'RTS', 'RTI',
    # Compare
    'CMP', 'CPX', 'CPY',
    # Flags
    'CLC', 'CLD', 'CLI', 'CLV', 'SEC', 'SED', 'SEI',
    # No-op
    'NOP',
    # Break
    'BRK',
}

# NES memory-mapped registers
PPU_REGISTERS = {
    0x2000: 'PPUCTRL',
    0x2001: 'PPUMASK',
    0x2002: 'PPUSTATUS',
    0x2003: 'OAMADDR',
    0x2004: 'OAMDATA',
    0x2005: 'PPUSCROLL',
    0x2006: 'PPUADDR',
    0x2007: 'PPUDATA',
}

APU_IO_REGISTERS = {
    0x4000: 'SQ1_VOL',
    0x4001: 'SQ1_SWEEP',
    0x4002: 'SQ1_LO',
    0x4003: 'SQ1_HI',
    0x4004: 'SQ2_VOL',
    0x4005: 'SQ2_SWEEP',
    0x4006: 'SQ2_LO',
    0x4007: 'SQ2_HI',
    0x4008: 'TRI_LINEAR',
    0x400A: 'TRI_LO',
    0x400B: 'TRI_HI',
    0x400C: 'NOISE_VOL',
    0x400E: 'NOISE_LO',
    0x400F: 'NOISE_HI',
    0x4010: 'DMC_FREQ',
    0x4011: 'DMC_RAW',
    0x4012: 'DMC_START',
    0x4013: 'DMC_LEN',
    0x4014: 'OAMDMA',
    0x4015: 'SND_CHN',
    0x4016: 'JOY1',
    0x4017: 'JOY2',
}

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
    addr_str = addr_str.strip()

    # Remove $ prefix for hex
    if addr_str.startswith('$'):
        try:
            return int(addr_str[1:], 16)
        except ValueError:
            return None

    # Try hex without prefix
    try:
        return int(addr_str, 16)
    except ValueError:
        pass

    # Try decimal
    try:
        return int(addr_str, 10)
    except ValueError:
        return None

def check_invalid_instructions(lines: List[str]) -> List[ValidationError]:
    """Check for invalid 6502 instructions."""
    errors = []

    for line_num, line in enumerate(lines, 1):
        # Remove comments
        if ';' in line:
            line = line[:line.index(';')]

        line = line.strip()
        if not line:
            continue

        # Skip labels (end with :)
        if ':' in line:
            line = line.split(':', 1)[1].strip()
            if not line:
                continue

        # Skip directives (start with .)
        if line.startswith('.'):
            continue

        # Extract instruction (first word)
        parts = line.split()
        if not parts:
            continue

        instruction = parts[0].upper()

        # Check if instruction is valid
        if instruction not in VALID_6502_INSTRUCTIONS:
            # Might be a label or macro, skip common ones
            if instruction in ['BYTE', 'WORD', 'DBYT', 'ADDR', 'RES', 'ORG', 'EQU', 'INCLUDE', 'INCBIN', 'SEGMENT', 'PROC', 'ENDPROC']:
                continue

            # Check if it's a potential typo of valid instruction
            errors.append(ValidationError(
                line_num,
                f"Invalid or unknown instruction '{instruction}' (NES uses standard 6502 only)"
            ))

    return errors

def check_oamdata_usage(lines: List[str]) -> List[ValidationWarning]:
    """Warn about OAMDATA ($2004) usage - should use OAMDMA ($4014) instead."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        # Remove comments
        code = line
        if ';' in code:
            code = code[:code.index(';')]

        code = code.upper()

        # Check for writes to $2004
        if re.search(r'\bSTA\s+\$2004\b', code):
            warnings.append(ValidationWarning(
                line_num,
                "Writing to OAMDATA ($2004) is very slow - use OAMDMA ($4014) instead during VBlank"
            ))

    return warnings

def check_ppu_timing(lines: List[str]) -> List[ValidationWarning]:
    """Warn about potential PPU timing issues."""
    warnings = []

    # Look for writes to PPU registers without apparent VBlank waiting
    in_nmi = False
    seen_vblank_wait = False

    for line_num, line in enumerate(lines, 1):
        code = line
        if ';' in code:
            code = code[:code.index(';')]

        code_upper = code.upper()

        # Track if we're in NMI handler
        if 'NMI' in code_upper and ':' in code:
            in_nmi = True

        # Track VBlank waiting
        if 'BIT $2002' in code_upper or 'LDA $2002' in code_upper:
            if 'BPL' in code_upper or 'BVC' in code_upper:
                seen_vblank_wait = True

        # Check for PPUADDR/PPUDATA writes
        if re.search(r'\bSTA\s+\$200[67]\b', code_upper):
            # If not in NMI and haven't seen VBlank wait, warn
            if not in_nmi and not seen_vblank_wait:
                warnings.append(ValidationWarning(
                    line_num,
                    f"Writing to PPU registers outside VBlank can cause glitches - ensure rendering is off or in NMI handler"
                ))

    return warnings

def check_ppuaddr_latch(lines: List[str]) -> List[ValidationWarning]:
    """Check for proper PPUADDR latch reset before writes."""
    warnings = []

    for i, line in enumerate(lines):
        code = line
        if ';' in code:
            code = code[:code.index(';')]

        code_upper = code.upper()

        # Look for PPUADDR writes
        if re.search(r'\bSTA\s+\$2006\b', code_upper):
            # Check previous ~10 lines for PPUSTATUS read
            found_reset = False
            for j in range(max(0, i-10), i):
                prev_line = lines[j]
                if ';' in prev_line:
                    prev_line = prev_line[:prev_line.index(';')]
                prev_line = prev_line.upper()

                if 'LDA $2002' in prev_line or 'BIT $2002' in prev_line:
                    found_reset = True
                    break

            if not found_reset:
                warnings.append(ValidationWarning(
                    i + 1,
                    "PPUADDR write without reading PPUSTATUS first - may write to wrong address (latch not reset)"
                ))
                # Only warn once per sequence
                break

    return warnings

def check_sprite_0_x_position(lines: List[str]) -> List[ValidationWarning]:
    """Warn about sprite 0 hit at X=255 (hardware bug)."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        # Look for sprite 0 X position writes ($0203)
        if re.search(r'LDA\s+#\$FF', line, re.IGNORECASE):
            # Check next few lines for STA $0203 (sprite 0 X)
            for offset in range(1, 4):
                if line_num + offset - 1 < len(lines):
                    next_line = lines[line_num + offset - 1]
                    if re.search(r'STA\s+\$0203\b', next_line, re.IGNORECASE):
                        warnings.append(ValidationWarning(
                            line_num,
                            "Sprite 0 hit unreliable at X=255 (hardware bug) - use X=254 or less"
                        ))
                        break

    return warnings

def check_interrupt_vectors(lines: List[str]) -> List[ValidationError]:
    """Check for interrupt vector definitions."""
    errors = []

    # Look for .segment "VECTORS" or equivalent
    has_nmi = False
    has_reset = False
    has_irq = False

    for line in lines:
        code = line.upper()

        # Look for vector definitions
        if '.ADDR' in code or '.WORD' in code:
            if 'NMI' in code:
                has_nmi = True
            if 'RESET' in code:
                has_reset = True
            if 'IRQ' in code:
                has_irq = True

    # RESET is mandatory, NMI highly recommended if using rendering
    if not has_reset:
        errors.append(ValidationError(
            0,
            "Missing RESET vector - NES will not boot correctly (must define .addr reset_handler at $FFFC)"
        ))

    if not has_nmi:
        # This is just a warning since some simple programs don't use NMI
        pass

    return errors

def check_decimal_mode(lines: List[str]) -> List[ValidationError]:
    """Check for decimal mode usage (not supported on NES)."""
    errors = []

    for line_num, line in enumerate(lines, 1):
        code = line
        if ';' in code:
            code = code[:code.index(';')]

        code_upper = code.upper()

        # Check for SED instruction
        if re.search(r'\bSED\b', code_upper):
            errors.append(ValidationError(
                line_num,
                "SED (set decimal mode) has no effect on NES - 6502 decimal mode is disabled"
            ))

    return errors

def validate_nes_asm(filepath: str) -> Tuple[List[ValidationError], List[ValidationWarning]]:
    """Run all validation checks on NES assembly file."""
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
    errors.extend(check_invalid_instructions(lines))
    errors.extend(check_interrupt_vectors(lines))
    errors.extend(check_decimal_mode(lines))

    warnings.extend(check_oamdata_usage(lines))
    warnings.extend(check_ppu_timing(lines))
    warnings.extend(check_ppuaddr_latch(lines))
    warnings.extend(check_sprite_0_x_position(lines))

    return errors, warnings

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 validate-nes-asm.py <file.asm>")
        sys.exit(1)

    filepath = sys.argv[1]

    print(f"\n🔍 Validating NES Assembly: {filepath}\n")

    errors, warnings = validate_nes_asm(filepath)

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
