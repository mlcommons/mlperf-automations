# generate-mlperf-endpoints-system-desc

Generates the `system_desc.json` (§8.2 system description) required by an
MLPerf Endpoints submission. It declares the **Maximum Supported Concurrency M**
(which defines the concurrency regions), the submitter/system metadata, and the
per-node hardware/software stack.

```bash
mlcr generate,mlperf,endpoints-system-desc \
  --org="Acme" --system_name="acme_h100x8" \
  --max_supported_concurrency=1024 \
  --availability=available --division=standardized \
  --accelerator_model_name="NVIDIA H100" --accelerators_per_node=8 \
  --host_processor_model_name="AMD EPYC 9004" \
  --inference_backend=vllm --operating_system="Ubuntu 22.04" \
  --model_name="meta-llama/Llama-3.1-8B-Instruct" --dataset_name=open_orca \
  --system_desc_path=./system_desc.json
```

## Key inputs

| Input | Required | Notes |
|---|---|---|
| `--org` | yes (defaults to placeholder + warning) | submitter organization |
| `--system_name` | yes (placeholder + warning) | becomes the submission system id |
| `--max_supported_concurrency` | yes (defaults to 64 + warning) | **must be > 32**; defines regions |
| `--availability` | no | `available` (default) / `preview` / `rdi` |
| `--division` | no | `standardized` (default) / `serviced` / `rdi` |
| `--system_category` | no | default `datacenter` |
| `--accelerator_model_name`, `--accelerators_per_node`, `--host_processor_model_name`, `--number_of_nodes`, `--inference_backend`, `--operating_system`, `--driver` | no | per-node hardware/software (a single `node_types` entry) |
| `--model_name`, `--model_precision`, `--dataset_name`, `--serving_framework` | no | model / dataset metadata |
| `--system_desc_path` / `--output` | no | output path (default `./system_desc.json`) |

Placeholder defaults let a smoke test run with no arguments, but the script warns
which fields you must fill in before a real submission.

## Output

| Env key | Meaning |
|---|---|
| `MLC_MLPERF_ENDPOINTS_SYSTEM_DESC_PATH` | path to the generated `system_desc.json` |

The output validates against the submission checker's `SystemDescription` schema.
