from mlc import utils
import os


def preprocess(i):
    os_info = i['os_info']
    env = i['env']

    logger = i['automation'].logger

    machine = env.get('MLC_HOST_OS_MACHINE', '')
    if machine == '':
        machine = 'x86_64'
    if machine == 'x86_64':
        machine = 'x64'

    hostos = env['MLC_HOST_OS_TYPE']

    ext = '.tgz'

    if hostos == 'darwin':
        hostos = 'osx'
    elif hostos == 'windows':
        hostos = 'win'
        ext = '.zip'

    device = env.get('MLC_ONNXRUNTIME_DEVICE', '')
    if device != '':
        machine += '-' + device

    version = env['MLC_VERSION']

    FOLDER = 'onnxruntime-{}-{}-{}'.format(hostos, machine, version)

    FILENAME = FOLDER + ext

    URL = 'https://github.com/microsoft/onnxruntime/releases/download/v{}/{}'.format(
        version, FILENAME)

    logger.info('')
    logger.info('Downloading from {}'.format(URL))
    logger.info('')

    env['FOLDER'] = FOLDER
    env['FILENAME'] = FILENAME
    env['URL'] = URL

    return {'return': 0}


def postprocess(i):

    env = i['env']

    hostos = env['MLC_HOST_OS_TYPE']

    install_folder = env['MLC_TMP_INSTALL_FOLDER']

    for key in ['+C_INCLUDE_PATH', '+CPLUS_INCLUDE_PATH',
                '+LD_LIBRARY_PATH', '+DYLD_FALLBACK_LIBRARY_PATH']:
        #        20221024: we save and restore env in the main script and can clean env here for determinism
        #        if key not in env:
        env[key] = []

    include_path = os.path.join(
        os.getcwd(),
        'install',
        install_folder,
        'include')

    env['+C_INCLUDE_PATH'].append(include_path)
    env['+CPLUS_INCLUDE_PATH'].append(include_path)

    lib_path = os.path.join(os.getcwd(), 'install', install_folder, 'lib')

    env['+LD_LIBRARY_PATH'].append(lib_path)
    env['+DYLD_FALLBACK_LIBRARY_PATH'].append(lib_path)

    if hostos == 'windows':
        # For dynamic libraries
        env['+PATH'] = [lib_path]

    env['MLC_ONNXRUNTIME_LIB_PATH'] = lib_path
    env['MLC_ONNXRUNTIME_INCLUDE_PATH'] = include_path

    return {'return': 0}
