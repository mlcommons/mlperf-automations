from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for WRF builds'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    src_path = env.get('MLC_WRF_SRC_PATH', '')
    main_dir = os.path.join(src_path, 'main')
    wrf_exe = os.path.join(main_dir, 'wrf.exe')

    if not os.path.isfile(wrf_exe):
        return {'return': 1, 'error': f'WRF binary not found at {wrf_exe}'}

    env['MLC_WRF_BIN_PATH'] = main_dir
    env['MLC_WRF_INSTALL_PATH'] = src_path
    env['+PATH'] = [main_dir]

    return {'return': 0}
