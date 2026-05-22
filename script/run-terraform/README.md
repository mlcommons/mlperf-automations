# README for run-terraform
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
mlcr run,terraform
```

### Script Inputs

| Name | Description | Choices | Default |
|------|-------------|---------|------|
| `--cminit` |  |  | `` |
| `--destroy` |  |  | `` |
| `--gcp_credentials_json_file` |  |  | `` |
| `--key_file` |  |  | `` |
| `--run_cmds` |  |  | `` |
| `--ssh_key_file` | Alias for key_file |  | `` |
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

### Aws-instance-image

- `aws_instance_image.#` _(# can be substituted dynamically)_
- `aws_instance_image.ami-0735c191cf914754d`
- `aws_instance_image.ami-0a0d8589b597d65b3`

### Aws-instance-type

- `a1.2xlarge` (base: aws, arm64)
- `a1.metal` (base: aws, arm64)
- `a1.xlarge` (base: aws, arm64)
- `aws_instance_type.#` _(# can be substituted dynamically)_
- `c5.12xlarge` (base: aws)
- `c5.4xlarge` (base: aws)
- `c5d.9xlarge` (base: aws)
- `g4dn.xlarge` (base: aws)
- `inf1.2xlarge` (base: aws, inferentia)
- `inf1.xlarge` (base: aws, inferentia)
- `inf2.8xlarge` (base: aws, inferentia)
- `inf2.xlarge` (base: aws, inferentia)
- `m7g.2xlarge` (base: aws, arm64, graviton)
- `m7g.xlarge` (base: aws, arm64, graviton)
- `t2.#` _(# can be substituted dynamically)_ (base: aws)
- `t2.2xlarge` (base: aws)
- `t2.large` (base: aws)
- `t2.medium` (base: aws)
- `t2.micro` (base: aws)
- `t2.nano` (base: aws)
- `t2.small` (base: aws)
- `t2.xlarge` (base: aws)

### Cloud-provider

- `aws` (default)
- `gcp`

### Gcp-instance-image

- `debian-cloud/debian-11`
- `gcp_instance_image.#` _(# can be substituted dynamically)_
- `ubuntu-2204-jammy-v20230114`

### Gcp-instance-type

- `f1-micro` (base: gcp)
- `gcp_instance_type.#` _(# can be substituted dynamically)_
- `n1-highmem.#` _(# can be substituted dynamically)_ (base: gcp)
- `n1-standard.#` _(# can be substituted dynamically)_ (base: gcp)

### Gcp-project

- `gcp_project.#` _(# can be substituted dynamically)_

### Instance-name

- `instance_name.#` _(# can be substituted dynamically)_

### Platform

- `arm64`
- `x86` (default)

### Region

- `region.#` _(# can be substituted dynamically)_
- `us-west-2`

### Storage-size

- `storage_size.#` _(# can be substituted dynamically)_
- `storage_size.8`

### Ungrouped

- `amazon-linux-2-kernel.#` _(# can be substituted dynamically)_
- `graviton`
- `inferentia`
- `rhel.#` _(# can be substituted dynamically)_
- `ubuntu.#` _(# can be substituted dynamically)_

### Zone

- `zone.#` _(# can be substituted dynamically)_
