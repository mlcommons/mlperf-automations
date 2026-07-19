from mlc import utils
import os
import subprocess


def preprocess(i):

    os_info = i['os_info']
    env = i['env']

    venv_name = env.get('MLC_MLPERF_ENDPOINTS_CLI_VENV_NAME',
                        'mlperf-endpoints-cli-venv')
    venv_path = os.path.join(os.getcwd(), venv_name)
    env['MLC_MLPERF_ENDPOINTS_CLI_VENV_PATH'] = venv_path

    scripts = 'Scripts' if os_info['platform'] == 'windows' else 'bin'
    python_name = 'python.exe' if os_info['platform'] == 'windows' else 'python3'
    env['MLC_MLPERF_ENDPOINTS_CLI_PYTHON_BIN'] = os.path.join(
        venv_path, scripts, python_name)

    src = env.get('MLC_MLPERF_ENDPOINTS_CLI_SOURCE', '').strip()
    if src:
        if not os.path.isdir(src):
            return {'return': 1,
                    'error': f'submission-cli source path does not exist: {src}'}
        env['MLC_MLPERF_ENDPOINTS_CLI_INSTALL_TARGET'] = src
    else:
        env['MLC_MLPERF_ENDPOINTS_CLI_INSTALL_TARGET'] = env.get(
            'MLC_MLPERF_ENDPOINTS_CLI_PACKAGE', 'endpoints-submission-cli')

    return {'return': 0}


def postprocess(i):

    os_info = i['os_info']
    env = i['env']

    venv_path = env['MLC_MLPERF_ENDPOINTS_CLI_VENV_PATH']
    scripts = 'Scripts' if os_info['platform'] == 'windows' else 'bin'
    cli_name = 'endpoints-submission-cli'
    if os_info['platform'] == 'windows':
        cli_name += '.exe'
    env['MLC_MLPERF_ENDPOINTS_CLI_BIN'] = os.path.join(
        venv_path, scripts, cli_name)
    env['MLC_MLPERF_ENDPOINTS_CLI_INSTALLED'] = 'yes'
    env['MLC_GET_DEPENDENT_CACHED_PATH'] = venv_path

    venv_python = env['MLC_MLPERF_ENDPOINTS_CLI_PYTHON_BIN']
    try:
        version = subprocess.check_output(
            [venv_python, '-c',
             'import importlib.metadata as m; '
             'print(m.version("endpoints-submission-cli"))'],
            text=True, stderr=subprocess.DEVNULL).strip()
        if version:
            env['MLC_MLPERF_ENDPOINTS_CLI_VERSION'] = version
    except subprocess.CalledProcessError:
        # Version detection is best-effort; run.sh already verified the install.
        pass

    return {'return': 0}
