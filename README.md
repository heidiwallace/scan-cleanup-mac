# scan-cleanup

`scan-cleanup` helps you clean up scanned PDFs (for example, old scanned
documents) so the pages are straightened, cropped, cleaned up, and turned
into a searchable PDF. It walks you through the process step by step:

1. It pulls each page out of your PDF as an image.
2. It opens a program called ScanTailor Advanced, already set up with good
   default settings, so you can look over and adjust each page.
3. Once you close ScanTailor Advanced, it automatically checks that every
   page came out correctly.
4. It puts the cleaned-up pages back together in the right order.
5. It makes the text on the pages searchable and saves the finished PDF.

## Getting set up

This section only needs to be done once. It walks through installing a few
free programs, plus `scan-cleanup` itself. Once it's done, skip down to
"Cleaning up a PDF" for everyday use.

Every step below is run in the **Terminal** app. If it's not already open,
find it by searching for "Terminal" in Spotlight (the magnifying glass in the
top-right corner of your screen, or press Cmd+Space). Each gray box below is a
command: click into the box to copy it, paste it into Terminal (Cmd+V), press
Enter, and wait for it to finish before moving to the next one.

### Step 1: Install Homebrew

Homebrew is a tool that makes it easy to install other software on a Mac. If
you're not sure whether you already have it, run:

```bash
brew --version
```

If you see a version number printed back, Homebrew is already installed —
skip ahead to Step 2. Otherwise, run:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow any on-screen instructions it gives you (it may ask for your Mac
password, and that's expected — nothing shows on screen as you type it, so
just type it and press Enter). When it finishes, run `brew --version` again
to confirm you now see a version number.

### Step 2: Install ScanTailor Advanced

ScanTailor Advanced is the program you'll use to review and adjust each
scanned page. There isn't a one-line install for it, so you'll build it from
its source code — Homebrew handles the hard parts. Paste each of these lines
into Terminal one at a time, waiting for each to finish before starting the
next (the build step can take several minutes):

```bash
brew install cmake ninja qt jpeg-turbo libpng libtiff
git clone https://github.com/ScanTailor-Advanced/scantailor-advanced.git
cmake -S scantailor-advanced -B scantailor-advanced/build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build scantailor-advanced/build
cmake --install scantailor-advanced/build --prefix "$(brew --prefix)"
```

Once this finishes, `scan-cleanup` will be able to find ScanTailor Advanced
automatically — you won't need to point to it manually. (If you'd rather
download the ready-made ScanTailor Advanced app instead, that also works, as
long as it ends up in your Applications folder.)

### Step 3: Install the other required programs

`scan-cleanup` also needs two more small programs: one that reads text out of
scanned pages (Tesseract), and one that helps assemble the final PDF
(Ghostscript). Install both with:

```bash
brew install tesseract ghostscript
```

### Step 4: Install uv

`uv` is the tool `scan-cleanup` uses to set itself up and run. Install it
with:

```bash
brew install uv
```

(`scan-cleanup` also needs Python, version 3.12 or newer — but you don't need
to install that yourself; `uv` will take care of it automatically the first
time it's needed.)

### Step 5: Download and set up scan-cleanup

Choose a location for `scan-cleanup` — for example, your Documents folder —
and navigate there in Terminal. If you'd like to put it in Documents, run:

```bash
cd ~/Documents
```

Then download a copy of `scan-cleanup` and set it up:

```bash
git clone https://github.com/heidiwallace/scan-cleanup-mac.git scan-cleanup
cd scan-cleanup
uv sync
```

That's it — setup is done, and you should now have a `scan-cleanup` folder
inside Documents (or wherever you chose). From now on, run every command
below from inside that folder — if you ever close Terminal and reopen it,
just run `cd ~/Documents/scan-cleanup` (adjusting the path if you chose
somewhere else) to get back there.

## Using scan-cleanup

Remember to `cd` into the `scan-cleanup` folder first (see Step 5 above) if
you've just opened a new Terminal window.

In the commands below, replace anything in ALL CAPS with your own file or
folder path — for example, `INPUT.pdf` becomes the actual path to your PDF,
and `OUTPUT_DIRECTORY` becomes the folder you want the result saved in. The
easiest way to get a path right is to type the command up to that point, then
drag the file or folder from Finder directly into the Terminal window — it
will fill in the correct path for you.

### Cleaning up a PDF

To clean up a single scanned PDF, run:

```bash
uv run scan-cleanup process INPUT.pdf OUTPUT_DIRECTORY
```

Replace `INPUT.pdf` with the path to your scanned PDF, and
`OUTPUT_DIRECTORY` with the folder where you want the finished file saved.
The finished file will appear as:

```text
OUTPUT_DIRECTORY/INPUT_processed.pdf
```

If a file with that name already exists, you'll be asked to confirm before
it gets replaced.

Shortly after you run the command, ScanTailor Advanced will open on its own
with your pages already loaded and good default settings applied. Look
through the pages, make any adjustments you'd like, then process all the
pages and close the ScanTailor Advanced window. `scan-cleanup` will notice
the window closed and automatically finish the job — assembling the pages
and making the text searchable.

When it's done, only your original PDF and the new finished PDF are kept;
everything created along the way is cleaned up automatically. If you'd like
to keep those in-between files (useful for troubleshooting), add
`--keep-workspace` to the command.

### If something goes wrong partway through

If ScanTailor Advanced closes but a page is missing or didn't come out
right, `scan-cleanup` will stop and tell you where your in-progress files are
being kept (this location is called the "workspace"). Fix the problem, then
pick up where you left off with:

```bash
uv run scan-cleanup resume WORKSPACE OUTPUT_DIRECTORY
```

(Use the workspace location `scan-cleanup` showed you.) This reopens
ScanTailor Advanced on the same project. Once you close it again,
`scan-cleanup` will check the pages and finish the job.

### Cleaning up many PDFs at once

If you have a whole folder of scanned PDFs to clean up, you can process them
one after another with a single command:

```bash
uv run scan-cleanup batch INPUT_DIRECTORY OUTPUT_DIRECTORY
```

ScanTailor Advanced will open once for each PDF in turn. If you need to stop
partway through, you can simply run the same command again later — any PDF
that's already been finished will be skipped automatically, so you'll pick up
right where you left off. If you'd like to redo files that were already
finished, add `--overwrite` to the command.



## Technical appendix

The rest of this README is written for contributors working on the
`scan-cleanup` codebase itself — it isn't needed to run the tool day to day.

### Development

Before opening a pull request, run the same checks the CI workflow runs:

```bash
uv run pytest
uv run ruff check .
uv build
```

GitHub Actions runs these three commands (lint, test, package build) on every
push and on every pull request.

### The bundled ScanTailor project template

Rather than generating a bare ScanTailor Advanced project from scratch for
every job, `scan-cleanup` ships a pre-configured project file at
`src/scan_cleanup/templates/scantailor-advanced-default.scantailor` and adapts
it to each input. This gives every job the same sensible Output-stage starting
point without the user having to configure ScanTailor Advanced by hand each
time (see "Default ScanTailor settings" below for exactly what it sets).

The template itself is just the project file saved at the end of the first
successful end-to-end test, so it reflects one real, human-reviewed 40-page
session (600 DPI output, plus that session's per-page transformations) rather
than being written by hand. Because the per-page geometry it contains (Select
Content, Page Layout) belongs to that specific 40-page scan, `scan-cleanup`
clears it when generating a new project — every job starts from a blank page
layout, while keeping the template's Output-stage recipe intact. Content
detection starts disabled; Page Box detection starts on Auto with Fine Tune
Page Corners enabled; "Match page size with other pages" starts unchecked.

### Default ScanTailor settings

These are the Output-stage settings baked into the bundled project template
and applied to every page by default. Any of them can be changed per-page (or
for the whole batch) inside the interactive ScanTailor Advanced session before
processing:

- Output DPI = 600
- Color mode = Black and white
- Binarization method = Otsu
- Otsu threshold adjustment = -15 (renders text thinner than a plain Otsu threshold)
- Despeckle level = 2 (Normal)
- Morphological smoothing = on
- Normalize illumination (B&W) = on
- Picture shape detection = Free, sensitivity 100
- Dewarping = off
- Content detection = disabled (Page Box detection: Auto, Fine Tune Page Corners = on)
- Match page size with other pages = off

### Input page counts beyond the template

Inputs are not limited to 40 pages. An input with fewer pages uses the
template's first N pages' settings; an input with more pages clones the
template's last page (files, filter settings, and the output recipe) for each
additional page, under fresh ids. Cloned pages inherit the same output recipe
(DPI, binarization, etc.) as the rest of the volume, but their auto-detected
geometry (page split, deskew, fix orientation) is a starting point, not a
guarantee — review it like any other page during the interactive ScanTailor
session.

### Workspace location and lifecycle

Each run creates a "workspace": a directory holding the extracted PNGs, the
generated `.ScanTailor` project, the resulting TIFFs, `workspace.json` (see
"Page ordering guarantee" below), and — once assembled — the pre-OCR PDF.

The workspace location depends only on `--workspace-root`; it is unrelated to
where the input PDF or output directory live (`workspace.py`'s
`create_workspace`). Without `--workspace-root`, the workspace is created under
the OS default temp directory (macOS: `$TMPDIR`, e.g.
`/var/folders/.../T/scan-cleanup-<stem>-<random>/`, where `<stem>` is the
input filename without its extension) regardless of whether the input or
output paths are inside a cloud-synced folder (Google Drive, Dropbox, etc.) —
so the hundreds of intermediate PNGs/TIFFs never get written into a folder a
sync client is watching, even with no flag at all. Passing
`--workspace-root DIR` only changes this for choosing a stable, inspectable
path (e.g. for use with `--keep-workspace`); if `DIR` is itself inside a
cloud-synced folder, prefer a local, non-synced path instead.

Successful workspaces are deleted after the final OCR PDF has been written.
Failed or incomplete workspaces are always retained, so their contents can be
inspected to diagnose what went wrong. During development, pass
`--keep-workspace` to retain a successful workspace for inspection too.

### Page ordering guarantee

The package never trusts filesystem iteration (e.g. directory listing order)
to determine page order, since that isn't guaranteed to match the original
PDF's page order across filesystems. Instead, the extraction step records the
authoritative order in `workspace.json`, and the final TIFFs are assembled
only after a complete one-to-one filename validation against that record.

### ScanTailor Advanced discovery on Linux and Windows

`resolve_scantailor()`'s fixed-location discovery (see "Step 2: Install
ScanTailor Advanced" above) only checks macOS install paths (the Homebrew
prefix and the official `.app` bundle location). On Linux and Windows it still
falls back to bare `PATH` discovery, with no fixed-location safety net —
adding equivalent fixed candidates for those platforms is planned.
