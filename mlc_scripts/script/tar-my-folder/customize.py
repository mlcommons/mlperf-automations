from mlc import utils
import os
import subprocess
from os.path import exists


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    logger = i['automation'].logger
    input_dir = env.get("MLC_TAR_INPUT_DIR", "")
    if input_dir == "":
        return {'return': 1, 'error': 'Please set MLC_TAR_INPUT_DIR'}
    output_dir = env.get("MLC_TAR_OUTPUT_DIR", "")
    if output_dir == "":
        output_dir = os.getcwd()
    output_file = env.get("MLC_TAR_OUTFILE", "")
    input_dirname = os.path.basename(input_dir)
    if output_file == "":
        output_file = input_dirname + ".tar.gz"
    env['MLC_TAR_OUTFILE'] = output_file
    from pathlib import Path
    input_path = Path(input_dir)
    sub_folders_to_include = env.get('MLC_TAR_SUB_FOLDERS_TO_INCLUDE', '')
    if sub_folders_to_include != '':
        cd_dir = input_path.absolute()
        r = sub_folders_to_include.split(",")
        v_sub_folders = []
        for sub_folder in r:
            f = sub_folder.strip()
            if os.path.exists(os.path.join(input_path, f)):
                v_sub_folders.append(f)
        CMD = 'tar --directory ' + \
            str(cd_dir) + ' -czf ' + os.path.join(output_dir,
                                                  output_file) + ' ' + ' '.join(v_sub_folders)
    else:
        cd_dir = input_path.parent.absolute()
        CMD = 'tar --directory ' + \
            str(cd_dir) + ' -czf ' + os.path.join(output_dir,
                                                  output_file) + ' ' + input_dirname

    logger.info(f"{CMD}")
    ret = os.system(CMD)
    logger.info(f"Tar file {os.path.join(output_dir, output_file)} created")

    return {'return': ret}
