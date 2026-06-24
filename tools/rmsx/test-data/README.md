# RMSX Galaxy Test Data

This directory contains the PDB/XTC fixture used by the Galaxy wrapper tests.

- `1UBQ.pdb`: ubiquitin structure fixture used with the RMSX example path.
- `mon_sys.xtc`: compressed trajectory fixture used with `1UBQ.pdb`; current
  size is 1,002,408 bytes.

## Source And Provenance

The fixture represents the ubiquitin case study described in the RMSX/FlipBook
Scientific Reports manuscript. The paper identifies the system as an SMD
trajectory of ubiquitin using PDB `1UBQ`, sourced from the NAMD case-study
materials for ubiquitin. It reports that the simulation used NAMD 2.14 with PME
electrostatics and periodic boundary conditions, fixed Lys48, steered Met1 at
0.05 A/ps with a 208.4 pN/A spring constant, recorded frames every 10 ps, and
stripped waters for analysis.

The paper citation for the case-study source is:

> Cruz-Chu, E. & Gumbart, J. C. Case study: Ubiquitin.
> https://www.ks.uiuc.edu/Training/CaseStudies/, 2016.

Before opening an IUC PR, confirm and record the exact downloaded archive name,
download URL, original `mon_sys.dcd` checksum, and license/redistribution terms
for the NAMD case-study files. The manuscript gives enough scientific context
for review discussion, but the fixture README should still include exact file
lineage for redistribution.

## IUC Readiness Note

The current XTC fixture is useful for cofest reproducibility and is below the
tools-iuc 1 MB file-size check. It was generated from the original full
`mon_sys.dcd` by preserving all 316 frames and all atoms, then writing XTC with
precision 2. The command shape is:

```bash
/Applications/Docker.app/Contents/Resources/bin/docker run --rm \
  -v /Users/finn/Documents/Flipbook\ Integration:/work \
  -w /work \
  ghcr.io/antuneslab/rmsx-galaxy:0.2.3-galaxy0 \
  python scripts/create_reduced_rmsx_fixture.py \
    --topology tools/rmsx/test-data/1UBQ.pdb \
    --trajectory /path/to/original/mon_sys.dcd \
    --output tools/rmsx/test-data/mon_sys.xtc \
    --frames 316 \
    --xtc-precision 2
```

The fixture still exercises:

- PDB/XTC loading through MDAnalysis/RMSX.
- Three trajectory slices.
- Static heatmap and triple-plot generation.
- PDB slice collection output.
- Molstar manifest generation.
