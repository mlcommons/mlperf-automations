import os
import re
import shutil


def _extract_ruleset_from_repo(repo_url):
    match = re.search(r'_v(\d+\.\d+)', repo_url)
    if match:
        return '{}.0'.format(match.group(1))
    return ''


def preprocess(i):
    os_info = i['os_info']
    env = i['env']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    repo_url = env.get('MLC_MLPERF_TRAINING_RESULTS_REPO_URL', '').strip()
    if repo_url == '':
        return {'return': 1, 'error': 'Please set MLC_MLPERF_TRAINING_RESULTS_REPO_URL'}

    ruleset = env.get('MLC_MLPERF_TRAINING_RESULTS_RULESET', '').strip()
    if ruleset == '':
        ruleset = _extract_ruleset_from_repo(repo_url)
        if ruleset == '':
            return {'return': 1, 'error': 'Please set MLC_MLPERF_TRAINING_RESULTS_RULESET'}
        env['MLC_MLPERF_TRAINING_RESULTS_RULESET'] = ruleset

    summary_file = env.get('MLC_MLPERF_TRAINING_RESULTS_SUMMARY_FILE',
                           'summary_results.json').strip()
    if not summary_file.endswith('.json'):
        return {'return': 1, 'error': 'MLC_MLPERF_TRAINING_RESULTS_SUMMARY_FILE should end with .json'}

    summary_json = summary_file if os.path.isabs(
        summary_file) else os.path.abspath(summary_file)
    summary_csv = summary_json[:-5] + '.csv'

    env['MLC_MLPERF_TRAINING_RESULTS_SUMMARY_JSON'] = summary_json
    env['MLC_MLPERF_TRAINING_RESULTS_SUMMARY_CSV'] = summary_csv

    env['MLC_RUN_CMD'] = '{} -m mlperf_logging.result_summarizer "$MLC_MLPERF_TRAINING_RESULTS_PATH" training {} --csv "{}"'.format(
        env['MLC_PYTHON_BIN_WITH_PATH'], ruleset, summary_csv
    )

    return {'return': 0}


def postprocess(i):
    env = i['env']

    summary_json = env.get('MLC_MLPERF_TRAINING_RESULTS_SUMMARY_JSON', '')
    if summary_json and os.path.isfile(summary_json):
        summary_dir = os.path.dirname(summary_json)
        summary_name = os.path.basename(summary_json)

        if summary_name == 'summary_results.json':
            compat_summary = os.path.join(summary_dir, 'results_summary.json')
            shutil.copyfile(summary_json, compat_summary)

    return {'return': 0}
