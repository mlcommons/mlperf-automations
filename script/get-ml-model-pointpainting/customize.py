from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if os_info['platform'] == "windows":
        return {'return': 1, 'error': 'Script not supported in windows yet!'}

    if env.get('MLC_ML_MODEL_POINT_PAINTING_PATH', '') != '':
        if not os.path.exists(env['MLC_ML_MODEL_POINT_PAINTING']):
            return {
                'return': 1, 'error': f"Provided model path {env['MLC_ML_MODEL_POINT_PAINTING']} does not exist."}

    if env.get('MLC_ML_MODEL_DPLAB_RESNET50_PATH', '') != '':
        if not os.path.exists(env['MLC_ML_MODEL_DPLAB_RESNET50_PATH']):
            return {
                'return': 1, 'error': f"Provided model path {env['MLC_ML_MODEL_DPLAB_RESNET50_PATH']} does not exist."}

    if env.get('MLC_ML_MODEL_POINT_PAINTING_PATH', '') == '' or env.get(
            'MLC_ML_MODEL_DPLAB_RESNET50_PATH', '') == '':
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = "yes"

    return {'return': 0}


def postprocess(i):

    env = i['env']

    if env.get('MLC_DOWNLOAD_MODE', '') != "dry":
        if env.get('MLC_ML_MODEL_POINT_PAINTING_PATH', '') == '':
            if env['MLC_ML_MODEL_PP_FORMAT'] == "onnx":
                env['MLC_ML_MODEL_POINT_PAINTING_PATH'] = os.path.join(
                    env['MLC_ML_MODEL_POINT_PAINTING_TMP_PATH'], "pp.onnx")
            else:
                env['MLC_ML_MODEL_POINT_PAINTING_PATH'] = os.path.join(
                    env['MLC_ML_MODEL_POINT_PAINTING_TMP_PATH'], "pp_ep36.pth")

        if env.get('MLC_ML_MODEL_DPLAB_RESNET50_PATH', '') == '':
            if env['MLC_ML_MODEL_DPLAB_RESNET50_FORMAT'] == "onnx":
                env['MLC_ML_MODEL_DPLAB_RESNET50_PATH'] = os.path.join(
                    env['MLC_ML_MODEL_POINT_PAINTING_TMP_PATH'], "deeplabv3+.onnx")
            else:
                env['MLC_ML_MODEL_DPLAB_RESNET50_PATH'] = os.path.join(
                    env['MLC_ML_MODEL_POINT_PAINTING_TMP_PATH'],
                    "best_deeplabv3plus_resnet50_waymo_os16.pth")

    return {'return': 0}
