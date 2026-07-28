#!/usr/bin/env python3
"""
Capture power and thermal data from a Redfish BMC endpoint and write to YAML.

Every actual HTTP request is delegated to the DMTF `redfishtool` CLI
(`redfishtool raw GET <uri>`) rather than talked to directly — this script
only walks the service root dynamically (no hardcoded IDs like Chassis/1 or
Systems/1) and shapes the results into YAML.

Two scopes are supported (--scope):
  full                       — complete chassis + systems + thermal capture
                                (the general-purpose raw dump).
  inference-optional-nameplate — minimal PSU-only walk: skips Thermal and
                                Systems entirely, and skips the legacy
                                Chassis/<id>/Power control+voltage fetch
                                whenever the newer PowerSubsystem schema is
                                available. Only produces --nameplate-output.
"""

import argparse
import datetime
import json
import re
import os
import subprocess
import sys
import urllib.parse
from typing import Optional

import yaml


# ---------------------------------------------------------------------------
# Redfish transport via the `redfishtool` CLI
# ---------------------------------------------------------------------------

class RedfishToolClient:
    """Runs the DMTF `redfishtool` CLI as a subprocess to fetch Redfish
    resources, instead of issuing HTTP requests directly. Every GET becomes
    `redfishtool <connection opts> raw GET <uri>`.
    """

    def __init__(self, redfishtool_bin: str, endpoint: str, username: str,
                 password: str, timeout: int = 30):
        self.redfishtool_bin = redfishtool_bin
        self.timeout = timeout

        parsed = urllib.parse.urlparse(endpoint)
        rhost = parsed.netloc or parsed.path
        self.conn_opts = ['-r', rhost]
        if username:
            self.conn_opts += ['-u', username, '-p', password]
        else:
            self.conn_opts += ['-A', 'None']
        # -S controls *whether* redfishtool uses https, not certificate
        # verification — redfishtool's own requests calls default to
        # verify=False regardless, so there is no separate "insecure" knob
        # to pass through here.
        self.conn_opts += ['-S',
                            'Always' if parsed.scheme == 'https' else 'Never']

    def get(self, uri: str) -> Optional[dict]:
        """GET an arbitrary Redfish URI via `redfishtool raw GET <uri>`.

        Returns None (silently) on a 404 — many resources probed here
        (PowerSubsystem, Thermal, legacy Power) are optional depending on
        which Redfish schema generation a given BMC implements.
        """
        cmd = [self.redfishtool_bin] + self.conn_opts + ['raw', 'GET', uri]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout)
        except Exception as exc:
            print(
                f'  Error running redfishtool for {uri}: {exc}',
                file=sys.stderr)
            return None
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if '404' in stderr or 'Not Found' in stderr:
                return None
            print(
                f'  redfishtool raw GET {uri} failed: '
                f'{stderr or f"exit code {result.returncode}"}',
                file=sys.stderr)
            return None
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            print(
                f'  Could not parse redfishtool output for {uri}',
                file=sys.stderr)
            return None


def _members(data: Optional[dict]) -> list[str]:
    """Extract @odata.id hrefs from a Members array."""
    if not data:
        return []
    return [m.get('@odata.id', '')
            for m in data.get('Members', []) if m.get('@odata.id')]


def _id_from_url(url: str) -> str:
    return url.rstrip('/').split('/')[-1]


# ---------------------------------------------------------------------------
# Per-resource extractors
# ---------------------------------------------------------------------------

def _extract_power_control(entry: dict) -> dict:
    out = {}
    for k in ('Name', 'PowerConsumedWatts', 'PowerCapacityWatts',
              'PowerAvailableWatts', 'PowerAllocatedWatts', 'PowerRequestedWatts'):
        if k in entry:
            out[_to_snake(k)] = entry[k]
    metrics = entry.get('PowerMetrics', {}) or {}
    if metrics:
        for mk, ok in (('AverageConsumedWatts', 'average_watts'),
                       ('MaxConsumedWatts', 'max_watts'),
                       ('MinConsumedWatts', 'min_watts'),
                       ('IntervalInMin', 'interval_minutes')):
            if mk in metrics:
                out[ok] = metrics[mk]
    limit = entry.get('PowerLimit', {}) or {}
    if limit and limit.get('LimitInWatts') is not None:
        out['limit_watts'] = limit['LimitInWatts']
    status = entry.get('Status', {}) or {}
    if status.get('Health') is not None:
        out['health'] = status['Health']
    if status.get('State') is not None:
        out['state'] = status['State']
    return out


def _extract_redundancy(entry: dict) -> dict:
    out = {}
    for k, ok in (
        ('MaxSupportedInGroup', 'max_supported_in_group'),
        ('MinNeededInGroup', 'min_needed_in_group'),
    ):
        if k in entry:
            out[ok] = entry[k]
    return out


def _extract_psu(entry: dict) -> dict:
    out = {}
    # Legacy Chassis/<id>/Power uses 'MemberId'; the newer
    # PowerSubsystem/PowerSupplies/<bay> resource uses 'Id'.
    if 'Id' in entry and 'MemberId' not in entry:
        out['id'] = entry['Id']
    for k, ok in (
        ('MemberId', 'id'),
        ('Name', 'name'),
        ('PowerCapacityWatts', 'capacity_watts'),
        ('LastPowerOutputWatts', 'last_output_watts'),
        ('LineInputVoltage', 'input_voltage'),
        ('LineInputVoltageType', 'input_voltage_type'),
        ('PowerSupplyType', 'type'),
        ('Model', 'model'),
        ('Manufacturer', 'manufacturer'),
        ('SerialNumber', 'serial_number'),
        ('FirmwareVersion', 'firmware_version'),
        ('PartNumber', 'part_number'),
        ('SparePartNumber', 'spare_part_number'),
    ):
        if k in entry:
            out[ok] = entry[k]
    # InputRanges: rated output wattage per input voltage range — the
    # nameplate data
    input_ranges = entry.get('InputRanges') or []
    if input_ranges:
        _ir_map = (('InputType', 'input_type'), ('MinimumVoltage', 'minimum_voltage'),
                   ('MaximumVoltage', 'maximum_voltage'), ('OutputWattage', 'output_wattage'))
        out['input_ranges'] = [
            {ok: ir[k] for k, ok in _ir_map if k in ir}
            for ir in input_ranges
        ]
    status = entry.get('Status', {}) or {}
    if status.get('Health') is not None:
        out['health'] = status['Health']
    if status.get('State') is not None:
        out['state'] = status['State']
    return out


def _extract_voltage(entry: dict) -> dict:
    out = {}
    for k, ok in (
        ('Name', 'name'),
        ('ReadingVolts', 'reading_volts'),
        ('UpperThresholdNonCritical', 'upper_threshold_non_critical'),
        ('UpperThresholdCritical', 'upper_threshold_critical'),
        ('LowerThresholdNonCritical', 'lower_threshold_non_critical'),
        ('LowerThresholdCritical', 'lower_threshold_critical'),
    ):
        if k in entry:
            out[ok] = entry[k]
    status = entry.get('Status', {}) or {}
    if status.get('Health') is not None:
        out['health'] = status['Health']
    return out


def _extract_fan(entry: dict) -> dict:
    out = {}
    for k, ok in (
        ('MemberId', 'id'),
        ('FanName', 'name'),
        ('Name', 'name'),
        ('PhysicalContext', 'physical_context'),
        # ReadingRPM (older Redfish) takes precedence; fallback to
        # Reading+ReadingUnits (newer)
        ('ReadingRPM', 'reading_rpm'),
        ('Reading', 'reading'),
        ('ReadingUnits', 'reading_units'),
        ('UpperThresholdNonCritical', 'upper_threshold_non_critical'),
        ('UpperThresholdCritical', 'upper_threshold_critical'),
        ('LowerThresholdNonCritical', 'lower_threshold_non_critical'),
        ('LowerThresholdCritical', 'lower_threshold_critical'),
    ):
        if k in entry and ok not in out:
            out[ok] = entry[k]
    status = entry.get('Status', {}) or {}
    if status.get('Health') is not None:
        out['health'] = status['Health']
    if status.get('State') is not None:
        out['state'] = status['State']
    return out


def _extract_temperature(entry: dict) -> dict:
    out = {}
    for k, ok in (
        ('Name', 'name'),
        ('ReadingCelsius', 'reading_celsius'),
        ('UpperThresholdNonCritical', 'upper_threshold_non_critical'),
        ('UpperThresholdCritical', 'upper_threshold_critical'),
        ('LowerThresholdNonCritical', 'lower_threshold_non_critical'),
        ('LowerThresholdCritical', 'lower_threshold_critical'),
        ('PhysicalContext', 'physical_context'),
    ):
        if k in entry:
            out[ok] = entry[k]
    status = entry.get('Status', {}) or {}
    if status.get('Health') is not None:
        out['health'] = status['Health']
    return out


def _to_snake(name: str) -> str:
    """CamelCase → snake_case for the simple cases we encounter."""
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
    s = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', s)
    return s.lower()


def _collect_power_subsystem(client: RedfishToolClient, chassis_url: str, chassis_id: str):
    """Query the newer (DSP2046 v1.5+) PowerSubsystem schema for a chassis.

    Returns (psu_list, redundancy_list) or (None, None) if the BMC doesn't
    implement this schema. PSU bays reporting Status.State == "Absent" (an
    empty slot) are skipped — only physically installed PSUs are nameplate
    power sources.
    """
    subsystem = client.get(f'{chassis_url}/{chassis_id}/PowerSubsystem')
    if not subsystem:
        return None, None

    redundancy_list = [_extract_redundancy(r)
                       for r in subsystem.get('PowerSupplyRedundancy', []) or []
                       if r]

    psu_collection_href = (
        subsystem.get('PowerSupplies', {}) or {}).get('@odata.id', '')
    if not psu_collection_href:
        return [], redundancy_list

    psu_hrefs = _members(client.get(psu_collection_href))
    psu_list = []
    for psu_href in psu_hrefs:
        psu_data = client.get(psu_href)
        if not psu_data:
            continue
        if (psu_data.get('Status', {}) or {}).get('State') == 'Absent':
            continue
        psu_list.append(_extract_psu(psu_data))

    return psu_list, redundancy_list


# ---------------------------------------------------------------------------
# Chassis and Systems collection
# ---------------------------------------------------------------------------

def collect_chassis(client: RedfishToolClient, chassis_url: str, full: bool = True) -> list:
    """Walk the Chassis collection.

    full=True:  identity + PowerControl + Voltages + PSUs/redundancy + Thermal.
    full=False: identity + PSUs/redundancy only (the "inference-optional-
                nameplate" scope) — no Thermal fetch, and the legacy
                Chassis/<id>/Power resource is only fetched as a PSU-data
                fallback when the newer PowerSubsystem schema isn't present.
    """
    chassis_list = _members(client.get(chassis_url))
    results = []
    for href in chassis_list:
        chassis_id = _id_from_url(href)
        chassis_data = client.get(href)
        if not chassis_data:
            continue

        entry: dict = {'id': chassis_id}
        identity_fields = [('Name', 'name'), ('Manufacturer', 'manufacturer'),
                            ('Model', 'model')]
        if full:
            identity_fields += [('ChassisType', 'chassis_type'),
                                 ('SerialNumber', 'serial_number'), ('SKU', 'sku')]
        for k, ok in identity_fields:
            if k in chassis_data:
                entry[ok] = chassis_data[k]
        if full:
            status = chassis_data.get('Status', {}) or {}
            if status.get('Health'):
                entry['health'] = status['Health']

        # PSU nameplate data + redundancy: prefer the newer PowerSubsystem
        # schema (also carries Min/MaxNeededInGroup); fall back to the
        # legacy Power/PowerSupplies array if a BMC only implements that one.
        # A real BMC implements one or the other, not both, so there is no
        # double-counting risk here in practice.
        subsystem_psus, redundancy_list = _collect_power_subsystem(
            client, chassis_url, chassis_id)

        # Only fetch the legacy Power resource when we actually need it:
        # always in full scope (for PowerControl/Voltages), or as a PSU-data
        # fallback in either scope when PowerSubsystem isn't implemented.
        power_data = None
        if full or subsystem_psus is None:
            power_href = (
                chassis_data.get('Power', {}) or {}).get('@odata.id', '')
            if not power_href:
                power_href = f'{chassis_url}/{chassis_id}/Power'
            power_data = client.get(power_href)

        power_block = {}
        if full and power_data:
            ctrl_list = [_extract_power_control(c)
                         for c in power_data.get('PowerControl', []) or []
                         if c]
            if ctrl_list:
                power_block['control'] = ctrl_list

            volt_list = [_extract_voltage(v)
                         for v in power_data.get('Voltages', []) or []
                         if v]
            if volt_list:
                power_block['voltages'] = volt_list

        if subsystem_psus is not None:
            if subsystem_psus:
                power_block['power_supplies'] = subsystem_psus
            if redundancy_list:
                power_block['redundancy'] = redundancy_list
        elif power_data:
            psu_list = [_extract_psu(p)
                        for p in power_data.get('PowerSupplies', []) or []
                        if p]
            if psu_list:
                power_block['power_supplies'] = psu_list

        if power_block:
            entry['power'] = power_block

        if full:
            thermal_href = (
                chassis_data.get('Thermal', {}) or {}).get('@odata.id', '')
            if not thermal_href:
                thermal_href = f'{chassis_url}/{chassis_id}/Thermal'
            thermal_data = client.get(thermal_href)
            if thermal_data:
                thermal_block = {}

                fan_list = [_extract_fan(f)
                            for f in thermal_data.get('Fans', []) or []
                            if f]
                if fan_list:
                    thermal_block['fans'] = fan_list

                temp_list = [_extract_temperature(t)
                             for t in thermal_data.get('Temperatures', []) or []
                             if t]
                if temp_list:
                    thermal_block['temperatures'] = temp_list

                if thermal_block:
                    entry['thermal'] = thermal_block

        results.append(entry)

    return results


# ---------------------------------------------------------------------------
# Nameplate power YAML — MLPerf submission_checker-compatible format
# ---------------------------------------------------------------------------

def build_nameplate_power(chassis_results: list, system_name: str) -> Optional[dict]:
    """Build the nameplate power tree consumed by the MLPerf Inference
    submission_checker's nameplate_power_check (checks/system_check.py).

    Structure: {system_name: [{label: [{"Description": ..., "Min PSUs
    Needed": N, "PSUs": [{"Name": ..., "PowerCapacityWatts": ...}, ...]}]}]}

    One leaf per chassis. Redfish has no concept of rack/system grouping
    above a chassis, so submitters who want an explicit rack layer in
    between need to add it by hand after generation.

    Returns None if no chassis had any PSU data to report.
    """
    leaves = []
    for chassis in chassis_results:
        psus = (chassis.get('power', {}) or {}).get('power_supplies', [])
        if not psus:
            continue

        redundancy = (chassis.get('power', {}) or {}).get('redundancy', [])
        min_needed = redundancy[0].get(
            'min_needed_in_group') if redundancy else None
        if min_needed is None:
            # Conservative fallback when the BMC doesn't report redundancy:
            # assume every installed PSU is required (no redundancy credit).
            min_needed = len(psus)

        desc = ' '.join(
            p for p in (chassis.get('manufacturer'), chassis.get('model')) if p
        ) or chassis.get('name') or f"Chassis {chassis['id']}"

        label = chassis.get('name') or chassis['id']
        leaves.append({
            label: [{
                'Description': desc,
                'Min PSUs Needed': min_needed,
                'PSUs': [
                    {
                        'Name': psu.get('name') or f"PSU {psu.get('id', '')}".strip(),
                        'PowerCapacityWatts': psu.get('capacity_watts', 0),
                    }
                    for psu in psus
                ],
            }]
        })

    if not leaves:
        return None
    return {system_name: leaves}


def collect_systems(client: RedfishToolClient, systems_url: str) -> list:
    systems_list = _members(client.get(systems_url))
    results = []
    for href in systems_list:
        system_id = _id_from_url(href)
        data = client.get(href)
        if not data:
            continue

        entry: dict = {'id': system_id}
        for k, ok in (
            ('Name', 'name'),
            ('Model', 'model'),
            ('Manufacturer', 'manufacturer'),
            ('SerialNumber', 'serial_number'),
            ('SKU', 'sku'),
            ('HostName', 'hostname'),
            ('PowerState', 'power_state'),
            ('BiosVersion', 'bios_version'),
            ('PartNumber', 'part_number'),
            ('SystemType', 'system_type'),
        ):
            if k in data:
                entry[ok] = data[k]

        proc_summary = data.get('ProcessorSummary', {}) or {}
        if proc_summary.get('Count') is not None:
            entry['processor_count'] = proc_summary['Count']
        if proc_summary.get('Model'):
            entry['processor_model'] = proc_summary['Model']

        mem_summary = data.get('MemorySummary', {}) or {}
        total_gib = mem_summary.get('TotalSystemMemoryGiB')
        if total_gib is not None:
            entry['total_memory_gib'] = total_gib

        storage = data.get('Storage', {}) or {}
        if storage.get('@odata.id'):
            entry['storage_url'] = storage['@odata.id']

        results.append(entry)

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Capture Redfish power/thermal/system info (via the '
                    'redfishtool CLI) and write to YAML'
    )
    parser.add_argument('--endpoint', default='http://localhost:8000',
                        help='Redfish base URL (default: http://localhost:8000)')
    parser.add_argument('--username', default='',
                        help='BMC username (leave empty for unauthenticated mockup)')
    parser.add_argument('--password', default='',
                        help='BMC password')
    parser.add_argument('--redfishtool-bin', default='redfishtool',
                        help='Path to the redfishtool executable (default: '
                             '"redfishtool", resolved from PATH)')
    parser.add_argument('--scope', choices=['full', 'inference-optional-nameplate'],
                        default='full',
                        help='"full": complete chassis+systems+thermal capture. '
                             '"inference-optional-nameplate": minimal PSU-only '
                             'walk (no Thermal, no Systems); requires '
                             '--nameplate-output.')
    parser.add_argument('--output', default='redfish_capture.yaml',
                        help='Raw capture YAML file path (default: redfish_capture.yaml). '
                             'Ignored in --scope=inference-optional-nameplate.')
    parser.add_argument('--nameplate-output', default='',
                        help='If set, also write the MLPerf submission_checker-compatible '
                             'nameplate power YAML (systems/<system>_power.yaml format) to this path')
    parser.add_argument('--system-name', default='System',
                        help='Top-level label to use in the nameplate power YAML '
                             '(default: "System")')
    args = parser.parse_args()

    if args.scope == 'inference-optional-nameplate' and not args.nameplate_output:
        print(
            'ERROR: --scope=inference-optional-nameplate requires --nameplate-output '
            '(that is the only output this scope produces).', file=sys.stderr)
        sys.exit(1)

    full_scope = args.scope == 'full'

    if full_scope:
        output_dir = os.path.dirname(os.path.abspath(args.output))
        if not os.path.isdir(output_dir):
            print(
                f'ERROR: Output directory does not exist: {output_dir}',
                file=sys.stderr)
            sys.exit(1)

    if args.nameplate_output:
        nameplate_dir = os.path.dirname(os.path.abspath(args.nameplate_output))
        if not os.path.isdir(nameplate_dir):
            print(
                f'ERROR: Nameplate output directory does not exist: {nameplate_dir}',
                file=sys.stderr)
            sys.exit(1)

    client = RedfishToolClient(
        args.redfishtool_bin, args.endpoint, args.username, args.password)

    print(
        f'Connecting to Redfish endpoint: {args.endpoint} (via {args.redfishtool_bin})',
        flush=True)
    service_root = client.get('/redfish/v1/')
    if not service_root:
        print(
            'ERROR: Could not reach Redfish service root at /redfish/v1/ '
            '(check --endpoint, --redfishtool-bin, and credentials)',
            file=sys.stderr)
        sys.exit(1)

    chassis_url = (
        service_root.get(
            'Chassis',
            {}) or {}).get(
        '@odata.id',
        '/redfish/v1/Chassis')
    systems_url = (
        service_root.get(
            'Systems',
            {}) or {}).get(
        '@odata.id',
        '/redfish/v1/Systems')

    print(f'Discovering Chassis from {chassis_url} (scope={args.scope})', flush=True)
    chassis_results = collect_chassis(client, chassis_url, full=full_scope)
    print(f'  Found {len(chassis_results)} chassis')

    systems_results = []
    if full_scope:
        print(f'Discovering Systems from {systems_url}', flush=True)
        systems_results = collect_systems(client, systems_url)
        print(f'  Found {len(systems_results)} systems')

    if full_scope:
        output = {
            'captured_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'redfish_endpoint': args.endpoint,
        }
        if chassis_results:
            output['chassis'] = chassis_results
        if systems_results:
            output['systems'] = systems_results

        with open(args.output, 'w') as f:
            yaml.dump(
                output,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True)

        print(f'Output written to: {args.output}')
    else:
        print(
            'Scope=inference-optional-nameplate: skipping raw capture output '
            '(Thermal/Systems not queried); only writing the nameplate power YAML.')

    if args.nameplate_output:
        nameplate = build_nameplate_power(chassis_results, args.system_name)
        if nameplate is None:
            print(
                'WARNING: No PSU data found on any chassis — nameplate power '
                'YAML not written. Check that the BMC exposes Chassis/<id>/Power '
                'or Chassis/<id>/PowerSubsystem with PowerSupplies.',
                file=sys.stderr)
        else:
            with open(args.nameplate_output, 'w') as f:
                yaml.dump(
                    nameplate,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True)
            print(f'Nameplate power YAML written to: {args.nameplate_output}')


if __name__ == '__main__':
    main()
