# get-tpu-devices

Detects the Google TPUs present on a node and exports their properties as
`MLC_TPU_*` environment variables, so that `get-mlperf-single-node-system-info`
(and through it, `get-mlperf-multi-node-system-info`) can fill in the
accelerator fields of an MLPerf `system_desc` JSON.

**This script is currently a skeleton.** The plumbing, the env/state contract
and the consumers are all in place and tested; the one thing missing is the
actual TPU probing. See [What you need to implement](#what-you-need-to-implement).

It is modelled directly on [`get-xpu-devices`](../get-xpu-devices/), which does
the same job for Intel GPUs. When something here is unclear, that script is the
working reference.

---

## Where this fits

```
mlcr get-mlperf-multi-node-system-info,_tpu --ssh_ids=user@node1,user@node2
  └─ (per node, over SSH) get-mlperf-single-node-system-info,_tpu
       ├─ detect,os / detect,cpu / detect,host,system,details
       └─ get,tpu-devices              ← THIS SCRIPT
            run.sh → detect.py → tmp-run.out
                                   └─ customize.py:postprocess()
                                        → MLC_TPU_* env + mlc_tpu_* state
       └─ parse.py  (maps MLC_TPU_* → system_desc fields)
```

`get-tpu-devices` only runs when the `_tpu` variation is active — it is gated by
`enable_if_env: MLC_ACCELERATOR_BACKEND: [tpu]` in
[`get-mlperf-single-node-system-info/meta.yaml`](../get-mlperf-single-node-system-info/meta.yaml),
the same way `get,cuda-devices`, `get,rocm-devices` and `get,xpu-devices` are.
It can also be run on its own:

```bash
mlcr get,tpu-devices
```

---

## What you need to implement

Exactly one function: `get_tpu_info()` in [`detect.py`](detect.py). It returns
a list of dicts, one per TPU chip. Writing `tmp-run.out` and parsing it back
into env vars is already written and should not need changing.

How you obtain the values is your call — pure Python via a library, `subprocess`
around a CLI, or commands in `run.sh` whose output `detect.py` just parses.

Two smaller `TODO(tpu)` items are marked in the other files:

| File | TODO |
|---|---|
| [`customize.py`](customize.py) | The chip-to-chip (ICI) interconnect probe. Currently sets both interconnect keys to `""`, which is a valid "fill this in manually" result. |
| [`meta.yaml`](meta.yaml) | The `docker:` block. TPU containers need `/dev/accel*` passthrough plus the host libtpu mounts; `all_gpus` is NVIDIA/AMD-specific and is deliberately not set. `run: false` until this is worked out. |

---

## The contract

`detect.py` writes plain `Key: Value` lines to `tmp-run.out` in the working
directory. `customize.py` turns each key into an env var by uppercasing it and
replacing spaces with underscores, prefixed with `MLC_TPU_DEVICE_PROP_`.

**The key spelling is the interface.** Renaming a key in `detect.py` silently
changes the env var name and the corresponding `system_desc` field goes to
`"N/A"` with no error. If you need a new key, add it in two places:
`customize.py` (`ALLOWED_KEYS`) and
`get-mlperf-single-node-system-info/parse.py` (`EXTRACT_RULES`). A key that is
not in `ALLOWED_KEYS` is dropped.

### Per-device keys

| `tmp-run.out` key | Env var | `system_desc` field | Required | Expected format |
|---|---|---|---|---|
| `TPU Device ID` | `MLC_TPU_DEVICE_PROP_TPU_DEVICE_ID` | — (block delimiter) | yes | unique per chip, e.g. `0` or `0000:00:05.0` |
| `TPU Name` | `MLC_TPU_DEVICE_PROP_TPU_NAME` | `accelerator_model_name` | yes | `TPU v5e` |
| `Memory Type` | `MLC_TPU_DEVICE_PROP_MEMORY_TYPE` | `accelerator_memory_type` | yes | `HBM2e` |
| `Global memory` | `MLC_TPU_DEVICE_PROP_GLOBAL_MEMORY` | `accelerator_memory_capacity` | yes | `16 GiB` — unit required |
| `Host Interconnect Type` | `MLC_TPU_DEVICE_PROP_HOST_INTERCONNECT_TYPE` | `accelerator_host_interconnect` | yes | `PCIe 4.0 x16` |
| `TPU driver version` | `MLC_TPU_DEVICE_PROP_TPU_DRIVER_VERSION` | — | no | free-form |
| `libtpu version` | `MLC_TPU_LIBTPU_VERSION` | `inference_backend`, `other_software_stack` | no | `0.0.11` |
| `Max clock rate` | `MLC_TPU_DEVICE_PROP_MAX_CLOCK_RATE` | `accelerator_frequency` | no | `940 MHz` — unit required |
| `Host Interconnect Bandwidth` | `MLC_TPU_DEVICE_PROP_HOST_INTERCONNECT_BANDWIDTH` | — | no | `64 GB/s` |

> `TPU Device ID` **must be the first key** emitted for each chip —
> `customize.py` uses it as the marker that starts a new device block.

> `libtpu version` is the one key that does not follow the
> `MLC_TPU_DEVICE_PROP_*` pattern: `customize.py` promotes it to
> `MLC_TPU_LIBTPU_VERSION` because it describes the node's software stack
> rather than a single chip.

### Script-level keys

Set by `customize.py`, not by `detect.py`:

| Env var | `system_desc` field | Set by |
|---|---|---|
| `MLC_TPU_NUM_DEVICES` | `accelerators_per_node` | counted from the device blocks |
| `MLC_TPU_DEVICE_PROP_ACCELERATOR_INTERCONNECT_TYPE` | `accelerator_interconnect` | **TODO** — currently `""` |
| `MLC_TPU_DEVICE_PROP_ACCELERATOR_INTERCONNECT_TOPOLOGY` | `accelerator_interconnect_topology` | **TODO** — currently `""` |

### State keys

Also exported for programmatic consumers:

- `mlc_tpu_num_devices` — int
- `mlc_tpu_device_prop` — flat dict of the last device's properties
- `mlc_tpu_devices_prop` — dict keyed by device index

---

## Value formatting notes

These come from how `parse.py` post-processes the values; getting them wrong
produces a silently wrong submission rather than an error.

- **`Global memory`** — emit integer GiB with the unit, e.g. `16 GiB`.
  `parse.py` takes the first whitespace-separated token, and any value below
  1 GiB-in-bytes is treated as already being in GiB. So `16 GiB` → `16GiB`,
  but a raw byte count like `17179869184` would be converted as bytes → `16GiB`
  too. Emitting a bare `16` with no unit also works, but the unit is clearer.
- **`Host Interconnect Type`** — if the value does not already start with
  `PCIe`, `customize.py` prepends it. So both `4.0 x16` and `PCIe 4.0 x16`
  end up as `PCIe 4.0 x16`.
- **`Memory Type`** — TPU APIs generally do not report this. `get-xpu-devices`
  handles the same gap with a static `memory_type_map` keyed on the chip name;
  do the same, and cite the source of the values in a comment so a reviewer can
  check them.
- **Empty vs `"N/A"`** — an empty string means "not auto-detectable, submitter
  fills this in by hand". Prefer that over guessing. `parse.py` renders missing
  required fields as `"N/A"`.

---

## Candidate data sources

Worth evaluating; none of these is assumed by the skeleton, and part of the
task is deciding which is authoritative on a stock Cloud TPU VM.

- the `tpu-info` CLI (pip package `tpu-info`) — chip type, HBM usage
- `jax.devices()` / `jax.local_devices()` → `device_kind`, core counts
- libtpu APIs
- the GCE metadata server for the slice type:
  ```bash
  curl -H "Metadata-Flavor: Google" \
    http://metadata.google.internal/computeMetadata/v1/instance/attributes/accelerator-type
  # e.g. v5litepod-8
  ```
- `/dev/accel*` enumeration plus `/sys/class/accel/accel*/device/*` for PCIe
  link speed and width
- `lspci -vmm` filtered on Google's PCI vendor id (`0x1ae0`)

Prefer a source that works while the TPU is **in use** — this script may run
alongside a benchmark, and anything that needs to claim the chip will fail
there. `get-xpu-devices` shells out to `xpu-smi`; the equivalent choice here is
yours to make.

---

## Testing

### 1. Unit-level: does `detect.py` produce the right file?

```bash
cd /tmp && python3 /path/to/script/get-tpu-devices/detect.py && cat tmp-run.out
```

Expected shape for a 2-chip node:

```
TPU Device ID: 0
TPU Name: TPU v5e
Memory Type: HBM2e
Global memory: 16 GiB
Host Interconnect Type: PCIe 4.0 x16
libtpu version: 0.0.11
TPU Device ID: 1
TPU Name: TPU v5e
...
```

### 2. Script-level: does the env come out right?

```bash
mlcr get,tpu-devices --new
mlc show cache --tags=get,tpu-devices
```

### 3. End-to-end: does it reach the submission JSON?

```bash
mlcr get,mlperf,single-node,system-info,_tpu \
     --out_dir_path=/tmp/sysinfo --out_file_name=tpu-node.json
python3 -m json.tool /tmp/sysinfo/tpu-node.json
```

Check `accelerator_model_name`, `accelerators_per_node`,
`accelerator_memory_capacity`, `accelerator_memory_type`,
`accelerator_host_interconnect`.

You can verify the consumer side without any TPU hardware by feeding `parse.py`
the env vars directly:

```bash
MLC_TPU_DEVICE_PROP_TPU_NAME="TPU v5e" \
MLC_TPU_NUM_DEVICES=8 \
MLC_TPU_DEVICE_PROP_GLOBAL_MEMORY="16 GiB" \
MLC_TPU_DEVICE_PROP_MEMORY_TYPE="HBM2e" \
MLC_TPU_DEVICE_PROP_HOST_INTERCONNECT_TYPE="PCIe 4.0 x16" \
MLC_TPU_LIBTPU_VERSION="0.0.11" \
python3 ../get-mlperf-single-node-system-info/parse.py --output /tmp/tpu-smoke.json
```

### 4. Multi-node

```bash
mlcr get-mlperf-multi-node-system-info,_tpu,_exclude_current_node \
     --ssh_ids=user@node1:22,user@node2:22 \
     --out_dir_path=/tmp/sysinfo \
     --system_name="8x TPU v5e"
```

---

## Checklist before opening a PR

- [ ] `get_tpu_info()` implemented; `NotImplementedError` removed
- [ ] `TODO(tpu)` in `customize.py` resolved (ICI type + topology), or
      consciously left as `""` with a comment explaining why
- [ ] `TODO(tpu)` in `meta.yaml` resolved (docker device passthrough), or
      `docker.run` left `false`
- [ ] Verified on real hardware for at least one TPU generation; note which one
      in the PR description
- [ ] `README.md` generated: `mlc doc script --tags=get,tpu-devices`
- [ ] `mlc lint script --tags=get,tpu-devices` clean
- [ ] Static values (memory type table, any hard-coded bandwidths) have a cited
      source in a code comment
- [ ] No `print()` in `customize.py` — use `i['automation'].logger`
- [ ] `customize.py` returns `{'return': 1, 'error': '...'}` on failure rather
      than raising

See [AGENTS.md](../../AGENTS.md) for the repo-wide script conventions and the
PR review format used here.

---

## Files

| File | Status |
|---|---|
| `meta.yaml` | done, except the `docker:` TODO |
| `run.sh` | done |
| `detect.py` | **skeleton — implement `get_tpu_info()`** |
| `customize.py` | done, except the ICI TODO |
| `info.md` | this file |
| `README.md` | not generated yet — `mlc doc script --tags=get,tpu-devices` |
| `run.bat` | not provided. `get,tpu-devices` is skipped on Windows by the caller (`skip_if_env: MLC_HOST_OS_TYPE: [windows]`), matching `get-cuda-devices` / `get-rocm-devices` / `get-xpu-devices`. |
