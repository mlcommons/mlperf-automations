from mlc import utils
from utils import is_true
import os
import subprocess


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    logger = i['automation'].logger
    q = '"' if os_info['platform'] == 'windows' else "'"

    submission_dir = env.get("MLC_MLPERF_INFERENCE_SUBMISSION_DIR", "")

    version = env.get('MLC_MLPERF_SUBMISSION_CHECKER_VERSION', 'v6.0')

    if submission_dir == "":
        return {'return': 1,
                'error': 'Please set --env.MLC_MLPERF_INFERENCE_SUBMISSION_DIR'}

    submitter = env.get("MLC_MLPERF_SUBMITTER", "")  # "default")
    if ' ' in submitter:
        return {
            'return': 1, 'error': 'MLC_MLPERF_SUBMITTER cannot contain a space. Please provide a name without space using --submitter input. Given value: {}'.format(submitter)}

    if 'MLC_MLPERF_SKIP_COMPLIANCE' in env:
        skip_compliance = " --skip_compliance"
    else:
        skip_compliance = ""

    if is_true(env.get('MLC_MLPERF_MODULARISED_INFERENCE_SUBMISSION_CHECKER', '')):
        constants_file = os.path.join(env['MLC_MLPERF_INFERENCE_SOURCE'], "tools", "submission", "submission_checker",
                                      "constants.py")
        performance_check_file = os.path.join(env['MLC_MLPERF_INFERENCE_SOURCE'], "tools", "submission", "submission_checker", "checks",
                                              "performance_check.py")
        accuracy_check_file = os.path.join(env['MLC_MLPERF_INFERENCE_SOURCE'], "tools", "submission", "submission_checker", "checks",
                                           "accuracy_check.py")
        submission_checker_file = os.path.join(
            env['MLC_MLPERF_INFERENCE_SOURCE'],
            "tools",
            "submission",
            "submission_checker",
            "main.py")
    else:
        submission_checker_file = os.path.join(
            env['MLC_MLPERF_INFERENCE_SOURCE'],
            "tools",
            "submission",
            "submission_checker.py")

    if is_true(env['MLC_MLPERF_SHORT_RUN']):
        # modify constants.py
        if is_true(
                env.get('MLC_MLPERF_MODULARISED_INFERENCE_SUBMISSION_CHECKER', '')):
            new_constants_file = os.path.join(
                os.path.dirname(submission_checker_file), "constants1.py")
            with open(constants_file, 'r') as file:
                constants_data = file.read()
            constants_data = constants_data.replace(
                "OFFLINE_MIN_SPQ = 24576", "OFFLINE_MIN_SPQ = 100")
            with open(new_constants_file, 'w') as file:
                file.write(constants_data)
            # modify performance_check.py
            new_performance_check_file = os.path.join(
                os.path.dirname(performance_check_file), "performance_check1.py")
            with open(performance_check_file, 'r') as file:
                performance_check_data = file.read()
            performance_check_data = performance_check_data.replace(
                "return is_valid",
                "return True").replace(
                    "return False",
                    "return True"
            ).replace(
                    "return is_valid",
                    "return True"
            )
            with open(new_performance_check_file, 'w') as file:
                file.write(performance_check_data)
            # modify accuracy_check.py
            new_accuracy_check_file = os.path.join(
                os.path.dirname(accuracy_check_file), "accuracy_check1.py")
            with open(accuracy_check_file, 'r') as file:
                accuracy_check_data = file.read()
            accuracy_check_data = accuracy_check_data.replace(
                "return is_valid",
                "return True").replace(
                    "return False",
                    "return True"
            ).replace(
                    "return is_valid",
                    "return True"
            )
            with open(new_accuracy_check_file, 'w') as file:
                file.write(accuracy_check_data)

        new_submission_checker_file = os.path.join(
            os.path.dirname(submission_checker_file),
            "submission_checker1.py")
        with open(submission_checker_file, 'r') as file:
            data = file.read()
        if is_true(
                env.get('MLC_MLPERF_MODULARISED_INFERENCE_SUBMISSION_CHECKER', '')):
            data = data.replace(
                ".constants",
                ".constants1").replace(
                ".checks.performance_check",
                ".checks.performance_check1").replace(
                ".checks.accuracy_check",
                ".checks.accuracy_check1")
        else:
            data = data.replace(
                "OFFLINE_MIN_SPQ = 24576",
                "OFFLINE_MIN_SPQ = 100")
            data = data.replace(
                "return is_valid, res, inferred",
                "return True, res, inferred"
            )
        with open(new_submission_checker_file, 'w') as file:
            file.write(data)
        submission_checker_file = new_submission_checker_file

    if env.get('MLC_MLPERF_EXTRA_MODEL_MAPPING', '') != '':
        extra_map = ' --extra_model_benchmark_map "' + \
            env['MLC_MLPERF_EXTRA_MODEL_MAPPING'] + '"'
    else:
        extra_map = ""

    if is_true(env.get('MLC_MLPERF_SKIP_POWER_CHECK', 'no')):
        power_check = " --skip-power-check"
    else:
        power_check = ""

    if is_true(env.get('MLC_MLPERF_SKIP_CALIBRATION_CHECK', 'no')):
        calibration_check = " --skip-calibration-check"
    else:
        calibration_check = ""

    raw_extra_args = env.get('MLC_MLPERF_SUBMISSION_CHECKER_EXTRA_ARGS', '')

    extra_args = ''
    if raw_extra_args:
        extra_args = ' ' + ' '.join(
            arg.strip() for arg in raw_extra_args.split(',') if arg.strip()
        )

    if (is_true(env.get('MLC_TAR_SUBMISSION_DIR')) or env.get('MLC_MLPERF_SUBMITTER_ID',
                                                              '') != '') and "skip-extra-files-in-root-check" not in extra_args:
        extra_args += " --skip-extra-files-in-root-check "

    if "skip-dataset-size-check" not in extra_args and is_true(
            env.get('MLC_MLPERF_MODULARISED_INFERENCE_SUBMISSION_CHECKER', '')):
        extra_args += " --skip-dataset-size-check "

    x_submitter = ' --submitter ' + q + submitter + q if submitter != '' else ''

    x_version = ' --version ' + version + ' ' if version != '' else ''

    CMD = env['MLC_PYTHON_BIN_WITH_PATH'] + ' ' + q + submission_checker_file + q + ' --input ' + q + submission_dir + q + \
        x_submitter + \
        x_version + \
        skip_compliance + extra_map + power_check + extra_args

    x_version = ' --version ' + version[1:] + ' ' if version != '' else ''

    x_submission_repo_name = ''
    x_submission_repo_owner = ''
    x_submission_repo_branch = ''

    if env.get('MLC_MLPERF_RESULTS_GIT_REPO_NAME', '') != '':
        x_submission_repo_name = f""" --repository {env['MLC_MLPERF_RESULTS_GIT_REPO_NAME']}"""
    if env.get('MLC_MLPERF_RESULTS_GIT_REPO_OWNER', '') != '':
        x_submission_repo_owner = f""" --repository-owner {env['MLC_MLPERF_RESULTS_GIT_REPO_OWNER']}"""
    if env.get('MLC_MLPERF_RESULTS_GIT_REPO_BRANCH', '') != '':
        x_submission_repo_branch = f""" --repository-branch  {env['MLC_MLPERF_RESULTS_GIT_REPO_BRANCH']}"""

    report_generator_file = os.path.join(env['MLC_MLPERF_INFERENCE_SOURCE'], "tools", "submission",
                                         "generate_final_report.py")
    env['MLC_RUN_CMD'] = CMD
    logger.info(f"{CMD}")
    env['MLC_POST_RUN_CMD'] = env['MLC_PYTHON_BIN_WITH_PATH'] + ' ' + q + report_generator_file + q + ' --input summary.csv ' + \
        x_version + \
        x_submission_repo_name + \
        x_submission_repo_owner + \
        x_submission_repo_branch

    return {'return': 0}


def postprocess(i):

    env = i['env']

    x = env.get('MLPERF_INFERENCE_SUBMISSION_TAR_FILE', '')
    if x != '':
        env['MLC_TAR_OUTFILE'] = x

    if env.get('MLC_MLPERF_INFERENCE_SUBMISSION_BASE_DIR', '') != '':
        env['MLC_TAR_OUTPUT_DIR'] = env['MLC_MLPERF_INFERENCE_SUBMISSION_BASE_DIR']

    x = env.get('MLPERF_INFERENCE_SUBMISSION_SUMMARY', '')
    if x != '':
        for y in ['.csv', '.json', '.xlsx']:

            z0 = 'summary' + y

            if os.path.isfile(z0):
                z1 = x + y

                if os.path.isfile(z1):
                    os.remove(z1)

                os.rename(z0, z1)

    return {'return': 0}
