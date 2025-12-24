# README for app-mlperf-automotive-mlcommons-python
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
mlcr automotive,mlcommons,reference,run-mlperf-inference,object-detection,abtf-model,demo
```

### Script Inputs

| Name | Description | Choices | Default |
|------|-------------|---------|------|
| `--device` |  |  | `` |
| `--count` |  |  | `` |
| `--docker` |  |  | `` |
| `--hw_name` |  |  | `` |
| `--imagenet_path` |  |  | `` |
| `--max_batchsize` |  |  | `` |
| `--mode` |  |  | `accuracy` |
| `--num_threads` |  |  | `` |
| `--threads` | Alias for num_threads |  | `` |
| `--dataset` |  |  | `` |
| `--model` |  |  | `` |
| `--output_dir` |  |  | `` |
| `--power` |  |  | `` |
| `--power_server` |  |  | `` |
| `--ntp_server` |  |  | `` |
| `--max_amps` |  |  | `` |
| `--max_volts` |  |  | `` |
| `--regenerate_files` |  |  | `` |
| `--rerun` |  |  | `` |
| `--scenario` |  |  | `Offline` |
| `--test_query_count` |  |  | `10` |
| `--clean` |  |  | `` |
| `--dataset_args` |  |  | `` |
| `--target_qps` |  |  | `` |
| `--target_latency` |  |  | `` |
| `--offline_target_qps` |  |  | `` |
| `--server_target_qps` |  |  | `` |
| `--constantstream_target_qps` |  |  | `` |
| `--singlestream_target_latency` |  |  | `` |
| `--multistream_target_latency` |  |  | `` |
| `--output` |  |  | `` |
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

### Batch-size

- `batch_size.#` _(# can be substituted dynamically)_

### Device

- `cpu` (default)
- `cuda`

### Framework

- `onnxruntime`
- `pytorch` (default)

### Implementation

- `python` (default)

### Loadgen-scenario

- `constantstream`
- `singlestream`

### Models

- `abtf-demo-model`
- `abtf-poc-model` (default)
- `bevformer`
- `deeplabv3plus`
- `ssd`

### Ungrouped

- `multistream`
- `mvp_demo`
- `offline`
- `server`
