# RMSX Galaxy

Galaxy and notebook integration workspace for [RMSX + FlipBook](https://github.com/AntunesLab/rmsx).

This repository is a cofest collaboration companion to the upstream RMSX project. Upstream RMSX remains the scientific Python/R package for time-sliced residue fluctuation analysis and FlipBook workflows. This repo focuses on making RMSX usable inside Galaxy, with a native Molstar FlipBook visualization path and a notebook prototype for inline Molstar viewing.

## What Is Here

- A Galaxy tool wrapper for RMSX trajectory analysis in `tools/rmsx/`.
- A native Galaxy visualization plugin for RMSX Molstar FlipBook manifests in `config/plugins/visualizations/rmsx_molstar/`.
- A JSON-backed RMSX Molstar manifest datatype scaffold in `config/datatypes/` and `tools/rmsx/datatypes_conf.xml`.
- A container-first runtime scaffold in `packaging/rmsx-galaxy/`.
- Planemo, viewer, and manifest smoke tests in `tests/rmsx/`.
- Notebook prototypes in `notebooks/`.
- Working project notes and readiness docs in `docs/`.

The native Galaxy visualization is the supported user-facing viewer path. The old standalone HTML report path is development-only and should not be presented as the primary Galaxy workflow.

## Cofest Goals

1. Make the local Galaxy demo reproducible for collaborators.
2. Harden the RMSX wrapper and Molstar manifest output.
3. Package a shareable runtime container.
4. Improve the native Molstar visualization enough for a compelling cofest demo.
5. Decide what belongs upstream in RMSX versus what remains Galaxy-specific.

See [docs/cofest-task-list.md](docs/cofest-task-list.md) for the working task list.

## Quick Local Checks

```bash
python3 -m py_compile tools/rmsx/*.py
python3 tests/rmsx/test_manifest_and_visualization.py
node --check config/plugins/visualizations/rmsx_molstar/static/script.js
python3 -m json.tool notebooks/rmsx_molstar_widget_sizing_prototype.ipynb
```

If Planemo is installed in the project-local environment:

```bash
.venv-planemo/bin/planemo lint --fail_level error tools/rmsx/rmsx.xml
.venv-planemo/bin/planemo shed_lint tools/rmsx
```

## Local Galaxy Demo

Build the merged datatype config, serve Galaxy through Planemo, then mirror the visualization static assets into the temporary Galaxy checkout:

```bash
python3 scripts/build_rmsx_datatypes_config.py

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

In a second terminal:

```bash
python3 scripts/sync_visualization_static.py
```

Run the bundled 1UBQ example in Galaxy, open the `Molstar native viewer manifest` history item with `Visualize`, and select `RMSX Molstar FlipBook`.

## Packaging Status

The current share path is container-first. The wrapper references:

```text
ghcr.io/antuneslab/rmsx-galaxy:0.1.0
```

Before external Galaxy administrators can use that tag, the image must be built and pushed by someone with GHCR permissions for `antuneslab`.

Longer term, a Bioconda or Conda package for RMSX would make Galaxy dependency resolution cleaner. That is a follow-up, not a blocker for the cofest workspace.

## Relationship To Upstream RMSX

Use upstream RMSX for the core method, scientific API, and publication-facing documentation. Use this repo for Galaxy wrapper work, native visualization experiments, container packaging, and cofest coordination. Changes that improve the general RMSX Python package or notebook helper can be proposed upstream after they are validated here.
