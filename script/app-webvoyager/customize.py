from mlc import utils
import os


def preprocess(i):
    env = i['env']

    backend = str(env.get('MLC_WEBVOYAGER_BACKEND', 'mock')).lower()
    if backend == 'endpoint' and not env.get(
            'MLC_WEBVOYAGER_ENDPOINT_URL', '').strip():
        return {'return': 1,
                'error': 'endpoint backend requires --endpoint (MLC_WEBVOYAGER_ENDPOINT_URL)'}

    # When the official repo is cloned, point the harness at its task files.
    src = env.get('MLC_WEBVOYAGER_SRC_PATH', '').strip()
    if src and not env.get('MLC_WEBVOYAGER_TASK_FILE', '').strip():
        env['MLC_WEBVOYAGER_TASK_FILE'] = os.path.join(
            src, 'data', 'WebVoyager_data.jsonl')
        ref = os.path.join(src, 'data', 'reference_answer.json')
        if os.path.isfile(ref):
            env['MLC_WEBVOYAGER_REF_FILE'] = ref

    # The workload is executed by the benchmark-program posthook dependency.
    python_bin = env.get('MLC_PYTHON_BIN_WITH_PATH', 'python3')
    script = os.path.join(
        env['MLC_TMP_CURRENT_SCRIPT_PATH'],
        'src',
        'run_webvoyager.py')
    env['MLC_RUN_CMD'] = f'{python_bin} "{script}"'
    if not env.get('MLC_RUN_DIR', ''):
        env['MLC_RUN_DIR'] = os.getcwd()

    return {'return': 0}


def postprocess(i):
    env = i['env']
    state = i['state']
    logger = i['automation'].action_object.logger

    output_dir = env.get('MLC_WEBVOYAGER_OUTPUT_DIR', '') or os.getcwd()
    results_file = os.path.join(output_dir, 'webvoyager_results.json')

    if not os.path.isfile(results_file):
        return {'return': 1, 'error': f'WebVoyager results not found: {results_file}'}

    import json
    with open(results_file, encoding='utf-8') as f:
        data = json.load(f)

    env['MLC_WEBVOYAGER_RESULTS_FILE'] = results_file
    env['MLC_WEBVOYAGER_SUCCESS_RATE'] = str(data.get('success_rate', ''))
    state['mlc_webvoyager'] = data

    logger.info(f"WebVoyager success rate: {data.get('success_rate')}")
    return {'return': 0}
