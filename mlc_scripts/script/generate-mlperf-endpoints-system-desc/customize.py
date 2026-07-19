from mlc import utils
import json
import os


def _f(env, key, default=""):
    v = env.get(key, "")
    return v.strip() if isinstance(v, str) else v


def preprocess(i):

    env = i['env']
    logger = i['automation'].logger

    placeholders = []

    org = _f(env, 'MLC_MLPERF_ENDPOINTS_SD_ORG')
    if not org:
        org = 'MyOrg'
        placeholders.append('org')
    system_name = _f(env, 'MLC_MLPERF_ENDPOINTS_SD_SYSTEM_NAME')
    if not system_name:
        system_name = 'MySystem'
        placeholders.append('system_name')

    max_concurrency_raw = _f(env, 'MLC_MLPERF_ENDPOINTS_SD_MAX_CONCURRENCY')
    if not max_concurrency_raw:
        max_concurrency = 64
        placeholders.append('max_supported_concurrency')
    else:
        try:
            max_concurrency = int(max_concurrency_raw)
        except ValueError:
            return {'return': 1,
                    'error': f'max_supported_concurrency must be an integer, '
                    f'got {max_concurrency_raw!r}'}
    if max_concurrency <= 32:
        return {'return': 1,
                'error': 'max_supported_concurrency must be > 32 (it defines the '
                f'concurrency regions); got {max_concurrency}.'}

    sd = {
        'submitter_org_names': org,
        'system_name': system_name,
        'system_category': _f(env, 'MLC_MLPERF_ENDPOINTS_SD_SYSTEM_CATEGORY')
        or 'datacenter',
        'system_availability_status': _f(
            env, 'MLC_MLPERF_ENDPOINTS_SD_AVAILABILITY') or 'available',
        'division': _f(env, 'MLC_MLPERF_ENDPOINTS_SD_DIVISION') or 'standardized',
        'max_supported_concurrency': max_concurrency,
    }

    contact = _f(env, 'MLC_MLPERF_ENDPOINTS_SD_CONTACT')
    if contact:
        sd['submitter_contact'] = contact
    for key, field in [
        ('MLC_MLPERF_ENDPOINTS_SD_SERVING_FRAMEWORK', 'serving_framework'),
        ('MLC_MLPERF_ENDPOINTS_SD_MODEL_NAME', 'model_name'),
        ('MLC_MLPERF_ENDPOINTS_SD_MODEL_PRECISION', 'model_precision'),
        ('MLC_MLPERF_ENDPOINTS_SD_DATASET_NAME', 'dataset_name'),
    ]:
        val = _f(env, key)
        if val:
            sd[field] = val

    # Single node_type entry from the provided hardware/software fields.
    node = {}
    int_fields = {
        'MLC_MLPERF_ENDPOINTS_SD_NUMBER_OF_NODES': 'number_of_nodes',
        'MLC_MLPERF_ENDPOINTS_SD_ACCELERATORS_PER_NODE': 'accelerators_per_node',
    }
    str_fields = {
        'MLC_MLPERF_ENDPOINTS_SD_ACCELERATOR_MODEL': 'accelerator_model_name',
        'MLC_MLPERF_ENDPOINTS_SD_HOST_PROCESSOR': 'host_processor_model_name',
        'MLC_MLPERF_ENDPOINTS_SD_INFERENCE_BACKEND': 'inference_backend',
        'MLC_MLPERF_ENDPOINTS_SD_OS': 'operating_system',
        'MLC_MLPERF_ENDPOINTS_SD_DRIVER': 'driver',
    }
    for key, field in int_fields.items():
        val = _f(env, key)
        if val:
            try:
                node[field] = int(val)
            except ValueError:
                return {'return': 1,
                        'error': f'{field} must be an integer, got {val!r}'}
    for key, field in str_fields.items():
        val = _f(env, key)
        if val:
            node[field] = val
    if not node:
        node = {'number_of_nodes': 1}
        placeholders.append('node_types (hardware details)')
    sd['node_types'] = [node]

    out_path = _f(env, 'MLC_MLPERF_ENDPOINTS_SYSTEM_DESC_PATH')
    if not out_path:
        out_path = os.path.join(os.getcwd(), 'system_desc.json')
    out_path = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(sd, f, indent=2)
    env['MLC_MLPERF_ENDPOINTS_SYSTEM_DESC_PATH'] = out_path

    logger.info('')
    logger.info(f'Generated system description at: {out_path}')
    if placeholders:
        logger.warning(
            'Placeholder values were used for: ' + ', '.join(placeholders) +
            '. Override them with the matching inputs before a real submission.')
    logger.info('')

    return {'return': 0}


def postprocess(i):
    return {'return': 0}
