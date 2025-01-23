from mlc import utils
import os
from os.path import exists
import shutil
import glob


def preprocess(i):

    env = i['env']
    if 'MLC_IMAGENET_PREPROCESSED_PATH' in env:
        files = glob.glob(
            env['MLC_IMAGENET_PREPROCESSED_PATH'] +
            "/**/" +
            env['MLC_IMAGENET_PREPROCESSED_FILENAME'],
            recursive=True)
        if files:
            env['MLC_DATASET_PREPROCESSED_PATH'] = env['MLC_IMAGENET_PREPROCESSED_PATH']
        else:
            return {'return': 1, 'error': 'No preprocessed images found in ' +
                    env['MLC_IMAGENET_PREPROCESSED_PATH']}
    else:
        if env.get('MLC_DATASET_REFERENCE_PREPROCESSOR', "0") == "1":
            print("Using MLCommons Inference source from '" +
                  env['MLC_MLPERF_INFERENCE_SOURCE'] + "'")

        env['MLC_DATASET_PREPROCESSED_PATH'] = os.getcwd()
        if env['MLC_DATASET_TYPE'] == "validation" and not exists(
                os.path.join(env['MLC_DATASET_PATH'], "val_map.txt")):
            shutil.copy(os.path.join(env['MLC_DATASET_AUX_PATH'], "val.txt"), os.path.join(env['MLC_DATASET_PATH'],
                                                                                           "val_map.txt"))

    preprocessed_path = env['MLC_DATASET_PREPROCESSED_PATH']

    if env.get('MLC_DATASET_TYPE', '') == "validation" and not exists(
            os.path.join(preprocessed_path, "val_map.txt")):
        shutil.copy(os.path.join(env['MLC_DATASET_AUX_PATH'], "val.txt"),
                    os.path.join(preprocessed_path, "val_map.txt"))

    if env.get('MLC_DATASET_TYPE', '') == "calibration":
        env['MLC_DATASET_IMAGES_LIST'] = env['MLC_MLPERF_IMAGENET_CALIBRATION_LIST_FILE_WITH_PATH']
        env['MLC_DATASET_SIZE'] = 500

    if env.get('MLC_DATASET_DATA_TYPE_INPUT', '') == '':
        env['MLC_DATASET_DATA_TYPE_INPUT'] = env['MLC_DATASET_DATA_TYPE']

    return {'return': 0}


def postprocess(i):

    env = i['env']

    # finalize path
    preprocessed_path = env['MLC_DATASET_PREPROCESSED_PATH']
    preprocessed_images_list = []
    preprocessed_imagenames_list = []

    match_text = "/*." + env.get("MLC_DATASET_PREPROCESSED_EXTENSION", "*")
    for filename in sorted(glob.glob(preprocessed_path + match_text)):
        preprocessed_images_list.append(filename)
        preprocessed_imagenames_list.append(os.path.basename(filename))
    with open("preprocessed_files.txt", "w") as f:
        f.write("\n".join(preprocessed_images_list))
    with open("preprocessed_filenames.txt", "w") as f:
        f.write("\n".join(preprocessed_imagenames_list))

    env['MLC_DATASET_PREPROCESSED_IMAGES_LIST'] = os.path.join(
        os.getcwd(), "preprocessed_files.txt")
    env['MLC_DATASET_PREPROCESSED_IMAGENAMES_LIST'] = os.path.join(
        os.getcwd(), "preprocessed_filenames.txt")

    return {'return': 0}
