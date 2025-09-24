# README for run-mlperf-inference-app
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
mlcr run-mlperf,inference
```

### Script Inputs

| Name | Description | Choices | Default |
|------|-------------|---------|------|
| `--division` | MLPerf division | ['open', 'closed'] | `open` |
| `--category` | MLPerf category | ['edge', 'datacenter', 'network'] | `edge` |
| `--device` | MLPerf device | ['cpu', 'cuda', 'rocm', 'qaic'] | `cpu` |
| `--model` | MLPerf model | ['resnet50', 'retinanet', 'bert-99', 'bert-99.9', '3d-unet-99', '3d-unet-99.9', 'rnnt', 'dlrm-v2-99', 'dlrm-v2-99.9', 'gptj-99', 'gptj-99.9', 'sdxl', 'llama2-70b-99', 'llama2-70b-99.9', 'mixtral-8x7b', 'mobilenet', 'efficientnet', 'rgat', 'llama3_1-405b', 'pointpainting'] | `resnet50` |
| `--precision` | MLPerf model precision | ['float32', 'float16', 'bfloat16', 'int8', 'uint8'] | `` |
| `--implementation` | MLPerf implementation | ['mlcommons-python', 'mlcommons-cpp', 'nvidia', 'intel', 'qualcomm', 'ctuning-cpp-tflite'] | `reference` |
| `--backend` | MLPerf framework (backend) | ['onnxruntime', 'tf', 'pytorch', 'deepsparse', 'tensorrt', 'glow', 'tvm-onnx'] | `` |
| `--scenario` | MLPerf scenario | ['Offline', 'Server', 'SingleStream', 'MultiStream'] | `Offline` |
| `--mode` | MLPerf benchmark mode | ['', 'accuracy', 'performance'] | `` |
| `--execution_mode` | MLPerf execution mode | ['test', 'fast', 'valid'] | `test` |
| `--sut` | SUT configuration (if known) |  | `` |
| `--submitter` | Submitter name (without space) |  | `MLCommons` |
| `--submission_dir` | Folder path to store MLPerf submission tree |  | `` |
| `--power` | Measure power | ['yes', 'no'] | `no` |
| `--adr.mlperf-power-client.power_server` | MLPerf Power server IP address |  | `192.168.0.15` |
| `--adr.mlperf-power-client.port` | MLPerf Power server port |  | `4950` |
| `--results_dir` | Alias for output_dir |  | `` |
| `--use_dataset_from_host` | Run the dataset download script on the host machine and mount the dataset into the Docker container to avoid repeated downloads. | [True, False] | `no` |
| `--use_model_from_host` | Run the model download script on the host machine and mount the model files into the Docker container to avoid repeated downloads. | [True, False] | `no` |
| `--adr.compiler.tags` | Compiler for loadgen and any C/C++ part of implementation |  | `` |
| `--adr.inference-src-loadgen.env.MLC_GIT_URL` | Git URL for MLPerf inference sources to build LoadGen (to enable non-reference implementations) |  | `` |
| `--adr.inference-src.env.MLC_GIT_URL` | Git URL for MLPerf inference sources to run benchmarks (to enable non-reference implementations) |  | `` |
| `--adr.mlperf-inference-implementation.max_batchsize` | Maximum batchsize to be used |  | `` |
| `--adr.mlperf-inference-implementation.num_threads` | Number of threads (reference & C++ implementation only) |  | `` |
| `--adr.python.name` | Python virtual environment name (optional) |  | `` |
| `--adr.python.version` | Force Python version (must have all system deps) |  | `` |
| `--adr.python.version_min` | Minimal Python version |  | `3.8` |
| `--clean` | Clean run |  | `False` |
| `--compliance` | Whether to run compliance tests (applicable only for closed division) | ['yes', 'no'] | `no` |
| `--hw_name` | MLPerf hardware name (for example "gcp.c3_standard_8", "nvidia_orin", "lenovo_p14s_gen_4_windows_11", "macbook_pro_m1_2", "thundercomm_rb6" ...) |  | `` |
| `--multistream_target_latency` | Set MultiStream target latency |  | `` |
| `--offline_target_qps` | Set LoadGen Offline target QPS |  | `` |
| `--quiet` | Quiet run (select default values for all questions) |  | `True` |
| `--server_target_qps` | Set Server target QPS |  | `` |
| `--singlestream_target_latency` | Set SingleStream target latency |  | `` |
| `--target_latency` | Set Target latency |  | `` |
| `--target_qps` | Set LoadGen target QPS |  | `` |
| `--repro` | Record input/output/state/info files to make it easier to reproduce results |  | `False` |
| `--time` | Print script execution time at the end of the run |  | `True` |
| `--debug` | Debug this script |  | `False` |
| `--api_server` |  |  | `` |
| `--batch_size` |  |  | `` |
| `--beam_size` |  |  | `` |
| `--custom_system_nvidia` |  |  | `` |
| `--dashboard_wb_project` |  |  | `` |
| `--dashboard_wb_user` |  |  | `` |
| `--dlrm_data_path` |  |  | `` |
| `--docker` |  |  | `` |
| `--dump_version_info` |  |  | `` |
| `--save_console_log` |  |  | `` |
| `--find_performance` |  |  | `` |
| `--framework` | Alias for backend |  | `` |
| `--status` |  |  | `` |
| `--docker_keep_alive` |  |  | `` |
| `--get_platform_details` |  |  | `` |
| `--gpu_name` |  |  | `` |
| `--pip_loadgen` |  |  | `` |
| `--hw_notes_extra` |  |  | `` |
| `--imagenet_path` |  |  | `` |
| `--lang` | Alias for implementation |  | `` |
| `--min_duration` |  |  | `` |
| `--min_query_count` |  |  | `` |
| `--max_query_count` |  |  | `` |
| `--network` |  |  | `` |
| `--nvidia_system_name` |  |  | `` |
| `--output_dir` |  |  | `` |
| `--output_summary` |  |  | `` |
| `--output_tar` |  |  | `` |
| `--performance_sample_count` |  |  | `` |
| `--preprocess_submission` |  |  | `` |
| `--push_to_github` |  |  | `` |
| `--pull_changes` |  |  | `` |
| `--pull_inference_changes` |  |  | `` |
| `--readme` |  |  | `` |
| `--regenerate_accuracy_file` |  |  | `` |
| `--regenerate_files` |  |  | `` |
| `--rerun` |  |  | `` |
| `--results_git_url` |  |  | `` |
| `--run_checker` |  |  | `` |
| `--run_style` | Alias for execution_mode |  | `` |
| `--skip_submission_generation` |  |  | `False` |
| `--skip_truncation` |  |  | `` |
| `--sut_servers` |  |  | `` |
| `--sw_notes_extra` | Alias for hw_notes_extra |  | `` |
| `--system_type` | Alias for category |  | `` |
| `--test_query_count` |  |  | `` |
| `--threads` |  |  | `` |
| `--nvidia_llama2_dataset_file_path` |  |  | `` |
| `--tp_size` |  |  | `` |
| `--vllm_tp_size` |  |  | `1` |
| `--vllm_model_name` |  |  | `` |
| `--num_workers` |  |  | `` |
| `--max_test_duration` |  |  | `` |
| `--all_models` |  |  | `` |
| `--criteo_day23_raw_data_path` |  |  | `` |
| `--rgat_checkpoint_path` |  |  | `` |
| `--pointpainting_checkpoint_path` |  |  | `` |
| `--deeplab_resnet50_path` |  |  | `` |
| `--waymo_path` |  |  | `` |
| `--nm_model_zoo_stub` |  |  | `` |
| `--use_service_account` |  |  | `` |
| `--client_id` |  |  | `` |
| `--client_secret` |  |  | `` |
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

### Benchmark-version

- `r2.1`
- `r3.0`
- `r3.1`
- `r4.0`
- `r4.0-dev`
- `r4.1`
- `r4.1-dev`
- `r5.0`
- `r5.0-dev`
- `r5.1`
- `r5.1-dev` (default)

### Mode

- `all-modes`

### Submission-generation

- `accuracy-only`
- `find-performance`
- `performance-and-accuracy` (base: all-modes) (default)
- `performance-only`
- `populate-readme` (base: all-modes)
- `submission` (base: all-modes)

### Submission-generation-style

- `full`
- `short` (default)

### Ungrouped

- `all-scenarios`
- `compliance`
- `scc24-base` (base: short)
- `scc24-main` (base: short)
