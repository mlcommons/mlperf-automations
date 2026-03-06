from mlc import utils
import os
import json
from utils import is_true


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
        # Pass parts separately so shell scripts can construct the command
        # without quoting issues
        env['MLC_GEEKBENCH_LICENSE_KEY'] = license_key
        env['MLC_GEEKBENCH_LICENSE_EMAIL'] = license_email
        logger.info(
            "Geekbench license key provided, will register before benchmark")

    # Build the run command
    args = []

    # Workload selection (CPU or compute)
    workload = env.get('MLC_GEEKBENCH_WORKLOAD', '').strip()
    if workload:
        args.append(workload)

    # No-upload flag
    if is_true(env.get('MLC_GEEKBENCH_NO_UPLOAD', 'yes')):
        args.append('--no-upload')

    # Export results as JSON
    if is_true(env.get('MLC_GEEKBENCH_EXPORT_JSON', 'yes')):
        results_dir = env.get('MLC_GEEKBENCH_RESULTS_DIR', os.getcwd())
        os.makedirs(results_dir, exist_ok=True)
        results_file = os.path.join(results_dir, 'geekbench_results.json')
        args.append('--export-json')
        args.append(f'"{results_file}"')

        env['MLC_GEEKBENCH_RESULTS_FILE'] = results_file
        env['MLC_GEEKBENCH_RESULTS_DIR'] = results_dir

    cmd = f"{q}{geekbench_bin}{q} {' '.join(args)}"

    env['MLC_RUN_CMD'] = cmd
    env['MLC_RUN_DIR'] = results_dir

    logger.info(f"Geekbench command: {cmd}")
    logger.info(f"Results will be saved to: {results_file}")

    return {'return': 0}


def postprocess(i):

    env = i['env']
    logger = i['automation'].logger
    state = i['state']

    results_file = env.get('MLC_GEEKBENCH_RESULTS_FILE', '')

    if results_file:
        if os.path.isfile(results_file):
            logger.info(f"Geekbench results saved to: {results_file}")

            try:
                with open(results_file, 'r') as f:
                    results = json.load(f)

                # Extract key scores from the results JSON
                if 'score' in results:
                    env['MLC_GEEKBENCH_SCORE'] = str(results['score'])
                    logger.info(f"Geekbench Score: {results['score']}")

                if 'multicore_score' in results:
                    env['MLC_GEEKBENCH_MULTICORE_SCORE'] = str(
                        results['multicore_score'])
                    logger.info(
                        f"Geekbench Multi-Core Score: {results['multicore_score']}")

                if 'single_core_score' in results:
                    env['MLC_GEEKBENCH_SINGLE_CORE_SCORE'] = str(
                        results['single_core_score'])
                    logger.info(
                        f"Geekbench Single-Core Score: {results['single_core_score']}")

                state['geekbench_results'] = results

            except Exception as e:
                logger.warning(f"Could not parse Geekbench results: {e}")
        else:
            logger.warning(
                "Geekbench results file not found. The benchmark may not have completed successfully.")

    return {'return': 0}
