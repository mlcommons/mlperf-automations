from mlc import utils
import os
import json
import statistics
from utils import is_true


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    logger = i['automation'].logger

    results_dir = env.get('MLC_PYPERFORMANCE_RESULTS_DIR', os.getcwd())
    os.makedirs(results_dir, exist_ok=True)
    env['MLC_PYPERFORMANCE_RESULTS_DIR'] = results_dir

    if is_true(env.get('MLC_PYPERFORMANCE_REUSE_LOGS', '')):
        logger.info("Reuse logs mode: skipping execution")
        return {'return': 0}

    python_bin = env.get('MLC_PYPERFORMANCE_PYTHON', '').strip()
    if not python_bin:
        # Use the Python detected by MLC
        python_bin = env.get('MLC_PYTHON_BIN_WITH_PATH', 'python3')
    env['MLC_PYPERFORMANCE_PYTHON'] = python_bin

    benchmarks = env.get('MLC_PYPERFORMANCE_BENCHMARKS', '')
    if benchmarks:
        logger.info(f"pyperformance benchmarks: {benchmarks}")
    else:
        logger.info("pyperformance: running full suite")

    compare_json = env.get('MLC_PYPERFORMANCE_COMPARE_JSON', '').strip()
    if compare_json:
        if not os.path.isfile(compare_json):
            logger.warning(f"Comparison baseline not found: {compare_json}")
        else:
            logger.info(f"Will compare against baseline: {compare_json}")

    return {'return': 0}


def postprocess(i):

    env = i['env']
    logger = i['automation'].logger
    state = i['state']

    results_dir = env.get('MLC_PYPERFORMANCE_RESULTS_DIR', '')
    num_runs = int(env.get('MLC_PYPERFORMANCE_NUM_RUNS', '1'))

    all_results = []

    for run in range(1, num_runs + 1):
        json_file = os.path.join(results_dir, f'pyperformance_run{run}.json')
        if os.path.isfile(json_file):
            try:
                with open(json_file, 'r') as f:
                    result = json.load(f)
                result['_run'] = run
                all_results.append(result)
                logger.info(f"Loaded pyperformance results: run {run}")
            except Exception as e:
                logger.warning(f"Could not parse {json_file}: {e}")
        else:
            logger.warning(f"Results file not found: {json_file}")

    if not all_results:
        logger.warning("No pyperformance results found.")
        return {'return': 0}

    # Extract per-benchmark geometric mean timings
    benchmark_times = {}
    for r in all_results:
        benchmarks = r.get('benchmarks', [])
        for bench in benchmarks:
            name = bench.get('metadata', {}).get('name', 'unknown')
            runs = bench.get('runs', [])
            # Get the mean of values for this benchmark
            values = []
            for run_data in runs:
                vals = run_data.get('values', [])
                values.extend(vals)
            if values:
                mean_time = statistics.mean(values)
                benchmark_times.setdefault(name, []).append(mean_time)

    # Build summary
    summary = {
        'num_runs': num_runs,
        'runs_completed': len(all_results),
        'benchmarks': {},
    }

    for name, times in benchmark_times.items():
        summary['benchmarks'][name] = {
            'mean_time_s': round(statistics.mean(times), 6),
            'min_time_s': round(min(times), 6),
        }

    # Compute geometric mean across all benchmarks
    all_means = [v['mean_time_s'] for v in summary['benchmarks'].values() if v['mean_time_s'] > 0]
    if all_means:
        geo_mean = _geometric_mean(all_means)
        summary['geometric_mean_s'] = round(geo_mean, 6)
        env['MLC_PYPERFORMANCE_GEOMETRIC_MEAN'] = str(round(geo_mean, 6))
        logger.info(f"pyperformance geometric mean: {geo_mean:.6f}s ({len(all_means)} benchmarks)")

    summary['total_benchmarks'] = len(benchmark_times)

    summary_json = os.path.join(results_dir, 'pyperformance_summary.json')
    with open(summary_json, 'w') as f:
        json.dump(summary, f, indent=2)
    env['MLC_PYPERFORMANCE_SUMMARY_JSON'] = summary_json

    state['pyperformance_results'] = all_results
    state['pyperformance_summary'] = summary

    return {'return': 0}


def _geometric_mean(values):
    """Compute geometric mean of a list of positive numbers."""
    import math
    if not values:
        return 0
    log_sum = sum(math.log(v) for v in values)
    return math.exp(log_sum / len(values))
