from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if is_true(env.get('MLC_ML_MODEL_LOCAL', '')):
        ml_model = env.get('MLC_ML_MODEL_FILENAME', '')
        if ml_model == '':
            return {'return': 1, 'error': '_local.{model name.pth} is not specified'}

        if not os.path.isabs(ml_model):
            ml_model = os.path.join(
                env.get(
                    'MLC_TMP_CURRENT_PATH',
                    ''),
                ml_model)

        if not os.path.isfile(ml_model):
            return {'return': 1,
                    'error': 'ML model {} is not found'.format(ml_model)}

        env['MLC_ML_MODEL_FILE_WITH_PATH'] = ml_model
    # handle download from mlcommons gdrive
    elif env.get('MLC_DOWNLOAD_SRC', '') == "mlcommons":
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = 'yes'

    return {'return': 0}


def postprocess(i):

    env = i['env']

    if env.get('MLC_ML_MODEL_FILE_WITH_PATH', '') == '':
        if env.get('MLC_ML_MODEL_SSD_PATH', '') == '':
            env['MLC_ML_MODEL_FILE_WITH_PATH'] = 'model-weights-skipped'
        else:
            env['MLC_ML_MODEL_SSD_PATH'] = os.path.join(
                env['MLC_ML_MODEL_SSD_PATH'], env['MLC_ML_MODEL_FILENAME'])
            env['MLC_ML_MODEL_FILE_WITH_PATH'] = env['MLC_ML_MODEL_SSD_PATH']

    env['MLC_ML_MODEL_FILE'] = os.path.basename(
        env['MLC_ML_MODEL_FILE_WITH_PATH'])

    if env.get('MLC_ABTF_SSD_PYTORCH', '') == '':
        env['MLC_ABTF_SSD_PYTORCH'] = 'model-code-skipped'

    env['MLC_ML_MODEL_CODE_WITH_PATH'] = env['MLC_ABTF_SSD_PYTORCH']

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_ML_MODEL_FILE_WITH_PATH']

    return {'return': 0}
