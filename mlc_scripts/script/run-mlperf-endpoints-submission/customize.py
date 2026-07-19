from mlc import utils
from utils import is_true
import os
import platform


def preprocess(i):

    env = i['env']
    logger = i['automation'].logger

    if not env.get('MLC_MLPERF_ENDPOINTS_PYTHON_BIN', '').strip():
        return {'return': 1,
                'error': 'inference-endpoint is not installed '
                '(get,mlperf,endpoints dependency did not run).'}
    if not env.get('MLC_MLPERF_ENDPOINTS_CLI_BIN', '').strip():
        return {'return': 1,
                'error': 'endpoints-submission-cli is not installed '
                '(get,mlperf,endpoints-submission-cli dependency did not run).'}
    if not env.get('MLC_MLPERF_ENDPOINTS_SYSTEM_DESC_PATH', '').strip():
        return {'return': 1,
                'error': 'system_desc.json path is unset. Pass --system_desc=<path> '
                'or let generate,mlperf,endpoints-system-desc create one.'}

    # Output directory holding all per-point run folders.
    out_dir = env.get('MLC_MLPERF_ENDPOINTS_SUB_OUTPUT_DIR', '').strip()
    if not out_dir:
        out_dir = os.path.join(os.getcwd(), 'endpoints_submission')
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    env['MLC_MLPERF_ENDPOINTS_SUB_OUTPUT_DIR'] = out_dir
    env['MLC_MLPERF_ENDPOINTS_SUB_RUN_IDS_FILE'] = os.path.join(
        out_dir, 'run_ids.json')

    # Self-contained local testing against the bundled echo server.
    if is_true(env.get('MLC_MLPERF_ENDPOINTS_SUB_USE_ECHO_SERVER', '')):
        port = env.get('MLC_MLPERF_ENDPOINTS_SUB_ECHO_PORT', '8765').strip()
        env['MLC_MLPERF_ENDPOINTS_SUB_ECHO_PORT'] = port
        env['MLC_MLPERF_ENDPOINTS_SUB_URL'] = f'http://localhost:{port}'
        if not env.get('MLC_MLPERF_ENDPOINTS_SUB_MODEL', '').strip():
            env['MLC_MLPERF_ENDPOINTS_SUB_MODEL'] = 'test-model'
        if not env.get('MLC_MLPERF_ENDPOINTS_SUB_DATASET_PATH', '').strip():
            src = env.get('MLC_MLPERF_INFERENCE_ENDPOINTS_SOURCE', '').strip()
            dummy = os.path.join(
                src, 'tests', 'assets', 'datasets', 'dummy_1k.jsonl')
            if not os.path.isfile(dummy):
                return {'return': 1,
                        'error': 'echo-server run requested without --dataset and '
                        f'the bundled dummy dataset was not found at {dummy}.'}
            env['MLC_MLPERF_ENDPOINTS_SUB_DATASET_PATH'] = dummy
            if not env.get('MLC_MLPERF_ENDPOINTS_SUB_PROMPT_COLUMN', '').strip():
                env['MLC_MLPERF_ENDPOINTS_SUB_PROMPT_COLUMN'] = 'text_input'
        # echo runs have no tokenizer/accuracy; keep them quick by default
        if not env.get('MLC_MLPERF_ENDPOINTS_SUB_DURATION', '').strip():
            env['MLC_MLPERF_ENDPOINTS_SUB_DURATION'] = '10s'
        if not env.get('MLC_MLPERF_ENDPOINTS_SUB_NUM_SAMPLES', '').strip():
            env['MLC_MLPERF_ENDPOINTS_SUB_NUM_SAMPLES'] = '200'
        if not env.get('MLC_MLPERF_ENDPOINTS_SUB_NUM_WORKERS', '').strip():
            env['MLC_MLPERF_ENDPOINTS_SUB_NUM_WORKERS'] = '2'
        # Cap the connection pool + settle between points: several back-to-back
        # localhost benchmarks otherwise exhaust ephemeral ports (esp. on macOS).
        if not env.get('MLC_MLPERF_ENDPOINTS_SUB_MAX_CONNECTIONS', '').strip():
            env['MLC_MLPERF_ENDPOINTS_SUB_MAX_CONNECTIONS'] = '128'
        if not env.get('MLC_MLPERF_ENDPOINTS_SUB_SETTLE_SECONDS', '').strip():
            env['MLC_MLPERF_ENDPOINTS_SUB_SETTLE_SECONDS'] = '3'
        # Accuracy against the echo server: it returns the prompt verbatim, so
        # string_match with ground_truth == prompt column scores 1.0. This
        # exercises the accuracy plumbing (the score is not meaningful).
        if is_true(env.get('MLC_MLPERF_ENDPOINTS_SUB_WITH_ACCURACY', '')):
            defaults = {
                'MLC_MLPERF_ENDPOINTS_SUB_ACC_DATASET_PATH':
                    env['MLC_MLPERF_ENDPOINTS_SUB_DATASET_PATH'],
                'MLC_MLPERF_ENDPOINTS_SUB_EVAL_METHOD': 'string_match',
                'MLC_MLPERF_ENDPOINTS_SUB_GROUND_TRUTH': 'text_input',
                'MLC_MLPERF_ENDPOINTS_SUB_EXTRACTOR': 'identity_extractor',
                'MLC_MLPERF_ENDPOINTS_SUB_ACC_NUM_SAMPLES': '20',
            }
            for k, v in defaults.items():
                if not env.get(k, '').strip():
                    env[k] = v

    if not env.get('MLC_MLPERF_ENDPOINTS_SUB_URL', '').strip():
        return {'return': 1,
                'error': 'Endpoint URL is required (--endpoints), '
                'or use the _echo-server variation.'}
    if not env.get('MLC_MLPERF_ENDPOINTS_SUB_MODEL', '').strip():
        return {'return': 1, 'error': 'Model name is required (--model).'}
    if not env.get('MLC_MLPERF_ENDPOINTS_SUB_DATASET_PATH', '').strip():
        return {'return': 1, 'error': 'Dataset path is required (--dataset).'}

    if (is_true(env.get('MLC_MLPERF_ENDPOINTS_SUB_WITH_ACCURACY', ''))
            and not env.get('MLC_MLPERF_ENDPOINTS_SUB_ACC_DATASET_PATH', '').strip()):
        return {'return': 1,
                'error': '_with-accuracy requires --accuracy_dataset (plus '
                '--eval_method / --ground_truth / --extractor), or use '
                '_echo-server which supplies echo-friendly defaults.'}

    # CPU affinity (pin_loadgen) requires Linux.
    env['MLC_MLPERF_ENDPOINTS_SUB_NO_CPU_AFFINITY'] = (
        'no' if platform.system().lower() == 'linux' else 'yes')

    if is_true(env.get('MLC_MLPERF_ENDPOINTS_SUB_RUNS_DRY_RUN', '')):
        logger.info('runs-dry-run mode: run folders are parsed/printed but not '
                    'uploaded, and no submission is assembled.')
    elif not os.environ.get('PRISM_USER_API_TOKEN', '').strip():
        logger.warning(
            'PRISM_USER_API_TOKEN is not set in the environment. `runs create` '
            'and `submissions create --dry-run` will fail without it. Either '
            'export it, or use the _runs-dry-run variation for an offline check.')

    return {'return': 0}


def postprocess(i):
    return {'return': 0}
