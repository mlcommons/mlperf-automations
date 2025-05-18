from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if is_true(env.get('MLC_TMP_ML_MODEL_RETINANET_NO_NMS', '')):
        i['run_script_input']['script_name'] = "run-no-nms"
        env['MLC_ML_MODEL_FILE_WITH_PATH'] = os.path.join(
            os.getcwd(), "retinanet.onnx")

    return {'return': 0}


def postprocess(i):

    env = i['env']

    env['MLC_ML_MODEL_FILE'] = os.path.basename(
        env['MLC_ML_MODEL_FILE_WITH_PATH'])
    if env.get('MLC_ENV_NAME_ML_MODEL_FILE', '') != '':
        env[env['MLC_ENV_NAME_ML_MODEL_FILE']
            ] = env['MLC_ML_MODEL_FILE_WITH_PATH']

    if is_true(env.get("MLC_QAIC_PRINT_NODE_PRECISION_INFO", '')):
        env['MLC_ML_MODEL_RETINANET_QAIC_NODE_PRECISION_INFO_FILE_PATH'] = os.path.join(
            os.getcwd(), 'node-precision-info.yaml')

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_ML_MODEL_FILE_WITH_PATH']

    return {'return': 0}
