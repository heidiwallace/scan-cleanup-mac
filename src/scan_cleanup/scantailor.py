"""ScanTailor project generation, launching, and output validation."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from importlib.resources import files
from pathlib import Path

import cv2


class ScanTailorError(RuntimeError):
    """Raised when ScanTailor cannot be launched or produces invalid output."""


def default_template_path() -> Path:
    resource = files("scan_cleanup").joinpath("templates/scantailor-advanced-default.scantailor")
    return Path(str(resource))


def resolve_scantailor(explicit: Path | None = None) -> Path:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit.expanduser())
    if env_path := os.environ.get("SCANTAILOR_ADVANCED"):
        candidates.append(Path(env_path).expanduser())

    for command in ("scantailor-advanced", "scantailor-advanced.exe"):
        if found := shutil.which(command):
            candidates.append(Path(found))

    if sys.platform == "darwin":
        candidates.extend(
            [
                Path(
                    "/Applications/ScanTailor Advanced.app/Contents/MacOS/"
                    "scantailor-advanced"
                ),
                Path.home()
                / "Applications/ScanTailor Advanced.app/Contents/MacOS/scantailor-advanced",
            ]
        )

    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()

    checked = ", ".join(str(path) for path in candidates) or "the system PATH"
    raise ScanTailorError(
        "ScanTailor Advanced executable was not found. Pass --scantailor PATH or set "
        f"SCANTAILOR_ADVANCED. Checked: {checked}"
    )


def _template_output_dpi(root: ET.Element) -> int:
    output_filter = root.find("./filters/output")
    if output_filter is None:
        raise ScanTailorError("Template has no output filter settings")
    dpi = output_filter.find(".//dpi")
    if dpi is None or "horizontal" not in dpi.attrib:
        raise ScanTailorError("Template has no output DPI setting")
    return int(dpi.attrib["horizontal"])


def generate_project(
    page_paths: list[Path],
    output_dir: Path,
    project_path: Path,
    source_dpi: int,
    template_path: Path | None = None,
) -> int:
    """Generate a project while preserving template settings page-for-page."""
    template_path = template_path or default_template_path()
    tree = ET.parse(template_path)
    root = tree.getroot()

    files_node = root.find("files")
    images_node = root.find("images")
    pages_node = root.find("pages")
    directory = root.find("./directories/directory")
    if any(node is None for node in (files_node, images_node, pages_node, directory)):
        raise ScanTailorError("Template is missing required project structure")

    template_files = list(files_node)
    template_images = list(images_node)
    template_pages = list(pages_node)
    expected = len(template_pages)
    if not (len(template_files) == len(template_images) == expected):
        raise ScanTailorError("Template has inconsistent file, image, and page counts")
    if len(page_paths) != expected:
        raise ScanTailorError(
            f"Template contains settings for {expected} pages, but the input PDF has "
            f"{len(page_paths)} pages. The workspace has been preserved."
        )

    root.set("outputDirectory", str(output_dir.resolve()))
    directory.set("path", str(page_paths[0].parent.resolve()))

    for file_node, image_node, page_path in zip(
        template_files, template_images, page_paths, strict=True
    ):
        image = cv2.imread(str(page_path), cv2.IMREAD_UNCHANGED)
        if image is None:
            raise ScanTailorError(f"Could not read extracted page: {page_path}")
        height, width = image.shape[:2]
        file_node.set("name", page_path.name)
        size = image_node.find("size")
        dpi = image_node.find("dpi")
        if size is None or dpi is None:
            raise ScanTailorError("Template image record is missing size or DPI")
        size.set("width", str(width))
        size.set("height", str(height))
        dpi.set("horizontal", str(source_dpi))
        dpi.set("vertical", str(source_dpi))

    ET.indent(tree, space="  ")
    tree.write(project_path, encoding="utf-8", xml_declaration=True)
    return _template_output_dpi(root)


def launch_scantailor(executable: Path, project_path: Path) -> None:
    try:
        completed = subprocess.run([str(executable), str(project_path)], check=False)
    except OSError as exc:
        raise ScanTailorError(f"Could not launch ScanTailor Advanced: {exc}") from exc
    if completed.returncode != 0:
        raise ScanTailorError(
            f"ScanTailor Advanced exited with status {completed.returncode}. "
            "The workspace has been preserved."
        )


def expected_tiff_names(page_paths: list[Path]) -> list[str]:
    return [f"{path.stem}.tif" for path in page_paths]


def validate_output(output_dir: Path, expected_names: list[str]) -> list[Path]:
    actual = {
        path.name: path
        for path in output_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".tif", ".tiff"}
    }
    expected = set(expected_names)
    missing = sorted(expected - set(actual))
    unexpected = sorted(set(actual) - expected)

    unreadable = []
    for name in expected_names:
        path = actual.get(name)
        if path is not None and cv2.imread(str(path), cv2.IMREAD_UNCHANGED) is None:
            unreadable.append(name)

    if missing or unexpected or unreadable:
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if unexpected:
            details.append("unexpected: " + ", ".join(unexpected))
        if unreadable:
            details.append("unreadable: " + ", ".join(unreadable))
        raise ScanTailorError(
            "ScanTailor output is incomplete or invalid (" + "; ".join(details) + "). "
            "The workspace has been preserved."
        )

    return [actual[name] for name in expected_names]
