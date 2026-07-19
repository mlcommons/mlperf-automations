from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if env.get("MLC_MODEL_HUGG_PATH", "") == "":
        return {'return': 1, 'error': 'MLC_MODEL_HUGG_PATH is not set'}

    automation = i['automation']

    cm = automation.action_object

    path = os.getcwd()

    return {'return': 0}


def postprocess(i):
    os_info = i['os_info']

    env = i['env']
    env['HUGGINGFACE_ONNX_FILE_PATH'] = os.path.join(os.getcwd(), "model.onnx")
    return {'return': 0}
