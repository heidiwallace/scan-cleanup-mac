# scan-cleanup

`scan-cleanup` coordinates an interactive ScanTailor Advanced workflow for
scanned PDFs:

1. Extract each PDF page to an ordered PNG in a persistent run workspace.
2. Generate and open a ScanTailor Advanced project using the bundled settings.
3. Wait while the user reviews settings and produces TIFF pages in `out/`.
4. After ScanTailor closes, validate that every source page has exactly one TIFF.
5. Assemble TIFFs in the original PDF page order.
6. Add an invisible OCR layer and write `<input-name>_processed.pdf`.

The package never trusts filesystem iteration for page order. The extraction
order is recorded in `workspace.json`, and TIFFs are assembled only after a
complete one-to-one filename validation.

## Current development scope

The bundled project template contains the settings saved during the first
successful end-to-end test, including 600 DPI output and page-specific
transformations for exactly 40 pages. Saved Select Content and Page Layout
geometry is cleared when a default project is generated. Content detection starts
disabled; Page Box detection starts on Auto with Fine Tune Page Corners enabled.
Page Layout starts with "Match size with other pages" unchecked. Inputs with a
different page count stop with a clear error and preserve their workspace.
Generalizing templates to other page counts is planned.

Successful workspaces are also retained during development. The release version
will delete them only after the final OCR PDF has been verified. Failed
workspaces are always retained.

## Requirements

- Python 3.12+
- ScanTailor Advanced
- Tesseract
- Ghostscript

Automatic ScanTailor installation is intentionally deferred until the core
workflow has been validated. For now, pass its executable path explicitly or
set `SCANTAILOR_ADVANCED`.

## Installation

From a clone of the repository, create the locked development environment:

```bash
cd scan-cleanup
uv sync
```

On macOS, OCR dependencies can be installed with:

```bash
brew install tesseract ghostscript
```

## Process a PDF

```bash
uv run scan-cleanup process INPUT.pdf OUTPUT_DIRECTORY \
  --scantailor /path/to/scantailor-advanced
```

The final file is:

```text
OUTPUT_DIRECTORY/INPUT_processed.pdf
```

If that file already exists, the CLI asks before replacing it.

For a local ScanTailor Advanced build:

```bash
uv run scan-cleanup process tests/data/MH_1976_vIV_bio_1-40.pdf output \
  --scantailor /path/to/scantailor-advanced \
  --workspace-root development-workspaces
```

ScanTailor opens the generated project automatically. Review or adjust its
settings, process all pages at the Output stage, and then close the application.
The Python command resumes after the ScanTailor process exits.

## Resume a failed workspace

If ScanTailor closes with missing, extra, or unreadable TIFFs, the command stops
and prints the workspace path. Correct the issue with:

```bash
uv run scan-cleanup resume WORKSPACE OUTPUT_DIRECTORY
```

The same ScanTailor project reopens. After it closes, validation, PDF assembly,
and OCR are attempted again.

## Batch processing

```bash
uv run scan-cleanup batch INPUT_DIRECTORY OUTPUT_DIRECTORY \
  --scantailor /path/to/scantailor-advanced
```

ScanTailor opens once for each PDF, sequentially.

## Development

```bash
uv run pytest
uv run ruff check .
uv build
```

The GitHub Actions workflow performs the same lint, test, and package-build
checks on pushes and pull requests.

The pre-revamp Python image-processing implementation is stored under
`.snapshots/` with a SHA-256 checksum and is not part of the new Git history.
