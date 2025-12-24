from mlc import utils
from utils import is_true, is_false
import os


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    meta = i['meta']
    automation = i['automation']
    logger = automation.logger
    run_script_input = i['run_script_input']
    pip_version = env.get('MLC_PIP_VERSION', '').strip().split('.')

    logger = automation.action_object.logger

    package_name = env.get('MLC_GENERIC_PYTHON_PACKAGE_NAME', '').strip()
    if package_name == '':
        return automation._available_variations({'meta': meta})

    if package_name == "onnxruntime_gpu":
        # https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html#requirements
        # 20240214: ONNXRuntime 1.17.0 now support CUDA 12 so we remove next check
        # TBD: if we have explicit version for ONNX < 17.0.0 and CUDA is >= 12,
        # we should add a check to fail ...
        cuda_version = env.get('MLC_CUDA_VERSION', '').strip()
#        if cuda_version!='':
#            cuda_version_split = cuda_version.split('.')
#            if int(cuda_version_split[0]) >= 12:
#                # env['MLC_INSTALL_ONNXRUNTIME_GPU_FROM_SRC'] = "yes"
# return {'return': 1, 'error':'at this moment, PIP package
# "onnxruntime_gpu" needs CUDA < 12'}

    extra = env.get('MLC_GENERIC_PYTHON_PIP_EXTRA', '')
    if (pip_version and len(pip_version) > 1 and int(pip_version[0]) >= 23) and (
            '--break-system-packages' not in extra):
        extra += '  --break-system-packages '
        env['MLC_PYTHON_PIP_COMMON_EXTRA'] = " --break-system-packages"

    if is_false(env.get('MLC_GENERIC_PYTHON_PACKAGE_INSTALL_DEPS', '')):
        env['MLC_PYTHON_PIP_COMMON_EXTRA'] = " --no-deps"

    if is_true(env.get('MLC_PIP_INSTALL_NEEDS_USER', '')):
        env['MLC_PYTHON_PIP_COMMON_EXTRA'] = " --user"

    if env.get('MLC_GENERIC_PYTHON_PIP_UNINSTALL_DEPS', '') != '':
        r = automation.run_native_script(
            {'run_script_input': run_script_input, 'env': env, 'script_name': 'uninstall_deps'})
        if r['return'] > 0:
            return r

    prepare_env_key = env.get('MLC_GENERIC_PYTHON_PACKAGE_NAME', '')
    for x in ["-", "[", "]"]:
        prepare_env_key = prepare_env_key.replace(x, "_")

    env['MLC_TMP_PYTHON_PACKAGE_NAME_ENV'] = prepare_env_key.upper()

    recursion_spaces = i['recursion_spaces']

    r = automation.detect_version_using_script({
        'env': env,
        'run_script_input': i['run_script_input'],
        'recursion_spaces': recursion_spaces})

    force_install = (
        is_true(env.get(
            'MLC_TMP_PYTHON_PACKAGE_FORCE_INSTALL',
            '')))

    if r['return'] > 0 or force_install:
        if r['return'] == 16 or force_install:
            # Clean detected version env if exists otherwise takes detected version
            # for example, when we reinstall generic python lib package
            env_version_key = 'MLC_' + \
                env['MLC_TMP_PYTHON_PACKAGE_NAME_ENV'].upper() + '_VERSION'
            if env.get(env_version_key, '') != '':
                del (env[env_version_key])

            # Check if upgrade
            if force_install:
                extra += ' --upgrade --no-deps --force-reinstall'

            # Check index URL
            index_url = env.get('MLC_GENERIC_PYTHON_PIP_INDEX_URL', '').strip()
            if index_url != '':
                # Check special cases
                if '${MLC_TORCH_CUDA}' in index_url:
                    index_url = index_url.replace(
                        '${MLC_TORCH_CUDA}', env.get('MLC_TORCH_CUDA'))

                extra += ' --index-url ' + index_url

            # Check extra index URL
            extra_index_url = env.get(
                'MLC_GENERIC_PYTHON_PIP_EXTRA_INDEX_URL', '').strip()

            if extra_index_url != '':
                # Check special cases
                if '${MLC_TORCH_CUDA}' in extra_index_url:
                    extra_index_url = extra_index_url.replace(
                        '${MLC_TORCH_CUDA}', env.get('MLC_TORCH_CUDA'))

                extra += ' --extra-index-url ' + extra_index_url

            # check find-links
            find_links_url = env.get(
                'MLC_GENERIC_PYTHON_PIP_EXTRA_FIND_LINKS_URL', '').strip()

            if find_links_url != '':
                extra += ' -f ' + find_links_url

            # Check update
            if is_true(env.get('MLC_GENERIC_PYTHON_PIP_UPDATE', '')):
                extra += ' -U'

            logger.info(recursion_spaces + '      Extra PIP CMD: ' + extra)

            env['MLC_GENERIC_PYTHON_PIP_EXTRA'] = extra

            r = automation.run_native_script(
                {'run_script_input': run_script_input, 'env': env, 'script_name': 'install'})

            if r['return'] > 0:
                return r

    return {'return': 0}


def detect_version(i):

    env = i['env']
    automation = i['automation']
    logger = automation.action_object.logger

    if env.get('MLC_TMP_PYTHON_PACKAGE_NAME_ENV', '') != '':
        env_version_key = 'MLC_' + \
            env['MLC_TMP_PYTHON_PACKAGE_NAME_ENV'].upper() + '_VERSION'
    else:
        env_version_key = 'MLC_CACHE_TMP_VERSION'

    r = i['automation'].parse_version({'match_text': r'\s*([\d.a-z\-]+)',
                                       'group_number': 1,
                                       'env_key': env_version_key,
                                       'which_env': i['env']})
    if r['return'] > 0:
        return r

    version = r['version']
    current_detected_version = version

    logger.info(
        i['recursion_spaces'] +
        '      Detected version: {}'.format(version))

    return {'return': 0, 'version': version}


def postprocess(i):

    env = i['env']

    env_version_key = 'MLC_' + \
        env['MLC_TMP_PYTHON_PACKAGE_NAME_ENV'].upper() + '_VERSION'

    if env.get(env_version_key, '') != '':
        version = env[env_version_key]
    else:
        r = detect_version(i)
        if r['return'] > 0:
            return r

        version = r['version']

    env['MLC_PYTHONLIB_' + env['MLC_TMP_PYTHON_PACKAGE_NAME_ENV'] +
        '_CACHE_TAGS'] = 'version-' + version

    import importlib.util
    package_name = env.get('MLC_GENERIC_PYTHON_PACKAGE_NAME', '').strip()
    spec = importlib.util.find_spec(package_name)
    if spec and spec.origin:
        env['MLC_GET_DEPENDENT_CACHED_PATH'] = spec.origin

    pip_version = env.get('MLC_PIP_VERSION', '').strip().split('.')
    if pip_version and len(pip_version) > 1 and int(pip_version[0]) >= 23:
        env['MLC_PYTHON_PIP_COMMON_EXTRA'] = " --break-system-packages"

    if version.count('.') > 1:
        env[f"{env_version_key}_MAJOR_MINOR"] = ".".join(
            version.split(".")[:2])

    return {'return': 0, 'version': version}
