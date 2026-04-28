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

    results_dir = env.get('MLC_STREAM_RESULTS_DIR', os.getcwd())
    os.makedirs(results_dir, exist_ok=True)
    env['MLC_STREAM_RESULTS_DIR'] = results_dir
    env['MLC_RUN_DIR'] = results_dir

    if is_true(env.get('MLC_STREAM_REUSE_LOGS', '')):
        logger.info("Reuse logs mode: skipping compilation and execution")
        return {'return': 0}

    array_size = env.get('MLC_STREAM_ARRAY_SIZE', '80000000')
    ntimes = env.get('MLC_STREAM_NTIMES', '20')
    compiler = env.get('MLC_STREAM_COMPILER', 'gcc')
    extra_cflags = env.get('MLC_STREAM_EXTRA_CFLAGS', '')
    use_openmp = is_true(env.get('MLC_STREAM_USE_OPENMP', ''))

    # Download STREAM source if not present
    stream_c = os.path.join(results_dir, 'stream.c')
    if not os.path.isfile(stream_c):
        download_cmd = (
            f"curl -L -o {stream_c} "
            "https://raw.githubusercontent.com/jeffhammond/STREAM/master/stream.c"
        )
        logger.info(f"Downloading STREAM source: {download_cmd}")
        os.system(download_cmd)
        if not os.path.isfile(stream_c):
            return {'return': 1, 'error': 'Failed to download STREAM source'}

    # Build compile command
    cflags = f"-O3 -DSTREAM_ARRAY_SIZE={array_size} -DNTIMES={ntimes}"
    if use_openmp:
        cflags += " -fopenmp"
    if extra_cflags:
        cflags += f" {extra_cflags}"

    if os_info['platform'] == 'windows':
        compile_cmd = f"cl /O2 /DSTREAM_ARRAY_SIZE={array_size} /DNTIMES={ntimes} {extra_cflags} stream.c /Fe:stream.exe"
    else:
        compile_cmd = f"{compiler} {cflags} stream.c -o stream -lm"

    env['MLC_STREAM_COMPILE_CMD'] = compile_cmd
    logger.info(f"STREAM compile command: {compile_cmd}")

    return {'return': 0}


def postprocess(i):

    env = i['env']
    logger = i['automation'].logger
    state = i['state']

    results_dir = env.get('MLC_STREAM_RESULTS_DIR', '')
    num_runs = int(env.get('MLC_STREAM_NUM_RUNS', '3'))

    all_results = []

    for run in range(1, num_runs + 1):
        txt_file = os.path.join(results_dir, f'stream_run{run}.txt')
        if os.path.isfile(txt_file):
            result = _parse_stream_output(txt_file)
            if result:
                result['_run'] = run
                all_results.append(result)
                logger.info(f"Parsed STREAM results: run {run}")
        else:
            logger.warning(f"Results file not found: {txt_file}")

    if not all_results:
        logger.warning("No STREAM results found.")
        return {'return': 0}

    # Aggregate across runs
    functions = ['Copy', 'Scale', 'Add', 'Triad']
    summary = {'num_runs': num_runs, 'runs_completed': len(all_results)}

    for func in functions:
        best_rates = [r[func]['best_rate'] for r in all_results if func in r]
        avg_times = [r[func]['avg_time'] for r in all_results if func in r]
        if best_rates:
            summary[func] = {
                'best_rate_mb_s': {
                    'mean': round(statistics.mean(best_rates), 2),
                    'max': round(max(best_rates), 2),
                    'min': round(min(best_rates), 2),
                },
                'avg_time_s': {
                    'mean': round(statistics.mean(avg_times), 6),
                }
            }
            env[f'MLC_STREAM_{func.upper()}_BEST_RATE'] = str(round(max(best_rates), 2))
            logger.info(f"STREAM {func}: best={max(best_rates):.2f} MB/s, mean={statistics.mean(best_rates):.2f} MB/s")

    summary_json = os.path.join(results_dir, 'stream_summary.json')
    with open(summary_json, 'w') as f:
        json.dump(summary, f, indent=2)
    env['MLC_STREAM_SUMMARY_JSON'] = summary_json

    state['stream_results'] = all_results
    state['stream_summary'] = summary

    return {'return': 0}


def _parse_stream_output(filepath):
    """Parse STREAM text output to extract bandwidth and timing results."""
    result = {}
    pattern = re.compile(
        r'^(Copy|Scale|Add|Triad):\s+'
        r'(\d+\.?\d*)\s+'
        r'(\d+\.?\d*)\s+'
        r'(\d+\.?\d*)\s+'
        r'(\d+\.?\d*)'
    )
    with open(filepath, 'r') as f:
        for line in f:
            m = pattern.match(line.strip())
            if m:
                func = m.group(1)
                result[func] = {
                    'best_rate': float(m.group(2)),
                    'avg_time': float(m.group(3)),
                    'min_time': float(m.group(4)),
                    'max_time': float(m.group(5)),
                }
    return result if result else None
