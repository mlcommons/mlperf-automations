from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    logger = automation.logger

    quiet = is_true(env.get('MLC_QUIET', False))

    ############################################################
    cur_dir = os.getcwd()

    name = env.get('MLC_NAME', '')
    if name == '':
        artifacts = i.get('input', {}).get('artifacts', [])
        if len(artifacts) > 0:
            name = artifacts[0]
    if name == '':
        name = 'default'

    if os_info['platform'] == 'windows':
        activate_script = os.path.join('Scripts', 'activate.bat')
    else:
        activate_script = os.path.join('bin', 'activate')

    activate_script2 = os.path.join(name, activate_script)

    if not os.path.isfile(activate_script2):
        force_python_path = env.get('MLC_SET_VENV_PYTHON', '')

        if force_python_path != '' and not os.path.isfile(force_python_path):
            return {'return': 1, 'error': 'python executable not found: {}'.format(
                force_python_path)}

        if os_info['platform'] == 'windows':
            python_path = 'python.exe' if force_python_path == '' else force_python_path
            create_dir = ' & md {}\\work'
        else:
            python_path = 'python3' if force_python_path == '' else force_python_path
            create_dir = ' ; mkdir {}/work'

        cmd = python_path + ' -m venv ' + name + create_dir.format(name)

        logger.info(
            '====================================================================')

        logger.info('Creating venv: "{}" ...'.format(cmd))
        os.system(cmd)

    if os.path.isfile(activate_script2):
        script_file = 'venv-' + name
        if os_info['platform'] == 'windows':
            script_file += '.bat'
            xcmd = script_file
        else:
            script_file += '.sh'
            xcmd = 'source ' + script_file

        if not os.path.isfile(script_file):

            work_dir = os.path.join(name, 'work')
            if not os.path.isdir(work_dir):
                os.makedirs(work_dir)

            if os_info['platform'] == 'windows':
                shell = os.environ.get('MLC_SET_VENV_SHELL', '')
                if shell == '':
                    shell = env.get('MLC_SET_VENV_SHELL', '')
                if shell != '':
                    shell = shell.replace('MLC_SET_VENV_WORK', 'work')
                if shell == '':
                    shell = 'cmd'
                cmd = 'cd {} & call {} & set MLC_REPOS=%CD%\\{}\\CM & {}\n'.format(
                    name, activate_script, name, shell)
            else:
                cmd = '#!/bin/bash\n\ncd {} ; source {} ; export MLC_REPOS=$PWD/CM ; cd work\n'.format(
                    name, activate_script)

            with open(script_file, 'w') as f:
                f.write(cmd)

        logger.info(
            '====================================================================')
        logger.info('Please run the following command:')
        logger.info('')
        logger.info(f"{xcmd}")
        logger.info(
            '====================================================================')

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
