from mlc import utils
import os
import platform
import yaml

# Predefined datasets that can be referenced by name (no path required).
PREDEFINED_DATASETS = {
    "open_orca", "cnn_dailymail", "gpqa", "aime25", "livecodebench",
    "random", "shopify_product_catalogue", "shopify_product_catalogue_8k",
}


def _f(env, key):
    """Return a stripped env value, or '' if unset."""
    return env.get(key, "").strip()


# When this script runs as a dependency of app-mlperf-inference-endpoints
# (the _from-config variation), inputs arrive under the app's MLC_MLPERF_ENDPOINT_*
# env keys. Fall back to those when the generator's own keys are unset, so the
# same CLI works both standalone and chained.
_APP_KEY_FALLBACKS = {
    "MLC_MLPERF_ENDPOINTS_CONF_TYPE": "MLC_MLPERF_ENDPOINT_MODE",
    "MLC_MLPERF_ENDPOINTS_CONF_MODEL": "MLC_MLPERF_ENDPOINT_MODEL",
    "MLC_MLPERF_ENDPOINTS_CONF_URL": "MLC_MLPERF_ENDPOINT_URL",
    "MLC_MLPERF_ENDPOINTS_CONF_API_KEY": "MLC_MLPERF_ENDPOINT_API_KEY",
    "MLC_MLPERF_ENDPOINTS_CONF_API_TYPE": "MLC_MLPERF_ENDPOINT_API_TYPE",
    "MLC_MLPERF_ENDPOINTS_CONF_DATASET_PATH": "MLC_MLPERF_ENDPOINT_DATASET_PATH",
    "MLC_MLPERF_ENDPOINTS_CONF_PROMPT_COLUMN": "MLC_MLPERF_ENDPOINT_PROMPT_COLUMN",
    "MLC_MLPERF_ENDPOINTS_CONF_NUM_SAMPLES": "MLC_MLPERF_ENDPOINT_NUM_SAMPLES",
    "MLC_MLPERF_ENDPOINTS_CONF_LOAD_PATTERN": "MLC_MLPERF_ENDPOINT_LOAD_PATTERN",
    "MLC_MLPERF_ENDPOINTS_CONF_TARGET_QPS": "MLC_MLPERF_ENDPOINT_TARGET_QPS",
    "MLC_MLPERF_ENDPOINTS_CONF_CONCURRENCY": "MLC_MLPERF_ENDPOINT_CONCURRENCY",
    "MLC_MLPERF_ENDPOINTS_CONF_MAX_OUTPUT_TOKENS":
        "MLC_MLPERF_ENDPOINT_MAX_OUTPUT_TOKENS",
    "MLC_MLPERF_ENDPOINTS_CONF_STREAMING": "MLC_MLPERF_ENDPOINT_STREAMING",
    "MLC_MLPERF_ENDPOINTS_CONF_NUM_WORKERS": "MLC_MLPERF_ENDPOINT_NUM_WORKERS",
    "MLC_MLPERF_ENDPOINTS_CONF_REPORT_DIR": "MLC_MLPERF_ENDPOINT_REPORT_DIR",
}


def _apply_app_fallbacks(env):
    for conf_key, app_key in _APP_KEY_FALLBACKS.items():
        if not env.get(conf_key, "").strip() and env.get(app_key, "").strip():
            env[conf_key] = env[app_key]
    # conf_type derives from the app mode (offline/online); eval/submission have
    # no app-mode equivalent and must be set explicitly.
    ct = env.get("MLC_MLPERF_ENDPOINTS_CONF_TYPE", "").strip().lower()
    if ct not in ("offline", "online", "eval", "submission"):
        env["MLC_MLPERF_ENDPOINTS_CONF_TYPE"] = "offline"


def _dataset_entry(name, preset, path, ds_type, prompt_column, samples,
                   eval_method="", ground_truth="", extractor=""):
    """Build one `datasets:` list entry.

    A predefined `name` needs no path; otherwise `path` is required.
    """
    entry = {}
    if name:
        entry["name"] = f"{name}::{preset}" if preset else name
    else:
        entry["name"] = "perf" if ds_type == "performance" else "accuracy"
    entry["type"] = ds_type
    if path:
        entry["path"] = path
    if samples:
        entry["samples"] = int(samples)
    if prompt_column:
        entry["parser"] = {"prompt": prompt_column}
    if ds_type == "accuracy":
        if ground_truth or extractor:
            acc = {}
            if eval_method:
                acc["eval_method"] = eval_method
            if ground_truth:
                acc["ground_truth"] = ground_truth
            if extractor:
                acc["extractor"] = extractor
            entry["accuracy_config"] = acc
        elif eval_method:
            entry["eval_method"] = eval_method
    return entry


def _validate_dataset(name, path, role):
    """A dataset is usable only if it is predefined-by-name or has a path."""
    if not name and not path:
        return f"{role} dataset requires a predefined --{'dataset_name' if role == 'performance' else 'accuracy_dataset_name'} or a custom path."
    if name and name not in PREDEFINED_DATASETS and not path:
        return (f"{role} dataset '{name}' is not a predefined dataset and no "
                f"path was given. Predefined: {sorted(PREDEFINED_DATASETS)}")
    return None


def preprocess(i):

    env = i['env']
    logger = i['automation'].logger

    _apply_app_fallbacks(env)

    conf_type = (_f(env, 'MLC_MLPERF_ENDPOINTS_CONF_TYPE') or 'offline').lower()
    if conf_type not in ('offline', 'online', 'eval', 'submission'):
        return {'return': 1,
                'error': f"Unsupported conf type '{conf_type}' "
                "(expected offline, online, eval, or submission)."}

    cfg = {}
    cfg['name'] = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_NAME') or \
        f'{conf_type}_endpoints_benchmark'
    cfg['version'] = '1.0'
    cfg['type'] = conf_type

    if conf_type == 'submission':
        cfg['benchmark_mode'] = _f(
            env, 'MLC_MLPERF_ENDPOINTS_CONF_BENCHMARK_MODE') or 'offline'
        submission_model = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_SUBMISSION_MODEL')
        ruleset = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_RULESET') or \
            'mlperf-inference-v5.1'
        if not submission_model:
            return {'return': 1,
                    'error': 'submission config requires --submission_model '
                    '(ruleset model id, e.g. llama2-70b).'}
        cfg['submission_ref'] = {'model': submission_model, 'ruleset': ruleset}

    # --- model_params ---
    model_params = {}
    model = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_MODEL')
    if model:
        model_params['name'] = model
    elif conf_type != 'submission':
        # submission can derive model_params.name from submission_ref.model
        return {'return': 1, 'error': 'Model name is required (--model).'}
    temperature = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_TEMPERATURE')
    if temperature:
        model_params['temperature'] = float(temperature)
    top_p = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_TOP_P')
    if top_p:
        model_params['top_p'] = float(top_p)
    top_k = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_TOP_K')
    if top_k:
        model_params['top_k'] = int(top_k)
    max_output_tokens = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_MAX_OUTPUT_TOKENS')
    if max_output_tokens:
        model_params['max_new_tokens'] = int(max_output_tokens)
    streaming = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_STREAMING')
    if streaming:
        model_params['streaming'] = streaming
    if model_params:
        cfg['model_params'] = model_params

    # --- datasets ---
    datasets = []
    perf_name = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_DATASET_NAME')
    perf_path = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_DATASET_PATH')
    prompt_column = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_PROMPT_COLUMN')
    perf_samples = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_NUM_SAMPLES')

    # eval is accuracy-only; every other type needs a performance dataset.
    if conf_type != 'eval':
        err = _validate_dataset(perf_name, perf_path, 'performance')
        if err:
            return {'return': 1, 'error': err}
        datasets.append(_dataset_entry(
            perf_name, _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_DATASET_PRESET'),
            perf_path, 'performance', prompt_column, perf_samples))

    acc_name = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_ACC_DATASET_NAME')
    acc_path = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_ACC_DATASET_PATH')
    eval_method = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_EVAL_METHOD')
    ground_truth = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_GROUND_TRUTH')
    extractor = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_EXTRACTOR')
    acc_samples = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_ACC_NUM_SAMPLES')

    needs_accuracy = conf_type in ('eval', 'submission') or acc_name or acc_path
    if needs_accuracy:
        err = _validate_dataset(acc_name, acc_path, 'accuracy')
        if err:
            return {'return': 1, 'error': err}
        datasets.append(_dataset_entry(
            acc_name, '', acc_path, 'accuracy',
            prompt_column if not perf_path else '', acc_samples,
            eval_method, ground_truth, extractor))

    cfg['datasets'] = datasets

    # --- settings ---
    runtime = {}
    min_dur = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_MIN_DURATION_MS')
    if min_dur:
        runtime['min_duration_ms'] = min_dur
    max_dur = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_MAX_DURATION_MS')
    if max_dur:
        runtime['max_duration_ms'] = max_dur

    # Load pattern: explicit, else inferred from the type/inputs.
    load_pattern = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_LOAD_PATTERN')
    target_qps = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_TARGET_QPS')
    concurrency = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_CONCURRENCY')
    if not load_pattern:
        if conf_type == 'online':
            load_pattern = 'concurrency' if (
                concurrency and not target_qps) else 'poisson'
        else:
            load_pattern = 'max_throughput'

    if conf_type == 'online':
        if load_pattern == 'poisson' and not target_qps:
            return {'return': 1,
                    'error': 'online poisson config requires --target_qps.'}
        if load_pattern == 'concurrency' and not concurrency:
            return {'return': 1,
                    'error': 'online concurrency config requires --concurrency.'}

    lp = {'type': load_pattern}
    if target_qps:
        lp['target_qps'] = float(target_qps)
    if concurrency:
        lp['target_concurrency'] = int(concurrency)

    settings = {}
    if runtime:
        settings['runtime'] = runtime
    settings['load_pattern'] = lp
    num_workers = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_NUM_WORKERS')
    if num_workers:
        settings['client'] = {'num_workers': int(num_workers)}
    cfg['settings'] = settings

    # CPU affinity (pin_loadgen) requires Linux; from-config has no CLI override,
    # so encode it in the config itself.
    if platform.system().lower() != 'linux':
        cfg['enable_cpu_affinity'] = False

    # --- endpoint_config ---
    url = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_URL') or 'http://localhost:8000'
    endpoint_config = {'endpoints': [url]}
    api_key = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_API_KEY')
    endpoint_config['api_key'] = api_key if api_key else None
    api_type = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_API_TYPE') or 'openai'
    endpoint_config['api_type'] = api_type
    cfg['endpoint_config'] = endpoint_config

    report_dir = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_REPORT_DIR')
    if report_dir:
        cfg['report_dir'] = report_dir

    # --- write YAML ---
    conf_path = _f(env, 'MLC_MLPERF_ENDPOINTS_CONF_PATH')
    if not conf_path:
        conf_path = os.path.join(os.getcwd(), 'endpoints_conf.yaml')
    conf_path = os.path.abspath(conf_path)
    os.makedirs(os.path.dirname(conf_path), exist_ok=True)
    with open(conf_path, 'w') as f:
        yaml.safe_dump(cfg, f, sort_keys=False, default_flow_style=False)
    env['MLC_MLPERF_ENDPOINTS_CONF_PATH'] = conf_path

    logger.info('')
    logger.info(f'Generated endpoints config ({conf_type}) at: {conf_path}')
    logger.info('-' * 60)
    for line in yaml.safe_dump(cfg, sort_keys=False).splitlines():
        logger.info('  ' + line)
    logger.info('-' * 60)
    logger.info('')

    return {'return': 0}


def postprocess(i):
    return {'return': 0}
