# README for install-llvm-src
This README is automatically generated. Add custom content in [info.md](info.md). Please follow the [script execution document](https://docs.mlcommons.org/mlcflow/targets/script/execution-flow/) to understand more about the MLC script execution.

`mlcflow` stores all local data under `$HOME/MLC` by default. So, if there is space constraint on the home directory and you have more space on say `/mnt/$USER`, you can do
```
mkdir /mnt/$USER/MLC
ln -s /mnt/$USER/MLC $HOME/MLC
```
You can also use the `ENV` variable `MLC_REPOS` to control this location but this will need a set after every system reboot.

## Setup

If you are not on a Python development environment please refer to the [official docs](https://docs.mlcommons.org/mlcflow/install/) for the installation.

```bash
python3 -m venv mlcflow
. mlcflow/bin/activate
pip install mlcflow
```

- Using a virtual environment is recommended (per `pip` best practices), but you may skip it or use `--break-system-packages` if needed.

### Pull mlperf-automations

Once `mlcflow` is installed:

```bash
mlc pull repo mlcommons@mlperf-automations --pat=<Your Private Access Token>
```
- `--pat` or `--ssh` is only needed if the repo is PRIVATE
- If `--pat` is avoided, you'll be asked to enter the password where you can enter your Private Access Token
- `--ssh` option can be used instead of `--pat=<>` option if you prefer to use SSH for accessing the github repository.
## Run Commands

```bash
mlcr install,src,llvm,from.src,src-llvm
```

### Script Inputs

| Name | Description | Choices | Default |
|------|-------------|---------|------|
| `--targets` |  |  | `` |
| `--target_triple` |  |  | `` |
| `--extra_options` |  |  | `` |
### Generic Script Inputs

| Name | Description | Choices | Default |
|------|-------------|---------|------|
| `--input` | Input to the script passed using the env key `MLC_INPUT` |  | `` |
| `--output` | Output from the script passed using the env key `MLC_OUTPUT` |  | `` |
| `--outdirname` | The directory to store the script output |  | `cache directory ($HOME/MLC/repos/local/cache/<>) if the script is cacheable or else the current directory` |
| `--outbasename` | The output file/folder name |  | `` |
| `--name` |  |  | `` |
| `--extra_cache_tags` | Extra cache tags to be added to the cached entry when the script results are saved |  | `` |
| `--skip_compile` | Skip compilation |  | `False` |
| `--skip_run` | Skip run |  | `False` |
| `--accept_license` | Accept the required license requirement to run the script |  | `False` |
| `--skip_system_deps` | Skip installing any system dependencies |  | `False` |
| `--git_ssh` | Use SSH for git repos |  | `False` |
| `--gh_token` | Github Token |  | `` |
| `--hf_token` | Huggingface Token |  | `` |
| `--verify_ssl` | Verify SSL |  | `False` |
## Variations

### Build-type

- `debug`
- `release` (default)

### Clang

- `clang` (default)
- `no-clang`

### Compiler-rt

- `compiler-rt` (default)
- `no-compiler-rt`

### Flang

- `flang`

### Libcxx

- `libcxx` (default)
- `no-libcxx`

### Lld

- `lld` (default)
- `no-lld`

### Repo

- `repo.#` _(# can be substituted dynamically)_

### Ungrouped

- `branch.#` _(# can be substituted dynamically)_
- `cross-compile-x86-aarch64`
- `for-intel-mlperf-inference-v3.1-bert` (base: tag.llvmorg-15.0.7, clang, release)
- `for-intel-mlperf-inference-v3.1-gptj` (base: tag.llvmorg-16.0.6, clang, release)
- `full-history`
- `path.#` _(# can be substituted dynamically)_
- `runtimes.#` _(# can be substituted dynamically)_
- `sha.#` _(# can be substituted dynamically)_
- `tag.#` _(# can be substituted dynamically)_ (base: full-history)

### Version

- `version.#` _(# can be substituted dynamically)_
- `version.main` (base: branch.main)
