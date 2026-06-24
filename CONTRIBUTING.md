# Contributing

Thanks for helping with the RMSX Galaxy cofest work. This repo is intentionally practical: small branches, clear screenshots, and reproducible local checks are more useful than perfect polish.

## Local Setup

1. Clone this repo.
2. Install or reuse the project-local Planemo environment if available.
3. Install Node dependencies when working on browser checks:

```bash
pnpm install
```

4. Keep generated environments and outputs out of commits. `.gitignore` excludes Planemo homes, Node modules, notebook outputs, test reports, and notebook checkpoints.

## Branches

Use short-lived branches:

```text
codex/<short-task-name>
<yourname>/<short-task-name>
```

Prefer one issue per branch or pull request when practical.

## Checks Before Pull Request

Run the relevant subset for your change:

```bash
python3 -m py_compile tools/rmsx/*.py
python3 tests/rmsx/test_manifest_and_visualization.py
node --check config/plugins/visualizations/rmsx_molstar/static/script.js
python3 -m json.tool notebooks/rmsx_molstar_widget_sizing_prototype.ipynb
```

For Galaxy wrapper changes:

```bash
.venv-planemo/bin/planemo lint --fail_level error tools/rmsx/rmsx.xml
.venv-planemo/bin/planemo shed_lint tools/rmsx
```

For runtime/container changes, run the Docker-backed Planemo test documented in `docs/rmsx-galaxy-share-readiness.md`.

## Issues

Good issues include:

- What you tried.
- What happened.
- What you expected.
- Browser/Galaxy/Planemo version if relevant.
- A screenshot or short GIF for viewer behavior.
- The manifest, Galaxy URL, or fixture path when safe to share.

Use labels to route work:

- `galaxy-tool`
- `molstar-viewer`
- `notebook`
- `container`
- `docs`
- `tests`
- `good-first-cofest-task`
- `blocked`

## Viewer Work

The native Galaxy Molstar visualization is the primary viewer target. Standalone HTML and notebook direct-mount prototypes are useful for development, but do not replace the Galaxy `Visualize` path unless the team explicitly decides to change direction.
