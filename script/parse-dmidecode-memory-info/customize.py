from mlc import utils
import os
import subprocess


def preprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    input_file = env.get('MLC_MEMINFO_FILE', '')

    if input_file == '':
        return {'return': 1, 'error': 'Please provide a valid input file containing the meminfo output from dmidecode -t memory'}

    output_file = env.get('MLC_MEMINFO_OUTFILE', os.path.join(os.getcwd(), 'meminfo.txt'))

    env['MLC_MEMINFO_OUTFILE'] = output_file

    env['MLC_RUN_CMD'] = f"""{env['MLC_PYTHON_BIN_WITH_PATH']} {os.path.join(env['MLC_TMP_CURRENT_SCRIPT_PATH'], "get_memory_info.py")} {input_file} {output_file}""" 
    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    return {'return': 0}
