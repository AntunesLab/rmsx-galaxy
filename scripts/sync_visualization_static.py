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
DEFAULT_ENTRY_POINT = "script_compact_0624.js"


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
        plugin_source / "static" / DEFAULT_ENTRY_POINT,
        plugin_source / "static" / "vendor" / "molstar" / "5.4.2" / "molstar.js",
        plugin_source / "static" / "vendor" / "molstar" / "5.4.2" / "molstar.css",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("Plugin source is incomplete:\n" + "\n".join(missing))


def patch_asgi_visualization_href(galaxy_root: Path, dry_run: bool = False) -> bool:
    """Patch temporary Planemo Galaxy checkouts that cannot resolve plugin hrefs.

    Some recent Galaxy dev checkouts serve Planemo with the ASGI stack while the
    visualization plugin serializer still asks the legacy WSGI ``url_for`` for a
    static path. In that mode the API returns Galaxy's literal deprecated-url
    placeholder, so the browser tries to load visualization scripts from an
    invalid path. For local demo checkouts the static path is already absolute,
    so returning ``self.static_path`` is the correct URL.
    """

    plugin_py = galaxy_root / "lib" / "galaxy" / "visualization" / "plugins" / "plugin.py"
    if not plugin_py.exists():
        print(f"Skipping ASGI href patch; not found: {plugin_py}")
        return False

    text = plugin_py.read_text()
    old = '"href": url_for(self.static_path),'
    new = '"href": self.static_path,'
    if new in text:
        print("Galaxy visualization href patch already present.")
        return False
    if old not in text:
        print("Skipping ASGI href patch; expected serializer line was not found.")
        return False
    if dry_run:
        print(f"Would patch Galaxy visualization href resolver: {plugin_py}")
        return True
    plugin_py.write_text(text.replace(old, new, 1))
    print("Patched Galaxy visualization href resolver for local ASGI Planemo serving.")
    return True


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
    patch_asgi_visualization_href(galaxy_root, dry_run=args.dry_run)
    if args.dry_run:
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(plugin_source, target)
    print(f"Mirrored {args.plugin} static assets.")
    print(f"Entry point URL: /static/plugins/visualizations/{args.plugin}/static/{DEFAULT_ENTRY_POINT}")


if __name__ == "__main__":
    main()
