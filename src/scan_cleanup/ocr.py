"""Adds an invisible, searchable text layer to the final PDF via ocrmypdf."""

import os
import shutil
import sys
from pathlib import Path

import ocrmypdf

from scan_cleanup.config import Recipe

_REQUIRED_BINARIES = {
    "tesseract": "the OCR engine",
    "gs": "Ghostscript, used to process the PDF",
}

_INSTALL_INSTRUCTIONS = """
scan-cleanup requires two non-Python programs to be installed before OCR can
run: Tesseract (the OCR engine) and Ghostscript. These are NOT installed by
pip/uv — they need to be installed separately, like installing an app.

On a Mac, the easiest way is with Homebrew:

  1. If you don't already have Homebrew, open Terminal and run:
       /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
     Follow any instructions it prints when it finishes.

  2. Then install the required programs:
       brew install tesseract ghostscript

  3. Close and reopen Terminal, then run scan-cleanup again.

See the README's Installation section for more detail.
""".strip()


class MissingSystemDependencyError(RuntimeError):
    """Raised when a required non-Python program (Tesseract, Ghostscript) is missing."""


def _find_macos_homebrew_bin(command: str) -> Path | None:
    """Locate a Homebrew-installed binary directly, without relying on PATH.

    Mirrors resolve_scantailor()'s fixed-location fallback in
    scantailor.py: Homebrew's install prefix isn't guaranteed to be on PATH
    in every execution context (e.g. a non-interactive shell, a LaunchAgent,
    or a shell profile that was never updated), so a genuinely installed
    Tesseract or Ghostscript can still resolve to "missing" via
    shutil.which alone.
    """
    for prefix in ("/opt/homebrew", "/usr/local"):  # Apple Silicon, Intel
        candidate = Path(prefix, "bin", command)
        if candidate.is_file():
            return candidate
    return None


def _ensure_macos_homebrew_discoverable() -> None:
    """Make a standard Homebrew install of Tesseract/Ghostscript visible to
    shutil.which and ocrmypdf, even when Homebrew's prefix isn't on PATH.

    Prepending the discovered folder to this process's PATH makes it visible
    both to the check below and to every subprocess ocrmypdf launches
    afterward (subprocesses inherit the parent's environment).
    """
    for command in _REQUIRED_BINARIES:
        if shutil.which(command):
            continue
        found = _find_macos_homebrew_bin(command)
        if found is not None:
            os.environ["PATH"] = str(found.parent) + os.pathsep + os.environ.get("PATH", "")


def check_system_dependencies() -> None:
    if sys.platform == "darwin":
        _ensure_macos_homebrew_discoverable()
    missing = [name for name in _REQUIRED_BINARIES if shutil.which(name) is None]
    if missing:
        missing_desc = ", ".join(f"'{name}' ({_REQUIRED_BINARIES[name]})" for name in missing)
        raise MissingSystemDependencyError(
            f"Missing required program(s): {missing_desc}.\n\n{_INSTALL_INSTRUCTIONS}"
        )


def add_ocr_layer(pdf_path: Path, output_path: Path, recipe: Recipe) -> None:
    check_system_dependencies()
    ocrmypdf.ocr(
        pdf_path,
        output_path,
        language=recipe.ocr_language,
        output_type=recipe.ocr_output_type,
        # ScanTailor has already processed the page images; avoid changing
        # their pixels again while adding the invisible text layer.
        deskew=False,
        clean=False,
        remove_background=False,
    )
