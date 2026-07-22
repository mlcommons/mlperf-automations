# This repo is now content-only

As of `mlc-scripts` 2.0.0 (the "Option B" migration), `mlperf-automations` no
longer contains an execution engine. The `automation/` directory is gone. This
repo is now purely **content**: ~378 benchmark script directories
(`meta.yaml` + `customize.py` + `run.sh`), published as pip package data in
the `mlc-scripts` package.

The engine that runs these scripts — `ScriptAutomation`, dependency
resolution, caching, Docker/Apptainer/remote-SSH execution — lives in
[`mlcflow`](https://github.com/mlcommons/mlcflow) at `mlc/engine/`, and is
`pip install`ed as the separate `mlcflow` package.

**Full explanation, reference, and how-to docs for this migration live in the
mlcflow docs** — this page is intentionally short:

- [Why Option B](https://docs.mlcommons.org/mlcflow/migration/) — the problem this solves and the design trade-offs
- [Reference](https://docs.mlcommons.org/mlcflow/migration/reference/) — package layout, script discovery, cache resolution, remote/Docker flags
- [Running remote/Docker without a clone](https://docs.mlcommons.org/mlcflow/migration/remote-and-docker/)
- [Upgrading from pre-2.0 mlcflow](https://docs.mlcommons.org/mlcflow/migration/upgrading/)
- [Tutorial: fresh install to first run](https://docs.mlcommons.org/mlcflow/migration/tutorial-fresh-install/)

## What changed in this repo specifically

- `automation/script/*.py` and `automation/utils.py` → moved to `mlcflow`'s
  `mlc/engine/`. No longer present here.
- Top-level `script/<alias>/` → moved to `mlc_scripts/script/<alias>/`,
  declared as `package-data` in `pyproject.toml` so `pip install mlc-scripts`
  bundles every script directory's full contents (yaml, Python, shell,
  README, tests, and any binary/source assets a script needs).
- `setup.py` and its `CustomInstallCommand` (which used to run `mlc pull repo`
  as a post-install step) were removed. Packaging is pure `pyproject.toml`
  now — nothing is fetched over the network at install time.
- `mlc_scripts/script/by-category/**` is a set of symlinks back into the
  canonical `mlc_scripts/script/<alias>/` directories, kept for docs-site
  category browsing. It's not a second copy of any script's logic — if you're
  editing a script, edit it at its canonical path.

## Installing this package alone doesn't run anything

```bash
pip install mlc-scripts
```

only gives you script *content* — `mlc_scripts.SCRIPTS_DIR`. You also need the
engine:

```bash
pip install mlcflow mlc-scripts
```

`mlc-scripts`' own `pyproject.toml` declares `mlcflow>=2.0.0,<3` as a
dependency, so a plain `pip install mlc-scripts` pulls in a compatible
`mlcflow` automatically — the explicit `pip install mlcflow mlc-scripts` above
is just the clearest way to say what you're getting.

## Contributing a new script

The workflow is unchanged — `mlc add script`, edit `meta.yaml`/`customize.py`,
`mlc lint script`, open a PR against `main` — see
[AGENTS.md](https://github.com/mlcommons/mlperf-automations/blob/main/AGENTS.md)
for the full walkthrough. The only difference from before the migration is
where your script ends up: `mlc_scripts/script/<alias>/`, not `script/<alias>/`.

If you're actively developing a script and want your local edits to take
effect instead of the published `mlc-scripts` package's version of the same
script (on a UID clash), set `MLC_PREFER_DEV_SCRIPTS=1` — see the
[mlcflow reference](https://docs.mlcommons.org/mlcflow/migration/reference/#priority-on-a-uid-clash-bundled-package-wins-by-default)
for why the bundled package wins by default otherwise.
