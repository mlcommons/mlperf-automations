from mlc import utils
import os
import json
import subprocess


# State keys holding the per-device property records published by the
# accelerator detection scripts, in the order they are looked for.
_DEVICE_STATE_KEYS = [
    'mlc_cuda_devices_prop',
    'mlc_rocm_devices_prop',
    'mlc_xpu_devices_prop',
]


def _dump_device_props(state, dir_path, logger):
    """Write the detected per-device records to a file for parse.py.

    parse.py runs as a plain subprocess and so can only see the environment,
    where each MLC_*_DEVICE_PROP_* var holds whichever device was enumerated
    last. The state published by the detection script describes every device,
    which is what a host with more than one accelerator model needs, so it is
    handed over as a file rather than flattened into the environment.

    Returns the path written, or '' when no accelerator was detected."""
    devices = None
    for key in _DEVICE_STATE_KEYS:
        if state.get(key):
            devices = state[key]
            break
    if not devices:
        return ''

    # Published as a dict keyed by device index; the order of the devices is
    # what matters downstream, not the keys.
    if isinstance(devices, dict):
        try:
            ordered = [devices[k]
                       for k in sorted(devices, key=lambda x: int(x))]
        except (TypeError, ValueError):
            ordered = [devices[k] for k in sorted(devices, key=str)]
    else:
        ordered = list(devices)

    path = os.path.join(dir_path, 'tmp-device-props.json')
    try:
        with open(path, 'w') as f:
            json.dump(ordered, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not write device properties to {path}: {e}")
        return ''
    return path


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    state = i['state']
    logger = i['automation'].logger
    if env.get('MLC_SINGLE_NODE_SYSTEM_INFO_FILE_PATH', '') == '':
        if env.get('MLC_SINGLE_NODE_SYSTEM_INFO_DIR_PATH', '') == '':
            env['MLC_SINGLE_NODE_SYSTEM_INFO_DIR_PATH'] = os.getcwd()
        if env.get('MLC_SINGLE_NODE_SYSTEM_INFO_FILE_NAME', '') == '':
            env['MLC_SINGLE_NODE_SYSTEM_INFO_FILE_NAME'] = f"mlperf-system-info-single-node-{env.get('MLC_SINGLE_NODE_SYSTEM_ID', '')}.json"
        env['MLC_SINGLE_NODE_SYSTEM_INFO_FILE_PATH'] = os.path.join(
            env['MLC_SINGLE_NODE_SYSTEM_INFO_DIR_PATH'], env['MLC_SINGLE_NODE_SYSTEM_INFO_FILE_NAME'])

    if not os.path.exists(env['MLC_SINGLE_NODE_SYSTEM_INFO_DIR_PATH']):
        os.makedirs(env['MLC_SINGLE_NODE_SYSTEM_INFO_DIR_PATH'], exist_ok=True)

    CMD = f"""{env['MLC_PYTHON_BIN_WITH_PATH']} {env['MLC_TMP_CURRENT_SCRIPT_PATH']}/parse.py --output {env['MLC_SINGLE_NODE_SYSTEM_INFO_FILE_PATH']}"""

    device_props_path = _dump_device_props(
        state, env['MLC_SINGLE_NODE_SYSTEM_INFO_DIR_PATH'], logger)
    if device_props_path:
        CMD += f" --device-props {device_props_path}"

    env['MLC_RUN_CMD'] = CMD

    return {'return': 0}


def postprocess(i):

    state = i['state']

    env = i['env']

    os_info = i['os_info']

    automation = i['automation']

    # Stamp the output with the git version of the automations repo that
    # produced it (traceability, since mlc-scripts has no tagged release).
    output_path = env.get('MLC_SINGLE_NODE_SYSTEM_INFO_FILE_PATH', '')
    repo_path = env.get('MLC_TMP_CURRENT_SCRIPT_REPO_PATH', '')
    if output_path and os.path.exists(output_path):
        try:
            from mlc.utils import get_repo_version
            version = get_repo_version(repo_path)
            if version:
                with open(output_path) as f:
                    data = json.load(f)
                data['mlc_scripts_version'] = {
                    'repo': os.path.basename(repo_path), **version}
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            automation.logger.warning(
                f"Could not add version info to {output_path}: {e}")

    return {'return': 0}
