from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if env.get('MLC_DATASET_DOWNLOAD_SRC', '') != "mlcommons":
        print("Using MLCommons Inference source from '" +
              env['MLC_MLPERF_INFERENCE_SOURCE'] + "'")
        downloader_path = os.path.join(
            env['MLC_MLPERF_INFERENCE_SOURCE'], 'automotive', 'llm', 'download_data.py')
        env['MLC_DATASET_MMLU_PATH'] = os.path.join(
            env.get('MLC_DATASET_MMLU_OUT_PATH', os.getcwd()), "mmlu.json")
        run_cmd = f"{env['MLC_PYTHON_BIN_WITH_PATH']} {downloader_path} --output {env['MLC_DATASET_MMLU_PATH']}"
        if env.get('MLC_DATASET_MMLU_COUNT', '') != '':
            run_cmd += f" --count {int(env['MLC_DATASET_MMLU_COUNT'])})"

    env['MLC_RUN_CMD'] = run_cmd

    return {'return': 0}


def postprocess(i):

    env = i['env']

    print(
        f"Path to the MMLU dataset: {env['MLC_DATASET_MMLU_PATH']}")

    return {'return': 0}
