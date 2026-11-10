from mlc import utils
import os


def postprocess(i):
    env = i['env']
    prefix = env.get('MLC_AOCL_FFTW_INSTALL_PATH', '')
    if env.get('MLC_AOCL_FFTW_LIB_PATH') and prefix:
        env['MLC_FFTW3_VENDOR'] = 'aocl'
        env['MLC_FFTW3_LIB_PATH'] = env['MLC_AOCL_FFTW_LIB_PATH']
    else:
        prefix = '/usr'
        env['MLC_FFTW3_VENDOR'] = 'system'
    env['MLC_FFTW3_ROOT'] = prefix
    env['FFTW_ROOT'] = prefix
    env['FFTW_HOME'] = prefix
    return {'return': 0}
