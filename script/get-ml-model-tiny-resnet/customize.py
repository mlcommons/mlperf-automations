from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if is_true(env.get("MLC_TMP_ML_MODEL_TF2ONNX", "")):
        outputfile = env.get('MLC_ML_MODEL_OUTFILE', 'model_quant.onnx')
        env['MLC_RUN_CMD'] = env['MLC_PYTHON_BIN_WITH_PATH'] + " -m tf2onnx.convert --tflite " + \
            env['MLC_ML_MODEL_FILE_WITH_PATH'] + " --output " + \
            outputfile + " --inputs-as-nchw \"input_1_int8\""
        env['MLC_ML_MODEL_FILE_WITH_PATH'] = os.path.join(
            os.getcwd(), outputfile)

    return {'return': 0}


def postprocess(i):

    env = i['env']

    env['MLC_ML_MODEL_FILE'] = os.path.basename(
        env['MLC_ML_MODEL_FILE_WITH_PATH'])
    env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_ML_MODEL_FILE_WITH_PATH']

    return {'return': 0}
