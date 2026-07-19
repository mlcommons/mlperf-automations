from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    automation = i['automation']

    cm = automation.action_object

    path = os.path.dirname(env['MLC_ML_MODEL_FILE_WITH_PATH'])

    if env.get("MLC_DAE_EXTRACT_DOWNLOADED", " ") != " ":
        env['MLC_ML_MODEL_PATH'] = os.path.join(path, env['MLC_ML_MODEL_FILE'])
        env['MLC_ML_MODEL_FILE_WITH_PATH'] = env['MLC_ML_MODEL_PATH']
    else:
        env['MLC_ML_MODEL_PATH'] = path

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_ML_MODEL_PATH']

    return {'return': 0}
