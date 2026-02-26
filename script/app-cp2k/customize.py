from utils import *
from mlc import utils
import os
import subprocess


def preprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    if "+LD_LIBRARY_PATH" not in env:
        env["+LD_LIBRARY_PATH"] = []

    if "+LIBRARY_PATH" not in env:
        env["+LIBRARY_PATH"] = []
    
    if "+PATH" not in env:
        env["+PATH"] = []
    
    aocc_lib_path = env['MLC_AOCC_LIB_PATH']
    blas_lib_path = os.path.join(env['MLC_BLAS_INSTALL_PATH'], "lib")
    blas_bin_path = os.path.join(env['MLC_BLAS_INSTALL_PATH'], "bin")

    env['+LD_LIBRARY_PATH'].append(os.path.abspath(aocc_lib_path))
    env['+LIBRARY_PATH'].append(os.path.abspath(aocc_lib_path))

    env['+LD_LIBRARY_PATH'].append(os.path.abspath(blas_lib_path))
    env['+LIBRARY_PATH'].append(os.path.abspath(blas_lib_path))
    #print(env)
    env['+PATH'].append(os.path.abspath(blas_bin_path))
    
    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    lib_path = os.path.join(os.getcwd(), "install", "lib")

    env['MLC_GPERFTOOLS_PATH'] = os.path.dirname(lib_path)
    env['MLC_TCMALLOC_LIB_PATH'] = lib_path
    env['MLC_DEPENDENT_CACHED_PATH'] = os.path.join(lib_path, "libtcmalloc.so")

    return {'return': 0}
