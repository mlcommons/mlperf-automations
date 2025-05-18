from mlc import utils
from utils import *
import os
import shutil


def preprocess(i):

    env = i['env']

    if is_true(str(env.get('MLC_DATASET_PREPROCESSED_BY_MLC', ''))):
        run_dir = os.getcwd()
        if is_true(env.get('MLC_DATASET_CALIBRATION', '')):
            env['MLC_DATASET_CALIBRATION_PATH'] = os.path.join(
                env['MLC_OPENORCA_PREPROCESSED_ROOT'],
                "open_orca_gpt4_tokenized_llama.calibration_1000.pkl.gz")
            env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_DATASET_CALIBRATION_PATH']
            env['MLC_DATASET_OPENORCA_CALIBRATION_PATH'] = env['MLC_DATASET_CALIBRATION_PATH']
        else:
            env['MLC_DATASET_PREPROCESSED_PATH'] = os.path.join(
                env['MLC_OPENORCA_PREPROCESSED_ROOT'],
                "open_orca_gpt4_tokenized_llama.sampled_24576.pkl.gz")
            env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_DATASET_PREPROCESSED_PATH']
            env['MLC_DATASET_OPENORCA_PREPROCESSED_PATH'] = env['MLC_DATASET_PREPROCESSED_PATH']
        # run_cmd = f"gunzip -k {env['MLC_DATASET_PREPROCESSED_PATH']}"
        run_cmd = ''
    else:
        inference_src = env['MLC_MLPERF_INFERENCE_SOURCE']
        run_dir = os.path.join(inference_src, 'language', 'llama2-70b')
        model_dir = env['MLC_ML_MODEL_PATH']
        if is_true(env.get('MLC_DATASET_CALIBRATION', '')):
            return {'return': 1, 'error': 'No raw preprocessing information is available for openorca calibration. Please use _mlcommons variation to use the MLCommons shared calibration dataset'}
        else:
            env['MLC_DATASET_PREPROCESSED_PATH'] = os.path.join(
                os.path.join(
                    os.getcwd(),
                    "processed-openorca",
                    'open_orca_gpt4_tokenized_llama.sampled_' +
                    env['MLC_DATASET_SIZE'] +
                    '.pkl'))
            run_cmd = env['MLC_PYTHON_BIN_WITH_PATH'] + ' processorca.py --dataset_pq_path=' + env['MLC_DATASET_OPENORCA_PARQUET'] + ' --model_dir=' + model_dir + \
                ' --seqlen_limit=2048 --export_dir=' + \
                os.path.join(os.getcwd(), "processed-openorca") + \
                ' --num_total_samples=' + env['MLC_DATASET_SIZE']

    env['MLC_RUN_DIR'] = run_dir
    env['MLC_RUN_CMD'] = run_cmd

    return {'return': 0}


def postprocess(i):
    env = i['env']

    return {'return': 0}
