# RMSX Galaxy Cofest Task List

This is the shared working list for the `rmsx-galaxy` cofest repository.

## Milestone 1: Shareable Private Repo

- [ ] Create the private `AntunesLab/rmsx-galaxy` repository.
- [ ] Push the clean initial scaffold.
- [ ] Add collaborator access once GitHub usernames are known.
- [ ] Confirm Issues, labels, and project board are available.
- [ ] Keep generated local artifacts out of the first commit.

## Milestone 2: Reproducible Local Demo

- [ ] Document the one-command-or-short-sequence local Galaxy serve path.
- [ ] Confirm the bundled 1UBQ example runs in local Galaxy.
- [ ] Confirm outputs include RMSX, RMSD, RMSF, PDB slices, heatmap PNG, triple plot PNG, execution log, and Molstar manifest.
- [ ] Confirm the manifest opens through Galaxy `Visualize` without a trusted-HTML warning.
- [ ] Capture one current screenshot or short GIF for the README after the demo stabilizes.

## Milestone 3: Galaxy Tool Hardening

- [ ] Run `planemo lint --fail_level error`.
- [ ] Run `planemo shed_lint`.
- [ ] Run Docker-backed Planemo tests with `config/planemo_docker_job_conf.yml`.
- [ ] Verify the wrapper no longer exposes stale NGL or public HTML report outputs.
- [ ] Review tool labels, help text, citations, and output names for collaborator clarity.

## Milestone 4: Native Molstar Viewer

- [ ] Keep tiled layout as the default presentation.
- [ ] Verify palette switching, spacing, thickness, columns, local rotation, and residue marker behavior.
- [ ] File viewer polish issues for camera fit, tile spacing, notebook direct mount, and Galaxy plugin packaging.
- [ ] Keep the native visualization plugin on vendored `molstar@5.4.2` until the team decides to upgrade.
- [ ] Decide which viewer improvements should move upstream versus remain Galaxy-specific.

## Milestone 5: Container And Packaging

- [ ] Choose the first supported upstream RMSX tag or commit.
- [ ] Build `ghcr.io/antuneslab/rmsx-galaxy:0.1.0`.
- [ ] Push the image to GHCR.
- [ ] Re-run Docker-backed Planemo tests using the pushed image.
- [ ] Open a follow-up issue for the Bioconda/Conda packaging route.

## Suggested GitHub Labels

- `galaxy-tool`
- `molstar-viewer`
- `notebook`
- `container`
- `docs`
- `tests`
- `good-first-cofest-task`
- `blocked`

## Known Non-Goals For The First Cofest Milestone

- Immediate Tool Shed publication.
- Immediate Bioconda publication.
- Replacing upstream RMSX documentation.
- Making the notebook prototype the primary Galaxy viewer path.
