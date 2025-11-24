# C64 BASIC Validation Scripts

This directory contains tools for validating C64 BASIC code samples used in the curriculum.

## Overview

The validation pipeline combines two complementary tools:
1. **petcat** - Syntax validation (tokenization check)
2. **validate-c64-basic.py** - Semantic validation (C64 BASIC V2 correctness)

Together they catch errors that would otherwise only appear at runtime on a real C64.

## Quick Start

Validate a single `.bas` file:

```bash
./validate-bas.sh path/to/example.bas
```

This runs both syntax and semantic validation, exiting with code 0 (pass) or 1 (fail).

## Tools

### validate-bas.sh

**Purpose**: Comprehensive validation wrapper that runs both syntax and semantic checks.

**Usage**:
```bash
./validate-bas.sh <file.bas>
```

**Exit codes**:
- `0` - All validation passed
- `1` - Validation failed (syntax or semantic errors found)

**Output**:
- ✅ Green checkmarks for passing stages
- ❌ Red X marks for failures with detailed error messages
- ⚠️  Yellow warnings for non-blocking issues

**Example**:
```bash
$ ./validate-bas.sh /tmp/test.bas
🔍 Validating: /tmp/test.bas

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 1: Syntax Validation (petcat)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Syntax validation passed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 2: Semantic Validation (C64 BASIC V2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ /tmp/test.bas passed all semantic checks

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ ALL VALIDATION PASSED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### validate-c64-basic.py

**Purpose**: Static semantic analysis for C64 BASIC V2 code.

**Usage**:
```bash
python3 validate-c64-basic.py <file.bas>
```

**What it checks**:

1. **RESTORE syntax** - Detects `RESTORE <line>` which doesn't exist in C64 BASIC V2
2. **POKE values** - Validates literal values are 0-255 to prevent ILLEGAL QUANTITY errors
3. **Hardware addresses** - Checks POKE/PEEK addresses against known C64 memory map
4. **BASIC V2 features** - Detects commands from later BASIC versions (DO, WHILE, PROC, etc.)
5. **Sprite boundaries** - Warns if sprite Y positions are outside visible range (50-229)

**Exit codes**:
- `0` - No errors (warnings are non-blocking)
- `1` - Errors found (must be fixed)

**Example error output**:
```bash
❌ ERRORS in example.bas:
   ❌ Line 40: RESTORE with line number not supported in C64 BASIC V2 (use bare RESTORE)
   ❌ Line 80: POKE value 300 exceeds 255 (will cause ?ILLEGAL QUANTITY ERROR)

2 error(s) found. Fix these before committing.
```

**Example warning output**:
```bash
⚠️  WARNINGS in example.bas:
   ⚠️  Line 120: Sprite Y position 20 outside visible range (50-229)

1 warning(s) found (non-blocking).
```

## What Gets Validated

### Syntax Errors (petcat)
- Missing quotes
- Unmatched brackets
- Invalid tokens
- Malformed line numbers

### Semantic Errors (Python validator)
- **C64 BASIC V2 incompatibilities** that compile but fail at runtime
- **Hardware register misuse** that causes unexpected behavior
- **Value range violations** that trigger runtime errors
- **Common mistakes** that work in emulators but fail on real hardware

## Integration with Workflow

### When Creating Lessons

**Mandatory step** before committing any `.bas` file:

```bash
cd /path/to/lesson-NNN
./../../../../scripts/validate-bas.sh example-1.bas
./../../../../scripts/validate-bas.sh example-2.bas
```

See `/docs/LESSON-PREFLIGHT-CHECKLIST.md` for full workflow.

### Pre-commit Hook (Optional)

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash

# Find all staged .bas files
STAGED_BAS=$(git diff --cached --name-only --diff-filter=ACM | grep '\.bas$')

if [ -n "$STAGED_BAS" ]; then
    echo "🔍 Validating C64 BASIC files..."

    for FILE in $STAGED_BAS; do
        ./scripts/validate-bas.sh "$FILE"
        if [ $? -ne 0 ]; then
            echo ""
            echo "❌ Commit blocked: $FILE has validation errors"
            exit 1
        fi
    done

    echo "✅ All BASIC files validated"
fi

exit 0
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

### CI/CD Integration

Add to GitHub Actions workflow:

```yaml
- name: Validate C64 BASIC files
  run: |
    find code-samples -name "*.bas" | while read file; do
      ./scripts/validate-bas.sh "$file" || exit 1
    done
```

## Understanding Validation Errors

### Common Error: RESTORE with line number

**Error message**:
```
❌ Line 40: RESTORE with line number not supported in C64 BASIC V2 (use bare RESTORE)
```

**Problem**: C64 BASIC V2 only supports `RESTORE` (no arguments). Later BASIC versions like BASIC V7 allow `RESTORE 100`.

**Fix**:
```basic
❌ WRONG (BASIC V7+):
40 RESTORE 10

✅ CORRECT (C64 BASIC V2):
40 RESTORE
```

### Common Error: POKE value out of range

**Error message**:
```
❌ Line 80: POKE value 300 exceeds 255 (will cause ?ILLEGAL QUANTITY ERROR)
```

**Problem**: POKE values must be 0-255 (single byte). Values >255 cause `?ILLEGAL QUANTITY ERROR`.

**Fix**:
```basic
❌ WRONG:
80 POKE 53280,300

✅ CORRECT:
80 POKE 53280,44  rem 44 is a valid color (0-15)
```

### Common Error: Unsupported BASIC features

**Error message**:
```
❌ Line 60: WHILE...WEND not supported in C64 BASIC V2
```

**Problem**: Structured control flow (WHILE, DO, PROC) doesn't exist in C64 BASIC V2.

**Fix**:
```basic
❌ WRONG (BASIC V7+):
60 WHILE X<100
70 X=X+1
80 WEND

✅ CORRECT (C64 BASIC V2):
60 IF X>=100 THEN 90
70 X=X+1
80 GOTO 60
90 REM continue
```

### Common Warning: Sprite boundary

**Warning message**:
```
⚠️  Line 120: Sprite Y position 20 outside visible range (50-229)
```

**Problem**: Sprite is positioned outside the visible screen area. This isn't an error (won't crash), but the sprite won't be visible.

**Fix if unintentional**:
```basic
⚠️  BARELY VISIBLE:
120 POKE 53249,20  rem sprite 0 Y - too high

✅ VISIBLE:
120 POKE 53249,100  rem sprite 0 Y - middle of screen
```

Safe sprite ranges:
- **X**: 24-320 (uses MSB register 53264 for values >255)
- **Y**: 50-229 (visible screen area)

## Technical Details

### Why Two Tools?

**petcat** is a tokenizer that converts BASIC text to C64 binary format. It validates:
- Token correctness
- Basic syntax structure
- Line number format

It **cannot** detect:
- Wrong BASIC version features
- Invalid hardware addresses
- Value range errors
- Logical mistakes

**validate-c64-basic.py** uses pattern matching to detect semantic errors that would only appear at runtime.

### Limitations

Static analysis has inherent limitations:

**Cannot validate**:
- Variable values (only literal values in POKE statements)
- Runtime logic errors
- Performance issues
- Memory usage

**Example**:
```basic
10 A=300
20 POKE 53280,A  rem validator cannot detect A>255
```

The validator only catches literal values like `POKE 53280,300`.

**Best practice**: Use literals in hardware register access code for validator coverage.

## Hardware Register Reference

The validator checks addresses against these known ranges:

| Range | Description | Example Registers |
|-------|-------------|------------------|
| 1024-2023 | Screen RAM | Character display |
| 55296-56295 | Color RAM | Character colors |
| 2040-2047 | Sprite pointers | Sprite data location |
| 53248-53295 | VIC-II | Graphics chip |
| 54272-54300 | SID | Sound chip |
| 56320-56335 | CIA #1 | Keyboard, joystick |
| 56576-56591 | CIA #2 | Serial, timers |

Addresses outside these ranges generate warnings (not errors) since intentional low-memory access is sometimes valid.

## Troubleshooting

### "petcat: command not found"

Install VICE emulator which includes petcat:
```bash
brew install vice  # macOS
apt-get install vice  # Linux
```

### "python3: command not found"

Install Python 3:
```bash
brew install python  # macOS
apt-get install python3  # Linux
```

### False Positives

If the validator flags correct code:
1. Check if you're using a BASIC V2 extension or alternate dialect
2. Verify against [C64 BASIC V2 reference](https://www.c64-wiki.com/wiki/BASIC)
3. If validator is wrong, report as issue

### Need Help?

See `/docs/PETCAT-LIMITATIONS.md` for detailed background on petcat's limitations.

## Version History

- **1.0** (2025-01) - Initial release: RESTORE validation, POKE range checks, BASIC V2 feature detection
