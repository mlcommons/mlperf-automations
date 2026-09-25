from mlc import utils
import os
import re
import subprocess


# Properties accepted from tmp-run.out. Anything else written by detect.py is
# ignored here, so the env surface stays exactly what parse.py consumes.
# Keep in sync with the keys detect.py emits -- see info.md.
ALLOWED_KEYS = {
    "TPU Device ID",
    "TPU Name",
    "TPU driver version",
    "libtpu version",
    "Memory Type",
    "Global memory",
    "Max clock rate",
    "Host Interconnect Type",
    "Host Interconnect Bandwidth",
}


def preprocess(i):
    env = i['env']
    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

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

            # "TPU Device ID" marks the start of a new device block.
            if key == "TPU Device ID":
                tpu_id += 1
                tpu[tpu_id] = {}

            if tpu_id < 0:
                continue

            if key not in ALLOWED_KEYS:
                continue

            tpu[tpu_id][key] = val
            p[key] = val

            key_env = 'MLC_TPU_DEVICE_PROP_' + key.upper().replace(' ', '_')

            # Host Interconnect Type
            if key_env == 'MLC_TPU_DEVICE_PROP_HOST_INTERCONNECT_TYPE':
                if val and not val.startswith('PCIe'):
                    val = 'PCIe ' + val

            env[key_env] = val

    if tpu_id < 0:
        return {'return': 1,
                'error': 'No TPU Device ID entries found in tmp-run.out'}

    state['mlc_tpu_num_devices'] = tpu_id + 1
    env['MLC_TPU_NUM_DEVICES'] = tpu_id + 1

    state['mlc_tpu_device_prop'] = p
    state['mlc_tpu_devices_prop'] = tpu

    # libtpu version is surfaced separately so that
    # get-mlperf-single-node-system-info/parse.py :: detect_inference_backend()
    # can report it as part of the software stack.
    if p.get('libtpu version'):
        env['MLC_TPU_LIBTPU_VERSION'] = p['libtpu version']

    # ------------------------------------------------------------------
    # Chip-to-chip interconnect (ICI) -- best effort, must never fail the
    # script. Mirrors the `xpu-smi topology -m` probe in
    # ../get-xpu-devices/customize.py.
    #
    # TODO(tpu): fill in the real probe. These two keys feed the MLPerf
    # `accelerator_interconnect` and `accelerator_interconnect_topology`
    # fields, so "" is an acceptable (manual-entry) result, but a wrong
    # value is not.
    #
    #   MLC_TPU_DEVICE_PROP_ACCELERATOR_INTERCONNECT_TYPE
    #       e.g. "ICI" / "ICI + OCS"
    #   MLC_TPU_DEVICE_PROP_ACCELERATOR_INTERCONNECT_TOPOLOGY
    #       e.g. "4x4x4 3D torus" or the slice type reported by the GCE
    #       metadata key instance/attributes/accelerator-type
    # ------------------------------------------------------------------
    env['MLC_TPU_DEVICE_PROP_ACCELERATOR_INTERCONNECT_TYPE'] = ''
    env['MLC_TPU_DEVICE_PROP_ACCELERATOR_INTERCONNECT_TOPOLOGY'] = ''

    return {'return': 0}
