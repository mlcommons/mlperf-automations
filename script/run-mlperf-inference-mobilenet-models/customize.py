from mlc import utils
import os
import sys
from utils import *
import mlc
import importlib


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    add_deps_recursive = i['input'].get('add_deps_recursive')

    adr = i['input'].get('adr')

    automation = i['automation']
    # mlc = i['automation'].action_object
    # cache_action = i['automation'].cache_action
    cache_action = mlc

    quiet = (env.get('MLC_QUIET', False) == 'yes')
    verbose = (env.get('MLC_VERBOSE', False) == 'yes')

    models_all = {
        "mobilenet": {
            "v1": {
                "multiplier": ["multiplier-1.0", "multiplier-0.75", "multiplier-0.5", "multiplier-0.25"],
                "resolution": ["resolution-224", "resolution-192", "resolution-160", "resolution-128"],
                "kind": [""]
            },
            "v2": {
                "multiplier": ["multiplier-1.0", "multiplier-0.75", "multiplier-0.5", "multiplier-0.35"],
                "resolution": ["resolution-224", "resolution-192", "resolution-160", "resolution-128"],
                "kind": [""]
            },
            "v3": {
                "multiplier": [""],
                "resolution": [""],
                "kind": ["large", "large-minimalistic", "small", "small-minimalistic"]
            }
        },
        "efficientnet": {
            "": {
                "multiplier": [""],
                "resolution": [""],
                "kind": ["lite0", "lite1", "lite2", "lite3", "lite4"]
            }
        }
    }

    models = {}
    if is_true(env.get('MLC_MLPERF_RUN_MOBILENET_V1', '')):
        models['mobilenet'] = {}
        models['mobilenet']['v1'] = models_all['mobilenet']['v1']
    elif is_true(env.get('MLC_MLPERF_RUN_MOBILENET_V2', '')):
        models['mobilenet'] = {}
        models['mobilenet']['v2'] = models_all['mobilenet']['v2']
    elif is_true(env.get('MLC_MLPERF_RUN_MOBILENET_V3', '')):
        models['mobilenet'] = {}
        models['mobilenet']['v3'] = models_all['mobilenet']['v3']
    elif is_true(env.get('MLC_MLPERF_RUN_MOBILENETS', '')):
        models['mobilenet'] = models_all['mobilenet']
    if is_true(env.get('MLC_MLPERF_RUN_EFFICIENTNETS', '')):
        models['efficientnet'] = models_all['efficientnet']

    variation_strings = {}
    for t1 in models:
        variation_strings[t1] = []
        variation_list = []
        variation_list.append(t1)
        for version in models[t1]:
            variation_list = []
            if version.strip():
                variation_list.append("_" + version)
            variation_list_saved = variation_list.copy()
            for k1 in models[t1][version]["multiplier"]:
                variation_list = variation_list_saved.copy()
                if k1.strip():
                    variation_list.append("_" + k1)
                variation_list_saved_2 = variation_list.copy()
                for k2 in models[t1][version]["resolution"]:
                    variation_list = variation_list_saved_2.copy()
                    if k2.strip():
                        variation_list.append("_" + k2)
                    variation_list_saved_3 = variation_list.copy()
                    for k3 in models[t1][version]["kind"]:
                        variation_list = variation_list_saved_3.copy()
                        if k3.strip():
                            variation_list.append("_" + k3)
                        variation_strings[t1].append(",".join(variation_list))

    if is_true(env.get('MLC_MLPERF_SUBMISSION_MODE', '')):
        var = "_submission"
        execution_mode = "valid"
    elif is_true(env.get('MLC_MLPERF_ACCURACY_MODE', '')) and is_true(env.get('MLC_MLPERF_PERFORMANCE_MODE', '')):
        var = "_full,_performance-and-accuracy"
        execution_mode = "valid"
    elif is_true(env.get('MLC_MLPERF_ACCURACY_MODE', '')):
        var = "_full,_accuracy-only"
        execution_mode = "valid"
    elif is_true(env.get('MLC_MLPERF_PERFORMANCE_MODE', '')):
        var = "_full,_performance-only"
        execution_mode = "valid"
    else:
        var = "_find-performance"
        execution_mode = "test"

    precisions = []
    if is_true(env.get('MLC_MLPERF_RUN_FP32', '')):
        precisions.append("fp32")
    if is_true(env.get('MLC_MLPERF_RUN_INT8', '')):
        precisions.append("uint8")

    implementation_tags = []
    if is_true(env.get('MLC_MLPERF_USE_ARMNN_LIBRARY', '')):
        implementation_tags.append("_armnn")
    if is_true(env.get('MLC_MLPERF_TFLITE_ARMNN_NEON', '')):
        implementation_tags.append("_use-neon")
    if is_true(env.get('MLC_MLPERF_TFLITE_ARMNN_OPENCL', '')):
        implementation_tags.append("_use-opencl")
    implementation_tags_string = ",".join(implementation_tags)

    inp = i['input']
    clean_input = {
        'action': 'rm',
        'target': 'cache',
        'tags': 'get,preprocessed,dataset,_for.mobilenet',
        'quiet': True,
        'v': verbose,
        'f': True
    }

    for precision in precisions:
        for model in variation_strings:
            for v in variation_strings[model]:

                if "small-minimalistic" in v and precision == "uint8":
                    continue

                if model == "efficientnet" and precision == "uint8":
                    precision = "int8"

                mlc_input = {
                    'action': 'run',
                    'target': 'script',
                    'tags': f'run-mlperf,mlperf,inference,{var}',
                    'quiet': True,
                    'env': env,
                    'input': inp,
                    'v': verbose,
                    'implementation': 'tflite-cpp',
                    'precision': precision,
                    'model': model,
                    'scenario': 'SingleStream',
                    'execution_mode': execution_mode,
                    'test_query_count': '100',
                    'adr': {
                        'tflite-model': {
                            'tags': v
                        },
                        'mlperf-inference-implementation': {
                            'tags': implementation_tags_string
                        }
                    }
                }
                if add_deps_recursive:
                    # script automation will merge adr and add_deps_recursive
                    mlc_input['add_deps_recursive'] = add_deps_recursive

                if adr:
                    utils.merge_dicts(
                        {'dict1': mlc_input['adr'], 'dict2': adr, 'append_lists': True, 'append_unique': True})

                if env.get('MLC_MLPERF_INFERENCE_RESULTS_DIR', '') != '':
                    mlc_input['results_dir'] = env['MLC_MLPERF_INFERENCE_RESULTS_DIR']

                if env.get('MLC_MLPERF_INFERENCE_SUBMISSION_DIR', '') != '':
                    mlc_input['submission_dir'] = env['MLC_MLPERF_INFERENCE_SUBMISSION_DIR']

                if is_true(env.get('MLC_MLPERF_FIND_PERFORMANCE_MODE', '')) and not is_true(env.get(
                        'MLC_MLPERF_NO_RERUN', '')):
                    mlc_input['rerun'] = True

                if is_true(env.get('MLC_MLPERF_POWER', '')):
                    mlc_input['power'] = 'yes'

                print(mlc_input)
                r = mlc.access(mlc_input)
                if r['return'] > 0:
                    return r
                importlib.reload(mlc.action)

                if is_true(env.get('MLC_MINIMIZE_DISK_SPACE', '')):
                    r = cache_action.access(clean_input)
                    if r['return'] > 0:
                        print(r)
                    #    return r
                    else:
                        importlib.reload(mlc.action)

                if is_true(env.get('MLC_TEST_ONE_RUN', '')):
                    return {'return': 0}

            r = cache_action.access(clean_input)
            if r['return'] > 0:
                print(r)
                #    return r
            else:
                importlib.reload(mlc.action)
    return {'return': 0}


def postprocess(i):

    return {'return': 0}
