from mlc import utils
import os
import shutil


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}
    env = i['env']

    logger = i['automation'].logger

    if env.get('MLC_MLPERF_SKIP_RUN', '') == "yes":
        return {'return': 0}

    import json
    if 'MLC_MODEL' not in env:
        return {
            'return': 1, 'error': 'Please select a variation specifying the model to run'}
    if 'MLC_MLPERF_BACKEND' not in env:
        return {'return': 1,
                'error': 'Please select a variation specifying the backend'}
    if 'MLC_MLPERF_DEVICE' not in env:
        return {
            'return': 1, 'error': 'Please select a variation specifying the device to run on'}

    ml_model = env['MLC_MODEL']
    master_model = ml_model.replace("-99.9", "").replace("-99", "")
    master_model = master_model.replace("gptj", "gpt-j")

    backend = env['MLC_MLPERF_BACKEND']
    device = env['MLC_MLPERF_DEVICE']
    code_base_folder = backend + '-' + device
    if env.get('MLC_MLPERF_INFERENCE_CODE_VERSION', '') == 'v4.0':
        if 'gptj' in ml_model:
            code_base_folder = "ITREX"
    if 'dlrm-v2' in ml_model:
        code_base_folder = "pytorch-cpu-int8"

    harness_root = os.path.join(
        env['MLC_MLPERF_INFERENCE_RESULTS_PATH'],
        'closed',
        'Intel',
        'code',
        ml_model,
        code_base_folder)

    env['MLC_HARNESS_CODE_ROOT'] = harness_root

    if env.get('MLC_MODEL') == "resnet50":
        pass

    elif "bert" in env.get('MLC_MODEL'):
        pass
    elif "retinanet" in env.get('MLC_MODEL'):
        pass
    elif "gptj" in env.get('MLC_MODEL'):
        env['CHECKPOINT_DIR'] = env['GPTJ_CHECKPOINT_PATH']

    script_path = i['run_script_input']['path']
    if env['MLC_MODEL'] == "retinanet":
        env['MLC_DATASET_LIST'] = env['MLC_DATASET_ANNOTATIONS_FILE_PATH']

    if 'MLC_MLPERF_CONF' not in env:
        env['MLC_MLPERF_CONF'] = os.path.join(
            env['MLC_MLPERF_INFERENCE_SOURCE'], "mlperf.conf")
    if 'MLC_MLPERF_USER_CONF' not in env:
        env['MLC_MLPERF_USER_CONF'] = os.path.join(
            env['MLC_MLPERF_INFERENCE_CLASSIFICATION_AND_DETECTION_PATH'], "user.conf")

    loadgen_mode = env['MLC_MLPERF_LOADGEN_MODE']
    env['CONDA_PREFIX'] = env['MLC_CONDA_PREFIX']

    if env['MLC_LOCAL_MLPERF_INFERENCE_INTEL_RUN_MODE'] == "calibration":
        if master_model == "resnet50":
            i['run_script_input']['script_name'] = "prepare_imagenet_calibration"
        elif master_model == "3d-unet":
            i['run_script_input']['script_name'] = "prepare_3d-unet_data_model"
        elif "dlrm-v2" in master_model:
            i['run_script_input']['script_name'] = "calibrate_dlrm_v2_model"
        else:
            calibration_root = os.path.join(
                env['MLC_MLPERF_INFERENCE_RESULTS_PATH'],
                'closed',
                'Intel',
                'calibration',
                master_model,
                backend + "-" + device)

            if "gpt" in env['MLC_MODEL']:
                i['run_script_input']['script_name'] = "calibrate_gptj_int4_model"
                calibration_path = os.path.join(calibration_root, "INT4")
                env['MLC_MLPERF_INFERENCE_INTEL_CALIBRATION_PATH'] = calibration_path
                env['INT4_CALIBRATION_DIR'] = os.path.join(
                    calibration_path, "data", "quantized-int4-model")

    elif env['MLC_LOCAL_MLPERF_INFERENCE_INTEL_RUN_MODE'] == "compilation":
        if master_model == "resnet50":
            i['run_script_input']['script_name'] = "compile_resnet50"
        elif master_model == "retinanet":
            i['run_script_input']['script_name'] = "compile_retinanet"
            env['MLC_ML_MODEL_RETINANET_INT8_FILE_WITH_PATH'] = os.path.join(
                os.path.dirname(env['MLC_ML_MODEL_FILE_WITH_PATH']), 'retinanet-int8-model.pth')

    elif env['MLC_LOCAL_MLPERF_INFERENCE_INTEL_RUN_MODE'] == "build_harness":
        logger.info(f"Harness Root: {harness_root}")
        if "bert" in env['MLC_MODEL']:
            i['run_script_input']['script_name'] = "build_bert_harness"
            env['MLC_MLPERF_INFERENCE_INTEL_HARNESS_PATH'] = os.path.join(
                os.getcwd(), "harness", "build", "bert_inference")
            env['DATA_PATH'] = os.path.join(os.getcwd(), "harness", "bert")
        elif "stable-diffusion" in env['MLC_MODEL']:
            i['run_script_input']['script_name'] = "build_sdxl_harness"
        elif "resnet50" in env['MLC_MODEL']:
            i['run_script_input']['script_name'] = "build_resnet50_harness"
            env['MLC_MLPERF_INFERENCE_INTEL_HARNESS_PATH'] = os.path.join(
                os.getcwd(), "harness", "build", "resnet50_inference")
            env['DATA_PATH'] = os.path.join(os.getcwd(), "harness", "resnet50")
        elif "retinanet" in env['MLC_MODEL']:
            i['run_script_input']['script_name'] = "build_retinanet_harness"
            env['MLC_MLPERF_INFERENCE_INTEL_HARNESS_PATH'] = os.path.join(
                os.getcwd(), "harness", "build", "retinanet_inference")
        elif "gpt" in env['MLC_MODEL']:
            i['run_script_input']['script_name'] = "build_gptj_harness"
            env['MLC_MLPERF_INFERENCE_INTEL_HARNESS_PATH'] = os.path.join(
                os.getcwd(), "harness", "build", "gptj_inference")
            env['DATA_PATH'] = os.path.join(os.getcwd(), "harness", "gptj")
            env['MLPERF_INFERENCE_ROOT'] = env['MLC_MLPERF_INFERENCE_SOURCE']
            if env.get('INTEL_GPTJ_INT4', '') == 'yes':
                model_precision = "int4"
                if env.get('MLC_MLPERF_INFERENCE_CODE_VERSION', '') == 'v3.1':
                    env['RUN_QUANTIZATION_CMD'] = "bash run_quantization_int4.sh"
                else:
                    env['FILE_TAG'] = "final"
                    env['OUT_DIR'] = os.getcwd()
                    env['RUN_QUANTIZATION_CMD'] = "bash run_quantization.sh"
            else:
                model_precision = "int8"
                env['RUN_QUANTIZATION_CMD'] = "bash run_quantization.sh"
            if env.get('MLC_MLPERF_INFERENCE_CODE_VERSION', '') == "v3.1":
                final_model_path = os.path.join(
                    harness_root, "data", f"gpt-j-{model_precision}-model", "best_model.pt")
            else:
                final_model_path = os.path.join(
                    env['OUT_DIR'], "checkpoint-final-final-q4-j-int8-pc.bin")
            model_dir_name = f"{model_precision.upper()}_MODEL_DIR"
            env[model_dir_name] = os.path.dirname(final_model_path)
            if not os.path.exists(env[model_dir_name]):
                os.makedirs(env[model_dir_name])
            env['MLC_ML_MODEL_PATH'] = env[model_dir_name]
            env['MLC_ML_MODEL_FILE_WITH_PATH'] = final_model_path
            if env.get('MLC_MLPERF_INFERENCE_INTEL_GPTJ_INT8_MODEL_PATH',
                       '') != '' and env.get('INT8_MODEL_DIR', '') != '':
                shutil.copy(
                    env['MLC_MLPERF_INFERENCE_INTEL_GPTJ_INT8_MODEL_PATH'],
                    env[model_dir_name])
            if env.get('MLC_MLPERF_INFERENCE_INTEL_GPTJ_INT4_MODEL_PATH',
                       '') != '' and env.get('INT4_MODEL_DIR', '') != '':
                shutil.copy(
                    env['MLC_MLPERF_INFERENCE_INTEL_GPTJ_INT4_MODEL_PATH'],
                    env[model_dir_name])

    elif env['MLC_LOCAL_MLPERF_INFERENCE_INTEL_RUN_MODE'] == "run_harness":
        logger.info(f"Harness Root: {harness_root}")
        if env.get('MLC_MLPERF_LOADGEN_MODE', '') == "compliance":
            audit_path = env['MLC_MLPERF_INFERENCE_AUDIT_PATH']
            shutil.copy(audit_path, env['MLC_RUN_DIR'])

        if env['MLC_MLPERF_LOADGEN_MODE'] == "accuracy":
            env['LOADGEN_MODE'] = 'Accuracy'
        else:
            env['LOADGEN_MODE'] = 'Performance'

        if 'bert' in env['MLC_MODEL']:
            env['MODEL_PATH'] = os.path.dirname(os.path.dirname(
                env['MLC_MLPERF_INFERENCE_INTEL_HARNESS_PATH']))
            env['DATASET_PATH'] = os.path.dirname(os.path.dirname(
                env['MLC_MLPERF_INFERENCE_INTEL_HARNESS_PATH']))
            env['MLC_RUN_DIR'] = i['run_script_input']['path']
            env['MLC_RUN_CMD'] = "bash run_bert_harness.sh " + \
                ("--accuracy" if env['MLC_MLPERF_LOADGEN_MODE']
                 == "accuracy" else "")

        elif 'resnet50' in env['MLC_MODEL']:
            env['MODEL_PATH'] = os.path.dirname(os.path.dirname(
                env['MLC_MLPERF_INFERENCE_INTEL_HARNESS_PATH']))
            env['DATASET_PATH'] = os.path.dirname(os.path.dirname(
                env['MLC_MLPERF_INFERENCE_INTEL_HARNESS_PATH']))
            env['MLC_RUN_DIR'] = env['MLC_MLPERF_OUTPUT_DIR']
            env['MLC_RUN_CMD'] = f"bash {os.path.join(i['run_script_input']['path'],'run_resnet50_harness.sh')} "

        elif 'retinanet' in env['MLC_MODEL']:
            env['MODEL_PATH'] = env['MLC_ML_MODEL_RETINANET_INT8_FILE_WITH_PATH']
            env['DATA_DIR'] = env['MLC_DATASET_PATH_ROOT']
            env['MLC_RUN_DIR'] = env['MLC_MLPERF_OUTPUT_DIR']
            env['MLC_RUN_CMD'] = f"bash {os.path.join(i['run_script_input']['path'],'run_retinanet_harness.sh')} "

        elif '3d-unet' in env['MLC_MODEL']:
            env['MLC_RUN_DIR'] = env['MLC_MLPERF_OUTPUT_DIR']
            env['MLC_RUN_CMD'] = f"bash {os.path.join(i['run_script_input']['path'],'run_3d-unet_harness.sh')} "

        elif 'dlrm' in env['MLC_MODEL']:
            env['MLC_RUN_DIR'] = i['run_script_input']['path']
            env['MLC_RUN_CMD'] = f"bash {os.path.join(i['run_script_input']['path'],'run_dlrm_v2_harness.sh')} "

        elif 'stable-diffusion' in env['MLC_MODEL']:
            env['MLC_RUN_DIR'] = i['run_script_input']['path']
            env['MLC_RUN_CMD'] = "bash run_sdxl_harness.sh " + \
                ("--accuracy" if env['MLC_MLPERF_LOADGEN_MODE']
                 == "accuracy" else "")

        elif "gptj" in env['MLC_MODEL']:
            env['MLC_RUN_DIR'] = i['run_script_input']['path']
            if env.get('MLC_MLPERF_INFERENCE_CODE_VERSION', '') == "v3.1":
                env['MLC_RUN_CMD'] = "bash run_gptj_harness_v3_1.sh "
                if env.get('INTEL_GPTJ_INT4', '') == 'yes':
                    model_precision = "int4"
                    env['INT4_MODEL_DIR'] = env['MLC_ML_MODEL_PATH']
                    env['QUANTIZED_MODEL'] = os.path.join(
                        env['INT4_MODEL_DIR'], "best_int4_model.pt")
                    env['PRECISION'] = "int4_bf16_mixed"
                else:
                    env['INT8_MODEL_DIR'] = env['MLC_ML_MODEL_PATH']
                    env['QUANTIZED_MODEL'] = os.path.join(
                        env["INT8_MODEL_DIR"], "best_model.pt")
                    env['PRECISION'] = "int8"
            elif env.get('MLC_MLPERF_INFERENCE_CODE_VERSION', '') == "v4.0":
                env['MLC_RUN_CMD'] = "bash run_gptj_harness_v4_0.sh "

                if env['MLC_MLPERF_RUN_STYLE'] == "test":
                    env['TOTAL_SAMPLE_COUNT'] = env['MLC_TEST_QUERY_COUNT']
                else:
                    env['TOTAL_SAMPLE_COUNT'] = env.get(
                        'MLC_MLPERF_MAX_QUERY_COUNT', env['MLC_TEST_QUERY_COUNT'])

                if env['MLC_MLPERF_LOADGEN_SCENARIO'] == "Offline":
                    env['WORKERS_PER_PROC'] = 4
                else:
                    env['WORKERS_PER_PROC'] = 1

    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    return {'return': 0}
