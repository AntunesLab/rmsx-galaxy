# Flipbook Galaxy Share Readiness

This project has two sharing paths:

1. A conservative Tool Shed/IUC candidate that installs the Flipbook wrapper and
   emits standard Galaxy datasets, including a JSON Molstar manifest.
2. A richer Galaxy admin/cofest bundle that also registers the prototype
   Molstar visualization plugin and optional project-local datatype.

## What Users Get

With the conservative wrapper, users can:

1. Run `Flipbook trajectory analysis`.
2. Receive CSV outputs, static RMSX heatmap/triple-plot PNGs, PDB slice
   collection, execution log, and a typed `rmsx.json` `RMSX Flipbook viewer manifest`.

When a Galaxy admin installs the full prototype visualization bundle, users can
also:

3. Open the manifest with Galaxy's `Visualize` action.
4. Choose `RMSX Flipbook`.
5. Use the native Molstar viewer without any trusted-HTML allowlist warning.

The public wrapper intentionally does not emit the old standalone HTML report.
The native manifest plus Galaxy visualization plugin is the supported viewer
path.

## Bundle Contents

- `tools/flipbook/flipbook.xml`
- `tools/flipbook/macros.xml`
- `tools/flipbook/rmsx_preflight.py`
- `tools/flipbook/flipbook_report_common.py`
- `tools/flipbook/flipbook_molstar_report.py`
- `tools/flipbook/test-data/`
- `config/plugins/visualizations/flipbook_molstar/`
- `config/datatypes/datatypes_conf.xml`
- `packaging/flipbook-galaxy/`

## Container Publication

The wrapper is configured for this registry-qualified image:

```text
ghcr.io/antuneslab/flipbook-galaxy:0.2.3-galaxy0
```

Build and push from the project root:

```bash
scripts/build_container.sh
docker push ghcr.io/antuneslab/flipbook-galaxy:0.2.3-galaxy0
```

If the image will live under a different owner or version, update
`tools/flipbook/macros.xml` before running final Planemo tests.

## Tool Shed Packaging Check

Run these before publishing or sending the bundle to another Galaxy admin:

```bash
scripts/run_static_checks.sh
```

Current local status:

- `planemo lint --fail_level error tools/flipbook/flipbook.xml` passes.
- `planemo shed_lint tools/flipbook` passes.
- Docker-backed `planemo test` should pass all three wrapper tests using
  `ghcr.io/antuneslab/flipbook-galaxy:0.2.3-galaxy0` as a locally tagged image.

Run the Docker-backed wrapper tests against the same container tag that appears
in `tools/flipbook/macros.xml`:

```bash
scripts/run_planemo_tests.sh
```

Then verify the native viewer:

```bash
node tests/flipbook/native_visualization_parity_check.mjs \
  --url "http://localhost:9090/visualizations/display?visualization=flipbook_molstar&dataset_id=..."

node tests/flipbook/native_visualization_visual_check.mjs \
  --url "http://localhost:9090/visualizations/display?visualization=flipbook_molstar&dataset_id=..." \
  --screenshot /private/tmp/flipbook_molstar_visual_check.png
```

## Galaxy Admin Install Shape

The conservative Tool Shed candidate has one Galaxy-side piece:

1. Install the Flipbook tool wrapper.

The full prototype viewer install has optional additional Galaxy-side pieces:

1. Register the `rmsx.json` datatype if using the dedicated local datatype.
2. Install/register the `flipbook_molstar` visualization plugin.

For local Planemo demos, the project uses:

```bash
scripts/serve_galaxy_demo.sh
```

For a managed Galaxy server, install the visualization directly into that
server's visualization plugin path instead of relying on the Planemo sync
helper.

Important limitation for sharing: a plain Tool Shed tool install can make the
RMSX computation and JSON manifest output available, but it is not by itself the
whole native viewer experience. Users get the Molstar visualization only on a
Galaxy instance where the `flipbook_molstar` visualization plugin has also been
registered by an admin.

## Remaining Publication Decisions

- Confirm provenance and regeneration details for the compressed full-frame XTC
  test fixture before opening an IUC PR.
- Generate the final dependency/license inventory from the runtime image.
- Decide whether the visualization plugin will be distributed as a local Galaxy
  admin bundle first, then proposed upstream later.
- Add CI for container build, Planemo lint, Planemo test, and native viewer
  harness checks.

## Before External Sharing

The last external step is publishing the container image:

```bash
docker push ghcr.io/antuneslab/flipbook-galaxy:0.2.3-galaxy0
```

That requires GHCR permissions for the `antuneslab` namespace. Until the image
is pushed, other Galaxy servers cannot resolve the container tag even though the
local Docker/Planemo tests can pass from the locally tagged image.
