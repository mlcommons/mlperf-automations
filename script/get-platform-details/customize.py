from mlc import utils
import os
import json
import re
import subprocess


def check_installation(command, os_info):
    if os_info['platform'] == "windows":
        return subprocess.call(
            [command, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True) == 0
    elif os_info['platform'] == "linux":
        return subprocess.call(['which', command], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE) == 0


def preprocess(i):

    os_info = i['os_info']
    env = i['env']

    if os_info['platform'] == 'linux':
        if not check_installation("numactl", os_info):
            env['MLC_INSTALL_NUMACTL'] = 'True'
        env['MLC_INSTALL_CPUPOWER'] = 'True'

    if env.get('MLC_PLATFORM_DETAILS_FILE_PATH', '') == '':
        if env.get('MLC_PLATFORM_DETAILS_DIR_PATH', '') == '':
            env['MLC_PLATFORM_DETAILS_DIR_PATH'] = os.getcwd()
        if env.get('MLC_PLATFORM_DETAILS_FILE_NAME', '') == '':
            env['MLC_PLATFORM_DETAILS_FILE_NAME'] = "system-info.json"
        env['MLC_PLATFORM_DETAILS_FILE_PATH'] = os.path.join(
            env['MLC_PLATFORM_DETAILS_DIR_PATH'], env['MLC_PLATFORM_DETAILS_FILE_NAME'])

    # Derive the raw file path from the parsed file path
    base, ext = os.path.splitext(env['MLC_PLATFORM_DETAILS_FILE_PATH'])
    env['MLC_PLATFORM_DETAILS_RAW_FILE_PATH'] = base + '-raw' + ext

    return {'return': 0}


def postprocess(i):

    state = i['state']
    env = i['env']
    os_info = i['os_info']
    automation = i['automation']

    raw_path = env.get('MLC_PLATFORM_DETAILS_RAW_FILE_PATH', '')
    parsed_path = env.get('MLC_PLATFORM_DETAILS_FILE_PATH', '')

    if not raw_path or not os.path.isfile(raw_path):
        return {'return': 0}

    try:
        with open(raw_path, 'r') as f:
            raw = json.load(f)
    except Exception:
        return {'return': 0}

    structured = _build_structured(raw, os_info.get('platform', 'linux'))

    with open(parsed_path, 'w') as f:
        json.dump(structured, f, indent=2)

    return {'return': 0}


# =====================================================================
# Parsing helpers
# =====================================================================

def _safe_int(val, default=0):
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _safe_float(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _get_output(raw, key):
    """Get the output string for a raw entry, stripped."""
    entry = raw.get(key, {})
    if isinstance(entry, dict):
        return entry.get('output', '').strip()
    return ''


def _parse_key_value_colon(text):
    """Parse lines of 'Key:  Value' into a dict."""
    result = {}
    for line in text.splitlines():
        if ':' in line:
            key, _, val = line.partition(':')
            key = key.strip()
            val = val.strip()
            if key:
                result[key] = val
    return result


# =====================================================================
# Linux parsers
# =====================================================================

def _parse_lscpu(text):
    """Parse lscpu output into a structured dict."""
    kv = _parse_key_value_colon(text)

    cpu = {
        'architecture': kv.get('Architecture', ''),
        'op_modes': kv.get('CPU op-mode(s)', ''),
        'address_sizes': kv.get('Address sizes', ''),
        'byte_order': kv.get('Byte Order', ''),
        'total_cpus': _safe_int(kv.get('CPU(s)', '')),
        'online_cpus_list': kv.get('On-line CPU(s) list', ''),
        'vendor_id': kv.get('Vendor ID', ''),
        'model_name': kv.get('Model name', ''),
        'cpu_family': _safe_int(kv.get('CPU family', '')),
        'model': _safe_int(kv.get('Model', '')),
        'stepping': _safe_int(kv.get('Stepping', '')),
        'threads_per_core': _safe_int(kv.get('Thread(s) per core', '')),
        'cores_per_socket': _safe_int(kv.get('Core(s) per socket', '')),
        'sockets': _safe_int(kv.get('Socket(s)', '')),
        'cpu_max_mhz': _safe_float(kv.get('CPU max MHz', '')),
        'cpu_min_mhz': _safe_float(kv.get('CPU min MHz', '')),
        'bogomips': _safe_float(kv.get('BogoMIPS', '')),
        'virtualization': kv.get('Virtualization', ''),
        'flags': kv.get('Flags', '').split(),
    }

    # Cache info
    caches = {}
    for label in ['L1d cache', 'L1i cache', 'L2 cache', 'L3 cache']:
        if label in kv:
            caches[label.replace(' cache', '').replace(' ', '_').lower()] = kv[label]
    cpu['caches'] = caches

    # NUMA
    cpu['numa_nodes'] = _safe_int(kv.get('NUMA node(s)', ''))
    for k, v in kv.items():
        if k.startswith('NUMA node') and 'CPU(s)' in k:
            node_id = k.replace('NUMA node', '').replace(' CPU(s)', '').strip()
            cpu.setdefault('numa_cpu_map', {})[f'node{node_id}'] = v

    # Vulnerabilities
    vulns = {}
    for k, v in kv.items():
        if k.startswith('Vulnerability '):
            vuln_name = k.replace('Vulnerability ', '')
            vulns[vuln_name] = v
    cpu['vulnerabilities'] = vulns

    return cpu


def _parse_meminfo(text):
    """Parse /proc/meminfo into a clean structured dict."""
    raw_entries = {}
    for line in text.splitlines():
        m = re.match(r'(\S+):\s+(\d+)\s*(\S*)', line)
        if m:
            raw_entries[m.group(1)] = _safe_int(m.group(2))

    def _kb_to_gb(key):
        v = raw_entries.get(key, 0)
        return round(v / 1048576, 2) if v else 0

    return {
        'total_kb': raw_entries.get('MemTotal', 0),
        'total_gb': _kb_to_gb('MemTotal'),
        'free_kb': raw_entries.get('MemFree', 0),
        'free_gb': _kb_to_gb('MemFree'),
        'available_kb': raw_entries.get('MemAvailable', 0),
        'available_gb': _kb_to_gb('MemAvailable'),
        'buffers_kb': raw_entries.get('Buffers', 0),
        'cached_kb': raw_entries.get('Cached', 0),
        'swap_total_kb': raw_entries.get('SwapTotal', 0),
        'swap_total_gb': _kb_to_gb('SwapTotal'),
        'swap_free_kb': raw_entries.get('SwapFree', 0),
        'swap_free_gb': _kb_to_gb('SwapFree'),
        'huge_pages_total': raw_entries.get('HugePages_Total', 0),
        'huge_pages_free': raw_entries.get('HugePages_Free', 0),
        'huge_page_size_kb': raw_entries.get('Hugepagesize', 0),
        'dirty_kb': raw_entries.get('Dirty', 0),
        'shmem_kb': raw_entries.get('Shmem', 0),
    }


def _parse_os_release(text):
    """Parse /etc/os-release or macOS sw_vers style output into a dict."""
    result = {}
    for line in text.splitlines():
        if '=' in line:
            key, _, val = line.partition('=')
            result[key.strip()] = val.strip().strip('"')
    return result


def _parse_numa(text):
    """Parse numactl --hardware output."""
    result = {}
    m = re.search(r'available:\s+(\d+)\s+nodes', text)
    if m:
        result['available_nodes'] = _safe_int(m.group(1))

    nodes = []
    for node_match in re.finditer(r'node\s+(\d+)\s+cpus:\s*(.+)', text):
        node_id = _safe_int(node_match.group(1))
        cpus = node_match.group(2).strip()
        size_match = re.search(rf'node\s+{node_id}\s+size:\s+(\d+)\s+MB', text)
        free_match = re.search(rf'node\s+{node_id}\s+free:\s+(\d+)\s+MB', text)
        nodes.append({
            'node_id': node_id,
            'cpus': cpus,
            'size_mb': _safe_int(size_match.group(1)) if size_match else 0,
            'free_mb': _safe_int(free_match.group(1)) if free_match else 0,
        })
    result['nodes'] = nodes
    return result


def _parse_cpu_cache_table(text):
    """Parse lscpu --cache table output."""
    lines = text.strip().splitlines()
    if not lines:
        return []
    headers = lines[0].split()
    caches = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= len(headers):
            entry = {}
            for i, h in enumerate(headers):
                entry[h.lower()] = parts[i]
            caches.append(entry)
    return caches


def _parse_disk_layout(text):
    """Parse lsblk output into a list of disks."""
    disks = []
    for line in text.strip().splitlines():
        parts = line.split(None, 6)
        if len(parts) >= 3:
            disk = {'name': parts[0], 'type': parts[1], 'size': parts[2]}
            if len(parts) >= 4:
                disk['model'] = parts[3]
            if len(parts) >= 5:
                disk['transport'] = parts[4]
            if len(parts) >= 6:
                disk['rotational'] = parts[5]
            if len(parts) >= 7:
                disk['vendor'] = parts[6]
            disks.append(disk)
    return disks


def _parse_ulimit(text):
    """Parse ulimit -a output."""
    result = {}
    for line in text.splitlines():
        m = re.match(r'(.+?)\s+\(([^)]+)\)\s+(\S+)$', line.strip())
        if m:
            name = m.group(1).strip()
            flag = m.group(2).strip()
            value = m.group(3).strip()
            key = name.lower().replace(' ', '_').replace('-', '_')
            result[key] = {'description': name, 'flag': flag, 'value': value}
    return result


def _parse_cpu_frequency(text):
    """Parse cpupower frequency-info output."""
    result = {}
    m = re.search(r'driver:\s+(\S+)', text)
    if m:
        result['driver'] = m.group(1)
    m = re.search(r'hardware limits:\s+(.+)', text)
    if m:
        result['hardware_limits'] = m.group(1).strip()
    m = re.search(r'available cpufreq governors:\s+(.+)', text)
    if m:
        result['available_governors'] = m.group(1).strip().split()
    m = re.search(r'current CPU frequency:.*?(\d[\d.]+\s*\w+)\s*\(asserted', text)
    if m:
        result['current_frequency'] = m.group(1).strip()

    # Current policy
    m = re.search(r'current policy:.*?frequency should be within (.+?) and ([\d.]+ [A-Za-z]+)', text, re.DOTALL)
    if m:
        result['policy_min'] = m.group(1).strip()
        result['policy_max'] = m.group(2).strip()

    # Boost info
    boost = {}
    m = re.search(r'Supported:\s+(yes|no)', text)
    if m:
        boost['supported'] = m.group(1) == 'yes'
    m = re.search(r'Active:\s+(yes|no)', text)
    if m:
        boost['active'] = m.group(1) == 'yes'
    m = re.search(r'Maximum Frequency:\s+([\d.]+ [A-Za-z]+)', text)
    if m:
        boost['max_frequency'] = m.group(1).strip()
    m = re.search(r'Nominal.*?Frequency:\s+([\d.]+ [A-Za-z]+)', text)
    if m:
        boost['nominal_frequency'] = m.group(1).strip()
    m = re.search(r'Lowest Non-linear.*?Frequency:\s+([\d.]+ [A-Za-z]+)', text)
    if m:
        boost['lowest_nonlinear_frequency'] = m.group(1).strip()
    m = re.search(r'Lowest Frequency:\s+([\d.]+ [A-Za-z]+)', text)
    if m:
        boost['lowest_frequency'] = m.group(1).strip()
    if boost:
        result['boost'] = boost

    return result


def _parse_dmidecode_bios(text):
    """Parse dmidecode -t bios for BIOS info."""
    result = {}
    kv = _parse_key_value_colon(text)
    for key in ['Vendor', 'Version', 'Release Date', 'Address', 'Runtime Size', 'ROM Size',
                'BIOS Revision']:
        if key in kv:
            result[key.lower().replace(' ', '_')] = kv[key]
    return result


def _parse_dmidecode_memory(text):
    """Parse dmidecode output for Memory Device entries (DMI type 17)."""
    dimms = []
    sections = re.split(r'\nHandle ', text)
    for section in sections:
        if 'Memory Device' not in section:
            continue
        kv = _parse_key_value_colon(section)
        size = kv.get('Size', '')
        if not size or size == 'No Module Installed':
            continue
        if 'Type' not in kv:
            continue
        dimm = {}
        for key in ['Size', 'Form Factor', 'Locator', 'Bank Locator', 'Type',
                     'Speed', 'Manufacturer', 'Part Number', 'Rank',
                     'Configured Memory Speed', 'Minimum Voltage', 'Maximum Voltage',
                     'Configured Voltage', 'Memory Technology', 'Total Width', 'Data Width',
                     'Serial Number']:
            if key in kv:
                dimm[key.lower().replace(' ', '_')] = kv[key]
        dimms.append(dimm)
    return dimms


def _parse_dmidecode_system(text):
    """Parse dmidecode for System Information, Base Board, and Chassis."""
    result = {}
    sections = re.split(r'\nHandle ', text)
    for section in sections:
        if 'System Information' in section:
            kv = _parse_key_value_colon(section)
            sys_info = {}
            for key in ['Manufacturer', 'Product Name', 'Version', 'UUID', 'Wake-up Type',
                        'SKU Number', 'Family']:
                if key in kv:
                    val = kv[key]
                    if val != 'Default string':
                        sys_info[key.lower().replace(' ', '_').replace('-', '_')] = val
            if sys_info:
                result['system'] = sys_info
        elif 'Base Board Information' in section:
            kv = _parse_key_value_colon(section)
            board = {}
            for key in ['Manufacturer', 'Product Name', 'Version', 'Serial Number', 'Type']:
                if key in kv:
                    val = kv[key]
                    if val != 'Default string':
                        board[key.lower().replace(' ', '_')] = val
            if board:
                result['baseboard'] = board
        elif 'Chassis Information' in section:
            kv = _parse_key_value_colon(section)
            chassis = {}
            for key in ['Manufacturer', 'Type', 'Lock']:
                if key in kv:
                    val = kv[key]
                    if val != 'Default string':
                        chassis[key.lower()] = val
            if chassis:
                result['chassis'] = chassis
    return result


def _parse_thp(text):
    """Parse transparent hugepage setting. E.g. '[always] madvise never' -> 'always'."""
    m = re.search(r'\[(\w+)\]', text)
    if m:
        return m.group(1)
    return text.strip()


def _parse_cpu_vulnerabilities(text):
    """Parse /sys/devices/system/cpu/vulnerabilities/ output."""
    result = {}
    for line in text.splitlines():
        m = re.match(r'.*/vulnerabilities/(\S+):(.+)', line)
        if m:
            result[m.group(1).strip()] = m.group(2).strip()
    return result


def _parse_memory_free_human(text):
    """Parse 'free -h' output into structured dict."""
    result = {}
    lines = text.strip().splitlines()
    if len(lines) < 2:
        return result
    headers = lines[0].split()
    for line in lines[1:]:
        parts = line.split()
        if not parts:
            continue
        row_name = parts[0].rstrip(':').lower()
        row = {}
        for i, h in enumerate(headers):
            if i + 1 < len(parts):
                row[h.lower()] = parts[i + 1]
        result[row_name] = row
    return result


def _parse_sysctl_key_settings(text):
    """Extract commonly interesting sysctl settings from sysctl -a output."""
    interesting_keys = [
        'vm.swappiness', 'vm.dirty_ratio', 'vm.dirty_background_ratio',
        'vm.overcommit_memory', 'vm.overcommit_ratio', 'vm.nr_hugepages',
        'vm.max_map_count', 'vm.zone_reclaim_mode',
        'kernel.shmmax', 'kernel.shmall', 'kernel.shmmni',
        'kernel.threads-max', 'kernel.pid_max', 'kernel.sched_migration_cost_ns',
        'kernel.numa_balancing', 'kernel.randomize_va_space',
        'net.core.somaxconn', 'net.core.rmem_max', 'net.core.wmem_max',
        'net.ipv4.tcp_max_syn_backlog', 'net.ipv4.ip_local_port_range',
    ]
    kv = {}
    for line in text.splitlines():
        if ' = ' in line:
            key, _, val = line.partition(' = ')
            kv[key.strip()] = val.strip()
    return {k: kv[k] for k in interesting_keys if k in kv}


# =====================================================================
# macOS parsers
# =====================================================================

def _parse_sysctl_hw(text):
    """Parse macOS 'sysctl hw' output into a CPU/hardware dict."""
    kv = {}
    for line in text.splitlines():
        if ':' in line:
            key, _, val = line.partition(':')
            kv[key.strip()] = val.strip()

    cpu = {
        'model_name': kv.get('machdep.cpu.brand_string', ''),
        'total_cpus': _safe_int(kv.get('hw.ncpu', kv.get('hw.logicalcpu', ''))),
        'physical_cpus': _safe_int(kv.get('hw.physicalcpu', '')),
        'logical_cpus': _safe_int(kv.get('hw.logicalcpu', '')),
        'cpu_family': kv.get('machdep.cpu.family', ''),
        'cpu_model': kv.get('machdep.cpu.model', ''),
        'stepping': kv.get('machdep.cpu.stepping', ''),
        'vendor_id': kv.get('machdep.cpu.vendor', ''),
        'cpu_freq_hz': _safe_int(kv.get('hw.cpufrequency', '')),
        'l1d_cache': _safe_int(kv.get('hw.l1dcachesize', '')),
        'l1i_cache': _safe_int(kv.get('hw.l1icachesize', '')),
        'l2_cache': _safe_int(kv.get('hw.l2cachesize', '')),
        'l3_cache': _safe_int(kv.get('hw.l3cachesize', '')),
        'memory_bytes': _safe_int(kv.get('hw.memsize', '')),
    }

    mem_bytes = cpu.pop('memory_bytes', 0)
    memory = {}
    if mem_bytes:
        memory['total_bytes'] = mem_bytes
        memory['total_gb'] = round(mem_bytes / (1024 ** 3), 2)

    return cpu, memory


def _parse_system_profiler(text):
    """Parse macOS system_profiler SPHardwareDataType output."""
    kv = _parse_key_value_colon(text)
    result = {}
    for key in ['Model Name', 'Model Identifier', 'Chip', 'Total Number of Cores',
                'Memory', 'System Firmware Version', 'OS Loader Version',
                'Serial Number (system)', 'Hardware UUID', 'Provisioning UDID']:
        if key in kv:
            result[key.lower().replace(' ', '_').replace('(', '').replace(')', '')] = kv[key]
    return result


def _parse_sw_vers(text):
    """Parse macOS sw_vers output."""
    result = {}
    for line in text.splitlines():
        if ':' in line:
            key, _, val = line.partition(':')
            result[key.strip().lower().replace(' ', '_')] = val.strip()
    return result


def _parse_diskutil(text):
    """Parse macOS diskutil list output into a simple list."""
    disks = []
    current_disk = None
    for line in text.splitlines():
        m = re.match(r'^(/dev/\S+)\s+\((\w+).*?\):', line)
        if m:
            current_disk = {'device': m.group(1), 'type': m.group(2)}
            disks.append(current_disk)
        elif current_disk and line.strip():
            m2 = re.match(r'\s+\d+:\s+(\S+)\s+(.+?)\s+([\d.]+\s+\S+)\s+(\S+)', line)
            if m2:
                current_disk.setdefault('partitions', []).append({
                    'type': m2.group(1),
                    'name': m2.group(2).strip(),
                    'size': m2.group(3),
                    'identifier': m2.group(4),
                })
    return disks


def _parse_macos_sysctl_settings(text):
    """Extract interesting macOS sysctl settings."""
    interesting_keys = [
        'kern.maxproc', 'kern.maxfiles', 'kern.maxfilesperproc',
        'kern.hostname', 'kern.ostype', 'kern.osrelease', 'kern.osrevision',
        'kern.version', 'kern.boottime', 'vm.swapusage',
        'machdep.cpu.core_count', 'machdep.cpu.thread_count',
        'machdep.cpu.features', 'machdep.cpu.leaf7_features',
    ]
    kv = {}
    for line in text.splitlines():
        if ':' in line:
            key, _, val = line.partition(':')
            kv[key.strip()] = val.strip()
    return {k: kv[k] for k in interesting_keys if k in kv}


# =====================================================================
# Windows parsers
# =====================================================================

def _parse_systeminfo(text):
    """Parse Windows systeminfo output."""
    kv = _parse_key_value_colon(text)
    result = {}
    for key in ['Host Name', 'OS Name', 'OS Version', 'OS Manufacturer',
                'OS Configuration', 'OS Build Type', 'Registered Owner',
                'System Manufacturer', 'System Model', 'System Type',
                'BIOS Version', 'Total Physical Memory', 'Available Physical Memory',
                'Virtual Memory: Max Size', 'Virtual Memory: Available',
                'Virtual Memory: In Use', 'Domain', 'Logon Server',
                'Boot Device', 'System Directory', 'Original Install Date',
                'System Boot Time', 'Time Zone']:
        if key in kv:
            result[key.lower().replace(' ', '_').replace(':', '_').replace('__', '_')] = kv[key]
    return result


def _parse_windows_cpu(text):
    """Parse Windows CPU info (from Get-CimInstance or wmic)."""
    result = {}
    kv = _parse_key_value_colon(text)
    for key in ['Name', 'Manufacturer', 'MaxClockSpeed', 'CurrentClockSpeed',
                'NumberOfCores', 'NumberOfLogicalProcessors', 'L2CacheSize',
                'L3CacheSize', 'Architecture', 'Caption', 'DeviceID',
                'ProcessorId', 'SocketDesignation', 'AddressWidth',
                'VirtualizationFirmwareEnabled']:
        if key in kv:
            result[key.lower()] = kv[key]
    # Unify
    cpu = {
        'model_name': result.get('name', result.get('caption', '')),
        'manufacturer': result.get('manufacturer', ''),
        'total_cpus': _safe_int(result.get('numberoflogicalprocessors', '')),
        'cores': _safe_int(result.get('numberofcores', '')),
        'max_clock_mhz': _safe_int(result.get('maxclockspeed', '')),
        'current_clock_mhz': _safe_int(result.get('currentclockspeed', '')),
        'l2_cache_kb': _safe_int(result.get('l2cachesize', '')),
        'l3_cache_kb': _safe_int(result.get('l3cachesize', '')),
        'socket': result.get('socketdesignation', ''),
        'address_width': _safe_int(result.get('addresswidth', '')),
    }
    return cpu


def _parse_windows_memory(text):
    """Parse Windows memory info (from Get-CimInstance Win32_PhysicalMemory)."""
    dimms = []
    current = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            if current:
                dimms.append(current)
                current = {}
            continue
        if ':' in line:
            key, _, val = line.partition(':')
            key = key.strip().lower()
            val = val.strip()
            if key and val:
                current[key] = val
    if current:
        dimms.append(current)

    result = []
    for d in dimms:
        dimm = {}
        capacity = _safe_int(d.get('capacity', '0'))
        if capacity:
            dimm['size_gb'] = round(capacity / (1024 ** 3), 2)
        for k in ['manufacturer', 'partnumber', 'speed', 'memorytype',
                   'formfactor', 'banklabel', 'devicelocator', 'serialnumber']:
            if k in d:
                dimm[k] = d[k]
        if dimm:
            result.append(dimm)
    return result


def _parse_windows_disk(text):
    """Parse Windows disk info (from Get-CimInstance Win32_DiskDrive)."""
    disks = []
    current = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            if current:
                disks.append(current)
                current = {}
            continue
        if ':' in line:
            key, _, val = line.partition(':')
            key = key.strip().lower()
            val = val.strip()
            if key and val:
                current[key] = val
    if current:
        disks.append(current)

    result = []
    for d in disks:
        disk = {}
        size = _safe_int(d.get('size', '0'))
        if size:
            disk['size_gb'] = round(size / (1024 ** 3), 2)
        for k in ['model', 'mediatype', 'interfacetype', 'serialnumber', 'caption']:
            if k in d:
                disk[k] = d[k]
        if disk:
            result.append(disk)
    return result


# =====================================================================
# Build structured JSON
# =====================================================================

def _build_structured(raw, platform='linux'):
    """Build a well-structured JSON from the raw command outputs."""
    structured = {'platform': platform}

    if platform == 'linux':
        _build_linux(raw, structured)
    elif platform == 'darwin':
        _build_macos(raw, structured)
    elif platform == 'windows':
        _build_windows(raw, structured)

    return structured


def _build_linux(raw, structured):
    """Parse Linux command outputs."""
    # CPU
    lscpu_text = _get_output(raw, 'lscpu')
    if lscpu_text:
        structured['cpu'] = _parse_lscpu(lscpu_text)

    cache_text = _get_output(raw, 'cpu_cache')
    if cache_text:
        structured['cpu_cache_topology'] = _parse_cpu_cache_table(cache_text)

    freq_text = _get_output(raw, 'cpu_frequency')
    if freq_text:
        structured['cpu_frequency'] = _parse_cpu_frequency(freq_text)

    vuln_text = _get_output(raw, 'cpu_vulnerabilities')
    if vuln_text:
        structured['cpu_vulnerabilities'] = _parse_cpu_vulnerabilities(vuln_text)

    # Memory
    meminfo_text = _get_output(raw, 'memory_info')
    if meminfo_text:
        structured['memory'] = _parse_meminfo(meminfo_text)

    memfree_text = _get_output(raw, 'memory_free_human')
    if memfree_text:
        structured['memory_human'] = _parse_memory_free_human(memfree_text)

    # DMI
    dmi_text = _get_output(raw, 'dmidecode_full')
    if dmi_text:
        dimms = _parse_dmidecode_memory(dmi_text)
        if dimms:
            structured['memory_dimms'] = dimms
        hw_info = _parse_dmidecode_system(dmi_text)
        if hw_info:
            structured['hardware'] = hw_info

    bios_text = _get_output(raw, 'bios_info')
    if bios_text:
        structured['bios'] = _parse_dmidecode_bios(bios_text)

    # OS
    os_release_text = _get_output(raw, 'os_release')
    if os_release_text:
        structured['os'] = _parse_os_release(os_release_text)

    op_sys = _get_output(raw, 'operating_system')
    if op_sys:
        structured.setdefault('os', {})['mlc_os_string'] = op_sys

    lsb = _get_output(raw, 'lsb_release')
    if lsb:
        structured.setdefault('os', {})['lsb_description'] = lsb

    # Kernel
    kernel = {}
    uname = _get_output(raw, 'kernel_and_arch')
    if uname:
        kernel['uname'] = uname
        parts = uname.split()
        if len(parts) >= 3:
            kernel['version'] = parts[2]
    cmdline = _get_output(raw, 'kernel_cmdline')
    if cmdline:
        kernel['cmdline'] = cmdline
    if kernel:
        structured['kernel'] = kernel

    # NUMA
    numa_text = _get_output(raw, 'numa_topology')
    if numa_text:
        structured['numa'] = _parse_numa(numa_text)

    # THP
    thp = {}
    thp_enabled = _get_output(raw, 'thp_enabled')
    if thp_enabled:
        thp['enabled'] = _parse_thp(thp_enabled)
    thp_defrag = _get_output(raw, 'thp_defrag')
    if thp_defrag:
        thp['defrag'] = thp_defrag
    if thp:
        structured['transparent_hugepages'] = thp

    # Disks
    disk_text = _get_output(raw, 'disk_layout')
    if disk_text:
        structured['disks'] = _parse_disk_layout(disk_text)

    # ulimit
    ulimit_text = _get_output(raw, 'ulimit_settings')
    if ulimit_text:
        structured['ulimits'] = _parse_ulimit(ulimit_text)

    # Systemd
    systemd = {}
    ver = _get_output(raw, 'systemd_version')
    if ver:
        systemd['version'] = ver
    units_text = _get_output(raw, 'systemd_units')
    if units_text:
        enabled = len(re.findall(r'\s+enabled\s', units_text))
        disabled = len(re.findall(r'\s+disabled\s', units_text))
        static = len(re.findall(r'\s+static\s', units_text))
        systemd['unit_counts'] = {'enabled': enabled, 'disabled': disabled, 'static': static}
    if systemd:
        structured['systemd'] = systemd

    # Sysctl
    sysctl_text = _get_output(raw, 'sysctl_all')
    if sysctl_text:
        sysctl = _parse_sysctl_key_settings(sysctl_text)
        if sysctl:
            structured['sysctl'] = sysctl

    # User / uptime
    user = _get_output(raw, 'current_user')
    if user:
        structured['current_user'] = user

    w_text = _get_output(raw, 'logged_in_users')
    if w_text:
        m = re.search(r'up\s+(.+?),\s+\d+\s+user', w_text)
        if m:
            structured['uptime'] = m.group(1).strip()
        m = re.search(r'load average:\s+(.+)', w_text)
        if m:
            structured['load_average'] = m.group(1).strip()

    # Runlevel
    runlevel_text = _get_output(raw, 'runlevel')
    if runlevel_text:
        m = re.search(r'run-level\s+(\d+)', runlevel_text)
        if m:
            structured['runlevel'] = _safe_int(m.group(1))

    # PCI devices
    pci_text = _get_output(raw, 'pci_devices')
    if pci_text and 'FAILED' not in pci_text:
        devices = []
        for line in pci_text.splitlines():
            m = re.match(r'(\S+)\s+(.+?):\s+(.+)', line)
            if m:
                devices.append({
                    'slot': m.group(1),
                    'class': m.group(2).strip(),
                    'device': m.group(3).strip(),
                })
        if devices:
            structured['pci_devices'] = devices

    # Infiniband
    ib_text = _get_output(raw, 'infiniband_status')
    if ib_text and 'FAILED' not in ib_text and 'not found' not in ib_text.lower():
        structured['infiniband'] = ib_text

    # GPU (CUDA)
    _parse_gpu_entries(raw, structured)


def _build_macos(raw, structured):
    """Parse macOS command outputs."""
    # CPU from sysctl hw
    hw_text = _get_output(raw, 'sysctl_hw')
    if hw_text:
        cpu, memory = _parse_sysctl_hw(hw_text)
        structured['cpu'] = cpu
        if memory:
            structured['memory'] = memory

    # System profiler
    profiler_text = _get_output(raw, 'system_profiler')
    if profiler_text:
        structured['hardware'] = _parse_system_profiler(profiler_text)

    # sw_vers
    swvers_text = _get_output(raw, 'sw_vers')
    if swvers_text:
        structured['os'] = _parse_sw_vers(swvers_text)

    op_sys = _get_output(raw, 'operating_system')
    if op_sys:
        structured.setdefault('os', {})['mlc_os_string'] = op_sys

    # Kernel
    uname = _get_output(raw, 'kernel_and_arch')
    if uname:
        parts = uname.split()
        structured['kernel'] = {
            'uname': uname,
            'version': parts[2] if len(parts) >= 3 else '',
        }

    # Disks
    disk_text = _get_output(raw, 'diskutil')
    if disk_text:
        structured['disks'] = _parse_diskutil(disk_text)

    # ulimit
    ulimit_text = _get_output(raw, 'ulimit_settings')
    if ulimit_text:
        structured['ulimits'] = _parse_ulimit(ulimit_text)

    # Sysctl settings
    sysctl_text = _get_output(raw, 'sysctl_all')
    if sysctl_text:
        sysctl = _parse_macos_sysctl_settings(sysctl_text)
        if sysctl:
            structured['sysctl'] = sysctl

    # User / uptime
    user = _get_output(raw, 'current_user')
    if user:
        structured['current_user'] = user

    w_text = _get_output(raw, 'logged_in_users')
    if w_text:
        m = re.search(r'up\s+(.+?),\s+\d+\s+user', w_text)
        if m:
            structured['uptime'] = m.group(1).strip()
        m = re.search(r'load average[s]?:\s+(.+)', w_text)
        if m:
            structured['load_average'] = m.group(1).strip()

    # GPU
    _parse_gpu_entries(raw, structured)


def _build_windows(raw, structured):
    """Parse Windows command outputs."""
    # systeminfo
    sysinfo_text = _get_output(raw, 'systeminfo')
    if sysinfo_text:
        structured['system'] = _parse_systeminfo(sysinfo_text)

    # CPU
    cpu_text = _get_output(raw, 'cpu_info')
    if cpu_text:
        structured['cpu'] = _parse_windows_cpu(cpu_text)

    # OS
    os_text = _get_output(raw, 'os_info')
    if os_text:
        structured['os'] = _parse_key_value_colon(os_text)

    op_sys = _get_output(raw, 'operating_system')
    if op_sys:
        structured.setdefault('os', {})['mlc_os_string'] = op_sys

    # Memory
    mem_text = _get_output(raw, 'memory_info')
    if mem_text:
        structured['memory_dimms'] = _parse_windows_memory(mem_text)

    # Disks
    disk_text = _get_output(raw, 'disk_info')
    if disk_text:
        structured['disks'] = _parse_windows_disk(disk_text)

    # Kernel
    uname = _get_output(raw, 'kernel_and_arch')
    if uname:
        structured['kernel'] = {'version': uname}

    # User
    user = _get_output(raw, 'current_user')
    if user:
        structured['current_user'] = user

    # GPU
    _parse_gpu_entries(raw, structured)


def _parse_gpu_entries(raw, structured):
    """Parse GPU/accelerator entries (shared across platforms)."""
    gpu_topo = _get_output(raw, 'nvidia_smi_topo')
    gpu_full = _get_output(raw, 'nvidia_smi_full')
    if gpu_topo or gpu_full:
        gpu = {}
        if gpu_topo:
            gpu['topology'] = gpu_topo
        if gpu_full:
            gpu['nvidia_smi_query'] = gpu_full
        structured['gpu'] = gpu
