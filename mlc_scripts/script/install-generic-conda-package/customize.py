from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    meta = i['meta']
    automation = i['automation']
    run_script_input = i['run_script_input']

    version_string = env.get('MLC_TMP_PIP_VERSION_STRING', '').strip()
    package_name = env['MLC_CONDA_PKG_NAME'].strip()

    install_cmd = env['MLC_CONDA_BIN_WITH_PATH'] + " install -y "
    if env.get('MLC_CONDA_PKG_SRC', '') != '':
        install_cmd += " -c " + env['MLC_CONDA_PKG_SRC'] + " "

    install_cmd += package_name
    install_cmd += version_string

    env['MLC_CONDA_PKG_INSTALL_CMD'] = install_cmd

    return {'return': 0}


def detect_version(i):

    logger = i['automation'].logger

    # TBD
    logger.info(
        i['recursion_spaces'] +
        '      Detected version: {}'.format(version))

    return {'return': 0, 'version': version}


def postprocess(i):

    env = i['env']
    version = env.get('MLC_VERSION', '')

    if env['MLC_CONDA_PKG_NAME'] == "python":
        env['MLC_PYTHON_BIN_WITH_PATH'] = os.path.join(
            os.path.dirname(env['MLC_CONDA_BIN_WITH_PATH']), "python")

    return {'return': 0, 'version': version}
