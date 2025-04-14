from mlc import utils
from utils import *
import os


def preprocess(i):

    os_info = i['os_info']
    env = i['env']

    if env.get('MLC_GPTJ_INTEL_MODEL', '') == 'yes':
        i['run_script_input']['script_name'] = 'run-intel'
        harness_root = os.path.join(
            env['MLC_MLPERF_INFERENCE_RESULTS_PATH'],
            'closed',
            'Intel',
            'code',
            'gptj-99',
            'pytorch-cpu')
        print(f"Harness Root: {harness_root}")
        env['MLC_HARNESS_CODE_ROOT'] = harness_root
        env['MLC_CALIBRATION_CODE_ROOT'] = os.path.join(
            env['MLC_MLPERF_INFERENCE_RESULTS_PATH'], 'closed', 'Intel', 'calibration')

        env['CHECKPOINT_DIR'] = env['GPTJ_CHECKPOINT_PATH']

        env['QUANTIZED_MODEL_DIR'] = os.getcwd()

        if env['MLC_ML_MODEL_WEIGHT_DATA_TYPES'] == "int8":
            env['INT8_MODEL_DIR'] = os.getcwd()
        else:
            env['INT4_MODEL_DIR'] = os.getcwd()

    elif env.get('MLC_TMP_ML_MODEL_PROVIDER', '') == 'nvidia':
        i['run_script_input']['script_name'] = 'run-nvidia'
        if is_true(str(env.get('MLC_DOCKER_DETACHED_MODE', ''))):
            env['DOCKER_RUN_OPTS'] = "--rm --ipc=host --ulimit memlock=-1 --ulimit stack=67108864"
        gpu_arch = int(
            float(
                env['MLC_CUDA_DEVICE_PROP_GPU_COMPUTE_CAPABILITY']) *
            10)
        env['MLC_GPU_ARCH'] = gpu_arch
        env['DOCKER_RUN_ARGS'] = f" -v {env['MLC_NVIDIA_MLPERF_SCRATCH_PATH']}:/mnt"

        if is_true(env.get('MLC_DOCKER_USE_GOOGLE_DNS', '')):
            env['DOCKER_RUN_ARGS'] += '  --dns 8.8.8.8 --dns 8.8.4.4 '

        env['MLC_TMP_REQUIRE_DOWNLOAD'] = 'no'

    else:
        is_saxml = env.get('MLC_TMP_MODEL_SAXML', '')
        if is_saxml == "fp32":
            i['run_script_input']['script_name'] = 'run-saxml'
        elif is_saxml == "int8":
            i['run_script_input']['script_name'] = 'run-saxml-quantized'
        else:
            path = env.get('GPTJ_CHECKPOINT_PATH', '').strip()

            if path == '' or not os.path.exists(path):
                env['MLC_TMP_REQUIRE_DOWNLOAD'] = 'yes'

    return {'return': 0}


def postprocess(i):

    env = i['env']

    if os.path.exists(os.path.join(
            env['GPTJ_CHECKPOINT_PATH'], "checkpoint-final")):
        env['GPTJ_CHECKPOINT_PATH'] = os.path.join(
            env['GPTJ_CHECKPOINT_PATH'], "checkpoint-final")

    is_saxml = env.get('MLC_TMP_MODEL_SAXML', '')
    if is_saxml == "fp32":
        if os.path.exists("pax_gptj_checkpoint"):
            env['GPTJ_SAXML_CHECKPOINT_PATH'] = os.path.join(
                os.getcwd(), "pax_gptj_checkpoint")
            env['MLC_ML_MODEL_FILE_WITH_PATH'] = env['GPTJ_SAXML_CHECKPOINT_PATH']
        else:
            return {'return': 1, 'error': 'pax_gptj_checkpoint generation failed'}

    elif is_saxml == "int8":
        if os.path.exists("int8_ckpt"):
            env['GPTJ_SAXML_INT8_CHECKPOINT_PATH'] = os.path.join(
                os.getcwd(), "int8_ckpt")
            env['MLC_ML_MODEL_FILE_WITH_PATH'] = env['GPTJ_SAXML_INT8_CHECKPOINT_PATH']
        else:
            return {'return': 1, 'error': 'pax_gptj_checkpoint generation failed'}
    elif env.get('MLC_TMP_ML_MODEL_PROVIDER', '') == 'nvidia':
        env['MLC_ML_MODEL_FILE_WITH_PATH'] = os.path.join(
            env['MLC_NVIDIA_MLPERF_SCRATCH_PATH'],
            'models',
            'GPTJ-6B',
            'fp8-quantized-ammo',
            'GPTJ-FP8-quantized')
    else:
        env['MLC_ML_MODEL_FILE_WITH_PATH'] = env['GPTJ_CHECKPOINT_PATH']

    env['MLC_ML_MODEL_FILE'] = os.path.basename(
        env['MLC_ML_MODEL_FILE_WITH_PATH'])
    env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_ML_MODEL_FILE_WITH_PATH']

    return {'return': 0}
