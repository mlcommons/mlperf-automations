from mlc import utils
import os


def preprocess(i):
    env = i['env']

    if env.get('MLC_HNSWLIB_DATASET', 'synthetic') == 'real':
        if not env.get('MLC_HNSWLIB_DATASET_FILE', '').strip():
            return {'return': 1,
                    'error': 'Real dataset selected but MLC_HNSWLIB_DATASET_FILE '
                             'is not set (download dependency did not run)'}

    # The workload is executed by the benchmark-program posthook dependency.
    python_bin = env.get('MLC_PYTHON_BIN_WITH_PATH', 'python3')
    script = os.path.join(
        env['MLC_TMP_CURRENT_SCRIPT_PATH'],
        'src',
        'run_hnswlib.py')
    env['MLC_RUN_CMD'] = f'{python_bin} "{script}"'
    if not env.get('MLC_RUN_DIR', ''):
        env['MLC_RUN_DIR'] = os.getcwd()

    return {'return': 0}


def postprocess(i):
    env = i['env']
    state = i['state']
    logger = i['automation'].action_object.logger

    output_dir = env.get('MLC_HNSWLIB_OUTPUT_DIR', '') or os.getcwd()
    results_file = os.path.join(output_dir, 'hnswlib_results.json')

    if not os.path.isfile(results_file):
        return {'return': 1, 'error': f'hnswlib results not found: {results_file}'}

    import json
    with open(results_file, encoding='utf-8') as f:
        data = json.load(f)

    env['MLC_HNSWLIB_RESULTS_FILE'] = results_file
    env['MLC_HNSWLIB_RECALL'] = str(data.get('recall_at_k', ''))
    env['MLC_HNSWLIB_QPS'] = str(data.get('query_qps', ''))
    env['MLC_HNSWLIB_BUILD_TIME'] = str(data.get('build_time_sec', ''))
    state['mlc_hnswlib'] = data

    logger.info(f"hnswlib recall@k={data.get('recall_at_k')} "
                f"QPS={data.get('query_qps')} build={data.get('build_time_sec')}s")
    return {'return': 0}
