# README for run-docker-container
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
mlcr run,docker,container
```

### Script Inputs

| Name | Description | Choices | Default |
|------|-------------|---------|------|
| `--all_gpus` |  |  | `` |
| `--num_gpus` |  |  | `` |
| `--base` |  |  | `` |
| `--cache` |  |  | `` |
| `--mlc_repo` |  |  | `` |
| `--detached` |  |  | `` |
| `--device` |  |  | `` |
| `--docker_image_base` | Alias for base |  | `` |
| `--docker_base_image` | Alias for base |  | `` |
| `--base_image` | Alias for base |  | `` |
| `--keep_detached` |  |  | `` |
| `--reuse_existing` |  |  | `no` |
| `--docker_os` |  |  | `` |
| `--docker_os_version` |  |  | `` |
| `--os` | Alias for docker_os |  | `` |
| `--os_version` | Alias for docker_os_version |  | `` |
| `--extra_run_args` |  |  | `` |
| `--fake_run_option` |  |  | `` |
| `--gh_token` |  |  | `` |
| `--image_name` |  |  | `` |
| `--image_repo` |  |  | `` |
| `--image_tag` |  |  | `` |
| `--image_tag_extra` |  |  | `` |
| `--interactive` |  |  | `` |
| `--it` |  |  | `` |
| `--mounts` |  |  | `` |
| `--use_host_user_id` |  |  | `` |
| `--use_host_group_id` |  |  | `` |
| `--pass_user_id` |  |  | `` |
| `--pass_user_group` |  |  | `` |
| `--port_maps` |  |  | `` |
| `--post_run_cmds` |  |  | `` |
| `--pre_run_cmds` |  |  | `` |
| `--privileged` |  |  | `no` |
| `--real_run` |  |  | `` |
| `--recreate` |  |  | `` |
| `--rebuild` | Alias for recreate |  | `` |
| `--run_cmd` |  |  | `` |
| `--run_cmd_extra` |  |  | `` |
| `--save_script` |  |  | `` |
| `--script_tags` |  |  | `` |
| `--shm_size` |  |  | `` |
| `--use_google_dns` |  |  | `` |
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
