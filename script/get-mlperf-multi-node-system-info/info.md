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
| `accelerator_interconnect_topology` | string | auto | Topology of the accelerator interconnect: `"Mesh"` (all pairs NVLink), `"Direct"` (PCIe-only or partial), or omitted for single GPU. Derived from `nvidia-smi topo -m`. |
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

### Accelerator backend (mutually exclusive)

| Tag | Effect |
|-----|--------|
| `_cuda` | Selects CUDA as the accelerator backend (NVIDIA GPUs). |
| `_rocm` | Selects ROCm as the accelerator backend (AMD GPUs). |
| `_xpu` | Selects XPU as the accelerator backend (Intel GPUs). |

Specify one of `_cuda`, `_rocm`, or `_xpu` to match your hardware. If none is given, no backend-specific collection is performed.

### MLPerf benchmark (mutually exclusive)

| Tag | Effect |
|-----|--------|
| `_inference` | Produces a flat `system_desc_id.json`-compatible output for MLPerf Inference submissions (see [Inference submission format](#inference-submission-format)). |
| `_endpoints` | Produces the nested format used for MLPerf Inference Endpoints submissions. |

### Stackable modifiers

| Tag | Effect |
|-----|--------|
| `_exclude_current_node` | Skips collecting info from the machine running this command. Use when the orchestrator is not part of the inference cluster. |
| `_network` | Adds the Network division extra fields (`is_network`, `network_type`, `network_media`, etc.) to the output. Stack with `_inference`. |
| `_power` | Adds the power submission extra fields (`power_supply_quantity_and_rating_watts`, `power_supply_details`, `boot_firmware_version`, etc.) to the output as blank strings for manual entry. Stack with `_inference`. |
| `_redfish` | Runs [`get-redfish-power-info`](../get-redfish-power-info/README.md) as a `prehook_dep` to capture live PSU data from a Redfish BMC/mockup endpoint. On its own, just produces a raw capture YAML in the output dir for reference. |
| `_inference_optional_nameplate` | Produces the nameplate power YAML the MLPerf Inference submission_checker optionally accepts (see [Nameplate power YAML](#nameplate-power-yaml-_redfish_inference_optional_nameplate)). Stacked with `_redfish`, it's populated with real PSU data from the BMC; used **alone**, it writes the generic fill-in-the-blanks skeleton template instead — no BMC is contacted. |

### Example: inference submission with power fields

```bash
mlcr get-mlperf-multi-node-system-info,_cuda,_inference,_power \
  --ssh_ids=user@node1:22,user@node2:22 \
  --out_dir_path=/tmp/sysinfo \
  --system_name="My System"
```

### Example: skeleton nameplate power template (no BMC)

```bash
mlcr get-mlperf-multi-node-system-info,_inference,_inference_optional_nameplate \
  --out_dir_path=/tmp/sysinfo \
  --system_name="My System"
```

### Example: nameplate power YAML populated from a Redfish BMC

```bash
mlcr get-mlperf-multi-node-system-info,_inference,_redfish,_inference_optional_nameplate \
  --out_dir_path=/tmp/sysinfo \
  --system_name="My System" \
  --redfish_endpoint=https://bmc.example.com \
  --redfish_username=admin \
  --redfish_password=secret
```

## Nameplate power YAML (`_redfish`,`_inference_optional_nameplate`)

`_inference_optional_nameplate` is unrelated to the `_power` variation above
— `_power` only adds blank text fields to `system_desc.json` for manual
entry, whereas `_inference_optional_nameplate` produces a real, separate
YAML file: the PSU nameplate/design-power declaration consumed by
`nameplate_power_check` in the MLPerf Inference `submission_checker`
(`tools/submission/submission_checker/checks/system_check.py` in the
`inference` repo). That checker sums `PowerCapacityWatts` across the
`Min PSUs Needed` largest PSUs per leaf node and expects the file at
`systems/<system_desc_id>_power.yaml` (`NAMEPLATE_POWER_PATH` in
`submission_checker/constants.py`, required starting `v6.1`).

**Two modes, depending on whether `_redfish` is also active:**

| Your tags | What gets written |
|---|---|
| `_inference_optional_nameplate` alone | The **generic skeleton template** verbatim from the optional power template in `tools/submission/submission_structure.md` — placeholder `My Rack 1` / `My Server 1` / `My Switch 1` labels, `PSU 1`/`PSU 2` at 1200W each, `Description: 'Optional Description'`. No BMC is contacted at all — the `get-redfish-power-info` dependency doesn't even run. Fill in the real numbers by hand. |
| `_redfish,_inference_optional_nameplate` | The **real** PSU data captured live from the Redfish BMC (see mapping below) |

**Data source and mapping (when `_redfish` is also active):**

| Nameplate field | Redfish source |
|---|---|
| `PSUs[].Name` / `PowerCapacityWatts` | `Chassis/<id>/PowerSubsystem/PowerSupplies/<bay>` (preferred) or the legacy `Chassis/<id>/Power` → `PowerSupplies[]` (fallback, when a BMC only implements the older schema) |
| `Min PSUs Needed` | `Chassis/<id>/PowerSubsystem` → `PowerSupplyRedundancy[].MinNeededInGroup`, when the BMC reports it; otherwise conservatively defaults to the number of installed PSUs (no redundancy credit) |

**What this does NOT give you automatically, even with real BMC data:**
Redfish has no concept of rack/system grouping above a chassis — each
chassis becomes one flat leaf under `<system_name>`. If you want an
explicit rack layer in between (as shown in the skeleton template), edit
the generated YAML by hand after generation.

**Output:** written to `<out_dir_path>/<system_name with spaces replaced
by _>_power.yaml`, and its path is reported via
`MLC_NAMEPLATE_POWER_YAML_FILE_PATH`. This script has no concept of the
submission's actual `<system_desc_id>` (only the human-readable
`--system_name`), so you still need to copy/rename the file into your
submission's `systems/` directory to match whatever `hw_name` that
submission uses — the same manual step already required for the main
`system_desc.json` output.

**Which `get-redfish-power-info` scope actually runs:** the dependency is
wired as two mutually exclusive `prehook_deps` entries, gated so that
neither runs unless `_redfish` is active:

| Your tags | `get-redfish-power-info` invocation |
|---|---|
| `_inference_optional_nameplate` alone | Neither — no BMC contact, skeleton template written directly by `postprocess()` |
| `_redfish` alone | `_full` scope — complete chassis+systems+thermal capture, no nameplate file |
| `_redfish,_inference_optional_nameplate` | `_inference_optional_nameplate` scope — lean PSU-only walk (no Thermal, no Systems), only produces the nameplate YAML |

Output paths (`MLC_REDFISH_OUTPUT_FILE`/`MLC_REDFISH_NAMEPLATE_OUTPUT_FILE`/
`MLC_REDFISH_SYSTEM_NAME`) are passed explicitly via `env:` templating in
`meta.yaml`, since they need to be derived from this script's own paths.
Connection args (`redfish_endpoint`/`username`/`password`) are **not**
re-templated — both scripts use the identical env var names
(`MLC_REDFISH_ENDPOINT`/`USERNAME`/`PASSWORD`), so they pass through via
ordinary env inheritance instead. (Self-referential templates like
`MLC_REDFISH_ENDPOINT: <<<MLC_REDFISH_ENDPOINT>>>` don't resolve in this
engine — they're left as a literal string — so don't add those.)

**Additional inputs (all optional; only relevant with `_redfish`):**

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--redfish_endpoint` | Redfish base URL. | `http://localhost:8000` |
| `--redfish_username` | BMC username. Leave unset for an unauthenticated mockup. | — |
| `--redfish_password` | BMC password. | — |

Every actual HTTP request to the BMC is made through the DMTF `redfishtool`
CLI (installed automatically as a pip dependency), not direct HTTP calls —
see [get-redfish-power-info's README](../get-redfish-power-info/README.md)
for details. `redfishtool` always skips TLS certificate verification
internally, so there is no separate "insecure" option to configure here.

For local testing without real hardware, point `--redfish_endpoint` at a
[DMTF Redfish-Mockup-Server](https://github.com/DMTF/Redfish-Mockup-Server)
instance — see the "Local testing" section in
[get-redfish-power-info's README](../get-redfish-power-info/README.md).

## Inference submission format

When the `_inference` variation is active, the script produces a flat JSON that matches the `system_desc_id.json` schema required by the MLPerf Inference submission checker, instead of the default nested format.

Field name remappings applied at this stage:

| Nested field | Flat field |
|---|---|
| `submitter_org_names` | `submitter` |
| `system_availability_status` | `status` |
| `system_category` | `system_type` |
| `serving_framework` | `framework` |

Hardware fields from `node_types` entries are lifted to the top level. For heterogeneous multi-node systems (different GPU or CPU types across nodes), unique values are comma-separated within each field.

Fields that cannot be auto-detected and require manual input are present in the output as empty strings:

| Field | Why manual |
|---|---|
| `host_networking_topology` | Physical topology (ring, fat-tree, etc.) requires human knowledge. |
| `system_type_detail` | Subcategory (cloud, on-premise, edge-server, etc.) requires human knowledge. |

The `accelerator_interconnect_topology` field is auto-derived from `nvidia-smi topo -m`:

| Value | Meaning |
|---|---|
| `"Mesh"` | All GPU pairs connected via NVLink (fully connected). |
| `"Direct"` | PCIe-only or partial NVLink connections. |
| omitted | Single GPU — no inter-GPU topology to describe. |

### Example flat output (`_inference`)

```json
{
  "submitter": "MLCommons",
  "system_name": "8x NVIDIA H100 80GB HBM3",
  "status": "available",
  "system_type": "datacenter",
  "division": "open",
  "number_of_nodes": 2,
  "host_processor_model_name": "Intel(R) Xeon(R) Platinum 8480+",
  "host_processors_per_node": "2",
  "host_processor_core_count": "112",
  "host_processor_vcpu_count": "224",
  "host_memory_capacity": "2.2T",
  "host_storage_type": "NVMe SSD",
  "host_storage_capacity": "1.8 TB NVMe SSD",
  "host_networking": "mlx5_0: native InfiniBand",
  "host_network_card_count": "3x mlx5_0",
  "host_networking_topology": "",
  "accelerator_model_name": "NVIDIA H100 80GB HBM3",
  "accelerators_per_node": "8",
  "accelerator_memory_capacity": "80GiB",
  "accelerator_memory_configuration": "80 GiB HBM3",
  "accelerator_host_interconnect": "PCIe Gen5 x16",
  "accelerator_interconnect": "NVLink",
  "accelerator_interconnect_topology": "Mesh",
  "accelerator_frequency": "",
  "accelerator_on-chip_memories": "Shared Memory: 228 KB/block",
  "framework": "vLLM 0.9.0",
  "operating_system": "ubuntu 24.04",
  "other_software_stack": "CUDA 12.9, Driver 575.57.08",
  "cooling": "",
  "hw_notes": "",
  "sw_notes": "",
  "other_hardware": "",
  "system_type_detail": ""
}
```
