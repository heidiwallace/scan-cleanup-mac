import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import numpy as np
import pytest

from scan_cleanup.scantailor import (
    ScanTailorError,
    expected_tiff_names,
    generate_project,
    validate_output,
)


def write_template(path: Path, page_count: int = 2) -> Path:
    root = ET.Element("project", version="4", outputDirectory="old/out")
    directories = ET.SubElement(root, "directories")
    ET.SubElement(directories, "directory", id="1", path="old/input")
    files = ET.SubElement(root, "files")
    images = ET.SubElement(root, "images")
    pages = ET.SubElement(root, "pages")
    filters = ET.SubElement(root, "filters")
    deskew = ET.SubElement(filters, "deskew")
    output = ET.SubElement(filters, "output")
    for index in range(page_count):
        file_id = str(index * 3 + 2)
        image_id = str(index * 3 + 3)
        page_id = str(index * 3 + 4)
        ET.SubElement(files, "file", id=file_id, dirId="1", name=f"old-{index}.png")
        image = ET.SubElement(
            images, "image", id=image_id, fileId=file_id, fileImage="0", subPages="1"
        )
        ET.SubElement(image, "size", width="100", height="200")
        ET.SubElement(image, "dpi", horizontal="300", vertical="300")
        ET.SubElement(pages, "page", id=page_id, imageId=image_id, subPage="single")
        settings = ET.SubElement(deskew, "page", id=page_id)
        ET.SubElement(settings, "rotation", value=str(index + 0.25))
        output_page = ET.SubElement(output, "page", id=page_id)
        params = ET.SubElement(output_page, "params")
        ET.SubElement(params, "dpi", horizontal="1200", vertical="1200")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    return path


def write_page(path: Path, width: int, height: int) -> None:
    assert cv2.imwrite(str(path), np.full((height, width), 255, dtype=np.uint8))


def test_generate_project_retargets_files_and_preserves_geometry(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    output_dir.mkdir()
    page_paths = [input_dir / "volume-01.png", input_dir / "volume-02.png"]
    write_page(page_paths[0], 80, 120)
    write_page(page_paths[1], 90, 130)
    template = write_template(tmp_path / "template.ScanTailor")
    project = tmp_path / "project.ScanTailor"

    output_dpi = generate_project(page_paths, output_dir, project, 400, template)

    root = ET.parse(project).getroot()
    assert output_dpi == 1200
    assert root.attrib["outputDirectory"] == str(output_dir.resolve())
    assert root.find("./directories/directory").attrib["path"] == str(input_dir.resolve())
    assert [node.attrib["name"] for node in root.findall("./files/file")] == [
        "volume-01.png",
        "volume-02.png",
    ]
    assert root.find("./images/image/size").attrib == {"width": "80", "height": "120"}
    assert root.find("./images/image/dpi").attrib == {"horizontal": "400", "vertical": "400"}
    assert root.find("./filters/deskew/page/rotation").attrib["value"] == "0.25"


def test_generate_project_rejects_page_count_mismatch(tmp_path):
    page = tmp_path / "one.png"
    write_page(page, 10, 10)

    with pytest.raises(ScanTailorError, match="settings for 2 pages"):
        generate_project(
            [page], tmp_path / "out", tmp_path / "project.ScanTailor", 300,
            write_template(tmp_path / "template.ScanTailor"),
        )


def test_validate_output_returns_manifest_order_not_directory_order(tmp_path):
    for name, value in (("volume-02.tif", 20), ("volume-01.tif", 10), ("volume-03.tif", 30)):
        assert cv2.imwrite(str(tmp_path / name), np.full((5, 5), value, dtype=np.uint8))

    result = validate_output(
        tmp_path, ["volume-01.tif", "volume-02.tif", "volume-03.tif"]
    )

    assert [path.name for path in result] == [
        "volume-01.tif",
        "volume-02.tif",
        "volume-03.tif",
    ]


def test_validate_output_reports_missing_and_unexpected_pages(tmp_path):
    write_page(tmp_path / "volume-01.tif", 5, 5)
    write_page(tmp_path / "extra.tif", 5, 5)

    with pytest.raises(ScanTailorError) as error:
        validate_output(tmp_path, ["volume-01.tif", "volume-02.tif"])

    assert "missing: volume-02.tif" in str(error.value)
    assert "unexpected: extra.tif" in str(error.value)


def test_expected_tiff_names_follow_extracted_page_names():
    pages = [Path("volume-01.png"), Path("volume-10.png"), Path("volume-100.png")]
    assert expected_tiff_names(pages) == [
        "volume-01.tif",
        "volume-10.tif",
        "volume-100.tif",
    ]
