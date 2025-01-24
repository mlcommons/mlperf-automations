from mlc import utils
import os
import json
import shutil
import subprocess
import mlc
import copy
import mlperf_utils

summary_ext = ['.csv', '.json', '.xlsx']

##########################################################################


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    const = i.get('const', {})

    inp = i['input']
    state = i['state']
    script_path = i['run_script_input']['path']

    if env.get('MLC_RUN_DOCKER_CONTAINER', '') == "yes":
        return {'return': 0}

    if env.get('MLC_DOCKER_IMAGE_NAME', '') == 'scc24':
        if env.get("MLC_MLPERF_IMPLEMENTATION", "reference") == "reference":
            env['MLC_DOCKER_IMAGE_NAME'] = "scc24-reference"
        elif "nvidia" in env.get("MLC_MLPERF_IMPLEMENTATION", "reference"):
            env['MLC_DOCKER_IMAGE_NAME'] = "scc24-nvidia"

    dump_version_info = env.get('MLC_DUMP_VERSION_INFO', True)

    system_meta = state.get('MLC_SUT_META', {})
    if system_meta:
        env['MLC_SUT_META_EXISTS'] = "yes"

    env['MLC_MODEL'] = env['MLC_MLPERF_MODEL']

    # Clean MLPerf inference output tar file if non-standard
    x = env.get('MLPERF_INFERENCE_SUBMISSION_TAR_FILE', '')
    if x != '' and os.path.isfile(x):
        os.remove(x)

    # Clean MLPerf inference submission summary files
    x = env.get('MLPERF_INFERENCE_SUBMISSION_SUMMARY', '')

    if x != '':
        for y in summary_ext:
            z = x + y
            if os.path.isfile(z):
                os.remove(z)

    if env.get('MLC_MLPERF_SUBMISSION_SYSTEM_TYPE', '') != '':
        system_type = env['MLC_MLPERF_SUBMISSION_SYSTEM_TYPE']
        system_meta['system_type'] = system_type

    if env.get('MLC_MLPERF_SUBMISSION_DIVISION', '') != '':
        division = env['MLC_MLPERF_SUBMISSION_DIVISION']
        system_meta['division'] = division

    if system_meta.get('division', '') != "closed":
        # no compliance runs needed for open division
        env["MLC_MLPERF_LOADGEN_COMPLIANCE"] = "no"

    clean = False

    if 'MLC_MLPERF_CLEAN_ALL' in env:
        clean = True
        if 'MLC_MLPERF_CLEAN_SUBMISSION_DIR' not in env:
            env['MLC_MLPERF_CLEAN_SUBMISSION_DIR'] = "yes"
        if 'MLC_RERUN' not in env:
            env['MLC_RERUN'] = "yes"

    if str(env.get('MLC_SYSTEM_POWER', 'no')).lower(
    ) != "no" or env.get('MLC_MLPERF_POWER', '') == "yes":
        power_variation = ",_power"
        env['MLC_MLPERF_POWER'] = "yes"
    else:
        power_variation = ""

    if env.get('MLC_RUN_STYLE',
               '') == "valid" and 'MLC_RUN_MLPERF_ACCURACY' not in env:
        env['MLC_RUN_MLPERF_ACCURACY'] = "on"

    print("Using MLCommons Inference source from " +
          env['MLC_MLPERF_INFERENCE_SOURCE'])

    if 'MLC_MLPERF_LOADGEN_EXTRA_OPTIONS' not in env:
        env['MLC_MLPERF_LOADGEN_EXTRA_OPTIONS'] = ""

    if 'MLC_MLPERF_LOADGEN_MODES' not in env:
        if 'MLC_MLPERF_LOADGEN_MODE' not in env:
            env['MLC_MLPERF_LOADGEN_MODE'] = "performance"

    if 'MLC_MLPERF_LOADGEN_SCENARIOS' not in env:
        if 'MLC_MLPERF_LOADGEN_SCENARIO' not in env:
            env['MLC_MLPERF_LOADGEN_SCENARIO'] = "Offline"

    if env.get('MLC_MLPERF_LOADGEN_ALL_SCENARIOS', '') == "yes":
        env['MLC_MLPERF_LOADGEN_SCENARIOS'] = get_valid_scenarios(
            env['MLC_MODEL'],
            system_meta.get(
                'system_type',
                'edge'),
            env['MLC_MLPERF_LAST_RELEASE'],
            env['MLC_MLPERF_INFERENCE_SOURCE'])
    else:
        system_meta = {}
        env['MLC_MLPERF_LOADGEN_SCENARIOS'] = [
            env['MLC_MLPERF_LOADGEN_SCENARIO']]

    if env.get('MLC_MLPERF_LOADGEN_ALL_MODES', '') == "yes":
        env['MLC_MLPERF_LOADGEN_MODES'] = ["performance", "accuracy"]
    else:
        env['MLC_MLPERF_LOADGEN_MODES'] = [env['MLC_MLPERF_LOADGEN_MODE']]

    if env.get('OUTPUT_BASE_DIR', '') == '':
        env['OUTPUT_BASE_DIR'] = env.get(
            'MLC_MLPERF_INFERENCE_RESULTS_DIR', os.getcwd())

    test_list = ["TEST01"]
    if env['MLC_MODEL'] in ["resnet50", "sdxl"]:
        test_list.append("TEST04")
    if "gpt" in env['MLC_MODEL'] or "llama2-70b" in env['MLC_MODEL'] or "mixtral-8x7b" in env['MLC_MODEL']:
        test_list.remove("TEST01")
        # test_list.remove("TEST05")

    if "llama2" in env['MLC_MODEL'].lower(
    ) or "mixtral-8x7b" in env['MLC_MODEL']:
        test_list.append("TEST06")

    variation_implementation = "_" + \
        env.get("MLC_MLPERF_IMPLEMENTATION", "reference")
    variation_model = ",_" + env["MLC_MLPERF_MODEL"]
    variation_backend = ",_" + \
        env["MLC_MLPERF_BACKEND"] if env.get(
            "MLC_MLPERF_BACKEND", "") != "" else ""
    variation_device = ",_" + \
        env["MLC_MLPERF_DEVICE"] if env.get(
            "MLC_MLPERF_DEVICE", "") != "" else ""
    variation_run_style = ",_" + env.get("MLC_MLPERF_RUN_STYLE", "test")
    variation_reproducibility = ",_" + env["MLC_RUN_MLPERF_INFERENCE_APP_DEFAULTS"] if env.get(
        "MLC_RUN_MLPERF_INFERENCE_APP_DEFAULTS", "") != "" else ""
    variation_all_models = ",_all-models" if env.get(
        "MLC_MLPERF_ALL_MODELS", "") == "yes" else ""

    if env.get("MLC_MLPERF_MODEL_PRECISION", '') != '':
        variation_quantization_string = ",_" + \
            env["MLC_MLPERF_MODEL_PRECISION"]
    else:
        variation_quantization_string = ""

    tags = "app,mlperf,inference,generic," + variation_implementation + variation_model + variation_backend + variation_device + \
        variation_run_style + variation_reproducibility + \
        variation_quantization_string + power_variation + variation_all_models
    verbose = inp.get('v', False)
    print_env = inp.get('print_env', False)
    print_deps = inp.get('print_deps', False)
    add_deps_recursive = inp.get('add_deps_recursive', {})
    add_deps = inp.get('add_deps', {})
    ad = inp.get('ad', {})
    adr = inp.get('adr', {})
    docker_it = inp.get('docker_it', '')
    docker_dt = inp.get('docker_dt', '')
    adr_from_meta = i['run_script_input'].get('add_deps_recursive')

    for key in adr_from_meta:
        add_deps_recursive[key] = adr_from_meta[key]

    if env.get('MLC_MLPERF_LOADGEN_MAX_BATCHSIZE', '') != '':
        if not add_deps_recursive.get('mlperf-inference-implementation', {}):
            add_deps_recursive['mlperf-inference-implementation'] = {}
        if add_deps_recursive['mlperf-inference-implementation'].get(
                'tags', '') == '':
            add_deps_recursive['mlperf-inference-implementation']['tags'] = ''
        else:
            add_deps_recursive['mlperf-inference-implementation']['tags'] += ','
        add_deps_recursive['mlperf-inference-implementation']['tags'] += "_batch_size." + \
            env['MLC_MLPERF_LOADGEN_MAX_BATCHSIZE']

    if env.get('MLC_MLPERF_INFERENCE_SUT_VARIATION', '') != '':
        if not add_deps_recursive.get('mlperf-inference-implementation', {}):
            add_deps_recursive['mlperf-inference-implementation'] = {}
        if add_deps_recursive['mlperf-inference-implementation'].get(
                'tags', '') == '':
            add_deps_recursive['mlperf-inference-implementation']['tags'] = ''
        else:
            add_deps_recursive['mlperf-inference-implementation']['tags'] += ','
        add_deps_recursive['mlperf-inference-implementation']['tags'] += "_" + \
            env['MLC_MLPERF_INFERENCE_SUT_VARIATION']

    if env.get('MLC_NETWORK_LOADGEN', '') != '':
        if not add_deps_recursive.get('mlperf-inference-implementation', {}):
            add_deps_recursive['mlperf-inference-implementation'] = {}
        network_variation_tag = f"_network-{env['MLC_NETWORK_LOADGEN']}"
        if add_deps_recursive['mlperf-inference-implementation'].get(
                'tags', '') == '':
            add_deps_recursive['mlperf-inference-implementation']['tags'] = ''
        else:
            add_deps_recursive['mlperf-inference-implementation']['tags'] += ','
        add_deps_recursive['mlperf-inference-implementation']['tags'] += network_variation_tag

    if env.get('MLC_OUTPUT_FOLDER_NAME', '') == '':
        env['MLC_OUTPUT_FOLDER_NAME'] = env['MLC_MLPERF_RUN_STYLE'] + "_results"

    output_dir = os.path.join(
        env['OUTPUT_BASE_DIR'],
        env['MLC_OUTPUT_FOLDER_NAME'])
    if clean:
        path_to_clean = output_dir

        print('=========================================================')
        print('Cleaning results in {}'.format(path_to_clean))
        if os.path.exists(path_to_clean):
            shutil.rmtree(path_to_clean)

        print('=========================================================')

    if str(env.get('MLC_MLPERF_USE_DOCKER', '')
           ).lower() in ["1", "true", "yes"]:
        action = "docker"
        # del(env['OUTPUT_BASE_DIR'])
        state = {}
        docker_extra_input = {}

        # if env.get('MLC_HW_NAME'):
        #    del(env['MLC_HW_NAME'])

        for k in inp:
            if k.startswith("docker_"):
                docker_extra_input[k] = inp[k]
        inp = {}
        if str(docker_dt).lower() in ["yes", "true", "1"]:
            # turning it off for the first run and after that we turn it on
            if env.get('MLC_DOCKER_REUSE_EXISTING_CONTAINER', '') == '':
                env['MLC_DOCKER_REUSE_EXISTING_CONTAINER'] = 'no'
            env['MLC_DOCKER_DETACHED_MODE'] = 'yes'

        if env.get('MLC_DOCKER_IMAGE_NAME', '') != '':
            docker_extra_input['docker_image_name'] = env['MLC_DOCKER_IMAGE_NAME']
    else:
        action = "run"

    # local_keys = [ 'MLC_MLPERF_SKIP_RUN', 'MLC_MLPERF_LOADGEN_QUERY_COUNT', 'MLC_MLPERF_LOADGEN_TARGET_QPS', 'MLC_MLPERF_LOADGEN_TARGET_LATENCY' ]

    for scenario in env['MLC_MLPERF_LOADGEN_SCENARIOS']:
        scenario_tags = tags + ",_" + scenario.lower()
        env['MLC_MLPERF_LOADGEN_SCENARIO'] = scenario

        if scenario == "Offline":
            if env.get('MLC_MLPERF_LOADGEN_OFFLINE_TARGET_QPS'):
                env['MLC_MLPERF_LOADGEN_TARGET_QPS'] = env['MLC_MLPERF_LOADGEN_OFFLINE_TARGET_QPS']
        elif scenario == "Server":
            if env.get('MLC_MLPERF_LOADGEN_SERVER_TARGET_QPS'):
                env['MLC_MLPERF_LOADGEN_TARGET_QPS'] = env['MLC_MLPERF_LOADGEN_SERVER_TARGET_QPS']
        elif scenario == "SingleStream":
            if env.get('MLC_MLPERF_LOADGEN_SINGLESTREAM_TARGET_LATENCY'):
                env['MLC_MLPERF_LOADGEN_TARGET_LATENCY'] = env['MLC_MLPERF_LOADGEN_SINGLESTREAM_TARGET_LATENCY']
        elif scenario == "MultiStream":
            if env.get('MLC_MLPERF_LOADGEN_MULTISTREAM_TARGET_LATENCY'):
                env['MLC_MLPERF_LOADGEN_TARGET_LATENCY'] = env['MLC_MLPERF_LOADGEN_MULTISTREAM_TARGET_LATENCY']

        for mode in env['MLC_MLPERF_LOADGEN_MODES']:
            env['MLC_MLPERF_LOADGEN_MODE'] = mode

            env_copy = copy.deepcopy(env)
            const_copy = copy.deepcopy(const)
            print(f"\nRunning loadgen scenario: {scenario} and mode: {mode}")
            ii = {'action': action, 'automation': 'script', 'tags': scenario_tags, 'quiet': 'true',
                  'env': env_copy, 'const': const_copy, 'input': inp, 'state': state, 'add_deps': copy.deepcopy(add_deps), 'add_deps_recursive':
                  copy.deepcopy(add_deps_recursive), 'ad': ad, 'adr': copy.deepcopy(adr), 'v': verbose, 'print_env': print_env, 'print_deps': print_deps, 'dump_version_info': dump_version_info}

            if action == "docker":
                for k in docker_extra_input:
                    ii[k] = docker_extra_input[k]

            # mlc = i['automation'].action_object

            # print(ii)
            # return {'return': 1}
            r = mlc.access(ii)
            if r['return'] > 0:
                return r

            if env_copy.get(
                    'MLC_MLPERF_INFERENCE_FINAL_RESULTS_DIR', '') != '':
                env['MLC_MLPERF_INFERENCE_RESULTS_DIR_'] = env_copy['MLC_MLPERF_INFERENCE_FINAL_RESULTS_DIR']
            else:
                env['MLC_MLPERF_INFERENCE_RESULTS_DIR_'] = os.path.join(
                    env['OUTPUT_BASE_DIR'], f"{env['MLC_MLPERF_RUN_STYLE']}_results")

            if action == "docker":
                if str(docker_dt).lower() not in ["yes", "true", "1"]:
                    print(
                        f"\nStop Running loadgen scenario: {scenario} and mode: {mode}")
                    # We run commands interactively inside the docker container
                    return {'return': 0}
                else:
                    env['MLC_DOCKER_REUSE_EXISTING_CONTAINER'] = 'yes'
                    container_id = env_copy['MLC_DOCKER_CONTAINER_ID']
                    env['MLC_DOCKER_CONTAINER_ID'] = container_id
            if state.get('docker', {}):
                del (state['docker'])

        if env.get("MLC_MLPERF_LOADGEN_COMPLIANCE", "") == "yes":
            for test in test_list:
                env['MLC_MLPERF_LOADGEN_COMPLIANCE_TEST'] = test
                env['MLC_MLPERF_LOADGEN_MODE'] = "compliance"
                ii = {'action': action, 'automation': 'script', 'tags': scenario_tags, 'quiet': 'true',
                      'env': copy.deepcopy(env), 'const': copy.deepcopy(const), 'input': inp, 'state': state, 'add_deps': copy.deepcopy(add_deps), 'add_deps_recursive':
                      copy.deepcopy(add_deps_recursive), 'adr': copy.deepcopy(adr), 'ad': ad, 'v': verbose, 'print_env': print_env, 'print_deps': print_deps, 'dump_version_info': dump_version_info}
                if action == "docker":
                    for k in docker_extra_input:
                        ii[k] = docker_extra_input[k]
                r = mlc.access(ii)
                if r['return'] > 0:
                    return r
                if state.get('docker', {}):
                    del (state['docker'])

    if env.get('MLC_DOCKER_CONTAINER_ID', '') != '' and str(env.get(
            'MLC_DOCKER_CONTAINER_KEEP_ALIVE', '')).lower() not in ["yes", "1", "true"]:
        container_id = env['MLC_DOCKER_CONTAINER_ID']
        CMD = f"docker kill {container_id}"
        docker_out = subprocess.check_output(CMD, shell=True).decode("utf-8")

    if state.get("mlc-mlperf-inference-results"):
        # print(state["mlc-mlperf-inference-results"])
        for sut in state["mlc-mlperf-inference-results"]:  # only one sut will be there
            # Better to do this in a stand alone CM script with proper deps but
            # currently we manage this by modifying the sys path of the python
            # executing CM
            from tabulate import tabulate  # noqa

            print(sut)
            result_table, headers = mlperf_utils.get_result_table(
                state["mlc-mlperf-inference-results"][sut])
            print(tabulate(result_table, headers=headers, tablefmt="pretty"))

            print(
                f"\nThe MLPerf inference results are stored at {output_dir}\n")

    return {'return': 0}


def get_valid_scenarios(model, category, mlperf_version, mlperf_path):

    import sys

    submission_checker_dir = os.path.join(mlperf_path, "tools", "submission")

    sys.path.append(submission_checker_dir)
    if not os.path.exists(os.path.join(
            submission_checker_dir, "submission_checker.py")):
        shutil.copy(os.path.join(submission_checker_dir, "submission-checker.py"), os.path.join(submission_checker_dir,
                                                                                                "submission_checker.py"))

    import submission_checker as checker

    if "dlrm-99" in model:
        model = model.replace("dlrm-99", "dlrm-v2-99")
    if "sdxl" in model:
        model = "stable-diffusion-xl"

    config = checker.MODEL_CONFIG

    internal_model_name = config[mlperf_version]["model_mapping"].get(
        model, model)

    valid_scenarios = config[mlperf_version]["required-scenarios-" +
                                             category.replace(",", "-")][internal_model_name]

    print(
        "Valid Scenarios for " +
        model +
        " in " +
        category +
        " category are :" +
        str(valid_scenarios))

    return valid_scenarios

##########################################################################


def postprocess(i):

    env = i['env']
    state = i['state']

    if env.get('MLC_MLPERF_IMPLEMENTATION', '') == 'reference':
        x1 = env.get('MLC_MLPERF_INFERENCE_SOURCE', '')
        x2 = env.get('MLC_MLPERF_INFERENCE_CONF_PATH', '')

        if x1 != '' and x2 != '':
            print('')
            print(
                'Path to the MLPerf inference benchmark reference sources: {}'.format(x1))
            print(
                'Path to the MLPerf inference reference configuration file: {}'.format(x2))
            print('')

    return {'return': 0}

##########################################################################


def load_md(path, path2, name):

    fn = os.path.join(path, path2, name + '.md')

    s = ''

    if os.path.isfile(fn):
        r = utils.load_txt(fn)
        if r['return'] > 0:
            return r

        s = r['string']

    return {'return': 0, 'string': s}

##########################################################################


def get_url(url, path, path2, name, text):

    name_md = name + '.md'
    fn = os.path.join(path, path2, name_md)

    urlx = ''
    url_online = ''
    if os.path.isfile(fn):
        if not url.endswith('/'):
            url += '/'
        urlx = url + path2 + '/' + name_md

        url_online = '[{}]({})'.format(text, urlx)

    return {'return': 0, 'url_online': url_online}
