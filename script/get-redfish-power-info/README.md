# get-redfish-power-info

Captures power-related fields from a Redfish BMC endpoint and writes them to a YAML file.

Motivated by the MLCommons Power WG proposal ([inference_policies#324](https://github.com/mlcommons/inference_policies/pull/324), [inference#2576](https://github.com/mlcommons/inference/issues/2576)) to include nameplate / design power (PSU capacity data) in MLPerf Inference submissions.

## What it does

Every actual HTTP request to the BMC is delegated to the DMTF
[`redfishtool`](https://pypi.org/project/redfishtool/) CLI
(`redfishtool raw GET <uri>`), installed as a pip dependency
(`get,generic-python-lib,_package.redfishtool`) — this script doesn't talk
HTTP directly; it shells out to `redfishtool` and shapes the JSON it returns.

1. **Discovers** all Chassis and Systems dynamically from `/redfish/v1/` — no hardcoded IDs.
2. **For each Chassis**, queries PSU data (preferring the newer `PowerSubsystem` schema,
   falling back to the legacy `Power` resource) and, in `--scope=full`, also
   `PowerControl`/`Voltages` and `/Thermal` (Fans, Temperatures).
3. **For each System** (`--scope=full` only), captures identity and hardware summary fields.
4. **Writes a YAML file** whose structure mirrors the actual Redfish response — fields absent from the response are omitted entirely; arrays reflect the real count (e.g. 3 PSUs → 3 entries).

## Scopes (`--scope` / `_full` / `_inference_optional_nameplate`)

| Scope | What it queries | Output |
|---|---|---|
| `full` (default) | Chassis identity, PowerControl, Voltages, PSUs/redundancy, Thermal, and the full Systems collection | `--output` raw capture YAML, plus `--nameplate-output` if given |
| `inference-optional-nameplate` | Chassis identity + PSUs/redundancy **only** — no Thermal fetch, no Systems collection, and the legacy `Power` resource is only fetched as a PSU-data fallback when `PowerSubsystem` isn't implemented | **only** `--nameplate-output` (required in this scope — `--output` is ignored) |

Use `full` for a general-purpose capture; use `inference-optional-nameplate`
when all you need is the nameplate power YAML — it issues noticeably fewer
`redfishtool` calls per chassis.

## Usage

### Via mlcr

```bash
# Full capture
mlcr get,redfish,power,info,_full \
    --endpoint=https://bmc.example.com \
    --username=admin \
    --password=secret \
    --output=redfish_power.yaml \
    --nameplate_output=redfish_power_nameplate.yaml \
    --system_name="My System"

# Lean nameplate-only capture
mlcr get,redfish,power,info,_inference_optional_nameplate \
    --endpoint=https://bmc.example.com \
    --username=admin \
    --password=secret \
    --nameplate_output=redfish_power_nameplate.yaml \
    --system_name="My System"
```

### Standalone (no mlcflow)

```bash
pip install redfishtool pyyaml

python3 get_redfish_power_info.py \
    --endpoint http://localhost:8000 \
    --output redfish_capture.yaml
```

## Arguments

| Argument | Default | Description |
|---|---|---|
| `--endpoint` | `http://localhost:8000` | Redfish base URL |
| `--username` | `""` | BMC username (empty = no auth) |
| `--password` | `""` | BMC password |
| `--redfishtool-bin` | `redfishtool` | Path to the `redfishtool` executable. Resolved from PATH by default; the mlcr wrapper (`customize.py`) resolves this automatically from the `get,generic-python-lib,_package.redfishtool` dependency. |
| `--scope` | `full` | `full` or `inference-optional-nameplate` — see table above |
| `--output` | `redfish_capture.yaml` | Raw capture YAML file path. Ignored in `--scope=inference-optional-nameplate` |
| `--nameplate-output` | `""` | If set, also write the MLPerf submission_checker-compatible nameplate power YAML (see below). Required when `--scope=inference-optional-nameplate` |
| `--system-name` | `System` | Top-level label used in the nameplate power YAML |

`redfishtool` itself always skips TLS certificate verification internally
(no CLI flag controls this), so there is no separate "insecure" option here.

### Nameplate power YAML (`--nameplate-output`)

In addition to the raw capture above, this script can emit the PSU
nameplate/design-power YAML consumed by the MLPerf Inference
`submission_checker`'s `nameplate_power_check`
(`tools/submission/submission_checker/checks/system_check.py` in the
`inference` repo), which sums `PowerCapacityWatts` across the `Min PSUs
Needed` largest PSUs per leaf and expects the file at
`systems/<system_desc_id>_power.yaml`.

```bash
python3 get_redfish_power_info.py \
    --endpoint http://localhost:8000 \
    --output redfish_capture.yaml \
    --nameplate-output redfish_nameplate_power.yaml \
    --system-name "My System"
```

```yaml
My System:
- Computer System Chassis:
  - Description: Contoso 3500RX
    Min PSUs Needed: 1
    PSUs:
    - Name: Power Supply Bay 1
      PowerCapacityWatts: 400
```

PSU data is read preferentially from the newer `Chassis/<id>/PowerSubsystem`
schema (`PowerSupplies` + `PowerSupplyRedundancy[].MinNeededInGroup`),
falling back to the legacy `Chassis/<id>/Power` → `PowerSupplies[]` array
when a BMC only implements that one. When redundancy isn't reported at all,
`Min PSUs Needed` conservatively defaults to the number of installed PSUs
(no redundancy credit — verify and adjust manually if your hardware is
actually redundant). PSU bays reporting `Status.State == "Absent"` (empty
slots) are skipped.

Redfish has no concept of rack/system grouping above a chassis, so each
chassis becomes one flat leaf under the system-name label — if you want an
explicit rack layer in between, add it to the generated YAML by hand.

The [`get-mlperf-multi-node-system-info`](../get-mlperf-multi-node-system-info/README.md)
script's `_redfish` + `_inference_optional_nameplate` variations wire this up
automatically as part of MLPerf system-info collection (and, used without
`_redfish`, that script writes a generic skeleton template instead of
contacting a BMC at all).

## Local testing with Redfish Mockup Server

```bash
git clone https://github.com/DMTF/Redfish-Mockup-Server.git
cd Redfish-Mockup-Server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 redfishMockupServer.py   # serves on http://localhost:8000
```

Then in another terminal (with `redfishtool` and `pyyaml` installed, see Usage above):

```bash
python3 get_redfish_power_info.py --endpoint http://localhost:8000 --output test_output.yaml
cat test_output.yaml
```

## Output format

```yaml
captured_at: "2025-07-06T10:30:00Z"
redfish_endpoint: "http://localhost:8000"

chassis:
  - id: "1"
    name: "..."
    power:
      control:
        - name: "..."
          consumed_watts: ...
          capacity_watts: ...
      power_supplies:
        - id: "0"
          name: "..."
          capacity_watts: 1200
          health: "OK"
      voltages:
        - name: "..."
          reading_volts: 12.1
    thermal:
      fans:
        - name: "..."
          reading_rpm: 3200
          health: "OK"
      temperatures:
        - name: "..."
          reading_celsius: 42.0

systems:
  - id: "1"
    name: "..."
    model: "..."
    manufacturer: "..."
    power_state: "On"
    processor_count: 2
    processor_model: "Intel Xeon"
    total_memory_gib: 128
    bios_version: "P79 v1.45"
```

Only fields present in the Redfish response are included. Null values are preserved as `null`.

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_REDFISH_OUTPUT_FILE_PATH` | Absolute path to the raw capture YAML file (only set in `_full` scope) |
| `MLC_REDFISH_NAMEPLATE_OUTPUT_FILE_PATH` | Absolute path to the nameplate power YAML file (set whenever `--nameplate-output`/`_inference_optional_nameplate` produced one) |
| `MLC_REDFISH_TOOL_BIN` | Resolved path to the `redfishtool` executable actually used |
