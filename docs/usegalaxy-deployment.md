# UseGalaxy Deployment

The Flipbook analysis tool and the native RMSX Molstar viewer have separate
release paths. Both need to finish before users get the complete experience on
UseGalaxy.eu or Galaxy Main.

## Shared Prerequisites

1. Merge `galaxyproject/galaxy-visualizations#174` and publish
   `@galaxyproject/rmsxflipbook@0.0.2`.
2. Update `galaxyproject/galaxy#23009` from viewer package `0.0.1` to `0.0.2`,
   then merge it so Galaxy recognizes the `rmsx.json` output datatype.
3. Merge the wrapper/runtime changes in `AntunesLab/rmsx-galaxy`.
4. Run the `Flipbook Runtime Image` workflow and verify that
   `ghcr.io/antuneslab/flipbook-galaxy:0.2.3-galaxy0` pulls anonymously.
   On its first publication, GHCR may require an AntunesLab administrator to
   change the `flipbook-galaxy` package visibility to **Public** before the
   workflow's anonymous-pull check can pass.
5. Propose the tested `tools/flipbook` wrapper to
   `galaxycomputationalchemistry/galaxy-tools-compchem` with Tool Shed owner
   `chemteam`. That repository already maintains the MDAnalysis and GROMACS
   tools used beside Flipbook and deploys merged wrappers to the Test and Main
   Tool Sheds.
6. Ensure that the chemistry repository's Galaxy test branch contains the
   merged `rmsx.json` datatype before expecting its Planemo tests to pass.
7. After the wrapper is published, install and test its Test Tool Shed revision.
8. Run `scripts/check_server_deployment_readiness.sh` and record the Main Tool
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
