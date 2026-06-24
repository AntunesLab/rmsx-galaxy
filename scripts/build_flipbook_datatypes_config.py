#!/usr/bin/env python3
"""Build a full Galaxy datatypes config that includes Flipbook Molstar manifests."""

from __future__ import annotations

import argparse
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "config" / "datatypes" / "merged_datatypes_conf.xml"
FLIPBOOK_EXTENSION = "flipbookmolstar"
FLIPBOOK_DATATYPE = {
    "extension": FLIPBOOK_EXTENSION,
    "type": "galaxy.datatypes.text:Json",
    "subclass": "True",
    "mimetype": "application/json",
    "display_in_upload": "true",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--galaxy-root",
        type=Path,
        help="Galaxy checkout root. Defaults to the newest tmp*/galaxy-dev checkout, then local Planemo resources.",
    )
    parser.add_argument(
        "--base",
        type=Path,
        help="Existing full Galaxy datatypes_conf.xml or datatypes_conf.xml.sample to extend.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Merged config output path. Default: {DEFAULT_OUTPUT}",
    )
    return parser.parse_args()


def newest_tmp_galaxy_root() -> Path | None:
    candidates = []
    tmp_root = Path(tempfile.gettempdir()).resolve()
    for path in tmp_root.glob("tmp*/galaxy-dev"):
        if (path / "lib" / "galaxy" / "config" / "sample" / "datatypes_conf.xml.sample").is_file():
            candidates.append(path)
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def candidate_base_configs(galaxy_root: Path | None) -> list[Path]:
    candidates: list[Path] = []
    if galaxy_root:
        candidates.append(galaxy_root / "lib" / "galaxy" / "config" / "sample" / "datatypes_conf.xml.sample")
        candidates.append(galaxy_root / "config" / "datatypes_conf.xml")
    candidates.extend(PROJECT_ROOT.glob(".venv-planemo/lib/python*/site-packages/galaxy/tool_util/linters/datatypes_conf.xml.sample"))
    return candidates


def resolve_base_config(args: argparse.Namespace) -> Path:
    if args.base:
        base = args.base.resolve()
        if not base.is_file():
            raise SystemExit(f"Base datatype config does not exist: {base}")
        return base

    galaxy_root = args.galaxy_root.resolve() if args.galaxy_root else newest_tmp_galaxy_root()
    for candidate in candidate_base_configs(galaxy_root):
        if candidate.is_file():
            return candidate.resolve()
    raise SystemExit("Could not find a Galaxy datatypes_conf.xml.sample. Pass --base explicitly.")


def ensure_registration(root: ET.Element) -> ET.Element:
    registration = root.find("registration")
    if registration is None:
        registration = ET.SubElement(root, "registration")
    return registration


def add_flipbook_datatype(root: ET.Element) -> bool:
    registration = ensure_registration(root)
    for datatype in registration.findall("datatype"):
        if datatype.get("extension") == FLIPBOOK_EXTENSION:
            for key, value in FLIPBOOK_DATATYPE.items():
                datatype.set(key, value)
            return False
    ET.SubElement(registration, "datatype", FLIPBOOK_DATATYPE)
    return True


def indent_xml(element: ET.Element, level: int = 0) -> None:
    child_indent = "\n" + ("    " * (level + 1))
    current_indent = "\n" + ("    " * level)
    children = list(element)
    if children:
        if not element.text or not element.text.strip():
            element.text = child_indent
        for child in children:
            indent_xml(child, level + 1)
        if not children[-1].tail or not children[-1].tail.strip():
            children[-1].tail = current_indent
    if level and (not element.tail or not element.tail.strip()):
        element.tail = current_indent


def main() -> None:
    args = parse_args()
    base = resolve_base_config(args)
    output = args.output.resolve()

    tree = ET.parse(base)
    root = tree.getroot()
    added = add_flipbook_datatype(root)
    if hasattr(ET, "indent"):
        ET.indent(tree, space="    ")
    else:
        indent_xml(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output, encoding="utf-8", xml_declaration=True)

    action = "Added" if added else "Updated"
    print(f"Base datatypes: {base}")
    print(f"{action} {FLIPBOOK_EXTENSION} datatype.")
    print(f"Merged datatypes: {output}")
    print("Use with: GALAXY_CONFIG_OVERRIDE_DATATYPES_CONFIG_FILE=" + str(output))


if __name__ == "__main__":
    try:
        main()
    except ET.ParseError as error:
        print(f"Could not parse datatype config: {error}", file=sys.stderr)
        raise SystemExit(2) from error
