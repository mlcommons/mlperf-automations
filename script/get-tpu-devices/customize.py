from mlc import utils
import os
import re
import urllib.request


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
    # Every TPU generation from v4 on links chips with ICI, so the type is
    # "ICI" whenever at least one chip was found (we got here, so it was).
    # OCS is not reported: it cannot be detected from inside the VM and a
    # wrong value is worse than an empty one.
    #
    # The topology is not exposed by the hardware. It comes from the slice
    # metadata that Cloud TPU sets up for the VM / pod, see _tpu_slice_info().
    # An empty string means "fill in manually".
    # ------------------------------------------------------------------
    env['MLC_TPU_DEVICE_PROP_ACCELERATOR_INTERCONNECT_TYPE'] = 'ICI'

    accelerator_type, topology = _tpu_slice_info()
    if topology and accelerator_type:
        topology = f'{topology} ({accelerator_type})'
    else:
        topology = topology or accelerator_type

    # Multislice: the per-slice ICI topology above is identical on every
    # slice, so a 4-slice job would be indistinguishable from a single slice
    # of the same shape. Multislice launchers (xpk, MaxText, Pathways) export
    # MEGASCALE_NUM_SLICES; append it when it is > 1. The inter-slice fabric
    # (DCN) is host networking, not ICI, and is left to host_networking.
    num_slices = _megascale_num_slices()
    if topology and num_slices > 1:
        topology = f'{topology}, {num_slices} slices'

    env['MLC_TPU_DEVICE_PROP_ACCELERATOR_INTERCONNECT_TOPOLOGY'] = topology

    return {'return': 0}


def _megascale_num_slices():
    """Return MEGASCALE_NUM_SLICES as an int, or 1 if unset/invalid."""
    try:
        return int(os.environ.get('MEGASCALE_NUM_SLICES', '1').strip() or 1)
    except ValueError:
        return 1


_GCE_METADATA_URL = \
    'http://metadata.google.internal/computeMetadata/v1/instance/attributes/'


def _gce_metadata(key, timeout=2):
    """Return a GCE instance attribute, or "" if unavailable (non-GCE host)."""
    req = urllib.request.Request(
        _GCE_METADATA_URL + key, headers={'Metadata-Flavor': 'Google'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', 'replace').strip()
    except Exception:
        return ''


def _tpu_slice_info():
    """Return (accelerator_type, topology) for the slice this host is part of.

    Sources, in order:
      1. TPU_ACCELERATOR_TYPE / TPU_TOPOLOGY process env vars (set by GKE in
         TPU pods, and by some launchers).
      2. GCE metadata: instance/attributes/accelerator-type (e.g. "v5p-8")
         and instance/attributes/tpu-env, a KEY: 'VALUE' blob that includes
         TOPOLOGY (e.g. "2x2x1") and ACCELERATOR_TYPE.

    Never raises; missing pieces are returned as "".
    """
    accelerator_type = os.environ.get('TPU_ACCELERATOR_TYPE', '').strip()
    topology = os.environ.get('TPU_TOPOLOGY', '').strip()

    try:
        if not accelerator_type:
            accelerator_type = _gce_metadata('accelerator-type')

        if not topology or not accelerator_type:
            tpu_env = _gce_metadata('tpu-env')
            if not topology:
                topology = _tpu_env_value(tpu_env, 'TOPOLOGY')
            if not accelerator_type:
                accelerator_type = _tpu_env_value(tpu_env, 'ACCELERATOR_TYPE')
    except Exception:
        pass

    return accelerator_type, topology


def _tpu_env_value(tpu_env, key):
    """Extract KEY from a tpu-env blob of lines like: KEY: 'value'."""
    m = re.search(rf"^{key}:\s*'?([^'\n]*?)'?\s*$", tpu_env, re.M)
    return m.group(1).strip() if m else ''


