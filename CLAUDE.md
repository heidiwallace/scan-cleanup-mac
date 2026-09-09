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
- `scan-cleanup process` asks for interactive confirmation before replacing an
  existing output file. `scan-cleanup batch` instead skips, without prompting,
  any input whose output already exists — so an interrupted batch can be
  re-run to pick up only the unfinished files. Pass `--overwrite` to either
  command to bypass this and force reprocessing.

## Template behavior

The bundled version-4 project is at
`src/scan_cleanup/templates/scantailor-advanced-default.scantailor`.
It preserves page-specific transformations by ordinal. When generating a project
from the bundled template, the package clears saved Select Content and Page
Layout geometry. Content detection remains disabled, while automatic Page Box
detection has Fine Tune Page Corners enabled. Page Layout defaults to not matching
the page size with other pages. The template contains 40 pages, but the
generator (`_resize_pages` in `scantailor.py`) adapts it to any input page
count before applying those defaults:

- Fewer pages: keep the template's first N pages' settings, in scan order.
- More pages: clone the template's last page — its file/image/page nodes and
  every per-page filter entry (`fix-orientation`, `page-split`, `deskew`,
  `select-content`, `page-layout`, `output`) — once per extra page, assigning
  fresh sequential ids. `deskew` carries two parallel page-keyed structures
  (direct `page` children for content-based detection, plus an
  `image-settings/page` wrapper for the legacy image-based path); both are
  resized. `page-split` is keyed by image id, not page id, and is resized on
  that basis.

Cloned pages' auto-detection filters (page split, deskew, fix orientation) carry
forward the *previous* page's geometry as a placeholder — safe because those
filters run in `auto` mode, so a fresh page's content is intended to be
reviewed and re-detected by the user during the interactive ScanTailor session,
same as any other page. The output recipe (DPI, binarization method, etc.) is
the one setting that is genuinely meant to be identical across all pages, so
cloning it for extra pages is correct rather than a placeholder.

The template's run-specific fields are replaced: source directory, filenames,
pixel dimensions, source DPI, and output directory. Internal IDs remain stable,
allowing all filter settings to continue referring to their corresponding page.
Stale rendered-output cache records are removed along with the saved geometry.
The template was updated from the project saved during the first successful
end-to-end test. Its output DPI is 600 and it includes the user's saved settings
from that test session.

The output recipe's Otsu threshold adjustment (`thresholdAdj` on every page's
`<bw>` element) is set to `-15` (previously `0`), which renders text thinner
than the plain Otsu threshold would. See the README's "Default ScanTailor
settings" for the full human-readable list of bundled defaults.

## ScanTailor executable

The executable accepts a `.ScanTailor` project as its first argument.
`resolve_scantailor()` in `scantailor.py` checks, in order: an explicit
`--scantailor` path, the `SCANTAILOR_ADVANCED` environment variable, PATH
discovery, then fixed macOS install locations checked directly (independent of
PATH, since PATH is not guaranteed set in every execution context):
`$(brew --prefix)/bin/scantailor-advanced` (both the Apple Silicon and Intel
Homebrew prefixes are checked) and the official `.app` bundle locations.

`$(brew --prefix)/bin/scantailor-advanced` is the supported, documented install
location for this package (see README's "Installing ScanTailor Advanced"). There
is no upstream Homebrew formula; it is a plain `cmake --install --prefix
"$(brew --prefix)"` of the upstream source (github.com/ScanTailor-Advanced/scantailor-advanced).
Because its dependencies (Qt, libtiff, libpng, jpeg-turbo) are linked via
absolute Homebrew paths rather than relative rpaths, the installed binary is
fully standalone — it does not depend on the source checkout it was built from,
and that checkout can be deleted or moved after install.

Cross-platform automatic discovery and installation (Linux, Windows) is the
final deferred task, to be addressed only after the working package is
validated.

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
