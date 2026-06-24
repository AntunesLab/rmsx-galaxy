Flipbook trajectory analysis
============================

RMSX partitions a molecular dynamics trajectory into time slices and computes
per-residue RMSF within each slice. This Galaxy wrapper exposes the RMSX compute
path and returns workflow-friendly Galaxy datasets: RMSX, RMSD, and RMSF CSV
tables; mask metadata; a list collection of PDB slice snapshots; a standalone
RMSX heatmap PNG; the original RMSD/RMSX/RMSF triple plot PNG; an execution log;
and a schema-validated JSON manifest for the Molstar Flipbook prototype viewer.

Scope
-----

The conservative Tool Shed candidate is a Flipbook Galaxy wrapper backed by
RMSX. It does not launch Flipbook, ChimeraX, VMD, an external viewer server, or
a trusted HTML report. Those richer viewer paths remain in the companion
repository for cofest development.

The first reviewable wrapper path accepts PDB topology/structure input and DCD
or XTC trajectory input. RMSX and MDAnalysis can support additional molecular
dynamics formats, but broader Galaxy datatype coverage should be added
deliberately with tests for each supported pair.

Viewer manifest
---------------

The Molstar Flipbook manifest is emitted as standard Galaxy JSON using schema
version ``flipbook-molstar-viewer/v1``. The companion repository also contains a
native Galaxy visualization plugin and a project-local ``flipbookmolstar``
datatype, but those are not assumed for the conservative IUC wrapper path. The
manifest is still useful as structured data and can be rendered by the prototype
viewer when that plugin is installed.

Dependency status
-----------------

The wrapper currently declares RMSX, MDAnalysis, Python table dependencies,
Plotly, the rich-display package imported by upstream RMSX at startup,
``r-base``, and the R plotting packages required by the original RMSX plot
script. A temporary container scaffold is provided at
``ghcr.io/antuneslab/flipbook-galaxy:0.2.3-galaxy0`` and pins upstream RMSX
``v0.2.3``. That tag currently installs Python package metadata as
``rmsx==0.1.0``, so the wrapper requirement and version command remain honest
about the executable package version while this upstream metadata mismatch is
tracked as a pre-IUC packaging issue. The intended durable route for IUC is a
Conda/Bioconda RMSX package or a Galaxy-visible mulled container generated from
Conda dependencies.

The Galaxy runtime path must not install R packages at job runtime. The
container and future Conda recipe should preinstall the R stack and tests should
exercise plotting without network access.

Known pre-IUC blockers
----------------------

* The bundled XTC fixture preserves all 316 frames from the original demo
  trajectory while staying below the tools-iuc 1 MB file-size check. Its
  original source, redistribution status, and regeneration command should still
  be recorded before an IUC PR.
* The vendored Molstar bundle belongs to the companion visualization prototype,
  not the minimal IUC tool wrapper.
* A bio.tools entry or equivalent EDAM/xref strategy should be settled before
  submission.
* Upstream RMSX release metadata should be reconciled so the tag, package
  version, and Galaxy wrapper version tell the same story.
* Test-data provenance and the full transitive dependency license inventory
  should be kept with the review packet.

License
-------

This wrapper repository is MIT licensed. Upstream RMSX is MIT licensed. Molstar
is MIT licensed. MDAnalysis uses LGPL-compatible licensing. The final IUC review
packet should include transitive license checks for Conda, pip, R, and vendored
JavaScript assets.
