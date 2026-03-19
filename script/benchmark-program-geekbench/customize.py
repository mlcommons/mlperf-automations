from mlc import utils
import os
import json
import csv
import statistics
import datetime
from utils import is_true


def compute_olympic_score(values):
    """Drop the highest and lowest values, then return the mean of the rest.
    If fewer than 3 values, return the plain mean."""
    if not values:
        return 0
    if len(values) < 3:
        return statistics.mean(values)
    sorted_vals = sorted(values)
    trimmed = sorted_vals[1:-1]
    return statistics.mean(trimmed)


def extract_scores(result):
    """Extract top-level score fields from a geekbench result dict.
    Handles both Geekbench 5 and 6 JSON formats."""
    scores = {}

    # Geekbench 5 / generic format
    if 'score' in result:
        scores['score'] = result['score']
    if 'multicore_score' in result:
        scores['multicore_score'] = result['multicore_score']
    if 'single_core_score' in result:
        scores['single_core_score'] = result['single_core_score']

    # Geekbench 6 nested format
    if 'single_core' in result and isinstance(result['single_core'], dict):
        sc = result['single_core'].get('score')
        if sc is not None:
            scores['single_core_score'] = sc
    if 'multi_core' in result and isinstance(result['multi_core'], dict):
        mc = result['multi_core'].get('score')
        if mc is not None:
            scores['multicore_score'] = mc

    return scores


def extract_workload_scores(result):
    """Extract per-section and per-workload scores from a geekbench result dict.
    Returns a dict keyed by section name, each containing section score and
    per-workload details including per-iteration runtimes.

    Geekbench's --iterations N flag results in 1 warmup iteration + (N-1)
    scored iterations. The 'runtimes' list contains per-scored-iteration
    runtimes, and 'runtime' is their mean. 'runtime_warmup' is the warmup
    iteration runtime."""
    sections_data = {}
    for section in result.get('sections', []):
        sec_name = section.get('name', 'Unknown')
        sec_info = {
            'section_score': section.get('score', 0),
            'workloads': {}
        }
        for wl in section.get('workloads', []):
            wl_name = wl.get('name', 'Unknown')
            runtimes_list = wl.get('runtimes', [])
            sec_info['workloads'][wl_name] = {
                'score': wl.get('score', 0),
                'runtime': wl.get('runtime', 0),
                'runtime_warmup': wl.get('runtime_warmup', 0),
                'runtimes': [round(r, 6) for r in runtimes_list],
                'iterations_scored': len(runtimes_list),
            }
        sections_data[sec_name] = sec_info
    return sections_data


def merge_sc_mc_results(sc_result, mc_result):
    """Merge single-core and multi-core JSON results into one combined result.
    The SC run has only Single-Core section, MC run has only Multi-Core section.
    The merged result looks like a normal full run with both sections."""
    merged = dict(sc_result)  # Start from SC as base
    # Combine sections from both
    merged['sections'] = list(sc_result.get(
        'sections', [])) + list(mc_result.get('sections', []))
    # Set top-level scores from both
    if 'score' in sc_result:
        merged['score'] = sc_result['score']
    if 'multicore_score' in mc_result:
        merged['multicore_score'] = mc_result['multicore_score']
    elif 'score' in mc_result:
        merged['multicore_score'] = mc_result['score']
    return merged


def compute_stats(values):
    """Compute mean, median, olympic, cv_percent, min, max for a list of numeric values."""
    if not values:
        return {}
    mean_val = round(statistics.mean(values), 2)
    stdev_val = round(statistics.stdev(values), 2) if len(values) >= 2 else 0
    result = {
        'mean': mean_val,
        'median': round(statistics.median(values), 2),
        'olympic': round(compute_olympic_score(values), 2),
        'min': round(min(values), 2),
        'max': round(max(values), 2),
        'count': len(values)
    }
    if mean_val != 0:
        result['cv_percent'] = round((stdev_val / abs(mean_val)) * 100, 2)
    else:
        result['cv_percent'] = 0
    return result


def _print_table(headers, rows):
    """Print a nicely formatted ASCII table."""
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    fmt = " | ".join(f"{{:<{w}}}" for w in col_widths)
    separator = "-+-".join("-" * w for w in col_widths)

    lines = []
    lines.append(fmt.format(*[str(h) for h in headers]))
    lines.append(separator)
    for row in rows:
        lines.append(fmt.format(*[str(c) for c in row]))

    table_str = "\n".join(lines)
    print("\n" + table_str)
    return table_str


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    logger = i['automation'].logger

    geekbench_bin = env.get('MLC_GEEKBENCH_BIN_WITH_PATH', '')
    if geekbench_bin == '' or not os.path.isfile(geekbench_bin):
        return {'return': 1,
                'error': f'Geekbench binary {geekbench_bin} not found. Ensure get-geekbench dependency ran successfully.'}

    q = '"' if os_info['platform'] == 'windows' else "'"

    # License registration
    license_key = env.get('MLC_GEEKBENCH_LICENSE_KEY', '').strip()
    license_email = env.get('MLC_GEEKBENCH_LICENSE_EMAIL', '').strip()
    if license_key:
        if not license_email:
            return {'return': 1,
                    'error': 'MLC_GEEKBENCH_LICENSE_EMAIL is required when MLC_GEEKBENCH_LICENSE_KEY is provided'}
        env['MLC_GEEKBENCH_LICENSE_KEY'] = license_key
        env['MLC_GEEKBENCH_LICENSE_EMAIL'] = license_email
        logger.info(
            "Geekbench license key provided, will register before benchmark")

    # Results directory
    results_dir = env.get('MLC_GEEKBENCH_RESULTS_DIR', os.getcwd())
    os.makedirs(results_dir, exist_ok=True)
    env['MLC_GEEKBENCH_RESULTS_DIR'] = results_dir
    env['MLC_RUN_DIR'] = results_dir

    # --- Info-only modes (no benchmark execution) ---
    if is_true(env.get('MLC_GEEKBENCH_SYSINFO_ONLY', '')):
        env['MLC_RUN_CMD'] = f"{q}{geekbench_bin}{q} --sysinfo"
        env['MLC_GEEKBENCH_INFO_ONLY_MODE'] = 'yes'
        return {'return': 0}

    if is_true(env.get('MLC_GEEKBENCH_GPU_LIST', '')):
        env['MLC_RUN_CMD'] = f"{q}{geekbench_bin}{q} --gpu-list"
        env['MLC_GEEKBENCH_INFO_ONLY_MODE'] = 'yes'
        return {'return': 0}

    if is_true(env.get('MLC_GEEKBENCH_WORKLOAD_LIST', '')):
        env['MLC_RUN_CMD'] = f"{q}{geekbench_bin}{q} --workload-list"
        env['MLC_GEEKBENCH_INFO_ONLY_MODE'] = 'yes'
        return {'return': 0}

    # --- Load mode (display saved result, no benchmark) ---
    load_file = env.get('MLC_GEEKBENCH_LOAD_FILE', '').strip()
    if load_file:
        env['MLC_RUN_CMD'] = f"{q}{geekbench_bin}{q} --load {q}{load_file}{q}"
        env['MLC_GEEKBENCH_INFO_ONLY_MODE'] = 'yes'
        return {'return': 0}

    # --- Reuse logs mode (skip execution, just re-run postprocess) ---
    if is_true(env.get('MLC_GEEKBENCH_REUSE_LOGS', '')):
        env['MLC_RUN_CMD'] = ' '
        logger.info("Reuse logs mode: skipping benchmark execution, will parse existing results")
        return {'return': 0}

    # --- Build the base benchmark command ---
    args = []

    # Workload selection (--cpu, --gpu [API], --compute [API])
    workload = env.get('MLC_GEEKBENCH_WORKLOAD', '').strip()
    if workload:
        args.append(workload)

    # Determine single-core / multi-core / all-cores mode
    explicit_single_core = is_true(env.get('MLC_GEEKBENCH_SINGLE_CORE', ''))
    explicit_multi_core = is_true(env.get('MLC_GEEKBENCH_MULTI_CORE', ''))
    all_cores_mode = not explicit_single_core and not explicit_multi_core

    if explicit_single_core:
        args.append('--single-core')
    elif explicit_multi_core:
        args.append('--multi-core')

    # CPU workers (Pro: --cpu-workers N)
    cpu_workers = env.get('MLC_GEEKBENCH_CPU_WORKERS', '').strip()
    if cpu_workers:
        args.append(f'--cpu-workers {cpu_workers}')

    # Section filter (Pro: --section IDs)
    section = env.get('MLC_GEEKBENCH_SECTION', '').strip()
    if section:
        args.append(f'--section {section}')

    # Workload filter (Pro: --workload IDs, used with --section)
    workload_ids = env.get('MLC_GEEKBENCH_WORKLOAD_IDS', '').strip()
    if workload_ids:
        args.append(f'--workload {workload_ids}')

    # Iterations (native geekbench: --iterations N)
    # Only pass --iterations if explicitly set; otherwise use geekbench default
    iterations = env.get('MLC_GEEKBENCH_ITERATIONS', '').strip()
    if iterations:
        args.append(f'--iterations {iterations}')

    # Workload gap (Pro: --workload-gap N milliseconds)
    workload_gap = env.get('MLC_GEEKBENCH_WORKLOAD_GAP', '').strip()
    if workload_gap:
        args.append(f'--workload-gap {workload_gap}')

    # GPU device selection
    gpu_platform_id = env.get('MLC_GEEKBENCH_GPU_PLATFORM_ID', '').strip()
    if gpu_platform_id:
        args.append(f'--gpu-platform-id {gpu_platform_id}')

    gpu_device_id = env.get('MLC_GEEKBENCH_GPU_DEVICE_ID', '').strip()
    if gpu_device_id:
        args.append(f'--gpu-device-id {gpu_device_id}')

    # Upload control
    if is_true(env.get('MLC_GEEKBENCH_NO_UPLOAD', 'yes')):
        args.append('--no-upload')
    else:
        args.append('--upload')

    # Extra args passthrough (for any flags not explicitly mapped)
    extra_args = env.get('MLC_GEEKBENCH_EXTRA_ARGS', '').strip()
    if extra_args:
        args.append(extra_args)

    # Number of external repeated runs
    num_runs = int(env.get('MLC_GEEKBENCH_NUM_RUNS', '1'))
    env['MLC_GEEKBENCH_NUM_RUNS'] = str(num_runs)

    # Core pinning
    core_pinning = is_true(env.get('MLC_GEEKBENCH_CORE_PINNING', 'no'))
    pinned_core = env.get('MLC_GEEKBENCH_PINNED_CORE', '0').strip()
    env['MLC_GEEKBENCH_PINNED_CORE'] = pinned_core

    # Additional export formats (beyond JSON/CSV which are always generated)
    extra_exports = ""
    save_file = env.get('MLC_GEEKBENCH_SAVE_FILE', '').strip()
    if save_file:
        extra_exports += f" --save {q}{save_file}{q}"

    export_html = env.get('MLC_GEEKBENCH_EXPORT_HTML', '').strip()
    if export_html:
        extra_exports += f" --export-html {q}{export_html}{q}"

    export_xml = env.get('MLC_GEEKBENCH_EXPORT_XML', '').strip()
    if export_xml:
        extra_exports += f" --export-xml {q}{export_xml}{q}"

    export_text = env.get('MLC_GEEKBENCH_EXPORT_TEXT', '').strip()
    if export_text:
        extra_exports += f" --export-text {q}{export_text}{q}"

    platform = os_info['platform']

    # --- Split SC/MC mode: core_pinning + all-cores ---
    if core_pinning and all_cores_mode:
        env['MLC_GEEKBENCH_SPLIT_SC_MC'] = 'yes'

        # SC command: add --single-core and apply core pinning
        sc_args = args + ['--single-core']
        sc_cmd = f"{q}{geekbench_bin}{q} {' '.join(sc_args)}{extra_exports}"
        if platform == 'linux':
            sc_cmd = f"taskset -c {pinned_core} {sc_cmd}"

        # MC command: add --multi-core, no core pinning
        mc_args = args + ['--multi-core']
        mc_cmd = f"{q}{geekbench_bin}{q} {' '.join(mc_args)}{extra_exports}"

        env['MLC_GEEKBENCH_BASE_CMD_SC'] = sc_cmd
        env['MLC_GEEKBENCH_BASE_CMD_MC'] = mc_cmd

        if platform == 'windows':
            core_num = int(pinned_core)
            affinity_mask = f"{1 << core_num:x}"
            env['MLC_GEEKBENCH_AFFINITY_MASK'] = affinity_mask
            env['MLC_GEEKBENCH_CORE_PINNING'] = 'yes'

        logger.info(
            f"Split SC/MC mode enabled with core pinning on core {pinned_core}")
        logger.info(f"  SC command: {sc_cmd}")
        logger.info(f"  MC command: {mc_cmd}")
    else:
        env['MLC_GEEKBENCH_SPLIT_SC_MC'] = 'no'
        base_cmd = f"{q}{geekbench_bin}{q} {' '.join(args)}{extra_exports}"

        # Apply core pinning to the single command
        if core_pinning:
            if explicit_multi_core:
                logger.warning("Core pinning with --multi-core will pin all threads to one core. "
                               "Consider using split mode (all-cores + core_pinning) instead.")
            if platform == 'linux':
                base_cmd = f"taskset -c {pinned_core} {base_cmd}"
                logger.info(
                    f"Core pinning enabled (Linux): taskset -c {pinned_core}")
            elif platform == 'windows':
                core_num = int(pinned_core)
                affinity_mask = f"{1 << core_num:x}"
                env['MLC_GEEKBENCH_AFFINITY_MASK'] = affinity_mask
                env['MLC_GEEKBENCH_CORE_PINNING'] = 'yes'
                logger.info(
                    f"Core pinning enabled (Windows): affinity mask 0x{affinity_mask} (core {core_num})")

        env['MLC_GEEKBENCH_BASE_CMD'] = base_cmd
        logger.info(f"Geekbench command: {base_cmd}")

    iter_display = iterations if iterations else 'default (geekbench built-in)'
    logger.info(
        f"Native iterations per workload: {iter_display}, Number of runs: {num_runs}")
    logger.info(f"Results directory: {results_dir}")

    return {'return': 0}


def postprocess(i):

    env = i['env']
    logger = i['automation'].logger
    state = i['state']

    # Info-only modes — nothing to aggregate
    if is_true(env.get('MLC_GEEKBENCH_INFO_ONLY_MODE', '')):
        logger.info("Info-only mode — no results to process")
        return {'return': 0}

    results_dir = env.get('MLC_GEEKBENCH_RESULTS_DIR', '')
    num_runs = int(env.get('MLC_GEEKBENCH_NUM_RUNS', '1'))
    iterations_cfg = env.get('MLC_GEEKBENCH_ITERATIONS', 'default')
    split_mode = is_true(env.get('MLC_GEEKBENCH_SPLIT_SC_MC', 'no'))

    all_results = []
    run_durations = []

    for run in range(1, num_runs + 1):
        if split_mode:
            # In split mode, we have separate SC and MC result files per run
            sc_file = os.path.join(results_dir, f'geekbench_run{run}_sc.json')
            mc_file = os.path.join(results_dir, f'geekbench_run{run}_mc.json')

            sc_result = None
            mc_result = None

            if os.path.isfile(sc_file):
                try:
                    with open(sc_file, 'r') as f:
                        sc_result = json.load(f)
                    logger.info(f"Loaded SC results: run {run}")
                except Exception as e:
                    logger.warning(f"Could not parse {sc_file}: {e}")
            else:
                logger.warning(f"SC results file not found: {sc_file}")

            if os.path.isfile(mc_file):
                try:
                    with open(mc_file, 'r') as f:
                        mc_result = json.load(f)
                    logger.info(f"Loaded MC results: run {run}")
                except Exception as e:
                    logger.warning(f"Could not parse {mc_file}: {e}")
            else:
                logger.warning(f"MC results file not found: {mc_file}")

            # Merge SC + MC into one combined result
            if sc_result and mc_result:
                result = merge_sc_mc_results(sc_result, mc_result)
                result['_run'] = run
                result['_split_mode'] = True
                all_results.append(result)
                # Save merged JSON for reference
                merged_file = os.path.join(
                    results_dir, f'geekbench_run{run}.json')
                with open(merged_file, 'w') as f:
                    json.dump(result, f, indent=2)
                logger.info(f"Merged SC+MC results saved: {merged_file}")
            elif sc_result:
                sc_result['_run'] = run
                all_results.append(sc_result)
                logger.warning(f"Run {run}: only SC results available")
            elif mc_result:
                mc_result['_run'] = run
                all_results.append(mc_result)
                logger.warning(f"Run {run}: only MC results available")

            # Load timing data for both SC and MC
            for phase in ['sc', 'mc']:
                timing_file = os.path.join(
                    results_dir, f'geekbench_run{run}_{phase}_timing.json')
                if os.path.isfile(timing_file):
                    try:
                        with open(timing_file, 'r') as f:
                            timing = json.load(f)
                        duration = timing.get('duration_sec', None)
                        if duration is not None:
                            run_durations.append({
                                'run': run,
                                'phase': phase.upper(),
                                'duration_sec': float(duration)
                            })
                    except Exception as e:
                        logger.warning(f"Could not parse {timing_file}: {e}")

            # Also load total run timing
            timing_file = os.path.join(
                results_dir, f'geekbench_run{run}_timing.json')
            if os.path.isfile(timing_file):
                try:
                    with open(timing_file, 'r') as f:
                        timing = json.load(f)
                    duration = timing.get('duration_sec', None)
                    if duration is not None:
                        run_durations.append({
                            'run': run,
                            'phase': 'total',
                            'duration_sec': float(duration)
                        })
                except Exception as e:
                    logger.warning(f"Could not parse {timing_file}: {e}")
        else:
            json_file = os.path.join(results_dir, f'geekbench_run{run}.json')

            if os.path.isfile(json_file):
                try:
                    with open(json_file, 'r') as f:
                        result = json.load(f)
                    result['_run'] = run
                    all_results.append(result)
                    logger.info(f"Loaded results: run {run}")
                except Exception as e:
                    logger.warning(f"Could not parse {json_file}: {e}")
            else:
                logger.warning(f"Results file not found: {json_file}")

            # Load timing data
            timing_file = os.path.join(
                results_dir, f'geekbench_run{run}_timing.json')
            if os.path.isfile(timing_file):
                try:
                    with open(timing_file, 'r') as f:
                        timing = json.load(f)
                    duration = timing.get('duration_sec', None)
                    if duration is not None:
                        run_durations.append({
                            'run': run,
                            'phase': 'total',
                            'duration_sec': float(duration)
                        })
                except Exception as e:
                    logger.warning(f"Could not parse {timing_file}: {e}")

    if not all_results:
        logger.warning(
            "No Geekbench results found. The benchmark may not have completed successfully.")
        return {'return': 0}

    # --- Collect top-level scores across runs ---
    overall_score_lists = {}
    for r in all_results:
        for key, val in extract_scores(r).items():
            overall_score_lists.setdefault(key, []).append(val)

    overall_stats = {
        key: compute_stats(vals) for key, vals in overall_score_lists.items()
    }

    # --- Collect per-workload scores across runs ---
    workload_data = {}
    section_scores = {}
    for r in all_results:
        sections = extract_workload_scores(r)
        for sec_name, sec_info in sections.items():
            section_scores.setdefault(
                sec_name, []).append(
                sec_info['section_score'])
            if sec_name not in workload_data:
                workload_data[sec_name] = {}
            for wl_name, wl_info in sec_info['workloads'].items():
                if wl_name not in workload_data[sec_name]:
                    workload_data[sec_name][wl_name] = {
                        'score': [], 'runtime': [], 'runtimes': []}
                workload_data[sec_name][wl_name]['score'].append(
                    wl_info['score'])
                workload_data[sec_name][wl_name]['runtime'].append(
                    wl_info['runtime'])
                workload_data[sec_name][wl_name]['runtimes'].append(
                    wl_info['runtimes'])

    # Compute per-workload statistics
    workload_stats = {}
    for sec_name, wls in workload_data.items():
        workload_stats[sec_name] = {
            'section_score_stats': compute_stats(section_scores.get(sec_name, [])),
            'workloads': {}
        }
        for wl_name, wl_lists in wls.items():
            all_iter_runtimes = []
            for run_runtimes in wl_lists['runtimes']:
                all_iter_runtimes.extend(run_runtimes)
            workload_stats[sec_name]['workloads'][wl_name] = {
                'score': compute_stats(wl_lists['score']),
                'runtime': compute_stats(wl_lists['runtime']),
                'iteration_runtimes': compute_stats(all_iter_runtimes),
            }

    # --- Runtime statistics ---
    runtime_stats = {}
    total_durations = [d['duration_sec']
                       for d in run_durations if d['phase'] == 'total']
    if total_durations:
        runtime_stats['total'] = compute_stats(total_durations)
    if split_mode:
        sc_durations = [d['duration_sec']
                        for d in run_durations if d['phase'] == 'SC']
        mc_durations = [d['duration_sec']
                        for d in run_durations if d['phase'] == 'MC']
        if sc_durations:
            runtime_stats['single_core'] = compute_stats(sc_durations)
        if mc_durations:
            runtime_stats['multi_core'] = compute_stats(mc_durations)

    # --- Build summary ---
    individual_results = []
    for r in all_results:
        entry = {
            'run': r['_run'],
            'scores': extract_scores(r),
            'sections': extract_workload_scores(r),
        }
        individual_results.append(entry)

    summary = {
        'num_runs': num_runs,
        'iterations_per_workload': iterations_cfg,
        'total_runs_completed': len(all_results),
        'split_sc_mc': split_mode,
        'overall_statistics': overall_stats,
        'workload_statistics': workload_stats,
        'runtime_statistics': runtime_stats,
        'individual_results': individual_results,
        'individual_runtimes': run_durations,
    }

    # Log key results
    for key, stat in overall_stats.items():
        logger.info(
            f"Overall {key}: mean={stat['mean']}, "
            f"median={stat['median']}, olympic={stat['olympic']}, "
            f"cv={stat['cv_percent']}%")

    for phase, rstats in runtime_stats.items():
        logger.info(
            f"Runtime {phase} (sec): mean={rstats['mean']}, "
            f"cv={rstats['cv_percent']}%, "
            f"min={rstats['min']}, max={rstats['max']}")

    # Set env vars with overall mean scores for downstream consumers
    if 'score' in overall_stats:
        env['MLC_GEEKBENCH_SCORE'] = str(overall_stats['score']['mean'])
    if 'single_core_score' in overall_stats:
        env['MLC_GEEKBENCH_SINGLE_CORE_SCORE'] = str(
            overall_stats['single_core_score']['mean'])
    if 'multicore_score' in overall_stats:
        env['MLC_GEEKBENCH_MULTICORE_SCORE'] = str(
            overall_stats['multicore_score']['mean'])

    # Export summary as JSON
    summary_json = os.path.join(results_dir, 'geekbench_summary.json')
    with open(summary_json, 'w') as f:
        json.dump(summary, f, indent=2)
    env['MLC_GEEKBENCH_SUMMARY_JSON'] = summary_json
    logger.info(f"Summary JSON saved to: {summary_json}")

    # Export summary as CSV
    summary_csv = os.path.join(results_dir, 'geekbench_summary.csv')
    _write_summary_csv(summary, summary_csv)
    env['MLC_GEEKBENCH_SUMMARY_CSV'] = summary_csv
    logger.info(f"Summary CSV saved to: {summary_csv}")

    # --- Print results in tabular format ---
    _print_results_table(summary)

    state['geekbench_results'] = all_results
    state['geekbench_summary'] = summary

    return {'return': 0}


def _print_results_table(summary):
    """Print results in nicely formatted ASCII tables."""

    individual = summary.get('individual_results', [])
    run_durations = summary.get('individual_runtimes', [])
    num_runs = summary.get('num_runs', 1)
    iterations_cfg = summary.get('iterations_per_workload', '3')
    split_mode = summary.get('split_sc_mc', False)

    # Build per-run duration maps
    total_dur = {}
    sc_dur = {}
    mc_dur = {}
    for d in run_durations:
        run = d['run']
        if d['phase'] == 'total':
            total_dur[run] = d['duration_sec']
        elif d['phase'] == 'SC':
            sc_dur[run] = d['duration_sec']
        elif d['phase'] == 'MC':
            mc_dur[run] = d['duration_sec']

    # Print CV description
    print("")
    print("  Note: CV% (Coefficient of Variation) = (StdDev / Mean) * 100.")
    print("  Lower CV% indicates more consistent/reproducible results.")
    print("  CV% < 1% is excellent, 1-5% is good, > 5% may need investigation.")

    # ============================================================
    # 1. Individual Run Top-Level Scores
    # ============================================================
    if individual:
        score_keys = sorted(individual[0]['scores'].keys())
        headers = ['Run'] + [k.replace('_', ' ').title() for k in score_keys]
        if split_mode:
            headers.extend(['SC Duration (s)', 'MC Duration (s)', 'Total (s)'])
        elif total_dur:
            headers.append('Duration (s)')
        rows = []
        for entry in individual:
            run_num = entry['run']
            row = [run_num]
            row.extend(entry['scores'].get(k, '-') for k in score_keys)
            if split_mode:
                row.append(sc_dur.get(run_num, '-'))
                row.append(mc_dur.get(run_num, '-'))
                row.append(total_dur.get(run_num, '-'))
            elif total_dur:
                row.append(total_dur.get(run_num, '-'))
            rows.append(row)

        print("")
        print("=" * 78)
        if split_mode:
            print("  INDIVIDUAL RUN SCORES (SC pinned, MC unpinned)")
        else:
            print("  INDIVIDUAL RUN SCORES (top-level)")
        print("=" * 78)
        _print_table(headers, rows)

    # ============================================================
    # 2. Per-Section / Per-Workload Results for each run
    # ============================================================
    if individual and individual[0].get('sections'):
        for entry in individual:
            run_num = entry['run']
            sections = entry.get('sections', {})
            for sec_name, sec_info in sections.items():
                print("")
                print("-" * 78)
                if split_mode:
                    if 'single' in sec_name.lower():
                        pinned_note = " [PINNED]"
                    else:
                        pinned_note = " [UNPINNED]"
                label = (f"  Run {run_num} | {sec_name}{pinned_note}"
                         f" (section score: {sec_info['section_score']},"
                         f" iterations: {iterations_cfg})")
                print(label)
                print("-" * 78)

                max_iters = 0
                for wl_info in sec_info['workloads'].values():
                    max_iters = max(
                        max_iters, wl_info.get(
                            'iterations_scored', 0))

                headers = ['Workload', 'Score', 'Warmup (s)', 'Mean RT (s)']
                for it in range(1, max_iters + 1):
                    headers.append(f'Iter {it} (s)')
                if max_iters >= 2:
                    headers.append('Iter CV%')

                rows = []
                for wl_name, wl_info in sec_info['workloads'].items():
                    iters = wl_info.get('runtimes', [])
                    row = [
                        wl_name,
                        wl_info['score'],
                        round(wl_info.get('runtime_warmup', 0), 4),
                        round(wl_info['runtime'], 4),
                    ]
                    for it in range(max_iters):
                        if it < len(iters):
                            row.append(round(iters[it], 6))
                        else:
                            row.append('-')
                    if max_iters >= 2:
                        if len(iters) >= 2:
                            mean_rt = statistics.mean(iters)
                            std_rt = statistics.stdev(iters)
                            cv_pct = round(
                                (std_rt / abs(mean_rt)) * 100,
                                2) if mean_rt != 0 else 0
                            row.append(cv_pct)
                        else:
                            row.append('-')
                    rows.append(row)
                _print_table(headers, rows)

    # ============================================================
    # 3. Overall Top-Level Statistics (across runs)
    # ============================================================
    overall = summary.get('overall_statistics', {})
    runtime_stats = summary.get('runtime_statistics', {})

    if overall:
        headers = [
            'Metric',
            'Mean',
            'Median',
            'Olympic',
            'CV%',
            'Min',
            'Max',
            'Count']
        rows = []
        for metric, stats in overall.items():
            rows.append([
                metric.replace('_', ' ').title(),
                stats.get('mean', '-'),
                stats.get('median', '-'),
                stats.get('olympic', '-'),
                stats.get('cv_percent', '-'),
                stats.get('min', '-'),
                stats.get('max', '-'),
                stats.get('count', '-'),
            ])
        for phase, rstats in runtime_stats.items():
            rows.append([
                f'Runtime {phase} (sec)',
                rstats.get('mean', '-'),
                rstats.get('median', '-'),
                rstats.get('olympic', '-'),
                rstats.get('cv_percent', '-'),
                rstats.get('min', '-'),
                rstats.get('max', '-'),
                rstats.get('count', '-'),
            ])

        print("")
        print("=" * 78)
        print("  OVERALL TOP-LEVEL STATISTICS (across all runs)")
        print("=" * 78)
        _print_table(headers, rows)

    # ============================================================
    # 4. Per-Workload Statistics (aggregated across runs)
    # ============================================================
    workload_stats = summary.get('workload_statistics', {})

    if workload_stats and num_runs > 1:
        for sec_name, sec_info in workload_stats.items():
            sec_stats = sec_info.get('section_score_stats', {})
            pinned_note = ""
            if split_mode:
                if 'single' in sec_name.lower():
                    pinned_note = " [PINNED]"
                else:
                    pinned_note = " [UNPINNED]"
            print("")
            print("=" * 78)
            print(f"  WORKLOAD STATISTICS (across runs) | {sec_name}{pinned_note}"
                  f" (section score: mean={sec_stats.get('mean', '-')},"
                  f" cv={sec_stats.get('cv_percent', '-')}%)")
            print("=" * 78)
            headers = ['Workload',
                       'Score Mean', 'Score CV%',
                       'RT Mean', 'RT CV%',
                       'Iter RT Mean', 'Iter RT CV%']
            rows = []
            for wl_name, wl_stats in sec_info['workloads'].items():
                s = wl_stats.get('score', {})
                r = wl_stats.get('runtime', {})
                ir = wl_stats.get('iteration_runtimes', {})
                rows.append([
                    wl_name,
                    s.get('mean', '-'), s.get('cv_percent', '-'),
                    r.get('mean', '-'), r.get('cv_percent', '-'),
                    ir.get('mean', '-'), ir.get('cv_percent', '-'),
                ])
            _print_table(headers, rows)

    # For single run, show per-workload with iteration details
    if workload_stats and num_runs == 1:
        for sec_name, sec_info in workload_stats.items():
            sec_stats = sec_info.get('section_score_stats', {})
            pinned_note = ""
            if split_mode:
                if 'single' in sec_name.lower():
                    pinned_note = " [PINNED]"
                else:
                    pinned_note = " [UNPINNED]"
            print("")
            print("=" * 78)
            print(f"  ITERATION VARIANCE | {sec_name}{pinned_note}"
                  f" (section score: {sec_stats.get('mean', '-')})")
            print("  (Variance is between iterations within a single run."
                  " Geekbench reports per-iteration runtimes only, not scores.)")
            print("=" * 78)
            headers = ['Workload', 'Score', 'Mean RT (s)',
                       'Iter RT CV%', 'Iters Scored']
            rows = []
            for wl_name, wl_stats in sec_info['workloads'].items():
                s = wl_stats.get('score', {})
                r = wl_stats.get('runtime', {})
                ir = wl_stats.get('iteration_runtimes', {})
                rows.append([
                    wl_name,
                    s.get('mean', '-'),
                    r.get('mean', '-'),
                    ir.get('cv_percent', '-'),
                    ir.get('count', '-'),
                ])
            _print_table(headers, rows)

    print("")


def _write_summary_csv(summary, csv_path):
    """Write summary statistics to a CSV file."""
    split_mode = summary.get('split_sc_mc', False)

    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)

        # --- Individual top-level results ---
        writer.writerow(['Individual Results (Top-Level Scores)'])
        if summary['individual_results']:
            score_keys = sorted(
                summary['individual_results'][0]['scores'].keys())
            run_durations = summary.get('individual_runtimes', [])
            total_dur = {d['run']: d['duration_sec']
                         for d in run_durations if d['phase'] == 'total'}
            sc_dur = {d['run']: d['duration_sec']
                      for d in run_durations if d['phase'] == 'SC'}
            mc_dur = {d['run']: d['duration_sec']
                      for d in run_durations if d['phase'] == 'MC'}
            header = ['run'] + score_keys
            if split_mode:
                header.extend(
                    ['sc_duration_sec', 'mc_duration_sec', 'total_duration_sec'])
            elif total_dur:
                header.append('duration_sec')
            writer.writerow(header)
            for entry in summary['individual_results']:
                run_num = entry['run']
                row = [run_num]
                row.extend(entry['scores'].get(k, '') for k in score_keys)
                if split_mode:
                    row.extend([sc_dur.get(run_num, ''), mc_dur.get(
                        run_num, ''), total_dur.get(run_num, '')])
                elif total_dur:
                    row.append(total_dur.get(run_num, ''))
                writer.writerow(row)

        writer.writerow([])

        # --- Individual per-workload results ---
        for entry in summary.get('individual_results', []):
            sections = entry.get('sections', {})
            for sec_name, sec_info in sections.items():
                pinned_note = ""
                if split_mode:
                    pinned_note = " [PINNED]" if 'single' in sec_name.lower(
                    ) else " [UNPINNED]"
                writer.writerow(
                    [f'Run {entry["run"]} | {sec_name}{pinned_note} (section score: {sec_info["section_score"]})'])
                max_iters = max(
                    (wl['iterations_scored']
                     for wl in sec_info['workloads'].values()),
                    default=0)
                header = [
                    'workload',
                    'score',
                    'warmup_runtime',
                    'mean_runtime']
                for it in range(1, max_iters + 1):
                    header.append(f'iter_{it}_runtime')
                if max_iters >= 2:
                    header.append('iter_cv_percent')
                writer.writerow(header)
                for wl_name, wl_info in sec_info['workloads'].items():
                    iters = wl_info.get('runtimes', [])
                    row = [wl_name, wl_info['score'],
                           round(wl_info.get('runtime_warmup', 0), 6),
                           round(wl_info['runtime'], 6)]
                    for it in range(max_iters):
                        row.append(
                            round(
                                iters[it],
                                6) if it < len(iters) else '')
                    if max_iters >= 2:
                        if len(iters) >= 2:
                            mean_rt = statistics.mean(iters)
                            std_rt = statistics.stdev(iters)
                            cv_pct = round(
                                (std_rt / abs(mean_rt)) * 100,
                                2) if mean_rt != 0 else 0
                            row.append(cv_pct)
                        else:
                            row.append('')
                    writer.writerow(row)
                writer.writerow([])

        # --- Overall statistics ---
        writer.writerow(['Overall Statistics'])
        writer.writerow(['metric', 'mean', 'median', 'olympic',
                        'cv_percent', 'min', 'max', 'count'])
        for metric, stats in summary.get('overall_statistics', {}).items():
            writer.writerow([metric, stats.get('mean', ''), stats.get('median', ''),
                             stats.get('olympic', ''),
                             stats.get('cv_percent', ''), stats.get('min', ''),
                             stats.get('max', ''), stats.get('count', '')])
        for phase, rstats in summary.get('runtime_statistics', {}).items():
            writer.writerow([f'runtime_{phase}_sec', rstats.get('mean', ''),
                             rstats.get(
                'median', ''), rstats.get(
                'olympic', ''),
                rstats.get('cv_percent', ''),
                rstats.get('min', ''), rstats.get('max', ''),
                rstats.get('count', '')])
        writer.writerow([])

        # --- Per-workload statistics ---
        workload_stats = summary.get('workload_statistics', {})
        if workload_stats:
            for sec_name, sec_info in workload_stats.items():
                sec_ss = sec_info.get('section_score_stats', {})
                writer.writerow(
                    [f'Workload Statistics | {sec_name} (section score mean: {sec_ss.get("mean", "")})'])
                writer.writerow(['workload',
                                 'score_mean', 'score_median', 'score_olympic',
                                 'score_cv_percent',
                                 'runtime_mean', 'runtime_median', 'runtime_olympic',
                                 'runtime_cv_percent',
                                 'iter_rt_mean', 'iter_rt_cv_percent'])
                for wl_name, wl_stats in sec_info['workloads'].items():
                    s = wl_stats.get('score', {})
                    r = wl_stats.get('runtime', {})
                    ir = wl_stats.get('iteration_runtimes', {})
                    writer.writerow([
                        wl_name,
                        s.get(
                            'mean', ''), s.get(
                            'median', ''), s.get(
                            'olympic', ''),
                        s.get('cv_percent', ''),
                        r.get(
                            'mean', ''), r.get(
                            'median', ''), r.get(
                            'olympic', ''),
                        r.get('cv_percent', ''),
                        ir.get('mean', ''), ir.get('cv_percent', ''),
                    ])
                writer.writerow([])
