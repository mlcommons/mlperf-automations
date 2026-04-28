from mlc import utils
import os
import json
import re
import statistics
from utils import is_true


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    logger = i['automation'].logger

    results_dir = env.get('MLC_SYSBENCH_RESULTS_DIR', os.getcwd())
    os.makedirs(results_dir, exist_ok=True)
    env['MLC_SYSBENCH_RESULTS_DIR'] = results_dir

    if is_true(env.get('MLC_SYSBENCH_REUSE_LOGS', '')):
        logger.info("Reuse logs mode: skipping execution")
        return {'return': 0}

    # Check sysbench is installed
    check_cmd = 'which sysbench' if os_info['platform'] != 'windows' else 'where sysbench'
    if os.system(f'{check_cmd} > /dev/null 2>&1' if os_info['platform'] != 'windows'
                 else f'{check_cmd} > nul 2>&1') != 0:
        return {'return': 1,
                'error': 'sysbench is not installed. '
                         'Install via: sudo apt install sysbench'}

    test = env.get('MLC_SYSBENCH_TEST', 'cpu')
    logger.info(f"Sysbench test: {test}, threads={env.get('MLC_SYSBENCH_NUM_THREADS', '1')}")

    return {'return': 0}


def postprocess(i):

    env = i['env']
    logger = i['automation'].logger
    state = i['state']

    results_dir = env.get('MLC_SYSBENCH_RESULTS_DIR', '')
    num_runs = int(env.get('MLC_SYSBENCH_NUM_RUNS', '3'))

    all_results = []

    for run in range(1, num_runs + 1):
        txt_file = os.path.join(results_dir, f'sysbench_run{run}.txt')
        if os.path.isfile(txt_file):
            result = _parse_sysbench_output(txt_file)
            if result:
                result['_run'] = run
                all_results.append(result)
                logger.info(f"Parsed Sysbench results: run {run}")
        else:
            logger.warning(f"Results file not found: {txt_file}")

    if not all_results:
        logger.warning("No Sysbench results found.")
        return {'return': 0}

    # Aggregate key metrics
    summary = {
        'test': env.get('MLC_SYSBENCH_TEST', ''),
        'num_runs': num_runs,
        'runs_completed': len(all_results),
    }

    # CPU test: events per second
    eps_list = [r['events_per_second'] for r in all_results if 'events_per_second' in r]
    if eps_list:
        summary['events_per_second'] = {
            'mean': round(statistics.mean(eps_list), 2),
            'max': round(max(eps_list), 2),
            'min': round(min(eps_list), 2),
        }
        env['MLC_SYSBENCH_EVENTS_PER_SEC'] = str(round(statistics.mean(eps_list), 2))
        logger.info(f"Sysbench events/sec: mean={statistics.mean(eps_list):.2f}")

    # Memory test: transfer rate
    transfer_list = [r['transfer_mib_s'] for r in all_results if 'transfer_mib_s' in r]
    if transfer_list:
        summary['transfer_mib_s'] = {
            'mean': round(statistics.mean(transfer_list), 2),
            'max': round(max(transfer_list), 2),
        }
        env['MLC_SYSBENCH_TRANSFER_MIB_S'] = str(round(statistics.mean(transfer_list), 2))

    # Latency
    lat_list = [r['latency_avg_ms'] for r in all_results if 'latency_avg_ms' in r]
    if lat_list:
        summary['latency_avg_ms'] = {
            'mean': round(statistics.mean(lat_list), 4),
        }

    summary_json = os.path.join(results_dir, 'sysbench_summary.json')
    with open(summary_json, 'w') as f:
        json.dump(summary, f, indent=2)
    env['MLC_SYSBENCH_SUMMARY_JSON'] = summary_json

    state['sysbench_results'] = all_results
    state['sysbench_summary'] = summary

    return {'return': 0}


def _parse_sysbench_output(filepath):
    """Parse sysbench text output for key metrics."""
    result = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()

            # events per second
            m = re.search(r'events per second:\s+([\d.]+)', line)
            if m:
                result['events_per_second'] = float(m.group(1))

            # total number of events
            m = re.search(r'total number of events:\s+(\d+)', line)
            if m:
                result['total_events'] = int(m.group(1))

            # total time
            m = re.search(r'total time:\s+([\d.]+)s', line)
            if m:
                result['total_time_s'] = float(m.group(1))

            # latency avg
            m = re.search(r'avg:\s+([\d.]+)', line)
            if m and 'latency_avg_ms' not in result:
                result['latency_avg_ms'] = float(m.group(1))

            # latency p95
            m = re.search(r'95th percentile:\s+([\d.]+)', line)
            if m:
                result['latency_p95_ms'] = float(m.group(1))

            # memory transfer rate
            m = re.search(r'([\d.]+) MiB/sec', line)
            if m:
                result['transfer_mib_s'] = float(m.group(1))

    return result if result else None
