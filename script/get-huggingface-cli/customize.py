from mlc import utils
from utils import is_true
import os


def preprocess(i):
    env = i['env']
    if env.get('MLC_HF_TOKEN', '') != '':
        env['MLC_HF_LOGIN_CMD'] = f"""git config --global credential.helper store && huggingface-cli login --token {env['MLC_HF_TOKEN']} --add-to-git-credential
"""
    elif is_true(str(env.get('MLC_HF_DO_LOGIN'))):
        env['MLC_HF_LOGIN_CMD'] = f"""git config --global credential.helper store && huggingface-cli login
"""
    return {'return': 0}


def postprocess(i):
    env = i['env']
    logger = i['automation'].logger
    r = i['automation'].parse_version({'match_text': r'huggingface_hub\s*version:\s*([\d.]+)',
                                       'group_number': 1,
                                       'env_key': 'MLC_GITHUBCLI_VERSION',
                                       'which_env': i['env']})
    if r['return'] > 0:
        return r

    version = r['version']

    logger.info(
        i['recursion_spaces'] +
        '    Detected version: {}'.format(version))

    return {'return': 0, 'version': version}
