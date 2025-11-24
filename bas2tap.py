#!/usr/bin/env python3
"""
Simple BASIC to TAP converter for ZX Spectrum
Converts plain text BASIC listing to TAP file format
"""

import sys
import struct

def tokenize_basic(line):
    """Convert BASIC line to tokenized form"""
    # This is a simplified tokenizer - ZX Spectrum keywords
    tokens = {
        'REM': b'\xea',
        'LET': b'\xf1',
        'PRINT': b'\xf5',
        'GO TO': b'\xec',
        'GO SUB': b'\xed',
        'RETURN': b'\xf8',
        'IF': b'\xfa',
        'THEN': b'\xcb',
        'FOR': b'\xeb',
        'NEXT': b'\xf3',
        'TO': b'\xcc',
        'STEP': b'\xcd',
        'CLS': b'\xfb',
        'BORDER': b'\xe7',
        'PAPER': b'\xda',
        'INK': b'\xd9',
        'PAUSE': b'\xf2',
        'AT': b'\x16',
        'INPUT': b'\xee',
        'DIM': b'\xe9',
        'BEEP': b'\xf4',
        'CIRCLE': b'\xc5',
        'PLOT': b'\xf0',
        'DRAW': b'\xf9',
        'OVER': b'\xe1',
        'BRIGHT': b'\xdb',
        'FLASH': b'\xdc',
        'INVERSE': b'\xd8',
        'INKEY$': b'\xa5',
        'AND': b'\xc8',
        'OR': b'\xc7',
    }

    # Replace keywords with tokens (longest first)
    result = line
    for keyword, token in sorted(tokens.items(), key=lambda x: -len(x[0])):
        result = result.replace(keyword, token.decode('latin1'))

    return result.encode('latin1')

def create_tap_block(data, block_type=0xff):
    """Create a TAP block with header"""
    # Block format: length(2) + flag(1) + data + checksum(1)
    flag = bytes([block_type])
    block_data = flag + data

    # Calculate checksum
    checksum = 0
    for byte in block_data:
        checksum ^= byte

    block = block_data + bytes([checksum])
    length = len(block) - 1  # Length doesn't include checksum

    return struct.pack('<H', len(block)) + block

def bas2tap(bas_file, tap_file, program_name='program'):
    """Convert BASIC text file to TAP file"""
    # Read BASIC file
    with open(bas_file, 'r') as f:
        lines = f.readlines()

    # Parse and tokenize BASIC lines
    basic_data = b''
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Parse line number
        parts = line.split(' ', 1)
        if not parts[0].isdigit():
            continue

        line_num = int(parts[0])
        line_content = parts[1] if len(parts) > 1 else ''

        # Tokenize content
        tokenized = tokenize_basic(line_content)

        # Line format: line_num(2) + length(2) + content + 0x0d
        line_length = len(tokenized) + 1  # +1 for 0x0d
        basic_line = struct.pack('>H', line_num) + struct.pack('<H', line_length) + tokenized + b'\x0d'
        basic_data += basic_line

    # Create program header
    program_name_bytes = program_name.ljust(10)[:10].encode('ascii')
    autostart_line = 10  # Auto-run from line 10

    header = program_name_bytes + struct.pack('<HHH', len(basic_data), autostart_line, len(basic_data))

    # Create TAP file
    with open(tap_file, 'wb') as f:
        # Write header block
        f.write(create_tap_block(bytes([0]) + header, 0x00))
        # Write data block
        f.write(create_tap_block(basic_data, 0xff))

    print(f"Created {tap_file} ({len(basic_data)} bytes of BASIC)")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: bas2tap.py input.bas output.tap [program_name]")
        sys.exit(1)

    bas_file = sys.argv[1]
    tap_file = sys.argv[2]
    program_name = sys.argv[3] if len(sys.argv) > 3 else 'example1'

    bas2tap(bas_file, tap_file, program_name)
