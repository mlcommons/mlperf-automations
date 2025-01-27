from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if os_info['platform'] == "windows":
        return {'return': 1, 'error': 'Script not supported in windows yet!'}

    if env.get('MLC_ML_MODEL_POINT_PILLARS_PATH', '') == '':
        return {'return': 1, 'error': 'Please provide path to pointpillars model using tag \\`--pp_path\\`as automatic download of this model is not supported yet.'}

    if os.path.isdir(env['MLC_ML_MODEL_POINT_PILLARS_PATH']):
        if env['MLC_ML_MODEL_PP_FORMAT'] == "onnx":
            env['MLC_ML_MODEL_POINT_PILLARS_PATH'] = os.path.join(
                env['MLC_ML_MODEL_POINT_PILLARS_PATH'], "pp.onnx")
        else:
            env['MLC_ML_MODEL_POINT_PILLARS_PATH'] = os.path.join(
                env['MLC_ML_MODEL_POINT_PILLARS_PATH'], "pp_ep36.pth")

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
