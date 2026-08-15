# scan-cleanup — project memory

## Current architecture

This package no longer attempts to reproduce ScanTailor's image processing in
Python. It coordinates ScanTailor Advanced interactively:

```text
PDF -> ordered PNGs -> generated ScanTailor project -> user processing
    -> validated ordered TIFFs -> PDF -> OCR
```

The former Sauvola, deskew, and despeckle implementation was archived before
the revamp in `.snapshots/scan-cleanup-pre-scantailor-revamp-20260814-archive.tar.gz`.
The archive checksum is stored beside it.

## Important guarantees

- Page order comes from `workspace.json`, never directory enumeration.
- Final physical page size uses validated DPI metadata from the actual TIFFs,
  not the template value (users may change output DPI inside ScanTailor).
- ScanTailor output must exactly match the expected TIFF list.
- Missing, extra, or unreadable TIFFs preserve the workspace and stop the run.
- `scan-cleanup resume WORKSPACE OUTPUT_DIR` reopens the same project.
- OCR always runs.
- The final name is `<input-stem>_processed.pdf`.
- Existing output requires interactive confirmation in the CLI.

## Template behavior

The bundled version-4 project is at
`src/scan_cleanup/templates/scantailor-advanced-default.scantailor`.
It preserves page-specific transformations by ordinal. When generating a project
from the bundled template, the package clears saved Select Content and Page
Layout geometry. Content detection remains disabled, while automatic Page Box
detection has Fine Tune Page Corners enabled. Page Layout defaults to not matching
the page size with other pages. The template contains exactly 40 pages, so the
current generator deliberately rejects inputs with any other page count rather
than applying undefined settings.

The template's run-specific fields are replaced: source directory, filenames,
pixel dimensions, source DPI, and output directory. Internal IDs remain stable,
allowing all filter settings to continue referring to their corresponding page.
Stale rendered-output cache records are removed along with the saved geometry.
The template was updated from the project saved during the first successful
end-to-end test. Its output DPI is 600 and it includes the user's saved settings
from that test session.

## ScanTailor executable

The executable accepts a `.ScanTailor` project as its first argument. The
launcher supports an explicit `--scantailor` path, the
`SCANTAILOR_ADVANCED` environment variable, PATH discovery, and conventional
macOS application locations.

Cross-platform automatic discovery and installation is the final deferred task,
to be addressed only after the working package is validated.

## Workspace lifecycle

Successful workspaces are deleted by default after the final OCR PDF is safely
moved into place. The CLI's `--keep-workspace` option disables cleanup for
development and inspection. Failures always retain the workspace. A workspace
contains `input/`, `out/`, `project.ScanTailor`, `workspace.json`, and later
`assembled.pdf`.

## Validation

Run:

```bash
uv run pytest
uv run ruff check .
uv build
```

Manual validation should use a short sample first. The real 40-page scan remains
under `tests/data/` and is git-ignored.
