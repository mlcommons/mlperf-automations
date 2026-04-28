# README for run-mlperf-automotive-app
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
mlcr run-abtf,inference
```

### Script Inputs

| Name | Description | Choices | Default |
|------|-------------|---------|------|
| `--backend` |  |  | `` |
| `--batch_size` |  |  | `` |
| `--category` |  |  | `` |
| `--clean` |  |  | `` |
| `--compliance` |  |  | `` |
| `--constantstream_target_qps` |  |  | `` |
| `--dashboard_wb_project` |  |  | `` |
| `--dashboard_wb_user` |  |  | `` |
| `--debug` |  |  | `` |
| `--device` |  |  | `` |
| `--division` |  |  | `` |
| `--docker` |  |  | `` |
| `--dump_version_info` |  |  | `` |
| `--execution_mode` |  |  | `test` |
| `--find_performance` |  |  | `` |
| `--framework` | Alias for backend |  | `` |
| `--gh_token` |  |  | `` |
| `--gpu_name` |  |  | `` |
| `--hw_name` |  |  | `` |
| `--hw_notes_extra` |  |  | `` |
| `--imagenet_path` |  |  | `` |
| `--implementation` |  |  | `reference` |
| `--lang` | Alias for implementation |  | `` |
| `--max_query_count` |  |  | `` |
| `--min_query_count` |  |  | `` |
| `--mode` |  |  | `` |
| `--model` |  |  | `retinanet` |
| `--multistream_target_latency` |  |  | `` |
| `--offline_target_qps` |  |  | `` |
| `--output_dir` |  |  | `` |
| `--output_summary` |  |  | `` |
| `--output_tar` |  |  | `` |
| `--performance_sample_count` |  |  | `` |
| `--power` |  |  | `` |
| `--precision` |  |  | `` |
| `--preprocess_submission` |  |  | `` |
| `--push_to_github` |  |  | `` |
| `--readme` |  |  | `` |
| `--regenerate_accuracy_file` |  |  | `` |
| `--regenerate_files` |  |  | `` |
| `--rerun` |  |  | `` |
| `--results_dir` | Alias for output_dir |  | `` |
| `--results_git_url` |  |  | `` |
| `--run_checker` |  |  | `` |
| `--run_style` | Alias for execution_mode |  | `` |
| `--save_console_log` |  |  | `` |
| `--scenario` |  |  | `` |
| `--server_target_qps` |  |  | `` |
| `--singlestream_target_latency` |  |  | `` |
| `--skip_submission_generation` |  |  | `` |
| `--skip_truncation` |  |  | `` |
| `--status` |  |  | `` |
| `--submission_dir` |  |  | `` |
| `--submitter` |  |  | `` |
| `--sut` |  |  | `` |
| `--sut_servers` |  |  | `` |
| `--sw_notes_extra` | Alias for hw_notes_extra |  | `` |
| `--system_type` | Alias for category |  | `` |
| `--target_latency` |  |  | `` |
| `--target_qps` |  |  | `` |
| `--test_query_count` |  |  | `` |
| `--threads` |  |  | `` |
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

### Benchmark-version

- `mvp-demo`
- `poc-demo`
- `v0.5`
- `v1.0`

### Mode

- `all-modes`

### Submission-generation

- `accuracy-only`
- `find-performance`
- `performance-and-accuracy` (base: all-modes) (default)
- `performance-only`
- `submission` (base: all-modes)

### Submission-generation-style

- `full`

### Ungrouped

- `all-scenarios`
- `compliance`
- `dashboard`
