from mlc import utils
import os


def preprocess(i):
    env = i['env']

    backend = str(env.get('MLC_GAIA_BACKEND', 'mock')).lower()
    if backend == 'endpoint' and not env.get(
            'MLC_GAIA_ENDPOINT_URL', '').strip():
        return {'return': 1,
                'error': 'endpoint backend requires --endpoint (MLC_GAIA_ENDPOINT_URL)'}

    # The workload is executed by the benchmark-program posthook dependency.
    python_bin = env.get('MLC_PYTHON_BIN_WITH_PATH', 'python3')
    script = os.path.join(
        env['MLC_TMP_CURRENT_SCRIPT_PATH'],
        'src',
        'run_gaia.py')
    env['MLC_RUN_CMD'] = f'{python_bin} "{script}"'
    if not env.get('MLC_RUN_DIR', ''):
        env['MLC_RUN_DIR'] = os.getcwd()

    return {'return': 0}


def postprocess(i):
    env = i['env']
    state = i['state']
    logger = i['automation'].action_object.logger

    output_dir = env.get('MLC_GAIA_OUTPUT_DIR', '') or os.getcwd()
    results_file = os.path.join(output_dir, 'gaia_results.json')

    if not os.path.isfile(results_file):
        return {'return': 1, 'error': f'GAIA results not found: {results_file}'}

    import json
    with open(results_file, encoding='utf-8') as f:
        data = json.load(f)

    env['MLC_GAIA_RESULTS_FILE'] = results_file
    env['MLC_GAIA_ACCURACY'] = str(data.get('accuracy', ''))
    state['mlc_gaia'] = data

    logger.info(
        f"GAIA accuracy ({data.get('trace_type')}): {data.get('accuracy')}")
    return {'return': 0}
