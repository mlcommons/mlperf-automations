from mlc import utils
import os
from utils import *


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    logger = i['automation'].logger

    if os_info['platform'] == 'windows':
        return {
            'return': 1,
            'error': 'Apptainer image building is not supported on Windows.'}

    def_file_path = env.get('MLC_APPTAINERFILE_WITH_PATH', '')
    if def_file_path != '' and os.path.exists(def_file_path):
        build_def_file = False
        env['MLC_BUILD_APPTAINERFILE'] = "no"
    else:
        build_def_file = True
        env['MLC_BUILD_APPTAINERFILE'] = "yes"

    # Determine image name
    image_name = env.get('MLC_APPTAINER_IMAGE_NAME', '')
    if image_name == '':
        image_name = "mlc-script-" + \
            env.get('MLC_APPTAINER_RUN_SCRIPT_TAGS', 'default').replace(
                ',', '-').replace('_', '-')
    env['MLC_APPTAINER_IMAGE_NAME'] = image_name.lower()

    image_tag = env.get('MLC_APPTAINER_IMAGE_TAG', 'latest')
    env['MLC_APPTAINER_IMAGE_TAG'] = image_tag

    # SIF output path
    sif_name = f"{env['MLC_APPTAINER_IMAGE_NAME']}_{image_tag}.sif"
    sif_path = os.path.join(os.getcwd(), sif_name)
    env['MLC_APPTAINER_SIF_PATH'] = sif_path

    # Build command options
    build_opts = ''

    if is_true(env.get('MLC_APPTAINER_FAKEROOT', '')):
        build_opts += ' --fakeroot'

    if is_true(env.get('MLC_APPTAINER_BUILD_SANDBOX', '')):
        # Build sandbox instead of SIF
        sandbox_path = sif_path.replace('.sif', '_sandbox')
        env['MLC_APPTAINER_SIF_PATH'] = sandbox_path
        build_opts += ' --sandbox'

    if is_true(env.get('MLC_APPTAINER_BUILD_FORCE', '')):
        build_opts += ' --force'

    if is_true(env.get('MLC_APPTAINER_BUILD_NOTEST', '')):
        build_opts += ' --notest'

    if build_def_file:
        def_file_ref = "${MLC_APPTAINERFILE_WITH_PATH}"
    else:
        def_file_ref = def_file_path

    output_path = env['MLC_APPTAINER_SIF_PATH']

    CMD = f"apptainer build{build_opts} {output_path} {def_file_ref}"

    logger.info('')
    logger.info(f'Apptainer build command:')
    logger.info(f'  {CMD}')
    logger.info('')

    env['MLC_APPTAINER_BUILD_CMD'] = CMD

    # Save build script
    with open('apptainer-build.sh', 'w') as f:
        f.write('#!/bin/bash\n')
        f.write(CMD + '\n')

    return {'return': 0}


def postprocess(i):

    env = i['env']
    logger = i['automation'].logger

    sif_path = env.get('MLC_APPTAINER_SIF_PATH', '')
    if sif_path and os.path.exists(sif_path):
        logger.info(f'Apptainer image built: {sif_path}')
    else:
        logger.info(f'Apptainer image expected at: {sif_path}')

    return {'return': 0}
