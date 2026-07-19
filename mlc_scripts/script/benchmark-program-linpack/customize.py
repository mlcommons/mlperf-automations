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

    results_dir = env.get('MLC_LINPACK_RESULTS_DIR', os.getcwd())
    os.makedirs(results_dir, exist_ok=True)
    env['MLC_LINPACK_RESULTS_DIR'] = results_dir
    env['MLC_RUN_DIR'] = results_dir

    if is_true(env.get('MLC_LINPACK_REUSE_LOGS', '')):
        logger.info("Reuse logs mode: skipping execution")
        return {'return': 0}

    variant = env.get('MLC_LINPACK_VARIANT', 'xhpl')

    if variant == 'intel-mp':
        # Intel MP Linpack (from Intel oneAPI)
        run_cmd = 'xhpl_intel64_dynamic'
    else:
        # Standard HPL - check if xhpl is available
        run_cmd = './xhpl'

    env['MLC_LINPACK_RUN_CMD'] = run_cmd
    logger.info(f"Linpack variant: {variant}, run command: {run_cmd}")
    logger.info(f"Problem size: {env.get('MLC_LINPACK_PROBLEM_SIZE', '20000')}")

    return {'return': 0}


def postprocess(i):

    env = i['env']
    logger = i['automation'].logger
    state = i['state']

    results_dir = env.get('MLC_LINPACK_RESULTS_DIR', '')
    num_runs = int(env.get('MLC_LINPACK_NUM_RUNS', '3'))

    all_results = []

    for run in range(1, num_runs + 1):
        txt_file = os.path.join(results_dir, f'linpack_run{run}.txt')
        if os.path.isfile(txt_file):
            result = _parse_hpl_output(txt_file)
            if result:
                result['_run'] = run
                all_results.append(result)
                logger.info(f"Parsed Linpack results: run {run}")
        else:
            logger.warning(f"Results file not found: {txt_file}")

    if not all_results:
        logger.warning("No Linpack results found.")
        return {'return': 0}

    gflops_list = [r['gflops'] for r in all_results if 'gflops' in r]

    summary = {
        'num_runs': num_runs,
        'runs_completed': len(all_results),
        'gflops': {
            'mean': round(statistics.mean(gflops_list), 4),
            'max': round(max(gflops_list), 4),
            'min': round(min(gflops_list), 4),
        } if gflops_list else {},
        'individual_results': all_results,
    }

    if gflops_list:
        env['MLC_LINPACK_GFLOPS'] = str(round(max(gflops_list), 4))
        logger.info(f"Linpack best: {max(gflops_list):.4f} GFLOPS")

    summary_json = os.path.join(results_dir, 'linpack_summary.json')
    with open(summary_json, 'w') as f:
        json.dump(summary, f, indent=2)
    env['MLC_LINPACK_SUMMARY_JSON'] = summary_json

    state['linpack_results'] = all_results
    state['linpack_summary'] = summary

    return {'return': 0}


def _parse_hpl_output(filepath):
    """Parse HPL output to extract GFLOPS and timing."""
    result = {}
    # HPL output line format:
    # WR11C2R4     20000   256     1     1             xxx.xx             yyy.yye+zz
    pattern = re.compile(
        r'WR\w+\s+(\d+)\s+(\d+)\s+\d+\s+\d+\s+([\d.]+)\s+([\d.eE+\-]+)'
    )
    with open(filepath, 'r') as f:
        for line in f:
            m = pattern.search(line)
            if m:
                result['n'] = int(m.group(1))
                result['nb'] = int(m.group(2))
                result['time_s'] = float(m.group(3))
                result['gflops'] = float(m.group(4))

            # Check pass/fail
            if 'PASSED' in line:
                result['passed'] = True
            elif 'FAILED' in line:
                result['passed'] = False

    return result if result else None
