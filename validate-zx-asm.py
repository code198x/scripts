#!/usr/bin/env python3
"""
ZX Spectrum Z80 Assembly Semantic Validator

Performs static analysis on Z80 assembly code to catch common errors
that would compile but fail at runtime or produce unexpected behavior.

Usage:
    python3 validate-z80-asm.py <file.asm>

Exit codes:
    0 - No errors (warnings are non-blocking)
    1 - Errors found (must be fixed)
"""

import sys
import re
from typing import List, Tuple, Optional

# Valid Z80 instructions
VALID_Z80_INSTRUCTIONS = {
    # 8-bit load
    'LD', 'PUSH', 'POP',
    # 16-bit load
    'EX', 'EXX', 'LDI', 'LDIR', 'LDD', 'LDDR',
    # 8-bit arithmetic
    'ADD', 'ADC', 'SUB', 'SBC', 'AND', 'OR', 'XOR', 'CP',
    'INC', 'DEC', 'DAA', 'CPL', 'NEG', 'CCF', 'SCF',
    # 16-bit arithmetic
    # Rotate and shift
    'RLCA', 'RLA', 'RRCA', 'RRA', 'RLC', 'RL', 'RRC', 'RR',
    'SLA', 'SRA', 'SRL', 'SLL',
    # Bit operations
    'BIT', 'SET', 'RES',
    # Jump and call
    'JP', 'JR', 'DJNZ', 'CALL', 'RET', 'RETI', 'RETN', 'RST',
    # Input/output
    'IN', 'INI', 'INIR', 'IND', 'INDR',
    'OUT', 'OUTI', 'OTIR', 'OUTD', 'OTDR',
    # CPU control
    'NOP', 'HALT', 'DI', 'EI',
    'IM', 'RLD', 'RRD',
    # Block operations
    'CPI', 'CPIR', 'CPD', 'CPDR',
}

# ZX Spectrum memory ranges
SCREEN_BITMAP = (16384, 22527)  # $4000-$57FF
SCREEN_ATTRS = (22528, 23295)   # $5800-$5AFF
ROM_AREA = (0, 16383)            # $0000-$3FFF
CONTENDED_RAM = (16384, 32767)  # $4000-$7FFF

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

    # Remove $ or # prefix
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

    # Try hex without prefix (if ends with H)
    if addr_str.endswith('H'):
        try:
            return int(addr_str[:-1], 16)
        except ValueError:
            return None

    # Try decimal
    try:
        return int(addr_str, 10)
    except ValueError:
        return None

def check_screen_memory_access(lines: List[str]) -> List[ValidationWarning]:
    """Warn about direct screen memory writes without thirds formula."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        # Remove comments
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # Check for writes to screen memory area
        # Look for LD (HL), or LD (addr), patterns in screen range
        if re.search(r'\bLD\s+\(', line_upper):
            # Check for screen address range (16384-22527)
            for match in re.finditer(r'16384|0x4000|\$4000|4000H', line_upper):
                warnings.append(ValidationWarning(
                    line_num,
                    "Direct screen bitmap access - ensure using thirds formula for pixel addressing"
                ))
                break

    return warnings

def check_contended_memory_timing(lines: List[str]) -> List[ValidationWarning]:
    """Warn about operations in contended memory that may have timing issues."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # Check for code execution in contended RAM
        # ORG in contended area
        org_match = re.search(r'\bORG\s+(\S+)', line_upper)
        if org_match:
            addr = parse_address(org_match.group(1))
            if addr and CONTENDED_RAM[0] <= addr <= CONTENDED_RAM[1]:
                warnings.append(ValidationWarning(
                    line_num,
                    f"Code at ${addr:04X} in contended RAM ($4000-$7FFF) - timing will vary due to ULA contention"
                ))

    return warnings

def check_rom_writes(lines: List[str]) -> List[ValidationError]:
    """Error on attempts to write to ROM area."""
    errors = []

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # Check for LD to ROM addresses
        ld_match = re.search(r'\bLD\s+\((\S+)\)', line_upper)
        if ld_match:
            addr_str = ld_match.group(1)
            addr = parse_address(addr_str)
            if addr and ROM_AREA[0] <= addr <= ROM_AREA[1]:
                errors.append(ValidationError(
                    line_num,
                    f"Attempting to write to ROM address ${addr:04X} - ROM is read-only"
                ))

    return errors

def check_attribute_calculation(lines: List[str]) -> List[ValidationWarning]:
    """Check for proper attribute address calculation (linear, not thirds)."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # Look for attribute base address (22528 or $5800)
        if '22528' in line or '5800' in line_upper:
            # Check if they're using AND operations (thirds formula)
            if 'AND' in line_upper and ('7' in line or '56' in line or '192' in line):
                warnings.append(ValidationWarning(
                    line_num,
                    "Attributes use LINEAR addressing, not thirds formula - calculation may be wrong"
                ))

    return warnings

def check_register_preservation(lines: List[str]) -> List[ValidationWarning]:
    """Warn about subroutines that may not preserve registers."""
    warnings = []

    in_subroutine = False
    subroutine_start = 0
    pushed_registers = set()
    popped_registers = set()

    for line_num, line in enumerate(lines, 1):
        code = line
        if ';' in code:
            code = code[:code.index(';')]

        code_upper = code.strip().upper()

        # Detect subroutine start (label ending with colon)
        if ':' in code and not code_upper.startswith(';'):
            if in_subroutine:
                # Check if pushes match pops
                if pushed_registers != popped_registers:
                    warnings.append(ValidationWarning(
                        subroutine_start,
                        "Subroutine may not preserve all registers - PUSH/POP mismatch detected"
                    ))
            in_subroutine = True
            subroutine_start = line_num
            pushed_registers = set()
            popped_registers = set()

        # Track PUSH instructions
        push_match = re.search(r'\bPUSH\s+(\w+)', code_upper)
        if push_match:
            pushed_registers.add(push_match.group(1))

        # Track POP instructions
        pop_match = re.search(r'\bPOP\s+(\w+)', code_upper)
        if pop_match:
            popped_registers.add(pop_match.group(1))

        # Detect RET (end of subroutine)
        if re.search(r'\bRET\b', code_upper):
            if in_subroutine and pushed_registers != popped_registers:
                warnings.append(ValidationWarning(
                    line_num,
                    "RET with mismatched PUSH/POP - may corrupt registers or stack"
                ))

    return warnings

def check_djnz_range(lines: List[str]) -> List[ValidationWarning]:
    """Warn about DJNZ with potentially out-of-range jumps."""
    warnings = []

    for line_num, line in enumerate(lines, 1):
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # DJNZ has limited range (-126 to +129 bytes)
        if 'DJNZ' in line_upper:
            warnings.append(ValidationWarning(
                line_num,
                "DJNZ has limited range (-126 to +129 bytes) - use JP if target is far"
            ))

    return warnings

def check_interrupt_mode(lines: List[str]) -> List[ValidationWarning]:
    """Check for interrupt mode usage."""
    warnings = []

    has_im = False
    has_ei_di = False

    for line_num, line in enumerate(lines, 1):
        code = line
        if ';' in code:
            code = code[:code.index(';')]

        code_upper = code.upper()

        if re.search(r'\bIM\s+[012]', code_upper):
            has_im = True

        if 'EI' in code_upper or 'DI' in code_upper:
            has_ei_di = True

    if has_ei_di and not has_im:
        warnings.append(ValidationWarning(
            0,
            "Using EI/DI without IM instruction - interrupt mode not set (Spectrum defaults to IM 1)"
        ))

    return warnings

def check_stack_initialization(lines: List[str]) -> List[ValidationWarning]:
    """Check if SP (stack pointer) is initialized."""
    warnings = []

    has_sp_init = False

    for line in lines:
        if ';' in line:
            line = line[:line.index(';')]

        line_upper = line.upper()

        # Look for LD SP, initialization
        if re.search(r'\bLD\s+SP\s*,', line_upper):
            has_sp_init = True
            break

    if not has_sp_init:
        warnings.append(ValidationWarning(
            0,
            "Stack pointer (SP) not initialized - may use ROM default (not ideal for games)"
        ))

    return warnings

def check_halt_with_interrupts(lines: List[str]) -> List[ValidationWarning]:
    """Warn about HALT without interrupt setup."""
    warnings = []

    has_halt = False
    has_ei = False

    for line_num, line in enumerate(lines, 1):
        code = line
        if ';' in code:
            code = code[:code.index(';')]

        code_upper = code.upper()

        if 'HALT' in code_upper:
            has_halt = True
            halt_line = line_num

        if 'EI' in code_upper:
            has_ei = True

    if has_halt and not has_ei:
        warnings.append(ValidationWarning(
            halt_line if 'halt_line' in locals() else 0,
            "HALT without EI - CPU will hang forever (interrupts disabled)"
        ))

    return warnings

def validate_z80_asm(filepath: str) -> Tuple[List[ValidationError], List[ValidationWarning]]:
    """Run all validation checks on Z80 assembly file."""
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

    warnings.extend(check_screen_memory_access(lines))
    warnings.extend(check_contended_memory_timing(lines))
    warnings.extend(check_attribute_calculation(lines))
    warnings.extend(check_register_preservation(lines))
    warnings.extend(check_djnz_range(lines))
    warnings.extend(check_interrupt_mode(lines))
    warnings.extend(check_stack_initialization(lines))
    warnings.extend(check_halt_with_interrupts(lines))

    return errors, warnings

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 validate-z80-asm.py <file.asm>")
        sys.exit(1)

    filepath = sys.argv[1]

    print(f"\n🔍 Validating Z80 Assembly: {filepath}\n")

    errors, warnings = validate_z80_asm(filepath)

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
