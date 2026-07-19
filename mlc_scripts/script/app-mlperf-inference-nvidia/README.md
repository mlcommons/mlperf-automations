# README for app-mlperf-inference-nvidia
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
mlcr reproduce,mlcommons,mlperf,inference,harness,nvidia-harness,nvidia
```

### Script Inputs

| Name | Description | Choices | Default |
|------|-------------|---------|------|
| `--audio_buffer_num_lines` |  |  | `` |
| `--count` |  |  | `` |
| `--deque_timeout_usec` |  |  | `` |
| `--devices` |  |  | `` |
| `--dla_batch_size` |  |  | `` |
| `--dla_copy_streams` |  |  | `` |
| `--dla_inference_streams` |  |  | `` |
| `--embedding_weights_on_gpu_part` |  |  | `` |
| `--enable_sort` |  |  | `` |
| `--end_on_device` |  |  | `` |
| `--extra_run_options` |  |  | `` |
| `--gpu_batch_size` |  |  | `` |
| `--gpu_copy_streams` |  |  | `` |
| `--gpu_inference_streams` |  |  | `` |
| `--graphs_max_seqlen` |  |  | `` |
| `--input_format` |  |  | `` |
| `--log_dir` |  |  | `` |
| `--make_cmd` |  |  | `` |
| `--max_batchsize` |  |  | `` |
| `--max_dlas` |  |  | `` |
| `--mlperf_conf` |  |  | `` |
| `--mode` |  |  | `performance` |
| `--multistream_target_latency` |  |  | `` |
| `--num_issue_query_threads` |  |  | `` |
| `--num_sort_segments` |  |  | `` |
| `--num_warmups` |  |  | `` |
| `--offline_target_qps` |  |  | `` |
| `--output_dir` |  |  | `` |
| `--performance_sample_count` |  |  | `` |
| `--power_setting` |  |  | `` |
| `--rerun` |  |  | `` |
| `--run_infer_on_copy_streams` |  |  | `` |
| `--scenario` |  |  | `Offline` |
| `--sdxl_batcher_time_limit` |  |  | `` |
| `--server_target_qps` |  |  | `` |
| `--singlestream_target_latency` |  |  | `` |
| `--skip_postprocess` |  |  | `` |
| `--skip_preprocess` |  |  | `no` |
| `--skip_preprocessing` | Alias for skip_preprocess |  | `` |
| `--soft_drop` |  |  | `` |
| `--start_from_device` |  |  | `` |
| `--target_latency` |  |  | `` |
| `--target_qps` |  |  | `` |
| `--use_cuda_thread_per_device` |  |  | `` |
| `--use_deque_limit` |  |  | `` |
| `--use_fp8` |  |  | `` |
| `--use_graphs` |  |  | `` |
| `--use_small_tile_gemm_plugin` |  |  | `` |
| `--use_triton` |  |  | `` |
| `--user_conf` |  |  | `` |
| `--workspace_size` |  |  | `` |
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

### Backend

- `tensorrt` (default)

### Batch-size

- `batch_size.#` _(# can be substituted dynamically)_

### Batchsize-format-change

- `pre5.0`
- `v5.0+`

### Build-engine-options

- `build_engine_options.#` _(# can be substituted dynamically)_

### Device

- `cpu`
- `cuda` (default)

### Device-memory

- `gpu_memory.#` _(# can be substituted dynamically)_
- `gpu_memory.16`
- `gpu_memory.24`
- `gpu_memory.32`
- `gpu_memory.40`
- `gpu_memory.48`
- `gpu_memory.8`
- `gpu_memory.80`

### Dla-batch-size

- `dla_batch_size.#` _(# can be substituted dynamically)_

### Gpu-connection

- `pcie`
- `sxm`

### Gpu-name

- `a100`
- `a6000`
- `custom`
- `l4`
- `orin`
- `rtx_4090`
- `rtx_6000_ada`
- `t4`

### Graphs

- `use-graphs`

### Loadgen-scenario

- `multistream`
- `offline`
- `server`
- `singlestream`

### Model

- `3d-unet-99` (base: 3d-unet_)
- `3d-unet-99.9` (base: 3d-unet_)
- `bert-99` (base: bert_)
- `bert-99.9` (base: bert_)
- `dlrm-v2-99` (base: dlrm_)
- `dlrm-v2-99.9` (base: dlrm_)
- `gptj-99` (base: gptj_)
- `gptj-99.9` (base: gptj_)
- `llama2-70b-99` (base: llama2-70b_)
- `llama2-70b-99.9` (base: llama2-70b_)
- `resnet50` (default)
- `retinanet`
- `rnnt`
- `sdxl`

### Num-gpus

- `num-gpus.#` _(# can be substituted dynamically)_
- `num-gpus.1` (default)

### Power-mode

- `maxn`
- `maxq`

### Run-mode

- `build`
- `build_engine` (alias: build-engine)
- `calibrate`
- `download_model`
- `prebuild`
- `preprocess_data` (alias: preprocess-data)
- `run_harness` (alias: run-harness) (default)

### Triton

- `use_triton`

### Ungrouped

- `3d-unet_`
- `bert_`
- `dlrm_`
- `env`
- `gptj_`
- `llama2-70b_`
- `v3.1` (base: pre5.0)

### Version

- `v4.0` (base: pre5.0)
- `v4.1` (base: pre5.0)
- `v4.1-dev` (base: pre5.0) (default)
- `v5.0` (base: v5.0+)
- `v5.1` (base: v5.0+)
