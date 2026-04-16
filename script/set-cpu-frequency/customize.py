from mlc import utils
import os
import shutil
import subprocess
import re

def preprocess(i):

    env = i['env']
    state = i['state']

    # Check that cpupower is available
    if shutil.which('cpupower') is None:
        return {'return': 1, 'error': "'cpupower' utility not found. Please install it (e.g., 'sudo apt install linux-tools-common linux-tools-generic' on Ubuntu, 'sudo dnf install kernel-tools' on Fedora/RHEL)."}

    # Check that cpufreq is available on this system
    driver_file = '/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver'
    if not os.path.exists(driver_file):
        return {'return': 1, 'error': f"cpufreq not available on this system ({driver_file} does not exist). This can happen in VMs, containers, or if the kernel lacks cpufreq support."}

    freq = env.get('MLC_TARGET_FREQ', '').strip()
    if freq != '':
        try:
            freq = parse_target_freq(freq)
        except ValueError as e:
            return {'return': 1, 'error': str(e)}

    os_info = i['os_info']

    return {'return': 0}


def parse_target_freq(raw: str) -> int | None:
    """
    Parse a freq string like '2300KHz', '2.3GHz', '2500M' or a plain integer
    into an integer number of kHz. Returns None if the env var is empty.
    """
    if not raw:
        return None

    # match <number>[.<fraction>][unit], unit = k/M/G (case-insensitive),
    # optional "Hz"
    m = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)([KMGkmg])(?:[Hh][Zz])?", raw)
    if m:
        val, unit = m.group(1), m.group(2).lower()
        val = float(val)
        if unit == "g":
            khz = int(val * 1_000_000)
        elif unit == "m":
            khz = int(val * 1_000)
        else:  # "k"
            khz = int(val)
        return khz

    # plain integer? treat as kHz
    if raw.isdigit():
        return int(raw)

    raise ValueError(f"Invalid frequency format: '{raw}'")


def postprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    return {'return': 0}
