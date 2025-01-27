from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if os_info['platform'] == "windows":
        return {'return': 1, 'error': 'Script not supported in windows yet!'}

    if env.get('MLC_ML_MODEL_DPLAB_RESNET50_PATH', '') == '':
        return {'return': 1, 'error': 'Please provide path to kitti dataset using tag \`--waymo_path\`as automatic download of this dataset is not supported yet.'}

    if os.path.isdir(env['MLC_ML_MODEL_DPLAB_RESNET50_PATH']):
        if env['MLC_ML_MODEL_DPLAB_RESNET50_FORMAT'] == "onnx":
            env['MLC_ML_MODEL_DPLAB_RESNET50_PATH'] = os.path.join(env['MLC_ML_MODEL_DPLAB_RESNET50_PATH'], "deeplabv3+.onnx")
        else:
            env['MLC_ML_MODEL_DPLAB_RESNET50_PATH'] = os.path.join(env['MLC_ML_MODEL_DPLAB_RESNET50_PATH'], "best_deeplabv3plus_resnet50_waymo_os16.pth")
    
    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
