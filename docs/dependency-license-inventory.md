# RMSX Galaxy Dependency And License Inventory

This is the human-readable dependency inventory for the current Galaxy runtime
plan. It should be regenerated from the final Conda/container environment before
IUC submission.

| Component | Role | Source | License status |
| --- | --- | --- | --- |
| RMSX | Scientific CLI and Python package | `AntunesLab/rmsx` tag `v0.2.3`; package metadata currently reports `0.1.0` | MIT |
| MDAnalysis | Topology/trajectory loading | Conda/PyPI | LGPL-compatible |
| pandas | Table handling | Conda/PyPI | BSD-style |
| numpy | Numeric runtime | Conda/PyPI | BSD-style |
| Plotly | Imported by upstream RMSX CLI at startup | Conda/PyPI | MIT |
| IPython | Imported by upstream RMSX core at startup; should become optional upstream | Conda/PyPI | BSD-3-Clause |
| R | Static plot runtime | Conda | GPL-family |
| ggplot2 | RMSX plot script dependency | Conda/CRAN | MIT |
| viridis | Palette support | Conda/CRAN | MIT-style |
| dplyr/tidyr/stringr/readr | RMSX plot script dependencies | Conda/CRAN | MIT |
| gridExtra | RMSX triple-plot layout | Conda/CRAN | GPL-compatible |
| Molstar 5.4.2 | Prototype native Galaxy viewer | npm/vendor bundle | MIT |

## Open Items

- Generate a machine-readable SBOM from the final runtime image.
- Record exact Conda build strings for all runtime dependencies.
- Reconcile upstream RMSX package metadata for `v0.2.3` before IUC submission.
- Keep ChimeraX and VMD out of the Galaxy runtime dependency list.
