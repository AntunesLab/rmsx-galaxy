# Contributing

Thanks for helping with the RMSX Galaxy cofest work. This repo is intentionally practical: small branches, clear screenshots, and reproducible local checks are more useful than perfect polish.

## Local Setup

1. Clone this repo.
2. Bootstrap the project-local Planemo environment and optional Node dependencies:

```bash
scripts/bootstrap_dev.sh
```

3. Build the local runtime image before running Galaxy or Planemo Docker tests:

```bash
scripts/build_container.sh
```

4. Keep generated environments and outputs out of commits. `.gitignore` excludes Planemo homes, Node modules, local test reports, and editor caches.

For a one-command first setup, use:

```bash
scripts/bootstrap_dev.sh --with-container
```

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
scripts/run_static_checks.sh
```

This command skips the network-dependent Tool Shed check when the public Tool Shed is unreachable. For publication or CI checks, run:

```bash
STRICT_SHED_LINT=1 scripts/run_static_checks.sh
```

For Galaxy wrapper changes:

```bash
scripts/run_planemo_tests.sh
```

If you changed the container runtime, rebuild first:

```bash
scripts/run_planemo_tests.sh --build
```

For manual viewer testing, run:

```bash
scripts/serve_galaxy_demo.sh
```

Then run the bundled example and open the Molstar manifest through Galaxy's `Visualize` action.

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
- `container`
- `docs`
- `tests`
- `good-first-cofest-task`
- `blocked`

## Viewer Work

The native Galaxy Molstar visualization is the primary viewer target. Development-only standalone HTML output can be useful while debugging the viewer, but the supported path is the Galaxy `Visualize` action on the RMSX manifest dataset.
