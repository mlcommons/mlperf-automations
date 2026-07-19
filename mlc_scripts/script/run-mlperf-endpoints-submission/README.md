# run-mlperf-endpoints-submission

End-to-end automation for producing an **MLPerf Endpoints** submission: it runs
the [inference-endpoint](https://github.com/mlcommons/endpoints) benchmark at
several concurrency points (covering the required regions), registers each run
with the [endpoints-submission-cli](https://github.com/mlcommons/endpoints-submission-cli),
and assembles + checks the submission via `submissions create --dry-run`.

> **TL;DR — smoke test (no real model, no GPU):**
> ```bash
> export PRISM_USER_API_TOKEN=mlc_...        # your PRISM API token
> mlcr run,mlperf,endpoints-submission,_echo-server,_short-run,_with-accuracy \
>   --num_points=7 --org=MyOrg --system_name=MySystem --max_supported_concurrency=64
> ```
> This launches the bundled echo server, runs 7 short concurrency points (one of
> them also measuring accuracy), uploads them as runs, and runs the submission
> checker in dry-run mode. It verifies the **whole pipeline end-to-end** — with
> the echo server this passes the structural checker, but it is **not** a real
> submission (the numbers are from an echo, not a model — see *Short run*).

---

## 1. What a valid submission requires

The rules live in the [endpoints policies](https://github.com/mlcommons/endpoints_policies)
(`endpoints_submission_rules.md`). The submission checker (bundled in the
submission CLI) enforces them. The ones that drive this automation:

| Requirement | Rule | Notes |
|---|---|---|
| **Maximum Supported Concurrency M** | §5, §7 | Declared in `system_desc.json`; **must be > 32**. Defines the regions. |
| **4 concurrency regions, each covered** | §3–§6 | At least **one measurement point in each** of: Low Latency, Low Throughput, Medium Throughput, High Throughput. |
| **7–32 measurement points total** | §2, §8 | Across all regions. |
| **Load pattern = concurrency** | §10 | Each point is a fixed-concurrency run (`--load-pattern concurrency`). |
| **Streaming on** | §13 | `stream_all_chunks` must be true → benchmark run with `--streaming on`. |
| **Per-region minimum duration** | §6.2/§11 | Low Latency ≥ 600 s; the other regions ≥ 1200 s (illustrative/WIP in the checker). |
| **Minimum query count** | §6.4/§12 | Dataset-specific (e.g. llama3-8b 13368, llama2-70b 24576, mixtral-8x7b 15000, llama3.1-405b 8313). |
| **Accuracy gate** | §15 | A run with `accuracy.txt` + `accuracy_result.json`; score ≥ the model's quality target. |
| **System description** | §8.2 | `system_desc.json` with org / system / hardware metadata. |

### Concurrency regions (§5.5)

Given M (> 32), the regions are computed log-spaced. The High Throughput region
includes a 10 % margin (`ceil(M × 1.10)`). Example for **M = 64**:

| Region | Range |
|---|---|
| Low Latency | 1–32 (always) |
| Low Throughput | 33–35 |
| Medium Throughput | 36–42 |
| High Throughput | 43–71 |

This script computes the exact ranges for your M using the official algorithm
(from the installed `submission_checker`) and auto-selects points that cover
every region. You can also pass explicit points with `--concurrencies`.

---

## 2. The automation pieces (composable)

| Script | Role |
|---|---|
| [get-mlperf-endpoints](../get-mlperf-endpoints/) | installs the benchmark (`inference-endpoint`) into a venv |
| [get-mlperf-endpoints-submission-cli](../get-mlperf-endpoints-submission-cli/) | installs `endpoints-submission-cli` (+ submission checker) into a venv |
| [generate-mlperf-endpoints-system-desc](../generate-mlperf-endpoints-system-desc/) | writes `system_desc.json` (declares M, org, hardware) |
| **run-mlperf-endpoints-submission** (this) | orchestrates: benchmark per point → `runs create` → `submissions create --dry-run` |

`run-mlperf-endpoints-submission` pulls the other three in automatically.

---

## 3. Authentication

`runs create` and `submissions create` talk to the PRISM API. Export your token
(the CLI also reads it; this script never stores it):

```bash
export PRISM_USER_API_TOKEN=mlc_your_token_here
```

If the token is not set, use the `_runs-dry-run` variation for a fully offline
check (see below).

---

## 4. Short run (verify everything works)

A **short run** uses a tiny duration and few samples so you can confirm the whole
pipeline runs on your machine before committing to a multi-hour real submission.

**Fully offline** (no token, no uploads) — runs the benchmark per point and
`runs create --dry-run` (prints the parsed payload, no API):

```bash
mlcr run,mlperf,endpoints-submission,_echo-server,_short-run,_runs-dry-run \
  --num_points=4 --max_supported_concurrency=64
```

**Live dry-run** (uploads runs, assembles + checks, does NOT submit):

```bash
export PRISM_USER_API_TOKEN=mlc_...
mlcr run,mlperf,endpoints-submission,_echo-server,_short-run,_with-accuracy \
  --num_points=7 --org=MyOrg --system_name=MySystem --max_supported_concurrency=64
```

What the short run **does** verify: benchmark runs at each concurrency, region
selection + coverage, the accuracy run (`--mode both`), `system_desc.json`
generation, run-folder parsing, run registration, submission assembly, and the
submission checker.

What it **does not** represent: real numbers. The echo server just echoes the
prompt, so throughput/latency are meaningless and the accuracy score is a
trivial 1.0. For a real model the checker additionally enforces per-region
minimum durations, minimum query counts, and the model's accuracy quality gate —
which a 10-second echo run would not meet. If a checker error *does* occur on a
short run, the script prints `[SHORT RUN] … plumbing executed successfully` and
still exits 0.

> The `_echo-server` variation starts the bundled echo server and defaults the
> model/dataset, so no real endpoint is needed. Drop it (and pass `--endpoints`,
> `--model`, `--dataset`) to point at a real server.

---

## 5. Creating a real submission

A real submission needs a running inference endpoint, a real model + tokenizer
(for output-token / accuracy metrics), and runs long enough to meet the region
durations and query counts.

```bash
export PRISM_USER_API_TOKEN=mlc_...

# (optional) generate / inspect / edit the system description first
mlcr generate,mlperf,endpoints-system-desc \
  --org="Acme" --system_name="acme_h100x8" --max_supported_concurrency=1024 \
  --accelerator_model_name="NVIDIA H100" --accelerators_per_node=8 \
  --inference_backend=vllm --model_name="meta-llama/Llama-3.1-8B-Instruct" \
  --system_desc_path=./system_desc.json

# run the full multi-point submission (dry-run: assembles + checks, no submit)
mlcr run,mlperf,endpoints-submission,_with-accuracy \
  --endpoints=https://my-endpoint:8000 \
  --model=meta-llama/Llama-3.1-8B-Instruct \
  --dataset=/data/openorca.jsonl --prompt_column=text \
  --tokenizer=meta-llama/Llama-3.1-8B-Instruct \
  --accuracy_dataset=/data/cnn_dailymail.jsonl \
  --eval_method=rouge --ground_truth=highlights --extractor=identity_extractor \
  --accuracy_samples=13368 \
  --system_desc=./system_desc.json \
  --num_points=8 \
  --output_dir=./acme_submission
```

Each point uses its region's minimum duration automatically. To control points
explicitly: `--concurrencies=8,33,40,60,...`.

**Accuracy** is measured once (on the lowest-concurrency point, run with
`--mode both`); its `accuracy.txt` + `accuracy_result.json` are produced and
picked up during assembly. The score must meet the model's quality target
(§15). Available `--eval_method`s include `rouge`, `string_match`, `pass_at_1`;
extractors include `identity_extractor`, `abcd_extractor`, `boxed_math_extractor`,
`python_code_extractor`.

When the dry-run checker passes, the actual submission (PR creation) is done by
you, deliberately, with the submission CLI directly:

```bash
endpoints-submission-cli submissions create \
  --division standardized --scenario con --availability available \
  --run-ids <id1> --run-ids <id2> ...      # ids are saved in <output_dir>/run_ids.json
```

---

## 6. Variations & key inputs

| Variation | Effect |
|---|---|
| `_echo-server` | launch the bundled echo server; default model/dataset (local testing) |
| `_short-run` | tiny duration + sample count (plumbing check, not submission-valid) |
| `_with-accuracy` | also measure accuracy on the lowest-concurrency point (`--mode both`) → produces `accuracy/` |
| `_runs-dry-run` | `runs create --dry-run` only — no uploads, no submission (offline) |

| Input | Description |
|---|---|
| `--endpoints` | endpoint base URL (omit with `_echo-server`) |
| `--model` / `--dataset` / `--prompt_column` / `--tokenizer` | benchmark target |
| `--accuracy_dataset` / `--accuracy_samples` / `--accuracy_prompt_column` | accuracy dataset (enables accuracy; implies `_with-accuracy`) |
| `--eval_method` / `--ground_truth` / `--extractor` | accuracy scoring config |
| `--max_supported_concurrency` | M (> 32); also settable via `--system_desc` |
| `--num_points` | number of measurement points (7–32 for a valid submission; default 7) |
| `--concurrencies` | explicit comma-separated points (overrides auto-selection) |
| `--division` / `--scenario` / `--availability` | submission metadata (`standardized` / `con` / `available`) |
| `--duration` | per-point duration override (default: region minimum, or 10 s for `_short-run`) |
| `--num_workers` / `--max_connections` / `--settle_seconds` | client tuning (defaults are conservative for `_echo-server`) |
| `--org` / `--system_name` / hardware flags | forwarded to the system-description generator |
| `--output_dir` | where per-point run folders + `run_ids.json` are written |
| `--system_desc` | use an existing `system_desc.json` (skips generation) |

## 7. Outputs

`<output_dir>/`
- `point_<c>/` — one benchmark run folder per concurrency (`config.yaml`,
  `result_summary.json`, `system_desc.json`, …)
- `run_ids.json` — the registered run UUIDs (reuse for `submissions create`, or
  `runs delete`)
- `echo_server.log` — present when `_echo-server` was used

## 8. Notes & limitations

- **macOS / localhost:** back-to-back high-concurrency runs can exhaust ephemeral
  ports. For `_echo-server` the script caps `--max-connections` (128) and settles
  3 s between points. On real Linux endpoints these defaults don't apply.
- CPU affinity is disabled automatically off Linux (the benchmark's NUMA pinning
  is Linux-only).
- Accuracy is measured on a single point (the lowest concurrency) via
  `--mode both`, since the submission requires one accuracy result per
  (system, model).
- Local (offline) submission assembly + `submission-checker` is a planned
  follow-up (pending a submission-CLI change); today the dry-run path uploads the
  runs and lets the API assemble + check them.
