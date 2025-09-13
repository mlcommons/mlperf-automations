# README for get-ml-model-llama2
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
mlcr get,raw,ml-model,language-processing,llama2,llama2-70b,text-summarization
```

### Script Inputs

| Name | Description | Choices | Default |
|------|-------------|---------|------|
| `--checkpoint` |  |  | `` |
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

### Download-source

- `hf`
- `mlc` (default)

### Download-tool

- `r2-downloader` (default)
- `rclone`

### Framework

- `pytorch` (default)

### Huggingface-stub

- `meta-llama/Llama-2-70b-chat-hf` (base: 70b)
- `meta-llama/Llama-2-7b-chat-hf` (base: 7b)
- `stub.#` _(# can be substituted dynamically)_

### Model-provider

- `amd`
- `nvidia`

### Model-size

- `70b` (default)
- `70b-fused-qkv`
- `7b`

### Pp-size

- `pp-size.#` _(# can be substituted dynamically)_

### Precision

- `fp32` (default)
- `fp8`
- `int8`
- `uint8`

### Quantization

- `pre-quantized`
- `quantize-locally` (default)

### Run-mode

- `dry-run`

### Tp-size

- `tp-size.#` _(# can be substituted dynamically)_

### Ungrouped

- `batch_size.#` _(# can be substituted dynamically)_

### Version

- `v5.0` (default)
