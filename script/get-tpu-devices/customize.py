from mlc import utils
import os


def preprocess(i):
    env = i['env']
    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    tmp_run_out = os.path.join(
        env.get('MLC_TMP_CURRENT_PATH', '.'), 'tmp-run.out')

    r = utils.load_txt(file_name=tmp_run_out,
                       check_if_exists=True,
                       split=True)
    if r['return'] > 0:
        return r

    lst = r['list']

    # properties
    p = {}
    tpu = {}

    tpu_id = -1

    for line in lst:
        j = line.find(':')

        if j >= 0:
            key = line[:j].strip()
            val = line[j + 1:].strip()

            if key == "TPU Device ID":
                tpu_id += 1
                tpu[tpu_id] = {}

            if tpu_id < 0:
                continue

            tpu[tpu_id][key] = val
            p[key] = val

            # Named after the CUDA/ROCm/XPU keys (..._GPU_NAME,
            # ..._GPU_INTERCONNECT_TYPE) so parse.py reads all four alike.
            if key.startswith('TPU '):
                key = 'GPU ' + key[len('TPU '):]
            key_env = 'MLC_TPU_DEVICE_PROP_' + key.upper().replace(' ', '_')

            env[key_env] = val

    if tpu_id < 0:
        return {'return': 1,
                'error': 'No TPU Device ID entries found in tmp-run.out'}

    state['mlc_tpu_num_devices'] = tpu_id + 1
    env['MLC_TPU_NUM_DEVICES'] = tpu_id + 1

    state['mlc_tpu_device_prop'] = p
    state['mlc_tpu_devices_prop'] = tpu

    return {'return': 0}
