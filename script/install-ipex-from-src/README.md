# README for install-ipex-from-src
This README is automatically generated. Create and add custom content in info.md. Please follow the [script execution document](https://docs.mlcommons.org/mlcflow/targets/script/execution-flow/) to understand more about the MLC script execution.

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
mlcr install,get,src,from.src,ipex,src-ipex
```

No script specific inputs
### Generic Script Inputs

| Name | Description | Choices | Default |
|------|-------------|---------|------|
| `--input` | Input to the script passed using the env key `MLC_INPUT` |  | `` |
| `--output` | Output from the script passed using the env key `MLC_OUTPUT` |  | `` |
| `--outdirname` | The directory to store the script output |  | `cache directory ($HOME/MLC/repos/local/cache/<>) if the script is cacheable or else the current directory` |
| `--outbasename` | The output file/folder name |  | `` |
| `--search_folder_path` | The folder path where executables of a given script need to be searched. Search is done recursively upto 4 levels. |  | `` |
| `--name` |  |  | `` |
| `--extra_cache_tags` | Extra cache tags to be added to the cached entry when the script results are saved |  | `` |
| `--skip_compile` | Skip compilation |  | `False` |
| `--skip_run` | Skip run |  | `False` |
| `--skip_sudo` | Skip SUDO detection |  | `False` |
| `--accept_license` | Accept the required license requirement to run the script |  | `False` |
| `--skip_system_deps` | Skip installing any system dependencies |  | `False` |
| `--git_ssh` | Use SSH for git repos |  | `False` |
| `--gh_token` | Github Token |  | `` |
| `--hf_token` | Huggingface Token |  | `` |
| `--verify_ssl` | Verify SSL |  | `False` |
## Variations

### Repo

- `repo.#` _(# can be substituted dynamically)_
- `repo.https://github.com/intel/intel-extension-for-pytorch` (default)

### Ungrouped

- `branch.#` _(# can be substituted dynamically)_
- `for-intel-mlperf-inference-3d-unet` (alias: for-intel-mlperf-inference-v3.1-3d-unet) (base: branch.1.9.0-rc)
- `for-intel-mlperf-inference-resnet50` (alias: for-intel-mlperf-inference-v3.1-resnet50) (base: tag.v1.12.0)
- `for-intel-mlperf-inference-retinanet` (alias: for-intel-mlperf-inference-v3.1-retinanet) (base: tag.v1.12.0)
- `for-intel-mlperf-inference-v3.1-dlrm-v2` (base: sha.7256d0848ba81bb802dd33fca0e33049a751db58)
- `for-intel-mlperf-inference-v3.1-gptj` (base: branch.v2.1.0.dev+cpu.llm.mlperf)
- `for-intel-mlperf-inference-v4.0-sdxl` (alias: for-intel-mlperf-inference-sdxl) (base: sha.f27c8d42a734ae0805de2bd0d8396ce205638329)
- `sha.#` _(# can be substituted dynamically)_
- `tag.#` _(# can be substituted dynamically)_
