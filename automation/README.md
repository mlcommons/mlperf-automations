# The automation engine has moved

The MLC script automation engine that used to live in this directory
(`automation/utils.py` and `automation/script/*`) is now maintained in
**[mlcflow](https://github.com/mlcommons/mlcflow)**, under `automation/`
there, and ships bundled with every `mlcflow` install.

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

- **Editing engine behaviour?** Open a PR against mlcflow, not this repo.
- **`from utils import ...` in a `customize.py` still works.** mlcflow puts its
  bundled `automation/` directory on `sys.path` before loading a script, so
  that import resolves against `mlcflow/automation/utils.py`. Nothing in
  `script/` needs to change.
- **Needs a recent mlcflow.** An mlcflow release that predates the engine
  bundling cannot run this repo any more, because neither side would ship an
  engine. Upgrade with `pip install --upgrade mlcflow`.

This file is a signpost, not code. It can be deleted once the redirect is no
longer useful to anyone.
