from mlc import utils
import os
import shutil
from utils import is_true, is_false


def preprocess(i):

    env = i['env']

    print("Using MLCommons Inference source from '" +
          env['MLC_MLPERF_INFERENCE_SOURCE'] + "'")

    run_dir = os.path.join(
        env['MLC_MLPERF_INFERENCE_SOURCE'],
        "text_to_image",
        "tools")

    env['MLC_RUN_DIR'] = run_dir

    return {'return': 0}


def postprocess(i):
    logger = i["automation"].logger
    env = i['env']
    if is_true(env.get('MLC_GENERATE_SAMPLE_ID', '')):
        env['MLC_COCO2014_SAMPLE_ID_PATH'] = os.path.join(
            os.getcwd(), 'sample_ids.txt')
        print(env['MLC_COCO2014_SAMPLE_ID_PATH'])
    if is_false(env.get('MLC_DATASET_CALIBRATION', '')):
        env['MLC_DATASET_PATH_ROOT'] = os.getcwd()
        # env['MLC_DATASET_PATH'] = os.path.join(os.getcwd(), 'install', 'validation', 'data')
        env['MLC_DATASET_CAPTIONS_DIR_PATH'] = os.path.join(
            os.getcwd(), 'captions')
        env['MLC_DATASET_LATENTS_DIR_PATH'] = os.path.join(
            os.getcwd(), 'latents')
    else:
        env['MLC_CALIBRATION_DATASET_PATH'] = os.path.join(
            os.getcwd(), 'calibration', 'data')

    return {'return': 0}
