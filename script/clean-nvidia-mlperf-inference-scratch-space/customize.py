from mlc import utils
import os
from utils import is_true


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    clean_cmd = ''
    cache_rm_tags = ''
    extra_cache_rm_tags = env.get('MLC_CLEAN_EXTRA_CACHE_RM_TAGS', '').strip()

    extra_tags = "," + extra_cache_rm_tags if extra_cache_rm_tags != '' else ''
    model = env.get('MLC_MODEL', '')
    artifact_name = env.get('MLC_CLEAN_ARTIFACT_NAME', '')
    if artifact_name == 'downloaded_model':
        artifact_name = 'models'

    model_aliases = {
        'stable-diffusion-xl': 'sdxl',
        '3d-unet-99': '3d-unet',
        '3d-unet-99.9': '3d-unet',
        'bert-99': 'bert',
        'bert-99.9': 'bert',
        'dlrm-v2-99': 'dlrm-v2',
        'dlrm-v2-99.9': 'dlrm-v2',
        'gptj-99': 'gptj',
        'gptj-99.9': 'gptj',
        'llama2-70b-99': 'llama2-70b',
        'llama2-70b-99.9': 'llama2-70b'
    }
    model_name = model_aliases.get(model, model)
    if model_name == '':
        return {'return': 1, 'error': 'Please select a variation specifying the model to clean'}

    model_artifacts = {
        '3d-unet': {
            'downloaded_data': [os.path.join('data', 'KiTS19')],
            'preprocessed_data': [os.path.join('preprocessed_data', 'KiTS19')],
            'models': [os.path.join('models', '3d-unet-kits19')]
        },
        'bert': {
            'downloaded_data': [os.path.join('data', 'squad')],
            'preprocessed_data': [os.path.join('preprocessed_data', 'squad')],
            'models': [os.path.join('models', 'bert')]
        },
        'dlrm-v2': {
            'downloaded_data': [os.path.join('data', 'criteo')],
            'preprocessed_data': [os.path.join('preprocessed_data', 'criteo')],
            'models': [os.path.join('models', 'dlrm'), os.path.join('models', 'dlrm-v2')]
        },
        'gptj': {
            'downloaded_data': [os.path.join('data', 'cnn-daily-mail')],
            'preprocessed_data': [os.path.join('preprocessed_data', 'cnn-daily-mail')],
            'models': [os.path.join('models', 'GPTJ-6B')]
        },
        'llama2-70b': {
            'downloaded_data': [os.path.join('data', 'llama2-70b')],
            'preprocessed_data': [os.path.join('preprocessed_data', 'open_orca')],
            'models': [os.path.join('models', 'Llama2')]
        },
        'resnet50': {
            'downloaded_data': [os.path.join('data', 'imagenet')],
            'preprocessed_data': [os.path.join('preprocessed_data', 'imagenet')],
            'models': [os.path.join('models', 'ResNet50')]
        },
        'retinanet': {
            'downloaded_data': [os.path.join('data', 'open-images-v6-mlperf')],
            'preprocessed_data': [os.path.join('preprocessed_data', 'open-images-v6-mlperf')],
            'models': [os.path.join('models', 'retinanet-resnext50-32x4d')]
        },
        'rnnt': {
            'downloaded_data': [os.path.join('data', 'LibriSpeech')],
            'preprocessed_data': [
                os.path.join('preprocessed_data', 'rnnt_dev_clean_500_raw'),
                os.path.join('preprocessed_data', 'rnnt_train_clean_512_wav')
            ],
            'models': [os.path.join('models', 'rnn-t')]
        },
        'sdxl': {
            'downloaded_data': [os.path.join('data', 'coco', 'SDXL')],
            'preprocessed_data': [os.path.join('preprocessed_data', 'coco2014-tokenized-sdxl')],
            'models': [os.path.join('models', 'SDXL')]
        }
    }

    clean_paths = model_artifacts.get(model_name, {}).get(artifact_name, [])
    if clean_paths:
        full_clean_paths = [os.path.join(env['MLC_NVIDIA_MLPERF_SCRATCH_PATH'], p) for p in clean_paths]
        clean_cmd = " && ".join([f"rm -rf {p}" for p in full_clean_paths])

    cache_action_tag = ''
    if artifact_name in ['downloaded_data', 'preprocessed_data']:
        cache_action_tag = '_preprocess_data'
    elif artifact_name == 'models':
        cache_action_tag = '_download_model'

    if cache_action_tag:
        cache_model_name = 'sdxl' if model == 'stable-diffusion-xl' else model
        cache_rm_tags = f"nvidia-harness,{cache_action_tag},_{cache_model_name}"

    cache_rm_tags = cache_rm_tags + extra_tags
    mlc_cache = i['automation'].cache_action

    if cache_rm_tags:
        r = mlc_cache.access({'action': 'rm', 'target': 'cache',
                              'tags': cache_rm_tags, 'f': True})
        utils.logger.info(r)
        # Check if return code is 0 (success)
        # currently, the warning code is not being checked as the possibility
        # arises only for missing cache entry
        if r['return'] != 0:
            return r
        if r['return'] == 0:  # cache entry found
            if clean_cmd != '':
                env['MLC_RUN_CMD'] = clean_cmd
    else:
        if clean_cmd != '':
            env['MLC_RUN_CMD'] = clean_cmd

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
