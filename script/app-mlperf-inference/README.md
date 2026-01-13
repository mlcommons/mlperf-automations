# README for app-mlperf-inference
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
mlcr app,vision,language,mlcommons,mlperf,inference,generic
```

### Script Inputs

| Name | Description | Choices | Default |
|------|-------------|---------|------|
| `--scenario` | MLPerf inference scenario | ['Offline', 'Server', 'SingleStream', 'MultiStream'] | `Offline` |
| `--mode` | MLPerf inference mode | ['performance', 'accuracy'] | `accuracy` |
| `--test_query_count` | Specifies the number of samples to be processed during a test run |  | `10` |
| `--target_qps` | Target QPS |  | `` |
| `--target_latency` | Target Latency |  | `` |
| `--max_batchsize` | Maximum batchsize to be used |  | `` |
| `--num_threads` | Number of CPU threads to launch the application with |  | `` |
| `--hw_name` | Hardware part of the SUT name |  | `` |
| `--output_dir` | Location where the outputs are produced |  | `` |
| `--rerun` | Redo the run even if previous run files exist |  | `True` |
| `--regenerate_files` | Regenerates measurement files including accuracy.txt files even if a previous run exists. This option is redundant if `--rerun` is used |  | `` |
| `--adr.python.name` | Python virtual environment name (optional) |  | `mlperf` |
| `--adr.python.version_min` | Minimal Python version |  | `3.8` |
| `--adr.python.version` | Force Python version (must have all system deps) |  | `` |
| `--adr.compiler.tags` | Compiler for loadgen |  | `gcc` |
| `--adr.inference-src-loadgen.env.MLC_GIT_URL` | Git URL for MLPerf inference sources to build LoadGen (to enable non-reference implementations) |  | `` |
| `--adr.inference-src.env.MLC_GIT_URL` | Git URL for MLPerf inference sources to run benchmarks (to enable non-reference implementations) |  | `` |
| `--quiet` | Quiet run (select default values for all questions) |  | `False` |
| `--readme` | Generate README with the reproducibility report |  | `` |
| `--debug` | Debug MLPerf script |  | `` |
| `--count` |  |  | `` |
| `--docker` |  |  | `` |
| `--imagenet_path` |  |  | `` |
| `--power` |  |  | `` |
| `--power_server` |  |  | `` |
| `--ntp_server` |  |  | `` |
| `--max_amps` |  |  | `` |
| `--max_volts` |  |  | `` |
| `--clean` |  |  | `` |
| `--offline_target_qps` |  |  | `` |
| `--server_target_qps` |  |  | `` |
| `--singlestream_target_latency` |  |  | `` |
| `--multistream_target_latency` |  |  | `` |
| `--gpu_name` |  |  | `` |
| `--tp_size` |  |  | `2` |
| `--pp_size` |  |  | `1` |
| `--use_dataset_from_host` |  |  | `` |
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

### Backend

- `deepsparse`
- `glow`
- `ncnn`
- `onnxruntime`
- `openshift`
- `pytorch`
- `ray`
- `sglang`
- `tensorrt`
- `tf` (alias: tensorflow)
- `tflite`
- `tvm-onnx` (base: batch_size.1)
- `tvm-pytorch` (base: batch_size.1)
- `tvm-tflite` (base: batch_size.1)
- `vllm`

### Batch_size

- `batch_size.#` _(# can be substituted dynamically)_

### Device

- `cpu` (default)
- `cuda`
- `qaic`
- `rocm`
- `tpu`

### Execution-mode

- `fast`
- `test` (default)
- `valid`

### Implementation

- `amd`
- `cpp` (alias: mil, mlcommons-cpp)
- `intel-original` (alias: intel)
- `kilt` (alias: qualcomm)
- `nvidia-original` (alias: nvidia)
- `redhat`
- `reference` (alias: mlcommons-python, neuralmagic, python) (default)
- `tflite-cpp` (alias: ctuning-cpp-tflite)

### Loadgen-scenario

- `multistream`
- `offline` (default)
- `server`
- `singlestream`

### Model

- `3d-unet-99` (base: 3d-unet_)
- `3d-unet-99.9` (base: 3d-unet_)
- `bert-99` (base: bert_)
- `bert-99.9` (base: bert_)
- `deepseek-r1`
- `dlrm-v2-99` (base: dlrm_)
- `dlrm-v2-99.9` (base: dlrm_)
- `efficientnet`
- `gptj-99` (base: gptj_)
- `gptj-99.9` (base: gptj_)
- `llama2-70b-99` (base: llama2-70b_)
- `llama2-70b-99.9` (base: llama2-70b_)
- `llama3_1-405b`
- `llama3_1-8b_`
- `mixtral-8x7b` (base: mixtral-8x7b)
- `mobilenet`
- `pointpainting`
- `resnet50` (default)
- `retinanet`
- `rgat`
- `rnnt`
- `sdxl`
- `whisper`

### Precision

- `bfloat16`
- `float16`
- `float32` (alias: fp32) (default)
- `float4` (alias: fp4)
- `float8` (alias: fp8)
- `int4`
- `int8` (alias: quantized)
- `uint8`

### Reproducibility

- `r2.1_default`
- `r3.0_default`
- `r3.1_default`
- `r4.0-dev_default`
- `r4.0_default`
- `r4.1-dev_default`
- `r4.1_default`
- `r5.0-dev_default`
- `r5.0_default`
- `r5.1-dev_default`
- `r5.1_default`
- `r6.0-dev_default`

### Ungrouped

- `3d-unet_`
- `all-models`
- `bert_`
- `dlrm_`
- `gptj_` (alias: gptj)
- `llama2-70b_`
- `llama3_1-8b` (base: llama3_1-8b_)
- `llama3_1-8b-edge` (base: llama3_1-8b_)
- `power`
