from mlc import utils
import os
import subprocess


def preprocess(i):

    os_info = i['os_info']
    env = i['env']

    src = env.get('MLC_MLPERF_INFERENCE_ENDPOINTS_SOURCE', '').strip()
    if src == '':
        return {
            'return': 1,
            'error': 'inference-endpoint source path is not set. The '
            'get,mlperf,endpoints,src dependency should set '
            'MLC_MLPERF_INFERENCE_ENDPOINTS_SOURCE, or pass '
            '--endpoints_src=<path> to use a local checkout.'}

    if not os.path.isdir(src):
        return {
            'return': 1,
            'error': f'inference-endpoint source path does not exist: {src}'}

    # Place the dedicated virtual environment inside the (cached) run directory
    # so it is reused across runs and isolated from the MLC host Python.
    venv_name = env.get('MLC_MLPERF_ENDPOINTS_VENV_NAME',
                        'mlperf-endpoints-venv')
    venv_path = os.path.join(os.getcwd(), venv_name)
    env['MLC_MLPERF_ENDPOINTS_VENV_PATH'] = venv_path

    scripts = 'Scripts' if os_info['platform'] == 'windows' else 'bin'
    python_name = 'python.exe' if os_info['platform'] == 'windows' else 'python3'
    env['MLC_MLPERF_ENDPOINTS_PYTHON_BIN'] = os.path.join(
        venv_path, scripts, python_name)

    return {'return': 0}


def postprocess(i):

    env = i['env']

    venv_python = env['MLC_MLPERF_ENDPOINTS_PYTHON_BIN']
    env['MLC_MLPERF_ENDPOINTS_INSTALLED'] = 'yes'
    env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_MLPERF_ENDPOINTS_VENV_PATH']

    # Record the installed version for provenance (informational only).
    try:
        version = subprocess.check_output(
            [venv_python, '-c',
             'import inference_endpoint as m; print(getattr(m, "__version__", ""))'],
            text=True, stderr=subprocess.DEVNULL).strip()
        if version:
            env['MLC_MLPERF_ENDPOINTS_VERSION'] = version
    except subprocess.CalledProcessError:
        # Version detection is best-effort; the install itself already
        # succeeded (run.sh would have failed otherwise).
        pass

    return {'return': 0}
