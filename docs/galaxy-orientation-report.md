# Galaxy Orientation Report for RMSX/Flipbook

Purpose: orient the next RMSX/Flipbook integration phase around Galaxy's tool model, existing computational chemistry patterns, and the least-surprising route from a local analysis workflow to a reusable Galaxy tool.

This report is a working orientation, not a final implementation specification. It should be updated after direct inspection of the RMSX and Flipbook repositories.

## Source Snapshot

Research date: 2026-06-03.

Primary Galaxy sources:

- Galaxy tool XML schema: <https://docs.galaxyproject.org/en/latest/dev/schema.html>
- Galaxy datatypes guide: <https://docs.galaxyproject.org/en/latest/dev/data_types.html>
- Galaxy dataset collections tutorial: <https://galaxyproject.org/tutorials/collections/>
- GTN history, datasets, and collections FAQ: <https://training.galaxyproject.org/training-material/faqs/galaxy/histories_datasets_vs_collections.html>
- Galaxy visualization framework: <https://galaxyproject.org/learn/visualization/>
- Galaxy InteractiveTools administration guide: <https://docs.galaxyproject.org/en/release_24.0/admin/special_topics/interactivetools.html>
- Planemo standalone tool tutorial: <https://planemo.readthedocs.io/en/stable/writing_standalone.html>
- Planemo Tool Shed publishing guide: <https://planemo.readthedocs.io/en/master/publishing.html>
- Galaxy IUC tool XML best practices: <https://galaxy-iuc-standards.readthedocs.io/en/latest/best_practices/tool_xml.html>
- Galaxy Europe ChemicalToolbox index: <https://usegalaxy-eu.github.io/index-cheminformatics.html>
- Galaxy computational chemistry tools repository, inspected at commit `e9345f76e3f953eea14bad2287cbc5a9c1ff882e`: <https://github.com/galaxycomputationalchemistry/galaxy-tools-compchem/tree/e9345f76e3f953eea14bad2287cbc5a9c1ff882e>

Comparable GTN workflow and tool pages:

- MDAnalysis analysis tutorial: <https://training.galaxyproject.org/training-material/topics/computational-chemistry/tutorials/analysis-md-simulations/tutorial.html>
- HTMD/MDAnalysis/Bio3D analysis tutorial: <https://training.galaxyproject.org/training-material/topics/computational-chemistry/tutorials/htmd-analysis/tutorial.html>
- Simple MD analysis workflow: <https://training.galaxyproject.org/training-material/topics/computational-chemistry/tutorials/analysis-md-simulations/workflows/main_workflow.html>
- Advanced MDAnalysis workflow: <https://training.galaxyproject.org/training-material/topics/computational-chemistry/tutorials/analysis-md-simulations/workflows/advanced_workflow.html>
- Bio3D PCA visualization tool page: <https://training.galaxyproject.org/training-material/by-tool/chemteam/bio3d_pca_visualize/bio3d_pca_visualize.html>
- Bio3D RMSD tool page: <https://training.galaxyproject.org/training-material/by-tool/chemteam/bio3d_rmsd/bio3d_rmsd.html>
- Tool Shed MDAnalysis extract RMSD entry: <https://toolshed.g2.bx.psu.edu/repository/view_repository?changeset_revision=589f8ef21e58&id=abf67e41c09c8170>

## Executive Summary

Galaxy already has a strong computational chemistry ecosystem for molecular dynamics setup, conversion, slicing, analysis, plotting, and trajectory-derived summaries. The closest conceptual neighbors to RMSX/Flipbook are the Bio3D and MDAnalysis wrappers that accept a topology/structure file plus a trajectory, expose atom-selection controls, emit tabular analysis data, and often emit plots or report artifacts.

The most conservative first integration route is a standard Galaxy tool wrapper around a noninteractive RMSX command-line workflow. That route should produce typed, inspectable datasets first: raw RMSX metrics, optional plots, logs, and any generated structural or trajectory artifacts. Flipbook-style visualization should then be layered on as a second route, either as a static/self-contained HTML report, a Galaxy visualization or Charts plugin, or a full InteractiveTool if live server behavior is required.

Do not start with a full InteractiveTool unless the inspected Flipbook repository proves that interactivity is the core deliverable and cannot be represented as datasets plus a viewer. InteractiveTools are powerful, but they add deployment and administrator requirements such as container networking, entry points, proxy routing, and often wildcard-subdomain setup.

## Galaxy Mental Model

Galaxy tools are declarative wrappers around computational programs. A tool XML file describes the user interface, input parameters, command invocation, dependencies, expected outputs, tests, help text, and citations. Galaxy handles job staging, provenance, histories, workflows, and dataset typing around that wrapper.

The practical model for RMSX/Flipbook is:

- A user has datasets in a Galaxy history.
- A tool consumes those datasets and parameters.
- The tool command runs in an isolated job working directory.
- The command reads Galaxy-provided input paths and writes declared output paths or files in the job working directory.
- Galaxy records the outputs as new history datasets, with datatypes, metadata, provenance, and workflow compatibility.

The IUC best-practice guidance is especially relevant for RMSX: tools may read input datasets, but should write only declared outputs and files in the current working directory. Any index, cache, temporary trajectory, extracted frame set, or derived support file should be created in the job working directory or an explicit output directory, not beside inputs.

## Tool Wrapper Anatomy

A conventional Galaxy tool wrapper has these pieces:

- `<tool>` root: stable `id`, human-readable `name`, wrapper `version`, and a `profile` that controls Galaxy behavior expectations.
- `<macros>`: shared tokens and reusable XML fragments for requirements, inputs, citations, tests, or command snippets.
- `<requirements>`: Conda packages and versions, or container expectations.
- `<command>`: a Cheetah-templated command line that turns Galaxy inputs and parameters into a noninteractive invocation.
- `<configfiles>`: generated helper files when the underlying program expects config, script, or list-file inputs.
- `<inputs>`: dataset, collection, select, conditional, repeat, boolean, integer, float, and text parameters.
- `<outputs>`: declared datasets, conditional outputs, output collections, discovered outputs, and format propagation.
- `<tests>`: small deterministic examples with expected content, sizes, image checks, collection structure, and failure behavior where useful.
- `<help>`: user-facing operational guidance, not a substitute for tests.
- `<citations>`: papers, DOIs, or BibTeX records for RMSX, Flipbook, and underlying libraries.

The schema supports normal tools and interactive tools. A normal tool is the likely RMSX starting point. An interactive tool uses `tool_type="interactive"` and `entry_points` to expose a running service, which is a better fit only if Flipbook requires a live web application.

## Histories, Datasets, Datatypes, and Collections

Galaxy histories are provenance-aware analysis ledgers. Datasets are typed files inside histories. Galaxy datatypes are usually keyed by extension and backed by datatype classes. Collections group related datasets so workflows can operate on many files without turning the history into an unmanageable list.

Important implications for RMSX/Flipbook:

- Prefer existing molecular formats whenever possible: PDB, GRO, DCD, XTC, TRR, tabular, JSON, PNG, HDF5, HTML.
- Avoid custom datatypes for the first wrapper unless RMSX produces a file format that Galaxy cannot reasonably represent with existing types.
- If publishing to the Tool Shed and a custom datatype is unavoidable, plan to upstream or separately maintain the datatype definition.
- Use collections when processing multiple structures, multiple trajectories, replicate simulations, or frame sets.
- If RMSX/Flipbook produces a multi-file report bundle, evaluate Galaxy composite datatypes or a declared HTML/report dataset with associated files.
- Keep raw machine-readable outputs separate from human-readable visual reports so downstream workflows can reuse the data.

## Dependencies, Containers, Tool Shed, and Planemo

Galaxy wrappers usually express runtime dependencies with Conda packages in `<requirements>`. Containers can also be used, and InteractiveTools rely heavily on containerized services. Planemo is the standard development companion for linting, testing, serving, and publishing Galaxy tools.

Expected RMSX/Flipbook development loop:

1. Confirm a deterministic noninteractive CLI path for RMSX.
2. Create a minimal wrapper with explicit requirements and tiny test data.
3. Run `planemo lint` and `planemo test`.
4. Add workflow-shaped tests as the wrapper becomes more stable.
5. Use `planemo serve` for local manual checks.
6. Prepare `.shed.yml` and Tool Shed metadata only after the wrapper API stabilizes.

The Tool Shed is the distribution path for Galaxy tools, dependency definitions, and workflows. The main Tool Shed is for production-ready releases; the test Tool Shed is for iteration.

## Visualization Routes

Galaxy offers several visualization patterns. RMSX/Flipbook should choose among them based on what the inspected code already does and what users need to preserve in workflow outputs.

### Static Output Route

This is the recommended first phase. The wrapper emits tabular metrics, optional JSON/HDF5 data, static PNG/SVG plots, logs, and any structure/trajectory artifacts. It is easiest to test, easiest to publish, and most compatible with Galaxy workflows.

This route matches existing Bio3D and MDAnalysis patterns.

### Self-Contained HTML Report Route

The wrapper emits an HTML dataset, ideally self-contained or with a controlled set of associated files. This can work well for Flipbook summaries, but Galaxy instances may restrict inline HTML display unless administrators configure allowlists. The MDAnalysis Ramachandran wrapper is a useful precedent because it produces raw HDF5 data, PNG plots, and an HTML summary rather than making the HTML the only output.

### Galaxy Charts or Visualization Plugin Route

Galaxy Charts is the primary in-browser visualization framework. It supports standard charts and domain-specific viewers, including molecular, protein, network, and tree viewers. A custom plugin can render RMSX output datasets directly in the Galaxy UI without an external server.

This is a strong candidate if Flipbook can be represented as client-side rendering over one or more Galaxy datasets.

### InteractiveTool Route

InteractiveTools expose containerized web applications from Galaxy jobs. They can support R Shiny apps, VNC applications, and similar browser-based services. A Flipbook web app could fit here if it needs a live backend or complex browser-server interaction.

Costs to account for:

- Galaxy administrator enablement.
- Container image maintenance.
- Port and URL entry point definitions.
- Proxy and routing configuration.
- More involved security and reproducibility review.
- Harder automated testing than a standard wrapper.

## Comparable Ecosystem Concepts

The Galaxy Europe ChemicalToolbox and the Galaxy Computational Chemistry repository already include roughly the same families of operations RMSX/Flipbook will need to coexist with:

- Molecular dynamics conversion and slicing through MDTraj.
- GROMACS simulation and analysis wrappers.
- Bio3D trajectory analyses, including RMSD, RMSF, PCA, and PCA visualization trajectories.
- MDAnalysis wrappers for distances, dihedrals, radial distribution functions, Ramachandran analysis, and RMSD matrix extraction.
- VMD-based hydrogen bond analysis.

These tools establish user expectations for:

- Structure plus trajectory inputs.
- Selection-language parameters.
- Raw tabular outputs paired with plots.
- Optional logs.
- Small deterministic test fixtures.
- Workflows that chain conversion, analysis, and visualization.

## RMSX/Flipbook Repository Inspection Checklist

Use this checklist before writing wrappers.

### RMSX Command Surface

- Identify the primary executable entry point.
- Confirm whether it can run headless and noninteractively.
- Capture required inputs, optional inputs, and supported molecular formats.
- Determine whether structure and trajectory inputs are paired, many-to-one, many-to-many, or collection-friendly.
- Identify atom-selection syntax and whether it maps to Bio3D, MDAnalysis, MDTraj, VMD, or a custom language.
- Determine whether the program writes only to explicit output paths or assumes local working-directory names.
- Record expected runtime, memory use, and parallelism controls.
- Check exit codes and error messages for Galaxy-compatible failure detection.

### RMSX Output Surface

- List all outputs and their formats.
- Separate machine-readable outputs from human-readable reports.
- Identify generated structures, trajectories, frame series, or coordinate bundles.
- Identify logs, diagnostics, warnings, and provenance metadata.
- Decide which outputs should be required, optional, conditional, or discovered dynamically.
- Determine whether any output requires a custom datatype.

### Flipbook Visualization Surface

- Identify whether Flipbook is a static renderer, browser-only viewer, local GUI, or web service.
- Determine whether it can consume Galaxy-friendly datasets directly.
- Determine whether it can render from JSON/HDF5/tabular metrics plus structure/trajectory files.
- Check whether it requires external assets, local absolute paths, server state, or browser storage.
- Determine whether it can produce a self-contained HTML report.
- Identify licensing and redistribution constraints for bundled assets or viewers.

### Packaging Surface

- Identify language runtimes: Python, R, JavaScript/Node, compiled binaries, shell, Tcl/VMD, or mixed.
- Check existing package manifests: `pyproject.toml`, `setup.py`, `environment.yml`, `renv.lock`, `package.json`, Dockerfile, Conda recipe.
- Confirm versioning strategy.
- Confirm license compatibility with Galaxy Tool Shed distribution.
- Check whether dependencies already exist in Bioconda, conda-forge, CRAN, PyPI, npm, or containers.
- Identify test data small enough for a Galaxy wrapper repository.

## Candidate Integration Routes

### Route A: Standard RMSX Analysis Tool

This is the recommended first deliverable.

Inputs:

- Structure dataset, likely PDB or GRO.
- Trajectory dataset, likely DCD, XTC, TRR, or another supported trajectory type.
- Selection parameters.
- RMSX-specific numeric and mode parameters.

Outputs:

- Tabular RMSX metrics.
- Optional JSON/HDF5 data for downstream visualization.
- Static plot images.
- Log or diagnostics dataset.
- Optional generated structure or trajectory artifact.

Advantages:

- Fits Galaxy's normal tool model.
- Straightforward Planemo testing.
- Workflow-friendly.
- Similar to existing Bio3D and MDAnalysis tools.

### Route B: RMSX Analysis Plus Static Flipbook Report

This extends Route A by adding a self-contained HTML or report output. The report should not be the only output. Raw data should remain available for reuse.

Advantages:

- Gives users a visual artifact early.
- Still mostly standard-wrapper territory.
- Avoids live-service deployment complexity.

Risks:

- HTML display can be restricted by Galaxy instance configuration.
- Associated assets must be handled carefully.
- Large embedded assets can make histories heavy.

### Route C: Galaxy Visualization or Charts Plugin

This makes Flipbook a viewer over RMSX outputs. It is a good second or third phase if the report data model is stable.

Advantages:

- Feels native inside Galaxy.
- Avoids running a live per-job server.
- Can reuse Galaxy datasets as the source of truth.

Risks:

- Requires frontend plugin work.
- Requires a stable data contract.
- May need instance-level installation.

### Route D: Flipbook InteractiveTool

This runs Flipbook as a containerized web app launched from Galaxy.

Advantages:

- Best fit for a rich live application.
- Can preserve existing web-app behavior if Flipbook already runs as a service.

Risks:

- Highest administrative and deployment burden.
- Harder to test and publish.
- Less portable across Galaxy instances than a normal wrapper.

## Staged Implementation Plan

### Stage 1: Repository Inspection

- Inspect RMSX and Flipbook source trees.
- Record command entry points, dependencies, formats, outputs, and licenses.
- Run existing tests or minimal sample commands if available.
- Identify the smallest scientifically meaningful example dataset.

### Stage 2: Wrapper Contract

- Define v1 Galaxy inputs and outputs.
- Decide whether v1 supports one structure/trajectory pair or collections.
- Decide whether v1 exposes a compact parameter set or advanced mode.
- Choose output datatypes and naming.
- Draft help text and citations.

### Stage 3: Minimal Standard Wrapper

- Create one standard Galaxy XML wrapper.
- Add Conda/container requirements.
- Add tiny test data.
- Add deterministic Planemo tests.
- Emit raw data, plots, and logs.

### Stage 4: Workflow and Corpus Alignment

- Build a small Galaxy workflow connecting conversion or slicing tools to RMSX.
- Compare behavior against Bio3D RMSD/PCA and MDAnalysis distance/Ramachandran expectations.
- Add tests for common format combinations.

### Stage 5: Flipbook Output Route

- Prototype a static HTML/report output if feasible.
- Preserve raw datasets as primary outputs.
- Confirm whether Galaxy display restrictions affect the report.
- Decide whether a Charts plugin or InteractiveTool is justified.

### Stage 6: Publication Hardening

- Run Planemo lint and tests.
- Add citations and complete help.
- Review IUC best-practice alignment.
- Prepare Tool Shed metadata.
- Consider upstreaming or documenting any custom datatype.

## Key Unknowns to Resolve Next

- What exactly is RMSX's scientific output, and which outputs are required for downstream use?
- Does RMSX already have a stable CLI, or does it need a thin command-line adapter before Galaxy wrapping?
- Which molecular file formats are required for real users: PDB/DCD, GRO/XTC, TRR, NetCDF, mmCIF, or others?
- Are structure and trajectory inputs one-to-one, one-to-many, or collection-oriented?
- Does Flipbook render from static files, or does it require a live server?
- Can Flipbook produce a self-contained HTML artifact?
- Does either repository require dependencies that are not available through Conda or containers?
- Are there licensing constraints around redistribution in the Tool Shed or containers?
- What small public sample dataset can be included in tests?
- Is the intended first Galaxy deployment local/private, a public Galaxy instance, or the main Tool Shed?
