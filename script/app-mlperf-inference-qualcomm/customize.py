from mlc import utils
from utils import is_true
import os
import shutil


def preprocess(i):

    os_info = i['os_info']

    logger = i['automation'].logger

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}
    env = i['env']

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

    kilt_root = env['MLC_KILT_CHECKOUT_PATH']

    logger.info(f"Harness Root: {kilt_root}")

    source_files = []
    env['MLC_SOURCE_FOLDER_PATH'] = env['MLC_KILT_CHECKOUT_PATH']

    env['kilt_model_root'] = env.get('MLC_ML_MODEL_FILE_WITH_PATH')

    if env.get('MLC_MLPERF_LOADGEN_BATCH_SIZE', '') != '':
        env['kilt_model_batch_size'] = env['MLC_MLPERF_LOADGEN_BATCH_SIZE']

    if env.get('MLC_QAIC_DEVICES', '') != '':
        env['kilt_device_ids'] = env['MLC_QAIC_DEVICES']

    if '+ CXXFLAGS' not in env:
        env['+ CXXFLAGS'] = []

    if '+CPLUS_INCLUDE_PATH' not in env:
        env['+CPLUS_INCLUDE_PATH'] = []

    if env['MLC_MLPERF_DEVICE'] == "qaic":
        env['kilt_model_root'] = os.path.dirname(
            env['MLC_QAIC_MODEL_COMPILED_BINARY_WITH_PATH'])

    if env.get('MLC_MODEL') == "resnet50":
        env['dataset_imagenet_preprocessed_subset_fof'] = env['MLC_DATASET_PREPROCESSED_IMAGENAMES_LIST']
        env['dataset_imagenet_preprocessed_dir'] = env['MLC_DATASET_PREPROCESSED_PATH']

    elif "bert" in env.get('MLC_MODEL'):
        env['dataset_squad_tokenized_max_seq_length'] = env['MLC_DATASET_SQUAD_TOKENIZED_MAX_SEQ_LENGTH']
        env['dataset_squad_tokenized_root'] = env['MLC_DATASET_SQUAD_TOKENIZED_ROOT']
        env['dataset_squad_tokenized_input_ids'] = os.path.basename(
            env['MLC_DATASET_SQUAD_TOKENIZED_INPUT_IDS'])
        env['dataset_squad_tokenized_input_mask'] = os.path.basename(
            env['MLC_DATASET_SQUAD_TOKENIZED_INPUT_MASK'])
        env['dataset_squad_tokenized_segment_ids'] = os.path.basename(
            env['MLC_DATASET_SQUAD_TOKENIZED_SEGMENT_IDS'])

    elif "retinanet" in env.get('MLC_MODEL'):
        env['kilt_prior_bin_path'] = os.path.join(
            kilt_root, "plugins", "nms-abp", "data")
        env['kilt_object_detection_preprocessed_subset_fof'] = os.path.basename(
            env['MLC_DATASET_PREPROCESSED_IMAGENAMES_LIST'])
        env['kilt_object_detection_preprocessed_dir'] = env['MLC_DATASET_PREPROCESSED_PATH']
        env['+ CXXFLAGS'].append("-DMODEL_RX50")
        env['+ CXXFLAGS'].append("-DSDK_1_11_X")

        loc_offset = env.get('MLC_QAIC_MODEL_RETINANET_LOC_OFFSET')
        if loc_offset:
            env['+ CXXFLAGS'].append("-DMODEL_RX50")

        keys = ['LOC_OFFSET', 'LOC_SCALE', 'CONF_OFFSET', 'CONF_SCALE']

        if is_true(env.get('MLC_RETINANET_USE_MULTIPLE_SCALES_OFFSETS', '')):
            env['+ CXXFLAGS'].append("-DUSE_MULTIPLE_SCALES_OFFSETS=1")
            for j in range(0, 4):
                keys.append(f'LOC_OFFSET{j}')
                keys.append(f'LOC_SCALE{j}')
                keys.append(f'CONF_OFFSET{j}')
                keys.append(f'CONF_SCALE{j}')

        for key in keys:
            value = env.get('MLC_QAIC_MODEL_RETINANET_' + key, '')
            if value != '':
                env['+ CXXFLAGS'].append(f" -D{key}_={value} ")

    if env.get('MLC_BENCHMARK', '') == 'NETWORK_BERT_SERVER':
        source_files.append(
            os.path.join(
                kilt_root,
                "benchmarks",
                "network",
                "bert",
                "server",
                "pack.cpp"))
        source_files.append(
            os.path.join(
                kilt_root,
                "benchmarks",
                "network",
                "bert",
                "server",
                "server.cpp"))
        env['+ CXXFLAGS'].append("-DNETWORK_DIVISION=1")
    elif env.get('MLC_BENCHMARK', '') == 'NETWORK_BERT_CLIENT':
        # source_files.append(os.path.join(kilt_root, "benchmarks", "network", "bert", "client", "pack.cpp"))
        # env['+CPLUS_INCLUDE_PATH'].append(kilt_root)
        # source_files.append(os.path.join(kilt_root, "benchmarks", "network", "bert", "client", "client.cpp"))
        env['+ CXXFLAGS'].append("-DNETWORK_DIVISION")
    elif env.get('MLC_BENCHMARK', '') == 'STANDALONE_BERT':
        source_files.append(
            os.path.join(
                kilt_root,
                "benchmarks",
                "standalone",
                "bert",
                "pack.cpp"))

    script_path = i['run_script_input']['path']
    if env['MLC_MODEL'] == "retinanet":
        env['MLC_DATASET_LIST'] = env['MLC_DATASET_ANNOTATIONS_FILE_PATH']

    for file in os.listdir(env['MLC_SOURCE_FOLDER_PATH']):
        if file.endswith(".c") or file.endswith(".cpp"):
            source_files.append(file)

    if 'SERVER' not in env.get('MLC_BENCHMARK', ''):
        source_files.append(
            os.path.join(
                kilt_root,
                "benchmarks",
                "harness",
                "harness.cpp"))

    # source_files.append(env['MLC_QAIC_API_SRC_FILE'])

    env['+CPLUS_INCLUDE_PATH'].append(kilt_root)
    env['+C_INCLUDE_PATH'].append(kilt_root)

    if env['MLC_MLPERF_DEVICE'] == 'gpu':
        env['+C_INCLUDE_PATH'].append(env['MLC_CUDA_PATH_INCLUDE'])
        env['+CPLUS_INCLUDE_PATH'].append(env['MLC_CUDA_PATH_INCLUDE'])
        env['+LD_LIBRARY_PATH'].append(env['MLC_CUDA_PATH_LIB'])
        env['+DYLD_FALLBACK_LIBRARY_PATH'].append(env['MLC_CUDA_PATH_INCLUDE'])

    elif env['MLC_MLPERF_DEVICE'] == 'qaic':
        source_files.append(
            os.path.join(
                kilt_root,
                "devices",
                "qaic",
                "api",
                "master",
                "QAicInfApi.cpp"))

    logger.info(f"Compiling the source files: {source_files}")
    env['MLC_CXX_SOURCE_FILES'] = ";".join(source_files)

    env['+ CXXFLAGS'].append("-std=c++17")
    env['+ CXXFLAGS'].append("-fpermissive")

    env['+ CXXFLAGS'].append("-DKILT_CONFIG_FROM_ENV")
    env['+ CXXFLAGS'].append("-DKILT_CONFIG_TRANSLATE_X")
    env['+ CXXFLAGS'].append("-DKILT_BENCHMARK_" + env['MLC_BENCHMARK'])
    env['+ CXXFLAGS'].append("-DKILT_DEVICE_" + env['device'].upper())

    # add preprocessor flag like "#define MLC_MODEL_RESNET50"
    # env['+ CXXFLAGS'].append('-DMLC_MODEL_' + env['MLC_MODEL'].upper())
    # add preprocessor flag like "#define MLC_MLPERF_BACKEND_ONNXRUNTIME"
    env['+ CXXFLAGS'].append('-DMLC_MLPERF_BACKEND_' +
                             env['MLC_MLPERF_BACKEND'].upper())
    # add preprocessor flag like "#define MLC_MLPERF_DEVICE_CPU"
    env['+ CXXFLAGS'].append('-DMLC_MLPERF_DEVICE_' +
                             env['MLC_MLPERF_DEVICE'].upper())

    if '+ LDCXXFLAGS' not in env:
        env['+ LDCXXFLAGS'] = []

    env['+ LDCXXFLAGS'] += [
        "-lmlperf_loadgen",
        "-lpthread",
        "-ldl"
    ]
    # e.g. -lonnxruntime
    if 'MLC_MLPERF_BACKEND_LIB_NAMESPEC' in env:
        env['+ LDCXXFLAGS'].append('-l' +
                                   env['MLC_MLPERF_BACKEND_LIB_NAMESPEC'])
    # e.g. -lcudart
    if 'MLC_MLPERF_DEVICE_LIB_NAMESPEC' in env:
        env['+ LDCXXFLAGS'].append('-l' +
                                   env['MLC_MLPERF_DEVICE_LIB_NAMESPEC'])

    if '-DPRINT_NETWORK_DESCRIPTOR' in env['+ CXXFLAGS']:
        env['+ LDCXXFLAGS'].append('-lprotobuf')

    env['MLC_LINKER_LANG'] = 'CXX'
    env['MLC_RUN_DIR'] = env.get('MLC_MLPERF_OUTPUT_DIR', os.getcwd())

    if 'MLC_MLPERF_CONF' not in env:
        env['MLC_MLPERF_CONF'] = os.path.join(
            env['MLC_MLPERF_INFERENCE_SOURCE'], "mlperf.conf")
    if 'MLC_MLPERF_USER_CONF' not in env:
        env['MLC_MLPERF_USER_CONF'] = os.path.join(
            env['MLC_MLPERF_INFERENCE_CLASSIFICATION_AND_DETECTION_PATH'], "user.conf")

    # to LOADGEN_MLPERF_CONF
    env['loadgen_mlperf_conf_path'] = env['MLC_MLPERF_CONF']
    # to LOADGEN_USER_CONF
    env['loadgen_user_conf_path'] = env['MLC_MLPERF_USER_CONF']
    env['loadgen_scenario'] = env['MLC_MLPERF_LOADGEN_SCENARIO']

    loadgen_mode = env['MLC_MLPERF_LOADGEN_MODE']
    if loadgen_mode == 'performance':
        kilt_loadgen_mode = 'PerformanceOnly'
    elif loadgen_mode == 'accuracy':
        kilt_loadgen_mode = 'AccuracyOnly'
    elif loadgen_mode == 'compliance':
        kilt_loadgen_mode = 'PerformanceOnly'
    else:
        return {'return': 1, 'error': 'Unknown loadgen mode'}
    env['loadgen_mode'] = kilt_loadgen_mode

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
