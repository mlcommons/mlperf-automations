from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    recursion_spaces = i['recursion_spaces']

    file_name = 'openssl'
    if 'MLC_OPENSSL_BIN_WITH_PATH' not in env:
        r = i['automation'].find_artifact({'file_name': file_name,
                                           'env': env,
                                           'os_info': os_info,
                                           'default_path_env_key': 'PATH',
                                           'detect_version': True,
                                           'env_path_key': 'MLC_OPENSSL_BIN_WITH_PATH',
                                           'run_script_input': i['run_script_input'],
                                           'recursion_spaces': i['recursion_spaces']})
        if r['return'] > 0:
            if r['return'] == 16 and os_info['platform'] != 'windows':
                env['MLC_REQUIRE_INSTALL'] = "yes"
                return {'return': 0}
            return r

    return {'return': 0}


def detect_version(i):
    r = i['automation'].parse_version({'match_text': r'OpenSSL\s*([\d.]+)',
                                       'group_number': 1,
                                       'env_key': 'MLC_OPENSSL_VERSION',
                                       'which_env': i['env']})
    if r['return'] > 0:
        return r

    version = r['version']

    logger = i['automation'].logger
    logger.info(
        i['recursion_spaces'] +
        '      Detected version: {}'.format(version))
    return {'return': 0, 'version': version}


def postprocess(i):

    env = i['env']
    r = detect_version(i)
    if r['return'] > 0:
        return r
    version = r['version']
    found_file_path = env['MLC_OPENSSL_BIN_WITH_PATH']

    found_path = os.path.dirname(found_file_path)
    env['MLC_OPENSSL_INSTALLED_PATH'] = found_path

    # Save tags that can be used to specialize further dependencies (such as
    # python packages)
    tags = 'version-' + version

    return {'return': 0, 'version': version}
