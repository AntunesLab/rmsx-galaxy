# Flipbook Galaxy IUC Readiness Audit

This document is the working checklist for preparing RMSX/Flipbook for scrutiny
by Galaxy and IUC reviewers.

## Current Review Posture

The first IUC-facing target should be the conservative Flipbook Galaxy wrapper in
`tools/flipbook`, not the whole cofest repository. The wrapper should be useful on
its own through standard Galaxy outputs: CSV tables, PNG plots, PDB slice
collections, logs, and a JSON Molstar manifest.

The native Molstar visualization, custom `flipbookmolstar` datatype, and standalone
HTML experiments remain companion/prototype assets until Galaxy/IUC agree on the
appropriate visualization and datatype packaging route.

## IUC Rules And Patterns Checked

- tools-iuc accepts wrappers for OSI-licensed tools, visualization plugins,
  updates, tests, and documentation, but expects functional tests and passing
  Planemo lint.
- tools-iuc discourages duplicate wrappers, wrappers without tests, and new
  datatypes in tool repositories when the datatype belongs in Galaxy core.
- IUC best practices call for recent Galaxy profiles, version macros, meaningful
  tool IDs, strict parameters, clear help, citations, test data, and Tool Shed
  metadata.
- The current tools-iuc CI checks Python style, R style where relevant,
  Planemo lint/test behavior, and files larger than 1 MB.

## Findings

- No RMSX or Molstar wrapper precedent was found in tools-iuc during the current
  audit. The closest patterns are conventional plotting wrappers and the limited
  `visualizations/` area, such as `biojs-msa`.
- The original DCD fixture was too large for a direct IUC PR; the current
  `tools/flipbook/test-data/mon_sys.xtc` fixture preserves all 316 frames as
  precision-2 XTC while staying below 1 MB.
  The fixture README now records the paper-backed 1UBQ simulation context,
  source archive URL, archive checksum, extracted source-file checksums, and
  regeneration command.
- The TCBG copyright statement permits educational reproduction and distribution
  with credit, but it is not a standard open-data license. Confirm with IUC that
  this is acceptable for bundled test data, or replace the trajectory fixture
  with one carrying clearer open-data terms.
- The vendored Molstar JavaScript bundle is too large for a minimal IUC tool PR
  and belongs to the companion visualization discussion.
- The wrapper now emits the Molstar manifest as standard JSON for the
  conservative Tool Shed path.
- The project-local `flipbookmolstar` datatype remains useful for local demos but
  should not be assumed in an IUC tool PR without prior guidance.
- The container scaffold now pins upstream RMSX `v0.2.3` instead of building
  from `main`.
- Building that tag currently installs Python package metadata as `rmsx==0.1.0`.
  The wrapper keeps the executable package version honest and tracks the
  tag/package-version mismatch as a pre-IUC packaging issue.
- Upstream RMSX imports a rich-display helper at module import time. The
  container declares that dependency for now, but the cleaner IUC path is to
  make the import optional upstream.
- The pinned upstream `plot_rmsx.R` contains an `install.packages()` fallback
  when R packages are missing. The Galaxy-side helper now preflights the required
  R packages and fails before calling the upstream script if any are absent, so
  Galaxy jobs use declared Conda/container dependencies instead of runtime
  package installation.

## Dependency And License Notes

- RMSX: MIT license upstream.
- Molstar: MIT license; currently vendored only for the prototype visualization
  path.
- MDAnalysis: LGPL-compatible licensing.
- R plotting stack: viridis/tidyverse/gridExtra packages are open-source, but
  the transitive dependency inventory still needs a generated SBOM.
- ChimeraX and VMD are optional upstream RMSX/Flipbook workflows and are not
  Galaxy runtime dependencies for this wrapper.

## Before Opening An IUC PR

- Confirm IUC acceptance of the TCBG educational-use redistribution statement
  for the compressed XTC fixture, or replace the fixture.
- Reconcile upstream RMSX release metadata so the tag, Python package version,
  Conda package version, and Galaxy wrapper version are consistent.
- Keep vendored Molstar assets out of the minimal IUC tool PR.
- Add or confirm a bio.tools entry and EDAM/xref strategy for RMSX.
- Run `planemo lint --fail_level warn`, `planemo shed_lint`, and
  `planemo test --install_galaxy`.
- Run Python style checks and any R style checks required by the final wrapper.
- Verify that the Galaxy-side R package preflight catches missing R packages
  before the packaged upstream `plot_rmsx.R` can reach its `install.packages()`
  fallback, and that static R plotting works without network access in the final
  runtime.
- Produce a dependency/license inventory from the exact Conda/container runtime.
- Include screenshots and a short known-limitations note in the cofest review
  packet.
