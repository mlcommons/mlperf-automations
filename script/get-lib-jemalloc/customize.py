from mlc import utils
import os
import subprocess


def preprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    lib_path = os.path.join(os.getcwd(), "obj", "lib")

    env['+LD_LIBRARY_PATH'] = lib_path
    env['MLC_JEMALLOC_PATH'] = os.path.dirname(lib_path)
    env['MLC_JEMALLOC_LIB_PATH'] = lib_path
    env['MLC_DEPENDENT_CACHED_PATH'] = os.path.join(lib_path, "libjemalloc.so")

    return {'return': 0}
