from mlc import utils
import os
from os.path import exists
import shutil


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    submission_dir = env.get("MLC_MLPERF_INFERENCE_SUBMISSION_DIR", "")

    if submission_dir == "":
        print("Please set --env.MLC_MLPERF_INFERENCE_SUBMISSION_DIR")
        return {'return': 1,
                'error': 'MLC_MLPERF_INFERENCE_SUBMISSION_DIR is not specified'}

    if not os.path.exists(submission_dir):
        print("Please set --env.MLC_MLPERF_INFERENCE_SUBMISSION_DIR to a valid submission directory")
        return {'return': 1,
                'error': 'MLC_MLPERF_INFERENCE_SUBMISSION_DIR is not existing'}

    submission_dir = submission_dir.rstrip(os.path.sep)
    submitter = env.get("MLC_MLPERF_SUBMITTER", "MLCommons")
    submission_processed = f"{submission_dir}_processed"

    if os.path.exists(submission_processed):
        print(f"Cleaning {submission_processed}")
        shutil.rmtree(submission_processed)

    version = env.get('MLC_MLPERF_SUBMISSION_CHECKER_VERSION', '')
    x_version = ' --version ' + version + ' ' if version != '' else ''

    CMD = env['MLC_PYTHON_BIN'] + " '" + os.path.join(env['MLC_MLPERF_INFERENCE_SOURCE'], "tools", "submission",
                                                      "preprocess_submission.py") + "' --input '" + submission_dir + "' --submitter '" + submitter + "' --output '" + submission_processed + "'" + x_version
    env['MLC_RUN_CMD'] = CMD

    return {'return': 0}


def postprocess(i):

    env = i['env']
    submission_dir = env["MLC_MLPERF_INFERENCE_SUBMISSION_DIR"]
    import datetime
    submission_backup = submission_dir + "_backup_" + \
        '{date:%Y-%m-%d_%H:%M:%S}'.format(date=datetime.datetime.now())

    submission_processed = submission_dir + "_processed"
    shutil.copytree(submission_dir, submission_backup)
    shutil.rmtree(submission_dir)
    os.rename(submission_processed, submission_dir)

    return {'return': 0}
