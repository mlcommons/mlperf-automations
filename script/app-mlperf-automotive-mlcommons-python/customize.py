from mlc import utils
from utils import is_true
import os
import json
import shutil
import subprocess


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    state = i['state']
    script_path = i['run_script_input']['path']

    logger = i['automation'].logger

    if is_true(env.get('MLC_MLPERF_SKIP_RUN', '')):
        return {'return': 0}

    if is_true(env.get('MLC_RUN_DOCKER_CONTAINER', '')):
        return {'return': 0}

    if is_true(env.get('MLC_MLPERF_POWER', '')):
        power = "yes"
    else:
        power = "no"

    rerun = True if env.get("MLC_RERUN", "") != '' else False

    if 'MLC_MLPERF_LOADGEN_SCENARIO' not in env:
        env['MLC_MLPERF_LOADGEN_SCENARIO'] = "Offline"

    if 'MLC_MLPERF_LOADGEN_MODE' not in env:
        env['MLC_MLPERF_LOADGEN_MODE'] = "accuracy"

    if 'MLC_MODEL' not in env:
        return {
            'return': 1, 'error': "Please select a variation specifying the model to run"}

    # if env['MLC_MODEL'] == "resnet50":
    #    cmd = "cp " + os.path.join(env['MLC_DATASET_AUX_PATH'], "val.txt") + " " + os.path.join(env['MLC_DATASET_PATH'],
    #    "val_map.txt")
    #    ret = os.system(cmd)

    env['MLC_MLPERF_LOADGEN_EXTRA_OPTIONS'] = " " + \
        env.get('MLC_MLPERF_LOADGEN_EXTRA_OPTIONS', '') + " "

    if 'MLC_MLPERF_LOADGEN_QPS' not in env:
        env['MLC_MLPERF_LOADGEN_QPS_OPT'] = ""
    else:
        env['MLC_MLPERF_LOADGEN_QPS_OPT'] = " --qps " + \
            env['MLC_MLPERF_LOADGEN_QPS']

    env['MLC_MLPERF_LOADGEN_EXTRA_OPTIONS'] += env['MLC_MLPERF_LOADGEN_QPS_OPT']

    if 'MLC_NUM_THREADS' not in env:
        if 'MLC_MINIMIZE_THREADS' in env:
            env['MLC_NUM_THREADS'] = str(int(env['MLC_HOST_CPU_TOTAL_CORES']) //
                                         (int(env.get('MLC_HOST_CPU_SOCKETS', '1')) * int(env.get('MLC_HOST_CPU_TOTAL_CORES', '1'))))
        else:
            env['MLC_NUM_THREADS'] = env.get('MLC_HOST_CPU_TOTAL_CORES', '1')

    if env.get('MLC_MLPERF_LOADGEN_MAX_BATCHSIZE', '') != '' and not env.get(
            'MLC_MLPERF_MODEL_SKIP_BATCHING', False):
        env['MLC_MLPERF_LOADGEN_EXTRA_OPTIONS'] += " --max-batchsize " + \
            str(env['MLC_MLPERF_LOADGEN_MAX_BATCHSIZE'])

    if env.get('MLC_MLPERF_LOADGEN_BATCH_SIZE', '') != '':
        env['MLC_MLPERF_LOADGEN_EXTRA_OPTIONS'] += " --batch-size " + \
            str(env['MLC_MLPERF_LOADGEN_BATCH_SIZE'])

    if env.get('MLC_MLPERF_LOADGEN_QUERY_COUNT', '') != '' and not env.get(
            'MLC_TMP_IGNORE_MLPERF_QUERY_COUNT', False) and env.get('MLC_MLPERF_RUN_STYLE', '') != "valid":
        env['MLC_MLPERF_LOADGEN_EXTRA_OPTIONS'] += " --count " + \
            env['MLC_MLPERF_LOADGEN_QUERY_COUNT']

    print("Using MLCommons Inference source from '" +
          env['MLC_MLPERF_INFERENCE_SOURCE'] + "'")

    env['MODEL_DIR'] = env.get('MLC_ML_MODEL_PATH')
    if not env['MODEL_DIR']:
        env['MODEL_DIR'] = os.path.dirname(
            env.get(
                'MLC_MLPERF_CUSTOM_MODEL_PATH',
                env.get('MLC_ML_MODEL_FILE_WITH_PATH')))

    RUN_CMD = ""

    scenario = env['MLC_MLPERF_LOADGEN_SCENARIO']
    scenario_extra_options = ''

    NUM_THREADS = env['MLC_NUM_THREADS']
    if int(NUM_THREADS) > 2 and env['MLC_MLPERF_DEVICE'] == "gpu":
        NUM_THREADS = "2"  # Don't use more than 2 threads when run on GPU

    if env['MLC_MODEL'] in ['resnet50', 'retinanet', 'stable-diffusion-xl']:
        scenario_extra_options += " --threads " + NUM_THREADS

    ml_model_name = env['MLC_MODEL']
    if 'MLC_MLPERF_USER_CONF' in env:
        user_conf_path = env['MLC_MLPERF_USER_CONF']
        x = "" if os_info['platform'] == 'windows' else "'"
        scenario_extra_options += " --user_conf " + x + user_conf_path + x

    mode = env['MLC_MLPERF_LOADGEN_MODE']
    mode_extra_options = ""

    # Grigori blocked for ABTF to preprocess data set on the fly for now
    # we can later move it to a separate script to preprocess data set

#    if 'MLC_DATASET_PREPROCESSED_PATH' in env and env['MLC_MODEL'] in  [ 'resnet50', 'retinanet' ]:
#        #dataset_options = " --use_preprocessed_dataset --preprocessed_dir "+env['MLC_DATASET_PREPROCESSED_PATH']
#        if env.get('MLC_MLPERF_LAST_RELEASE') not in [ "v2.0", "v2.1" ]:
#            dataset_options = " --use_preprocessed_dataset --cache_dir "+env['MLC_DATASET_PREPROCESSED_PATH']
#        else:
#            dataset_options = ""
#        if env['MLC_MODEL'] == "retinanet":
#            dataset_options += " --dataset-list "+ env['MLC_DATASET_ANNOTATIONS_FILE_PATH']
#        elif env['MLC_MODEL'] == "resnet50":
#            dataset_options += " --dataset-list "+ os.path.join(env['MLC_DATASET_AUX_PATH'], "val.txt")
#        env['DATA_DIR'] = env.get('MLC_DATASET_PREPROCESSED_PATH')
#    else:
#        if 'MLC_DATASET_PREPROCESSED_PATH' in env:
#            env['DATA_DIR'] = env.get('MLC_DATASET_PREPROCESSED_PATH')
#        else:
#            env['DATA_DIR'] = env.get('MLC_DATASET_PATH')
#        dataset_options = ''

    # Grigori added for ABTF
#    dataset_path = env.get('MLC_DATASET_PATH')
#    env['DATA_DIR'] = dataset_path

#    dataset_options = " --dataset-list " + env['MLC_DATASET_ANNOTATIONS_FILE_PATH']
#    dataset_options += " --cache_dir " + os.path.join(script_path, 'preprocessed-dataset')

    dataset_options = ''

    if env.get('MLC_MLPERF_EXTRA_DATASET_ARGS', '') != '':
        dataset_options += " " + env['MLC_MLPERF_EXTRA_DATASET_ARGS']

    if mode == "accuracy":
        mode_extra_options += " --accuracy"
        if env.get('MLC_MODEL', '') == "retinanet":
            env['MLC_OUTPUT_PREDICTIONS_PATH'] = os.path.join(
                env['MLC_DATASET_MLCOMMONS_COGNATA_PATH'],
                env['MLC_DATASET_MLCOMMONS_COGNATA_SERIAL_NUMBERS'],
                'Cognata_Camera_01_8M_png',
                'output')

    elif mode == "performance":
        pass

    elif mode == "compliance":

        audit_full_path = env['MLC_MLPERF_INFERENCE_AUDIT_PATH']
        mode_extra_options = " --audit '" + audit_full_path + "'"

    if env.get('MLC_MLPERF_OUTPUT_DIR', '') == '':
        env['MLC_MLPERF_OUTPUT_DIR'] = os.getcwd()

    mlperf_implementation = env.get('MLC_MLPERF_IMPLEMENTATION', 'reference')

    # Generate CMD

    # Grigori updated for ABTF demo
#    cmd, run_dir = get_run_cmd(os_info, env, scenario_extra_options, mode_extra_options, dataset_options, mlperf_implementation)
    cmd, run_dir = get_run_cmd_reference(
        os_info, env, scenario_extra_options, mode_extra_options, dataset_options, logger, script_path)

    if env.get('MLC_NETWORK_LOADGEN', '') == "lon":

        run_cmd = i['state']['mlperf_inference_run_cmd']
        env['MLC_SSH_RUN_COMMANDS'] = []
        env['MLC_SSH_RUN_COMMANDS'].append(
            run_cmd.replace(
                "--network=lon",
                "--network=sut") + " &")

    env['MLC_MLPERF_RUN_CMD'] = cmd
    env['MLC_RUN_DIR'] = run_dir
    env['MLC_RUN_CMD'] = cmd
    env['CK_PROGRAM_TMP_DIR'] = env.get('MLC_ML_MODEL_PATH')  # for tvm

    if env.get('MLC_HOST_PLATFORM_FLAVOR', '') == "arm64":
        env['MLC_HOST_PLATFORM_FLAVOR'] = "aarch64"

    if env.get('MLC_MODEL', '') == "retinanet":
        if not env.get('MLC_COGNATA_ACCURACY_DUMP_FILE'):
            env['MLC_COGNATA_ACCURACY_DUMP_FILE'] = os.path.join(
                env['OUTPUT_DIR'], "accuracy.txt")

    return {'return': 0}


def get_run_cmd_reference(os_info, env, scenario_extra_options,
                          mode_extra_options, dataset_options, logger, script_path=None):

    q = '"' if os_info['platform'] == 'windows' else "'"

    ##########################################################################
    # Grigori added for ABTF demo

    if env['MLC_MODEL'] in ['retinanet']:

        run_dir = os.path.join(script_path, 'ref')

        env['RUN_DIR'] = run_dir

        env['OUTPUT_DIR'] = env['MLC_MLPERF_OUTPUT_DIR']

        cognata_dataset_path = env['MLC_DATASET_MLCOMMONS_COGNATA_PATH']
# cognata_dataset_path = env['MLC_DATASET_PATH'] # Using open images
# dataset for some tests

        path_to_model = env.get(
            'MLC_MLPERF_CUSTOM_MODEL_PATH',
            env.get(
                'MLC_ML_MODEL_FILE_WITH_PATH',
                env.get('MLC_ML_MODEL_CODE_WITH_PATH')))
        env['MODEL_FILE'] = path_to_model

        cmd = env['MLC_PYTHON_BIN_WITH_PATH'] + " " + os.path.join(run_dir, "python", "main.py") + " --profile " + env['MLC_MODEL'] + "-" + env['MLC_MLPERF_BACKEND'] + \
            " --model=" + q + path_to_model + q + \
            " --dataset=" + env["MLC_MLPERF_VISION_DATASET_OPTION"] + \
            " --dataset-path=" + q + cognata_dataset_path + q + \
            " --cache_dir=" + q + os.path.join(script_path, 'tmp-preprocessed-dataset') + q + \
            " --scenario " + env['MLC_MLPERF_LOADGEN_SCENARIO'] + " " + \
            " --output " + q + env['OUTPUT_DIR'] + q + " " + \
            env['MLC_MLPERF_LOADGEN_EXTRA_OPTIONS'] + \
            scenario_extra_options + mode_extra_options + dataset_options

    elif env['MLC_MODEL'] in ['bevformer']:
        run_dir = env['MLC_MLPERF_AUTOMOTIVE_BEVFORMER_PATH']

        env['RUN_DIR'] = run_dir

        env['OUTPUT_DIR'] = env['MLC_MLPERF_OUTPUT_DIR']

        if env['MLC_MLPERF_BACKEND'] != "onnxruntime":
            logger.warning(
                "Unsupported backend {MLC_MLPERF_BACKEND}, defaulting to onnx")
            env['MLC_MLPERF_BACKEND'] = "onnx"

        config_path = os.path.join(
            run_dir,
            "projects",
            "configs",
            "bevformer",
            "bevformer_tiny.py")
        print(env['MLC_MLPERF_LOADGEN_EXTRA_OPTIONS'])
        cmd = f"""{env['MLC_PYTHON_BIN_WITH_PATH']} {os.path.join(run_dir, "main.py")} --output {env['OUTPUT_DIR']} --scenario {env['MLC_MLPERF_LOADGEN_SCENARIO']} --backend onnx --dataset nuscenes --nuscenes-root {os.path.dirname(env['MLC_PREPROCESSED_DATASET_NUSCENES_PATH'].rstrip("/"))} --dataset-path {env['MLC_PREPROCESSED_DATASET_NUSCENES_PATH']} --checkpoint {env['MLC_ML_MODEL_BEVFORMER_PATH']} --config {config_path} {env['MLC_MLPERF_LOADGEN_EXTRA_OPTIONS']} {scenario_extra_options} {mode_extra_options} {dataset_options}"""
        print(cmd)
    elif env['MLC_MODEL'] in ['ssd-resnet50']:
        run_dir = env['MLC_MLPERF_AUTOMOTIVE_SSD_RESNET50_PATH']

        env['RUN_DIR'] = run_dir

        env['OUTPUT_DIR'] = env['MLC_MLPERF_OUTPUT_DIR']

        backend = "onnx" if env.get(
            'MLC_MLPERF_BACKEND') == "onnxruntime" else env.get('MLC_MLPERF_BACKEND')

        config_path = "baseline_8MP_ss_scales_fm1_5x5_all"

        cmd = f"""{env['MLC_PYTHON_BIN_WITH_PATH']} {os.path.join(run_dir, "main.py")} --output {env['OUTPUT_DIR']} --scenario {env['MLC_MLPERF_LOADGEN_SCENARIO']} --backend {backend} --dataset cognata --dataset-path {env['MLC_PREPROCESSED_DATASET_COGNATA_PATH']} --checkpoint {env['MLC_ML_MODEL_SSD_PATH']} --config {config_path} {env['MLC_MLPERF_LOADGEN_EXTRA_OPTIONS']} {scenario_extra_options} {mode_extra_options} {dataset_options}"""

    elif env['MLC_MODEL'] in ['deeplab_v3+']:
        run_dir = env['MLC_MLPERF_AUTOMOTIVE_DEEPLABV3PLUS_PATH']

        env['RUN_DIR'] = run_dir

        env['OUTPUT_DIR'] = env['MLC_MLPERF_OUTPUT_DIR']

        backend = "onnx" if env.get(
            'MLC_MLPERF_BACKEND') == "onnxruntime" else env.get('MLC_MLPERF_BACKEND')

        cmd = f"""{env['MLC_PYTHON_BIN_WITH_PATH']} {os.path.join(run_dir, "main.py")} --output {env['OUTPUT_DIR']} --scenario {env['MLC_MLPERF_LOADGEN_SCENARIO']} --backend {backend} --dataset cognata --dataset-path {env['MLC_PREPROCESSED_DATASET_COGNATA_PATH']} --checkpoint {env['MLC_ML_MODEL_DEEPLABV3_PLUS_PATH']} --config {config_path} {env['MLC_MLPERF_LOADGEN_EXTRA_OPTIONS']} {scenario_extra_options} {mode_extra_options} {dataset_options}"""

    ##########################################################################

    return cmd, run_dir


def postprocess(i):

    env = i['env']

    state = i['state']

    inp = i['input']

    return {'return': 0}