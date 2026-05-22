# README for run-vllm-server
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
mlcr run,server,vllm,vllm-server
```

### Script Inputs

| Name | Description | Choices | Default |
|------|-------------|---------|------|
| `--allow_credentials` |  |  | `` |
| `--allowed_headers` |  |  | `` |
| `--allowed_methods` |  |  | `` |
| `--allowed_origins` |  |  | `` |
| `--api_key` |  |  | `` |
| `--block_size` |  |  | `` |
| `--chat_template` |  |  | `` |
| `--code_revision` |  |  | `` |
| `--device` |  |  | `` |
| `--disable_custom_all_reduce` |  |  | `` |
| `--disable_log_requests` |  |  | `` |
| `--disable_log_stats` |  |  | `` |
| `--disable_sliding_window` |  |  | `` |
| `--distributed-executor-backend` |  |  | `` |
| `--download_dir` |  |  | `` |
| `--dtype` |  |  | `` |
| `--enable_chunked_prefill` |  |  | `` |
| `--enable_lora` |  |  | `` |
| `--enable_prefix_caching` |  |  | `` |
| `--enable_prompt_adapter` |  |  | `` |
| `--enforce_eager` |  |  | `` |
| `--engine_use_ray` |  |  | `` |
| `--fully_sharded_loras` |  |  | `` |
| `--gpu_memory_utilization` |  |  | `` |
| `--guided_decoding_backend` |  |  | `` |
| `--host` |  |  | `` |
| `--kv_cache_dtype` |  |  | `` |
| `--load_format` |  |  | `` |
| `--long_lora_scaling_factors` |  |  | `` |
| `--lora_dtype` |  |  | `` |
| `--lora_extra_vocab_size` |  |  | `` |
| `--lora_modules` |  |  | `` |
| `--max_context_len_to_capture` |  |  | `` |
| `--max_cpu_loras` |  |  | `` |
| `--max_log_len` |  |  | `` |
| `--max_logprobs` |  |  | `` |
| `--max_lora_rank` |  |  | `` |
| `--max_loras` |  |  | `` |
| `--max_model_len` |  |  | `` |
| `--max_num_batched_tokens` |  |  | `` |
| `--max_num_seqs` |  |  | `` |
| `--max_parallel_loading_workers` |  |  | `` |
| `--max_prompt_adapter_token` |  |  | `` |
| `--max_prompt_adapters` |  |  | `` |
| `--max_seq_len_to_capture` |  |  | `` |
| `--middleware` |  |  | `` |
| `--model` |  |  | `` |
| `--model_loader_extra_config` |  |  | `` |
| `--ngram_prompt_lookup_max` |  |  | `` |
| `--ngram_prompt_lookup_min` |  |  | `` |
| `--num_gpu_blocks_override` |  |  | `` |
| `--num_lookahead_slots` |  |  | `` |
| `--num_speculative_tokens` |  |  | `` |
| `--otlp_traces_endpoint` |  |  | `` |
| `--pipeline_parallel_size` |  |  | `` |
| `--port` |  |  | `` |
| `--pp_size` |  |  | `` |
| `--preemption_mode` |  |  | `` |
| `--prompt_adapters` |  |  | `` |
| `--qlora_adapter_name_or_path` |  |  | `` |
| `--quantization` |  |  | `` |
| `--quantization_param_path` |  |  | `` |
| `--ray_workers_use_nsight` |  |  | `` |
| `--response_role` |  |  | `` |
| `--revision` |  |  | `` |
| `--root_path` |  |  | `` |
| `--rope_scaling` |  |  | `` |
| `--rope_theta` |  |  | `` |
| `--scheduler_delay_factor` |  |  | `` |
| `--seed` |  |  | `` |
| `--served_model_name` |  |  | `` |
| `--skip_docker_model_download` |  |  | `` |
| `--skip_tokenizer_init` |  |  | `` |
| `--spec_decoding_acceptance_method` |  |  | `` |
| `--speculative_disable_by_batch_size` |  |  | `` |
| `--speculative_draft_tensor_parallel_size` |  |  | `` |
| `--speculative_max_model_len` |  |  | `` |
| `--speculative_model` |  |  | `` |
| `--ssl_ca_certs` |  |  | `` |
| `--ssl_cert_reqs` |  |  | `` |
| `--ssl_certfile` |  |  | `` |
| `--ssl_keyfile` |  |  | `` |
| `--swap_space` |  |  | `` |
| `--tokenizer` |  |  | `` |
| `--tokenizer_mode` |  |  | `` |
| `--tokenizer_pool_extra_config` |  |  | `` |
| `--tokenizer_pool_size` |  |  | `` |
| `--tokenizer_pool_type` |  |  | `` |
| `--tokenizer_revision` |  |  | `` |
| `--tp_size` |  |  | `` |
| `--trust_remote_code` |  |  | `` |
| `--typical_acceptance_sampler_posterior_alpha` |  |  | `` |
| `--typical_acceptance_sampler_posterior_threshold` |  |  | `` |
| `--use_v2_block_manager` |  |  | `` |
| `--uvicorn_log_level` |  |  | `` |
| `--worker_use_ray` |  |  | `` |
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
