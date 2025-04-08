from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    script_path = i['artifact'].path

    if env.get('MLC_MLPERF_INFERENCE_VERSION', '') == "5.0":
        extra_run_cmd = 'patch -p1 < {}'.format(os.path.join(
            script_path, 'patch', 'numpy-mitten-v5.0.patch'))
        env['EXTRA_RUN_CMD'] = extra_run_cmd

    return {'return': 0}


def postprocess(i):

    os_info = i['os_info']
    env = i['env']

    # TBD
    cur_dir = os.getcwd()

    return {'return': 0}
