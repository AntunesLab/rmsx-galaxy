# Flipbook Galaxy

Galaxy integration workspace for [RMSX + Flipbook](https://github.com/AntunesLab/rmsx).

This repository is a cofest collaboration companion to upstream RMSX. Upstream RMSX remains the scientific Python/R package for time-sliced residue fluctuation analysis and Flipbook workflows. This repo focuses on making Flipbook easy to run in Galaxy, with RMSX as the underlying analysis engine and a native Molstar Flipbook visualization path.

## What Is Here

- Galaxy Flipbook tool wrapper: `tools/flipbook/`
- Native Galaxy Molstar visualization plugin: `config/plugins/visualizations/flipbook_molstar/`
- RMSX Flipbook manifest datatype scaffold: `config/datatypes/`
- Container runtime scaffold: `packaging/flipbook-galaxy/`
- Planemo, manifest, and viewer smoke tests: `tests/flipbook/`
- Cofest docs and task list: `docs/`

The native Galaxy visualization is the supported user-facing viewer path. The old standalone HTML report path is development-only.

## Quick Start For Collaborators

Prerequisites:

- Python 3.10 or newer
- Docker Desktop or another working Docker CLI
- Node.js with `corepack` or `pnpm` for optional browser checks

Clone the repo, then run:

```bash
scripts/bootstrap_dev.sh --with-container
scripts/run_static_checks.sh
scripts/serve_galaxy_demo.sh
```

Open the printed Galaxy URL, usually:

```text
http://127.0.0.1:9090
```

In Galaxy:

1. Open **Tools**.
2. Select **Flipbook trajectory analysis**.
3. Keep the default **Load example data: 1UBQ plus mon_sys** input source.
4. Click **Run Tool**.
5. Open the **RMSX Flipbook viewer manifest** output.
6. Use **Visualize** -> **RMSX Flipbook**.

That path uses the bundled 1UBQ example data and does not require collaborators to upload a trajectory before testing the tool.

## Common Commands

Create or refresh the local development environment:

```bash
scripts/bootstrap_dev.sh
```

Build the local runtime image used by Planemo/Galaxy:

```bash
scripts/build_container.sh
```

Run fast checks:

```bash
scripts/run_static_checks.sh
```

By default this skips the network-dependent Tool Shed check when the public Tool Shed cannot be reached. For publication or CI, make that step strict:

```bash
STRICT_SHED_LINT=1 scripts/run_static_checks.sh
```

Run Docker-backed Planemo tests:

```bash
scripts/run_planemo_tests.sh
```

Start the local Galaxy demo on another port:

```bash
GALAXY_PORT=9091 scripts/serve_galaxy_demo.sh
```

If Docker is installed somewhere unusual, set:

```bash
DOCKER_CMD=/path/to/docker scripts/serve_galaxy_demo.sh
```

## What A Successful Demo Shows

A successful bundled-example Galaxy run should produce:

- RMSX, RMSD, and RMSF tables
- PDB slice collection
- RMSX heatmap PNG
- RMSX triple plot PNG
- execution log
- RMSX Flipbook viewer manifest

The manifest should open through Galaxy's native **Visualize** path without a trusted-HTML warning. The viewer should open in tiled mode by default and expose palette switching, spacing, thickness, columns, residue controls, and local per-slice rotation.

## Troubleshooting

If `scripts/bootstrap_dev.sh` cannot install Planemo, confirm that Python can create virtual environments:

```bash
python3 -m venv /tmp/rmsx-venv-check
```

If Docker tests fail because the image cannot be found, build it locally:

```bash
scripts/build_container.sh
```

The wrapper references the registry-style tag `ghcr.io/antuneslab/flipbook-galaxy:0.2.3-galaxy0`. The local build script creates that tag on your machine, so Planemo can run before the image is published to GHCR.

If Galaxy starts but the visualization is blank, run this in a second terminal after Galaxy is fully up:

```bash
python3 scripts/sync_visualization_static.py
```

If port `9090` is already in use:

```bash
GALAXY_PORT=9091 scripts/serve_galaxy_demo.sh
```

## Cofest Goals

1. Make the local Galaxy demo reproducible for collaborators.
2. Harden the Flipbook wrapper and Molstar manifest output.
3. Package a shareable runtime container.
4. Improve the native Molstar visualization enough for a compelling cofest demo.
5. Decide what belongs upstream in RMSX versus what remains Galaxy-specific.

See [docs/cofest-task-list.md](docs/cofest-task-list.md) for the working task list.

For a collaborator-friendly implementation overview, see
[docs/flipbook-galaxy-implementation-explainer.md](docs/flipbook-galaxy-implementation-explainer.md).

For the IUC preparation checklist, see [docs/iuc-readiness-audit.md](docs/iuc-readiness-audit.md).

## Packaging Status

The current share path is container-first. The wrapper references:

```text
ghcr.io/antuneslab/flipbook-galaxy:0.2.3-galaxy0
```

For local cofest testing, run `scripts/build_container.sh` to build that tag locally. Before external Galaxy administrators can use the tag directly, the image should be pushed to GHCR by someone with `antuneslab` package permissions.

Longer term, a Bioconda or Conda package for the RMSX engine would make Galaxy dependency resolution cleaner and is expected before a polished IUC submission.

## Relationship To Upstream RMSX

Use upstream RMSX for the core method, scientific API, and publication-facing documentation. Use this repo for Galaxy wrapper work, native visualization experiments, container packaging, and cofest coordination. Changes that improve the general RMSX Python package can be proposed upstream after they are validated here.
