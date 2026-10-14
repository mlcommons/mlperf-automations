from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for MILC builds'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    src_path = env.get('MLC_MILC_SRC_PATH', '')
    compiler_tag = env.get('MLC_COMPILER_FAMILY', '') or 'default'
    bin_dir = os.path.join(src_path, 'install-' + compiler_tag, 'bin')

    binary = os.path.join(bin_dir, 'su3_rmd')
    if not os.path.isfile(binary):
        return {'return': 1,
                'error': f'MILC binary (su3_rmd) not found in {bin_dir}'}

    env['MLC_MILC_INSTALL_PATH'] = src_path
    env['MLC_MILC_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]

    return {'return': 0}
