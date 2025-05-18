from mlc import utils
import os
import subprocess
from os.path import exists


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    logger = i['automation'].logger
    submission_dir = env.get("MLC_MLPERF_INFERENCE_SUBMISSION_DIR", "")

    if submission_dir == "":
        logger.error("Please set MLC_MLPERF_INFERENCE_SUBMISSION_DIR")
        return {'return': 1, 'error': 'MLC_MLPERF_INFERENCE_SUBMISSION_DIR is not specified in env in run-mlperf-accuracy-log-truncator'}

    submitter = env.get("MLC_MLPERF_SUBMITTER", "CTuning")

    os.system("rm -rf " + submission_dir + "_logs")

    CMD = env['MLC_PYTHON_BIN'] + " '" + os.path.join(env['MLC_MLPERF_INFERENCE_SOURCE'], "tools", "submission",
                                                      "truncate_accuracy_log.py") + "' --input '" + submission_dir + "' --submitter '" + submitter + "' --backup '" + submission_dir + "_logs'"
    env['MLC_RUN_CMD'] = CMD

    return {'return': 0}
