from mlc import utils
from utils import is_true
import os
import shutil


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}
    env = i['env']

    logger = i['automation'].logger

    if is_true(env.get('MLC_MLPERF_SKIP_RUN', '')):
        return {'return': 0}

    if 'MLC_MODEL' not in env:
        return {
            'return': 1, 'error': 'Please select a variation specifying the model to run'}
    if 'MLC_MLPERF_BACKEND' not in env:
        return {'return': 1,
                'error': 'Please select a variation specifying the backend'}
    if 'MLC_MLPERF_DEVICE' not in env:
        return {
            'return': 1, 'error': 'Please select a variation specifying the device to run on'}

    r = get_run_cmd(env['MLC_MODEL'], i)
    if r['return'] > 0:
        return r
    run_cmd = r['run_cmd']
    run_dir = r['run_dir']
    logger.info(run_cmd)
    logger.info(run_dir)
    env['MLC_MLPERF_RUN_CMD'] = run_cmd
    env['MLC_RUN_DIR'] = run_dir
    env['MLC_RUN_CMD'] = run_cmd

    return {'return': 0}
    # return {'return':1, 'error': 'Run command needs to be tested'}


def get_run_cmd(model, i):
    env = i['env']
    if "gptj" in model:
        scenario = env['MLC_MLPERF_LOADGEN_SCENARIO']
        device = env['MLC_MLPERF_DEVICE']
        mode = env['MLC_MLPERF_LOADGEN_MODE']
        outdir = env['MLC_MLPERF_OUTPUT_DIR']
        mlperf_conf_path = env['MLC_MLPERF_CONF']
        user_conf_path = env['MLC_MLPERF_USER_CONF']
        api_server = env.get('MLC_MLPERF_INFERENCE_API_SERVER', 'localhost')
        model_path = env['GPTJ_CHECKPOINT_PATH']
        dataset_path = env['MLC_DATASET_CNNDM_EVAL_PATH']
        precision = env['MLC_MLPERF_MODEL_PRECISION']
        if mode == "accuracy":
            accuracy_string = " --accuracy "
        else:
            accuracy_string = ""

        run_cmd = f"python3 -u main.py --scenario {scenario} --model-path {model_path} --api-server {api_server} --api-model-name gpt-j-cnn --mlperf-conf {mlperf_conf_path} {accuracy_string} --vllm --user-conf {user_conf_path} --dataset-path {dataset_path} --output-log-dir {outdir} --dtype float32 --device {device} "
        submitter = "CTuning"
        run_dir = os.path.join(
            env['MLC_MLPERF_INFERENCE_IMPLEMENTATION_REPO'],
            "open",
            submitter,
            "code",
            "gptj-99")

        return {'return': 0, 'run_cmd': run_cmd, 'run_dir': run_dir}

    if "llama2" in model:
        scenario = env['MLC_MLPERF_LOADGEN_SCENARIO']
        device = env['MLC_MLPERF_DEVICE']
        mode = env['MLC_MLPERF_LOADGEN_MODE']
        outdir = env['MLC_MLPERF_OUTPUT_DIR']
        mlperf_conf_path = env['MLC_MLPERF_CONF']
        user_conf_path = env['MLC_MLPERF_USER_CONF']
        api_server = env.get(
            'MLC_MLPERF_INFERENCE_API_SERVER',
            'localhost:8000/v1')
        api_model_name = env['MLC_VLLM_SERVER_MODEL_NAME']
        dataset_path = env['MLC_DATASET_OPENORCA_PATH']
        precision = env['MLC_MLPERF_MODEL_PRECISION']
        if mode == "accuracy":
            accuracy_string = " --accuracy "
        else:
            accuracy_string = ""

        run_cmd = f"python3 -u  'main.py' --scenario {scenario} --model-path {api_model_name} --api-model-name {api_model_name} --api-server {api_server} --mlperf-conf {mlperf_conf_path} {accuracy_string} --vllm --user-conf {user_conf_path} --dataset-path {dataset_path} --output-log-dir {outdir} --dtype float32 --device {device} "
        submitter = "RedHat-Supermicro"
        run_dir = os.path.join(
            env['MLC_MLPERF_INFERENCE_IMPLEMENTATION_REPO'],
            "open",
            submitter,
            "code",
            model)

        return {'return': 0, 'run_cmd': run_cmd, 'run_dir': run_dir}


def postprocess(i):

    env = i['env']

    return {'return': 0}
