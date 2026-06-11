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
  --endpoint_url=http://node1:8000
```

`--endpoint_url` is probed via HTTP to detect the serving framework name and version (e.g. `vLLM 0.9.0`). `--serving_node` + `--log_path` is used to extract parallelism settings from the startup log. Both are optional and independent. If `--log_path` is not provided, it defaults to `/tmp/serving.log` on the serving node — redirect your server's stdout/stderr there before running:

```bash
python -m vllm.entrypoints.openai.api_server ... > /tmp/serving.log 2>&1 &
```

## Parameters

### Infrastructure

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--config_file` | Path to a JSON or YAML file supplying submission/model/dataset metadata (see [Config file](#config-file)). Individual CLI args take precedence over values in this file. | — |
| `--ssh_ids` | **Required.** Comma-separated SSH targets. Format: `user@host` or `user@host:port`. | — |
| `--out_dir_path` | Directory where the output JSON is written. | current directory |
| `--out_file_name` | Output file name. | `system-info-multi-node.json` |
| `--skip_ssh_key_file` | Skip mlcflow's SSH key file lookup; use pre-configured key auth. | `False` |
| `--node_config_file` | Path to a YAML file declaring function-based node groupings. | — |
| `--serving_node` | SSH target of the inference server (`user@host:port`). When set, the script SSHes in to extract serving config from the startup log. | — |
| `--log_path` | Path to the serving framework log **on the serving node**. Used to extract parallelism config (tensor/pipeline/expert/data parallelism, batch size) from the startup output. Supported frameworks: **vLLM**, **SGLang**, **TRT-LLM**. If not provided, defaults to `/tmp/serving.log`. | `/tmp/serving.log` |
| `--endpoint_url` | Base URL of the running inference server. The script issues an HTTP probe to detect the serving framework and version. | — |
| `--serving_framework_type` | Serving framework hint (`vllm`, `sglang`, `trtllm`). Used when the framework cannot be detected automatically. | — |

### Submission metadata

| Parameter | Type | Description |
|-----------|------|-------------|
| `--submitter_org_name` | string | Submitting organization name. |
| `--submitter_contact` | string | Contact email for submission queries. |
| `--system_name` | string | **Required.** Human-readable name for the system under test (e.g. `"8x NVIDIA H100 80GB HBM3"`). |
| `--category` | string | System category (e.g. `"datacenter"`). |
| `--status` | string | System availability status (e.g. `"available"`). |
| `--division` | string | Submission division (e.g. `"open"`, `"closed"`). |

### Model metadata

| Parameter | Type | Description |
|-----------|------|-------------|
| `--model_id` | string | Model identifier (e.g. `"llama2-70b"`). |
| `--model_name` | string | Human-readable model name. |
| `--model_precision` | string | Numerical precision used (e.g. `"fp8"`, `"int4"`). |
| `--link_to_model` | string | URL pointing to the model weights or registry entry. |
| `--link_to_model_transformation` | string | URL describing any model transformations applied (quantization, pruning, etc.). |
| `--model_notes` | string | Free-form notes about the model. |

### Dataset metadata

| Parameter | Type | Description |
|-----------|------|-------------|
| `--dataset_id` | string | Dataset identifier. |
| `--dataset_name` | string | Human-readable dataset name. |
| `--dataset_type` | string | Dataset type (e.g. `"synthetic"`, `"real"`). |
| `--input_token_average` | string | Average number of input tokens per sample. |
| `--output_token_average` | string | Average number of output tokens per sample. |
| `--link_to_dataset` | string | URL pointing to the dataset. |

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

The script writes `system-info-multi-node.json` to `--out_dir_path`. All fields are at the top level — there are no nested section wrappers:

```json
{
  "submitter_org_names": "MLCommons",
  "submitter_contact": "contact@example.com",
  "submission_id": "",
  "submission_date": "",
  "publish_date": "",

  "system_name": "8x NVIDIA H100 80GB HBM3",
  "system_category": "datacenter",
  "system_availability_status": "available",
  "system_size": "8x NVIDIA H100 80GB HBM3",
  "system_node_ensemble_count": 1,
  "system_node_ensemble_total": 1,
  "serving_framework": "vLLM 0.9.0",

  "node_types": [
    {
      "system_node_ensemble_id": 0,
      "number_of_nodes": 1,
      "host_processor_model_name": "Intel(R) Xeon(R) Platinum 8480+",
      "host_processors_per_node": 2,
      "host_processor_core_count": 112,
      "host_processor_vcpu_count": 224,
      "host_memory_capacity": "2.2T",
      "host_memory_configuration": "Not available",
      "accelerator_model_name": "NVIDIA H100 80GB HBM3",
      "accelerators_per_node": 8,
      "accelerator_memory_capacity": "80GiB",
      "accelerator_memory_type": "HBM3",
      "accelerator_interconnect": "NVLink",
      "accelerator_host_interconnect": "PCIe Gen5 x16",
      "host_network_card_count": "3x mlx5_0",
      "host_networking": "mlx5_0: native InfiniBand",
      "host_storage_capacity": "1.1 GB NVMe SSD, 1.8 TB SSD",
      "host_storage_type": "NVMe SSD",
      "other_hardware": "",
      "hw_notes": "",
      "cooling": "",
      "inference_backend": "CUDA 12.9",
      "driver": "Driver 575.57.08",
      "operating_system": "ubuntu 24.04",
      "filesystem": "ext4 vfat zfs",
      "container_link": "",
      "other_software_stack": "CUDA 12.9, Driver 575.57.08",
      "sw_notes": null
    }
  ],

  "division": "open",
  "model_id": "llama2-70b",
  "model_name": "Llama 2 70B",
  "model_precision": "fp8",
  "link_to_model": "...",
  "link_to_model_transformation": "...",
  "model_notes": "",

  "dataset_id": "openorca",
  "dataset_name": "Open Orca",
  "input_token_average": "128",
  "output_token_average": "256",
  "dataset_type": "real",
  "dataset_link": "...",

  "measured_accuracy_score": ""
}
```

The full path to the generated file is also returned in the `MLC_MULTI_NODE_SYSTEM_INFO_FILE_PATH` environment variable, which downstream scripts can consume.

### Output fields

**Manual** fields must be supplied via `--config_file` or CLI args. **Auto** fields are detected or computed by the script and do not need user input. Manual fields are listed first in each table since those require user attention.

#### Top-level fields

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `submitter_org_names` | string | **manual** | Submitting organization name. |
| `submitter_contact` | string | **manual** | Contact email for submission queries. |
| `system_name` | string | **manual** (required) | Human-readable system name (e.g. `"8x NVIDIA H100 80GB HBM3"`). Script exits with an error if not provided. |
| `system_category` | string | **manual** | System category (e.g. `"datacenter"`, `"edge"`). |
| `system_availability_status` | string | **manual** | Availability status (e.g. `"available"`, `"preview"`). |
| `division` | string | **manual** | Submission division (`"open"` or `"closed"`). |
| `model_id` | string | **manual** | Model identifier (e.g. `"llama2-70b"`). |
| `model_name` | string | **manual** | Human-readable model name. |
| `model_precision` | string | **manual** | Numerical precision (e.g. `"fp8"`, `"int4"`). |
| `link_to_model` | string | **manual** | URL to model weights or registry entry. |
| `link_to_model_transformation` | string | **manual** | URL describing quantization or other transformations applied. |
| `model_notes` | string | **manual** | Free-form notes about the model. |
| `dataset_id` | string | **manual** | Dataset identifier. |
| `dataset_name` | string | **manual** | Human-readable dataset name. |
| `dataset_type` | string | **manual** | Dataset type (`"real"` or `"synthetic"`). |
| `input_token_average` | string | **manual** | Average input tokens per sample. |
| `output_token_average` | string | **manual** | Average output tokens per sample. |
| `dataset_link` | string | **manual** | URL to the dataset. |
| `measured_accuracy_score` | string | **manual** | Measured accuracy result (populated post-run). |
| `submission_id` | string | auto (infra) | Populated by submission infrastructure; left empty by this script. |
| `submission_date` | string | auto (infra) | Populated by submission infrastructure; left empty by this script. |
| `publish_date` | string | auto (infra) | Populated by submission infrastructure; left empty by this script. |
| `system_size` | string | auto | Computed as `(nodes × accelerators_per_node)x accelerator_model_name` per node type, joined with ` + `. |
| `system_node_ensemble_count` | int | auto | Number of distinct node types in the system. |
| `system_node_ensemble_total` | int | auto | Total number of nodes across all node types. |
| `serving_framework` | string | auto | Detected serving framework name and version. Auto-detected via HTTP probe (`--endpoint_url`) or startup log (`--serving_node` + `--log_path`). Supported frameworks: **vLLM**, **SGLang**, **TRT-LLM**. Can also be set manually via `--serving_framework`. |

#### Per-node fields (`node_types` entries)

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `other_hardware` | string | **manual** | Any additional hardware not captured above. |
| `hw_notes` | string | **manual** | Free-form hardware notes. |
| `cooling` | string | **manual** | Cooling solution description. |
| `container_link` | string | **manual** | URL to the container image used. |
| `other_software_stack` | string | auto | Compute software stack combining the inference backend (CUDA/ROCm + cuDNN) and GPU driver (e.g. `"CUDA 12.9, Driver 575.57.08"`). `null` if nothing is detected. |
| `sw_notes` | string | **manual** | Free-form software notes. |
| `system_node_ensemble_id` | int | auto | Zero-based index for this node type entry. |
| `number_of_nodes` | int | auto | Number of identical nodes of this type. |
| `host_processor_model_name` | string | auto | CPU model name. |
| `host_processors_per_node` | int | auto | Number of CPU sockets per node. |
| `host_processor_core_count` | int | auto | Total physical CPU cores per node. |
| `host_processor_vcpu_count` | int | auto | Total logical CPU threads per node. |
| `host_memory_capacity` | string | auto | Total host DRAM capacity. |
| `host_memory_configuration` | string | auto | Memory configuration details. |
| `accelerator_model_name` | string | auto | GPU/accelerator model name. |
| `accelerators_per_node` | int | auto | Number of accelerators per node. |
| `accelerator_memory_capacity` | string | auto | Accelerator memory per device (e.g. `"80GiB"`). |
| `accelerator_memory_type` | string | **manual** | Accelerator memory type (e.g. `"HBM3"`). |
| `accelerator_interconnect` | string | auto | Accelerator-to-accelerator interconnect (e.g. `"NVLink"`). |
| `accelerator_host_interconnect` | string | auto | Accelerator-to-host interconnect (e.g. `"PCIe Gen5 x16"`). |
| `host_network_card_count` | string | auto | Network interface summary (e.g. `"3x mlx5_0"`). |
| `host_networking` | string | auto | Network interface type and protocol. |
| `host_storage_capacity` | string | auto | Storage capacity summary. |
| `host_storage_type` | string | auto | Storage type (e.g. `"NVMe SSD"`). |
| `inference_backend` | string | auto | CUDA/ROCm runtime version, plus cuDNN version if installed. |
| `driver` | string | auto | GPU driver version. |
| `operating_system` | string | auto | OS distribution and version (e.g. `"ubuntu 24.04"`). |
| `filesystem` | string | auto | Detected filesystem types. |

## Config file

Instead of passing every metadata field on the command line, you can supply a single JSON or YAML file via `--config_file`. The file uses the same key names as the output JSON. Any field already provided as a CLI arg takes precedence over the value in the file.

```json
{
  "submitter_org_names": "MLCommons",
  "submitter_contact": "contact@example.com",

  "system_name": "8x NVIDIA H100 80GB HBM3",
  "system_category": "datacenter",
  "system_availability_status": "available",
  "serving_framework": "vLLM 0.9.0",

  "division": "open",
  "model_id": "llama2-70b",
  "model_name": "Llama 2 70B",
  "model_precision": "fp8",
  "link_to_model": "",
  "link_to_model_transformation": "",
  "model_notes": "",

  "dataset_id": "openorca",
  "dataset_name": "Open Orca",
  "dataset_type": "real",
  "input_token_average": "128",
  "output_token_average": "256",
  "dataset_link": "",

  "other_hardware": "",
  "hw_notes": "",
  "cooling": "",
  "container_link": "",
  "measured_accuracy_score": ""
}
```

Fields not present in the file and not supplied as CLI args will fall back to the placeholder defaults in the output.

## Variations

| Tag | Effect |
|-----|--------|
| `_cuda` | Selects CUDA as the accelerator backend (NVIDIA GPUs). |
| `_rocm` | Selects ROCm as the accelerator backend (AMD GPUs). |
| `_xpu` | Selects XPU as the accelerator backend (Intel GPUs). |
| `_exclude_current_node` | Skips collecting info from the machine running this command. Use when the orchestrator is not part of the inference cluster. |

Specify `_cuda`, `_rocm`, or `_xpu` to match your hardware. If none is given, no backend-specific collection is performed.
