from mlc import utils
from utils import is_true
import os
import shutil

def _get_hf_cli():
    """Return the available Hugging Face CLI command, preferring 'hf' over the deprecated 'huggingface-cli'."""
    for cmd in ('hf', 'huggingface-cli'):
        if shutil.which(cmd) is not None:
            return cmd
    raise EnvironmentError("Neither 'hf' nor 'huggingface-cli' found on PATH.")

def preprocess(i):
    env = i['env']
    if env.get('MLC_HF_TOKEN', '') != '':
        hf_cli = _get_hf_cli()
        env['MLC_HF_LOGIN_CMD'] = (
            f"git config --global credential.helper store && "
            f"{hf_cli} login --token {env['MLC_HF_TOKEN']} --add-to-git-credential\n"
        )
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
