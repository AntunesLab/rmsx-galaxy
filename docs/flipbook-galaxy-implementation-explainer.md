# Flipbook Galaxy Implementation Explainer

This document is a quick collaborator-facing explanation of how the Flipbook Galaxy
integration works under the hood. It is meant to help us discuss the design,
debug runs, and explain the project clearly during cofest or IUC-oriented
review.

## The Short Version

This repo wraps upstream RMSX as a Galaxy tool and adds a native Galaxy Molstar
Flipbook visualization path.

The Galaxy tool runs RMSX on a PDB topology plus a DCD or XTC trajectory,
generates the standard RMSX scientific outputs, restores the original static R
plot outputs, and writes a structured JSON manifest for the Molstar viewer. The
interactive viewer is separate from the tool job: Galaxy stores the manifest as
a normal dataset, then the native visualization plugin renders that manifest
through Galaxy's **Visualize** path.

That separation is intentional. The tool stays reviewable as a conventional
Galaxy wrapper with typed outputs, while the Molstar viewer can evolve as a
Galaxy visualization plugin.

## Main Pieces

- `tools/flipbook/flipbook.xml`: the Galaxy tool wrapper.
- `tools/flipbook/macros.xml`: pinned versions, requirements, container tag, and
  citations.
- `tools/flipbook/rmsx_preflight.py`: validates topology, trajectory, selector, and
  frame settings before RMSX runs.
- `tools/flipbook/rmsx_static_plots.py`: calls the upstream RMSX R plotting script
  to generate PNG plots.
- `tools/flipbook/flipbook_molstar_report.py`: builds the Molstar viewer manifest.
- `tools/flipbook/flipbook_report_common.py`: shared parsing helpers for RMSX tables and
  PDB slice outputs.
- `config/plugins/visualizations/flipbook_molstar/`: native Galaxy visualization
  plugin that renders the manifest with Molstar.
- `packaging/flipbook-galaxy/`: container scaffold for reproducible local Galaxy
  and Planemo runs.

## Tool Execution Flow

When the Flipbook Galaxy tool runs, the wrapper does the following:

1. Creates a working directory with `rmsx_output/` and `pdb_slices/`.
2. Either links user-provided Galaxy inputs or the bundled 1UBQ example data.
3. Runs `rmsx_preflight.py`.
4. Runs upstream `rmsx` in compute-only mode using `--no-plot`.
5. Copies RMSX, RMSD, RMSF, and mask metadata CSVs into Galaxy outputs.
6. Copies per-slice first-frame PDB snapshots into a Galaxy list collection.
7. Runs `rmsx_static_plots.py` to produce:
   - standalone RMSX heatmap PNG,
   - original RMSD/RMSX/RMSF triple plot PNG.
8. Runs `flipbook_molstar_report.py` to build a self-contained JSON viewer
   manifest.
9. Writes a text execution log with preflight and plotting status.

The wrapper currently supports the conservative PDB + DCD/XTC path for the
first Galaxy-ready milestone. RMSX and MDAnalysis can support more formats, but
each additional Galaxy datatype pair should be added deliberately with tests.

## Outputs

A successful run produces 9 Galaxy outputs:

1. RMSX table, CSV
2. RMSD table, CSV
3. RMSF table, CSV
4. mask metadata table, CSV
5. PDB slice collection, list of PDB datasets
6. RMSX heatmap plot, PNG
7. RMSX triple plot, PNG
8. execution log, TXT
9. Molstar native viewer manifest, JSON

The JSON manifest is the bridge between the conventional Galaxy tool output and
the interactive Molstar viewer.

## Why RMSX Runs With `--no-plot`

The wrapper asks RMSX to do computation first and skips RMSX's normal plotting
path during that run. Then the Galaxy helper calls the upstream R plotting
script explicitly.

That gives Galaxy predictable output paths. The original plotting script writes
the heatmap and triple plot through overlapping filenames, so the helper calls
the plotting code twice and copies each generated PNG to the correct Galaxy
output. It also verifies that the files exist, are non-empty, and have a PNG
signature.

## The Viewer Manifest

The manifest schema is:

```text
flipbook-molstar-viewer/v1
```

The manifest is standard JSON for the conservative Galaxy wrapper path. It
contains all data needed by the viewer:

- embedded PDB text for each slice,
- RMSX residue values,
- per-slice summary statistics,
- RMSX value domain,
- mask metadata,
- selected palette and available palette definitions,
- presentation defaults,
- visual mapping settings,
- local rotation model metadata,
- Molstar render-style defaults.

Embedding the PDB slice text keeps the first viewer path simple. The
visualization does not need to chase sibling datasets in the Galaxy history.
Later we can consider lazy loading from the PDB collection if large manifests
become a problem.

## Native Galaxy Molstar Viewer

The viewer plugin is registered in:

```text
config/plugins/visualizations/flipbook_molstar/
```

It accepts datasets with extension `json` and also accepts the project-local
`flipbookmolstar` datatype when that datatype is installed in a local Galaxy demo.
The plugin validates the manifest schema before rendering. Generic JSON files
should get a clear unsupported-manifest message instead of a broken viewer.

The viewer uses Molstar to render embedded PDB slices as Flipbook-style worm
ribbons. The current viewer supports:

- tiled layout by default,
- overlay and flip layout modes,
- palette switching,
- spacing, thickness, and column controls,
- residue selection/marker controls,
- masked residue styling,
- local per-slice rotation.

The rotation behavior is important. A drag gesture should apply the same
rotation delta to every slice, but each slice rotates around its own local
center. That preserves the tiled/row layout instead of making all slices orbit a
single global scene origin.

## Static Plots And Interactive Viewer Use The Same Palette

The wrapper exposes one palette selector. That palette is passed to:

- the static R heatmap/triple plot helper,
- the Molstar manifest as the initial viewer palette.

That makes it easier to compare the static heatmap with the interactive
Flipbook view.

## Runtime And Dependencies

The current shareable path is container-first:

```text
ghcr.io/antuneslab/flipbook-galaxy:0.2.3-galaxy0
```

For local testing, `scripts/build_container.sh` builds that tag locally. The
container pins upstream RMSX source ref `v0.2.3` and installs the Python, R, and
plotting dependencies needed by the wrapper.

The wrapper still declares Galaxy-style requirements in `tools/flipbook/macros.xml`.
The longer-term IUC-friendly route is a proper Conda/Bioconda RMSX package, or
a Galaxy-visible mulled container generated from Conda dependencies.

## Local Demo Path

For collaborators, the easiest smoke test is:

```bash
scripts/bootstrap_dev.sh --with-container
scripts/run_static_checks.sh
scripts/serve_galaxy_demo.sh
```

Then in Galaxy:

1. Open **Tools**.
2. Select **Flipbook trajectory analysis**.
3. Choose **Load example data: 1UBQ plus mon_sys**.
4. Click **Run Tool**.
5. Open **Molstar native viewer manifest - open with Visualize**.
6. Use **Visualize** -> **Flipbook Molstar**.

The bundled example exists so collaborators can test the tool without bringing
their own trajectory.

## Test Coverage

The current checks cover three layers:

- Static/local checks:
  - Python compile checks,
  - manifest and visualization smoke tests,
  - JavaScript syntax check,
  - Planemo lint.
- Docker-backed Planemo tests:
  - history-input success case,
  - bundled-example success case,
  - expected preflight failure case.
- IUC readiness check:
  - file-size audit for the candidate Tool Shed path.

The Docker-backed Planemo run currently passes all 3 wrapper tests.

## What Is Ready

The repo is ready for collaborator testing of the Galaxy workflow:

- the wrapper runs in local Planemo/Galaxy,
- the container builds,
- the example run produces all 9 expected outputs,
- static plots are restored,
- the native Molstar manifest is emitted as standard JSON,
- the visualization plugin renders the manifest in local Galaxy demos.

## Core Implementation Pain Points

These are the main places where the integration is nontrivial or likely to need
careful discussion with Galaxy collaborators.

### Tool Versus Viewer Boundary

Galaxy tools are easiest to review when they produce ordinary datasets. The
interactive Molstar experience is valuable, but it should not be the only useful
output. The current design handles this by making the Flipbook wrapper produce CSV,
PNG, PDB, log, and JSON outputs first, then letting the visualization plugin
render the JSON manifest separately.

The pain point is packaging and expectations: a Galaxy administrator can install
the tool wrapper and get useful outputs, but the rich Molstar viewer requires
the visualization plugin to be installed too.

### Manifest Size And Data Linking

The v1 manifest embeds PDB text directly. This makes the viewer reliable because
it can render from one JSON dataset without needing to discover sibling history
datasets. The tradeoff is manifest size. Long trajectories, many slices, or
large proteins could make the JSON output bulky.

The likely future improvement is a linked-data manifest that references the PDB
collection, but that is more complicated inside Galaxy visualizations and needs
careful API/security handling.

### Datatype Strategy

For local demos, a custom `flipbookmolstar` datatype is useful because it makes the
manifest feel like a first-class viewer input. For a conservative IUC tool PR,
standard `json` is safer because IUC generally does not want tool repositories
to introduce datatypes that belong in Galaxy core.

The pain point is discoverability. Standard JSON is easy to review, but it makes
the viewer less obviously tied to RMSX unless the user knows to use
**Visualize**.

### Molstar Asset Packaging

Molstar is open source and works well for the viewer, but the JavaScript bundle
is large. Vendoring it directly into an IUC tool candidate is likely to trigger
review and file-size concerns.

“Vendored Molstar assets” means local copies of Molstar's browser files, such
as the JavaScript and CSS bundles, checked into or shipped with this repository
instead of loaded from an external CDN at runtime. Vendoring is good for
reproducibility and offline Galaxy instances because the viewer does not depend
on `cdn.jsdelivr.net` or another remote host. The downside is that those files
are large and become part of the repository/package review surface.

For now, the Molstar assets belong with the local/native visualization prototype,
not the minimal Tool Shed wrapper. Before a public Galaxy submission, we should
ask Galaxy/IUC maintainers how they prefer Molstar-based visualization assets to
be packaged.

### Python And R Runtime Reproducibility

RMSX uses Python for analysis and R for the original static plots. That is fine
for Galaxy, but only if dependencies are pinned and preinstalled. Galaxy jobs
should not install R packages at runtime.

The current container solves this for local testing. The longer-term pain point
is producing a durable Conda/Bioconda package or mulled container so the runtime
is reproducible in standard Galaxy deployments.

### Upstream Version Metadata

The container pins upstream RMSX tag `v0.2.3`, but that tag currently installs
Python package metadata as `rmsx==0.1.0`. The wrapper is honest about the
installed executable version, but the mismatch will be confusing in review.

Before IUC submission, the upstream tag, Python package version, Conda package
version, and Galaxy wrapper version should tell one coherent story.

### Test Data Size

The bundled XTC fixture makes local testing easy. The original DCD trajectory
was larger than the tools-iuc 1 MB file-size check, so it has been converted to
precision-2 XTC. The current fixture keeps all 316 original frames and all atoms
while staying below the 1 MB limit.

The remaining pain point is provenance rather than size: before IUC submission,
we should document the original source, redistribution status, and exact
regeneration command for the compressed fixture.

### Rotation And Visual Fidelity

The Molstar viewer is not simply loading structures. It tries to mimic the
Flipbook idea: multiple protein slices shown together, with RMSX mapped to
color and worm thickness, and local per-slice rotation. The hard part is making
drag rotation feel natural while preserving the tiled layout.

The current approach applies the same rotation delta to every visible slice
around each slice's own center. This is the right conceptual model, but viewer
polish should still be tested across different protein shapes, slice counts,
and layouts.

### Review Surface Area

There are really two review tracks:

- The conservative Flipbook Galaxy tool wrapper.
- The native Molstar visualization plugin.

Bundling both into one first IUC submission could make review harder. The safer
path is to make the tool wrapper solid and useful on its own, then discuss the
visualization plugin with Galaxy/IUC as a coordinated follow-up.

## Known Issues Before IUC Submission

The main pre-IUC blockers are practical and review-oriented:

- The compressed `tools/flipbook/test-data/mon_sys.xtc` fixture is under the
  tools-iuc 1 MB file limit and preserves all 316 original frames, but its final
  provenance and regeneration command should be documented for review.
- Upstream RMSX tag `v0.2.3` currently installs Python package metadata as
  `rmsx==0.1.0`; the version story should be reconciled before public review.
- The native Molstar visualization and custom datatype should be discussed with
  Galaxy/IUC before submission as first-class plugin/datatype work.
- A final dependency/license inventory should be generated from the exact final
  runtime image.
- A bio.tools/EDAM strategy should be settled before an IUC PR.

## How To Explain The Design

The main design point is that this is not an opaque interactive report. It is a
normal Galaxy analysis tool first. The tool produces durable scientific outputs
that can be inspected, downloaded, tested, and used in workflows. The
interactive Molstar viewer is powered by a separate JSON manifest output, which
lets Galaxy own the analysis results and lets the viewer remain a clean
visualization layer.

That makes the implementation easier to test, easier to review, and more
aligned with how Galaxy tools are usually expected to behave.
