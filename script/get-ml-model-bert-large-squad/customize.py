from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']
    if is_true(env.get('MLC_ML_MODEL_BERT_PACKED', '')):
        i['run_script_input']['script_name'] = "run-packed"
        env['MLC_BERT_CONFIG_PATH'] = os.path.join(
            env['MLC_MLPERF_INFERENCE_BERT_PATH'], "bert_config.json")
        env['MLC_BERT_CHECKPOINT_DOWNLOAD_DIR'] = os.getcwd()
        env['MLC_ML_MODEL_FILE_WITH_PATH'] = os.path.join(
            os.getcwd(), "model.onnx")
        env['MLC_ML_MODEL_BERT_PACKED_PATH'] = os.path.join(
            os.getcwd(), "model.onnx")

    return {'return': 0}


def postprocess(i):

    env = i['env']

    env['MLC_ML_MODEL_FILE'] = os.path.basename(
        env['MLC_ML_MODEL_FILE_WITH_PATH'])

    if env.get('MLC_ML_MODEL_PRECISION', '') == "fp32":
        env['MLC_ML_MODEL_BERT_LARGE_FP32_PATH'] = env['MLC_ML_MODEL_FILE_WITH_PATH']
    elif env.get('MLC_ML_MODEL_PRECISION', '') == "int8":
        env['MLC_ML_MODEL_BERT_LARGE_INT8_PATH'] = env['MLC_ML_MODEL_FILE_WITH_PATH']

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_ML_MODEL_FILE_WITH_PATH']

    return {'return': 0}
