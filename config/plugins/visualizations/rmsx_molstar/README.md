# RMSX Molstar Galaxy Visualization Plugin

This is a local prototype Galaxy visualization plugin for RMSX
`rmsx-molstar-viewer/v1` manifests.

The plugin is registered for the project-local `rmsxmolstar` datatype and also
for generic `json` datasets during prototype development. In both cases it
validates `schemaVersion` at runtime and shows a clear unsupported-manifest
message for unrelated JSON files.

`tools/rmsx/datatypes_conf.xml` registers the dedicated `rmsxmolstar` datatype
beside the wrapper for linting and Tool Shed-style packaging. The same
registration is also mirrored in `config/datatypes/datatypes_conf.xml` as a
standalone snippet for local Galaxy experiments. Do not point Galaxy at the
standalone snippet as the entire `datatypes_config_file` unless it has been
merged with Galaxy's stock datatype registry; using the snippet alone hides
built-in datatypes such as `pdb`, `json`, and `html`.

The native plugin loads the bundled Molstar 5.4.2 viewer assets from
`static/vendor/molstar/5.4.2` first. The manifest/CDN URL is retained as a
development fallback only.

For local Planemo serving, first build a full datatype registry that contains
Galaxy's stock datatypes plus the RMSX Molstar manifest datatype:

```bash
python3 scripts/build_rmsx_datatypes_config.py
```

Then point Galaxy at both the merged datatype registry and this visualization
plugin directory:

```bash
GALAXY_CONFIG_OVERRIDE_DATATYPES_CONFIG_FILE="$PWD/config/datatypes/merged_datatypes_conf.xml" \
GALAXY_CONFIG_OVERRIDE_VISUALIZATION_PLUGINS_DIRECTORY="$PWD/config/plugins/visualizations" \
env HOME="$PWD/.planemo-home" .venv-planemo/bin/planemo serve \
  --host 127.0.0.1 --port 9090 \
  --install_prebuilt_client \
  --docker \
  --docker_cmd /Applications/Docker.app/Contents/Resources/bin/docker \
  --job_config_file config/planemo_docker_job_conf.yml \
  --no_conda_auto_install \
  --no_conda_auto_init \
  tools/rmsx/rmsx.xml
```

In a second terminal, mirror the plugin assets into the active temporary Galaxy
checkout so Galaxy's `/static/plugins/visualizations/...` route can serve the
entry point and bundled Molstar files:

```bash
python3 scripts/sync_visualization_static.py
```

After running RMSX, open the `Molstar native viewer manifest - open with
Visualize` history item and use Galaxy's `Visualize` action to launch `RMSX
Molstar FlipBook`. This path
renders through Galaxy's native visualization framework, so it does not need the
trusted-HTML allowlist used by standalone HTML report datasets.

The plugin prefers Galaxy's history-content display endpoint when a
`history_id` is available, then falls back to Galaxy's dataset text-content and
dataset display APIs. A direct test URL can therefore include both ids:

```text
http://localhost:9090/visualizations/display?visualization=rmsx_molstar&dataset_id=...&history_id=...
```

The native viewer opens with a desktop control sidebar on the left and the
Molstar canvas filling the remaining space. The Layout accordion is open by
default and focuses on two all-slices modes: Tiled and Overlay, plus slice
visibility chips and a compact loaded-state line. The remaining sidebar
accordions expose Appearance, Scale, Residues, Rotation, and Metrics without a
playback tab or Flip-only frame mode. Scale carries the HTML
fallback's visual calibration controls: palette switching, low/high RMSX color
domain, low/high putty radius, thickness, Reset Scale, and a live low/mid/high
color-and-radius legend. Appearance exposes the clean/soft render preset and
fine outline toggle, while Rotation exposes the local-drag sensitivity control
in addition to the X/Y/Z rotation controls. The selected-residue marker is
available from the Residues accordion but starts disabled so the default
FlipBook view emphasizes the RMSX worm geometry and color field without an
analysis overlay. Tiled placement reserves
slots from the default side-on projected row footprint plus the configured
putty-radius padding, so thick worms have room without pushing long, skinny
structures unnecessarily far apart. Reset View and initial load frame the scene
with extra putty-aware camera margin so the whole tiled row is visible before
the user starts inspecting individual slices. On narrow iframes, the sidebar
collapses back into a stacked top control area so the viewer remains usable.

For an interactive parity smoke check, copy the native visualization URL from
the browser and run:

```bash
node tests/rmsx/native_visualization_parity_check.mjs \
  --url "http://localhost:9090/visualizations/display?visualization=rmsx_molstar&dataset_id=..."
```

The parity script expects a running Galaxy page and a Node environment with
Playwright available. It checks that the sidebar accordions render,
Molstar creates a canvas, palette/scale/layout/residue/local-drag controls
update diagnostics, and the managed URL state stays synchronized.

For a slower visual smoke check that also saves a screenshot and inspects the
rendered canvas for separated tiled clusters, run:

```bash
node tests/rmsx/native_visualization_visual_check.mjs \
  --url "http://localhost:9090/visualizations/display?visualization=rmsx_molstar&dataset_id=..." \
  --screenshot /private/tmp/rmsx_molstar_visual_check.png
```

This check is useful after layout, camera, spacing, or representation changes
because it catches blank canvases and tiled rows that visually collapse into a
single cluster.

The same checker can also render a saved `rmsx-molstar-viewer/v1` manifest
directly, including Galaxy API responses that wrap the manifest in `item_data`:

```bash
node tests/rmsx/native_visualization_visual_check.mjs \
  --manifest /private/tmp/rmsx_manifest_text_content.json \
  --screenshot /private/tmp/rmsx_molstar_manifest_visual_check.png
```

If Galaxy's visualization display route is not cooperating, run the same parity
script against the local harness. From the project root:

```bash
python3 -m http.server 8787
```

Then, in a second terminal:

```bash
node tests/rmsx/native_visualization_parity_check.mjs \
  --url "http://127.0.0.1:8787/tests/rmsx/native_visualization_harness.html"
```

The harness uses an inline `rmsx-molstar-viewer/v1` manifest but loads the same
native visualization script and vendored Molstar assets as Galaxy.

The visual check can target the same harness URL; it should report at least
three separated visual clusters for the bundled three-slice manifest.

For production-style Galaxy packaging, install the visualization as a standard
plugin under Galaxy's `static/plugins/visualizations/rmsx_molstar` path, or use
Galaxy's current visualization packaging mechanism for that static location. The
`sync_visualization_static.py` helper is only for Planemo's disposable local
Galaxy checkout.

Avoid `--no_install_prebuilt_client` for ordinary local smoke tests. It forces a
local Galaxy client build, which can fail on current Galaxy master before the
visualization plugin is exercised.
