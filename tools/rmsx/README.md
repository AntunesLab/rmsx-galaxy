# RMSX Galaxy Wrapper Scaffold

This directory contains the RMSX-only Galaxy wrapper scaffold. It is focused on the compute path and does not launch FlipBook, ChimeraX, or VMD. It emits a native Galaxy Molstar viewer manifest for the generated PDB slice collection.

## Current Scope

- Inputs: MDAnalysis/RMSX-readable topology and trajectory datasets, or the bundled 1UBQ/mon_sys example dataset from the tool form.
- Required selection: one RMSX chain/segment selector, with comma-separated selectors allowed.
- Slicing: number of trajectory slices, plus optional start/end frame controls.
- Outputs: RMSX CSV, RMSD CSV, RMSF CSV, mask metadata CSV, PDB slice collection, RMSX heatmap PNG, RMSX triple-plot PNG, native Molstar viewer manifest for Galaxy's Visualize action, and execution log.
- RMSX controls: analysis type, summary residue count, interpolation, and the shared Molstar/static-plot palette are exposed. The wrapper generates the original RMSX heatmap and RMSD/RMSX/RMSF triple plots after the validated compute step so users can compare static plots with the native Molstar FlipBook.
- Viewer integration: the native Galaxy Molstar visualization loads generated slices into one Molstar scene with Tiled and Overlay layouts, defaults to the tiled presentation, and uses Molstar `putty` representations with RMSX-normalized B-factors driving FlipBook-matched palette color and an explicit low-to-high worm radius range. The Galaxy form selects the viewer's starting palette, and the viewer can switch among viridis-family palettes such as `mako` and `turbo` interactively. Tiled mode exposes FlipBook-style tile spacing and column controls. Rotation controls apply one shared rotation matrix around each slice's own geometric center, then place that center on a shared FlipBook slot anchor plus any tile offset, so slices spin in place without drifting or orbiting the row. The default rotation honors FlipBook's ChimeraX `turn x 90` side-on view unless URL parameters override it. Local drag captures Molstar's current screen-right and screen-up camera axes and converts the gesture into a coordinate-space rotation delta, matching the VMD prototype's screen-axis/pivot behavior with an upward/downward drag direction aligned to common molecular-viewer expectations. The Molstar canvas defaults to a clean interactive render preset with a white background, antialiasing, a fine outline, no multisample/progressive accumulation, no fog, and no stochastic soft-lighting effects; `outline=0` can be added to disable the fine outline, and `render=soft` can be added to re-enable softer occlusion/illumination for comparison. The default live path updates Molstar representation transform matrices directly, with the browser-side PDB coordinate rewrite retained as a fallback. Masked residues are split into a second Molstar layer at 30% opacity when mask metadata is present, and the selected residue can be shown as a separate marker in every visible slice for cross-slice comparison.

## Important Packaging Note

The XML declares `rmsx` as the intended executable dependency, but RMSX still needs Galaxy-ready dependency packaging before this wrapper can run in a clean Planemo/Galaxy environment. The local source inspection found that RMSX depends on Python packages plus an R plotting stack, and the current R script can install missing R packages at runtime. For Galaxy, those R dependencies should be provided by Conda or a container instead.

The first dependency scaffold lives in `packaging/rmsx-galaxy/`. It builds a container from the upstream RMSX source repository and preinstalls the Python/R runtime stack. The active wrapper references a registry-qualified container tag, `ghcr.io/antuneslab/rmsx-galaxy:0.2.3-galaxy0`. Collaborators can build that tag locally with `scripts/build_container.sh` before it is published to GHCR.

For purely local development, you may temporarily retag or override the container as `rmsx-galaxy:0.2.3-galaxy0`, but the shareable wrapper should keep the registry-qualified tag in `tools/rmsx/macros.xml`.

The first CLI smoke path exercises the RMSX compute step only and only requires a topology, trajectory, chain/segment selector, and slice count. The Galaxy wrapper then calls the packaged R plotting script separately to create explicit heatmap and triple-plot PNG outputs. The fixture path uses PDB/XTC:

```bash
RMSX_NO_CITATION=1 rmsx input.pdb input.xtc --output_dir rmsx_output --num_slices 3 --chain A --palette viridis --start_frame 0 --analysis_type protein --summary_n 3 --no-interpolate --quiet --no-plot --overwrite
```

## Local Verification

The wrapper fixture compute path can be smoke-tested through the container:

```bash
scripts/build_container.sh
mkdir -p /tmp/rmsx_galaxy_wrapper_smoke
docker run --rm \
  -v "$PWD/tools/rmsx/test-data:/data:ro" \
  -v /tmp/rmsx_galaxy_wrapper_smoke:/out \
  ghcr.io/antuneslab/rmsx-galaxy:0.2.3-galaxy0 \
  rmsx /data/1UBQ.pdb /data/mon_sys.xtc \
    --output_dir /out \
    --num_slices 3 \
    --chain 7 \
    --quiet \
    --no-plot \
    --overwrite
```

That run produced the expected RMSX, RMSD, and RMSF CSV files plus three `slice_*_first_frame.pdb` files. The installed RMSX environment used for this smoke test does not emit `masked_residues.csv`; the Galaxy wrapper therefore derives an all-unmasked metadata table from the RMSX CSV when RMSX omits that file. During a full Galaxy run, `rmsx_static_plots.py` locates the installed RMSX `plot_rmsx.R` script and writes the standalone heatmap and original triple-composite PNG outputs.

The Galaxy tool form includes an input-source selector. "Use datasets from history" accepts uploaded topology/structure and DCD/XTC trajectory datasets, preserves their Galaxy extensions with job-local symlinks, and validates them with `rmsx_preflight.py` before RMSX runs. "Load example data: 1UBQ plus mon_sys" uses `tools/rmsx/test-data/1UBQ.pdb` and `tools/rmsx/test-data/mon_sys.xtc` directly from the wrapper directory. The example branch defaults to chain/segment ID `7` and nine trajectory slices so a fresh Galaxy session can produce the interactive reports without a manual upload step.

The Galaxy wrapper creates the native Molstar viewer manifest with `rmsx_molstar_report.py`. Shared report-parsing helpers live in `rmsx_report_common.py`. The script can still write a standalone HTML report for development if called manually with `--output`, but the public Galaxy wrapper does not emit that HTML dataset.

The manifest uses schema version `rmsx-molstar-viewer/v1` and embeds the PDB slice text, RMSX residue values, slice summaries, mask metadata, palette defaults, layout defaults, and Molstar render settings. The conservative wrapper emits this output as standard Galaxy JSON. A project-local `rmsxmolstar` datatype remains available for local Galaxy experiments, but it is not required by the Tool Shed candidate unless Galaxy/IUC agrees on that datatype route. A local prototype Galaxy visualization plugin lives under `config/plugins/visualizations/rmsx_molstar`; run Planemo with the visualization plugin directory override to make the manifest offer the `RMSX Molstar FlipBook` Visualize action.

The native visualization is now the primary and public viewer target. Its Galaxy iframe UI opens with a compact desktop control sidebar on the left, the View panel selected by default, and the Molstar canvas taking the remaining space. The sidebar exposes View, Style, Rotation, and Metrics panels. View focuses on tiled FlipBook layout, spacing, columns, and numbered slice visibility chips; Style carries palette, RMSX color/radius ranges, thickness, outline, and reset controls; Metrics summarizes the whole RMSX sequence. Narrow iframes collapse back to the stacked layout.

Native tiled placement now reserves stable slots from the default side-on projected row footprint plus configured putty-radius padding, which gives thick RMSX worms room to rotate without overlap while avoiding unnecessarily wide rows for long, skinny structures. Reset View and initial load apply extra putty-aware camera margin so the row opens as a readable whole-scene FlipBook rather than a close crop.

The native viewer loads the bundled Molstar 5.4.2 assets from the Galaxy
visualization plugin, validates the manifest schema, and renders all visible
slices in one Molstar scene. Tiled mode is the default presentation and Overlay
is available for direct comparison. Slice chips toggle individual slices while
keeping structures loaded. Scale controls can switch palettes, calibrate the
RMSX color domain, tune putty radius, adjust thickness, and reset back to the
canonical RMSX mapping. Rotation uses one shared screen-axis rotation delta
applied independently around each slice's own geometric center, matching the
VMD prototype's local-pivot behavior without making the tiled row orbit around
a global origin. The clean render preset defaults to a white background, stable
antialiasing, and a fine outline without progressive speckling.

## Container Verification

The runtime image in `packaging/rmsx-galaxy/` is built locally with the same tag that the Galaxy wrapper declares:

```bash
scripts/build_container.sh
```

The container exposes the RMSX CLI:

```bash
docker run --rm ghcr.io/antuneslab/rmsx-galaxy:0.2.3-galaxy0 rmsx --help
```

The container also completed the RMSX compute smoke fixture and produced the expected RMSX, RMSD, RMSF, mask metadata, and three PDB slice files:

```bash
mkdir -p /tmp/rmsx_container_smoke
docker run --rm \
  -v "$PWD/tools/rmsx/test-data:/data:ro" \
  -v /tmp/rmsx_container_smoke:/out \
  ghcr.io/antuneslab/rmsx-galaxy:0.2.3-galaxy0 \
  rmsx /data/1UBQ.pdb /data/mon_sys.xtc \
    --output_dir /out \
    --num_slices 3 \
    --chain 7 \
    --quiet \
    --no-plot \
    --overwrite
```

For Docker-backed Planemo/Galaxy tests, use `config/planemo_docker_job_conf.yml`. The explicit job config keeps Galaxy's Docker volume configuration to `$defaults`, which avoids a local Planemo/Galaxy volume-quoting failure seen with the generated config.

## Planemo Validation

Planemo is installed project-locally by `scripts/bootstrap_dev.sh` in `.venv-planemo`.

The wrapper exposes an input-source selector, PDB topology input, DCD/XTC trajectory input, a chain/segment selector, slice count, frame window controls, analysis type, summary count, interpolation, and a shared Molstar/static-plot palette selector. The bundled example branch uses the wrapper fixture files directly and keeps only the relevant example controls visible. The wrapper should pass XML parsing, Planemo lint at error level, and Docker-backed Galaxy tool tests using the explicit `ghcr.io/antuneslab/rmsx-galaxy:0.2.3-galaxy0` container:

```bash
scripts/run_static_checks.sh
```

The Docker-backed Planemo test uses the locally built RMSX runtime image instead of the local RMSX Python environment:

```bash
scripts/run_planemo_tests.sh
```

That Docker-backed run should resolve the registry-qualified RMSX container, launch Docker, produce the static RMSX heatmap and triple-plot PNGs, produce the native Molstar viewer manifest, and pass the wrapper tests. The test suite covers the history-input path, bundled-example path, and an expected preflight failure for a missing chain/segment selector. The Tool Shed candidate manifest output is JSON; the local `rmsxmolstar` datatype is only needed for prototype visualization experiments.

For manual native visualization testing in local Galaxy, use the serve helper:

```bash
scripts/serve_galaxy_demo.sh
```

It builds the merged datatype registry, starts Planemo/Galaxy with the prototype visualization plugin directory, and mirrors the visualization assets into the temporary Galaxy checkout created by Planemo. After running RMSX, open the `Molstar native viewer manifest - open with Visualize` history item, choose `Visualize`, and launch `RMSX Molstar FlipBook`. This route renders the manifest through Galaxy's visualization framework and avoids the trusted-HTML allowlist banner.

To exercise the native viewer parity checklist against a running visualization, copy the open visualization URL and run:

```bash
node tests/rmsx/native_visualization_parity_check.mjs \
  --url "http://localhost:9090/visualizations/display?visualization=rmsx_molstar&dataset_id=..."
```

That browser check verifies the sidebar layout, compact panels, canvas render, palette switching, scale controls, tiled/overlay layouts, residue marker toggle, local drag rotation diagnostics, and managed URL-state synchronization. It requires Playwright in the Node environment and is intentionally separate from the normal wrapper smoke tests.

For a visual smoke check after camera, spacing, or representation changes, run:

```bash
node tests/rmsx/native_visualization_visual_check.mjs \
  --url "http://localhost:9090/visualizations/display?visualization=rmsx_molstar&dataset_id=..." \
  --screenshot /private/tmp/rmsx_molstar_visual_check.png
```

That check waits for the native tiled view, saves a screenshot, reads the
Molstar canvas pixels, and asserts that the default view is nonblank and split
into separated visual clusters.

You can also point the same visual check at a saved manifest file, including a
Galaxy API response that wraps the manifest JSON in `item_data`:

```bash
node tests/rmsx/native_visualization_visual_check.mjs \
  --manifest /private/tmp/rmsx_manifest_text_content.json \
  --screenshot /private/tmp/rmsx_molstar_manifest_visual_check.png
```

When Galaxy's visualization route is blank or being rebuilt, you can exercise the same native viewer script without Galaxy:

```bash
python3 -m http.server 8787
node tests/rmsx/native_visualization_parity_check.mjs \
  --url "http://127.0.0.1:8787/tests/rmsx/native_visualization_harness.html"
```

The harness embeds a tiny RMSX Molstar manifest and loads the project visualization script plus local Molstar assets. It is a parity/debug harness, not a replacement for the final Galaxy Visualize acceptance check.

Do not use `--no_install_prebuilt_client` for this local prototype unless you are intentionally debugging Galaxy's frontend build. On current Galaxy master that path forced a local client build and failed during `pnpm` lockfile validation, while the prebuilt-client path successfully loaded the `rmsx_molstar` plugin.

Galaxy-specific details now handled in the wrapper:

- Galaxy stages uploaded datasets as extensionless `.dat` files, so the command symlinks them to `input_topology.<ext>` and `input_trajectory.<ext>` before invoking RMSX.
- The bundled example mode symlinks the wrapper's `test-data/1UBQ.pdb` and `test-data/mon_sys.xtc` to job-local `input_topology.pdb` and `input_trajectory.xtc`.
- `rmsx_preflight.py` validates topology/trajectory loading, atom/frame counts, frame windows, requested slice counts, and chain/segment selectors before RMSX runs.
- The fallback mask metadata writer uses LF line endings so Planemo line assertions are stable.

The package requirement versions in `macros.xml` are pinned to the versions present in the tested RMSX container. The explicit container remains the active runtime path until RMSX has a proper Conda/Bioconda package.

## Next Packaging Decisions

- Decide which RMSX tag or commit should become the first Galaxy-supported runtime target.
- Publish and pin a container image, then add an explicit Galaxy `<container type="docker">...` requirement.
- Prepare a Conda/Bioconda recipe so the wrapper can eventually resolve through Galaxy's preferred package path.
- Add an all-chain CLI mode or wrapper-side adapter after the single-chain path is stable.
- Decide when to expose mask selections after the CLI supports them directly.
- Decide whether the native `rmsx_molstar` visualization should stay as a local Galaxy visualization plugin, move into Galaxy Charts packaging, or be proposed upstream with the `rmsxmolstar` manifest datatype.
- Add Molstar-specific RMSX themes if the generic `uncertainty` theme is not sufficient for publication-quality color scale control.
