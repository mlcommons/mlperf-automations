# README for app-mlperf-inference-intel
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
mlcr reproduce,mlcommons,mlperf,inference,harness,intel-harness,intel,intel-harness,intel
```

### Script Inputs

| Name | Description | Choices | Default |
|------|-------------|---------|------|
| `--count` |  |  | `` |
| `--max_batchsize` |  |  | `` |
| `--mlperf_conf` |  |  | `` |
| `--mode` |  |  | `performance` |
| `--multistream_target_latency` |  |  | `` |
| `--offline_target_qps` |  |  | `` |
| `--output_dir` |  |  | `` |
| `--performance_sample_count` |  |  | `` |
| `--rerun` |  |  | `` |
| `--scenario` |  |  | `Offline` |
| `--server_target_qps` |  |  | `` |
| `--singlestream_target_latency` |  |  | `` |
| `--skip_preprocess` |  |  | `no` |
| `--skip_preprocessing` | Alias for skip_preprocess |  | `` |
| `--target_latency` |  |  | `` |
| `--target_qps` |  |  | `` |
| `--user_conf` |  |  | `` |
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

### Device

- `cpu` (default)

### Framework

- `pytorch` (default)

### Loadgen-batchsize

- `batch_size.#` _(# can be substituted dynamically)_

### Loadgen-scenario

- `multistream`
- `offline`
- `server`
- `singlestream`

### Model

- `3d-unet-99` (base: 3d-unet_)
- `3d-unet-99.9` (base: 3d-unet_)
- `bert-99` (base: bert_)
- `bert-99.9` (base: bert_)
- `dlrm-v2-99` (base: dlrm-v2_)
- `dlrm-v2-99.9` (base: dlrm-v2_)
- `gptj-99` (base: gptj_)
- `gptj-99.9` (base: gptj_)
- `resnet50` (default)
- `retinanet`
- `sdxl`

### Network-mode

- `network-server`
- `standalone` (default)

### Network-run-mode

- `network-client`

### Power-mode

- `maxn`
- `maxq`

### Precision

- `fp32`
- `int4`
- `uint8` (alias: int8)

### Run-mode

- `build-harness`
- `calibration`
- `compile-model`
- `run-harness` (default)

### Sut

- `sapphire-rapids.112c`
- `sapphire-rapids.24c`

### Ungrouped

- `3d-unet_`
- `bert_`
- `bs.#` _(# can be substituted dynamically)_
- `dlrm-v2_`
- `gptj_`

### Version

- `v3.1`
- `v4.0` (default)
