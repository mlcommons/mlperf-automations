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

The script writes `system_desc.json` to `--out_dir_path`. The full path is also returned in the `MLC_MULTI_NODE_SYSTEM_INFO_FILE_PATH` environment variable for downstream scripts.

### system_desc.json Schema

The file has five top-level sections. All string fields default to an empty string when not detected; fields marked **(auto)** are computed by the script and must not be set manually.

---

#### `organization_metadata`

Submitter identity and submission lifecycle dates.

| Field | Type | Description |
|-------|------|-------------|
| `submitter_org_name` | string | Full legal name of the submitting organization. CLI: `--submitter_org_name` |
| `submitter_contact` | string | Contact email for submission queries. CLI: `--submitter_contact` |
| `submission_id` | string | Unique identifier for this submission (e.g. `"v07_test"`). CLI: `--submission_id` |
| `submission_date` | string | ISO-8601 date the submission was filed (e.g. `"2025-06-01"`). CLI: `--submission_date` |
| `publish_date` | string | ISO-8601 date results are expected to be published. CLI: `--publish_date` |

---

#### `system_under_test`

Describes the inference cluster — its metadata, per-node hardware/software details, and the serving framework.

##### `system_under_test.system_metadata`

| Field | Type | Description |
|-------|------|-------------|
| `system_name` | string | Human-readable name for the system (e.g. `"4x Intel Arc B70"`). CLI: `--system_name`. Falls back to the auto-computed `system_size` string if not provided. |
| `system_category` | string | `"datacenter"` or `"edge"`. CLI: `--category` |
| `system_availability_status` | string | `"available"`, `"preview"`, or `"rdi"`. CLI: `--status` |
| `system_size` | string | **(auto)** Compact hardware summary, e.g. `"8x NVIDIA H100 80GB HBM3"`. Computed from probed node details; override with `--system_size`. |
| `system_node_ensemble_count` | integer | **(auto)** Number of distinct node-type entries in `node_types`. |
| `system_node_ensemble_total` | integer | **(auto)** Total number of physical nodes across all entries (sum of `number_of_nodes`). |

##### `system_under_test.serving_framework`

| Field | Type | Description |
|-------|------|-------------|
| `serving_framework` | string | Serving framework name and version (e.g. `"vLLM 0.9.0"`). Auto-detected via HTTP probe (`--endpoint_url`) or startup log (`--serving_node` + `--log_path`). |

##### `system_under_test.node_types`

Array of node-type objects. Each entry represents one *type* of node in the cluster; homogeneous clusters have exactly one entry. When `--node_config_file` is used, entries are shaped by the declared function groups (e.g. Prefill / Decode). Without it, entries are grouped by detected hardware identity.

Each entry has the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `system_node_ensemble_id` | integer | **(auto)** 0-based index (no YAML) or 1-based ensemble counter (with YAML). |
| `number_of_nodes` | integer | **(auto)** Count of physical nodes of this type. |
| `hardware_ensemble` | object | Hardware details for this node type — see below. |
| `software_ensemble` | object | Software stack details for this node type — see below. |

###### `hardware_ensemble.processor`

CPU details, collected automatically via SSH.

| Field | Type | Description |
|-------|------|-------------|
| `host_processor_model_name` | string | CPU model string (e.g. `"Intel(R) Xeon(R) 698X"`). |
| `host_processors_per_node` | integer | Number of CPU sockets per node. |
| `host_processor_core_count` | integer | Total physical cores per node. |
| `host_processor_vcpu_count` | integer | Total logical (hyper-threaded) cores per node. |

###### `hardware_ensemble.host_memory`

| Field | Type | Description |
|-------|------|-------------|
| `host_memory_capacity` | string | Total RAM (e.g. `"134G"`). |
| `host_memory_configuration` | string | DIMM layout (e.g. `"8 x 16GB DDR5-6400"`). |

###### `hardware_ensemble.accelerator`

GPU / accelerator details, collected automatically. Fields show `"Not available"` when no accelerator is detected.

| Field | Type | Description |
|-------|------|-------------|
| `accelerator_model_name` | string | GPU product name (e.g. `"NVIDIA H100 80GB HBM3"`). |
| `accelerators_per_node` | integer | Number of GPUs per node. |
| `accelerator_memory_capacity` | string | Per-GPU memory, rounded to marketed GiB (e.g. `"80GiB"`). |
| `accelerator_memory_type` | string | Memory technology (e.g. `"HBM3"`, `"GDDR6"`). |
| `accelerator_interconnect` | string | GPU-to-GPU interconnect (e.g. `"NVLink"`, `"Not available"`). |
| `accelerator_host_interconnect` | string | GPU-to-CPU interconnect (e.g. `"PCIe 5.0 x16"`). |

###### `hardware_ensemble.networking`

| Field | Type | Description |
|-------|------|-------------|
| `host_networking` | string | Primary network type (e.g. `"Ethernet"`, `"InfiniBand"`). |
| `host_network_card_count` | string | NIC count and type (e.g. `"3x Ethernet"`). |

###### `hardware_ensemble.storage`

| Field | Type | Description |
|-------|------|-------------|
| `host_storage_capacity` | string | Total disk capacity (e.g. `"1.8 TB NVMe SSD"`). |
| `host_storage_type` | string | Storage technology (e.g. `"NVMe SSD"`). |

###### `hardware_ensemble` — top-level optional fields

These are injected from CLI flags and apply uniformly to every node type.

| Field | Type | Description |
|-------|------|-------------|
| `other_hardware` | string | Any additional hardware not captured above. CLI: `--other_hardware` |
| `hw_notes` | string | Free-form hardware notes. CLI: `--hw_notes` |
| `cooling` | string | Cooling solution description (e.g. `"air"`, `"liquid"`). CLI: `--cooling` |

###### `software_ensemble`

Software stack details per node type, collected automatically.

| Field | Type | Description |
|-------|------|-------------|
| `inference_backend` | string | Compute runtime (e.g. `"CUDA 12.4, cuDNN 9.1"`). Auto-detected. |
| `driver` | string | GPU driver version. Auto-detected. |
| `operating_system` | string | OS string (e.g. `"linux debian ubuntu 24.04"`). Auto-detected. |
| `filesystem` | string | Filesystem types present (e.g. `"ext4 vfat"`). Auto-detected. |
| `container_link` | string | URL to the inference container image (optional). CLI: via `--container_link` env. |
| `other_software_stack` | string | Additional software not captured above (optional). |
| `sw_notes` | string | Free-form software notes (optional). |

> **Note:** `serving_framework` is a system-level property and is moved to `system_under_test.serving_framework`. It is removed from per-node `software_ensemble` during post-processing to avoid duplication.

---

#### `model_metadata`

Describes the model used in this submission.

| Field | Type | Description |
|-------|------|-------------|
| `division` | string | MLPerf division (e.g. `"datacenter"`). CLI: `--division` |
| `model_id` | string | HuggingFace model ID (e.g. `"meta-llama/Llama-3.1-8b-instruct"`). CLI: `--model_id` |
| `model_name` | string | Human-readable model name (e.g. `"Llama 3.1 8B Instruct"`). CLI: `--model_name` |
| `model_precision` | string | Inference precision (e.g. `"FP16"`, `"W4A8"`). CLI: `--model_precision` |
| `link_to_model` | string | URL to the model weights or card. CLI: `--link_to_model` |
| `link_to_model_transformation` | string | URL describing any quantization or transformation applied. CLI: `--link_to_model_transformation` |
| `model_notes` | string | Free-form notes about the model or transformations applied. CLI: `--model_notes` |

---

#### `dataset_metadata`

Describes the evaluation dataset.

| Field | Type | Description |
|-------|------|-------------|
| `dataset_id` | string | Dataset identifier (e.g. `"cnn_dailymail"`). CLI: `--dataset_id` |
| `dataset_name` | string | Human-readable dataset name (e.g. `"CNN/DailyMail"`). CLI: `--dataset_name` |
| `input_token_average` | string | Average input token count (e.g. `"870"`). CLI: `--input_token_average` |
| `output_token_average` | string | Average output token count (e.g. `"128"`). CLI: `--output_token_average` |
| `dataset_type` | string | `"performance"` or `"accuracy"`. CLI: `--dataset_type` |
| `dataset_link` | string | URL to the dataset. CLI: `--link_to_dataset` |

---

#### `accuracy`

| Field | Type | Description |
|-------|------|-------------|
| `measured_accuracy_score` | string | The measured accuracy value (e.g. `"38.7287"`). |

---

### Template — fill in the fields marked "Insert …"

The script auto-populates all hardware and software fields. Fields that still say `"Insert … here"` must be filled in manually before submitting.

```json
{
  "organization_metadata": {
    "submitter_org_name": "Insert your organization name here",
    "submitter_contact": "Insert a contact email here",
    "submission_id": "Insert submission ID here",
    "submission_date": "",
    "publish_date": ""
  },
  "system_under_test": {
    "system_metadata": {
      "system_category": "Insert system category here",
      "system_availability_status": "Insert system availability status here",
      "system_size": "8x NVIDIA H100 80GB HBM3",
      "system_node_ensemble_count": 1,
      "system_node_ensemble_total": 1,
      "system_name": "8x NVIDIA H100 80GB HBM3"
    },
    "node_types": [
      {
        "system_node_ensemble_id": 0,
        "number_of_nodes": 1,
        "hardware_ensemble": {
          "processor": {
            "host_processor_model_name": "Intel(R) Xeon(R) Platinum 8480+",
            "host_processors_per_node": 2,
            "host_processor_core_count": 112,
            "host_processor_vcpu_count": 224
          },
          "host_memory": {
            "host_memory_capacity": "2.2T",
            "host_memory_configuration": "Not available"
          },
          "accelerator": {
            "accelerator_model_name": "NVIDIA H100 80GB HBM3",
            "accelerators_per_node": 8,
            "accelerator_memory_capacity": "80GiB",
            "accelerator_memory_type": "HBM3",
            "accelerator_interconnect": "NVLink",
            "accelerator_host_interconnect": "PCIe Gen5 x16"
          },
          "networking": {
            "host_network_card_count": "3x mlx5_0: native InfiniBand",
            "host_networking": "mlx5_0: native InfiniBand"
          },
          "storage": {
            "host_storage_capacity": "1.1 GB NVMe SSD, 1.8 TB SSD",
            "host_storage_type": "NVMe SSD"
          },
          "other_hardware": "",
          "hw_notes": "",
          "cooling": ""
        },
        "software_ensemble": {
          "inference_backend": "CUDA 12.9",
          "driver": "Driver 575.57.08",
          "operating_system": "linux debian ubuntu 24.04",
          "filesystem": "ext4 vfat zfs",
          "container_link": "",
          "other_software_stack": null,
          "sw_notes": null
        }
      }
    ],
    "serving_framework": "vLLM 0.22.0"
  },
  "model_metadata": {
    "division": "Insert model division here",
    "model_id": "Insert model id here",
    "model_name": "Insert model name here",
    "model_precision": "Insert model precision here",
    "link_to_model": "Insert link to model here",
    "link_to_model_transformation": "Insert link to model transformations here",
    "model_notes": "Insert any relevant notes about the model here"
  },
  "dataset_metadata": {
    "dataset_id": "Insert dataset name here",
    "dataset_name": "Insert dataset name here",
    "input_token_average": "Insert dataset input token average here",
    "output_token_average": "Insert dataset output token average here",
    "dataset_type": "Insert dataset type here",
    "dataset_link": "Insert link to dataset here"
  },
  "accuracy": {
    "measured_accuracy_score": ""
  }
}
```

## Variations

| Tag | Effect |
|-----|--------|
| `_cuda` | Selects CUDA as the accelerator backend (NVIDIA GPUs). |
| `_rocm` | Selects ROCm as the accelerator backend (AMD GPUs). |
| `_xpu` | Selects XPU as the accelerator backend (Intel GPUs). |
| `_exclude_current_node` | Skips collecting info from the machine running this command. Use when the orchestrator is not part of the inference cluster. |

Specify `_cuda`, `_rocm`, or `_xpu` to match your hardware. If none is given, no backend-specific collection is performed.
