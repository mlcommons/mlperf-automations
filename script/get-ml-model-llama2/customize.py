from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']
    env = i['env']

    if env.get('MLC_TMP_ML_MODEL_PROVIDER', '') == 'nvidia':
        if is_true(env.get('MLC_ML_MODEL_QUANTIZE_LOCALLY')):
            i['run_script_input']['script_name'] = 'run-nvidia'
            gpu_arch = int(
                float(
                    env['MLC_CUDA_DEVICE_PROP_GPU_COMPUTE_CAPABILITY']) *
                10)
            env['MLC_GPU_ARCH'] = gpu_arch
            env['MLC_TMP_REQUIRE_DOWNLOAD'] = 'no'
        else:
            target_dir = os.path.join(
                env['MLC_NVIDIA_MLPERF_SCRATCH_PATH'],
                "models",
                "Llama2",
                "fp8-quantized-ammo",
                f"llama-2-70b-chat-hf-tp{env['MLC_NVIDIA_TP_SIZE']}pp{env['MLC_NVIDIA_PP_SIZE']}-{env['MLC_ML_MODEL_PRECISION']}"
            )

            # Ensure target directory exists
            os.makedirs(target_dir, exist_ok=True)

            run_cmd = f"cp -r {env['LLAMA2_QUANTIZED_CHECKPOINT_PATH']}\* {env['MLC_NVIDIA_MLPERF_SCRATCH_PATH']}/models/Llama2/fp8-quantized-ammo/llama-2-70b-chat-hf-tp{env['MLC_NVIDIA_TP_SIZE']}pp{env['MLC_NVIDIA_PP_SIZE']}-{env['MLC_ML_MODEL_PRECISION']}"
            run_cmd = f"cp -r {env['LLAMA2_CHECKPOINT_PATH']}\* {env['MLC_NVIDIA_MLPERF_SCRATCH_PATH']}/models/Llama2/Llama-2-70b-chat-hf"
            
            env['MLC_RUN_CMD'] = run_cmd
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

    return {'return': 0}


def postprocess(i):

    env = i['env']
    if env.get('MLC_DOWNLOAD_MODE', '') != "dry":
        if is_true(env.get('MLC_ML_MODEL_QUANTIZE_LOCALLY')):
            if env.get('LLAMA2_CHECKPOINT_PATH', '') == '':
                env['LLAMA2_CHECKPOINT_PATH'] = env['MLC_ML_MODEL_PATH']
            else:
                env['MLC_ML_MODEL_PATH'] = env['LLAMA2_CHECKPOINT_PATH']
            env['MLC_ML_MODEL_LLAMA2_FILE_WITH_PATH'] = env['LLAMA2_CHECKPOINT_PATH']
            env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_ML_MODEL_PATH']
        else:
            env['LLAMA2_PRE_QUANTIZED_CHECKPOINT_PATH'] = env['LLAMA2_CHECKPOINT_PATH']

    return {'return': 0}
