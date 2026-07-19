from mlc import utils
import os
import shutil


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if os_info['platform'] == "windows":
        return {'return': 1, 'error': 'Script not supported in windows yet!'}

    if env.get('MLC_DATASET_WHISPER_PATH', '') != '':
        return {'return': 0}

    if env.get('MLC_TMP_DATASET_TYPE', '') == "preprocessed":
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = "yes"
    else:
        cwd = env.get('MLC_OUTDIRNAME', os.getcwd())
        data_dir = os.path.join(cwd, 'data')
        librispeech_dir = os.path.join(data_dir, 'LibriSpeech')
        utils_dir = os.path.join(
            env['MLC_MLPERF_INFERENCE_SOURCE'],
            'speech2text',
            'utils')

        # create directories if not exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(librispeech_dir, exist_ok=True)

        env['MLC_TMP_DATA_DIR'] = data_dir
        env['MLC_TMP_LIBRISPEECH_DIR'] = librispeech_dir
        env['MLC_TMP_UTILS_DIR'] = utils_dir
        env['MLC_DATASET_WHISPER_PATH'] = data_dir

    return {'return': 0}


def postprocess(i):

    env = i['env']

    if env.get('MLC_DOWNLOAD_MODE', '') != "dry":
        if env.get('MLC_TMP_DATASET_TYPE', '') != "preprocessed":
            cwd = env.get('MLC_OUTDIRNAME', os.getcwd())
            data_dir = os.path.join(cwd, 'data')
            env['MLC_DATASET_WHISPER_PATH'] = data_dir
        else:
            # copy files to data folder
            tmp_src_dir = env["MLC_DATASET_WHISPER_PATH"]
            tmp_dest_dir = os.path.join(tmp_src_dir, "data")

            os.makedirs(tmp_dest_dir, exist_ok=True)

            items_to_copy = [
                "LibriSpeech",
                "dev-all",
                "dev-all-repack",
                "dev-all-repack.json"
            ]

            for item in items_to_copy:
                src_path = os.path.join(tmp_src_dir, item)
                dst_path = os.path.join(tmp_dest_dir, item)
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                elif os.path.isfile(src_path):
                    shutil.copy2(src_path, dst_path)

    return {'return': 0}
