from mlc import utils
import os
from utils import is_true

def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    if env.get('MLC_DATASET_SQUAD_CALIBRATION_SET', '') == "one":
        env['DATASET_CALIBRATION_FILE'] = os.path.join(
            env['MLC_MLPERF_INFERENCE_SOURCE'],
            'calibration',
            'SQuAD-v1.1',
            'bert_calibration_features.txt')
        env['DATASET_CALIBRATION_ID'] = 1
    elif env.get('MLC_DATASET_SQUAD_CALIBRATION_SET', '') == "two":
        env['DATASET_CALIBRATION_FILE'] = os.path.join(
            env['MLC_MLPERF_INFERENCE_SOURCE'],
            'calibration',
            'SQuAD-v1.1',
            'bert_calibration_qas_ids.txt')
        env['DATASET_CALIBRATION_ID'] = 2
    else:
        env['DATASET_CALIBRATION_FILE'] = "''"
        env['DATASET_CALIBRATION_ID'] = 0

    env['CK_ENV_MLPERF_INFERENCE'] = env['MLC_MLPERF_INFERENCE_SOURCE']

    if is_true(env.get('MLC_DATASET_SQUAD_PACKED', '')):
        i['run_script_input']['script_name'] = "run-packed"
        if env.get('+PYTHONPATH', '') == '':
            env['+PYTHONPATH'] = []

    env['+PYTHONPATH'].append(env['MLC_MLPERF_INFERENCE_BERT_PATH'])

    return {'return': 0}


def postprocess(i):

    env = i['env']
    cur = os.getcwd()

    if not is_true(env.get('MLC_DATASET_SQUAD_PACKED', '')):
        env['MLC_DATASET_SQUAD_TOKENIZED_ROOT'] = cur
        if is_true(env.get('MLC_DATASET_RAW', '')):
            env['MLC_DATASET_SQUAD_TOKENIZED_INPUT_IDS'] = os.path.join(
                cur, 'bert_tokenized_squad_v1_1_input_ids.raw')
            env['MLC_DATASET_SQUAD_TOKENIZED_SEGMENT_IDS'] = os.path.join(
                cur, 'bert_tokenized_squad_v1_1_segment_ids.raw')
            env['MLC_DATASET_SQUAD_TOKENIZED_INPUT_MASK'] = os.path.join(
                cur, 'bert_tokenized_squad_v1_1_input_mask.raw')
        else:
            env['MLC_DATASET_SQUAD_TOKENIZED_PICKLE_FILE'] = os.path.join(
                cur, 'bert_tokenized_squad_v1_1.pickle')

        env['MLC_DATASET_SQUAD_TOKENIZED_MAX_SEQ_LENGTH'] = env['MLC_DATASET_MAX_SEQ_LENGTH']
        env['MLC_DATASET_SQUAD_TOKENIZED_DOC_STRIDE'] = env['MLC_DATASET_DOC_STRIDE']
        env['MLC_DATASET_SQUAD_TOKENIZED_MAX_QUERY_LENGTH'] = env['MLC_DATASET_MAX_QUERY_LENGTH']

    else:
        with open("packed_filenames.txt", "w") as f:
            for dirname in os.listdir(cur):
                if os.path.isdir(dirname) and not dirname.startswith("_"):
                    f.write(
                        os.path.join(
                            cur,
                            dirname,
                            "input_ids.raw") +
                        "," +
                        os.path.join(
                            cur,
                            dirname,
                            "input_mask.raw") +
                        "," +
                        os.path.join(
                            cur,
                            dirname,
                            "segment_ids.raw") +
                        "," +
                        os.path.join(
                            cur,
                            dirname,
                            "input_position_ids.raw") +
                        "\n")
        env['MLC_DATASET_SQUAD_TOKENIZED_PACKED_FILENAMES_FILE'] = os.path.join(
            cur, "packed_filenames.txt")

    return {'return': 0}
