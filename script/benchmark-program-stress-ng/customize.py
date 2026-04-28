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

    results_dir = env.get('MLC_STRESSNG_RESULTS_DIR', os.getcwd())
    os.makedirs(results_dir, exist_ok=True)
    env['MLC_STRESSNG_RESULTS_DIR'] = results_dir

    if is_true(env.get('MLC_STRESSNG_REUSE_LOGS', '')):
        logger.info("Reuse logs mode: skipping execution")
        return {'return': 0}

    # Check stress-ng is installed
    check_cmd = 'which stress-ng' if os_info['platform'] != 'windows' else 'where stress-ng'
    if os.system(f'{check_cmd} > /dev/null 2>&1' if os_info['platform'] != 'windows'
                 else f'{check_cmd} > nul 2>&1') != 0:
        return {'return': 1,
                'error': 'stress-ng is not installed. '
                         'Install via: sudo apt install stress-ng'}

    stressor = env.get('MLC_STRESSNG_STRESSOR', 'cpu')
    logger.info(f"stress-ng stressor: {stressor}, workers={env.get('MLC_STRESSNG_WORKERS', '0')}")

    return {'return': 0}


def postprocess(i):

    env = i['env']
    logger = i['automation'].logger
    state = i['state']

    results_dir = env.get('MLC_STRESSNG_RESULTS_DIR', '')
    num_runs = int(env.get('MLC_STRESSNG_NUM_RUNS', '3'))

    all_results = []

    for run in range(1, num_runs + 1):
        txt_file = os.path.join(results_dir, f'stressng_run{run}.txt')
        if os.path.isfile(txt_file):
            result = _parse_stressng_output(txt_file)
            if result:
                result['_run'] = run
                all_results.append(result)
                logger.info(f"Parsed stress-ng results: run {run}")

        # Also try YAML output
        yaml_file = os.path.join(results_dir, f'stressng_run{run}.yaml')
        if os.path.isfile(yaml_file):
            env[f'MLC_STRESSNG_YAML_RUN{run}'] = yaml_file

    if not all_results:
        logger.warning("No stress-ng results found.")
        return {'return': 0}

    # Aggregate bogo ops
    bogo_ops_list = [r['bogo_ops_per_sec'] for r in all_results if 'bogo_ops_per_sec' in r]

    summary = {
        'stressor': env.get('MLC_STRESSNG_STRESSOR', ''),
        'num_runs': num_runs,
        'runs_completed': len(all_results),
    }

    if bogo_ops_list:
        summary['bogo_ops_per_sec'] = {
            'mean': round(statistics.mean(bogo_ops_list), 2),
            'max': round(max(bogo_ops_list), 2),
            'min': round(min(bogo_ops_list), 2),
        }
        env['MLC_STRESSNG_BOGO_OPS_PER_SEC'] = str(round(statistics.mean(bogo_ops_list), 2))
        logger.info(f"stress-ng bogo ops/sec: mean={statistics.mean(bogo_ops_list):.2f}")

    summary_json = os.path.join(results_dir, 'stressng_summary.json')
    with open(summary_json, 'w') as f:
        json.dump(summary, f, indent=2)
    env['MLC_STRESSNG_SUMMARY_JSON'] = summary_json

    state['stressng_results'] = all_results
    state['stressng_summary'] = summary

    return {'return': 0}


def _parse_stressng_output(filepath):
    """Parse stress-ng text output for metrics-brief results."""
    result = {}
    with open(filepath, 'r') as f:
        for line in f:
            # Format: stress-ng: info:  [pid] stressor  bogo ops  real time  usr time  sys time  bogo ops/s  bogo ops/s
            # Look for the bogo ops/s (real time) value
            m = re.search(
                r'(\w+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*$',
                line.strip()
            )
            if m:
                result['stressor'] = m.group(1)
                result['bogo_ops'] = int(m.group(2))
                result['real_time'] = float(m.group(3))
                result['usr_time'] = float(m.group(4))
                result['sys_time'] = float(m.group(5))
                result['bogo_ops_per_sec'] = float(m.group(6))
                result['bogo_ops_per_sec_usr_sys'] = float(m.group(7))

    return result if result else None
