from mlc import utils
import os


def preprocess(i):
    env = i['env']

    if env.get('MLC_GIT_URL', '') == '' and env.get('MLC_VERSION', '') == '':
        env['MLC_GIT_URL'] = "https://github.com/hans-intel/inference"
        env['MLC_GIT_CHECKOUT'] = env.get('MLC_GIT_CHECKOUT', 'perf_test_with_cached_output')
        env['MLC_VERSION'] = "perf_test_with_cached_output"

    return {'return': 0}


def postprocess(i):
    env = i['env']

    e2e_src = env.get('MLC_MLPERF_INFERENCE_E2E_SOURCE', '')
    if e2e_src:
        env['MLC_MLPERF_INFERENCE_E2E_SOURCE_VERSION'] = env.get('MLC_GIT_CHECKOUT', 'main')
        e2e_dir = os.path.join(e2e_src, 'e2e')
        if env.get('+PYTHONPATH') is None:
            env['+PYTHONPATH'] = []
        env['+PYTHONPATH'].append(e2e_dir)

    return {'return': 0}
