#!/usr/bin/env python3
"""
Commodore 64 6510 Assembly Semantic Validator

Performs static analysis on 6510 assembly code to catch common errors
that would compile but fail at runtime or produce unexpected behavior.

Usage:
    python3 validate-c64-asm.py <file.asm>

Exit codes:
    0 - No errors (warnings are non-blocking)
    1 - Errors found (must be fixed)
"""

import sys
import re
from typing import List, Tuple, Optional

# C64 memory map
ZERO_PAGE = (0x00, 0xFF)
STACK = (0x0100, 0x01FF)
SCREEN_RAM_DEFAULT = (0x0400, 0x07FF)
BASIC_AREA = (0x0800, 0x9FFF)
VIC_II = (0xD000, 0xD3FF)
SID = (0xD400, 0xD7FF)
COLOR_RAM = (0xD800, 0xDBFF)
CIA1 = (0xDC00, 0xDCFF)
CIA2 = (0xDD00, 0xDDFF)
KERNAL_ROM = (0xE000, 0xFFFF)
BASIC_ROM = (0xA000, 0xBFFF)

# Key VIC-II registers
VIC_SPRITE_X = list(range(0xD000, 0xD010, 2))  # $D000, $D002, etc.
VIC_SPRITE_Y = list(range(0xD001, 0xD011, 2))  # $D001, $D003, etc.
VIC_SPRITE_X_MSB = 0xD010
VIC_RASTER = 0xD012
VIC_SPRITE_ENABLE = 0xD015
VIC_CONTROL_1 = 0xD011
VIC_CONTROL_2 = 0xD016
VIC_BORDER_COLOR = 0xD020
VIC_BACKGROUND_COLOR = 0xD021

# Key SID registers
SID_VOICE1_FREQ_LO = 0xD400
SID_VOICE1_FREQ_HI = 0xD401
SID_FILTER_CUTOFF = 0xD415
SID_VOLUME = 0xD418

# CIA registers
CIA1_PORT_A = 0xDC00  # Keyboard/joystick
CIA1_PORT_B = 0xDC01  # Keyboard
CIA1_INTERRUPT = 0xDC0D
CIA2_PORT_A = 0xDD00  # VIC bank selection


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

    # Remove $ prefix (6502 hex notation)
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


def check_rom_writes(lines: List[str]) -> List[ValidationError]:
    """Error on attempts to write to ROM without banking."""
    errors = []

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # Check for STA/STX/STY to ROM addresses
        store_match = re.search(r'\b(STA|STX|STY)\s+\$([0-9A-F]+)', line_upper)
        if store_match:
            addr = parse_address('$' + store_match.group(2))
            if addr:
                if KERNAL_ROM[0] <= addr <= KERNAL_ROM[1]:
                    errors.append(ValidationError(
                        line_num,
                        f"Writing to Kernal ROM ${addr:04X} - ROM is read-only unless banked out via $01"
                    ))
                elif BASIC_ROM[0] <= addr <= BASIC_ROM[1]:
                    errors.append(ValidationError(
                        line_num,
                        f"Writing to BASIC ROM ${addr:04X} - ROM is read-only unless banked out via $01"
                    ))

    return errors


def check_sprite_x_msb(lines: List[str]) -> List[ValidationWarning]:
    """Warn about sprite X positioning without MSB handling."""
    warnings = []
    has_sprite_x_write = False
    has_msb_handling = False

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # Check for sprite X register writes
        for addr in ['D000', 'D002', 'D004', 'D006', 'D008', 'D00A', 'D00C', 'D00E']:
            if f'${addr}' in line_upper or f'53248' in line or f'53250' in line:
                has_sprite_x_write = True

        # Check for MSB register ($D010 or 53264)
        if '$D010' in line_upper or '53264' in line:
            has_msb_handling = True

    if has_sprite_x_write and not has_msb_handling:
        warnings.append(ValidationWarning(
            0,
            "Sprite X position written without MSB ($D010/53264) handling - sprites won't move past X=255"
        ))

    return warnings


def check_raster_interrupt_setup(lines: List[str]) -> List[ValidationWarning]:
    """Check for proper raster interrupt setup."""
    warnings = []
    has_raster_irq = False
    has_sei = False
    has_irq_vector = False

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # Check for raster register access
        if '$D012' in line_upper or '53266' in line:
            has_raster_irq = True

        # Check for SEI instruction
        if re.search(r'\bSEI\b', line_upper):
            has_sei = True

        # Check for IRQ vector setup ($FFFE or $0314)
        if '$FFFE' in line_upper or '$0314' in line_upper:
            has_irq_vector = True

    if has_raster_irq and not has_sei:
        warnings.append(ValidationWarning(
            0,
            "Raster IRQ setup without SEI - interrupts should be disabled during vector setup"
        ))

    if has_raster_irq and not has_irq_vector:
        warnings.append(ValidationWarning(
            0,
            "Raster register accessed but no IRQ vector setup ($0314 or $FFFE)"
        ))

    return warnings


def check_cia_timer_setup(lines: List[str]) -> List[ValidationWarning]:
    """Check for CIA timer configuration issues."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # Check for CIA interrupt register access without acknowledge
        if '$DC0D' in line_upper or '$DD0D' in line_upper:
            if 'LDA' in line_upper:
                # Reading acknowledges - good
                pass
            elif 'STA' in line_upper:
                warnings.append(ValidationWarning(
                    line_num,
                    "CIA interrupt control register - remember to acknowledge IRQs by reading $DC0D/$DD0D"
                ))

    return warnings


def check_vic_bank_selection(lines: List[str]) -> List[ValidationWarning]:
    """Warn about VIC bank selection via CIA2."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # Check for CIA2 port A writes (VIC bank selection)
        if '$DD00' in line_upper and ('STA' in line_upper or 'STX' in line_upper or 'STY' in line_upper):
            warnings.append(ValidationWarning(
                line_num,
                "$DD00 controls VIC bank - ensure screen/charset/sprite data is in selected bank"
            ))

    return warnings


def check_zero_page_conflicts(lines: List[str]) -> List[ValidationWarning]:
    """Warn about zero page locations used by BASIC/Kernal."""
    warnings = []

    # BASIC/Kernal zero page locations to be careful with
    reserved_zp = {
        0x00: "CPU port data direction",
        0x01: "CPU port (bank switching)",
        0x02: "Unused (safe)",
        0xFB: "Free for user",
        0xFC: "Free for user",
        0xFD: "Free for user",
        0xFE: "Free for user",
    }

    kernal_zp = list(range(0x90, 0xFB))  # Kernal workspace

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # Check for zero page stores
        store_match = re.search(r'\b(STA|STX|STY)\s+\$([0-9A-F]{1,2})\b', line_upper)
        if store_match:
            addr = parse_address('$' + store_match.group(2))
            if addr and addr < 0x100:
                if addr in [0x00, 0x01]:
                    warnings.append(ValidationWarning(
                        line_num,
                        f"Writing to ${addr:02X} ({reserved_zp.get(addr, 'system')}) - ensure intentional"
                    ))
                elif addr in kernal_zp:
                    warnings.append(ValidationWarning(
                        line_num,
                        f"Zero page ${addr:02X} is Kernal workspace - may conflict if using Kernal routines"
                    ))

    return warnings


def check_stack_management(lines: List[str]) -> List[ValidationWarning]:
    """Check for balanced PHA/PLA, PHP/PLP."""
    warnings = []
    push_count = 0
    pop_count = 0

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # Count pushes
        if re.search(r'\b(PHA|PHP|PHX|PHY)\b', line_upper):
            push_count += 1

        # Count pops
        if re.search(r'\b(PLA|PLP|PLX|PLY)\b', line_upper):
            pop_count += 1

    if push_count != pop_count:
        warnings.append(ValidationWarning(
            0,
            f"Unbalanced stack operations: {push_count} pushes vs {pop_count} pops - may corrupt stack"
        ))

    return warnings


def check_jsr_rts_balance(lines: List[str]) -> List[ValidationWarning]:
    """Check subroutine structure."""
    warnings = []
    labels = set()
    jsr_targets = set()

    for line_num, line in enumerate(lines, 1):
        orig_line = line
        if ';' in line:
            line = line[:line.index(';')]

        line_stripped = line.strip()

        # Collect labels
        label_match = re.match(r'^(\w+):', line_stripped, re.IGNORECASE)
        if label_match:
            labels.add(label_match.group(1).upper())

        # Collect JSR targets
        jsr_match = re.search(r'\bJSR\s+(\w+)', line.upper())
        if jsr_match:
            jsr_targets.add(jsr_match.group(1).upper())

    # Check for JSR to undefined labels (could be Kernal)
    kernal_routines = {'CHROUT', 'GETIN', 'PLOT', 'RDTIM', 'SETTIM', 'SCNKEY', 'CINT', 'IOINIT'}

    for target in jsr_targets:
        if target not in labels:
            # Check if it's a hex address
            if not target.startswith('$') and target not in kernal_routines:
                # Could be external or undefined
                pass  # Don't warn - assembler will catch undefined symbols

    return warnings


def check_sid_initialization(lines: List[str]) -> List[ValidationWarning]:
    """Check for SID register initialization."""
    warnings = []
    has_sid_write = False
    has_volume_set = False

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # Check for any SID register write
        if '$D4' in line_upper and ('STA' in line_upper or 'STX' in line_upper or 'STY' in line_upper):
            has_sid_write = True

            # Check specifically for volume register
            if '$D418' in line_upper or '54296' in line:
                has_volume_set = True

    if has_sid_write and not has_volume_set:
        warnings.append(ValidationWarning(
            0,
            "SID registers written but volume ($D418) not set - no sound will be heard"
        ))

    return warnings


def check_interrupt_handling(lines: List[str]) -> List[ValidationWarning]:
    """Check interrupt handler structure."""
    warnings = []
    has_rti = False
    has_interrupt_setup = False

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # Check for RTI
        if re.search(r'\bRTI\b', line_upper):
            has_rti = True

        # Check for interrupt vector setup
        if '$0314' in line_upper or '$FFFE' in line_upper:
            has_interrupt_setup = True

    if has_interrupt_setup and not has_rti:
        warnings.append(ValidationWarning(
            0,
            "Interrupt vector setup but no RTI found - interrupt handler must end with RTI"
        ))

    return warnings


def check_illegal_opcodes_usage(lines: List[str]) -> List[ValidationWarning]:
    """Note usage of illegal/undocumented opcodes (valid on C64 but may confuse readers)."""
    warnings = []

    # Common illegal opcodes
    illegal_opcodes = {
        'LAX': "Load A and X simultaneously",
        'SAX': "Store A AND X",
        'DCP': "Decrement and compare",
        'ISB': "Increment and subtract",
        'ISC': "Increment and subtract (alt name)",
        'SLO': "Shift left and OR",
        'RLA': "Rotate left and AND",
        'SRE': "Shift right and EOR",
        'RRA': "Rotate right and ADC",
        'ANC': "AND with carry",
        'ALR': "AND then LSR",
        'ARR': "AND then ROR",
        'AXS': "A AND X minus immediate",
    }

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        for opcode, description in illegal_opcodes.items():
            if re.search(rf'\b{opcode}\b', line_upper):
                warnings.append(ValidationWarning(
                    line_num,
                    f"Illegal opcode {opcode} ({description}) - works on C64 but not standard 6502"
                ))

    return warnings


def validate_c64_asm(filepath: str) -> Tuple[List[ValidationError], List[ValidationWarning]]:
    """Run all validation checks on C64 6510 assembly file."""
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
    errors.extend(check_rom_writes(lines))

    warnings.extend(check_sprite_x_msb(lines))
    warnings.extend(check_raster_interrupt_setup(lines))
    warnings.extend(check_cia_timer_setup(lines))
    warnings.extend(check_vic_bank_selection(lines))
    warnings.extend(check_zero_page_conflicts(lines))
    warnings.extend(check_stack_management(lines))
    warnings.extend(check_jsr_rts_balance(lines))
    warnings.extend(check_sid_initialization(lines))
    warnings.extend(check_interrupt_handling(lines))
    warnings.extend(check_illegal_opcodes_usage(lines))

    return errors, warnings


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 validate-c64-asm.py <file.asm>")
        sys.exit(1)

    filepath = sys.argv[1]

    print(f"\n🔍 Validating C64 6510 Assembly: {filepath}\n")

    errors, warnings = validate_c64_asm(filepath)

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
