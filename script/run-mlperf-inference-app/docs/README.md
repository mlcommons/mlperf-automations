# README for run-mlperf-inference-app
This README is automatically generated. Please follow the [script execution document](https://docs.mlcommons.org/mlcflow/targets/script/execution-flow/) to understand more about the MLC script execution.

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
| `--backend` | MLPerf framework (backend) | ['onnxruntime', 'tf', 'pytorch', 'deepsparse', 'tensorrt', 'glow', 'tvm-onnx'] | `onnxruntime` |
| `--scenario` | MLPerf scenario | ['Offline', 'Server', 'SingleStream', 'MultiStream'] | `Offline` |
| `--mode` | MLPerf benchmark mode | ['', 'accuracy', 'performance'] | `` |
| `--execution_mode` | MLPerf execution mode | ['test', 'fast', 'valid'] | `test` |
| `--sut` | SUT configuration (if known) |  | `` |
| `--submitter` | Submitter name (without space) |  | `MLCommons` |
| `--results_dir` | Folder path to store results (defaults to the current working directory) |  | `` |
| `--submission_dir` | Folder path to store MLPerf submission tree |  | `` |
| `--power` | Measure power | ['yes', 'no'] | `no` |
| `--adr.mlperf-power-client.power_server` | MLPerf Power server IP address |  | `192.168.0.15` |
| `--adr.mlperf-power-client.port` | MLPerf Power server port |  | `4950` |
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
