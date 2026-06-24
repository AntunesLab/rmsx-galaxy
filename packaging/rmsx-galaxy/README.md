# RMSX Galaxy Runtime Packaging

This directory contains the container scaffold used by the Galaxy wrapper while RMSX is not yet available as a Galaxy-ready Conda/Bioconda dependency.

The active wrapper references:

```xml
<container type="docker">ghcr.io/antuneslab/rmsx-galaxy:0.2.3-galaxy0</container>
```

For collaborator testing, the image does not need to be public yet. Build the same tag locally from the repository root:

```bash
scripts/build_container.sh
```

That creates both tags:

```text
ghcr.io/antuneslab/rmsx-galaxy:0.2.3-galaxy0
rmsx-galaxy:0.2.3-galaxy0
```

Planemo/Galaxy can then satisfy the explicit container requirement from the local Docker image cache.

## Manual Docker Commands

The helper script is preferred, but the equivalent manual build is:

```bash
docker build \
  -t ghcr.io/antuneslab/rmsx-galaxy:0.2.3-galaxy0 \
  -t rmsx-galaxy:0.2.3-galaxy0 \
  packaging/rmsx-galaxy
```

The Dockerfile pins upstream RMSX with `RMSX_REF=v0.2.3`. Override that build
argument only when intentionally testing another upstream release.

Smoke-check the executable:

```bash
docker run --rm ghcr.io/antuneslab/rmsx-galaxy:0.2.3-galaxy0 rmsx --help
```

Run the bundled compute fixture:

```bash
mkdir -p /tmp/rmsx_container_smoke
docker run --rm \
  -v "$PWD/tools/rmsx/test-data:/data:ro" \
  -v /tmp/rmsx_container_smoke:/out \
  ghcr.io/antuneslab/rmsx-galaxy:0.2.3-galaxy0 \
  rmsx /data/1UBQ.pdb /data/mon_sys.dcd \
    --output_dir /out \
    --num_slices 3 \
    --chain 7 \
    --quiet \
    --no-plot \
    --overwrite
```

## Planemo Test Path

From the repository root:

```bash
scripts/run_planemo_tests.sh
```

To rebuild the container first:

```bash
scripts/run_planemo_tests.sh --build
```

The Docker-backed Planemo tests cover the history-input path, bundled-example path, static R plot generation, native Molstar manifest generation, and an expected preflight failure for a missing chain/segment selector.

## Native Visualization Demo Path

From the repository root:

```bash
scripts/serve_galaxy_demo.sh
```

The serve helper builds the merged datatype registry, starts Planemo/Galaxy with the local visualization plugin directory, and mirrors the plugin static assets into Planemo's temporary Galaxy checkout once Galaxy starts.

## Publishing The Image

When the team is ready for Galaxy administrators to use the wrapper without building locally:

```bash
docker push ghcr.io/antuneslab/rmsx-galaxy:0.2.3-galaxy0
```

Only someone with `antuneslab` GHCR package permissions can publish this tag.

## Later Conda/Bioconda Route

The durable Galaxy ecosystem route is still a real package:

1. Add a Conda recipe for RMSX that installs the Python package and declares `MDAnalysis`, `pandas`, `plotly`, `r-base`, and the R plotting packages.
2. Confirm the RMSX CLI works without runtime package installation or writable package-library assumptions.
3. Publish to Bioconda or another Galaxy-visible channel.
4. Move exact package versions from this scaffold into the Conda recipe and `tools/rmsx/macros.xml`.
5. Let Galaxy resolve the wrapper through Conda or mulled containers rather than this source-install Dockerfile.
