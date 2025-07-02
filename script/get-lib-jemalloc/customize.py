from mlc import utils
import os
import subprocess


def preprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    configure_command = f"""{os.path.join(env['MLC_JEMALLOC_SRC_PATH'], 'configure')} --enable-autogen"""
    if env.get('MLC_JEMALLOC_LG_QUANTUM', '') != '':
        configure_command += f""" --with-lg-quantum={env['MLC_JEMALLOC_LG_QUANTUM']} """
    if env.get('MLC_JEMALLOC_LG_PAGE', '') != '':
        configure_command += f""" --with-lg-page={env['MLC_JEMALLOC_LG_PAGE']} """
    if env.get('MLC_JEMALLOC_CONFIG', '') != '':
        configure_command += f""" {env['MLC_JEMALLOC_CONFIG'].replace("'", "")} """

    env['MLC_JEMALLOC_CONFIGURE_COMMAND'] = configure_command

    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    lib_path = os.path.join(os.getcwd(), "obj", "lib")

    env['+LD_LIBRARY_PATH'] = [lib_path]
    env['MLC_JEMALLOC_PATH'] = os.path.dirname(lib_path)
    env['MLC_JEMALLOC_LIB_PATH'] = lib_path
    env['MLC_DEPENDENT_CACHED_PATH'] = os.path.join(lib_path, "libjemalloc.so")

    return {'return': 0}
