from mlc import utils
import os


def preprocess(i):
    os_info = i['os_info']

    env = i['env']
    script_path = i['run_script_input']['path']

    env["MLC_SOURCE_FOLDER_PATH"] = script_path
    env['MLC_C_SOURCE_FILES'] = "susan.c"

    if 'MLC_INPUT' not in env:
        env['MLC_INPUT'] = os.path.join(script_path, 'data.pgm')

    if 'MLC_OUTPUT' not in env:
        env['MLC_OUTPUT'] = 'output_image_with_corners.pgm'

    if 'MLC_RUN_DIR' not in env:
        output_path = os.path.join(script_path, "output")
        if output_path != '' and not os.path.isdir(output_path):
            os.makedirs(output_path)

        env['MLC_RUN_DIR'] = output_path

    env['MLC_RUN_SUFFIX'] = env['MLC_INPUT'] + ' ' + env['MLC_OUTPUT'] + ' -c'

    if os_info['platform'] == 'windows':
        env['MLC_BIN_NAME'] = 'image-corner.exe'
    else:
        env['MLC_BIN_NAME'] = 'image-corner'
        env['+ LDCFLAGS'] = ["-lm"]

    return {'return': 0}


def postprocess(i):

    env = i['env']
    logger = i['automation'].logger
    logger.info(env['MLC_OUTPUT'] + " generated in " + env['MLC_RUN_DIR'])

    return {'return': 0}
