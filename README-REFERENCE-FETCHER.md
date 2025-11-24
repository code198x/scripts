# Reference Materials Scripts

**Purpose:** Automate downloading and searching of authoritative reference manuals from Internet Archive.

---

## Quick Start

### 1. Download All Reference Materials

```bash
cd /Users/stevehill/Projects/Code198x/scripts
./fetch-reference-materials.sh
```

This will:
- Download 6 PDFs from Internet Archive (~50-100MB total)
- Extract searchable text from each PDF
- Save everything to `/docs/source-materials/`

**Time estimate:** 5-10 minutes depending on connection speed

### 2. Search the Materials

```bash
# Search all platforms for "sprite"
./search-reference-materials.sh "sprite"

# Search only NES materials
./search-reference-materials.sh "PPU" --platform nes

# Search with more context (5 lines before/after)
./search-reference-materials.sh "blitter" --platform amiga --context 5

# Case-sensitive search
./search-reference-materials.sh "POKE" --platform zx-spectrum --case-sensitive
```

---

## What Gets Downloaded

### NES (Nintendo Entertainment System)
- **NES Programmers Reference Guide (EA 1989)** - Professional third-party developer docs
- **NES Programmers Reference Guide (Sculptured Software)** - Reverse-engineered reference

### ZX Spectrum
- **ZX Spectrum BASIC Programming Manual** - Official Sinclair manual

### Amiga
- **AMOS Professional Manual** - Complete AMOS BASIC reference
- **Amiga Hardware Reference Manual (3rd Edition)** - OCS/ECS chipset specs

### Commodore 64
- **C64 Programmer's Reference Guide** - Official Commodore reference

**Total download size:** ~50-100MB  
**Text extraction size:** ~5-10MB

---

## Requirements

### macOS Installation

```bash
# Install via Homebrew
brew install wget poppler

# Verify installation
wget --version
pdftotext -v
```

### What Each Tool Does
- **wget** - Downloads files from Internet Archive
- **pdftotext** (from poppler) - Extracts searchable text from PDFs

---

## Script Details

### fetch-reference-materials.sh

**Synopsis:**
```bash
./fetch-reference-materials.sh [--no-extract]
```

**Options:**
- `--no-extract` - Skip text extraction (faster, PDFs only)

**Output Structure:**
```
docs/source-materials/
├── nes/
│   ├── NES-Programmers-Reference-Guide-EA-1989.pdf
│   ├── NES-Programmers-Reference-Guide-EA-1989.txt
│   ├── NES-Programmers-Reference-Guide-Sculptured-Software.pdf
│   └── NES-Programmers-Reference-Guide-Sculptured-Software.txt
├── zx-spectrum/
│   ├── ZX-Spectrum-BASIC-Programming.pdf
│   └── ZX-Spectrum-BASIC-Programming.txt
├── amiga/
│   ├── AMOS-Professional-Manual.pdf
│   ├── AMOS-Professional-Manual.txt
│   ├── Amiga-Hardware-Reference-Manual-3rd-Ed.pdf
│   └── Amiga-Hardware-Reference-Manual-3rd-Ed.txt
└── c64/
    ├── C64-Programmers-Reference-Guide.pdf
    └── C64-Programmers-Reference-Guide.txt
```

**Features:**
- ✅ Skips existing files (re-run safe)
- ✅ Shows progress for each download
- ✅ Displays file sizes
- ✅ Validates dependencies before starting
- ✅ Color-coded output
- ✅ Summary statistics

**Exit Codes:**
- `0` - Success (all or some files downloaded)
- `1` - Missing dependencies or critical error

---

### search-reference-materials.sh

**Synopsis:**
```bash
./search-reference-materials.sh <search-term> [options]
```

**Options:**
- `--platform <name>` - Search only one platform (nes, zx-spectrum, amiga, c64)
- `--context <n>` - Show n lines before/after match (default: 2)
- `--ignore-case` - Case-insensitive search (default)
- `--case-sensitive` - Case-sensitive search

**Examples:**

```bash
# Find all references to sprites across all platforms
./search-reference-materials.sh "sprite"

# Find NES PPU register documentation
./search-reference-materials.sh "\$2000" --platform nes --context 5

# Find AMOS Bob commands
./search-reference-materials.sh "Bob " --platform amiga

# Find ZX Spectrum POKE examples (case-sensitive)
./search-reference-materials.sh "POKE" --platform zx-spectrum --case-sensitive

# Find blitter operations with lots of context
./search-reference-materials.sh "blitter" --platform amiga --context 10
```

**Output:**
- Groups results by platform
- Shows match count per file
- Displays context around matches
- Color-codes for readability
- Limits output to 100 lines per file (shows count if more)

---

## Common Use Cases

### 1. Validating Quick References

```bash
# Check if our sprite documentation matches the manual
./search-reference-materials.sh "sprite" --platform nes --context 3

# Compare with our PPU-PROGRAMMING-QUICK-REFERENCE.md
```

### 2. Researching New Topics

```bash
# Learn about ZX Spectrum UDG (User-Defined Graphics)
./search-reference-materials.sh "user defined graphics" --platform zx-spectrum

# Understand Amiga Copper instructions
./search-reference-materials.sh "WAIT\|MOVE\|SKIP" --platform amiga
```

### 3. Finding Code Examples

```bash
# Find BASIC examples with PLOT
./search-reference-materials.sh "PLOT" --platform zx-spectrum --context 5

# Find assembly code with LDA
./search-reference-materials.sh "LDA" --platform nes --context 3
```

### 4. Checking Hardware Specifications

```bash
# Find exact PPU timing details
./search-reference-materials.sh "cycle\|timing" --platform nes

# Find palette information
./search-reference-materials.sh "palette\|colour" --context 5
```

---

## Tips & Tricks

### Regex Patterns

The search supports basic grep regex:

```bash
# Find either "sprite" or "sprites"
./search-reference-materials.sh "sprites\?"

# Find "PPU" followed by any character and "register"
./search-reference-materials.sh "PPU.register"

# Find lines with both "blitter" and "DMA"
./search-reference-materials.sh "blitter.*DMA\|DMA.*blitter" --platform amiga
```

### Piping to Files

```bash
# Save search results for later
./search-reference-materials.sh "sprite" --platform nes > nes-sprite-research.txt

# Search and page through results
./search-reference-materials.sh "AMOS" --platform amiga | less
```

### Quick Grep on Text Files

```bash
# Direct grep for maximum flexibility
grep -i "copper" docs/source-materials/amiga/*.txt

# Case-sensitive with line numbers
grep -n "POKE" docs/source-materials/zx-spectrum/*.txt

# Count occurrences
grep -c "sprite" docs/source-materials/nes/*.txt
```

---

## Troubleshooting

### "Missing dependencies: wget poppler"

**Solution:**
```bash
brew install wget poppler
```

Or run with `--no-extract` to skip text extraction:
```bash
./fetch-reference-materials.sh --no-extract
```

### "Download failed"

**Possible causes:**
1. Internet Archive temporarily unavailable
2. Network connection issue
3. Incorrect URL (archive.org content moved)

**Solutions:**
- Wait a few minutes and try again
- Check your internet connection
- Visit the archive.org URL directly in a browser to verify it exists

### "No text files found"

**Solution:**
Run the fetch script first:
```bash
./fetch-reference-materials.sh
```

### Downloads are slow

**Normal:** PDFs are 5-20MB each. Total download ~50-100MB.

**Speed it up:**
- Run with `--no-extract` first, extract later
- Download only what you need (edit script to comment out others)

---

## Maintenance

### Re-downloading a Specific File

Delete the PDF and run fetch script:

```bash
rm docs/source-materials/nes/NES-Programmers-Reference-Guide-EA-1989.pdf
rm docs/source-materials/nes/NES-Programmers-Reference-Guide-EA-1989.txt
./fetch-reference-materials.sh
```

### Extracting Text from Existing PDFs

If you already have PDFs but no text files:

```bash
cd docs/source-materials/nes
pdftotext -layout NES-Programmers-Reference-Guide-EA-1989.pdf
```

Or re-run fetch script (it will skip existing PDFs):
```bash
./fetch-reference-materials.sh
```

### Updating Archive.org URLs

If archive.org moves a file, edit `fetch-reference-materials.sh`:

1. Find the `download_file` call for that material
2. Update the URL (first parameter)
3. Keep the output filename and description the same

---

## Git Considerations

### .gitignore Recommendations

The PDFs and text files are **large** and shouldn't be committed to git:

```gitignore
# In /docs/source-materials/.gitignore
*.pdf
*.txt
```

**Exception:** If you want to commit the materials, ensure:
- Your git repository allows large files
- You're not using GitHub (100MB file limit)
- Or use Git LFS for the PDFs

### Sharing the Materials

**Don't commit PDFs.** Instead, share the fetcher script:

```bash
# New team member setup
git clone <repo>
cd scripts
./fetch-reference-materials.sh
```

---

## Credits

All materials sourced from [Internet Archive](https://archive.org):
- Archive.org is a non-profit digital library
- Materials used under fair use for educational reference
- Original copyright holders retain all rights

**Direct links:**
- NES EA Guide: https://archive.org/details/nes-programmers-reference-guide-by-electronic-arts-1989
- AMOS Manual: https://archive.org/details/AmosProfessionalManual
- Amiga Hardware Manual: https://archive.org/details/amiga-hardware-reference-manual-3rd-edition
- C64 PRG: https://archive.org/details/c64-programmer-ref

---

**Version:** 1.0  
**Created:** 2025-10-24  
**For:** Code Like It's 198x curriculum development
