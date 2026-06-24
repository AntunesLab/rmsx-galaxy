# RMSX Galaxy Runtime Packaging

This directory contains the first runtime scaffold for making the RMSX Galaxy wrapper independent of Finn's local RMSX environment.

The current wrapper in `tools/rmsx/` passes Planemo tests when the existing local RMSX environment is placed on `PATH`. This packaging scaffold is the next bridge: build a container that Galaxy can resolve explicitly, then later replace the source-install bridge with a proper Conda/Bioconda package.

## Current Packaging Findings

- RMSX is currently source-install oriented. The upstream README documents cloning `https://github.com/AntunesLab/rmsx.git` and running `pip install -e .`.
- The local RMSX `pyproject.toml` declares the Python package name `rmsx`, Python `>=3.8`, and Python dependencies on `MDAnalysis` and `pandas`.
- RMSX plotting uses `Rscript` plus R packages `ggplot2`, `viridis`, `dplyr`, `tidyr`, `stringr`, `readr`, and `gridExtra`; masked heatmap hatching additionally uses `ggpattern`.
- A conda-forge/Bioconda search for `rmsx` returned no package for the active osx-arm64/noarch channels on 2026-06-03.
- `r-ggpattern` is available from conda-forge, so the prototype environment preinstalls it instead of letting RMSX download R packages at runtime.
- `environment.yml` now pins the Python/R dependency versions that were present in the tested local `rmsx-galaxy:0.1.0` image. Keep these in sync with `tools/rmsx/macros.xml` until RMSX has a proper Conda/Bioconda package.

## Container-First Prototype

Build from this directory's parent project root. For local iteration you can use
the short tag:

```bash
docker build -t rmsx-galaxy:0.1.0 packaging/rmsx-galaxy
```

For the shareable wrapper, build and push the registry-qualified tag referenced
by `tools/rmsx/macros.xml`:

```bash
docker build -t ghcr.io/antuneslab/rmsx-galaxy:0.1.0 packaging/rmsx-galaxy
docker push ghcr.io/antuneslab/rmsx-galaxy:0.1.0
```

Pin a specific RMSX source ref when moving beyond local iteration:

```bash
docker build \
  --build-arg RMSX_REF=v0.2.3 \
  -t rmsx-galaxy:0.2.3 \
  packaging/rmsx-galaxy
```

Smoke-check the executable:

```bash
docker run --rm rmsx-galaxy:0.1.0 rmsx --help
```

Run the RMSX compute smoke fixture through the image:

```bash
mkdir -p /private/tmp/rmsx_container_smoke
docker run --rm \
  -v "/Users/finn/Documents/Flipbook Integration/tools/rmsx/test-data:/data:ro" \
  -v /private/tmp/rmsx_container_smoke:/out \
  rmsx-galaxy:0.1.0 \
  rmsx /data/1UBQ.pdb /data/mon_sys.dcd \
    --output_dir /out \
    --num_slices 3 \
    --chain 7 \
    --quiet \
    --no-plot \
    --overwrite
```

This local image build and smoke test passed on 2026-06-03. The compute smoke test produced `rmsx_mon_sys_0.015_ns.csv`, `rmsd.csv`, `rmsf.csv`, `masked_residues.csv`, and three `slice_*_first_frame.pdb` files under `/private/tmp/rmsx_container_smoke/chain_7_rmsx/`. The Galaxy wrapper keeps this compute step deterministic, then calls the packaged RMSX R plotting script separately to emit explicit heatmap and triple-plot PNG datasets.

For shareable Planemo/Galaxy testing, `tools/rmsx/macros.xml` points at the registry image tag:

```xml
<container type="docker">ghcr.io/antuneslab/rmsx-galaxy:0.1.0</container>
```

Use the project job config in `config/planemo_docker_job_conf.yml` when running Docker-backed Planemo tests. The wrapper emits the Molstar manifest as the JSON-backed `rmsxmolstar` datatype using the tool-local `tools/rmsx/datatypes_conf.xml`; the native visualization plugin also accepts generic JSON manifests as a development fallback after validating the RMSX schema. `config/datatypes/datatypes_conf.xml` mirrors the dedicated datatype as a standalone local-Galaxy snippet, but merge it with Galaxy's stock datatype registry before using it as a full `datatypes_config_file` override. The job config sets `docker_volumes: $defaults` explicitly to avoid Planemo/Galaxy quoting problems with generated Docker volume strings:

```bash
env HOME="/Users/finn/Documents/Flipbook Integration/.planemo-home" \
  .venv-planemo/bin/planemo test \
    --install_galaxy \
    --docker \
    --docker_cmd /Applications/Docker.app/Contents/Resources/bin/docker \
    --job_config_file config/planemo_docker_job_conf.yml \
    --no_conda_auto_install \
    --no_conda_auto_init \
    --test_output tool_test_output.html \
    --test_output_json tool_test_output.json \
    --job_output_files planemo-test-output \
    --test_timeout 300 \
    tools/rmsx/rmsx.xml
```

The Docker-backed Planemo run resolves the explicit container requirement, launches Docker jobs, and currently covers the history-input path, bundled-example path, static R plot generation, and an expected preflight failure for a missing chain/segment selector.

If the image is pushed to a registry, replace the local image tag with a registry-qualified explicit Galaxy container requirement. The default publication target for this scaffold is:

```xml
<container type="docker">ghcr.io/antuneslab/rmsx-galaxy:0.1.0</container>
```

Galaxy supports explicit Docker and Singularity container requirements inside the tool `<requirements>` block. Keep the package requirements in place as documentation for the eventual Conda path, but use the explicit container while RMSX is not available as a Conda package.

The native Molstar visualization has a separate packaging path from the runtime
container. For local Planemo demos, build a merged datatype registry, register
that registry plus the visualization plugin directory, and then mirror the
static assets after Galaxy starts:

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

python3 scripts/sync_visualization_static.py
```

That mirrors the plugin into Planemo's temporary Galaxy
`static/plugins/visualizations` tree so the native `Visualize` iframe can load
the bundled `molstar@5.4.2` assets. For Galaxy sharing, package or install the
visualization directly under Galaxy's static visualization plugin path instead
of relying on the Planemo sync helper.

## Later Conda/Bioconda Route

The durable Galaxy ecosystem route is still a real package:

1. Add a Conda recipe for RMSX that installs the Python package and declares `MDAnalysis`, `pandas`, `r-base`, and the R plotting packages.
2. Confirm the RMSX CLI works without runtime package installation or writable package-library assumptions.
3. Publish to Bioconda or another Galaxy-visible channel.
4. Move the exact package versions from this local scaffold into the Conda recipe and `tools/rmsx/macros.xml`.
5. Let Galaxy resolve the wrapper through Conda or mulled containers rather than this source-install Dockerfile.

## Open Packaging Checks

- Decide which RMSX tag or commit is the first Galaxy-supported runtime target.
- Publish the image to a registry and replace the local image tag in `tools/rmsx/macros.xml`.
- Add a CI build for the runtime image once the package/ref target is stable.
