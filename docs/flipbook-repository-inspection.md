# RMSX/Flipbook Repository Inspection

Purpose: capture a code-level inspection of the RMSX/Flipbook repository and translate it into Galaxy integration decisions. This document is the next-phase companion to the Galaxy orientation report and comparable-tool corpus.

No implementation code was written for this phase.

## Source Snapshot

Inspection date: 2026-06-03.

Primary repository:

- Canonical repository: <https://github.com/AntunesLab/rmsx>
- Local checkout inspected: `/Users/finn/Documents/GitHub/rmsx`
- Branch: `main`
- Commit inspected: `dbd394198a6eeba257339fd630a4038eba424afe`
- Last local commit message: `added masked flipbook example`
- Local working tree note: several generated local artifacts were modified locally. This report focuses on tracked source files and package metadata, not those local output changes.

Publication and public documentation context:

- Scientific Reports article: <https://www.nature.com/articles/s41598-026-39869-7>
- PubMed entry: <https://pubmed.ncbi.nlm.nih.gov/41720904/>
- Public README raw snapshot checked from `main`: <https://raw.githubusercontent.com/AntunesLab/rmsx/main/README.md>

Repository files inspected most closely:

- Package metadata: <https://github.com/AntunesLab/rmsx/blob/dbd394198a6eeba257339fd630a4038eba424afe/pyproject.toml>
- Package exports: <https://github.com/AntunesLab/rmsx/blob/dbd394198a6eeba257339fd630a4038eba424afe/rmsx/__init__.py>
- Console entry point: <https://github.com/AntunesLab/rmsx/blob/dbd394198a6eeba257339fd630a4038eba424afe/rmsx/cli.py>
- Core RMSX implementation: <https://github.com/AntunesLab/rmsx/blob/dbd394198a6eeba257339fd630a4038eba424afe/rmsx/core.py>
- Flipbook viewer launcher: <https://github.com/AntunesLab/rmsx/blob/dbd394198a6eeba257339fd630a4038eba424afe/rmsx/flipbook.py>
- R plotting script: <https://github.com/AntunesLab/rmsx/blob/dbd394198a6eeba257339fd630a4038eba424afe/rmsx/r_scripts/plot_rmsx.R>
- Output safety helpers: <https://github.com/AntunesLab/rmsx/blob/dbd394198a6eeba257339fd630a4038eba424afe/rmsx/output_safety.py>
- lDDT addon: <https://github.com/AntunesLab/rmsx/blob/dbd394198a6eeba257339fd630a4038eba424afe/rmsx/addons/lddt.py>
- Tests: <https://github.com/AntunesLab/rmsx/tree/dbd394198a6eeba257339fd630a4038eba424afe/tests>

## Executive Findings

RMSX is closer to Galaxy-ready than expected because it already has a Python package, a console script named `rmsx`, a noninteractive computational core, bundled demo data, explicit output directories, and tests for some important safety behaviors.

The immediate Galaxy target should be a standard RMSX analysis wrapper around the CLI or a very thin Python adapter. The first wrapper should produce CSVs, PNG plots, per-slice PDB files, mask metadata, and a log. It should not launch ChimeraX or VMD.

Flipbook is currently a local viewer-launch path, not a Galaxy-native visualization artifact. The useful Galaxy output from Flipbook today is the directory of PDB slice files with RMSX values written into B-factors. A Galaxy-friendly Flipbook route should treat those PDB slices as datasets first, then add a viewer later through a static report, Galaxy visualization plugin, or InteractiveTool.

The biggest hardening items before a publishable wrapper are dependency packaging and output predictability:

- R packages are installed at runtime by `plot_rmsx.R`, which is not appropriate for Galaxy job execution.
- The package version in `pyproject.toml` is `0.1.0`, while public release/documentation context points to later repository releases.
- The CLI exposes only single-chain `run_rmsx`, not all-chain RMSX or Flipbook.
- The core function prompts for chain selection if no chain is passed, so Galaxy must always pass a chain or use an all-chain adapter.
- `analysis_type` options are broader in the CLI than in the core selection logic.
- Test/demo data is useful but large for a Tool Shed wrapper test corpus.

## Repository Shape

The repository is a Python package with mixed Python, R, Tcl, desktop-viewer, and molecular-data assets.

Key package files:

- `pyproject.toml` declares package `rmsx`, Python `>=3.8`, dependencies `MDAnalysis>=2.0.0` and `pandas>=1.1.0`, and a console script `rmsx = "rmsx.cli:main"`.
- `rmsx/__init__.py` lazily exports `run_rmsx`, `all_chain_rmsx`, `run_rmsx_flipbook`, `run_flipbook`, shift-map functions, and related helpers.
- `rmsx/cli.py` is the only declared console script entry point.
- `rmsx/core.py` contains RMSX computation, output naming, mask handling, RMSD/RMSF helpers, R plotting invocation, per-chain and all-chain orchestration, shift-map variants, and Flipbook orchestration.
- `rmsx/flipbook.py` launches ChimeraX or VMD over generated PDB slices and can save or render a Flipbook image through viewer commands.
- `rmsx/r_scripts/plot_rmsx.R` generates heatmaps and optional triple plots.
- `rmsx/vmd_scripts/` contains VMD Tcl scripts used by the VMD Flipbook backend.
- `rmsx/addons/lddt.py` adds an lDDT-style map using the same output and Flipbook patterns.
- `tests/` covers output-directory safety, masking, Flipbook mask command generation, VMD script packaging, and local-demo safety assumptions.

The package includes demo molecular files under both `test_files/` and `rmsx/test_files/`. The top-level `test_files` directory is about 69 MB. The packaged `rmsx/test_files` directory is about 50 MB.

## Packaging and Dependencies

### Python Package Metadata

`pyproject.toml` is usable as a starting point for Galaxy packaging because it declares a package and console script.

Current declared Python dependencies:

- `MDAnalysis>=2.0.0`
- `pandas>=1.1.0`

Observed implicit or optional Python dependencies:

- `numpy`, imported in `rmsx/core.py`
- optional rich-display helpers, used only outside the Galaxy runtime
- Standard-library modules including `subprocess`, `shutil`, `argparse`, `pathlib`, `csv`, `threading`, and `pty`

Galaxy implication:

- A Conda recipe or container should include `python`, `mdanalysis`, `pandas`, `numpy`, and the R stack.
- rich-display helper packages should not be required for Galaxy execution.
- Package version metadata should be resolved before publication. A Galaxy wrapper version should not depend on a package claiming `0.1.0` if the intended source/release is later.

### R Plotting Dependencies

The plotting layer is an R script invoked by Python through `Rscript`. It uses:

- `ggplot2`
- `viridis`
- `dplyr`
- `tidyr`
- `stringr`
- `readr`
- `gridExtra`
- `grid`
- `ggpattern` when masked heatmaps are needed

`plot_rmsx.R` attempts to install missing packages into the user R library at runtime. This is fine for local exploratory use but should not be used in Galaxy jobs. Galaxy tools should declare dependencies up front through Conda or a container image.

Galaxy implication:

- The wrapper should either depend on a Conda environment that includes all needed R packages or use a container.
- Runtime CRAN downloads should be disabled or avoided in the Galaxy path.
- Masked heatmaps require R 4.1+ because of the `ggpattern` path.

### Viewer Dependencies

Flipbook currently depends on local desktop molecular viewers:

- ChimeraX for the default viewer path.
- VMD for an alternate viewer path with Tcl scripts and optional photorealistic rendering.

Galaxy implication:

- Do not launch ChimeraX or VMD in a standard Galaxy tool job for v1.
- Treat generated PDB slice files as Galaxy outputs.
- Consider a separate visualization route only after the compute wrapper is stable.

### License

The repository uses the MIT License. That is friendly to Galaxy wrapper publication, subject to dependency licenses and viewer redistribution constraints.

## Entry Points

### Console Script: `rmsx`

The declared console script points to `rmsx.cli:main`. The parser accepts two required positional inputs:

- `psf_file`: described as topology file, examples include PSF, PDB, PRMTOP.
- `dcd_file`: described as trajectory file, examples include DCD, XTC, TRR.

The names are legacy. The code passes them to `run_rmsx(topology_file, trajectory_file, **kw)`.

Important CLI options:

- `--output_dir`
- `--slice_size`
- `--num_slices`
- `--chain`
- `--palette`
- `--start_frame`
- `--end_frame`
- `--analysis_type`
- `--summary_n`
- `--manual_length_ns`
- `--custom_fill_label`
- `--rscript`
- `--verbose` / `--quiet`
- `--interpolate` / `--no-interpolate`
- `--triple`
- `--log_transform`
- `--no-plot`
- `--overwrite`

Galaxy fit:

- This is enough for a minimal single-chain Flipbook wrapper.
- The wrapper must always provide either `--num_slices` or `--slice_size`.
- The wrapper should pass `--chain` unless a separate all-chain adapter is used.
- The wrapper should pass `--output_dir` inside Galaxy's job working directory.

Limitation:

- The CLI does not expose `all_chain_rmsx`, `run_rmsx_flipbook`, `run_flipbook`, shift-map, or lDDT modes.

### Python API

The package exports the richer API lazily from `rmsx/__init__.py`:

- `run_rmsx`
- `all_chain_rmsx`
- `run_rmsx_flipbook`
- `run_flipbook`
- `run_shift_map`
- `all_chain_shift_map`
- `run_shift_flipbook`

Galaxy fit:

- A wrapper can use the console script for v1.
- Later all-chain or Flipbook-export modes will probably need either a new upstream CLI command or a very small Galaxy adapter script that calls the Python API and writes a predictable manifest.

## Core RMSX Behavior

### Selection Model

The core selection helper returns MDAnalysis selection strings:

- `analysis_type="dna"` uses `nucleicbackbone` or `nucleic and name P`.
- Other analysis types use `protein and backbone` or `protein and name CA`.
- If `chain_sele` is set, the selection adds `and segid <chain>`.

Important Galaxy implication:

- RMSX uses MDAnalysis `segid` for chain selection, not necessarily PDB chain IDs. Some uploaded PDBs may not have useful segids, or may encode chain identity differently.
- The CLI allows `analysis_type` values `protein`, `dna`, `rna`, and `generic`, but the core selection function only special-cases `dna`; other values behave as protein. That should be clarified before exposing all four choices in Galaxy.

### `run_rmsx`

`run_rmsx` is the single-chain compute entry point.

Inputs:

- Topology file.
- Trajectory file.
- Output directory.
- `num_slices` or `slice_size`.
- Chain selection.
- Rscript path and plotting options.
- Frame range.
- Analysis type.
- Optional mask selection.

Behavior:

- Loads topology with MDAnalysis.
- Detects segids and filters chains that have CA atoms under the requested selection.
- If `chain_sele` is not supplied, prompts interactively for a chain.
- Creates `output_dir/chain_<chain>_rmsx`.
- Loads topology plus trajectory with MDAnalysis.
- Applies an inclusive frame window.
- Splits the selected frame range by `num_slices` or `slice_size`.
- Truncates excess frames so all slices are equal size.
- For each slice, writes `slice_<n>_first_frame.pdb`.
- Computes per-slice RMSF for CA atoms and writes that as RMSX table columns.
- Writes an RMSX CSV named from trajectory stem and inferred/manual simulation length.
- Writes `masked_residues.csv` beside the RMSX CSV.
- Calculates whole-window RMSD and RMSF into `rmsd.csv` and `rmsf.csv`.
- Updates PDB B-factors with RMSX values.
- Optionally calls the R plotting script to generate PNG plots.
- Prints summary tables to stdout.

Outputs to collect in Galaxy:

- `chain_<chain>_rmsx/rmsx_*.csv`
- `chain_<chain>_rmsx/rmsd.csv`
- `chain_<chain>_rmsx/rmsf.csv`
- `chain_<chain>_rmsx/masked_residues.csv`
- `chain_<chain>_rmsx/*_rmsx_plot_chain_*.png`
- `chain_<chain>_rmsx/slice_*_first_frame.pdb`
- Tool stdout/stderr as a log dataset, especially for summary tables.

Galaxy friction:

- If no chain is passed, the function prompts. Galaxy must avoid this.
- If the output subdirectory already exists and `overwrite=False`, it prompts. Galaxy should write into a fresh directory or pass overwrite deliberately.
- The function returns summary data, not output paths. Galaxy can still discover files from the output directory, but an explicit manifest would make wrappers easier.
- There appears to be a duplicated `if num_slices is not None` compute block in `run_rmsx`; the first result is overwritten by the second. That is wasteful and should be cleaned up before large-scale use.

### `all_chain_rmsx`

`all_chain_rmsx` orchestrates `run_rmsx` over every valid segid in the topology.

Behavior:

- Uses `prepare_managed_output_dir` for safer output-directory handling.
- Runs `run_rmsx` for each valid chain.
- Can defer masked clipping so global unmasked min/max can be applied.
- Combines chain PDB slices into `output_dir/combined` when multiple chains are found.
- Writes combined mask metadata when masks are active.
- Can regenerate plots with synchronized color scaling.
- Returns the directory that should be used for Flipbook display.

Galaxy fit:

- This is likely the better long-term compute mode for Galaxy, because users may not know segids ahead of time and many MD systems are multi-chain.
- Because it is not exposed through the current console script, use it in a later phase via a new CLI mode or a small wrapper-side Python adapter.

### `run_rmsx_flipbook`

`run_rmsx_flipbook` calls `all_chain_rmsx`, then calls `run_flipbook` on the combined output directory.

Behavior:

- Computes RMSX for all chains.
- Combines PDB slices when appropriate.
- Launches the selected viewer, defaulting to ChimeraX.

Galaxy fit:

- Do not use this full path in a standard Galaxy tool v1 because it launches a desktop viewer.
- The compute half is useful; the viewer-launch half should be separated.

## Flipbook Behavior

`rmsx/flipbook.py` is a viewer launcher over already-generated PDB slice files.

Inputs:

- Directory containing files matching `slice_<number>_first_frame.pdb`.
- Palette.
- Optional min/max B-factor values.
- Spacing factor.
- Optional extra ChimeraX commands.
- Viewer choice: `chimerax` or `vmd`.

Behavior:

- Validates the directory exists.
- Finds and naturally sorts `slice_*_first_frame.pdb` files.
- Extracts min/max B-factor values if the user did not provide them.
- Builds a color mapping.
- Builds ChimeraX commands that open all PDB slices, color/worm by B-factor, tile models, and save `rmsx_<palette>.png`.
- If mask metadata is present, adds transparency commands.
- For VMD, finds a VMD executable and launches it with packaged Tcl scripts.
- Uses `subprocess.Popen` so viewer launch is detached/nonblocking.

Galaxy interpretation:

- Flipbook's current reusable data product is a set of PDB slice files with B-factors encoding RMSX or related values.
- `rmsx_<palette>.png` is generated by a viewer command, not by a headless library call in the Python code itself.
- A Galaxy v1 wrapper should expose the PDB slices and plot PNGs, but not try to pop up ChimeraX or VMD.
- A future Galaxy visualization could render these PDB slices with a browser molecular viewer if the data contract is stable.

## R Plotting Behavior

`plot_rmsx.R` is called from Python as:

```text
Rscript plot_rmsx.R <rmsx_csv> <rmsd_csv> <rmsf_csv> <interpolate> <triple> <palette> [min] [max] [log] [fill_label] [window_check]
```

It reads the RMSX CSV and optional mask metadata, then writes PNG files beside the CSV. Output filenames are derived from the CSV basename:

- `<csv_basename>_rmsx_plot_chain_<ChainID>.png`

If `triple=TRUE`, the triple composite overwrites the basic heatmap filename.

Galaxy interpretation:

- The plot output is predictable enough to discover by glob.
- Because output names depend on the CSV basename and chain IDs, a wrapper should either use discovery or write an explicit manifest.
- Runtime R package installation should be removed from the Galaxy execution path.

## Test and Demo Corpus

The repository has useful pytest coverage:

- Output directory safety refuses unsafe overwrite targets and unmanaged folders.
- Masking clips masked residues, writes metadata, and excludes masked residues from summaries.
- Flipbook masking builds ChimeraX transparency commands and passes VMD mask settings through environment variables.
- Local-demo safety tests check that demo files are packaged and that generated demo outputs go to `rmsx_demo_outputs`.

Test/data observations:

- `test_files/1UBQ.pdb` is about 96 KB.
- The original `test_files/mon_sys.dcd` was about 4.5 MB. The Galaxy wrapper
  now uses a precision-2 XTC fixture that preserves all 316 frames while staying
  under 1 MB for local demo and Planemo tests.
- `test_files/protease_backbone.pdb` is about 64 KB.
- `test_files/short_protease_backbone.dcd` is about 46 MB.
- The top-level `test_files/` directory is about 69 MB.
- The packaged `rmsx/test_files/` directory is about 50 MB.

Galaxy implications:

- `1UBQ.pdb` plus compressed `mon_sys.xtc` is the current best available
  starting fixture for wrapper tests.
- The fixture-size issue is addressed; provenance and redistribution notes
  still need to be finalized before Tool Shed/IUC submission.
- Tests currently exercise Python APIs more than the console script. A Galaxy wrapper should add at least one CLI-level smoke test before Planemo work.
- Some local-demo tests reference an absolute local path, which is not portable outside this workstation.

## Galaxy Readiness Assessment

### Ready for a Minimal Wrapper

The following are already in good shape for a first Galaxy wrapper:

- Python package structure.
- Console script entry point.
- Headless core computation using MDAnalysis.
- Explicit output directory parameter.
- PDB plus DCD/XTC demo data.
- Deterministic CSV and PNG output patterns.
- Per-slice PDB files with B-factor encoded values.
- MIT license.

### Needs Hardening Before Publication

These should be addressed before a public Tool Shed or IUC-style wrapper:

- Declare all R dependencies in Conda/container metadata; avoid runtime installs.
- Resolve package version metadata.
- Add a CLI mode for all-chain RMSX or create a narrow Galaxy adapter.
- Decide how Galaxy should handle chain selection: explicit text input, auto all-chain mode, or a separate chain-detection helper.
- Clarify `analysis_type` behavior before exposing `rna` or `generic`.
- Ensure all outputs have deterministic declarations or a manifest.
- Capture stdout summaries into a declared log/summary dataset.
- Avoid viewer launches in Galaxy jobs.
- Trim or generate smaller test data.
- Add CLI smoke tests independent of local demo harnesses.

## Proposed Galaxy v1 Wrapper Contract

Tool name:

- `Flipbook trajectory analysis`

Recommended v1 mode:

- Single-chain RMSX through the existing `rmsx` CLI, or all-chain RMSX through a very thin adapter if adding one is allowed in the next implementation phase.

Inputs:

- Topology/structure dataset: start with PDB.
- Trajectory dataset: start with DCD.
- Chain/segid text input.
- Slicing mode: `num_slices` or `slice_size`.
- Start frame and optional end frame.
- Analysis type: expose `protein` and maybe `dna` first; hold `rna` and `generic` until core behavior is explicit.
- Plot toggle.
- Triple-plot toggle.
- Palette.
- Optional mask selection using raw MDAnalysis syntax.
- Optional manual simulation length.

Outputs:

- RMSX table: CSV or tabular.
- RMSD table: CSV/tabular.
- RMSF table: CSV/tabular.
- RMSX heatmap/triple plot: PNG.
- Per-slice PDB files: output collection of PDB datasets.
- Mask metadata: CSV/tabular when present.
- Execution log: text.

Implementation notes for a future wrapper:

- Run inside a fresh job working directory.
- Use an explicit `--output_dir`.
- Always pass `--chain` for the CLI path.
- Always pass either `--num_slices` or `--slice_size`.
- Pass `--quiet` for normal operation, but capture stdout/stderr.
- Prefer output discovery for `rmsx_*.csv`, `*_rmsx_plot_chain_*.png`, and `slice_*_first_frame.pdb`.
- Keep Flipbook viewer launching out of the v1 wrapper.

## Proposed Later Routes

### Route 2: All-Chain RMSX Wrapper

Goal: run `all_chain_rmsx` and emit one collection per output type.

Why it matters:

- Users may not know segids.
- Multi-chain MD systems are common.
- It naturally creates a combined PDB-slice directory for Flipbook-style display.

Likely requirement:

- Add an upstream CLI subcommand or a wrapper-side Python adapter that calls `all_chain_rmsx` and writes a manifest.

### Route 3: Flipbook Export Tool

Goal: transform an RMSX output directory or PDB-slice collection into Galaxy-friendly visual artifacts.

Outputs:

- Collection of B-factor colored PDB slices.
- Optional combined PDB or model bundle if feasible.
- Optional static PNG if a headless rendering path is made reliable.
- Optional JSON manifest for browser viewers.

Avoid:

- Launching ChimeraX or VMD from the Galaxy job as the primary result.

### Route 4: Galaxy Visualization Plugin

Goal: display RMSX/Flipbook outputs in the Galaxy UI using browser-side molecular visualization.

Prerequisite:

- Stable data contract for PDB slices, RMSX CSVs, palette metadata, and optional masks.

### Route 5: InteractiveTool

Goal: expose a richer Flipbook web app if the visualization truly needs a live service.

Use only if:

- A static PDB/HTML/JavaScript visualization route cannot satisfy the core use case.

## Specific Issues and Questions to Resolve Next

- Is `segid` the right Galaxy-facing chain selector, or should RMSX support PDB chain ID more directly?
- Should Galaxy v1 be single-chain or all-chain by default?
- Should `rna` and `generic` be hidden until core selection behavior supports them explicitly?
- Can RMSX expose output paths or a manifest to make Galaxy output collection less brittle?
- Can the R plotting script be made dependency-pure for packaged execution?
- Is a smaller test trajectory available or easy to generate?
- Should the Galaxy wrapper package RMSX from PyPI, GitHub, a local source checkout, or a container?
- Which public release/version should the Galaxy wrapper pin?
- Should Flipbook's first Galaxy artifact be a PDB collection, a combined multi-model PDB, an HTML report, or a visualization plugin?

## Recommended Next Phase

The next phase should be a wrapper design spike, still before full implementation:

1. Draft the exact Galaxy XML interface for the single-chain RMSX CLI path.
2. Define the output discovery rules for CSV, PNG, PDB slices, mask metadata, and logs.
3. Decide whether to add a tiny RMSX-side manifest or adapter for all-chain mode.
4. Build a dependency matrix mapping Python/R packages to Conda packages.
5. Select the smallest viable test fixture and expected output assertions.
6. Only after that, scaffold a minimal Planemo-tested wrapper.
