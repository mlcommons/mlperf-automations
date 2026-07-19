from utils import *
from mlc import utils
import os
import subprocess


def preprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    cmake_command = f"""{env['MLC_CMAKE_BIN_WITH_PATH']} {env['MLC_MIMALLOC_SRC_PATH']} """

    if env.get('MLC_MIMALLOC_CONFIG', '') != '':
        cmake_command += f""" {env['MLC_MIMALLOC_CONFIG'].replace("'", "")} """

    env['MLC_MIMALLOC_CMAKE_COMMAND'] = cmake_command

    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    lib_path = os.path.join(os.getcwd(), "lib")

    env['+LD_LIBRARY_PATH'] = [lib_path]
    env['MLC_MIMALLOC_PATH'] = os.path.dirname(lib_path)
    env['MLC_MIMALLOC_LIB_PATH'] = lib_path
    env['MLC_DEPENDENT_CACHED_PATH'] = os.path.join(lib_path, "libmimalloc.so")

    return {'return': 0}
