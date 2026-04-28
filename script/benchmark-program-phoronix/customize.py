from mlc import utils
import os
import json
from utils import is_true


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    logger = i['automation'].logger

    results_dir = env.get('MLC_PHORONIX_RESULTS_DIR', os.getcwd())
    os.makedirs(results_dir, exist_ok=True)
    env['MLC_PHORONIX_RESULTS_DIR'] = results_dir

    # Check phoronix-test-suite is installed
    if os.system('phoronix-test-suite version > /dev/null 2>&1' if os_info['platform'] != 'windows'
                 else 'phoronix-test-suite version > nul 2>&1') != 0:
        return {'return': 1,
                'error': 'phoronix-test-suite is not installed. '
                         'Install via: sudo apt install phoronix-test-suite (Linux) '
                         'or download from https://www.phoronix-test-suite.com/'}

    test = env.get('MLC_PHORONIX_TEST', '').strip()
    if not test:
        return {'return': 1, 'error': 'MLC_PHORONIX_TEST is required'}

    result_id = env.get('MLC_PHORONIX_RESULT_IDENTIFIER', 'mlc-benchmark')
    env['MLC_PHORONIX_RESULT_IDENTIFIER'] = result_id

    logger.info(f"Phoronix test: {test}, result ID: {result_id}")

    return {'return': 0}


def postprocess(i):

    env = i['env']
    logger = i['automation'].logger
    state = i['state']

    results_dir = env.get('MLC_PHORONIX_RESULTS_DIR', '')

    # Try to load exported JSON results
    results_json = os.path.join(results_dir, 'phoronix_results.json')
    if os.path.isfile(results_json):
        try:
            with open(results_json, 'r') as f:
                results = json.load(f)
            state['phoronix_results'] = results
            env['MLC_PHORONIX_SUMMARY_JSON'] = results_json
            logger.info(f"Phoronix results loaded from: {results_json}")
        except Exception as e:
            logger.warning(f"Could not parse Phoronix results JSON: {e}")
    else:
        logger.info("No JSON results exported (phoronix result-file-to-json may not be available)")

    # Parse the text output as fallback
    output_file = os.path.join(results_dir, 'phoronix_output.txt')
    if os.path.isfile(output_file):
        env['MLC_PHORONIX_OUTPUT_FILE'] = output_file
        logger.info(f"Phoronix text output: {output_file}")

    return {'return': 0}
