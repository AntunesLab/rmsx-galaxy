#!/usr/bin/env python3
"""Smoke checks for the RMSX Flipbook manifest and native visualization."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools" / "flipbook"
sys.path.insert(0, str(TOOLS))

from flipbook_molstar_report import build_viewer_payload, read_mask_summary  # noqa: E402
from flipbook_report_common import build_residue_payload, read_rmsx_table, read_slices, summarize_slices  # noqa: E402


PDB_TEMPLATE = """\
ATOM      1  N   GLY A   1      {x1:7.3f}  {y1:7.3f}  {z1:7.3f}  1.00  0.00           N
ATOM      2  CA  GLY A   1      {x2:7.3f}  {y2:7.3f}  {z2:7.3f}  1.00  0.00           C
ATOM      3  N   SER A   2      {x3:7.3f}  {y3:7.3f}  {z3:7.3f}  1.00  0.00           N
ATOM      4  CA  SER A   2      {x4:7.3f}  {y4:7.3f}  {z4:7.3f}  1.00  0.00           C
END
"""


def write_fixture(tmpdir):
    pdb_dir = tmpdir / "pdb"
    pdb_dir.mkdir()
    (pdb_dir / "slice_1_first_frame.pdb").write_text(
        PDB_TEMPLATE.format(x1=0, y1=0, z1=0, x2=1, y2=0, z2=0, x3=0, y3=1, z3=0, x4=1, y4=1, z4=0),
        encoding="utf-8",
    )
    (pdb_dir / "slice_2_first_frame.pdb").write_text(
        PDB_TEMPLATE.format(x1=0, y1=0, z1=1, x2=1, y2=0, z2=1, x3=0, y3=1, z3=1, x4=1, y4=1, z4=1),
        encoding="utf-8",
    )
    rmsx = tmpdir / "rmsx.csv"
    rmsx.write_text(
        "ResidueID,ChainID,slice_1.dcd,slice_2.dcd\n"
        "1,A,0.25,1.25\n"
        "2,A,0.50,2.50\n",
        encoding="utf-8",
    )
    mask = tmpdir / "mask.csv"
    mask.write_text("ResidueID,ChainID,Masked\n1,A,False\n2,A,True\n", encoding="utf-8")
    return pdb_dir, rmsx, mask


def build_payload(tmpdir):
    pdb_dir, rmsx_table, mask_table = write_fixture(tmpdir)
    slices = read_slices(pdb_dir)
    rows, slice_columns = read_rmsx_table(rmsx_table)
    summaries, domain = summarize_slices(rows, slice_columns)
    residues = build_residue_payload(rows, slice_columns)
    return build_viewer_payload(
        "RMSX Flipbook viewer",
        slices,
        summaries,
        domain,
        read_mask_summary(mask_table),
        residues,
        "turbo",
    )


def test_manifest_payload():
    with tempfile.TemporaryDirectory() as tmp:
        payload = build_payload(Path(tmp))
    assert payload["schemaVersion"] == "flipbook-molstar-viewer/v1"
    assert len(payload["slices"]) == 2
    assert payload["slices"][0]["pdb"].startswith("ATOM")
    assert payload["residues"][1]["values"]["slice_2.dcd"] == 2.5
    assert payload["summaries"]["slice_2.dcd"]["maxResidue"] == "2"
    assert payload["domain"] == {"min": 0.25, "max": 2.5}
    assert payload["maskSummary"]["maskedKeys"] == ["A:2"]
    assert payload["palette"]["name"] == "turbo"
    assert "mako" in payload["availablePalettes"]
    assert payload["presentation"]["defaultLayout"] == "tiled"
    assert payload["flipbookReference"]["defaultColumns"] == len(payload["slices"])
    assert payload["flipbookReference"]["minimumSpacingFactor"] == 0.0
    assert payload["citation"]["doi"] == "10.1038/s41598-026-39869-7"
    assert payload["flipbookReference"]["tilePaddingFactor"] == 1.55
    assert payload["visualMapping"]["defaultRadiusMin"] == 0.63
    assert payload["visualMapping"]["defaultColorMin"] == payload["domain"]["min"]
    assert payload["visualMapping"]["defaultColorMax"] == payload["domain"]["max"]
    assert payload["selectedResidueMarker"]["enabledDefault"] is False
    assert payload["rotationModel"]["defaultRotation"] == {"x": 90, "y": 0, "z": 0}
    json.dumps(payload)


def test_native_visualization_contract():
    script = (ROOT / "config/plugins/visualizations/flipbook_molstar/static/script.js").read_text(encoding="utf-8")
    xml = (ROOT / "config/plugins/visualizations/flipbook_molstar/static/flipbook_molstar.xml").read_text(encoding="utf-8")
    datatypes = (ROOT / "config/datatypes/datatypes_conf.xml").read_text(encoding="utf-8")
    wrapper = (ROOT / "tools/flipbook/flipbook.xml").read_text(encoding="utf-8")
    macros = (ROOT / "tools/flipbook/macros.xml").read_text(encoding="utf-8")
    static_sync = (ROOT / "scripts/sync_visualization_static.py").read_text(encoding="utf-8")
    parity_script = (ROOT / "tests/flipbook/native_visualization_parity_check.mjs").read_text(encoding="utf-8")
    visual_script = (ROOT / "tests/flipbook/native_visualization_visual_check.mjs").read_text(encoding="utf-8")
    harness = (ROOT / "tests/flipbook/native_visualization_harness.html").read_text(encoding="utf-8")
    plugin_readme = (ROOT / "config/plugins/visualizations/flipbook_molstar/README.md").read_text(encoding="utf-8")
    package_json = (ROOT / "package.json").read_text(encoding="utf-8")
    assert "vendor/molstar/5.4.2/molstar.js" in script
    assert "This dataset is not an RMSX Flipbook manifest" in script
    assert "Please cite: RMSX/Flipbook paper" in script
    assert "10.1038/s41598-026-39869-7" in script
    assert "inline-harness-manifest" in script
    assert "inline-harness-dataset" in script
    assert "manifestSource: state.manifestSource" in script
    assert "function uniqueStrings(values)" in script
    assert "function historyIdCandidates()" in script
    assert 'URL_PARAMS.get("history_id")' in script
    assert "function parseManifestResponseText(text)" in script
    assert "parsed?.item_data || parsed?.data || parsed?.contents || parsed?.content" in script
    assert 'urls.push(`/api/histories/${encodedHistoryId}/contents/${encodedDatasetId}/display?to_ext=json`)' in script
    assert 'urls.push(`/api/histories/${encodedHistoryId}/contents/${encodedDatasetId}/display`)' in script
    assert 'urls.push(`/api/datasets/${encoded}/get_content_as_text`)' in script
    assert 'urls.push(`/api/datasets/${encoded}/content/data`)' in script
    assert "data-testid=\"molstar-palette-select\"" in script
    assert "data-testid=\"molstar-layout-select\"" not in script
    assert "data-testid=\"molstar-control-tabs\"" not in script
    assert "data-testid=\"molstar-control-panels\"" in script
    assert "data-testid=\"molstar-controls-sidebar\"" in script
    assert "data-testid=\"molstar-slice-chips\"" in script
    assert 'const CONTROL_PANEL_KEYS = ["view", "style", "rotation", "metrics"]' in script
    assert 'activePanel: "view"' in script
    assert 'data-panel-tab="playback"' not in script
    assert 'data-testid="molstar-panel-playback"' not in script
    assert 'data-testid="molstar-layout-flip"' not in script
    assert 'data-testid="molstar-play"' not in script
    assert 'data-testid="molstar-previous"' not in script
    assert 'data-testid="molstar-next"' not in script
    assert "marker: false" in script
    assert 'id="markerCheckbox" type="checkbox" data-testid="molstar-residue-marker-checkbox"' not in script
    assert ".rmsx-app { display: grid; grid-template-columns: minmax(236px, 286px) minmax(0, 1fr);" in script
    assert ".rmsx-controls { position: relative; z-index: 5; min-height: 0;" in script
    assert "border-right: 1px solid #d7dce2" in script
    assert ".rmsx-viewer { position: relative; z-index: 1;" in script
    assert "@media (max-width: 900px)" in script
    assert "data-panel-tab=" not in script
    assert "data-panel=\"style\" data-testid=\"molstar-panel-scale\"" in script
    assert "function setActiveControlPanel(panel)" in script
    assert "data-testid=\"molstar-panel-appearance\"" not in script
    assert 'data-panel="view" data-testid="molstar-panel-layout"' in script
    assert 'data-panel="residues" data-testid="molstar-panel-residue"' not in script
    assert 'data-panel="rotation" data-testid="molstar-panel-rotation"' in script
    assert "data-testid=\"molstar-render-select\"" not in script
    assert "data-testid=\"molstar-outline-checkbox\"" in script
    assert "data-testid=\"molstar-rotate-sensitivity-range\"" in script
    assert "data-testid=\"molstar-rotate-sensitivity-number\"" in script
    assert "data-testid=\"molstar-panel-rotation\"" in script
    assert 'data-layout="overlay"' not in script
    assert 'closest?.("[data-layout]")' not in script
    assert "id=\"legendColorBar\"" in script
    assert "data-testid=\"molstar-radius-legend\"" in script
    assert "function mappingLegendStops()" in script
    assert "function legendSummary()" in script
    assert "data-testid=\"molstar-radius-min-number\"" in script
    assert 'button.dataset.testid = "molstar-slice-chip"' in script
    assert "button.textContent = String(slice.index ?? index + 1)" in script
    assert "data-testid=\"molstar-residue-marker-checkbox\"" not in script
    assert "data-testid=\"molstar-local-rotate-checkbox\"" not in script
    assert "function setMarker(enabled)" in script
    assert "function setLocalDrag(enabled)" in script
    assert "function updateRenderMode(value)" in script
    assert "function setOutline(enabled)" in script
    assert "function updateRotateSensitivity(value)" in script
    assert "function molstarCanvasProps(options = {})" in script
    assert "function canvasRenderStyleSummary()" in script
    assert "data-testid=\"molstar-diagnostics\"" in script
    assert "liveTransforms" in script
    assert "function defaultTileColumns()" in script
    assert "function visualEnvelope()" in script
    assert "const projectedWidths = REPORT.slices.map" in script
    assert "function rotatedExtentX(stats, matrix)" in script
    assert "function defaultRotationMatrix()" in script
    assert "REPORT.flipbookReference?.tilePaddingFactor ?? 1.55" in script
    assert "wormRadiusMax() * 8 + 12" in script
    assert "function tilePaddingFactor()" in script
    assert "function visualRadiusPadding()" in script
    assert "function cameraFocusExtraRadius(sphere)" in script
    assert "Math.max(4, sphere.radius * 0.9)" in script
    assert "function requestMolstarDraw()" in script
    assert "viewer?.handleResize?.()" in script
    assert "viewer?.plugin?.layout?.events?.updated?.next?.(void 0)" in script
    assert "function schedulePostLayoutReset()" in script
    assert "function setupViewportResizeObserver()" in script
    assert "new ResizeObserver" in script
    assert "window.setTimeout(resetAfterLayout, 700)" in script
    assert "function tiledPlacementSummary(focusSphere = null)" in script
    assert "tiledPlacement: tiledPlacementSummary(focusSphere)" in script
    assert "sceneFocusSphere" in script
    assert "focusSphere(sphere" in script
    assert "function syncUrlState()" in script
    assert "function parentWindowIfSameOrigin()" in script
    assert "function urlStateContext()" in script
    assert 'fallbackOrigin = [scriptOrigin, windowOrigin].find((origin) => origin && origin !== "null")' in script
    assert 'new URL("/visualizations/blank", fallbackOrigin)' in script
    assert "function paramsFromVisualizationConfig()" in script
    assert "function visualizationConfigStateSummary()" in script
    assert "urlParamsOverrideVisualizationConfig: true" in script
    assert "about-blank-iframe-url-unavailable" in script
    assert "Galaxy did not expose a writable iframe or parent visualization URL" in script
    assert '"localDrag", "rotateSensitivity", "render", "outline"' in script
    assert 'localDrag: state.localDrag === true ? null : "0"' in script
    assert "render: state.renderMode === defaultRenderMode() ? null : state.renderMode" in script
    assert 'outline: state.outline === defaultOutline() ? null : state.outline ? "1" : "0"' in script
    assert 'state.localDrag = booleanParam("localDrag", true)' in script
    assert "scope: context.scope" in script
    assert "urlStatePersistence: true" in script
    assert "sidebarLayout: true" in script
    assert "accordionControls: true" in script
    assert "compactControlPanels: true" in script
    assert "selectedVisualColor" in script
    assert "renderStyle: canvasRenderStyleSummary()" in script
    assert "selectedVisualRadius" in script
    assert "visibility: {" in script
    assert "chipCount" in script
    assert "function setLoadedSceneStatus()" in script
    assert "geometryMode:" in script
    assert "statusText: elements.status.textContent" in script
    assert "maskedResidues:" in script
    assert "availableColorPalettes: paletteNames()" in script
    assert "playback: false" in script
    assert 'layoutModes: ["tiled"]' in script
    assert 'bindings: ["u/i", "n/m", "j/k", "[/]", "-/=", ",/."]' in script
    assert "queueInteractiveGeometryUpdate" in script
    assert "presentation: {" in script
    assert "spacing: state.spacing" in script
    assert "columns: state.columns" in script
    assert "elements.layoutSelect.value = state.layout" not in script
    assert "setLayout(event.target.value)" not in script
    assert "x: Number(state.rotation.x.toFixed(3))" in script
    assert '<entry_point entry_point_type="script" type="text/javascript" src="script_compact_0624.js"' in xml
    assert 'url="/static/plugins/visualizations/flipbook_molstar/static"' not in xml
    assert "patch_asgi_visualization_href" in (ROOT / "scripts" / "sync_visualization_static.py").read_text()
    assert "<param required=\"false\">history_id</param>" in xml
    assert '<visualization name="RMSX Flipbook">' in xml
    assert "<test test_attr=\"ext\">rmsx.json</test>" in xml
    assert "<test test_attr=\"ext\">json</test>" not in xml
    assert 'extension="rmsx.json"' in datatypes
    assert '<visualization plugin="flipbook_molstar"' in datatypes
    assert '<data name="viewer_manifest" format="rmsx.json"' in wrapper
    assert "RMSX Flipbook viewer manifest - open with Visualize" in wrapper
    assert '<option value="example" selected="true">Load example data: 1UBQ plus mon_sys</option>' in wrapper
    assert '<param argument="--num_slices" type="integer" value="9" min="1" label="Number of trajectory slices"/>' in wrapper
    assert '<output name="viewer_manifest" ftype="rmsx.json">' in wrapper
    assert '<data name="rmsx_heatmap_plot" format="png"' in wrapper
    assert '<data name="rmsx_triple_plot" format="png"' in wrapper
    assert '<output name="rmsx_heatmap_plot" ftype="png">' in wrapper
    assert '<output name="rmsx_triple_plot" ftype="png">' in wrapper
    assert '<has_size min="1000"/>' in wrapper
    assert 'expect_num_outputs="9"' in wrapper
    assert "rmsx_static_plots.py" in wrapper
    assert "--rmsx-source" in wrapper
    assert "--heatmap-output '$rmsx_heatmap_plot'" in wrapper
    assert "--triple-output '$rmsx_triple_plot'" in wrapper
    assert "RMSX static plots written" in wrapper
    assert '<data name="molstar_report"' not in wrapper
    assert "--output '$molstar_report'" not in wrapper
    assert 'ghcr.io/antuneslab/flipbook-galaxy:0.2.3-galaxy0' in macros
    assert "@VERSION_SUFFIX@" in macros
    assert "galaxy.datatypes.text:Json" in datatypes
    assert "static/plugins/visualizations" in static_sync
    assert '"vendor" / "molstar" / "5.4.2" / "molstar.js"' in static_sync
    assert "native_visualization_parity_check.mjs" in plugin_readme
    assert "native_visualization_visual_check.mjs" in plugin_readme
    assert '"test:native-visual": "node tests/flipbook/native_visualization_visual_check.mjs"' in package_json
    assert "FLIPBOOK_MOLSTAR_VIS_URL" in parity_script
    assert "page.frames().filter((frame) => frame !== page.mainFrame())" in parity_script
    assert "molstar-control-panels" in parity_script
    assert "molstar-control-tabs" not in parity_script
    assert "sidebar accordion controls are active" in parity_script
    assert "molstar-render-select" not in parity_script
    assert "molstar-outline-checkbox" in parity_script
    assert "molstar-rotate-sensitivity-range" in parity_script
    assert "molstar-radius-legend" in parity_script
    assert "molstar-residue-marker-checkbox" not in parity_script
    assert "marker toggle enables selected-residue overlay" not in parity_script
    assert "marker toggle disables selected-residue overlay" not in parity_script
    assert "molstar-local-rotate-checkbox" not in parity_script
    assert "reset scale restores color, radius, and thickness defaults" in parity_script
    assert "render preset control updates diagnostics" not in parity_script
    assert "outline toggle updates diagnostics and URL state" in parity_script
    assert "rotate sensitivity updates diagnostics" in parity_script
    assert "legend?.elements?.colorBar" in parity_script
    assert "urlState?.synced" in parity_script
    assert "canvasVisualStats" in visual_script
    assert "FLIPBOOK_MOLSTAR_MANIFEST" in visual_script
    assert "function parseManifestText(text)" in visual_script
    assert "item_data || parsed?.data || parsed?.contents || parsed?.content" in visual_script
    assert "async function writeManifestHarness(manifest, sourcePath)" in visual_script
    assert "tiled Flipbook view shows at least" in visual_script
    assert "tiled Flipbook clusters are framed inside the canvas margins" in visual_script
    assert "Molstar canvas is nonblank" in visual_script
    assert "presentation?.tiledPlacement?.slot" in visual_script
    assert "presentation?.tiledPlacement?.cameraExtraRadius" in visual_script
    assert "native_visualization_harness.html" in plugin_readme
    assert "schemaVersion: \"flipbook-molstar-viewer/v1\"" in harness
    assert "tilePaddingFactor: 1.55" in harness
    assert "../../config/plugins/visualizations/flipbook_molstar/static/script_compact_0624.js" in harness


def write_static_plot_fixture(tmpdir):
    rmsx = tmpdir / "rmsx_demo_0.015_ns.csv"
    rmsx.write_text(
        "ResidueID,ChainID,slice_1.dcd,slice_2.dcd\n"
        "1,7,0.25,1.25\n"
        "2,7,0.50,2.50\n",
        encoding="utf-8",
    )
    rmsd = tmpdir / "rmsd.csv"
    rmsd.write_text("Frame,Time,RMSD\n0,0,0.0\n1,1,0.2\n", encoding="utf-8")
    rmsf = tmpdir / "rmsf.csv"
    rmsf.write_text("ResidueID,RMSF\n1,0.1\n2,0.2\n", encoding="utf-8")
    plot_script = tmpdir / "plot_rmsx.R"
    plot_script.write_text("# fake plot script placeholder\n", encoding="utf-8")
    return rmsx, rmsd, rmsf, plot_script


def write_fake_rscript(tmpdir, body):
    fake_rscript = tmpdir / "fake_Rscript.py"
    fake_rscript.write_text(body, encoding="utf-8")
    fake_rscript.chmod(0o755)
    return fake_rscript


def test_static_plot_helper_preserves_heatmap_and_triple_outputs():
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        rmsx, rmsd, rmsf, plot_script = write_static_plot_fixture(tmpdir)
        fake_rscript = write_fake_rscript(
            tmpdir,
            """#!/usr/bin/env python3
import csv
import sys
from pathlib import Path

if len(sys.argv) > 1 and sys.argv[1] == "-e":
    sys.exit(0)

png = b"\\x89PNG\\r\\n\\x1a\\n"
rmsx = Path(sys.argv[2])
triple = sys.argv[6]
with rmsx.open(newline="", encoding="utf-8") as handle:
    chain_id = next(csv.DictReader(handle))["ChainID"]
out = rmsx.with_name(f"{rmsx.stem}_rmsx_plot_chain_{chain_id}.png")
out.write_bytes(png + triple.encode("ascii"))
print(f"fake plot triple={triple}")
""",
        )
        heatmap = tmpdir / "heatmap.png"
        triple = tmpdir / "triple.png"
        result = subprocess.run(
            [
                sys.executable,
                str(TOOLS / "rmsx_static_plots.py"),
                "--rmsx-source",
                str(rmsx),
                "--rmsd-source",
                str(rmsd),
                "--rmsf-source",
                str(rmsf),
                "--palette",
                "turbo",
                "--heatmap-output",
                str(heatmap),
                "--triple-output",
                str(triple),
                "--interpolate",
                "--rscript",
                str(fake_rscript),
                "--plot-script",
                str(plot_script),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        assert heatmap.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        assert triple.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        assert heatmap.read_bytes().endswith(b"FALSE")
        assert triple.read_bytes().endswith(b"TRUE")
        assert heatmap.read_bytes() != triple.read_bytes()
        assert "RMSX static plots written" in result.stdout


def test_static_plot_helper_fails_when_rscript_does_not_create_png():
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        rmsx, rmsd, rmsf, plot_script = write_static_plot_fixture(tmpdir)
        fake_rscript = write_fake_rscript(
            tmpdir,
            """#!/usr/bin/env python3
print("pretending to succeed without writing a plot")
""",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(TOOLS / "rmsx_static_plots.py"),
                "--rmsx-source",
                str(rmsx),
                "--rmsd-source",
                str(rmsd),
                "--rmsf-source",
                str(rmsf),
                "--palette",
                "viridis",
                "--heatmap-output",
                str(tmpdir / "heatmap.png"),
                "--triple-output",
                str(tmpdir / "triple.png"),
                "--rscript",
                str(fake_rscript),
                "--plot-script",
                str(plot_script),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode != 0
        assert "PNG was not created" in result.stderr


if __name__ == "__main__":
    test_manifest_payload()
    test_native_visualization_contract()
    test_static_plot_helper_preserves_heatmap_and_triple_outputs()
    test_static_plot_helper_fails_when_rscript_does_not_create_png()
