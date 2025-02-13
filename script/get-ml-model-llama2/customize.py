from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    env = i['env']

    if env.get('MLC_TMP_ML_MODEL_PROVIDER', '') == 'nvidia':
        i['run_script_input']['script_name'] = 'run-nvidia'
        gpu_arch = int(
            float(
                env['MLC_CUDA_DEVICE_PROP_GPU_COMPUTE_CAPABILITY']) *
            10)
        env['MLC_GPU_ARCH'] = gpu_arch
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = 'no'
    else:
        path = env.get('LLAMA2_CHECKPOINT_PATH', '').strip()

        if env.get('MLC_TMP_ML_MODEL_PROVIDER', '') == 'amd':
            env['MLC_TMP_REQUIRE_DOWNLOAD'] = 'no'
            i['run_script_input']['script_name'] = 'run-amd'
            env['AMD_CODE_DIR'] = os.path.join(
                env['MLC_MLPERF_INFERENCE_RESULTS_PATH'], 'closed', 'AMD', 'code')
            env['MLC_LLAMA2_FINAL_SAFE_TENSORS_ROOT'] = os.getcwd()
            env['MLC_LLAMA2_FINAL_SAFE_TENSORS_PATH'] = os.path.join(
                env['MLC_LLAMA2_FINAL_SAFE_TENSORS_ROOT'], "llama.safetensors")
        else:
            if path == '' or not os.path.exists(path):
                env['MLC_TMP_REQUIRE_DOWNLOAD'] = 'yes'
                if env['MLC_DOWNLOAD_SRC'] == "mlcommons":
                    i['run_script_input']['script_name'] = 'run-rclone'
                    if env.get('MLC_OUTDIRNAME', '') != '':
                        env['LLAMA2_CHECKPOINT_PATH'] = env['MLC_OUTDIRNAME']
                    else:
                        env['LLAMA2_CHECKPOINT_PATH'] = os.getcwd()

    return {'return': 0}


def postprocess(i):

    env = i['env']
    if env.get('LLAMA2_CHECKPOINT_PATH', '') == '':
        env['LLAMA2_CHECKPOINT_PATH'] = env['MLC_ML_MODEL_PATH']
    else:
        env['MLC_ML_MODEL_PATH'] = env['LLAMA2_CHECKPOINT_PATH']
    env['MLC_ML_MODEL_LLAMA2_FILE_WITH_PATH'] = env['LLAMA2_CHECKPOINT_PATH']
    env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_ML_MODEL_PATH']

    return {'return': 0}
