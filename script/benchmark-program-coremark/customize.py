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

    results_dir = env.get('MLC_COREMARK_RESULTS_DIR', os.getcwd())
    os.makedirs(results_dir, exist_ok=True)
    env['MLC_COREMARK_RESULTS_DIR'] = results_dir
    env['MLC_RUN_DIR'] = results_dir

    if is_true(env.get('MLC_COREMARK_REUSE_LOGS', '')):
        logger.info("Reuse logs mode: skipping build and execution")
        return {'return': 0}

    compiler = env.get('MLC_COREMARK_COMPILER', 'gcc')
    extra_cflags = env.get('MLC_COREMARK_EXTRA_CFLAGS', '')
    num_threads = env.get('MLC_COREMARK_NUM_THREADS', '1')
    iterations = env.get('MLC_COREMARK_ITERATIONS', '0')

    iter_flag = f"ITERATIONS={iterations}" if iterations != '0' else ''

    if num_threads == '0':
        import multiprocessing
        num_threads = str(multiprocessing.cpu_count())

    compile_cmd = (
        f"make PORT_DIR=linux "
        f"CC={compiler} "
        f'XCFLAGS="-DMULTITHREAD={num_threads} -DUSE_PTHREAD -pthread {extra_cflags}" '
        f"{iter_flag} "
        f"clean compile"
    )

    env['MLC_COREMARK_COMPILE_CMD'] = compile_cmd
    logger.info(f"CoreMark compile command: {compile_cmd}")

    return {'return': 0}


def postprocess(i):

    env = i['env']
    logger = i['automation'].logger
    state = i['state']

    results_dir = env.get('MLC_COREMARK_RESULTS_DIR', '')
    num_runs = int(env.get('MLC_COREMARK_NUM_RUNS', '3'))

    all_results = []

    for run in range(1, num_runs + 1):
        txt_file = os.path.join(results_dir, f'coremark_run{run}.txt')
        if os.path.isfile(txt_file):
            result = _parse_coremark_output(txt_file)
            if result:
                result['_run'] = run
                all_results.append(result)
                logger.info(f"Parsed CoreMark results: run {run}")
        else:
            logger.warning(f"Results file not found: {txt_file}")

    if not all_results:
        logger.warning("No CoreMark results found.")
        return {'return': 0}

    scores = [r['iterations_per_sec'] for r in all_results if 'iterations_per_sec' in r]

    summary = {
        'num_runs': num_runs,
        'runs_completed': len(all_results),
        'iterations_per_sec': {
            'mean': round(statistics.mean(scores), 2),
            'max': round(max(scores), 2),
            'min': round(min(scores), 2),
        } if scores else {},
        'individual_results': all_results,
    }

    if scores:
        env['MLC_COREMARK_SCORE'] = str(round(max(scores), 2))
        logger.info(f"CoreMark best: {max(scores):.2f} iterations/sec")

    summary_json = os.path.join(results_dir, 'coremark_summary.json')
    with open(summary_json, 'w') as f:
        json.dump(summary, f, indent=2)
    env['MLC_COREMARK_SUMMARY_JSON'] = summary_json

    state['coremark_results'] = all_results
    state['coremark_summary'] = summary

    return {'return': 0}


def _parse_coremark_output(filepath):
    result = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            m = re.search(r'CoreMark 1\.0 : (\d+\.?\d*)', line)
            if m:
                result['iterations_per_sec'] = float(m.group(1))
            m = re.search(r'Iterations\s*:\s*(\d+)', line)
            if m:
                result['iterations'] = int(m.group(1))
            m = re.search(r'Total ticks\s*:\s*(\d+)', line)
            if m:
                result['total_ticks'] = int(m.group(1))
            m = re.search(r'Total time \(secs\)\s*:\s*(\d+\.?\d*)', line)
            if m:
                result['total_time_s'] = float(m.group(1))
    return result if result else None
