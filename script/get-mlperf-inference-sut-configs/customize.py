from mlc import utils
from utils import is_true
import os
import yaml
import shutil


def postprocess(i):
    env = i['env']
    state = i['state']

    if env.get('MLC_HW_NAME', '') == '':
        host_name = env.get(
            'MLC_HOST_SYSTEM_NAME',
            'default').replace(
            "-",
            "_").replace(" ", "_")
        env['MLC_HW_NAME'] = host_name

    device = env.get('MLC_MLPERF_DEVICE', 'cpu')

    backend = env.get('MLC_MLPERF_BACKEND', 'default')
    if env.get('MLC_MLPERF_BACKEND_VERSION', '') != '':
        backend_version = "v" + env.get('MLC_MLPERF_BACKEND_VERSION') if not env.get(
            'MLC_MLPERF_BACKEND_VERSION').startswith("v") else env.get('MLC_MLPERF_BACKEND_VERSION')
    else:
        backend_version = 'vdefault'

    if 'MLC_SUT_CONFIG' not in state:
        state['MLC_SUT_CONFIG'] = {}
    if 'MLC_SUT_CONFIG_PATH' not in state:
        state['MLC_SUT_CONFIG_PATH'] = {}

    implementation_string = env['MLC_MLPERF_SUT_NAME_IMPLEMENTATION_PREFIX'] if env.get(
        'MLC_MLPERF_SUT_NAME_IMPLEMENTATION_PREFIX', '') != '' else env.get(
        'MLC_MLPERF_IMPLEMENTATION', 'default')

    run_config = []
    for i in range(1, 6):
        if env.get(f'MLC_MLPERF_SUT_NAME_RUN_CONFIG_SUFFIX{i}', '') != '':
            run_config.append(
                env.get(f'MLC_MLPERF_SUT_NAME_RUN_CONFIG_SUFFIX{i}'))

    run_config_string = "_".join(
        run_config) if run_config else 'default_config'
    env['MLC_MLPERF_INFERENCE_SUT_RUN_CONFIG'] = run_config_string

    if env.get('MLC_SUT_NAME', '') == '':
        env['MLC_SUT_NAME'] = env['MLC_HW_NAME'] + "-" + implementation_string + "-" + \
            device + "-" + backend + "-" + backend_version + "-" + run_config_string

    if env.get('MLC_SUT_CONFIGS_PATH', '') != '':
        path = env['MLC_SUT_CONFIGS_PATH']
    elif is_true(env.get('MLC_SUT_USE_EXTERNAL_CONFIG_REPO', '')):
        path = env.get('MLC_GIT_CHECKOUT_PATH')
    else:
        path = os.path.join(os.getcwd(), "configs")

    config_path = os.path.join(
        path,
        env['MLC_HW_NAME'],
        implementation_string +
        "-implementation",
        device +
        "-device",
        backend +
        "-framework",
        "framework-version-" +
        backend_version,
        run_config_string +
        "-config.yaml")
    if not os.path.exists(config_path):
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        config_path_default = os.path.join(
            path,
            env['MLC_HW_NAME'],
            implementation_string +
            "-implementation",
            device +
            "-device",
            backend +
            "-framework",
            "default-config.yaml")
        if os.path.exists(config_path_default):
            shutil.copy(config_path_default, config_path)
        else:
            src_config_full = os.path.join(
                env['MLC_TMP_CURRENT_SCRIPT_PATH'],
                "configs",
                env['MLC_HW_NAME'],
                implementation_string + "-implementation",
                device + "-device",
                backend + "-framework",
                "framework-version-" + backend_version,
                run_config_string + "-config.yaml")
            src_config_partial1 = os.path.join(
                env['MLC_TMP_CURRENT_SCRIPT_PATH'],
                "configs",
                env['MLC_HW_NAME'],
                implementation_string + "-implementation",
                device + "-device",
                backend + "-framework",
                "framework-version-" + backend_version,
                "default-config.yaml")
            src_config_partial2 = os.path.join(
                env['MLC_TMP_CURRENT_SCRIPT_PATH'],
                "configs",
                env['MLC_HW_NAME'],
                implementation_string + "-implementation",
                device + "-device",
                backend + "-framework",
                "framework-version-default",
                "default-config.yaml")
            src_config_partial3 = os.path.join(
                env['MLC_TMP_CURRENT_SCRIPT_PATH'],
                "configs",
                env['MLC_HW_NAME'],
                implementation_string + "-implementation",
                device + "-device",
                backend + "-framework",
                "default-config.yaml")
            if os.path.exists(src_config_full):
                shutil.copy(src_config_full, config_path)
            elif os.path.exists(src_config_partial1):
                shutil.copy(src_config_partial1, config_path)
            elif os.path.exists(src_config_partial2):
                shutil.copy(src_config_partial2, config_path)
            elif os.path.exists(src_config_partial3):
                shutil.copy(src_config_partial3, config_path)
            else:
                print(
                    f"Config file missing for given hw_name: '{env['MLC_HW_NAME']}', implementation: '{implementation_string}', device: '{device},  backend: '{backend}', copying from default")
                src_config = os.path.join(
                    env['MLC_TMP_CURRENT_SCRIPT_PATH'],
                    "configs",
                    "default",
                    "config.yaml")
                shutil.copy(src_config, config_path)
                os.makedirs(
                    os.path.dirname(config_path_default),
                    exist_ok=True)
                shutil.copy(src_config, config_path_default)

    state['MLC_SUT_CONFIG'][env['MLC_SUT_NAME']] = yaml.load(
        open(config_path), Loader=yaml.SafeLoader)
    state['MLC_SUT_CONFIG_NAME'] = env['MLC_SUT_NAME']
    state['MLC_SUT_CONFIG_PATH'][env['MLC_SUT_NAME']] = config_path

    return {'return': 0}
