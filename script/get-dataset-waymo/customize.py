from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if os_info['platform'] == "windows":
        return {'return': 1, 'error': 'Script not supported in windows yet!'}

    if env.get('MLC_DATASET_WAYMO_PATH', '') == '':
        return {'return': 1, 'error': 'Please provide path to kitti dataset using tag \`--waymo_path\`as automatic download of this dataset is not supported yet.'}

    if not os.path.exists(env['MLC_ML_MODEL_POINT_PILLARS_PATH']):
        return {'return': 1, 'error': f"Path {env['MLC_ML_MODEL_POINT_PILLARS_PATH']} does not exists!"}
    
    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
