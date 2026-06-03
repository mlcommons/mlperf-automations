# get-mlperf-multi-node-system-info

`get-mlperf-multi-node-system-info` collects hardware and software details from one or more nodes via SSH and writes a structured `system_desc.json` file for MLPerf submissions. It runs `get-mlperf-single-node-system-info` on each target node, merges the per-node results, and optionally retrieves serving framework configuration from the inference server's startup log.

## Prerequisites

- **mlcflow installed and mlperf-automations pulled** — see the [mlcflow installation guide](https://docs.mlcommons.org/mlcflow/install/).
- **SSH key-based access** to every target node. Password-based auth is not supported. Copy your public key to each node before running:
  ```bash
  ssh-copy-id user@host
  ```

## Usage

### Basic example

Collect system info from two remote nodes with a CUDA backend:

```bash
mlcr get-mlperf-multi-node-system-info,_cuda \
  --ssh_ids=user@node1:22,user@node2:22 \
  --out_dir_path=/tmp/sysinfo \
  --out_file_name=system_desc.json
```

### Excluding the current (orchestrator) node

Use `_exclude_current_node` when the machine running this command is not part of the cluster (e.g. a head/login node):

```bash
mlcr get-mlperf-multi-node-system-info,_cuda,_exclude_current_node \
  --ssh_ids=user@node1:22,user@node2:22 \
  --out_dir_path=/tmp/sysinfo
```

Without this tag, the local machine is treated as node 0 and its info is collected first.

### With node_config (function-based groupings)

For disaggregated inference setups (e.g. separate Prefill and Decode nodes), pass a `node_config_file` to declare the topology. The script validates the declared counts against what was actually probed:

```bash
mlcr get-mlperf-multi-node-system-info,_cuda,_exclude_current_node \
  --ssh_ids=user@prefill1:22,user@prefill2:22,user@decode1:22 \
  --out_dir_path=/tmp/sysinfo \
  --node_config_file=/path/to/node_config.yaml
```

See [node_config Reference](#node_config-reference) for the file format.

### With serving configuration extraction

To also capture the inference server's configuration (tensor/pipeline parallelism, batch size, framework version), provide either `--serving_node` + `--log_path` (reads the server startup log) or `--endpoint_url` (HTTP probe):

```bash
mlcr get-mlperf-multi-node-system-info,_cuda,_exclude_current_node \
  --ssh_ids=user@node1:22,user@node2:22 \
  --out_dir_path=/tmp/sysinfo \
  --serving_node=user@node1:22 \
  --log_path=/tmp/vllm.log \
  --endpoint_url=http://node1:8000
```

`--endpoint_url` is probed via HTTP to detect the serving framework name and version (e.g. `vLLM 0.9.0`). `--serving_node` + `--log_path` is used to extract parallelism settings from the startup log. Both are optional and independent.

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--ssh_ids` | **Required.** Comma-separated SSH targets. Format: `user@host` or `user@host:port`. | — |
| `--out_dir_path` | Directory where the output JSON is written. | current directory |
| `--out_file_name` | Output file name. | `system_desc.json` |
| `--skip_ssh_key_file` | Skip mlcflow's SSH key file lookup; use pre-configured key auth. | `False` |
| `--node_config_file` | Path to a YAML file declaring function-based node groupings. | — |
| `--serving_node` | SSH target of the inference server (`user@host:port`). When set, the script SSHes in to extract serving config from the startup log. | — |
| `--log_path` | Path to the vLLM or SGLang server log **on the serving node**. Required when `--serving_node` is set and serving config extraction is desired. | — |
| `--endpoint_url` | Base URL of the running inference server. The script issues an HTTP probe to detect the serving framework and version. | — |
| `--serving_framework_type` | Serving framework hint (`vllm`, `sglang`). Used when the framework cannot be detected automatically. | — |

## node_config Reference

`node_config_file` is an optional YAML that groups nodes by function (e.g. Prefill / Decode in disaggregated setups). When provided, the script validates that every declared GPU type and count matches what was actually probed over SSH.

**Format:**

```yaml
system_info:
  node_config:
    Prefill:
      - node_name: H100      # case-insensitive substring of the detected GPU model name
        no_of_nodes: 2
    Decode:
      - node_name: H100
        no_of_nodes: 5
```

**Validation rules:**

- Every `node_name` must match at least one probed node's GPU model string (case-insensitive substring). An unmatched name causes the script to fail with an error.
- For each unique `node_name`, the total `no_of_nodes` across all function groups must not exceed the count of nodes of that type actually probed. Declaring more nodes than were SSHed into is an error.

## Output

The script writes `system_desc.json` to `--out_dir_path`. The top-level structure follows the MLPerf submission schema:

```json
{
  "system_under_test": {
    "system_size": "8x NVIDIA H100 80GB HBM3",
    "node_types": [
      {
        "hardware_ensemble": { ... },
        "software_ensemble": { ... },
        ...
      }
    ]
  }
}
```

The full path to the generated file is also returned in the `MLC_MULTI_NODE_SYSTEM_INFO_FILE_PATH` environment variable, which downstream scripts can consume.

## Variations

| Tag | Effect |
|-----|--------|
| `_cuda` | Selects CUDA as the accelerator backend (NVIDIA GPUs). |
| `_rocm` | Selects ROCm as the accelerator backend (AMD GPUs). |
| `_xpu` | Selects XPU as the accelerator backend (Intel GPUs). |
| `_exclude_current_node` | Skips collecting info from the machine running this command. Use when the orchestrator is not part of the inference cluster. |

Specify `_cuda`, `_rocm`, or `_xpu` to match your hardware. If none is given, no backend-specific collection is performed.
