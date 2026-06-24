# Comparable Galaxy Tools Corpus for RMSX/Flipbook

Purpose: collect existing Galaxy computational chemistry tools that solve adjacent problems to RMSX/Flipbook, and extract implementation patterns worth copying or avoiding.

This is a source-guided corpus for design work. It is not a wrapper implementation.

## Source Snapshot

Research date: 2026-06-03.

Primary repository inspected:

- Galaxy Computational Chemistry tools, commit `e9345f76e3f953eea14bad2287cbc5a9c1ff882e`: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/tree/e9345f76e3f953eea14bad2287cbc5a9c1ff882e>

Related public documentation:

- ChemicalToolbox index: <https://usegalaxy-eu.github.io/index-cheminformatics.html>
- MDAnalysis analysis tutorial: <https://training.galaxyproject.org/training-material/topics/computational-chemistry/tutorials/analysis-md-simulations/tutorial.html>
- HTMD/MDAnalysis/Bio3D tutorial: <https://training.galaxyproject.org/training-material/topics/computational-chemistry/tutorials/htmd-analysis/tutorial.html>
- Bio3D PCA visualization GTN page: <https://training.galaxyproject.org/training-material/by-tool/chemteam/bio3d_pca_visualize/bio3d_pca_visualize.html>
- Bio3D RMSD GTN page: <https://training.galaxyproject.org/training-material/by-tool/chemteam/bio3d_rmsd/bio3d_rmsd.html>
- MDAnalysis extract RMSD Tool Shed page: <https://toolshed.g2.bx.psu.edu/repository/view_repository?changeset_revision=589f8ef21e58&id=abf67e41c09c8170>
- Galaxy visualization framework: <https://galaxyproject.org/learn/visualization/>
- Galaxy InteractiveTools guide: <https://docs.galaxyproject.org/en/release_24.0/admin/special_topics/interactivetools.html>

## Why These Tools Are Comparable

RMSX/Flipbook appears to sit near molecular dynamics analysis and visualization. The comparable Galaxy tools already handle the hard edges that RMSX/Flipbook will likely face:

- Paired structure and trajectory inputs.
- Multiple molecular file formats.
- Atom and residue selection.
- Derived coordinate transformations.
- Raw numeric outputs plus visual plots.
- Optional HTML reports.
- Multi-file and collection-oriented workflows.
- Scientific dependencies such as Bio3D, MDAnalysis, MDTraj, GROMACS, and VMD.

## High-Priority Case Studies

### Bio3D RMSD

Source files:

- Wrapper: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/bio3d/rmsd.xml>
- Script: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/bio3d/rmsd.R>
- Shared macros: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/bio3d/macros.xml>

What it does:

- Accepts a DCD trajectory and PDB structure.
- Uses Bio3D atom selection.
- Aligns trajectory coordinates before RMSD calculation.
- Emits raw tabular RMSD data, an RMSD plot, and a histogram plot.
- Uses a shared Bio3D requirement macro for `r-bio3d`.

Patterns to copy:

- Keep a simple pair of primary inputs for v1.
- Expose common selection presets while still allowing specific selection modes.
- Pair machine-readable tabular output with visual outputs.
- Put shared dependency, input, citation, and test fragments in macros once multiple related tools exist.

RMSX relevance:

This is the closest first-pass model if RMSX consumes a structure plus trajectory and emits one or more metrics over frames.

### Bio3D PCA and PCA Visualization

Source files:

- PCA wrapper: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/bio3d/pca.xml>
- PCA script: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/bio3d/pca.R>
- PCA visualization wrapper: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/bio3d/visualize_pc.xml>
- PCA visualization script: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/bio3d/visualize_pc.R>

What it does:

- Performs PCA over selected atoms from a DCD/PDB pair.
- Emits tabular PCA data and several plot images.
- Provides a separate tool to generate a PDB trajectory for a selected principal component.

Patterns to copy:

- Separate analysis from visualization-oriented derived artifacts.
- Let downstream workflow steps consume raw analysis outputs.
- Generate structural/trajectory artifacts as normal Galaxy datasets when possible.

RMSX relevance:

If Flipbook needs derived structural frames or motion paths, the PCA visualization split is a strong precedent: RMSX can produce primary metrics first, and a second tool can produce Flipbook-ready structures, trajectories, or reports.

### MDAnalysis Distance

Source files:

- Wrapper: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/mdanalysis/distance.xml>
- Single-distance script: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/mdanalysis/distance_single.py>
- Shared macros: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/mdanalysis/macros.xml>

What it does:

- Accepts DCD/XTC trajectory input and PDB/GRO topology input.
- Supports one pairwise distance or multiple selections from list files.
- Uses Galaxy input extensions to select MDAnalysis topology and trajectory formats.
- Emits tabular output and, for single-distance mode, a plot image.
- Tests both PDB/DCD and GRO/XTC combinations.

Patterns to copy:

- Let Galaxy datatypes drive file-format handling where possible.
- Add tests for each important structure/trajectory format combination.
- Use conditional outputs when plots only make sense for certain parameter modes.
- Keep plotting optional or mode-specific.

RMSX relevance:

This is a good model if RMSX should support more than PDB/DCD in v1.

### MDAnalysis Extract RMSD Matrix

Source files:

- Wrapper: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/mdanalysis/extract_rmsd.xml>
- Script: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/mdanalysis/extract_rmsd.py>

What it does:

- Accepts collections of structures and trajectories.
- Uses generated list files to pass collection members to Python.
- Extracts coordinates over a start/end/step range.
- Emits a JSON matrix result.

Patterns to copy:

- Use collections for multi-simulation or replicate workflows.
- Use generated list files when a script needs a list of paths.
- Emit JSON when the downstream consumer is likely a visualization or structured-analysis step.

Cautions:

- Paired collections need strict order and length validation.
- Help text must stay aligned with behavior as scientific assumptions change.

RMSX relevance:

This is the most relevant pattern if RMSX compares multiple simulations, multiple conformers, or multiple trajectories as a group.

### MDAnalysis Ramachandran Auto Protein

Source files:

- Wrapper: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/mdanalysis/ramachandran_auto_protein.xml>
- Script: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/mdanalysis/ramachandran_auto_protein.py>
- HTML template: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/mdanalysis/ramachandran_auto_protein_html.j2>

What it does:

- Accepts structure plus trajectory input.
- Exposes residue and grouping parameters.
- Writes raw HDF5 data, PNG plots, and an HTML summary.
- Embeds plot images into the HTML report.

Patterns to copy:

- Treat HTML as a companion report, not the sole scientific output.
- Preserve raw data in a reusable format.
- Add tests that assert both data outputs and report content.
- Validate selections and fail clearly when they produce no atoms.

RMSX relevance:

This is the best immediate precedent for a static Flipbook report route.

### MDTraj Converter and Slicer

Source files:

- Converter wrapper: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/mdfileconverter/md_converter.xml>
- Slicer wrapper: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/mdslicer/md_slicer.xml>

What they do:

- Convert between trajectory formats.
- Slice trajectory frame ranges using start, end, and stride.
- Propagate or change output formats according to user choice.
- Use small binary-output tests with size assertions.

Patterns to copy:

- Keep preprocessing as separate workflow steps when possible.
- Let existing conversion/slicing tools prepare RMSX inputs instead of building every transformation into RMSX.
- Use format propagation and explicit `change_format` logic for conversion outputs.

RMSX relevance:

These tools may already solve input preparation needs around trajectory format conversion and frame trimming.

### GROMACS Analysis Wrappers

Source files:

- Shared macros: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/gromacs/macros.xml>
- RMSD wrapper: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/gromacs/rmsd.xml>
- RMSF wrapper: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/gromacs/rmsf.xml>
- Trajectory manipulation wrapper: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/gromacs/trj.xml>
- Simulation wrapper: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/gromacs/sim.xml>

What they do:

- Wrap GROMACS command-line tools for simulation and analysis.
- Use expected file names, symlinks, optional index files, and conditional outputs.
- Emit XVG data, logs, optional matrices, optional trajectory outputs, and discovered frame collections.
- Use resource controls such as `GALAXY_SLOTS` and optional GPU availability variables.

Patterns to copy:

- Preserve detailed logs for complex scientific jobs.
- Use optional outputs with clear filters.
- Use discovered datasets or collections when a command emits variable numbers of frame files.
- Use job resource variables only when RMSX can actually take advantage of them.

RMSX relevance:

GROMACS wrappers are useful models for complex output handling, but they are probably too broad as a v1 design target.

### VMD Hydrogen Bonds

Source files:

- Wrapper: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/vmd/hbonds/hbonds.xml>
- Tcl script: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/blob/e9345f76e3f953eea14bad2287cbc5a9c1ff882e/tools/vmd/hbonds/hbonds.tcl>

What it does:

- Wraps a GUI-capable molecular tool through text-mode execution.
- Uses generated Tcl configuration.
- Accepts atom-selection strings and geometry cutoffs.
- Emits multiple text outputs from the job working directory.

Patterns to copy:

- GUI-origin tools can still be wrapped if they have reliable noninteractive execution.
- Generated config files are cleaner than overlong shell commands.
- Explicitly declare every output Galaxy should collect.

RMSX relevance:

If Flipbook or RMSX originated as a local GUI workflow, this is the precedent for extracting a headless execution path.

## Visualization and Interactivity Comparables

### Galaxy Charts and Visualization Plugins

Galaxy's visualization framework supports browser-based plugins over Galaxy datasets. The framework already includes standard charts and specialized viewers, including molecular and protein-oriented viewers.

Use this route when Flipbook can be a client-side viewer over RMSX outputs.

Design implications:

- Stabilize the RMSX output data contract first.
- Prefer JSON, HDF5, tabular, PDB, and trajectory datasets that Galaxy can manage.
- Keep the visual layer separate from the compute layer.

### Galaxy InteractiveTools

InteractiveTools are declared with `tool_type="interactive"` and `entry_points` for exposed service URLs. They run container-backed applications as Galaxy jobs and can support R Shiny, VNC, and web-app workflows.

Use this route only when Flipbook needs a live application process.

Design implications:

- Plan for container image maintenance.
- Plan for instance-level admin configuration.
- Plan for proxy/routing constraints.
- Keep a standard Flipbook wrapper backed by RMSX available even if an InteractiveTool is later added.

## Patterns Worth Copying for RMSX/Flipbook

- Start with a normal tool wrapper and deterministic tests.
- Use Galaxy-native datatypes and avoid custom datatypes unless necessary.
- Emit raw data separately from plots and HTML reports.
- Put shared dependency, citation, input, and test fragments in macros once there is more than one wrapper.
- Support one simple structure/trajectory pair first, then add collections when the single-pair contract is stable.
- Use conditional parameters for advanced modes.
- Validate atom selections and input pairings before long computation begins.
- Keep conversion and slicing as separate workflow steps unless RMSX absolutely requires integrated preprocessing.
- Include small public test data and assertions on content, not only file existence.
- Provide citations for RMSX, Flipbook, and major runtime libraries.

## Patterns to Avoid

- Making an HTML report the only useful output.
- Building a live InteractiveTool before confirming that static datasets cannot satisfy the first use case.
- Introducing a custom Galaxy datatype for convenience rather than necessity.
- Letting help text drift away from actual behavior.
- Assuming paired collections are aligned without explicit validation.
- Writing generated files beside input datasets.
- Embedding every preprocessing operation inside the Flipbook wrapper.
- Treating large simulation wrappers as the v1 complexity target.

## Candidate Flipbook v1 Wrapper Sketch

This is not implementation code. It is a target shape to test against repository reality.

Inputs:

- Structure: PDB first, with GRO support if RMSX and tests support it.
- Trajectory: DCD first, with XTC/TRR support if dependencies support them cleanly.
- Selection preset and optional custom selection.
- RMSX-specific numeric parameters.
- Optional frame range or stride, unless delegated to MDTraj slicer.

Outputs:

- Primary RMSX table: tabular.
- Structured result: JSON or HDF5 if Flipbook needs richer data.
- Static summary plot: PNG or SVG.
- Optional generated structure or trajectory artifact.
- Tool log: text.
- Optional static Flipbook report: HTML, only after raw outputs are stable.

Tests:

- Minimal PDB plus compact XTC fixture.
- One default-mode test with exact or near-exact tabular assertions.
- One selection-mode test.
- One failure or empty-selection test if practical.
- HTML/report assertions only after the report route exists.

Likely staged tools:

1. `rmsx_analyze`: standard compute wrapper.
2. `rmsx_flipbook_prepare`: optional derived artifact/report generator.
3. `rmsx_flipbook_viewer`: optional Galaxy visualization plugin or InteractiveTool, only if justified.
