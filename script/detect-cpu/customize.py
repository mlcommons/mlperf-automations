from mlc import utils
import json
import os
import re
from collections import defaultdict

lscpu_out = 'tmp-lscpu.out'
_cpu_freq_raw = 'cpu-freq-capture.raw'
_cpu_freq_pid = 'cpu-freq-capture.pid'

_FREQ_LINE_RE = re.compile(
    r'(.+?)\s+HW active frequency:\s+([\d.]+)\s*MHz', re.IGNORECASE)


def _cpu_freq_capture_mode(env):
    return str(env.get('MLC_CPU_FREQ_CAPTURE_MODE', '')).strip()


def _cpu_freq_capture_dir(env):
    for key in ('MLC_CPU_FREQ_CAPTURE_DIR', 'MLC_PLATFORM_DETAILS_DIR_PATH'):
        value = str(env.get(key, '')).strip()
        if value:
            return value
    return os.getcwd()


def _setup_cpu_freq_capture(env, os_info):
    if os_info.get('platform') != 'darwin':
        return
    if not _cpu_freq_capture_mode(env):
        return

    capture_dir = _cpu_freq_capture_dir(env)
    os.makedirs(capture_dir, exist_ok=True)
    env['MLC_CPU_FREQ_CAPTURE_OUTPUT_FILE'] = os.path.join(
        capture_dir, _cpu_freq_raw)
    env['MLC_CPU_FREQ_CAPTURE_PID_FILE'] = os.path.join(
        capture_dir, _cpu_freq_pid)


def _parse_hw_active_frequency(text):
    """Parse powermetrics 'HW active frequency' lines into per-cluster samples."""
    samples = []
    for line in text.splitlines():
        if 'HW active frequency' not in line:
            continue
        match = _FREQ_LINE_RE.search(line)
        if not match:
            continue
        cluster = match.group(1).strip().strip('*').strip() or 'cpu'
        samples.append({
            'cluster': cluster,
            'mhz': float(match.group(2)),
            'raw_line': line.strip(),
        })
    return samples


def _summarize_cpu_freq_samples(samples):
    by_cluster = defaultdict(list)
    for sample in samples:
        by_cluster[sample['cluster']].append(sample['mhz'])

    clusters = {}
    for cluster, values in sorted(by_cluster.items()):
        clusters[cluster] = {
            'min_mhz': round(min(values), 2),
            'max_mhz': round(max(values), 2),
            'avg_mhz': round(sum(values) / len(values), 2),
            'samples': len(values),
        }
    return clusters


def _build_cpu_frequency_data(text, env):
    mode = _cpu_freq_capture_mode(env)
    samples = _parse_hw_active_frequency(text)
    interval_ms = env.get('MLC_CPU_FREQ_CAPTURE_INTERVAL_MS', '500')

    if mode == 'sample':
        command = "sudo powermetrics -s cpu_power -n 1 | grep 'HW active frequency'"
    else:
        command = (
            f"sudo powermetrics -s cpu_power -i {interval_ms} -n 0 "
            "(background workload capture)"
        )

    result = {
        'source': 'powermetrics',
        'capture_mode': mode,
        'command': command,
        'sample_interval_ms': int(interval_ms) if str(interval_ms).isdigit() else interval_ms,
    }

    if samples:
        result['clusters'] = _summarize_cpu_freq_samples(samples)
        if mode != 'sample':
            result['workload_samples'] = samples
        else:
            result['snapshot'] = samples

    if not samples and text.strip():
        result['raw_output'] = text.strip()

    return result


def _merge_cpu_frequency_into_platform_file(platform_file, freq_data):
    if os.path.isfile(platform_file):
        with open(platform_file, 'r') as handle:
            data = json.load(handle)
    else:
        data = {'platform': 'darwin'}

    data['cpu_frequency'] = freq_data

    with open(platform_file, 'w') as handle:
        json.dump(data, handle, indent=2)


def _postprocess_cpu_freq_capture(env, os_info, logger):
    if os_info.get('platform') != 'darwin':
        return

    mode = _cpu_freq_capture_mode(env)
    if mode not in ('stop', 'sample'):
        return

    output_file = env.get('MLC_CPU_FREQ_CAPTURE_OUTPUT_FILE', '')
    platform_file = env.get('MLC_PLATFORM_DETAILS_FILE_PATH', '')
    if not output_file or not os.path.isfile(output_file):
        logger.warning('CPU frequency capture output not found; skipping platform merge')
        return
    if not platform_file:
        logger.warning('MLC_PLATFORM_DETAILS_FILE_PATH not set; skipping platform merge')
        return

    with open(output_file, 'r') as handle:
        text = handle.read()

    freq_data = _build_cpu_frequency_data(text, env)
    if not freq_data.get('clusters') and not freq_data.get('raw_output'):
        logger.warning('No HW active frequency data captured from powermetrics')
        return

    _merge_cpu_frequency_into_platform_file(platform_file, freq_data)
    logger.info(f'CPU frequency merged into {platform_file}')


def preprocess(i):

    env = i['env']
    os_info = i['os_info']

    if os.path.isfile(lscpu_out):
        os.remove(lscpu_out)

    _setup_cpu_freq_capture(env, os_info)

    return {'return': 0}


def postprocess(i):

    state = i['state']

    env = i['env']

    os_info = i['os_info']

    automation = i['automation']
    logger = automation.action_object.logger

    if os_info['platform'] == 'windows':
        sys = []
        sys1 = []
        cpu = []
        cpu1 = []

        import csv

        try:
            f = 'tmp-systeminfo.csv'

            if not os.path.isfile(f):
                logger.warning('{} file was not generated!'.format(f))
            else:
                keys = {}
                j = 0
                # Try UTF-8 first (PowerShell), fallback to system encoding
                # (WMIC)
                try:
                    csvfile = open(f, 'r', encoding='utf-8-sig')
                except BaseException:
                    csvfile = open(f, 'r')

                with csvfile as csvf:
                    for s in csv.reader(csvf):
                        if j == 0:
                            keys = s
                        else:
                            x = {}
                            for k in range(0, len(s)):
                                x[keys[k]] = s[k]

                            sys.append(x)

                            if j == 1:
                                sys1 = x

                        j += 1

        except Exception as e:
            logger.warning(
                'Problem processing file {} ({})!'.format(
                    f, format(e)))
            pass

        try:
            f = 'tmp-wmic-cpu.csv'
            if not os.path.isfile(f):
                logger.warning('{} file was not generated!'.format(f))
            else:

                keys = {}
                j = 0

                # Try UTF-8 first (PowerShell), fallback to UTF-16 (WMIC)
                try:
                    csvfile = open(f, 'r', encoding='utf-8-sig')
                except BaseException:
                    csvfile = open(f, 'r', encoding='utf16')

                with csvfile as csvf:
                    for s in csv.reader(csvf):
                        if j == 1:
                            keys = s
                        elif j > 1:
                            x = {}
                            for k in range(0, len(s)):
                                x[keys[k]] = s[k]

                            cpu.append(x)

                            if j == 2:
                                cpu1 = x

                        j += 1

        except Exception as e:
            logger.warning(
                'Problem processing file {} ({})!'.format(
                    f, format(e)))
            pass

        state['host_device_raw_info'] = {
            'sys': sys, 'sys1': sys1, 'cpu': cpu, 'cpu1': cpu1}

    ##########################################################################
    # Process lscpu output (both Linux and Windows)
    if not os.path.isfile(lscpu_out):
        logger.warning('lscpu.out file was not generated!')

        # Currently ignore this error though probably should fail?
        # But need to check that is supported on all platforms.
        _postprocess_cpu_freq_capture(env, os_info, logger)
        return {'return': 0}

    r = utils.load_txt(file_name=lscpu_out)
    if r['return'] > 0:
        _postprocess_cpu_freq_capture(env, os_info, logger)
        return r

    ss = r['string']

    # state['cpu_info_raw'] = ss

    # Unifying some CPU info across different platforms
    unified_env = {
        'MLC_CPUINFO_CPUs': 'MLC_HOST_CPU_TOTAL_CORES',
        'MLC_CPUINFO_L1d_cache': 'MLC_HOST_CPU_L1D_CACHE_SIZE',
        'MLC_CPUINFO_L1i_cache': 'MLC_HOST_CPU_L1I_CACHE_SIZE',
        'MLC_CPUINFO_L2_cache': 'MLC_HOST_CPU_L2_CACHE_SIZE',
        'MLC_CPUINFO_L3_cache': 'MLC_HOST_CPU_L3_CACHE_SIZE',
        'MLC_CPUINFO_Sockets': 'MLC_HOST_CPU_SOCKETS',
        'MLC_CPUINFO_NUMA_nodes': 'MLC_HOST_CPU_NUMA_NODES',
        'MLC_CPUINFO_Cores_per_socket': 'MLC_HOST_CPU_PHYSICAL_CORES_PER_SOCKET',
        'MLC_CPUINFO_Cores_per_cluster': 'MLC_HOST_CPU_PHYSICAL_CORES_PER_SOCKET',
        'MLC_CPUINFO_Threads_per_core': 'MLC_HOST_CPU_THREADS_PER_CORE',
        'MLC_CPUINFO_Architecture': 'MLC_HOST_CPU_ARCHITECTURE',
        'MLC_CPUINFO_CPU_family': 'MLC_HOST_CPU_FAMILY',
        'MLC_CPUINFO_CPU_max_MHz': 'MLC_HOST_CPU_MAX_MHZ',
        'MLC_CPUINFO_Model_name': 'MLC_HOST_CPU_MODEL_NAME',
        'MLC_CPUINFO_On_line_CPUs_list': 'MLC_HOST_CPU_ON_LINE_CPUS_LIST',
        'MLC_CPUINFO_Vendor_ID': 'MLC_HOST_CPU_VENDOR_ID',
        'MLC_CPUINFO_hw_physicalcpu': 'MLC_HOST_CPU_TOTAL_PHYSICAL_CORES',
        'MLC_CPUINFO_hw_logicalcpu': 'MLC_HOST_CPU_TOTAL_CORES',
        'MLC_CPUINFO_hw_packages': 'MLC_HOST_CPU_SOCKETS',
        'MLC_CPUINFO_hw_memsize': 'MLC_HOST_CPU_MEMSIZE',
        'MLC_CPUINFO_hw_l1icachesize': 'MLC_HOST_CPU_L1I_CACHE_SIZE',
        'MLC_CPUINFO_hw_l1dcachesize': 'MLC_HOST_CPU_L1D_CACHE_SIZE',
        'MLC_CPUINFO_hw_l2cachesize': 'MLC_HOST_CPU_L2_CACHE_SIZE'
    }

    vkeys = []
    if env.get('MLC_HOST_OS_TYPE',
               '') == 'linux' or os_info['platform'] == 'windows':
        vkeys = ['Architecture', 'Model name', 'Vendor ID', 'CPU family', 'NUMA node(s)', 'CPU(s)',
                 'On-line CPU(s) list', 'Socket(s)', 'Core(s) per socket', 'Core(s) per cluster', 'Thread(s) per core', 'L1d cache', 'L1i cache', 'L2 cache',
                 'L3 cache', 'CPU max MHz']
    elif env.get('MLC_HOST_OS_FLAVOR', '') == 'macos':
        vkeys = ['hw.physicalcpu', 'hw.logicalcpu', 'hw.packages', 'hw.ncpu', 'hw.memsize', 'hw.l1icachesize',
                 'hw.l2cachesize']
    if vkeys:
        for s in ss.split('\n'):
            # Split only on first colon to handle values with colons
            v = s.split(':', 1)
            if len(v) < 2:
                continue
            key = v[0].strip()
            value = v[1].strip()
            if key in vkeys:
                env_key = 'MLC_CPUINFO_' + key.replace(
                    " ",
                    "_").replace(
                    '(',
                    '').replace(
                    ')',
                    '').replace(
                    '-',
                    '_').replace(
                    '.',
                    '_')
                if env_key in unified_env:
                    env[unified_env[env_key]] = value
                else:
                    env[env_key] = value

    # get start cores
    matches = re.findall(r"NUMA node\d+ CPU\(s\):\s+([\d,-]+)", ss)
    start_cores = []
    for cpu_range in matches:
        # Example: '0-15,32-47' or '0-15'
        for part in cpu_range.split(','):
            start = part.split('-')[0]
            start_cores.append(start)
    if start_cores:
        env['MLC_HOST_CPU_START_CORES'] = ','.join(start_cores)

    if env.get('MLC_HOST_CPU_SOCKETS', '') in ['-', '']:  # assume as 1
        env['MLC_HOST_CPU_SOCKETS'] = '1'

    if env.get('MLC_HOST_CPU_TOTAL_CORES', '') != '' and env.get(
            'MLC_HOST_CPU_TOTAL_LOGICAL_CORES', '') == '':
        env['MLC_HOST_CPU_TOTAL_LOGICAL_CORES'] = env['MLC_HOST_CPU_TOTAL_CORES']

    if env.get('MLC_HOST_CPU_TOTAL_LOGICAL_CORES', '') != '' and env.get(
            'MLC_HOST_CPU_TOTAL_PHYSICAL_CORES', '') != '' and env.get('MLC_HOST_CPU_THREADS_PER_CORE', '') == '':
        env['MLC_HOST_CPU_THREADS_PER_CORE'] = str(int(int(env['MLC_HOST_CPU_TOTAL_LOGICAL_CORES']) //
                                                       int(env['MLC_HOST_CPU_TOTAL_PHYSICAL_CORES'])))

    if env.get('MLC_HOST_CPU_TOTAL_PHYSICAL_CORES', '') != '' and env.get(
            'MLC_HOST_CPU_PHYSICAL_CORES_PER_SOCKET', '') == '':
        env['MLC_HOST_CPU_PHYSICAL_CORES_PER_SOCKET'] = str(
            int(env['MLC_HOST_CPU_TOTAL_PHYSICAL_CORES']) // int(env['MLC_HOST_CPU_SOCKETS']))

    if env.get('MLC_HOST_CPU_TOTAL_PHYSICAL_CORES', '') == '' and env.get(
            'MLC_HOST_CPU_PHYSICAL_CORES_PER_SOCKET', '') != '':
        env['MLC_HOST_CPU_TOTAL_PHYSICAL_CORES'] = str(int(
            env['MLC_HOST_CPU_PHYSICAL_CORES_PER_SOCKET']) * int(env['MLC_HOST_CPU_SOCKETS']))

    if env.get('MLC_HOST_CPU_TOTAL_PHYSICAL_CORES', '') != '':
        env['MLC_HOST_CPU_PHYSICAL_CORES_LIST'] = f"""0-{int(env['MLC_HOST_CPU_TOTAL_PHYSICAL_CORES'])-1}"""

    _postprocess_cpu_freq_capture(env, os_info, logger)

    return {'return': 0}
