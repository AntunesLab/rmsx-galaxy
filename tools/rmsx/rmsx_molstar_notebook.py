#!/usr/bin/env python3
"""Notebook helpers for viewing RMSX/FlipBook snapshots with Molstar.

The helpers in this module intentionally reuse the same
``rmsx-molstar-viewer/v1`` manifest consumed by the Galaxy visualization.  That
keeps the notebook path aligned with the native Galaxy path while avoiding any
dependency on Galaxy, ChimeraX, or VMD at display time.
"""

from __future__ import annotations

import html
import json
import math
import os
import re
import subprocess
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence, Union

from rmsx_molstar_report import (
    FLIPBOOK_PALETTES,
    MANIFEST_SCHEMA_VERSION,
    build_viewer_payload,
    read_mask_summary,
)
from rmsx_report_common import build_residue_payload, read_rmsx_table, read_slices, summarize_slices


PathLike = Union[str, os.PathLike]
MaybePath = Optional[PathLike]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = PROJECT_ROOT / "config" / "plugins" / "visualizations" / "rmsx_molstar" / "static"
VIEWER_SCRIPT = STATIC_DIR / "script.js"
MOLSTAR_JS = STATIC_DIR / "vendor" / "molstar" / "5.4.2" / "molstar.js"
MOLSTAR_CSS = STATIC_DIR / "vendor" / "molstar" / "5.4.2" / "molstar.css"
DEFAULT_NOTEBOOK_VIEWER_HEIGHT = 1040
NOTEBOOK_RENDERER_VERSION = "notebook-centering-2026-06-22"


@dataclass
class NotebookFlipBookResult:
    """Displayable Molstar FlipBook result for notebooks and scripts."""

    manifest: Mapping
    html: str
    html_path: Optional[Path] = None
    output_dir: Optional[Path] = None
    snapshot_dir: Optional[Path] = None
    rmsx_command: Optional[Sequence[str]] = None
    rmsx_stdout: str = ""
    rmsx_stderr: str = ""
    width: str = "100%"
    height: int = DEFAULT_NOTEBOOK_VIEWER_HEIGHT

    def iframe_html(self, *, width: Optional[str] = None, height: Optional[int] = None) -> str:
        """Return a sandboxed iframe HTML snippet for notebook rich display."""

        iframe_width = str(width or self.width)
        iframe_height = int(height or self.height)
        srcdoc = html.escape(self.html, quote=True)
        return (
            f'<iframe title="{html.escape(str(self.manifest.get("title", "RMSX Molstar FlipBook")), quote=True)}" '
            f'style="width:{html.escape(iframe_width, quote=True)}; height:{iframe_height}px; '
            f'min-height:640px; display:block; max-width:100%; '
            f'border:1px solid #d7dce2; border-radius:6px; background:#fff;" '
            f'sandbox="allow-scripts allow-same-origin allow-downloads" allowfullscreen '
            f'srcdoc="{srcdoc}"></iframe>'
        )

    def widget_html(self, *, width: Optional[str] = None, height: Optional[int] = None) -> str:
        """Return an iframe wrapped in a fixed-size notebook widget shell."""

        widget_width = str(width or self.width)
        widget_height = int(height or self.height)
        return (
            f'<div class="rmsx-molstar-widget-shell" '
            f'style="width:{html.escape(widget_width, quote=True)}; height:{widget_height}px; '
            f'min-height:{widget_height}px; max-width:100%; overflow:hidden; contain:layout paint;">'
            f'{self.iframe_html(width="100%", height=widget_height)}'
            f"</div>"
        )

    def widget(self, *, width: Optional[str] = None, height: Optional[int] = None):
        """Return an ipywidgets HTML widget with explicit output dimensions."""

        try:
            import ipywidgets as widgets
        except ImportError as error:  # pragma: no cover - depends on notebook environment
            raise RuntimeError("ipywidgets is required for widget-backed Molstar notebook display.") from error
        widget_width = str(width or self.width)
        widget_height = int(height or self.height)
        return widgets.HTML(
            value=self.widget_html(width=widget_width, height=widget_height),
            layout=widgets.Layout(
                width=widget_width,
                height=f"{widget_height}px",
                min_height=f"{widget_height}px",
                overflow="hidden",
            ),
        )

    def _repr_html_(self) -> str:
        return self.iframe_html()

    def display(self):
        """Display the FlipBook in an IPython/Jupyter notebook cell."""

        try:
            from IPython.display import HTML, display
        except ImportError as error:  # pragma: no cover - exercised only outside notebook stacks
            raise RuntimeError("IPython is required for inline notebook display.") from error
        display(HTML(self.iframe_html()))
        return self

    def display_widget(self, *, width: Optional[str] = None, height: Optional[int] = None):
        """Display the FlipBook through an ipywidgets-sized output shell."""

        try:
            from IPython.display import HTML, display
        except ImportError as error:  # pragma: no cover - exercised only outside notebook stacks
            raise RuntimeError("IPython is required for inline notebook display.") from error
        try:
            display(self.widget(width=width, height=height))
        except RuntimeError:
            display(HTML(self.iframe_html(width=width, height=height)))
        return self

    def direct_html(
        self,
        *,
        width: Optional[str] = None,
        height: Optional[int] = None,
        spacing: float = 0.7,
        columns: Optional[int] = None,
        thickness: float = 1.0,
        palette: Optional[str] = None,
    ) -> str:
        """Return a no-iframe notebook HTML renderer for direct Molstar mounting."""

        return molstar_direct_notebook_html(
            self.manifest,
            width=width or self.width,
            height=int(height or self.height),
            spacing=spacing,
            columns=columns,
            thickness=thickness,
            palette=palette,
        )

    def display_direct(
        self,
        *,
        width: Optional[str] = None,
        height: Optional[int] = None,
        spacing: float = 0.7,
        columns: Optional[int] = None,
        thickness: float = 1.0,
        palette: Optional[str] = None,
    ):
        """Display a direct notebook Molstar mount without an iframe."""

        try:
            from IPython.display import HTML, display
        except ImportError as error:  # pragma: no cover - exercised only outside notebook stacks
            raise RuntimeError("IPython is required for inline notebook display.") from error
        display(
            HTML(
                self.direct_html(
                    width=width,
                    height=height,
                    spacing=spacing,
                    columns=columns,
                    thickness=thickness,
                    palette=palette,
                )
            )
        )
        return self


def validate_manifest(manifest: Mapping) -> None:
    if not isinstance(manifest, Mapping) or manifest.get("schemaVersion") != MANIFEST_SCHEMA_VERSION:
        raise ValueError(f"Expected an RMSX Molstar manifest with schemaVersion {MANIFEST_SCHEMA_VERSION}.")
    if not manifest.get("slices"):
        raise ValueError("RMSX Molstar manifest does not contain any slices.")
    if not manifest.get("residues"):
        raise ValueError("RMSX Molstar manifest does not contain any residue values.")


def _validate_palette(palette: str) -> str:
    palette_name = str(palette).lower()
    if palette_name not in FLIPBOOK_PALETTES:
        choices = ", ".join(sorted(FLIPBOOK_PALETTES))
        raise ValueError(f"Unknown RMSX palette {palette!r}. Choose one of: {choices}.")
    return palette_name


def _read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Required Molstar notebook asset is missing: {path}")
    return path.read_text(encoding="utf-8")


def _inline_script(text: str) -> str:
    return text.replace("</script", "<\\/script")


def _inline_style(text: str) -> str:
    return text.replace("</style", "<\\/style")


def molstar_notebook_html(manifest: Mapping, title: Optional[str] = None) -> str:
    """Build a standalone HTML document for a notebook iframe or saved report."""

    validate_manifest(manifest)
    page_title = title or str(manifest.get("title") or "RMSX Molstar FlipBook")
    incoming_json = json.dumps({"manifest": manifest}, separators=(",", ":")).replace("</", "<\\/")
    manifest_json = json.dumps(incoming_json)
    molstar_css = _inline_style(_read_text(MOLSTAR_CSS))
    molstar_js = _inline_script(_read_text(MOLSTAR_JS))
    viewer_js = _inline_script(_read_text(VIEWER_SCRIPT))
    escaped_title = html.escape(page_title)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_title}</title>
  <meta name="rmsx-molstar-notebook-renderer" content="{NOTEBOOK_RENDERER_VERSION}">
  <style>{molstar_css}</style>
  <style>
    html, body {{
      margin: 0;
      width: 100%;
      height: 100%;
      min-height: 0;
      overflow: hidden;
      background: #ffffff;
    }}
  </style>
</head>
<body>
  <div id="app"></div>
  <script>
    document.getElementById("app").dataset.incoming = {manifest_json};
  </script>
  <script>{molstar_js}</script>
  <script>{viewer_js}</script>
  <script>
    (() => {{
      const style = document.createElement("style");
      style.textContent = "html,body{{height:100%;min-height:0;overflow:hidden}} .rmsx-app,.rmsx-viewer{{height:100vh;min-height:0}}";
      document.head.appendChild(style);
    }})();
  </script>
</body>
</html>
"""


def _manifest_palette(manifest: Mapping, palette: Optional[str] = None) -> tuple[str, list[str]]:
    requested = str(palette or manifest.get("palette", {}).get("name") or "viridis").lower()
    available = manifest.get("availablePalettes") or {}
    colors = available.get(requested) or manifest.get("palette", {}).get("colors")
    if not colors:
        requested = "viridis"
        colors = FLIPBOOK_PALETTES.get(requested, ["#440154", "#21918C", "#FDE725"])
    return requested, [str(color).upper() for color in colors]


def _structure_stats_from_pdb(pdb: str) -> dict:
    stats = {
        "min_x": float("inf"),
        "max_x": float("-inf"),
        "min_y": float("inf"),
        "max_y": float("-inf"),
        "min_z": float("inf"),
        "max_z": float("-inf"),
        "sum_x": 0.0,
        "sum_y": 0.0,
        "sum_z": 0.0,
        "count": 0,
    }
    for line in pdb.splitlines():
        if not line.startswith(("ATOM  ", "HETATM")):
            continue
        try:
            x = float(line[30:38])
            y = float(line[38:46])
            z = float(line[46:54])
        except ValueError:
            continue
        stats["min_x"] = min(stats["min_x"], x)
        stats["max_x"] = max(stats["max_x"], x)
        stats["min_y"] = min(stats["min_y"], y)
        stats["max_y"] = max(stats["max_y"], y)
        stats["min_z"] = min(stats["min_z"], z)
        stats["max_z"] = max(stats["max_z"], z)
        stats["sum_x"] += x
        stats["sum_y"] += y
        stats["sum_z"] += z
        stats["count"] += 1
    if not stats["count"]:
        return {
            **stats,
            "center": (0.0, 0.0, 0.0),
            "width": 30.0,
            "height": 30.0,
            "depth": 30.0,
        }
    return {
        **stats,
        "center": (
            stats["sum_x"] / stats["count"],
            stats["sum_y"] / stats["count"],
            stats["sum_z"] / stats["count"],
        ),
        "width": max(1.0, stats["max_x"] - stats["min_x"]),
        "height": max(1.0, stats["max_y"] - stats["min_y"]),
        "depth": max(1.0, stats["max_z"] - stats["min_z"]),
    }


def _rotation_matrix(rotation: Mapping) -> list[list[float]]:
    def radians(value: object, fallback: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback

    x = radians(rotation.get("x"), 90.0) * 3.141592653589793 / 180.0
    y = radians(rotation.get("y"), 0.0) * 3.141592653589793 / 180.0
    z = radians(rotation.get("z"), 0.0) * 3.141592653589793 / 180.0
    sx, cx = math.sin(x), math.cos(x)
    sy, cy = math.sin(y), math.cos(y)
    sz, cz = math.sin(z), math.cos(z)
    rx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]
    ry = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]
    rz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]
    return _multiply_matrices(rz, _multiply_matrices(ry, rx))


def _multiply_matrices(left: Sequence[Sequence[float]], right: Sequence[Sequence[float]]) -> list[list[float]]:
    return [
        [sum(left_row[index] * right[index][column] for index in range(3)) for column in range(3)]
        for left_row in left
    ]


def _transform_point(
    matrix: Sequence[Sequence[float]],
    center: Sequence[float],
    target: Sequence[float],
    x: float,
    y: float,
    z: float,
) -> tuple[float, float, float]:
    lx = x - center[0]
    ly = y - center[1]
    lz = z - center[2]
    return (
        target[0] + matrix[0][0] * lx + matrix[0][1] * ly + matrix[0][2] * lz,
        target[1] + matrix[1][0] * lx + matrix[1][1] * ly + matrix[1][2] * lz,
        target[2] + matrix[2][0] * lx + matrix[2][1] * ly + matrix[2][2] * lz,
    )


def _residue_values_by_key(manifest: Mapping) -> dict[str, Mapping]:
    residues = {}
    for residue in manifest.get("residues", []):
        if residue.get("key"):
            residues[str(residue["key"])] = residue
        if residue.get("id"):
            residues[str(residue["id"])] = residue
    return residues


def _normalized_value(value: object, lower: float, upper: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    span = max(0.000001, upper - lower)
    return min(1.0, max(0.0, (numeric - lower) / span))


def _direct_scene_payload(
    manifest: Mapping,
    *,
    spacing: float,
    columns: Optional[int],
    thickness: float,
    palette: Optional[str],
) -> Mapping:
    validate_manifest(manifest)
    slices = list(manifest.get("slices", []))
    selected_palette, colors = _manifest_palette(manifest, palette)
    domain = manifest.get("domain", {})
    color_min = float(manifest.get("visualMapping", {}).get("defaultColorMin", domain.get("min", 0.0)))
    color_max = float(manifest.get("visualMapping", {}).get("defaultColorMax", domain.get("max", 1.0)))
    rotation = manifest.get("rotationModel", {}).get("defaultRotation", {"x": 90, "y": 0, "z": 0})
    matrix = _rotation_matrix(rotation)
    stats_by_index = [_structure_stats_from_pdb(str(slice_entry.get("pdb", ""))) for slice_entry in slices]
    max_extent = max(
        [max(stats["width"], stats["height"], stats["depth"]) for stats in stats_by_index] or [30.0]
    )
    requested_columns = columns or int(manifest.get("flipbookReference", {}).get("defaultColumns") or len(slices) or 1)
    column_count = max(1, min(int(requested_columns), len(slices) or 1))
    rows = max(1, (len(slices) + column_count - 1) // column_count)
    slot = max_extent * max(0.15, float(spacing)) + 12.0
    residues = _residue_values_by_key(manifest)
    rendered = []
    bounds = {
        "min_x": float("inf"),
        "max_x": float("-inf"),
        "min_y": float("inf"),
        "max_y": float("-inf"),
        "min_z": float("inf"),
        "max_z": float("-inf"),
    }

    for index, slice_entry in enumerate(slices):
        stats = stats_by_index[index]
        row = index // column_count
        column = index % column_count
        row_length = len(slices) - row * column_count if row == rows - 1 else column_count
        target = (
            (column - (row_length - 1) / 2) * slot,
            ((rows - 1) / 2 - row) * slot * 0.74,
            0.0,
        )
        output_lines = []
        for line in str(slice_entry.get("pdb", "")).splitlines():
            if not line.startswith(("ATOM  ", "HETATM")):
                output_lines.append(line)
                continue
            padded = line.ljust(80)
            try:
                x = float(padded[30:38])
                y = float(padded[38:46])
                z = float(padded[46:54])
            except ValueError:
                output_lines.append(line)
                continue
            chain = padded[21:22].strip()
            residue_id = padded[22:26].strip()
            key = f"{chain}:{residue_id}" if chain else residue_id
            residue = residues.get(key) or residues.get(residue_id) or {}
            rmsx = residue.get("values", {}).get(slice_entry.get("rmsxColumn"))
            bfactor = _normalized_value(rmsx, color_min, color_max)
            tx, ty, tz = _transform_point(matrix, stats["center"], target, x, y, z)
            bounds["min_x"] = min(bounds["min_x"], tx)
            bounds["max_x"] = max(bounds["max_x"], tx)
            bounds["min_y"] = min(bounds["min_y"], ty)
            bounds["max_y"] = max(bounds["max_y"], ty)
            bounds["min_z"] = min(bounds["min_z"], tz)
            bounds["max_z"] = max(bounds["max_z"], tz)
            output_lines.append(
                f"{padded[:30]}{tx:8.3f}{ty:8.3f}{tz:8.3f}{padded[54:60]}{bfactor:6.2f}{padded[66:]}".rstrip()
            )
        rendered.append(
            {
                "label": slice_entry.get("label", f"Slice {index + 1}"),
                "pdb": "\n".join(output_lines),
            }
        )

    if bounds["min_x"] == float("inf"):
        center = [0.0, 0.0, 0.0]
        radius = 40.0
    else:
        center = [
            (bounds["min_x"] + bounds["max_x"]) / 2,
            (bounds["min_y"] + bounds["max_y"]) / 2,
            (bounds["min_z"] + bounds["max_z"]) / 2,
        ]
        dx = bounds["max_x"] - bounds["min_x"]
        dy = bounds["max_y"] - bounds["min_y"]
        dz = bounds["max_z"] - bounds["min_z"]
        radius = max(8.0, ((dx * dx + dy * dy + dz * dz) ** 0.5) / 2)
    return {
        "title": manifest.get("title", "RMSX Molstar FlipBook"),
        "slices": rendered,
        "palette": selected_palette,
        "colors": colors,
        "thickness": float(thickness),
        "focus": {"center": center, "radius": radius},
        "summary": f"{len(rendered)} slices; direct notebook mount; {selected_palette}",
    }


def molstar_direct_notebook_html(
    manifest: Mapping,
    *,
    width: str = "100%",
    height: int = DEFAULT_NOTEBOOK_VIEWER_HEIGHT,
    spacing: float = 0.7,
    columns: Optional[int] = None,
    thickness: float = 1.0,
    palette: Optional[str] = None,
) -> str:
    """Build direct notebook HTML that mounts Molstar into a normal output div."""

    payload = _direct_scene_payload(
        manifest,
        spacing=spacing,
        columns=columns,
        thickness=thickness,
        palette=palette,
    )
    root_id = f"rmsx-molstar-direct-{uuid.uuid4().hex}"
    viewport_id = f"{root_id}-viewport"
    payload_json = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    molstar_css = _inline_style(_read_text(MOLSTAR_CSS))
    molstar_js = _inline_script(_read_text(MOLSTAR_JS))
    safe_width = html.escape(str(width), quote=True)
    safe_height = int(height)
    return f"""
<div id="{root_id}" class="rmsx-molstar-direct-root" style="width:{safe_width}; max-width:100%; height:{safe_height}px; min-height:{safe_height}px; overflow:hidden; border:1px solid #d7dce2; border-radius:6px; background:#fff; position:relative;">
  <style>{molstar_css}</style>
  <style>
    #{root_id} * {{ box-sizing: border-box; }}
    #{root_id} .rmsx-direct-toolbar {{
      height: 42px;
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 8px;
      border-bottom: 1px solid #d7dce2;
      background: #fbfcfd;
      color: #1d2630;
      font: 13px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    #{root_id} .rmsx-direct-toolbar strong {{ font-weight: 650; margin-right: auto; }}
    #{root_id} .rmsx-direct-toolbar button {{
      min-height: 28px;
      padding: 0 10px;
      border: 1px solid #d7dce2;
      border-radius: 6px;
      background: #fff;
      color: #1d2630;
      font: inherit;
      cursor: pointer;
    }}
    #{viewport_id} {{
      position: absolute;
      inset: 42px 0 0 0;
      overflow: hidden;
      background: #fff;
    }}
  </style>
  <div class="rmsx-direct-toolbar">
    <strong>{html.escape(str(payload["title"]))}</strong>
    <span data-role="summary">{html.escape(str(payload["summary"]))}</span>
    <button type="button" data-role="fit">Fit</button>
  </div>
  <div id="{viewport_id}"></div>
  <script>{molstar_js}</script>
  <script>
  (() => {{
    const payload = {payload_json};
    const root = document.getElementById("{root_id}");
    const viewport = document.getElementById("{viewport_id}");
    const fitButton = root?.querySelector("[data-role='fit']");
    let viewer = null;

    function hexToNumber(hex) {{
      return Number.parseInt(String(hex || "#ffffff").replace("#", ""), 16);
    }}

    function focusScene() {{
      const plugin = viewer?.plugin;
      const sphere = {{ center: payload.focus.center, radius: payload.focus.radius }};
      try {{
        viewer?.handleResize?.();
        plugin?.layout?.events?.updated?.next?.(void 0);
        plugin?.managers?.camera?.focusSphere?.(sphere, {{ durationMs: 0, extraRadius: Math.max(4, sphere.radius * 0.7) }});
        plugin?.canvas3d?.requestDraw?.();
      }} catch (error) {{
        console.warn("RMSX direct notebook fit failed.", error);
      }}
    }}

    async function addSlice(plugin, slice) {{
      const data = await plugin.builders.data.rawData({{ data: slice.pdb, label: slice.label }});
      const trajectory = await plugin.builders.structure.parseTrajectory(data, "pdb");
      const model = await plugin.builders.structure.createModel(trajectory);
      const structure = await plugin.builders.structure.createStructure(model);
      const rep = {{
        type: "putty",
        typeParams: {{ sizeFactor: payload.thickness, quality: "high", alpha: 1 }},
        color: "uncertainty",
        colorParams: {{
          domain: [0, 1],
          list: {{ kind: "interpolate", colors: [...payload.colors].reverse().map(hexToNumber) }}
        }},
        size: "uncertainty",
        sizeParams: {{ bfactorFactor: Math.max(0.3, payload.thickness * 2.4), rmsfFactor: 0, baseSize: Math.max(0.12, payload.thickness * 0.45) }}
      }};
      try {{
        return await plugin.builders.structure.representation.addRepresentation(structure, rep);
      }} catch (_error) {{
        return await plugin.builders.structure.representation.addRepresentation(structure, {{
          ...rep,
          type: "cartoon",
          typeParams: {{ aspectRatio: 1.2, sizeFactor: Math.max(0.35, payload.thickness), quality: "high", alpha: 1 }}
        }});
      }}
    }}

    async function init() {{
      try {{
        viewer = await window.molstar.Viewer.create("{viewport_id}", {{
          layoutIsExpanded: false,
          layoutShowControls: false,
          layoutShowRemoteState: false,
          layoutShowSequence: false,
          layoutShowLog: false,
          layoutShowLeftPanel: false,
          viewportShowExpand: true,
          viewportShowSelectionMode: false,
          viewportShowAnimation: false
        }});
        viewer.plugin.canvas3d?.setProps?.({{
          renderer: {{ backgroundColor: 0xffffff, ambientIntensity: 0.78 }},
          cameraFog: {{ name: "off", params: {{}} }},
          postprocessing: {{
            enabled: true,
            outline: {{ name: "on", params: {{ scale: 0.55, threshold: 0.22, color: 0x1f2937, includeTransparent: true }} }},
            occlusion: {{ name: "off", params: {{}} }}
          }},
          multiSample: {{ mode: "off", sampleLevel: 0, reduceFlicker: false, reuseOcclusion: false }}
        }});
        for (const slice of payload.slices) {{
          await addSlice(viewer.plugin, slice);
        }}
        focusScene();
        window.setTimeout(focusScene, 120);
        window.setTimeout(focusScene, 500);
      }} catch (error) {{
        viewport.textContent = `RMSX direct Molstar notebook viewer failed: ${{error.message}}`;
        viewport.style.padding = "14px";
        console.error(error);
      }}
    }}

    fitButton?.addEventListener("click", focusScene);
    if (typeof ResizeObserver !== "undefined") {{
      const observer = new ResizeObserver(() => window.setTimeout(focusScene, 80));
      observer.observe(root);
      observer.observe(viewport);
    }}
    init();
  }})();
  </script>
</div>
"""


def _resolve_html_path(write_html: Union[bool, PathLike], output_dir: MaybePath, default_name: str) -> Optional[Path]:
    if not write_html:
        return None
    if isinstance(write_html, (str, os.PathLike)):
        return Path(write_html)
    base = Path(output_dir) if output_dir else Path.cwd()
    return base / default_name


def display_manifest(
    manifest: Mapping,
    *,
    width: str = "100%",
    height: int = DEFAULT_NOTEBOOK_VIEWER_HEIGHT,
    write_html: Union[bool, PathLike] = False,
    output_dir: MaybePath = None,
    title: Optional[str] = None,
) -> NotebookFlipBookResult:
    """Return a displayable notebook object for an RMSX Molstar manifest."""

    validate_manifest(manifest)
    output_path = _resolve_html_path(write_html, output_dir, "rmsx_molstar_flipbook.html")
    html_text = molstar_notebook_html(manifest, title=title)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_text, encoding="utf-8")
    return NotebookFlipBookResult(
        manifest=manifest,
        html=html_text,
        html_path=output_path,
        output_dir=Path(output_dir) if output_dir else None,
        width=width,
        height=int(height),
    )


def _discover_snapshots(snapshots: Union[PathLike, Iterable[PathLike]]) -> list[Path]:
    if isinstance(snapshots, (str, os.PathLike)):
        root = Path(snapshots)
        if root.is_dir():
            paths = sorted(root.glob("*.pdb"), key=_snapshot_sort_key)
        else:
            paths = [root]
    else:
        paths = sorted((Path(path) for path in snapshots), key=_snapshot_sort_key)
    if not paths:
        raise FileNotFoundError("No PDB snapshots were provided.")
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"PDB snapshot file(s) do not exist: {', '.join(missing)}")
    return paths


def _snapshot_sort_key(path: Path):
    numbers = [int(value) for value in re.findall(r"\d+", path.name)]
    return (numbers or [0], path.name)


def _pdb_float(line: str, start: int, end: int) -> Optional[float]:
    try:
        return float(line[start:end])
    except ValueError:
        return None


def _parse_pdb_bfactors(path: Path) -> OrderedDict[str, dict]:
    residues: OrderedDict[str, dict] = OrderedDict()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith(("ATOM  ", "HETATM")):
            continue
        padded = line.ljust(80)
        residue_id = padded[22:26].strip()
        if not residue_id:
            continue
        insertion = padded[26:27].strip()
        if insertion:
            residue_id = f"{residue_id}{insertion}"
        chain = padded[21:22].strip()
        key = f"{chain}:{residue_id}" if chain else residue_id
        atom_name = padded[12:16].strip()
        bfactor = _pdb_float(padded, 60, 66)
        if bfactor is None:
            continue
        current = residues.get(key)
        if current is None or (atom_name == "CA" and current["atomName"] != "CA"):
            residues[key] = {
                "id": residue_id,
                "chain": chain,
                "key": key,
                "label": f"{residue_id} / chain {chain}" if chain else residue_id,
                "atomName": atom_name,
                "bfactor": bfactor,
            }
    return residues


def _snapshot_summaries(residues: Sequence[Mapping], slice_columns: Sequence[str]):
    summaries = {}
    all_values = []
    for column in slice_columns:
        column_values = []
        max_residue = None
        max_value = None
        for residue in residues:
            value = residue.get("values", {}).get(column)
            if value is None:
                continue
            column_values.append(float(value))
            all_values.append(float(value))
            if max_value is None or value > max_value:
                max_value = float(value)
                max_residue = residue.get("id", "")
        if column_values:
            summaries[column] = {
                "min": min(column_values),
                "max": max(column_values),
                "mean": sum(column_values) / len(column_values),
                "maxResidue": max_residue,
                "residueCount": len(column_values),
            }
    if not all_values:
        raise ValueError("No numeric B-factor values were found in the PDB snapshots.")
    return summaries, {"min": min(all_values), "max": max(all_values)}


def build_manifest_from_snapshots(
    snapshots: Union[PathLike, Iterable[PathLike]],
    *,
    palette: str = "viridis",
    title: str = "RMSX Molstar Notebook FlipBook",
    mask_table: MaybePath = None,
) -> Mapping:
    """Build an RMSX Molstar manifest from existing PDB snapshot B-factors."""

    palette_name = _validate_palette(palette)
    paths = _discover_snapshots(snapshots)
    slices = []
    residue_index: OrderedDict[str, dict] = OrderedDict()
    slice_columns = []
    for index, path in enumerate(paths, start=1):
        column = f"slice_{index}.dcd"
        slice_columns.append(column)
        slices.append(
            {
                "index": index,
                "id": f"slice_{index}",
                "label": f"Slice {index}",
                "filename": path.name,
                "rmsxColumn": column,
                "pdb": path.read_text(encoding="utf-8"),
            }
        )
        for key, entry in _parse_pdb_bfactors(path).items():
            residue = residue_index.setdefault(
                key,
                {
                    "id": entry["id"],
                    "chain": entry["chain"],
                    "key": entry["key"],
                    "label": entry["label"],
                    "values": {},
                },
            )
            residue["values"][column] = float(entry["bfactor"])

    residues = list(residue_index.values())
    summaries, domain = _snapshot_summaries(residues, slice_columns)
    if mask_table:
        mask_summary = read_mask_summary(mask_table)
    else:
        mask_summary = {"maskedResidues": 0, "totalResidues": len(residues), "masked": [], "maskedKeys": []}
    return build_viewer_payload(title, slices, summaries, domain, mask_summary, residues, palette_name)


def view_flipbook_snapshots(
    snapshots: Union[PathLike, Iterable[PathLike]],
    *,
    palette: str = "viridis",
    title: str = "RMSX Molstar Notebook FlipBook",
    mask_table: MaybePath = None,
    width: str = "100%",
    height: int = DEFAULT_NOTEBOOK_VIEWER_HEIGHT,
    write_html: Union[bool, PathLike] = False,
    output_dir: MaybePath = None,
) -> NotebookFlipBookResult:
    """Display precomputed RMSX/FlipBook PDB snapshots in a notebook."""

    manifest = build_manifest_from_snapshots(snapshots, palette=palette, title=title, mask_table=mask_table)
    result = display_manifest(
        manifest,
        width=width,
        height=height,
        write_html=write_html,
        output_dir=output_dir,
        title=title,
    )
    result.snapshot_dir = Path(snapshots) if isinstance(snapshots, (str, os.PathLike)) and Path(snapshots).is_dir() else None
    return result


def _rmsx_executable_parts(executable: Union[str, Sequence[str]]) -> list[str]:
    if isinstance(executable, str):
        return [executable]
    return [str(part) for part in executable]


def _find_chain_dir(output_dir: Path, chain: str) -> Path:
    exact = output_dir / f"chain_{chain}_rmsx"
    if exact.exists():
        return exact
    matches = sorted(output_dir.glob("chain_*_rmsx"))
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise FileNotFoundError(f"RMSX did not create a chain output directory under {output_dir}.")
    raise FileNotFoundError(
        f"Could not determine which RMSX chain directory to use under {output_dir}; found "
        + ", ".join(path.name for path in matches)
    )


def build_manifest_from_rmsx_output(
    output_dir: PathLike,
    *,
    chain: str,
    palette: str = "viridis",
    title: str = "RMSX Molstar Notebook FlipBook",
) -> Mapping:
    """Build a notebook/Galaxy Molstar manifest from an RMSX output directory."""

    palette_name = _validate_palette(palette)
    chain_dir = _find_chain_dir(Path(output_dir), chain)
    rmsx_tables = sorted(chain_dir.glob("rmsx_*.csv"))
    if not rmsx_tables:
        raise FileNotFoundError(f"No RMSX CSV table found in {chain_dir}.")
    rmsx_table = rmsx_tables[0]
    mask_table = chain_dir / "masked_residues.csv"
    slices = read_slices(chain_dir)
    rows, slice_columns = read_rmsx_table(rmsx_table)
    summaries, domain = summarize_slices(rows, slice_columns)
    residues = build_residue_payload(rows, slice_columns)
    if mask_table.exists():
        mask_summary = read_mask_summary(mask_table)
    else:
        mask_summary = {"maskedResidues": 0, "totalResidues": len(residues), "masked": [], "maskedKeys": []}
    return build_viewer_payload(title, slices, summaries, domain, mask_summary, residues, palette_name)


def run_rmsx_notebook(
    topology: PathLike,
    trajectory: PathLike,
    *,
    chain: str,
    num_slices: int = 3,
    output_dir: PathLike = "rmsx_notebook_output",
    palette: str = "viridis",
    start_frame: int = 0,
    end_frame: Optional[int] = None,
    analysis_type: str = "protein",
    summary_n: int = 3,
    interpolate: bool = False,
    rmsx_executable: Union[str, Sequence[str]] = "rmsx",
    overwrite: bool = True,
    title: str = "RMSX Molstar Notebook FlipBook",
    width: str = "100%",
    height: int = DEFAULT_NOTEBOOK_VIEWER_HEIGHT,
    write_html: Union[bool, PathLike] = False,
) -> NotebookFlipBookResult:
    """Run RMSX and return an inline Molstar FlipBook notebook result."""

    palette_name = _validate_palette(palette)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    command = _rmsx_executable_parts(rmsx_executable) + [
        str(topology),
        str(trajectory),
        "--output_dir",
        str(out),
        "--num_slices",
        str(int(num_slices)),
        "--chain",
        str(chain),
        "--palette",
        palette_name,
        "--start_frame",
        str(int(start_frame)),
        "--analysis_type",
        str(analysis_type),
        "--summary_n",
        str(int(summary_n)),
        "--quiet",
        "--no-plot",
        "--interpolate" if interpolate else "--no-interpolate",
    ]
    if end_frame is not None:
        command.extend(["--end_frame", str(int(end_frame))])
    if overwrite:
        command.append("--overwrite")

    env = dict(os.environ)
    env.setdefault("RMSX_NO_CITATION", "1")
    completed = subprocess.run(command, capture_output=True, text=True, check=False, env=env)
    if completed.returncode != 0:
        message = (
            "RMSX failed while generating notebook FlipBook snapshots.\n"
            f"Command: {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
        raise RuntimeError(message)

    manifest = build_manifest_from_rmsx_output(out, chain=chain, palette=palette_name, title=title)
    result = display_manifest(
        manifest,
        width=width,
        height=height,
        write_html=write_html,
        output_dir=out,
        title=title,
    )
    result.output_dir = out
    result.snapshot_dir = _find_chain_dir(out, chain)
    result.rmsx_command = command
    result.rmsx_stdout = completed.stdout
    result.rmsx_stderr = completed.stderr
    return result


__all__ = [
    "NotebookFlipBookResult",
    "build_manifest_from_rmsx_output",
    "build_manifest_from_snapshots",
    "DEFAULT_NOTEBOOK_VIEWER_HEIGHT",
    "display_manifest",
    "molstar_direct_notebook_html",
    "molstar_notebook_html",
    "run_rmsx_notebook",
    "view_flipbook_snapshots",
]
