#!/usr/bin/env python3
"""
C64 BASIC Semantic Validator

Validates C64 BASIC code for semantic correctness beyond what petcat can check.
Based on /docs/PETCAT-LIMITATIONS.md and lessons learned from Tier 3 development.

This validator catches:
- Reserved C64 BASIC V2 system variables (ST, TI, TI$) - NEW!
- Array re-dimensioning (DIM same array twice) - NEW!
- GOSUB/GOTO to non-existent line numbers - NEW!
- Duplicate line numbers - NEW!
- FOR/NEXT mismatches - NEW!
- C64 BASIC V2 incompatibilities (RESTORE with line numbers, later BASIC features)
- Invalid hardware register addresses
- POKE values >255 without MSB handling
- Boundary violations (screen coordinates, sprite positions)
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

class ValidationError:
    def __init__(self, line_num: int, message: str, severity: str = 'error'):
        self.line_num = line_num
        self.message = message
        self.severity = severity

    def __str__(self):
        icon = '❌' if self.severity == 'error' else '⚠️ '
        return f"{icon} Line {self.line_num}: {self.message}"

class C64BasicValidator:
    # Hardware register ranges
    VALID_RANGES = {
        'Screen RAM': (1024, 2023),
        'Color RAM': (55296, 56295),
        'Sprite pointers': (2040, 2047),
        'VIC-II': (53248, 53295),
        'SID': (54272, 54300),
        'CIA #1': (56320, 56335),
        'CIA #2': (56576, 56591),
    }

    # Specific register validation
    SPRITE_REGISTERS = {
        53248: "Sprite 0 X",
        53249: "Sprite 0 Y",
        53264: "Sprite X MSB",
        53269: "Sprite enable",
        53280: "Border color",
        53281: "Background color",
    }

    # Reserved C64 BASIC V2 system variables
    RESERVED_VARS = ['ST', 'TI', 'TI$']

    def __init__(self, filename: str):
        self.filename = filename
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.line_numbers = set()  # Track all line numbers in program
        self.dimmed_arrays = {}  # Track DIM statements: {array_name: line_num}
        self.for_vars = []  # Stack for FOR/NEXT matching

    def validate(self) -> bool:
        """Run all validation checks on the BASIC file."""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return False

        # First pass: collect line numbers and check structure
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith('#'):
                continue

            # Extract BASIC line number if present
            match = re.match(r'^(\d+)\s', line_stripped)
            if match:
                basic_line_num = int(match.group(1))
                if basic_line_num in self.line_numbers:
                    self.errors.append(ValidationError(
                        line_num,
                        f"Duplicate line number {basic_line_num}"
                    ))
                self.line_numbers.add(basic_line_num)

        # Second pass: run all validation checks
        for line_num, line in enumerate(lines, 1):
            # Convert to lowercase for case-insensitive matching
            line_lower = line.lower()

            # Run all validation checks
            self._check_reserved_variables(line, line_num)  # Pass original case
            self._check_array_redim(line_lower, line_num)
            self._check_gosub_goto_targets(line_lower, line_num)
            self._check_for_next_matching(line_lower, line_num)
            self._check_restore_syntax(line_lower, line_num)
            self._check_poke_values(line_lower, line_num)
            self._check_register_addresses(line_lower, line_num)
            self._check_basic_v2_features(line_lower, line_num)
            self._check_sprite_boundaries(line_lower, line_num)

        return len(self.errors) == 0

    def _check_reserved_variables(self, line: str, line_num: int):
        """Check for use of reserved C64 BASIC V2 system variables"""
        # Must use original case to detect ST, TI, TI$
        for var in self.RESERVED_VARS:
            # Match variable assignment or usage
            # Look for ST=, TI=, TI$= or variable in expressions
            pattern = rf'\b{re.escape(var)}\s*='
            if re.search(pattern, line, re.IGNORECASE):
                self.errors.append(ValidationError(
                    line_num,
                    f"Reserved variable '{var}' cannot be assigned to (causes ?SYNTAX ERROR)"
                ))

    def _check_array_redim(self, line: str, line_num: int):
        """Check for re-dimensioning arrays (DIM statement on same array twice)"""
        # Match DIM statements: dim a(10), b(20)
        match = re.search(r'\bdim\s+([a-z][a-z0-9\$]*)\s*\(', line)
        if match:
            array_name = match.group(1).upper()
            if array_name in self.dimmed_arrays:
                self.errors.append(ValidationError(
                    line_num,
                    f"Array '{array_name}' re-dimensioned (already DIM'd at line {self.dimmed_arrays[array_name]})"
                ))
            else:
                self.dimmed_arrays[array_name] = line_num

    def _check_gosub_goto_targets(self, line: str, line_num: int):
        """Check that GOSUB and GOTO targets exist"""
        # Match GOSUB/GOTO followed by line number
        matches = re.finditer(r'\b(gosub|goto)\s+(\d+)', line)
        for match in matches:
            command = match.group(1).upper()
            target = int(match.group(2))
            if target not in self.line_numbers:
                self.errors.append(ValidationError(
                    line_num,
                    f"{command} to non-existent line {target} (causes ?UNDEF'D STATEMENT ERROR)"
                ))

    def _check_for_next_matching(self, line: str, line_num: int):
        """Check that FOR/NEXT statements match properly"""
        # Match FOR statements: for i=1 to 10
        for_match = re.search(r'\bfor\s+([a-z][a-z0-9]*)\s*=', line)
        if for_match:
            var = for_match.group(1).upper()
            self.for_vars.append((var, line_num))

        # Match NEXT statements: next i
        next_match = re.search(r'\bnext\s+([a-z][a-z0-9]*)', line)
        if next_match:
            var = next_match.group(1).upper()
            if not self.for_vars:
                self.warnings.append(ValidationError(
                    line_num,
                    f"NEXT {var} without matching FOR",
                    severity='warning'
                ))
            else:
                last_for_var, for_line = self.for_vars.pop()
                if last_for_var != var:
                    self.warnings.append(ValidationError(
                        line_num,
                        f"NEXT {var} doesn't match FOR {last_for_var} (line {for_line})",
                        severity='warning'
                    ))

    def _check_restore_syntax(self, line: str, line_num: int):
        """RESTORE must have no arguments in C64 BASIC V2"""
        # Match RESTORE followed by space and digits
        if re.search(r'\brestore\s+\d+', line):
            self.errors.append(ValidationError(
                line_num,
                "RESTORE with line number not supported in C64 BASIC V2 (use bare RESTORE)"
            ))

    def _check_poke_values(self, line: str, line_num: int):
        """POKE values must be 0-255 (literals only - can't check variables)"""
        # Match: poke addr,literal_value
        # This only catches obvious errors with literal values
        matches = re.finditer(r'\bpoke\s+\d+\s*,\s*(\d+)', line)
        for match in matches:
            value = int(match.group(1))
            if value > 255:
                self.errors.append(ValidationError(
                    line_num,
                    f"POKE value {value} exceeds 255 (will cause ?ILLEGAL QUANTITY ERROR)"
                ))

    def _check_register_addresses(self, line: str, line_num: int):
        """Validate common hardware register addresses"""
        # Match POKE/PEEK addresses
        matches = re.finditer(r'\b(poke|peek)\s*(?:\(?\s*)?(\d+)', line)
        for match in matches:
            addr = int(match.group(2))

            # Skip low memory addresses (variables, BASIC program)
            if addr < 1024:
                continue

            # Check if address is in ANY valid range
            in_valid_range = any(
                start <= addr <= end
                for start, end in self.VALID_RANGES.values()
            )

            if not in_valid_range:
                self.warnings.append(ValidationError(
                    line_num,
                    f"Address {addr} not in known C64 hardware ranges (may be intentional)",
                    severity='warning'
                ))

    def _check_basic_v2_features(self, line: str, line_num: int):
        """Check for features NOT in C64 BASIC V2"""
        unsupported = [
            (r'\bdo\b', 'DO...LOOP'),
            (r'\bwhile\b', 'WHILE...WEND'),
            (r'\bproc\b', 'PROC/ENDPROC'),
            (r'\brepeat\b', 'REPEAT...UNTIL'),
            (r'\bendproc\b', 'ENDPROC'),
            (r'\buntil\b', 'UNTIL'),
        ]

        for pattern, feature in unsupported:
            if re.search(pattern, line):
                self.errors.append(ValidationError(
                    line_num,
                    f"{feature} not supported in C64 BASIC V2"
                ))

    def _check_sprite_boundaries(self, line: str, line_num: int):
        """Check for common sprite boundary violations"""
        # This is heuristic - we can't trace variable values
        # but we can catch obvious literal errors

        # Check for sprite Y coordinates (should be 50-229)
        # Pattern: poke 53249,<value> (sprite 0 Y)
        sprite_y_regs = [53249, 53251, 53253, 53255, 53257, 53259, 53261, 53263]
        for reg in sprite_y_regs:
            matches = re.finditer(rf'\bpoke\s+{reg}\s*,\s*(\d+)', line)
            for match in matches:
                y = int(match.group(1))
                if y < 50 or y > 229:
                    self.warnings.append(ValidationError(
                        line_num,
                        f"Sprite Y position {y} outside visible range (50-229)",
                        severity='warning'
                    ))

    def report(self) -> bool:
        """Print validation report and return success status."""
        if not self.errors and not self.warnings:
            print(f"✅ {self.filename} passed all semantic checks")
            return True

        if self.errors:
            print(f"\n❌ ERRORS in {self.filename}:")
            for error in self.errors:
                print(f"   {error}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS in {self.filename}:")
            for warning in self.warnings:
                print(f"   {warning}")

        if self.errors:
            print(f"\n{len(self.errors)} error(s) found. Fix these before committing.")
            return False
        else:
            print(f"\n{len(self.warnings)} warning(s) found (non-blocking).")
            return True

def main():
    if len(sys.argv) != 2:
        print("Usage: validate-c64-basic.py <file.bas>")
        sys.exit(1)

    filename = sys.argv[1]

    if not Path(filename).exists():
        print(f"❌ File not found: {filename}")
        sys.exit(1)

    validator = C64BasicValidator(filename)

    if validator.validate() and validator.report():
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
