from mlc import utils
import os
import json
import statistics
from utils import is_true


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    logger = i['automation'].logger

    results_dir = env.get('MLC_FIO_RESULTS_DIR', os.getcwd())
    os.makedirs(results_dir, exist_ok=True)
    env['MLC_FIO_RESULTS_DIR'] = results_dir

    if is_true(env.get('MLC_FIO_REUSE_LOGS', '')):
        logger.info("Reuse logs mode: skipping execution")
        return {'return': 0}

    # Check fio is installed
    check_cmd = 'which fio' if os_info['platform'] != 'windows' else 'where fio'
    if os.system(f'{check_cmd} > /dev/null 2>&1' if os_info['platform'] != 'windows'
                 else f'{check_cmd} > nul 2>&1') != 0:
        return {'return': 1,
                'error': 'fio is not installed. '
                         'Install via: sudo apt install fio (Linux) '
                         'or download from https://github.com/axboe/fio'}

    rw = env.get('MLC_FIO_RW', 'randread')
    logger.info(f"FIO workload: {rw}, bs={env.get('MLC_FIO_BS', '4k')}, "
                f"size={env.get('MLC_FIO_SIZE', '1G')}")

    return {'return': 0}


def postprocess(i):

    env = i['env']
    logger = i['automation'].logger
    state = i['state']

    results_dir = env.get('MLC_FIO_RESULTS_DIR', '')
    num_runs = int(env.get('MLC_FIO_NUM_RUNS', '3'))

    all_results = []

    for run in range(1, num_runs + 1):
        json_file = os.path.join(results_dir, f'fio_run{run}.json')
        if os.path.isfile(json_file):
            try:
                with open(json_file, 'r') as f:
                    result = json.load(f)
                result['_run'] = run
                all_results.append(result)
                logger.info(f"Loaded FIO results: run {run}")
            except Exception as e:
                logger.warning(f"Could not parse {json_file}: {e}")
        else:
            logger.warning(f"Results file not found: {json_file}")

    if not all_results:
        logger.warning("No FIO results found.")
        return {'return': 0}

    # Extract key metrics
    read_iops_list = []
    write_iops_list = []
    read_bw_list = []
    write_bw_list = []

    for r in all_results:
        jobs = r.get('jobs', [])
        if jobs:
            job = jobs[0]
            read_data = job.get('read', {})
            write_data = job.get('write', {})
            if read_data.get('iops', 0) > 0:
                read_iops_list.append(read_data['iops'])
                read_bw_list.append(read_data.get('bw', 0))  # KB/s
            if write_data.get('iops', 0) > 0:
                write_iops_list.append(write_data['iops'])
                write_bw_list.append(write_data.get('bw', 0))

    summary = {
        'num_runs': num_runs,
        'runs_completed': len(all_results),
        'workload': env.get('MLC_FIO_RW', ''),
    }

    if read_iops_list:
        summary['read_iops'] = {
            'mean': round(statistics.mean(read_iops_list), 2),
            'max': round(max(read_iops_list), 2),
        }
        summary['read_bw_kbs'] = {
            'mean': round(statistics.mean(read_bw_list), 2),
        }
        env['MLC_FIO_READ_IOPS'] = str(round(statistics.mean(read_iops_list), 2))
        logger.info(f"FIO read IOPS: mean={statistics.mean(read_iops_list):.2f}")

    if write_iops_list:
        summary['write_iops'] = {
            'mean': round(statistics.mean(write_iops_list), 2),
            'max': round(max(write_iops_list), 2),
        }
        summary['write_bw_kbs'] = {
            'mean': round(statistics.mean(write_bw_list), 2),
        }
        env['MLC_FIO_WRITE_IOPS'] = str(round(statistics.mean(write_iops_list), 2))
        logger.info(f"FIO write IOPS: mean={statistics.mean(write_iops_list):.2f}")

    summary_json = os.path.join(results_dir, 'fio_summary.json')
    with open(summary_json, 'w') as f:
        json.dump(summary, f, indent=2)
    env['MLC_FIO_SUMMARY_JSON'] = summary_json

    state['fio_results'] = all_results
    state['fio_summary'] = summary

    return {'return': 0}
