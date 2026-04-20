from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for Quantum ESPRESSO builds'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    src_path = env.get('MLC_QE_SRC_PATH', '')
    install_dir = os.path.join(src_path, 'install')
    bin_dir = os.path.join(install_dir, 'bin')

    pw_bin = os.path.join(bin_dir, 'pw.x')
    if not os.path.isfile(pw_bin):
        # Try build directory
        build_bin = os.path.join(src_path, 'build', 'bin')
        pw_bin = os.path.join(build_bin, 'pw.x')
        if not os.path.isfile(pw_bin):
            return {'return': 1, 'error': f'Quantum ESPRESSO binary (pw.x) not found in {bin_dir} or {build_bin}'}
        bin_dir = build_bin

    env['MLC_QE_BIN_PATH'] = bin_dir
    env['MLC_QE_INSTALL_PATH'] = install_dir
    env['+PATH'] = [bin_dir]
    env['+LD_LIBRARY_PATH'] = [os.path.join(install_dir, 'lib')]

    return {'return': 0}
