# UseGalaxy Deployment

The Flipbook analysis tool and the native RMSX Molstar viewer have separate
release paths. Both need to finish before users get the complete experience on
UseGalaxy.eu or Galaxy Main.

## Current Status

- Complete: `galaxyproject/galaxy-visualizations#174` is merged and
  `@galaxyproject/rmsxflipbook@0.0.2` is published.
- Complete: `galaxyproject/galaxy-test-data#83` is merged with the public
  `1UBQ.pdb` and `mon_sys.xtc` example.
- Complete: `galaxyproject/galaxy#23009` pins viewer package `0.0.2` and assigns
  the `rmsxflipbook` visualization to `rmsx.json`; the PR still needs to merge.
- Complete: the runtime image build, bundled-example smoke test, and all three
  Galaxy wrapper tests pass locally and in GitHub Actions.
- Pending: the published GHCR package is still private, so its anonymous-pull
  workflow gate fails with `unauthorized`.
- Prepared: the community, UseGalaxy.eu, and Galaxy Main request branches are
  pushed. Open the server-list PRs only after `chemteam/flipbook` has an
  installable Main Tool Shed revision.

## Remaining Order

1. Verify that
   `ghcr.io/antuneslab/flipbook-galaxy:0.2.3-galaxy0` pulls anonymously.
   GHCR requires an AntunesLab administrator to
   change the `flipbook-galaxy` package visibility to **Public** before the
   workflow's anonymous-pull check can pass.
2. Merge `galaxyproject/galaxy#23009` so Galaxy recognizes the `rmsx.json`
   output datatype and launches the native viewer for it.
3. Propose the tested `tools/flipbook` wrapper to
   `galaxycomputationalchemistry/galaxy-tools-compchem` with Tool Shed owner
   `chemteam`. That repository already maintains the MDAnalysis and GROMACS
   tools used beside Flipbook and deploys merged wrappers to the Test and Main
   Tool Sheds.
4. Ensure that the chemistry repository's Galaxy test branch contains the
   merged `rmsx.json` datatype before expecting its Planemo tests to pass. Its
   workflow currently pins Galaxy `release_24.0`, which predates this datatype,
   so maintainers will need to update that test branch or backport the registry
   entry.
5. After the wrapper is published, install and test its Test Tool Shed revision.
6. Run `scripts/check_server_deployment_readiness.sh` and record the Main Tool
   Shed installable revision used by the tool-list lock files.

Using the community `chemteam` owner is preferable to creating a separate
`antuneslab` Tool Shed account. It gives Europe and Galaxy Main the same trusted
repository and existing computational-chemistry maintainers. Direct publishing
from this repository remains possible by setting
`FLIPBOOK_TOOL_SHED_OWNER=antuneslab`, but it requires matching accounts and
credentials on both Tool Sheds and additional review for Galaxy Main.

## UseGalaxy.eu

Add this entry to `cheminformatics.yaml` in
`usegalaxy-eu/usegalaxy-eu-tools`, run `make fix`, inspect the generated
`cheminformatics.yaml.lock`, and run the repository checks before opening the
pull request:

```yaml
  - name: flipbook
    owner: chemteam
    tool_panel_section_label: ChemicalToolBox
```

Do not run `make fix` or commit the generated lock entry until `chemteam/flipbook`
has an installable revision in the Main Tool Shed.

## Galaxy Main (usegalaxy.org)

Add this entry to `usegalaxy.org/chemicaltoolbox.yml` in
`galaxyproject/usegalaxy-tools`, then run:

```bash
make TOOLSET=usegalaxy.org fix
make TOOLSET=usegalaxy.org lint
```

The source entry is:

```yaml
- name: flipbook
  owner: chemteam
```

Galaxy Main requires the repository to come from the Main Tool Shed. A tool
published by `chemteam` follows the established community-maintained route. The
wrapper's explicit public container is supported by the installation policy,
although an eventual Bioconda package and BioContainer remain the cleaner
long-term runtime.

## Native Viewer

The server's Galaxy code must also include the `rmsx.json` datatype and
`rmsxflipbook` visualization registration. Track these upstream changes:

- `galaxyproject/galaxy-visualizations#174`
- `galaxyproject/galaxy#23009`

UseGalaxy.eu and Galaxy Main need a Galaxy release or backport containing the
core change before the typed manifest can launch the viewer there.
