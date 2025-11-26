from mlc import utils
import os
import subprocess


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    exe = 'sde.exe' if os_info['platform'] == 'windows' else 'sde'

    if env.get('MLC_INTEL_SDE_DIR_PATH', '') == '':
        if env.get('MLC_EXTRACT_EXTRACTED_SUBDIR_PATH', '') != '':
            env['MLC_INTEL_SDE_DIR_PATH'] = env['MLC_EXTRACT_EXTRACTED_SUBDIR_PATH']
        elif env.get('MLC_EXTRACT_EXTRACTED_PATH', '') != '':
            env['MLC_INTEL_SDE_DIR_PATH'] = env['MLC_EXTRACT_EXTRACTED_PATH']
        else:
            return {'return': 1, 'error': 'Intel SDE path not found'}

    if 'MLC_INTEL_SDE_BIN_WITH_PATH' not in env:
        if env.get('MLC_INTEL_SDE_DIR_PATH', '') != '':
            sde_path = env['MLC_INTEL_SDE_DIR_PATH']
            if os.path.exists(os.path.join(sde_path, exe)):
                env['MLC_TMP_PATH'] = sde_path

        r = i['automation'].find_artifact({'file_name': exe,
                                           'env': env,
                                           'os_info': os_info,
                                           'default_path_env_key': 'PATH',
                                           'detect_version': True,
                                           'env_path_key': 'MLC_INTEL_SDE_BIN_WITH_PATH',
                                           'run_script_input': i['run_script_input'],
                                           'recursion_spaces': i['recursion_spaces']})
        if r['return'] > 0:
            return r

    return {'return': 0}


def detect_version(i):
    r = i['automation'].parse_version({'match_text': r'Software Development Emulator.\s+Version:\s*([\d.]+)',
                                       'group_number': 1,
                                       'env_key': 'MLC_INTEL_SDE_VERSION',
                                       'which_env': i['env']})
    if r['return'] > 0:
        return r
    version = r['version']

    print(i['recursion_spaces'] + '    Detected version: {}'.format(version))

    return {'return': 0, 'version': version}


def postprocess(i):

    env = i['env']
    state = i['state']

    r = detect_version(i)
    if r['return'] > 0:
        return r

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_INTEL_SDE_BIN_WITH_PATH']
    if '+PATH' not in env:
        env['+PATH'] = []

    os_info = i['os_info']

    return {'return': 0}
