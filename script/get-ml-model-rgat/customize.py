from cmind import utils
import os


def preprocess(i):

    os_info = i['os_info']
    env = i['env']

    download_dir = env.get('CM_OUTDIRNAME', '')

    path = env.get('RGAT_CHECKPOINT_PATH', '').strip()

    if path == '' or not os.path.exists(path):
        if download_dir != '' and os.path.exists(
                os.path.join(download_dir, "RGAT", "RGAT.pt")):
            env['RGAT_CHECKPOINT_PATH'] = os.path.join(
                download_dir, "RGAT", "RGAT.pt")
        else:
            env['CM_TMP_REQUIRE_DOWNLOAD'] = 'yes'

    return {'return': 0}


def postprocess(i):

    env = i['env']

    if env.get('RGAT_CHECKPOINT_PATH', '') == '':
        env['RGAT_CHECKPOINT_PATH'] = os.path.join(
            env['RGAT_DIR_PATH'], "RGAT.pt")

    if env.get('CM_ML_MODEL_RGAT_CHECKPOINT_PATH', '') == '':
        env['CM_ML_MODEL_RGAT_CHECKPOINT_PATH'] = env['RGAT_CHECKPOINT_PATH']

    if env.get('CM_ML_MODEL_PATH', '') == '':
        env['CM_ML_MODEL_PATH'] = env['CM_ML_MODEL_RGAT_CHECKPOINT_PATH']

    env['RGAT_CHECKPOINT_PATH'] = env['CM_ML_MODEL_RGAT_CHECKPOINT_PATH']
    env['CM_GET_DEPENDENT_CACHED_PATH'] = env['CM_ML_MODEL_RGAT_CHECKPOINT_PATH']

    return {'return': 0}
