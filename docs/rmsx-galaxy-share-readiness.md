# RMSX Galaxy Share Readiness

This project is shareable as a Galaxy admin bundle, not as a single ordinary
Tool Shed install that automatically enables every viewer everywhere.

## What Users Get

When a Galaxy admin installs the full bundle, users can:

1. Run `RMSX trajectory analysis`.
2. Receive CSV outputs, static RMSX heatmap/triple-plot PNGs, PDB slice
   collection, execution log, and a `Molstar native viewer manifest`.
3. Open the manifest with Galaxy's `Visualize` action.
4. Choose `RMSX Molstar FlipBook`.
5. Use the native Molstar viewer without any trusted-HTML allowlist warning.

The public wrapper intentionally does not emit the old standalone HTML report.
The native manifest plus Galaxy visualization plugin is the supported viewer
path.

## Bundle Contents

- `tools/rmsx/rmsx.xml`
- `tools/rmsx/macros.xml`
- `tools/rmsx/datatypes_conf.xml`
- `tools/rmsx/rmsx_preflight.py`
- `tools/rmsx/rmsx_report_common.py`
- `tools/rmsx/rmsx_molstar_report.py`
- `tools/rmsx/test-data/`
- `config/plugins/visualizations/rmsx_molstar/`
- `config/datatypes/datatypes_conf.xml`
- `packaging/rmsx-galaxy/`

## Container Publication

The wrapper is configured for this registry-qualified image:

```text
ghcr.io/antuneslab/rmsx-galaxy:0.1.0
```

Build and push from the project root after selecting the RMSX source ref that
should be the first supported Galaxy runtime:

```bash
scripts/build_container.sh
docker push ghcr.io/antuneslab/rmsx-galaxy:0.1.0
```

If the image will live under a different owner or version, update
`tools/rmsx/macros.xml` before running final Planemo tests.

## Tool Shed Packaging Check

Run these before publishing or sending the bundle to another Galaxy admin:

```bash
scripts/run_static_checks.sh
```

Current local status:

- `planemo lint --fail_level error tools/rmsx/rmsx.xml` passes.
- `planemo shed_lint tools/rmsx` passes.
- Docker-backed `planemo test` passes all three wrapper tests using
  `ghcr.io/antuneslab/rmsx-galaxy:0.1.0` as a locally tagged image.

Run the Docker-backed wrapper tests against the same container tag that appears
in `tools/rmsx/macros.xml`:

```bash
scripts/run_planemo_tests.sh
```

Then verify the native viewer:

```bash
node tests/rmsx/native_visualization_parity_check.mjs \
  --url "http://localhost:9090/visualizations/display?visualization=rmsx_molstar&dataset_id=..."

node tests/rmsx/native_visualization_visual_check.mjs \
  --url "http://localhost:9090/visualizations/display?visualization=rmsx_molstar&dataset_id=..." \
  --screenshot /private/tmp/rmsx_molstar_visual_check.png
```

## Galaxy Admin Install Shape

The complete install has three Galaxy-side pieces:

1. Install the RMSX tool wrapper.
2. Register the `rmsxmolstar` datatype.
3. Install/register the `rmsx_molstar` visualization plugin.

For local Planemo demos, the project uses:

```bash
scripts/serve_galaxy_demo.sh
```

For a managed Galaxy server, install the visualization directly into that
server's visualization plugin path instead of relying on the Planemo sync
helper.

Important limitation for sharing: a plain Tool Shed tool install can make the
RMSX computation and manifest output available, but it is not by itself the
whole native viewer experience. Users get the Molstar visualization only on a
Galaxy instance where the `rmsxmolstar` datatype and `rmsx_molstar`
visualization plugin have also been registered by an admin.

## Remaining Publication Decisions

- Confirm the first public RMSX runtime tag or commit.
- Confirm the final image namespace and version.
- Decide whether the visualization plugin will be distributed as a local Galaxy
  admin bundle first, then proposed upstream later.
- Add CI for container build, Planemo lint, Planemo test, and native viewer
  harness checks.

## Before External Sharing

The last external step is publishing the container image:

```bash
docker push ghcr.io/antuneslab/rmsx-galaxy:0.1.0
```

That requires GHCR permissions for the `antuneslab` namespace. Until the image
is pushed, other Galaxy servers cannot resolve the container tag even though the
local Docker/Planemo tests can pass from the locally tagged image.
