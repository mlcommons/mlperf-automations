from mlc import utils
import os


def preprocess(i):
    os_info = i['os_info']

    q = '"' if os_info['platform'] == 'windows' else "'"
    logger = i['automation'].logger
    env = i['env']
    CPPFLAGS = env.get('+ CPPFLAGS', [])
    env['MLC_C_COMPILER_FLAGS'] = " ".join(env.get('+ CFLAGS', []) + CPPFLAGS)
    env['MLC_CXX_COMPILER_FLAGS'] = " ".join(
        env.get('+ CXXFLAGS', []) + CPPFLAGS)
    env['MLC_F_COMPILER_FLAGS'] = " ".join(env.get('+ FFLAGS', []))

    CPATH = env.get('+CPATH', [])
    env['MLC_C_INCLUDE_PATH'] = " ".join(
        [f"""-I{q}{path}{q}""" for path in env.get('+C_INCLUDE_PATH', []) + CPATH])

    env['MLC_C_INCLUDE_PATH'] = " ".join(
        f"""-I{q}{path}{q}""" for path in env.get('+C_INCLUDE_PATH', []) + CPATH)

    env['MLC_CPLUS_INCLUDE_PATH'] = " ".join(
        f"""-I{q}{path}{q}""" for path in env.get('+CPLUS_INCLUDE_PATH', []) + CPATH)

    env['MLC_F_INCLUDE_PATH'] = " ".join(
        f"""-I{q}{path}{q}""" for path in env.get('+F_INCLUDE_PATH', []) + CPATH)

    # If windows, need to extend it more ...
    if os_info['platform'] == 'windows' and env.get(
            'MLC_COMPILER_FAMILY', '') != 'LLVM':
        logger.warning(
            "Compile-program script should be extended to support flags for non-LLVM compilers on Windows")
        return {'return': 0}

    LDFLAGS = env.get('+ LDFLAGS', [])

    env['MLC_C_LINKER_FLAGS'] = " ".join(env.get('+ LDCFLAGS', []) + LDFLAGS)
    env['MLC_CXX_LINKER_FLAGS'] = " ".join(
        env.get('+ LDCXXFLAGS', []) + LDFLAGS)
    env['MLC_F_LINKER_FLAGS'] = " ".join(env.get('+ LDFFLAGS', []) + LDFLAGS)

    if env.get('MLC_LINKER_LANG', 'C') == "C":
        env['MLC_LINKER_BIN'] = env['MLC_C_COMPILER_BIN']
        env['MLC_LINKER_WITH_PATH'] = env['MLC_C_COMPILER_WITH_PATH']
        env['MLC_LINKER_COMPILE_FLAGS'] = env['MLC_C_COMPILER_FLAGS']
        env['MLC_LINKER_FLAGS'] = env['MLC_C_LINKER_FLAGS']

    elif env.get('MLC_LINKER_LANG', 'C') == "CXX":
        env['MLC_LINKER_BIN'] = env['MLC_CXX_COMPILER_BIN']
        env['MLC_LINKER_WITH_PATH'] = env['MLC_CXX_COMPILER_WITH_PATH']
        env['MLC_LINKER_COMPILE_FLAGS'] = env['MLC_CXX_COMPILER_FLAGS']
        env['MLC_LINKER_FLAGS'] = env['MLC_CXX_LINKER_FLAGS']

    elif env.get('MLC_LINKER_LANG', 'C') == "F":
        env['MLC_LINKER_BIN'] = env['MLC_F_COMPILER_BIN']
        env['MLC_LINKER_WITH_PATH'] = env['MLC_F_COMPILER_WITH_PATH']
        env['MLC_LINKER_COMPILE_FLAGS'] = env['MLC_F_COMPILER_FLAGS']
        env['MLC_LINKER_FLAGS'] = env['MLC_F_LINKER_FLAGS']

    env['MLC_LD_LIBRARY_PATH'] = " ".join(
        f"""-L{q}{path}{q}""" for path in env.get('+LD_LIBRARY_PATH', []))

    env['MLC_SOURCE_FOLDER_PATH'] = env['MLC_SOURCE_FOLDER_PATH'] if 'MLC_SOURCE_FOLDER_PATH' in env else env[
        'MLC_TMP_CURRENT_SCRIPT_PATH'] if 'MLC_TMP_CURRENT_SCRIPT_PATH' in env else ''

    return {'return': 0}


def postprocess(i):

    return {'return': 0}
