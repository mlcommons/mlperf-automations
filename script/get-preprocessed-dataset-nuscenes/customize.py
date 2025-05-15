from mlc import utils
import os
import shutil


def preprocess(i):

    env = i['env']

    if env.get('MLC_NUSCENES_DATASET_TYPE', '') == "prebuilt":
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = "yes"

    return {'return': 0}


def postprocess(i):
    env = i['env']

    return {'return': 0}
