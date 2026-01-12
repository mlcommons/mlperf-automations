from mlc import utils
import os
from utils import *


def ask_url_acceptance(url):
    print(f"Please take a moment to read the EULA at this URL:\n{url}")
    print("\nDo you accept the terms of this EULA? [yes/no]")

    while True:
        response = input().lower()
        if response in ["yes", "y"]:
            print("You have accepted the EULA.")
            return True
        elif response in ["no", "n"]:
            print("You have not accepted the EULA.")
            return False
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")


def predeps(i):
    os_info = i['os_info']

    env = i['env']
    if env.get('MLC_UPROF_TAR_FILE_PATH', '') != '':
        env['MLC_UPROF_NEEDS_TAR'] = 'yes'

    elif is_true(env.get('MLC_UPROF_DOWNLOAD')) and not is_true(env.get('MLC_UPROF_ACCEPT_EULA')):
        url = "https://www.amd.com/en/developer/uprof/uprof-eula/uprof-5-1-eula.html?filename=AMDuProf_Linux_x64_5.1.701.tar.bz2"
        accepted = ask_url_acceptance(url)
        if accepted:
            env['MLC_UPROF_ACCEPT_EULA'] = 'yes'

    return {'return': 0}


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    exe = 'AMDuProfSys.exe' if os_info['platform'] == 'windows' else 'AMDuProfSys'

    if 'MLC_UPROF_BIN_WITH_PATH' not in env:

        if env.get('MLC_UPROF_DIR_PATH', '') != '':
            uprof_path = env['MLC_UPROF_DIR_PATH']
            if os.path.exists(os.path.join(uprof_path, 'bin', exe)):
                env['MLC_TMP_PATH'] = os.path.join(uprof_path, 'bin')

        r = i['automation'].find_artifact({'file_name': exe,
                                           'env': env,
                                           'os_info': os_info,
                                           'default_path_env_key': 'PATH',
                                           'detect_version': True,
                                           'env_path_key': 'MLC_UPROF_BIN_WITH_PATH',
                                           'run_script_input': i['run_script_input'],
                                           'recursion_spaces': i['recursion_spaces']})
        if r['return'] > 0:
            return r

    return {'return': 0}


def detect_version(i):
    logger = i['automation'].logger

    r = i['automation'].parse_version({'match_text': r'AMDuProfSys version\s+([\d.]+)',
                                       'group_number': 1,
                                       'env_key': 'MLC_UPROF_VERSION',
                                       'which_env': i['env']})
    if r['return'] > 0:
        return r
    version = r['version']

    logger.info(
        f"{i['recursion_spaces']}    Detected version: {version}")

    return {'return': 0, 'version': version}


def postprocess(i):

    env = i['env']
    r = detect_version(i)
    if r['return'] > 0:
        return r

    version = r['version']

    found_file_path = env['MLC_UPROF_BIN_WITH_PATH']

    found_path = os.path.dirname(found_file_path)

    env['MLC_UPROF_INSTALLED_PATH'] = os.path.dirname(found_path)

    env['+PATH'] = [found_path]

    return {'return': 0, 'version': version}
