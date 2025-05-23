from mlc import utils
import os
import xml.etree.ElementTree as et
from utils import is_true


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    platform_sdk_path = None

    if env.get('MLC_INPUT', '').strip() != '':
        path = env['MLC_INPUT']
        if os.path.exists(os.path.join(path, "exec", "qaic-runner")):
            platform_sdk_path = path
        else:
            return {
                'return': 1, 'error': 'exec/qaic-runner not found in the input path (--input)'}
    else:
        path = "/opt/qti-aic/"
        if os.path.exists(os.path.join(path, "exec", "qaic-runner")):
            platform_sdk_path = path

    if not platform_sdk_path:
        return {'return': 1,
                'error': f'qaic-runner not found in the default path: {path}'}

    env['MLC_QAIC_PLATFORM_SDK_PATH'] = path
    env['MLC_QAIC_RUNNER_PATH'] = os.path.join(path, "exec", "qaic-runner")
    env['MLC_QAIC_TOOLS_PATH'] = os.path.join(path, "tools")

    quiet = is_true(env.get('MLC_QUIET', False))

    return {'return': 0}


def detect_version(i):

    env = i['env']

    logger = i['automation'].logger
    sdk_path = env['MLC_QAIC_PLATFORM_SDK_PATH']
    version = None
    version_xml_path = os.path.join(sdk_path, "versions", "platform.xml")
    version_info = et.parse(version_xml_path)

    versions = version_info.getroot()
    build_id = None

    for child1 in versions:
        if child1.tag == "ci_build":
            for child2 in child1:
                if child2.tag == "base_version":
                    version = child2.text
                if child2.tag == "build_id":
                    build_id = child2.text
    if build_id:
        version = version + "." + build_id

    if not version:
        return {'return': 1, 'error': f'qaic platform sdk version info not found'}

    logger.info(
        i['recursion_spaces'] +
        '    Detected version: {}'.format(version))
    return {'return': 0, 'version': version}


def postprocess(i):

    env = i['env']
    r = detect_version(i)
    if r['return'] > 0:
        return r

    version = r['version']

    if "+PATH" not in env:
        env["+PATH"] = []

    env['+PATH'].append(os.path.dirname(env['MLC_QAIC_RUNNER_PATH']))

    paths = [
        "+C_INCLUDE_PATH",
        "+CPLUS_INCLUDE_PATH",
        "+LD_LIBRARY_PATH",
        "+DYLD_FALLBACK_LIBRARY_PATH"
    ]

    for key in paths:
        env[key] = []

    include_paths = []
    lib_paths = []

    inc_path = os.path.join(env['MLC_QAIC_PLATFORM_SDK_PATH'], "dev", "inc")
    if os.path.exists(inc_path):
        include_paths.append(inc_path)

    for inc_path in include_paths:
        env['+C_INCLUDE_PATH'].append(inc_path)
        env['+CPLUS_INCLUDE_PATH'].append(inc_path)

    lib_path = os.path.join(
        env['MLC_QAIC_PLATFORM_SDK_PATH'],
        "dev",
        "lib",
        env['MLC_HOST_PLATFORM_FLAVOR'])
    if os.path.exists(lib_path):
        lib_paths.append(lib_path)

    for lib_path in lib_paths:
        env['+LD_LIBRARY_PATH'].append(lib_path)
        env['+DYLD_FALLBACK_LIBRARY_PATH'].append(lib_path)

    return {'return': 0, 'version': version}
