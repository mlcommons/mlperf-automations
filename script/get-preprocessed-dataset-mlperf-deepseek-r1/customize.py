from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if os_info['platform'] == "windows":
        return {'return': 1, 'error': 'Script not supported in windows yet!'}

    if env.get('MLC_PREPROCESSED_DATASET_DEEPSEEK_R1_PATH', '') != '':
        if not os.path.exists(
                env['MLC_PREPROCESSED_DATASET_DEEPSEEK_R1_PATH']):
            return {
                'return': 1, 'error': f"Path {env['MLC_PREPROCESSED_DATASET_DEEPSEEK_R1_PATH']} does not exists!"}
    else:
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = "yes"

    return {'return': 0}


def postprocess(i):

    env = i['env']

    if env.get('MLC_DOWNLOAD_MODE', '') != "dry":
        if env.get('MLC_PREPROCESSED_DATASET_TYPE', '') == 'validation':
            env['MLC_PREPROCESSED_DATASET_DEEPSEEK_R1_VALIDATION_PATH'] = env['MLC_PREPROCESSED_DATASET_DEEPSEEK_R1_PATH']
        elif env.get('MLC_PREPROCESSED_DATASET_TYPE', '') == 'calibration':
            env['MLC_PREPROCESSED_DATASET_DEEPSEEK_R1_CALIBRATION_PATH'] = env['MLC_PREPROCESSED_DATASET_DEEPSEEK_R1_PATH']

    return {'return': 0}
