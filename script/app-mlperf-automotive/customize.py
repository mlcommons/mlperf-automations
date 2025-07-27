from mlc import utils
import os
import json
import shutil
import subprocess
import mlperf_utils
from log_parser import MLPerfLog
from utils import *
import copy
import platform
import sys


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    state = i['state']
    script_path = i['run_script_input']['path']

    if 'cmd' in i['input']:
        state['mlperf_inference_run_cmd'] = "mlcr " + \
            " ".join(i['input']['cmd'])

    state['abtf-inference-implementation'] = {}

    run_state = i['run_script_input']['run_state']
    state['abtf-inference-implementation']['script_id'] = run_state['script_id'] + \
        ":" + ",".join(run_state['script_variation_tags'])

    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    inp = i['input']
    os_info = i['os_info']

    xsep = '^' if os_info['platform'] == 'windows' else '\\'
    q = '"' if os_info['platform'] == 'windows' else "'"

    logger = i['automation'].logger

    env['CMD'] = ''

    # if env.get('MLC_MLPERF_USER_CONF', '') == '':
    #    return {'return': 0}

    output_dir = env['MLC_MLPERF_OUTPUT_DIR']
    mode = env['MLC_MLPERF_LOADGEN_MODE']

    mlc = i['automation'].action_object

    result_sut_folder_path = env['MLC_MLPERF_INFERENCE_RESULTS_SUT_PATH']

    model = env['MLC_MODEL']
    model_full_name = env.get('MLC_ML_MODEL_FULL_NAME', model)

    if mode == "accuracy" or mode == "compliance" and env[
            'MLC_MLPERF_LOADGEN_COMPLIANCE_TEST'] == "TEST01":

        out_baseline_accuracy_string = f"""> {q}{os.path.join(output_dir, "accuracy", "baseline_accuracy.txt")}{q} """
        out_compliance_accuracy_string = f"""> {q}{os.path.join(output_dir, "accuracy", "compliance_accuracy.txt")}{q} """

        if model == "ssd":
            accuracy_filename = "accuracy_cognata.py"
            accuracy_file_path = os.path.join(
                env['MLC_MLPERF_INFERENCE_SSD_RESNET50_PATH'], accuracy_filename)
            dataset_args = f""" --dataset-path {env['MLC_PREPROCESSED_DATASET_COGNATA_PATH']} --config baseline_8MP_ss_scales_fm1_5x5_all """
            accuracy_log_file_option_name = " --mlperf-accuracy-file "

        if model == "bevformer":
            accuracy_filename = "accuracy_nuscenes_cpu.py"
            accuracy_file_path = os.path.join(
                env['MLC_MLPERF_INFERENCE_BEVFORMER_PATH'], accuracy_filename)
            dataset_args = f""" --nuscenes-dir {env['MLC_PREPROCESSED_DATASET_NUSCENES_ACC_CHECKER_MIN_FILES_PATH']} --config {os.path.join(env['MLC_MLPERF_INFERENCE_BEVFORMER_PATH'], "projects" + "configs" + "bevformer" + "bevformer_tiny.py")} """
            accuracy_log_file_option_name = " --mlperf-accuracy-file "

        if model == "deeplabv3plus":
            accuracy_filename = "accuracy_cognata.py"
            accuracy_file_path = os.path.join(
                env['MLC_MLPERF_INFERENCE_DEEPLABV3PLUS_PATH'], accuracy_filename)
            dataset_args = f""" --dataset-path {env['MLC_PREPROCESSED_DATASET_COGNATA_PATH']} """
            accuracy_log_file_option_name = " --mlperf-accuracy-file "

    scenario = env['MLC_MLPERF_LOADGEN_SCENARIO']

    if not os.path.exists(output_dir) or not os.path.exists(
            os.path.join(output_dir, "mlperf_log_summary.txt")):
        # No output, fake_run?
        return {'return': 0}

    mlperf_log = MLPerfLog(os.path.join(output_dir, "mlperf_log_detail.txt"))
    if mode == "performance":
        if scenario in ["Offline", "Server", "ConstantStream"]:
            metric = "target_qps"
            result = mlperf_log['result_mean_latency_ns'] / 1000000
        elif scenario.endswith("Stream"):
            metric = "target_latency"
            result = mlperf_log['result_mean_latency_ns']
        else:
            return {'return': 1,
                    'error': 'Unsupported scenario: {}'.format(scenario)}
        import yaml
        sut_name = state['MLC_SUT_CONFIG_NAME']
        sut_config = state['MLC_SUT_CONFIG'][sut_name]
        sut_config_path = state['MLC_SUT_CONFIG_PATH'][sut_name]
        if scenario not in sut_config[model_full_name]:
            sut_config[model_full_name][scenario] = {}
        sut_config[model_full_name][scenario][metric] = result

        print(
            f"SUT: {sut_name}, model: {model_full_name}, scenario: {scenario}, {metric} (mean value) updated as {result}")
        with open(sut_config_path, "w") as f:
            yaml.dump(sut_config, f)
        logger.info(f"New config stored in {sut_config_path}")
    elif mode == "accuracy":
        acc = ""
        if env.get('MLC_MLPERF_INFERENCE_VERSION', '') == "mvp-demo" and env.get(
                'MLC_MLPERF_INFERENCE_VERSION') == "poc-demo":
            if not env.get(
                    'MLC_COGNATA_ACCURACY_DUMP_FILE'):  # can happen while reusing old runs
                env['MLC_COGNATA_ACCURACY_DUMP_FILE'] = os.path.join(
                    output_dir, "accuracy.txt")
            if os.path.exists(env['MLC_COGNATA_ACCURACY_DUMP_FILE']):
                with open(env['MLC_COGNATA_ACCURACY_DUMP_FILE'], "r") as f:
                    acc = f.readline()
        result = acc
    else:
        return {'return': 1, 'error': f"Unknown mode {mode}"}

    valid = {'performance': True, 'accuracy': True}  # its POC
    power_result = None  # No power measurement in POC

    # result, valid, power_result = mlperf_utils.get_result_from_log(env['MLC_MLPERF_LAST_RELEASE'], model, scenario, output_dir, mode)

    if not state.get('mlc-mlperf-inference-results'):
        state['mlc-mlperf-inference-results'] = {}
    if not state.get('mlc-mlperf-inference-results-last'):
        state['mlc-mlperf-inference-results-last'] = {}
    if not state['mlc-mlperf-inference-results'].get(
            state['MLC_SUT_CONFIG_NAME']):
        state['mlc-mlperf-inference-results'][state['MLC_SUT_CONFIG_NAME']] = {}
    if not state['mlc-mlperf-inference-results'][state['MLC_SUT_CONFIG_NAME']
                                                 ].get(model):
        state['mlc-mlperf-inference-results'][state['MLC_SUT_CONFIG_NAME']][model] = {}
    if not state['mlc-mlperf-inference-results'][state['MLC_SUT_CONFIG_NAME']
                                                 ][model].get(scenario):
        state['mlc-mlperf-inference-results'][state['MLC_SUT_CONFIG_NAME']
                                              ][model][scenario] = {}

    state['mlc-mlperf-inference-results'][state['MLC_SUT_CONFIG_NAME']
                                          ][model][scenario][mode] = result
    state['mlc-mlperf-inference-results'][state['MLC_SUT_CONFIG_NAME']
                                          ][model][scenario][mode + '_valid'] = valid.get(mode, False)

    state['mlc-mlperf-inference-results-last'][mode] = result
    state['mlc-mlperf-inference-results-last'][mode +
                                               '_valid'] = valid.get(mode, False)

    if mode in ["performance", "accuracy"] and env.get(
            'MLC_MLPERF_INFERENCE_VERSION', '') not in ["", "mvp-demo", "poc-demo"]:
        # if measurements file exist read it
        if os.path.exists("measurements.json"):
            with open("measurements.json", "r") as file:
                measurements = json.load(file)  # Load JSON data from the file
        else:
            measurements = {}
        measurements['starting_weights_filename'] = env.get(
            'MLC_ML_MODEL_STARTING_WEIGHTS_FILENAME', env.get(
                'MLC_ML_MODEL_FILE', measurements.get(
                    'starting_weights_filename', 'TBD')))
        measurements['retraining'] = env.get(
            'MLC_ML_MODEL_RETRAINING', measurements.get(
                'retraining', 'no'))
        measurements['input_data_types'] = env.get(
            'MLC_ML_MODEL_INPUTS_DATA_TYPE', measurements.get(
                'input_data_types', 'fp32'))
        measurements['weight_data_types'] = env.get(
            'MLC_ML_MODEL_WEIGHTS_DATA_TYPE', measurements.get(
                'weight_data_types', 'fp32'))
        measurements['weight_transformations'] = env.get(
            'MLC_ML_MODEL_WEIGHT_TRANSFORMATIONS', measurements.get(
                'weight_transformations', 'none'))

        os.chdir(output_dir)

        if not os.path.exists("mlperf_log_summary.txt"):
            return {'return': 0}

        mlperf_log_summary = ''
        if os.path.isfile("mlperf_log_summary.txt"):
            with open("mlperf_log_summary.txt", "r") as fp:
                mlperf_log_summary = fp.read()

        if mlperf_log_summary != '':
            state['app_mlperf_inference_log_summary'] = {}
            for x in mlperf_log_summary.split('\n'):
                y = x.split(': ')
                if len(y) == 2:
                    state['app_mlperf_inference_log_summary'][y[0].strip().lower()
                                                              ] = y[1].strip()

        if not is_false(env.get("MLC_MLPERF_PRINT_SUMMARY", "")):
            logger.info("\n")
            logger.info(mlperf_log_summary)

        with open("measurements.json", "w") as fp:
            json.dump(measurements, fp, indent=2)

        mlc_sut_info = {}
        mlc_sut_info['system_name'] = state['MLC_SUT_META']['system_name']
        mlc_sut_info['implementation'] = env['MLC_MLPERF_IMPLEMENTATION']
        mlc_sut_info['device'] = env['MLC_MLPERF_DEVICE']
        mlc_sut_info['framework'] = state['MLC_SUT_META']['framework']
        mlc_sut_info['run_config'] = env['MLC_MLPERF_INFERENCE_SUT_RUN_CONFIG']
        with open(os.path.join(result_sut_folder_path, "mlc-sut-info.json"), "w") as fp:
            json.dump(mlc_sut_info, fp, indent=2)

        system_meta = state['MLC_SUT_META']
        with open("system_meta.json", "w") as fp:
            json.dump(system_meta, fp, indent=2)

        # map the custom model for inference result to the official model
        # if custom model name is not set, the official model name will be
        # mapped to itself
        official_model_name = model
        if "efficientnet" in official_model_name or "mobilenet" in official_model_name:
            official_model_name = "resnet"
        model_mapping = {model_full_name: official_model_name}
        with open("model_mapping.json", "w") as fp:
            json.dump(model_mapping, fp, indent=2)

        # Add to the state
        state['app_mlperf_inference_measurements'] = copy.deepcopy(
            measurements)

        if os.path.exists(env['MLC_MLPERF_CONF']):
            shutil.copy(env['MLC_MLPERF_CONF'], 'mlperf.conf')

        if os.path.exists(env['MLC_MLPERF_USER_CONF']):
            shutil.copy(env['MLC_MLPERF_USER_CONF'], 'user.conf')

        result, valid, power_result = mlperf_utils.get_result_from_log(
            env['MLC_MLPERF_LAST_RELEASE'], model, scenario, output_dir, mode, env.get('MLC_MLPERF_INFERENCE_SOURCE_VERSION'))

        state['mlc-mlperf-inference-results'][state['MLC_SUT_CONFIG_NAME']
                                              ][model][scenario][mode] = result
        state['mlc-mlperf-inference-results'][state['MLC_SUT_CONFIG_NAME']
                                              ][model][scenario][mode + '_valid'] = valid.get(mode, False)

        state['mlc-mlperf-inference-results-last'][mode] = result
        state['mlc-mlperf-inference-results-last'][mode +
                                                   '_valid'] = valid.get(mode, False)

        # Power not included in v0.5, code should be added in future

        # Record basic host info
        host_info = {
            "os_version": platform.platform(),
            "cpu_version": platform.processor(),
            "python_version": sys.version,
        }
        try:
            import importlib.metadata
            mlc_version = importlib.metadata.version("mlc")
            host_info["mlc_version"] = mlc_version
        except Exception as e:
            error = format(e)
            mlc_version = "unknown"

        x = ''
        if env.get('MLC_HOST_OS_FLAVOR', '') != '':
            x += env['MLC_HOST_OS_FLAVOR']
        if env.get('MLC_HOST_OS_VERSION', '') != '':
            x += ' ' + env['MLC_HOST_OS_VERSION']
        if x != '':
            host_info['os_version_sys'] = x

        if env.get('MLC_HOST_SYSTEM_NAME', '') != '':
            host_info['system_name'] = env['MLC_HOST_SYSTEM_NAME']

        # Check MLC automation repository
        repo_name = 'mlcommons@mlperf-automations'
        repo_hash = ''
        r = mlc.access({'action': 'find', 'automation': 'repo',
                       'item': 'mlcommons@mlperf-automations,9e97bb72b0474657'})
        if r['return'] == 0 and len(r['list']) == 1:
            repo_path = r['list'][0].path
            if os.path.isdir(repo_path):
                repo_name = os.path.basename(repo_path)

                r = utils.run_system_cmd({
                    'path': repo_path,
                    'cmd': 'git rev-parse HEAD'})
                if r['return'] == 0:
                    repo_hash = r['output']

                    host_info['mlc_repo_name'] = repo_name
                    host_info['mlc_repo_git_hash'] = repo_hash

        with open("mlc-host-info.json", "w") as fp:
            fp.write(json.dumps(host_info, indent=2) + '\n')

        # Prepare README
        if "cmd" in inp:
            cmd = "mlc run script \\\n\t" + " \\\n\t".join(inp['cmd'])
            xcmd = "mlc run script " + xsep + "\n\t" + \
                (" " + xsep + "\n\t").join(inp['cmd'])
        else:
            cmd = ""
            xcmd = ""

        readme_init = "*Check [MLC MLPerf docs](https://docs.mlcommons.org/automotive) for more details.*\n\n"

        readme_body = "## Host platform\n\n* OS version: {}\n* CPU version: {}\n* Python version: {}\n* MLC version: {}\n\n".format(platform.platform(),
                                                                                                                                    platform.processor(), sys.version, mlc_version)

        x = repo_name
        if repo_hash != '':
            x += ' --checkout=' + str(repo_hash)

        readme_body += "## MLC Run Command\n\nSee [MLC installation guide](https://docs.mlcommons.org/mlcflow/install/).\n\n" + \
            "```bash\npip install -U mlcflow\n\nmlc rm cache -f\n\nmlc pull repo {}\n\n{}\n```".format(
                x, xcmd)

        readme_body += "\n*Note that if you want to use the [latest automation recipes](https://docs.mlcommons.org/inference) for MLPerf,\n" + \
                       " you should simply reload {} without checkout and clean MLC cache as follows:*\n\n".format(repo_name) + \
                       "```bash\nmlc rm repo {}\nmlc pull repo {}\nmlc rm cache -f\n\n```".format(
                           repo_name, repo_name)

        extra_readme_init = ''
        extra_readme_body = ''
        if env.get('MLC_MLPERF_README', '') == "yes":
            extra_readme_body += "\n## Dependent MLPerf Automation scripts\n\n"

            script_tags = inp['tags']
            script_adr = inp.get('adr', {})

            mlc_input = {'action': 'run',
                         'automation': 'script',
                         'tags': script_tags,
                         'adr': script_adr,
                         'print_deps': True,
                         'env': env,
                         'quiet': True,
                         'silent': True,
                         'fake_run': True
                         }
            r = mlc.access(mlc_input)
            if r['return'] > 0:
                return r

            print_deps = r['new_state']['print_deps']
            count = 1
            for dep in print_deps:
                extra_readme_body += "\n\n" + str(count) + ".  `" + dep + "`\n"
                count = count + 1

            if state.get(
                    'abtfabtf-inference-implementation') and state['abtfabtf-inference-implementation'].get('print_deps'):

                extra_readme_body += "\n## Dependent automation scripts for the MLPerf Automotive Implementation\n"

                print_deps = state['abtfabtf-inference-implementation']['print_deps']
                count = 1
                for dep in print_deps:
                    extra_readme_body += "\n\n" + \
                        str(count) + ". `" + dep + "`\n"
                    count = count + 1

        readme = readme_init + readme_body
        extra_readme = extra_readme_init + extra_readme_body

        with open("README.md", "w") as fp:
            fp.write(readme)
        if extra_readme:
            with open("README-extra.md", "w") as fp:
                fp.write(extra_readme)

    elif mode == "compliance":
        test = env.get("MLC_MLPERF_LOADGEN_COMPLIANCE_TEST", "TEST01")

        RESULT_DIR = os.path.split(output_dir)[0]
        COMPLIANCE_DIR = output_dir
        OUTPUT_DIR = os.path.dirname(COMPLIANCE_DIR)

        SCRIPT_PATH = os.path.join(
            env['MLC_MLPERF_INFERENCE_SOURCE'],
            "compliance",
            test,
            "run_verification.py")
        if test == "TEST06":
            cmd = f"""{env['MLC_PYTHON_BIN_WITH_PATH']}  {q}{SCRIPT_PATH}{q}  -c  {q}{COMPLIANCE_DIR}{q}  -o  {q}{OUTPUT_DIR}{q} --scenario {scenario} --dtype int32"""
        else:
            cmd = f"""{env['MLC_PYTHON_BIN_WITH_PATH']}  {q}{SCRIPT_PATH}{q}  -r {q}{RESULT_DIR}{q} -c  {q}{COMPLIANCE_DIR}{q}  -o  {q}{OUTPUT_DIR}{q}"""

        logger.info(cmd)
        os.system(cmd)

        if test == "TEST01":

            run_script_input = i['run_script_input']
            automation = i['automation']

            SCRIPT_PATH = os.path.join(env['MLC_MLPERF_INFERENCE_SOURCE'], "compliance", test,
                                       "create_accuracy_baseline.sh")
            TEST01_DIR = os.path.join(OUTPUT_DIR, "TEST01")
            OUTPUT_DIR = os.path.join(OUTPUT_DIR, "TEST01", "accuracy")
            if not os.path.exists(OUTPUT_DIR):
                os.makedirs(OUTPUT_DIR)

            ACCURACY_DIR = os.path.join(RESULT_DIR, "accuracy")
            if not os.path.exists(ACCURACY_DIR):
                logger.warning("Accuracy run not yet completed")
                return {
                    'return': 1, 'error': 'TEST01 needs accuracy run to be completed first'}

            cmd = f"""cd {q}{TEST01_DIR}{q} &&  bash {q}{SCRIPT_PATH}{q} {q}{os.path.join(ACCURACY_DIR, "mlperf_log_accuracy.json")}{q} {q}{os.path.join(COMPLIANCE_DIR, "mlperf_log_accuracy.json")}{q} """
            env['CMD'] = cmd
            logger.info(cmd)
            r = automation.run_native_script(
                {'run_script_input': run_script_input, 'env': env, 'script_name': 'verify_accuracy'})
            if r['return'] > 0:
                return r

            verify_accuracy_file = os.path.join(
                TEST01_DIR, "verify_accuracy.txt")
            with open(verify_accuracy_file, 'r') as file:
                data = file.read().replace('\n', '\t')

            if 'TEST PASS' not in data:
                logger.warning(
                    "\nDeterministic TEST01 failed... Trying with non-determinism.\n")
            # #Normal test failed, trying the check with non-determinism

                baseline_accuracy_file = os.path.join(
                    TEST01_DIR, "mlperf_log_accuracy_baseline.json")
                CMD = f"""cd {q}{ACCURACY_DIR}{q} && {q}{env['MLC_PYTHON_BIN_WITH_PATH']}{q} {q}{accuracy_filepath}{q} \
{accuracy_log_file_option_name} {q}{baseline_accuracy_file}{q} {dataset_args} {datatype_option} {out_baseline_accuracy_string} """

                env['CMD'] = CMD
                r = automation.run_native_script(
                    {'run_script_input': run_script_input, 'env': env, 'script_name': 'verify_accuracy'})
                if r['return'] > 0:
                    return r

                if os.stat(baseline_accuracy_file).st_size == 0:
                    return {'return': 1,
                            'error': f"{baseline_accuracy_file} is empty"}

                CMD = f"""cd {q}{ACCURACY_DIR}{q} && {q}{env['MLC_PYTHON_BIN_WITH_PATH']}{q} {q}{accuracy_filepath}{q} \
{accuracy_log_file_option_name} {q}{os.path.join(TEST01_DIR, "mlperf_log_accuracy.json")}{q} {dataset_args} {datatype_option} \
{out_compliance_accuracy_string} """

                env['CMD'] = CMD
                r = automation.run_native_script(
                    {'run_script_input': run_script_input, 'env': env, 'script_name': 'verify_accuracy'})
                if r['return'] > 0:
                    return r
        import submission_checker as checker
        is_valid = checker.check_compliance_perf_dir(
            COMPLIANCE_DIR) if test != "TEST06" else True
        state['mlc-mlperf-inference-results'][state['MLC_SUT_CONFIG_NAME']
                                              ][model][scenario][test] = "passed" if is_valid else "failed"

    if state.get(
            'abtf-inference-implementation') and state['abtf-inference-implementation'].get('version_info'):
        env['MLC_MLPERF_RUN_JSON_VERSION_INFO_FILE'] = os.path.join(
            output_dir, "mlc-version-info.json")
        env['MLC_MLPERF_RUN_DEPS_GRAPH'] = os.path.join(
            output_dir, "mlc-deps.png")
        env['MLC_MLPERF_RUN_DEPS_MERMAID'] = os.path.join(
            output_dir, "mlc-deps.mmd")
        with open(os.path.join(output_dir, "mlc-version-info.json"), "w") as f:
            f.write(
                json.dumps(
                    state['abtf-inference-implementation']['version_info'],
                    indent=2))

    if env.get('MLC_DUMP_SYSTEM_INFO', True):
        dump_script_output(
            "detect,os",
            env,
            state,
            'new_env',
            os.path.join(
                output_dir,
                "os_info.json"), mlc)
        dump_script_output(
            "detect,cpu",
            env,
            state,
            'new_env',
            os.path.join(
                output_dir,
                "cpu_info.json"), mlc)
        env['MLC_DUMP_RAW_PIP_FREEZE_FILE_PATH'] = os.path.join(
            env['MLC_MLPERF_OUTPUT_DIR'], "pip_freeze.raw")
        dump_script_output(
            "dump,pip,freeze",
            env,
            state,
            'new_state',
            os.path.join(
                output_dir,
                "pip_freeze.json"), mlc)

    return {'return': 0}


def dump_script_output(script_tags, env, state, output_key, dump_file, mlc):

    mlc_input = {'action': 'run',
                 'automation': 'script',
                 'tags': script_tags,
                 'env': env,
                 'state': state,
                 'quiet': True,
                 'silent': True,
                 }
    r = mlc.access(mlc_input)
    if r['return'] > 0:
        return r
    with open(dump_file, "w") as f:
        f.write(json.dumps(r[output_key], indent=2))

    return {'return': 0}
