from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']
    state = i['state']

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    if not state.get(
            'mlperf-inference-implementation'):  # No state information. Just returning
        return {'return': 0}

    if is_true(env.get('MLC_MLPERF_README', "")):
        import mlc
        inp = i['input']

        script_tags = state['mlperf-inference-implementation'].get(
            'script_tags', '')
        script_adr = state['mlperf-inference-implementation'].get(
            'script_adr', {})

        if script_tags != '':
            mlc_input = {'action': 'run',
                         'automation': 'script',
                         'tags': script_tags,
                         'adr': script_adr,
                         'env': env,
                         'print_deps': True,
                         'quiet': True,
                         'silent': True,
                         'fake_run': True
                         }

            r = mlc.access(mlc_input)
            if r['return'] > 0:
                return r

            state['mlperf-inference-implementation']['print_deps'] = r['new_state']['print_deps']

    if env.get('MLC_DUMP_VERSION_INFO', True):

        if state['mlperf-inference-implementation'].get('script_id', '') == '':
            state['mlperf-inference-implementation']['script_id'] = ''

        script_id = state['mlperf-inference-implementation']['script_id']
        run_state = i['input']['run_state']
        version_info = {}
        version_info[script_id] = run_state['version_info']

        state['mlperf-inference-implementation']['version_info'] = version_info

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
