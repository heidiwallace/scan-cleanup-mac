"""Tesseract/Ghostscript discovery, including the Homebrew fixed-location
fallback used when Homebrew's prefix isn't on PATH.
"""

from __future__ import annotations

import pytest

from scan_cleanup import ocr


def test_check_system_dependencies_passes_when_both_present(monkeypatch):
    monkeypatch.setattr(ocr.shutil, "which", lambda _name: "/opt/homebrew/bin/x")
    ocr.check_system_dependencies()  # must not raise


def test_missing_dependency_names_the_program(monkeypatch):
    monkeypatch.setattr(
        ocr.shutil, "which", lambda name: "/opt/homebrew/bin/tesseract" if name == "tesseract" else None
    )
    with pytest.raises(ocr.MissingSystemDependencyError, match="gs"):
        ocr.check_system_dependencies()


# --- Homebrew fixed-location discovery on macOS ------------------------------
#
# Homebrew's install prefix isn't guaranteed to be on PATH in every execution
# context (a non-interactive shell, a LaunchAgent, a shell profile that was
# never updated), so a genuinely installed Tesseract or Ghostscript can still
# resolve to "missing" via shutil.which alone.


def test_find_macos_homebrew_bin_returns_none_when_absent():
    # Real, hardcoded Homebrew prefixes (mirroring resolve_scantailor()'s
    # equivalent macOS branch in scantailor.py, which is likewise not
    # unit-tested against fake paths for the same reason): a command name
    # that can't plausibly exist under either prefix confirms the "not
    # found" path without needing a real Homebrew install.
    assert ocr._find_macos_homebrew_bin("a-command-that-does-not-exist-anywhere") is None


def test_ensure_macos_homebrew_discoverable_prepends_path_when_found(monkeypatch, tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "tesseract").write_text("stub")
    (bin_dir / "gs").write_text("stub")

    monkeypatch.setattr(ocr.shutil, "which", lambda _name: None)  # nothing on PATH
    monkeypatch.setattr(ocr, "_find_macos_homebrew_bin", lambda command: bin_dir / command)
    monkeypatch.setenv("PATH", "/somewhere/else")

    ocr._ensure_macos_homebrew_discoverable()

    assert ocr.os.environ["PATH"].split(ocr.os.pathsep)[0] == str(bin_dir)


def test_ensure_macos_homebrew_discoverable_noop_when_already_on_path(monkeypatch):
    monkeypatch.setattr(ocr.shutil, "which", lambda name: f"/opt/homebrew/bin/{name}")
    monkeypatch.setenv("PATH", "/unchanged")

    ocr._ensure_macos_homebrew_discoverable()

    assert ocr.os.environ["PATH"] == "/unchanged"


def test_check_system_dependencies_calls_macos_discovery_only_on_darwin(monkeypatch):
    """check_system_dependencies() must invoke the Homebrew fallback only on darwin."""
    called = []
    monkeypatch.setattr(ocr, "_ensure_macos_homebrew_discoverable", lambda: called.append(1))
    monkeypatch.setattr(ocr.shutil, "which", lambda _name: "present")

    monkeypatch.setattr(ocr.sys, "platform", "win32")
    ocr.check_system_dependencies()
    assert called == []

    monkeypatch.setattr(ocr.sys, "platform", "darwin")
    ocr.check_system_dependencies()
    assert called == [1]
