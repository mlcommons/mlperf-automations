# run-apptainer-container

Run a command or MLC script inside an Apptainer (formerly Singularity) container.

## Supported Platforms

- **Linux** (x86_64, aarch64, ppc64le) — native Apptainer support
- **macOS** — via Lima VM or Vagrant (Apptainer does not run natively on macOS)
- **Windows** — via WSL2 (Apptainer does not run natively on Windows)

## Usage

### Run from a local SIF image

```bash
mlcr run,apptainer,container --image=my_image.sif --run_cmd="echo hello"
```

### Run from a Docker Hub image

```bash
mlcr run,apptainer,container --docker_image=ubuntu:22.04 --run_cmd="cat /etc/os-release"
```

### Run with NVIDIA GPU support

```bash
mlcr run,apptainer,container --image=my_image.sif --nv=yes --run_cmd="nvidia-smi"
```

### Run with AMD ROCm GPU support

```bash
mlcr run,apptainer,container --image=my_image.sif --rocm=yes --run_cmd="rocm-smi"
```

### Run with bind mounts

```bash
mlcr run,apptainer,container --image=my_image.sif --bind="/data:/mnt/data" --run_cmd="ls /mnt/data"
```

### Run an MLC script inside the container

```bash
mlcr run,apptainer,container --image=my_image.sif --script_tags="run,mlperf,inference"
```

### Run as a writable sandbox

```bash
mlcr run,apptainer,container --docker_image=ubuntu:22.04 --sandbox=yes --writable=yes --run_cmd="apt-get update"
```

## Input Flags

| Flag | Env Variable | Description |
|------|-------------|-------------|
| `--image` | `MLC_APPTAINER_IMAGE` | Path to a local SIF or sandbox |
| `--image_url` | `MLC_APPTAINER_IMAGE_URL` | Remote image URI (`library://`, `oras://`, `https://`) |
| `--docker_image` | `MLC_APPTAINER_FROM_DOCKER` | Docker image reference to pull and convert |
| `--sandbox` | `MLC_APPTAINER_SANDBOX` | Build a writable sandbox from the image |
| `--sandbox_path` | `MLC_APPTAINER_SANDBOX_PATH` | Path for the sandbox directory |
| `--writable` | `MLC_APPTAINER_WRITABLE` | Run with `--writable` (requires sandbox) |
| `--writable_tmpfs` | `MLC_APPTAINER_WRITABLE_TMPFS` | Run with `--writable-tmpfs` (default: yes) |
| `--cleanenv` | `MLC_APPTAINER_CLEANENV` | Run with `--cleanenv` (default: yes) |
| `--nv` | `MLC_APPTAINER_NV` | Enable NVIDIA GPU support (`--nv`) |
| `--rocm` | `MLC_APPTAINER_ROCM` | Enable AMD ROCm GPU support (`--rocm`) |
| `--bind` | `MLC_APPTAINER_BIND_MOUNTS` | Bind mount paths (`host:container`) |
| `--overlay` | `MLC_APPTAINER_OVERLAY` | Overlay image path |
| `--fakeroot` | `MLC_APPTAINER_FAKEROOT` | Use `--fakeroot` for unprivileged builds |
| `--no_home` | `MLC_APPTAINER_NO_HOME` | Do not mount home directory |
| `--contain` | `MLC_APPTAINER_CONTAIN` | Use minimal `/dev` and empty other directories |
| `--containall` | `MLC_APPTAINER_CONTAINALL` | Contain everything (PID, IPC, environment) |
| `--home` | `MLC_APPTAINER_HOME` | Custom home directory inside container |
| `--pwd` | `MLC_APPTAINER_PWD` | Initial working directory inside container |
| `--env_vars` | `MLC_APPTAINER_ENV_VARS` | Environment variables to pass (`KEY=VAL`) |
| `--extra_args` | `MLC_APPTAINER_EXTRA_ARGS` | Extra arguments to `apptainer exec` |
| `--run_cmd` | `MLC_APPTAINER_RUN_CMD` | Command to run inside the container |
| `--script_tags` | `MLC_APPTAINER_RUN_SCRIPT_TAGS` | MLC script tags to run inside the container |
| `--pre_run_cmds` | `MLC_APPTAINER_PRE_RUN_COMMANDS` | Commands to run before the main command |
| `--post_run_cmds` | `MLC_APPTAINER_POST_RUN_COMMANDS` | Commands to run after the main command |
| `--save_script` | `MLC_APPTAINER_SAVE_SCRIPT` | Save the launch command to a script file |

## Dependencies

- `get-apptainer` — ensures Apptainer is installed
