# This engine is frozen — it has moved to mlcflow

The MLC script automation engine in this directory (`automation/utils.py` and
`automation/script/*`) is now maintained in
**[mlcflow](https://github.com/mlcommons/mlcflow)**, under `automation/` there,
and ships bundled with every `mlcflow` install.

**The copy here is frozen.** It is kept only so that `mlcflow <= 1.2.9`, which
predates the migration and has no bundled engine, still has one to fall back
on. `mlcflow >= 1.3.0` loads its own bundled copy and ignores this directory
entirely. Once the grace period ends, this directory will be removed.

This repository keeps the script **content** — the 350+ `script/<alias>/`
directories with their `meta.yaml`, `customize.py` and `run.sh`.

## Where things went

| Was here | Now in mlcflow |
|---|---|
| `automation/script/module.py` | `automation/script/module.py` |
| `automation/script/cache_utils.py` | `automation/script/cache_utils.py` |
| `automation/script/docker.py`, `docker_utils.py` | same paths |
| `automation/script/apptainer.py`, `remote_run.py` | same paths |
| `automation/script/meta_schema.py`, `lint.py`, `doc.py`, `help.py`, `validate.py`, `experiment.py`, `script_utils.py` | same paths |
| `automation/utils.py` | `automation/utils.py` |

## What this means for you

- **Editing engine behaviour? Open a PR against
  [mlcflow](https://github.com/mlcommons/mlcflow), not this repo.** A change
  made here reaches nobody running a current mlcflow — it only affects users
  still on the deprecated fallback path.
- **`from utils import ...` in a `customize.py` still works.** mlcflow puts its
  bundled `automation/` directory on `sys.path` before loading a script, so
  that import resolves against `mlcflow/automation/utils.py`. Nothing in
  `script/` needs to change.
- **On an older mlcflow?** It still runs, using this fallback copy, and will
  warn you once per run. Upgrade with `pip install --upgrade mlcflow` to get
  mlcflow >= 1.3.0 and the maintained engine.

This file is a signpost, not code. It can be deleted along with the rest of
this directory once the fallback is no longer needed.
