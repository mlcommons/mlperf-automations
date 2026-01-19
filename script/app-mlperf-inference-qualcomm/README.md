# README for app-mlperf-inference-qualcomm
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
mlcr reproduce,mlcommons,mlperf,inference,harness,qualcomm-harness,qualcomm,kilt-harness,kilt
```

### Script Inputs

| Name | Description | Choices | Default |
|------|-------------|---------|------|
| `--count` |  |  | `` |
| `--max_batchsize` |  |  | `` |
| `--mlperf_conf` |  |  | `` |
| `--mode` |  |  | `performance` |
| `--output_dir` |  |  | `` |
| `--performance_sample_count` |  |  | `` |
| `--scenario` |  |  | `Offline` |
| `--user_conf` |  |  | `` |
| `--devices` |  |  | `0` |
| `--skip_preprocess` |  |  | `no` |
| `--skip_preprocessing` | Alias for skip_preprocess |  | `` |
| `--target_qps` |  |  | `` |
| `--offline_target_qps` |  |  | `` |
| `--server_target_qps` |  |  | `` |
| `--target_latency` |  |  | `` |
| `--singlestream_target_latency` |  |  | `` |
| `--multistream_target_latency` |  |  | `` |
| `--rerun` |  |  | `` |
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
| `--skip_sudo` | Skip SUDO detection |  | `False` |
| `--accept_license` | Accept the required license requirement to run the script |  | `False` |
| `--skip_system_deps` | Skip installing any system dependencies |  | `False` |
| `--git_ssh` | Use SSH for git repos |  | `False` |
| `--gh_token` | Github Token |  | `` |
| `--hf_token` | Huggingface Token |  | `` |
| `--verify_ssl` | Verify SSL |  | `False` |
## Variations

### Batch-size

- `bs.#` _(# can be substituted dynamically)_
- `bs.0`

### Device

- `cpu` (default)
- `cuda`
- `qaic`

### Framework

- `glow`
- `onnxruntime` (default)
- `tensorrt`

### Loadgen-batch-size

- `loadgen-batch-size.#` _(# can be substituted dynamically)_

### Loadgen-scenario

- `multistream`
- `offline`
- `server`
- `singlestream`

### Model

- `bert-99` (base: bert_)
- `bert-99.9` (base: bert_)
- `resnet50` (default)
- `retinanet` (base: bs.1)

### Nsp

- `nsp.#` _(# can be substituted dynamically)_
- `nsp.14`
- `nsp.16` (base: pro)

### Power-mode

- `maxn`
- `maxq`

### Precision

- `fp16`
- `fp32`
- `uint8`

### Run-mode

- `network-client`
- `network-server`
- `standalone` (default)

### Sut

- `dl2q.24xlarge` (base: nsp.14)
- `rb6` (base: nsp.9)

### Ungrouped

- `activation-count.#` _(# can be substituted dynamically)_
- `bert_`
- `num-devices.4`
- `pro`
