# get-redfish-power-info

Captures power-related fields from a Redfish BMC endpoint and writes them to a YAML file.

Motivated by the MLCommons Power WG proposal ([inference_policies#324](https://github.com/mlcommons/inference_policies/pull/324), [inference#2576](https://github.com/mlcommons/inference/issues/2576)) to include nameplate / design power (PSU capacity data) in MLPerf Inference submissions.

## What it does

1. **Discovers** all Chassis and Systems dynamically from `/redfish/v1/` — no hardcoded IDs.
2. **For each Chassis**, queries `/Power` (PowerControl, PowerSupplies, Voltages) and `/Thermal` (Fans, Temperatures).
3. **For each System**, captures identity and hardware summary fields.
4. **Writes a YAML file** whose structure mirrors the actual Redfish response — fields absent from the response are omitted entirely; arrays reflect the real count (e.g. 3 PSUs → 3 entries).

## Usage

### Via mlcr

```bash
mlcr get,redfish,power,info \
    --endpoint=https://bmc.example.com \
    --username=admin \
    --password=secret \
    --output=redfish_power.yaml
```

### Standalone (no mlcflow)

```bash
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
| `--output` | `redfish_capture.yaml` | Output YAML file path |
| `--insecure` | `true` | Skip TLS verification (self-signed BMC certs) |

## Local testing with Redfish Mockup Server

```bash
git clone https://github.com/DMTF/Redfish-Mockup-Server.git
cd Redfish-Mockup-Server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 redfishMockupServer.py   # serves on http://localhost:8000
```

Then in another terminal:

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

## Output environment variable

| Variable | Description |
|---|---|
| `MLC_REDFISH_OUTPUT_FILE_PATH` | Absolute path to the generated YAML file |
