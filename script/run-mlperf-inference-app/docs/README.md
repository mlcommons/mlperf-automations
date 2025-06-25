# README for run-mlperf-inference-app
This README is automatically generated. Please follow the [script execution document](https://docs.mlcommons.org/mlcflow/targets/script/execution-flow/) to understand more about the MLC script execution.

## Run Commands

```bash
    mlcr run-mlperf,inference
```
### Script Inputs

| Name | Description | Default | Type |
|------|-------------|---------|------|
| `division` | MLPerf division | `open` | str |
| `category` | MLPerf category | `edge` | str |
| `device` | MLPerf device | `cpu` | str |
| `model` | MLPerf model | `resnet50` | str |
| `precision` | MLPerf model precision | `` | str |
| `implementation` | MLPerf implementation | `mlcommons-python` | str |
| `backend` | MLPerf framework (backend) | `onnxruntime` | str |
| `scenario` | MLPerf scenario | `Offline` | str |
| `mode` | MLPerf benchmark mode | `` | str |
| `execution_mode` | MLPerf execution mode | `test` | str |
| `sut` | SUT configuration (if known) | `` | str |
| `submitter` | Submitter name (without space) | `CTuning` | str |
| `results_dir` | Folder path to store results (defaults to the current working directory) | `` | str |
| `submission_dir` | Folder path to store MLPerf submission tree | `` | str |
| `power` | Measure power | `no` | str |
| `adr.mlperf-power-client.power_server` | MLPerf Power server IP address | `192.168.0.15` | str |
| `adr.mlperf-power-client.port` | MLPerf Power server port | `4950` | int |
| `adr.compiler.tags` | Compiler for loadgen and any C/C++ part of implementation | `` | str |
| `adr.inference-src-loadgen.env.MLC_GIT_URL` | Git URL for MLPerf inference sources to build LoadGen (to enable non-reference implementations) | `` | str |
| `adr.inference-src.env.MLC_GIT_URL` | Git URL for MLPerf inference sources to run benchmarks (to enable non-reference implementations) | `` | str |
| `adr.mlperf-inference-implementation.max_batchsize` | Maximum batchsize to be used | `` | str |
| `adr.mlperf-inference-implementation.num_threads` | Number of threads (reference & C++ implementation only) | `` | str |
| `adr.python.name` | Python virtual environment name (optional) | `` | str |
| `adr.python.version` | Force Python version (must have all system deps) | `` | str |
| `adr.python.version_min` | Minimal Python version | `3.8` | str |
| `clean` | Clean run | `False` | bool |
| `compliance` | Whether to run compliance tests (applicable only for closed division) | `no` | str |
| `dashboard_wb_project` | W&B dashboard project | `` | str |
| `dashboard_wb_user` | W&B dashboard user | `` | str |
| `hw_name` | MLPerf hardware name (for example "gcp.c3_standard_8", "nvidia_orin", "lenovo_p14s_gen_4_windows_11", "macbook_pro_m1_2", "thundercomm_rb6" ...) | `` | str |
| `multistream_target_latency` | Set MultiStream target latency | `` | str |
| `offline_target_qps` | Set LoadGen Offline target QPS | `` | str |
| `quiet` | Quiet run (select default values for all questions) | `True` | bool |
| `server_target_qps` | Set Server target QPS | `` | str |
| `singlestream_target_latency` | Set SingleStream target latency | `` | str |
| `target_latency` | Set Target latency | `` | str |
| `target_qps` | Set LoadGen target QPS | `` | str |
| `j` | Print results dictionary to console at the end of the run | `False` | bool |
| `repro` | Record input/output/state/info files to make it easier to reproduce results | `False` | bool |
| `time` | Print script execution time at the end of the run | `True` | bool |
| `debug` | Debug this script | `False` | bool |### Generic Script Inputs

| Name | Description | Default | Type |
|------|-------------|---------|------|
| `input` | Input to the script passed using the env key `MLC_INPUT` | `` | str |
| `output` | Output from the script passed using the env key `MLC_OUTPUT` | `` | str |
| `outdirname` | The directory to store the script output | `cache directory ($HOME/MLC/repos/local/cache/<>) if the script is cacheable or else the current directory` | str |
| `outbasename` | The output file/folder name | `` | str |
| `name` |  | `` | str |
| `extra_cache_tags` | Extra cache tags to be added to the cached entry when the script results are saved | `` | str |
| `skip_compile` | Skip compilation | `False` | bool |
| `skip_run` | Skip run | `False` | bool |
| `accept_license` | Accept the required license requirement to run the script | `False` | bool |
| `skip_system_deps` | Skip installing any system dependencies | `False` | bool |
| `git_ssh` | Use SSH for git repos | `False` | bool |
| `gh_token` | Github Token | `` | str |
| `hf_token` | Huggingface Token | `` | str |
| `verify_ssl` | Verify SSL | `False` | bool |
