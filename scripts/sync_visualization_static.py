#!/usr/bin/env python3
"""Mirror local Galaxy visualization assets into an active Galaxy checkout.

Planemo registers visualization plugins from the configured plugin directory,
but Galaxy serves visualization entry-point files from
``static/plugins/visualizations/<plugin>/static``. For local Planemo runs the
Galaxy checkout is usually temporary, so this helper mirrors the project plugin
into the active checkout after ``planemo serve`` starts.
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLUGIN = "rmsx_molstar"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--galaxy-root",
        type=Path,
        help="Galaxy checkout root. Defaults to the newest tmp*/galaxy-dev directory.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
        help=f"Project root containing config/plugins/visualizations. Default: {PROJECT_ROOT}",
    )
    parser.add_argument("--plugin", default=DEFAULT_PLUGIN, help=f"Visualization plugin name. Default: {DEFAULT_PLUGIN}")
    parser.add_argument("--dry-run", action="store_true", help="Print the mirror target without changing files.")
    return parser.parse_args()


def discover_galaxy_root() -> Path:
    candidates = []
    tmp_root = Path(tempfile.gettempdir()).resolve()
    for path in tmp_root.glob("tmp*/galaxy-dev"):
        if (path / "run.sh").is_file() and (path / "static").is_dir():
            candidates.append(path)
    if not candidates:
        raise SystemExit(
            "Could not find an active tmp*/galaxy-dev checkout. "
            "Pass --galaxy-root after starting planemo serve."
        )
    return max(candidates, key=lambda path: path.stat().st_mtime)


def validate_plugin_source(plugin_source: Path, plugin: str) -> None:
    required = [
        plugin_source / "static" / f"{plugin}.xml",
        plugin_source / "static" / "script.js",
        plugin_source / "static" / "vendor" / "molstar" / "5.4.2" / "molstar.js",
        plugin_source / "static" / "vendor" / "molstar" / "5.4.2" / "molstar.css",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("Plugin source is incomplete:\n" + "\n".join(missing))


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    galaxy_root = args.galaxy_root.resolve() if args.galaxy_root else discover_galaxy_root()
    plugin_source = project_root / "config" / "plugins" / "visualizations" / args.plugin
    validate_plugin_source(plugin_source, args.plugin)

    target = galaxy_root / "static" / "plugins" / "visualizations" / args.plugin
    print(f"Galaxy root: {galaxy_root}")
    print(f"Plugin source: {plugin_source}")
    print(f"Static target: {target}")
    if args.dry_run:
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(plugin_source, target)
    print(f"Mirrored {args.plugin} static assets.")
    print(f"Entry point URL: /static/plugins/visualizations/{args.plugin}/static/script.js")


if __name__ == "__main__":
    main()
