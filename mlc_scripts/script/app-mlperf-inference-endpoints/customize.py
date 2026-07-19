from mlc import utils
from utils import is_true
import json
import os
import platform
import shlex
import yaml


def _build_from_config_cmd(env, logger, venv_python, config_file):
    """Assemble a `benchmark from-config` command and align the report dir.

    `from-config` has no --report-dir flag, so the report directory comes from
    the YAML. To let postprocess find results.json reliably, adopt the config's
    report_dir if present, otherwise inject the script's report_dir into the
    config file.
    """
    config_file = os.path.abspath(config_file)
    with open(config_file) as f:
        conf = yaml.safe_load(f) or {}

    report_dir = (conf.get('report_dir') or '').strip()
    if not report_dir:
        report_dir = env.get('MLC_MLPERF_ENDPOINT_REPORT_DIR', '').strip() or \
            os.path.join(os.getcwd(), 'endpoint_results')
        report_dir = os.path.abspath(report_dir)
        conf['report_dir'] = report_dir
        with open(config_file, 'w') as f:
            yaml.safe_dump(conf, f, sort_keys=False)
    else:
        report_dir = os.path.abspath(report_dir)
    os.makedirs(report_dir, exist_ok=True)
    env['MLC_MLPERF_ENDPOINT_REPORT_DIR'] = report_dir

    opts = ['--config', config_file]
    test_mode = env.get('MLC_MLPERF_ENDPOINT_TEST_MODE', '').strip()
    if test_mode:
        opts += ['--mode', test_mode]
    timeout = env.get('MLC_MLPERF_ENDPOINT_TIMEOUT', '').strip()
    if timeout:
        opts += ['--timeout', timeout]

    cmd = ' '.join([
        shlex.quote(venv_python),
        '-m', 'inference_endpoint.main', 'benchmark', 'from-config',
        ' '.join(shlex.quote(o) for o in opts),
    ])
    env['MLC_MLPERF_ENDPOINT_CMD'] = cmd

    logger.info('')
    logger.info(f'Endpoint benchmark (from-config: {config_file}):\n  {cmd}')
    logger.info('')
    return {'return': 0}


def preprocess(i):

    env = i['env']
    logger = i['automation'].logger

    venv_python = env.get('MLC_MLPERF_ENDPOINTS_PYTHON_BIN', '').strip()
    if venv_python == '':
        return {
            'return': 1,
            'error': 'inference-endpoint is not installed '
            '(MLC_MLPERF_ENDPOINTS_PYTHON_BIN is unset). The get,mlperf,endpoints '
            'dependency is expected to provide it.'}

    # --- from-config path: run a YAML config via `benchmark from-config` ---
    use_config = is_true(env.get('MLC_MLPERF_ENDPOINT_USE_CONFIG', ''))
    config_file = (env.get('MLC_MLPERF_ENDPOINT_CONFIG_FILE', '').strip()
                   or env.get('MLC_MLPERF_ENDPOINTS_CONF_PATH', '').strip())
    if use_config or config_file:
        if not config_file:
            return {
                'return': 1,
                'error': 'from-config mode needs a config file: pass '
                '--config=<file>, or use the _from-config variation to '
                'generate one.'}
        if not os.path.isfile(config_file):
            return {'return': 1,
                    'error': f'config file not found: {config_file}'}
        return _build_from_config_cmd(env, logger, venv_python, config_file)

    mode = env.get('MLC_MLPERF_ENDPOINT_MODE', 'offline').strip().lower()
    if mode not in ('offline', 'online'):
        return {
            'return': 1,
            'error': f"Unsupported benchmark mode '{mode}' "
            "(expected 'offline' or 'online')."}

    # Report directory (created if missing).
    report_dir = env.get('MLC_MLPERF_ENDPOINT_REPORT_DIR', '').strip()
    if report_dir == '':
        report_dir = os.path.join(os.getcwd(), 'endpoint_results')
    report_dir = os.path.abspath(report_dir)
    os.makedirs(report_dir, exist_ok=True)
    env['MLC_MLPERF_ENDPOINT_REPORT_DIR'] = report_dir

    use_echo = is_true(env.get('MLC_MLPERF_ENDPOINT_USE_ECHO_SERVER', ''))
    if use_echo:
        port = env.get('MLC_MLPERF_ENDPOINT_ECHO_SERVER_PORT', '8765').strip()
        env['MLC_MLPERF_ENDPOINT_ECHO_SERVER_PORT'] = port
        env['MLC_MLPERF_ENDPOINT_URL'] = f'http://localhost:{port}'
        if env.get('MLC_MLPERF_ENDPOINT_MODEL', '').strip() == '':
            env['MLC_MLPERF_ENDPOINT_MODEL'] = 'test-model'
        # Default to the dummy dataset bundled with the endpoints source so a
        # bare `--echo-server` run is fully self-contained.
        if env.get('MLC_MLPERF_ENDPOINT_DATASET_PATH', '').strip() == '':
            src = env.get('MLC_MLPERF_INFERENCE_ENDPOINTS_SOURCE', '').strip()
            dummy = os.path.join(
                src, 'tests', 'assets', 'datasets', 'dummy_1k.jsonl')
            if not os.path.isfile(dummy):
                return {
                    'return': 1,
                    'error': 'echo-server run requested without a --dataset and '
                    f'the bundled dummy dataset was not found at {dummy}.'}
            env['MLC_MLPERF_ENDPOINT_DATASET_PATH'] = dummy
            if env.get('MLC_MLPERF_ENDPOINT_PROMPT_COLUMN', '').strip() == '':
                env['MLC_MLPERF_ENDPOINT_PROMPT_COLUMN'] = 'text_input'

    model = env.get('MLC_MLPERF_ENDPOINT_MODEL', '').strip()
    if model == '':
        return {
            'return': 1,
            'error': 'Model name is required (pass --model, or use --echo-server).'}

    url = env.get('MLC_MLPERF_ENDPOINT_URL', '').strip()
    if url == '':
        return {
            'return': 1,
            'error': 'Endpoint URL is required (pass --endpoints/--api_endpoint, '
            'or use --echo-server).'}

    dataset = env.get('MLC_MLPERF_ENDPOINT_DATASET_PATH', '').strip()
    if dataset == '':
        return {
            'return': 1,
            'error': 'Dataset path is required (pass --dataset).'}

    # Assemble the TOML-style dataset argument: PATH[,samples=N][,parser.prompt=col]
    dataset_suffixes = []
    nsamples = env.get('MLC_MLPERF_ENDPOINT_NUM_SAMPLES', '').strip()
    if nsamples:
        dataset_suffixes.append(f'samples={nsamples}')
    prompt_col = env.get('MLC_MLPERF_ENDPOINT_PROMPT_COLUMN', '').strip()
    if prompt_col:
        dataset_suffixes.append(f'parser.prompt={prompt_col}')
    dataset_arg = dataset
    if dataset_suffixes:
        dataset_arg = dataset + ',' + ','.join(dataset_suffixes)

    opts = ['--endpoints', url, '--model', model, '--dataset', dataset_arg,
            '--report-dir', report_dir]

    api_type = env.get('MLC_MLPERF_ENDPOINT_API_TYPE', '').strip()
    if api_type:
        opts += ['--api-type', api_type]

    api_key = env.get('MLC_MLPERF_ENDPOINT_API_KEY', '').strip()
    if api_key:
        opts += ['--api-key', api_key]

    tokenizer = env.get('MLC_MLPERF_ENDPOINT_TOKENIZER', '').strip()
    if tokenizer:
        opts += ['--tokenizer', tokenizer]

    max_output_tokens = env.get(
        'MLC_MLPERF_ENDPOINT_MAX_OUTPUT_TOKENS', '').strip()
    if max_output_tokens:
        opts += ['--max-output-tokens', max_output_tokens]

    streaming = env.get('MLC_MLPERF_ENDPOINT_STREAMING', '').strip()
    if streaming:
        opts += ['--streaming', streaming]

    duration = env.get('MLC_MLPERF_ENDPOINT_DURATION', '').strip()
    if duration:
        opts += ['--duration', duration]

    timeout = env.get('MLC_MLPERF_ENDPOINT_TIMEOUT', '').strip()
    if timeout:
        opts += ['--timeout', timeout]

    num_workers = env.get('MLC_MLPERF_ENDPOINT_NUM_WORKERS', '').strip()
    if num_workers:
        opts += ['--workers', num_workers]

    target_qps = env.get('MLC_MLPERF_ENDPOINT_TARGET_QPS', '').strip()
    concurrency = env.get('MLC_MLPERF_ENDPOINT_CONCURRENCY', '').strip()
    load_pattern = env.get(
        'MLC_MLPERF_ENDPOINT_LOAD_PATTERN', '').strip().lower()
    if mode == 'online':
        # Online requires an explicit load pattern. Infer a sensible default
        # when the user did not select one via a variation: concurrency if only
        # --concurrency was given, otherwise poisson.
        if not load_pattern:
            load_pattern = 'concurrency' if (
                concurrency and not target_qps) else 'poisson'
        if load_pattern == 'poisson' and not target_qps:
            return {
                'return': 1,
                'error': 'online poisson load pattern requires --target_qps.'}
        if load_pattern == 'concurrency' and not concurrency:
            return {
                'return': 1,
                'error': 'online concurrency load pattern requires --concurrency.'}
        opts += ['--load-pattern', load_pattern]
    if target_qps:
        opts += ['--target-qps', target_qps]
    if concurrency:
        opts += ['--concurrency', concurrency]

    # CPU affinity: inference-endpoint's pin_loadgen() requires Linux. Disable
    # it unless the user explicitly enabled it AND we are on Linux.
    affinity = env.get('MLC_MLPERF_ENDPOINT_CPU_AFFINITY', '').strip().lower()
    is_linux = platform.system().lower() == 'linux'
    if affinity != 'yes' or not is_linux:
        opts.append('--no-cpu-affinity')
        if affinity == 'yes' and not is_linux:
            logger.warning(
                'CPU affinity requested but the platform is not Linux; '
                'falling back to --no-cpu-affinity.')

    test_mode = env.get('MLC_MLPERF_ENDPOINT_TEST_MODE', '').strip()
    if test_mode:
        opts += ['--mode', test_mode]

    cmd = ' '.join([
        shlex.quote(venv_python),
        '-m', 'inference_endpoint.main', 'benchmark', mode,
        ' '.join(shlex.quote(o) for o in opts),
    ])
    env['MLC_MLPERF_ENDPOINT_CMD'] = cmd

    logger.info('')
    logger.info(f'Endpoint benchmark command:\n  {cmd}')
    logger.info('')

    return {'return': 0}


def postprocess(i):

    env = i['env']
    logger = i['automation'].logger

    report_dir = env.get('MLC_MLPERF_ENDPOINT_REPORT_DIR', '')
    results_file = os.path.join(report_dir, 'results.json')

    if not os.path.isfile(results_file):
        return {
            'return': 1,
            'error': f'Benchmark did not produce a results.json at {results_file}.'}

    with open(results_file) as f:
        data = json.load(f)
    results = data.get('results', {})

    env['MLC_MLPERF_ENDPOINT_RESULTS_FILE'] = results_file
    env['MLC_MLPERF_ENDPOINT_QPS'] = str(results.get('qps', ''))
    env['MLC_MLPERF_ENDPOINT_SAMPLES_TOTAL'] = str(results.get('total', ''))
    env['MLC_MLPERF_ENDPOINT_SAMPLES_SUCCESSFUL'] = str(
        results.get('successful', ''))
    env['MLC_MLPERF_ENDPOINT_SAMPLES_FAILED'] = str(results.get('failed', ''))
    env['MLC_MLPERF_ENDPOINT_ELAPSED_TIME'] = str(
        results.get('elapsed_time', ''))

    # Latency percentiles (if a perf run produced them).
    summary_file = os.path.join(report_dir, 'result_summary.json')
    if os.path.isfile(summary_file):
        with open(summary_file) as f:
            summary = json.load(f)
        latency = summary.get('latency', {}) or {}
        percentiles = latency.get('percentiles', {}) or {}
        if 'avg' in latency:
            env['MLC_MLPERF_ENDPOINT_LATENCY_MEAN_NS'] = str(latency['avg'])
        if '50.0' in percentiles:
            env['MLC_MLPERF_ENDPOINT_LATENCY_P50_NS'] = str(percentiles['50.0'])
        if '99.0' in percentiles:
            env['MLC_MLPERF_ENDPOINT_LATENCY_P99_NS'] = str(percentiles['99.0'])

    failed = results.get('failed', 0) or 0

    logger.info('')
    logger.info('----------------- Endpoint Benchmark Summary -----------------')
    logger.info(f"  Mode:       {env.get('MLC_MLPERF_ENDPOINT_MODE', '')}")
    logger.info(f"  QPS:        {results.get('qps', '')}")
    logger.info(f"  Total:      {results.get('total', '')}")
    logger.info(f"  Successful: {results.get('successful', '')}")
    logger.info(f"  Failed:     {failed}")
    logger.info(f"  Elapsed:    {results.get('elapsed_time', '')} s")
    logger.info(f"  Results:    {results_file}")
    logger.info('--------------------------------------------------------------')
    logger.info('')

    return {'return': 0}
