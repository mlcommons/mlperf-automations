import json
import re

# Load the input text from the system-info.txt file
with open("system-info.txt", "r", encoding="utf-8") as f:
    data = f.read()

# Define patterns to extract key data points
extracts = {
    "uname": r"uname -a\n(.+)",
    "username": r"3\. Username\n(.+)",
    "uptime": r"2\. w\n\s+.+\s+up\s+(.+?),",
    "cpu_model": r"Model name:\s+(.+)",
    "cpu_cores": r"Core\(s\) per socket:\s+(\d+)",
    "threads_per_core": r"Thread\(s\) per core:\s+(\d+)",
    "total_cpus": r"CPU\(s\):\s+(\d+)",
    "mem_total_kb": r"MemTotal:\s+(\d+)\s+kB",
    "mem_free_kb": r"MemFree:\s+(\d+)\s+kB",
    "swap_total_kb": r"SwapTotal:\s+(\d+)\s+kB",
    "swap_free_kb": r"SwapFree:\s+(\d+)\s+kB",
    "kernel_version": r"kernel.version\s+=\s+(.+)",
    "architecture": r"Architecture:\s+(\S+)",
    "boot_args": r"13\. Linux kernel boot-time arguments, from /proc/cmdline\n(.+)",
    "bios_vendor": r"Vendor:\s+(.+)",
    "bios_version": r"Version:\s+([\d\.]+)",
    "bios_release_date": r"Release Date:\s+(.+)",
    "cpu_frequency_range": r"hardware limits:\s+(.+)",
    "virtualization": r"Virtualization:\s+(.+)",
    "l1d_cache": r"L1d cache:\s+(.+)",
    "l2_cache": r"L2 cache:\s+(.+)",
    "l3_cache": r"L3 cache:\s+(.+)",
    "numa_nodes": r"NUMA node\(s\):\s+(\d+)",
    "runlevel": r"who -r\n\s+run-level\s+(\d+)",
    "systemd_version": r"Systemd service manager version\n(.+)",
    "max_mhz": r"CPU max MHz:\s+([\d\.]+)",
    "min_mhz": r"CPU min MHz:\s+([\d\.]+)",
    "bogomips": r"BogoMIPS:\s+([\d\.]+)",
    "cache_alignment": r"cache_alignment\s+:\s+(\d+)",
    "address_sizes": r"Address sizes:\s+(.+)",
    "numactl_total_mem_mb": r"node 0 size:\s+(\d+)\s+MB",
    "dimm_actual_speed": r"Speed:\s+(\d+)\s+MT/s",
    "dimm_configured_speed": r"Configured Memory Speed:\s+(\d+)\s+MT/s"
}

# Extract matched values
results = []
for key, pattern in extracts.items():
    match = re.search(pattern, data)
    if match:
        results.append({"key": key, "value": match.group(1)})

# Add derived field: number of services
services = re.findall(r"\.service", data)
results.append({"key": "total_services_detected", "value": len(services)})

# Output as JSON array
json_output = json.dumps(results, indent=2)
print(json_output)
