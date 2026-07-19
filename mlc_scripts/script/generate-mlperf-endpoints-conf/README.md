# generate-mlperf-endpoints-conf

Generates a YAML configuration file for the MLCommons
[inference-endpoint](https://github.com/mlcommons/endpoints) benchmark — the
endpoints analogue of `generate-mlperf-inference-user-conf`. The generated file
is consumed by `inference-endpoint benchmark from-config` (directly, or via
`app-mlperf-inference-endpoints --config=<file>` / its `_from-config` variation).

The output is validated by the package's own schema; this script only assembles
a well-formed config from MLC inputs.

## Run

```bash
# Offline, predefined dataset (no path needed)
mlcr generate,mlperf,endpoints-conf --conf_type=offline \
  --model=meta-llama/Llama-3.1-8B-Instruct \
  --dataset_name=cnn_dailymail --dataset_preset=llama3_8b --num_samples=1000 \
  --endpoints=http://host:8000 --conf_path=run.yaml

# Online (Poisson), custom dataset path
mlcr generate,mlperf,endpoints-conf --conf_type=online --load_pattern=poisson \
  --model=my-model --dataset=/data/prompts.jsonl --prompt_column=text \
  --target_qps=100 --conf_path=run.yaml

# Accuracy-only evaluation
mlcr generate,mlperf,endpoints-conf --conf_type=eval \
  --model=meta-llama/Llama-3.1-8B-Instruct \
  --accuracy_dataset_name=gpqa --accuracy_samples=500 --eval_method=exact_match \
  --conf_path=eval.yaml

# Submission (perf + accuracy, ruleset-referenced)
mlcr generate,mlperf,endpoints-conf --conf_type=submission --benchmark_mode=offline \
  --submission_model=llama2-70b --ruleset=mlperf-inference-v5.1 \
  --model=meta-llama/Llama-2-70B-Chat-HF \
  --dataset_name=open_orca --num_samples=5000 \
  --accuracy_dataset_name=gpqa --accuracy_samples=500 --eval_method=exact_match \
  --conf_path=submission.yaml
```

## Config types (`--conf_type`)

| Type | Meaning | Datasets |
|------|---------|----------|
| `offline` (default) | Max-throughput run (`load_pattern: max_throughput`) | performance |
| `online` | Sustained load (`poisson` / `concurrency`) | performance |
| `eval` | Accuracy-only evaluation | accuracy |
| `submission` | Official run; adds `submission_ref` (model + ruleset); both perf + accuracy | performance + accuracy |

These map to the package's `TestType`. The per-run `perf`/`acc`/`both` selection
is a separate axis applied at run time (`--mode`, handled by the app).

## Datasets: predefined name **or** custom path

Each dataset entry is either:

- **Predefined** — reference by `--dataset_name` (no path required):
  `open_orca`, `cnn_dailymail`, `gpqa`, `aime25`, `livecodebench`, `random`,
  `shopify_product_catalogue`, `shopify_product_catalogue_8k`.
  A model-specific preset can be added with `--dataset_preset` (emitted as
  `name::preset`, e.g. `cnn_dailymail::llama3_8b`).
- **Custom path** — `--dataset=/path/to/file.jsonl` plus `--prompt_column` to map
  your prompt column (emitted as `parser: {prompt: <col>}`). A path is required
  whenever the name is not one of the predefined datasets.

Accuracy datasets use the same rules via `--accuracy_dataset_name` /
`--accuracy_dataset`, with `--eval_method`, `--ground_truth`, `--extractor`.

## Key inputs

| Input | Maps to |
|-------|---------|
| `--conf_type` / `--type` | `type` |
| `--model` | `model_params.name` |
| `--endpoints` | `endpoint_config.endpoints` |
| `--api_type` (`openai`/`sglang`/`videogen`), `--api_key` | `endpoint_config.*` |
| `--dataset_name` / `--dataset` / `--dataset_preset` / `--prompt_column` / `--num_samples` | performance dataset |
| `--accuracy_dataset_name` / `--accuracy_dataset` / `--eval_method` / `--ground_truth` / `--extractor` / `--accuracy_samples` | accuracy dataset |
| `--load_pattern` / `--target_qps` / `--concurrency` | `settings.load_pattern` |
| `--min_duration` / `--max_duration` (ms) / `--num_workers` | `settings.runtime` / `settings.client` |
| `--max_output_tokens` / `--temperature` / `--top_p` / `--top_k` / `--streaming` | `model_params.*` |
| `--submission_model` / `--ruleset` / `--benchmark_mode` | submission fields |
| `--conf_path` / `--output` | output YAML path |

## Output

| Env key | Meaning |
|---------|---------|
| `MLC_MLPERF_ENDPOINTS_CONF_PATH` | path to the generated YAML |

## Notes

- On non-Linux hosts the generator sets `enable_cpu_affinity: false`
  (the package's CPU pinning requires Linux and `from-config` has no CLI override).
- Rulesets currently registered in the package: `mlperf-inference-v5.1`,
  `mlcommons-current`. Submission model ids: `llama3-1-8b`, `llama2-70b`,
  `deepseek-r1`, `llama3.1-405b`, `mixtral-8x7b`.
