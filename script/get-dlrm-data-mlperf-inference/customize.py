from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    logger = i['automation'].logger

    dlrm_data_path = env.get(
        'MLC_DLRM_DATA_PATH', env.get(
            'DLRM_DATA_PATH', ''))
    if dlrm_data_path == '':
        logger.warning(
            f'Data path is not given as input through --dlrm_data_path. Using the cache directory:{os.getcwd()} as the data path')
        dlrm_data_path = os.getcwd()
    elif not os.path.exists(dlrm_data_path):
        return {'return': 1, 'error': "given dlrm data path does not exists"}

    # creating required folders inside the dlrm data path if not exists
    # criteo dataset
    criteo_fp32_path = os.path.join(dlrm_data_path, "criteo", "day23", "fp32")
    if not os.path.exists(criteo_fp32_path):
        os.makedirs(criteo_fp32_path)

    # dlrm model
    model_path = os.path.join(dlrm_data_path, "model")
    if not os.path.exists(model_path):
        os.makedirs(model_path)

    meta = i['meta']

    script_path = i['run_script_input']['path']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    variation = env['MLC_DLRM_DATA_VARIATION']

    if variation == "nvidia":
        if not os.path.exists(os.path.join(dlrm_data_path, "model")):
            logger.warning(
                f'model directory is missing inside {dlrm_data_path}')
            env['MLC_DLRM_MODEL_DOWNLOAD'] = True
        if not os.path.exists(os.path.join(dlrm_data_path, "criteo")):
            logger.warning(
                f'criteo directory is missing inside {dlrm_data_path}')
            env['MLC_DLRM_DATASET_DOWNLOAD'] = True
        if not os.path.exists(os.path.join(
                dlrm_data_path, "model", "model_weights")):
            logger.warning(
                f'model_weights directory is missing inside {dlrm_data_path}/model')
            env['MLC_DLRM_MODEL_DOWNLOAD'] = True
        if not os.path.exists(os.path.join(dlrm_data_path, "criteo", "day23")):
            logger.warning(
                f'day23 directory is missing inside {dlrm_data_path}/day23')
            env['MLC_DLRM_DATASET_DOWNLOAD'] = True
        if not os.path.exists(os.path.join(
                dlrm_data_path, "criteo", "day23", "fp32")):
            logger.warning(
                f'fp32 directory is missing inside {dlrm_data_path}/criteo/day23')
            env['MLC_DLRM_DATASET_DOWNLOAD'] = True
        if not os.path.exists(os.path.join(dlrm_data_path, "criteo", "day23", "fp32", "day_23_sparse_multi_hot.npz")) and not os.path.exists(
                os.path.join(dlrm_data_path, "criteo", "day23", "fp32", "day_23_sparse_multi_hot_unpacked")):
            logger.warning(
                f'day_23_sparse_multi_hot.npz or day_23_sparse_multi_hot_unpacked is missing inside {dlrm_data_path}/criteo/day23/fp32')
            env['MLC_DLRM_DATASET_DOWNLOAD'] = True
        if not os.path.exists(os.path.join(
                dlrm_data_path, "criteo", "day23", "fp32", "day_23_dense.npy")):
            logger.warning(
                f'day_23_dense.npy is missing inside {dlrm_data_path}/criteo/day23/fp32')
            env['MLC_DLRM_DATASET_DOWNLOAD'] = True
        if not os.path.exists(os.path.join(
                dlrm_data_path, "criteo", "day23", "fp32", "day_23_labels.npy")):
            logger.warning(
                f'day_23_labels.npy is missing inside {dlrm_data_path}/criteo/day23/fp32')
            env['MLC_DLRM_DATASET_DOWNLOAD'] = True
        if not os.path.exists(os.path.join(
                dlrm_data_path, "criteo", "day23", "raw_data")):
            if env.get('MLC_CRITEO_DAY23_RAW_DATA_PATH', '') == '':
                return {
                    'return': 1, 'error': 'Raw data missing inside {dlrm_data_path}/criteo/day23. Specify the target folder through input mapping(--criteo_day23_raw_data_path="path to raw criteo dataset")'}

        run_cmd = ''
        xsep = ' && '

        # addition of run command to download the datasets and model
        if is_true(env.get('MLC_DLRM_DATASET_DOWNLOAD', False)):
            run_cmd += 'cp -r "$MLC_CRITEO_PREPROCESSED_PATH"/. ' + \
                os.path.join(dlrm_data_path, "criteo", "day23", "fp32") + xsep
        if is_true(env.get('MLC_DLRM_MODEL_DOWNLOAD', False)):
            run_cmd += 'cp -r "$MLC_ML_MODEL_FILE_WITH_PATH"/. ' + \
                os.path.join(dlrm_data_path, "model") + xsep

        if not is_true(env.get('MLC_DLRM_DATASET_DOWNLOAD', '')):
            if not os.path.exists(os.path.join(
                    dlrm_data_path, "criteo", "day23", "fp32", "day_23_sparse_multi_hot_unpacked")):
                os.system(f"unzip {os.path.join(dlrm_data_path, 'criteo', 'day23', 'fp32', 'day_23_sparse_multi_hot.npz')} -d {os.path.join(dlrm_data_path, 'criteo', 'day23', 'fp32', 'day_23_sparse_multi_hot_unpacked')}")
        else:
            run_cmd += f"unzip {os.path.join(dlrm_data_path, 'criteo', 'day23', 'fp32', 'day_23_sparse_multi_hot.npz')} -d {os.path.join(dlrm_data_path, 'criteo', 'day23', 'fp32', 'day_23_sparse_multi_hot_unpacked')}" + xsep

        if os.path.exists(os.path.join(dlrm_data_path, "criteo", "day23", "fp32",
                          "day_23_sparse_multi_hot.npz")) or is_true(env['MLC_DLRM_DATASET_DOWNLOAD']):
            file_path = os.path.join(
                dlrm_data_path,
                "criteo",
                "day23",
                "fp32",
                "day_23_sparse_multi_hot.npz")
            run_cmd += ("echo {} {} | md5sum -c").format(
                'c46b7e31ec6f2f8768fa60bdfc0f6e40', file_path) + xsep

        file_path = os.path.join(
            dlrm_data_path,
            "criteo",
            "day23",
            "fp32",
            "day_23_dense.npy")
        run_cmd += ("echo {} {} | md5sum -c").format(
            'cdf7af87cbc7e9b468c0be46b1767601', file_path) + xsep

        file_path = os.path.join(
            dlrm_data_path,
            "criteo",
            "day23",
            "fp32",
            "day_23_labels.npy")
        run_cmd += ("echo {} {} | md5sum -c").format(
            'dd68f93301812026ed6f58dfb0757fa7', file_path) + xsep

        dir_path = os.path.join(dlrm_data_path, "criteo", "day23", "fp32")
        run_cmd += ("cd {}; md5sum -c {}").format(dir_path,
                                                  os.path.join(script_path, "checksums.txt"))

        env['MLC_DLRM_V2_DAY23_FILE_PATH'] = os.path.join(
            dlrm_data_path, "criteo", "day23", "raw_data")
        env['MLC_DLRM_V2_AGGREGATION_TRACE_FILE_PATH'] = os.path.join(
            dlrm_data_path, "criteo", "day23", "sample_partition.txt")

        env['MLC_RUN_CMD'] = run_cmd

    return {'return': 0}


def postprocess(i):

    env = i['env']

    if env.get('MLC_DLRM_DATA_PATH', '') == '' and env.get(
            'DLRM_DATA_PATH', '') == '':
        env['MLC_DLRM_DATA_PATH'] = os.getcwd()
    else:
        env['MLC_GET_DEPENDENT_CACHED_PATH'] = env.get(
            'MLC_DLRM_DATA_PATH', env['DLRM_DATA_PATH'])

    return {'return': 0}
