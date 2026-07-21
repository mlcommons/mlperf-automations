#!/usr/bin/env python3
"""
Capture power and thermal data from a Redfish BMC endpoint and write to YAML.

Walks the service root dynamically — no hardcoded IDs like Chassis/1 or Systems/1.
"""

import argparse
import datetime
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
from typing import Optional

import yaml


def _make_opener(insecure: bool, username: str, password: str):
    handlers = []

    if insecure:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        handlers.append(urllib.request.HTTPSHandler(context=ctx))

    if username:
        mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        mgr.add_password(None, '', username, password)
        handlers.append(urllib.request.HTTPBasicAuthHandler(mgr))

    return urllib.request.build_opener(*handlers)


def _get(opener, url: str, timeout: int = 15) -> Optional[dict]:
    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with opener.open(req, timeout=timeout) as resp:
            raw = resp.read()
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        print(f"  HTTP {e.code} fetching {url}", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"  Error fetching {url}: {exc}", file=sys.stderr)
        return None


def _members(data: Optional[dict]) -> list[str]:
    """Extract @odata.id hrefs from a Members array."""
    if not data:
        return []
    return [m.get('@odata.id', '') for m in data.get('Members', []) if m.get('@odata.id')]


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


def _extract_psu(entry: dict) -> dict:
    out = {}
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
    # InputRanges: rated output wattage per input voltage range — the nameplate data
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
        # ReadingRPM (older Redfish) takes precedence; fallback to Reading+ReadingUnits (newer)
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


# ---------------------------------------------------------------------------
# Chassis and Systems collection
# ---------------------------------------------------------------------------

def collect_chassis(opener, base: str, chassis_url: str) -> dict:
    chassis_list = _members(_get(opener, base + chassis_url))
    results = []
    for href in chassis_list:
        chassis_id = _id_from_url(href)
        chassis_data = _get(opener, base + href)
        if not chassis_data:
            continue

        entry: dict = {'id': chassis_id}
        for k, ok in (('Name', 'name'), ('ChassisType', 'chassis_type'),
                       ('Manufacturer', 'manufacturer'), ('Model', 'model'),
                       ('SerialNumber', 'serial_number'), ('SKU', 'sku')):
            if k in chassis_data:
                entry[ok] = chassis_data[k]
        status = chassis_data.get('Status', {}) or {}
        if status.get('Health'):
            entry['health'] = status['Health']

        # Power
        power_href = (chassis_data.get('Power', {}) or {}).get('@odata.id', '')
        if not power_href:
            power_href = f'{chassis_url}/{chassis_id}/Power'
        power_data = _get(opener, base + power_href)
        if power_data:
            power_block = {}

            ctrl_list = [_extract_power_control(c)
                         for c in power_data.get('PowerControl', []) or []
                         if c]
            if ctrl_list:
                power_block['control'] = ctrl_list

            psu_list = [_extract_psu(p)
                        for p in power_data.get('PowerSupplies', []) or []
                        if p]
            if psu_list:
                power_block['power_supplies'] = psu_list

            volt_list = [_extract_voltage(v)
                         for v in power_data.get('Voltages', []) or []
                         if v]
            if volt_list:
                power_block['voltages'] = volt_list

            if power_block:
                entry['power'] = power_block

        # Thermal
        thermal_href = (chassis_data.get('Thermal', {}) or {}).get('@odata.id', '')
        if not thermal_href:
            thermal_href = f'{chassis_url}/{chassis_id}/Thermal'
        thermal_data = _get(opener, base + thermal_href)
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


def collect_systems(opener, base: str, systems_url: str) -> list:
    systems_list = _members(_get(opener, base + systems_url))
    results = []
    for href in systems_list:
        system_id = _id_from_url(href)
        data = _get(opener, base + href)
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
        description='Capture Redfish power/thermal/system info and write to YAML'
    )
    parser.add_argument('--endpoint', default='http://localhost:8000',
                        help='Redfish base URL (default: http://localhost:8000)')
    parser.add_argument('--username', default='',
                        help='BMC username (leave empty for unauthenticated mockup)')
    parser.add_argument('--password', default='',
                        help='BMC password')
    parser.add_argument('--output', default='redfish_capture.yaml',
                        help='Output YAML file path (default: redfish_capture.yaml)')
    parser.add_argument('--insecure', action='store_true', default=True,
                        help='Skip TLS certificate verification (default: true)')
    parser.add_argument('--no-insecure', dest='insecure', action='store_false',
                        help='Enforce TLS certificate verification')
    args = parser.parse_args()

    output_path = args.output
    output_dir = os.path.dirname(os.path.abspath(output_path))
    if not os.path.isdir(output_dir):
        print(f'ERROR: Output directory does not exist: {output_dir}', file=sys.stderr)
        sys.exit(1)

    base = args.endpoint.rstrip('/')
    opener = _make_opener(args.insecure, args.username, args.password)

    print(f'Connecting to Redfish endpoint: {base}', flush=True)
    service_root = _get(opener, base + '/redfish/v1/')
    if not service_root:
        print('ERROR: Could not reach Redfish service root at /redfish/v1/', file=sys.stderr)
        sys.exit(1)

    chassis_url = (service_root.get('Chassis', {}) or {}).get('@odata.id', '/redfish/v1/Chassis')
    systems_url = (service_root.get('Systems', {}) or {}).get('@odata.id', '/redfish/v1/Systems')

    print(f'Discovering Chassis from {chassis_url}', flush=True)
    chassis_results = collect_chassis(opener, base, chassis_url)
    print(f'  Found {len(chassis_results)} chassis')

    print(f'Discovering Systems from {systems_url}', flush=True)
    systems_results = collect_systems(opener, base, systems_url)
    print(f'  Found {len(systems_results)} systems')

    output = {
        'captured_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'redfish_endpoint': base,
    }
    if chassis_results:
        output['chassis'] = chassis_results
    if systems_results:
        output['systems'] = systems_results

    with open(output_path, 'w') as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f'Output written to: {output_path}')


if __name__ == '__main__':
    main()
