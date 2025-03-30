from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if os_info['platform'] == "windows":
        return {'return': 1, 'error': 'Script not supported in windows yet!'}

    if env.get('MLC_DATASET_WAYMO_CALIBRATION_PATH', '') != '':
        if not os.path.exists(env['MLC_DATASET_WAYMO_CALIBRATION_PATH']):
            return {
                'return': 1, 'error': f"Path {env['MLC_DATASET_WAYMO_CALIBRATION_PATH']} does not exists!"}
    else:
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = "yes"

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
