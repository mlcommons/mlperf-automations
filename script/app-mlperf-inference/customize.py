from mlc import utils

import os
import json
import shutil
import subprocess
import copy
import platform
import sys
import mlperf_utils
import re
from datetime import datetime, timezone


def preprocess(i):

    env = i['env']
    state = i['state']

    if env.get('MLC_MLPERF_IMPLEMENTATION', '') == 'nvidia':
        if env.get('MLC_NVIDIA_GPU_NAME', '') in [
                "rtx_4090", "a100", "t4", "l4", "orin", "custom"]:
            env['MLC_NVIDIA_HARNESS_GPU_VARIATION'] = "_" + \
                env['MLC_NVIDIA_GPU_NAME']
            env['MLC_NVIDIA_GPU_MEMORY'] = ''
        else:
            gpu_memory = i['state'].get(
                'mlc_cuda_device_prop', '').get('Global memory')
            gpu_memory_size = str(
                int((float(gpu_memory) / (1024 * 1024 * 1024) + 7) / 8) * 8)
            env['MLC_NVIDIA_GPU_MEMORY'] = gpu_memory_size
            env['MLC_NVIDIA_HARNESS_GPU_VARIATION'] = ''

    if 'cmd' in i['input']:
        state['mlperf_inference_run_cmd'] = "mlcr " + \
            " ".join(i['input']['cmd'])

    state['mlperf-inference-implementation'] = {}

    run_state = i['run_script_input']['run_state']
    state['mlperf-inference-implementation']['script_id'] = run_state['script_id'] + \
        ":" + ",".join(run_state['script_variation_tags'])

    if env.get('MLC_VLLM_SERVER_MODEL_NAME', '') != '' and env.get(
            'MLC_ML_MODEL_FULL_NAME', '') == '':
        env['MLC_ML_MODEL_FULL_NAME'] = env['MLC_VLLM_SERVER_MODEL_NAME'].replace(
            "/", "_")

    return {'return': 0}


def postprocess(i):

    os_info = i['os_info']

    xsep = '^' if os_info['platform'] == 'windows' else '\\'

    env = i['env']
    inp = i['input']
    env['CMD'] = ''
    state = i['state']

    # if env.get('MLC_MLPERF_USER_CONF', '') == '':
    #    return {'return': 0}

    output_dir = env['MLC_MLPERF_OUTPUT_DIR']

    result_sut_folder_path = env['MLC_MLPERF_INFERENCE_RESULTS_SUT_PATH']

    mode = env['MLC_MLPERF_LOADGEN_MODE']

    if not os.path.exists(output_dir) or not os.path.exists(
            os.path.join(output_dir, "mlperf_log_summary.txt")):
        # No output, fake_run?
        return {'return': 0}

    # in power mode copy the log files from tmp_power directory
    if env.get('MLC_MLPERF_POWER', '') == "yes" and mode == "performance":
        mlperf_power_logs_dir = os.path.join(
            env['MLC_MLPERF_OUTPUT_DIR'], "..", "power")
        mlperf_ranging_logs_dir = os.path.join(
            env['MLC_MLPERF_OUTPUT_DIR'], "..", "ranging")

        if os.path.exists(os.path.join(
                env['MLC_MLPERF_POWER_LOG_DIR'], "power")):
            if os.path.exists(mlperf_power_logs_dir):
                shutil.rmtree(mlperf_power_logs_dir)
            shutil.copytree(
                os.path.join(
                    env['MLC_MLPERF_POWER_LOG_DIR'],
                    "power"),
                mlperf_power_logs_dir)

        if os.path.exists(os.path.join(
                env['MLC_MLPERF_POWER_LOG_DIR'], "ranging")):
            if os.path.exists(mlperf_ranging_logs_dir):
                shutil.rmtree(mlperf_ranging_logs_dir)
            shutil.copytree(
                os.path.join(
                    env['MLC_MLPERF_POWER_LOG_DIR'],
                    "ranging"),
                mlperf_ranging_logs_dir)

        if os.path.exists(os.path.join(
                env['MLC_MLPERF_POWER_LOG_DIR'], "run_1", "spl.txt")):
            shutil.copyfile(
                os.path.join(
                    env['MLC_MLPERF_POWER_LOG_DIR'],
                    "run_1",
                    "spl.txt"),
                os.path.join(
                    env['MLC_MLPERF_OUTPUT_DIR'],
                    "spl.txt"))

    model = env['MLC_MODEL']
    model_full_name = env.get('MLC_ML_MODEL_FULL_NAME', model)

    if mode == "accuracy" or mode == "compliance" and env[
            'MLC_MLPERF_LOADGEN_COMPLIANCE_TEST'] == "TEST01":
        out_baseline_accuracy_string = f"""> {os.path.join(output_dir, "accuracy", "baseline_accuracy.txt")} """
        out_compliance_accuracy_string = f"""> {os.path.join(output_dir, "accuracy", "compliance_accuracy.txt")} """
        if model == "resnet50":
            accuracy_filename = "accuracy-imagenet.py"
            accuracy_filepath = os.path.join(env['MLC_MLPERF_INFERENCE_CLASSIFICATION_AND_DETECTION_PATH'], "tools",
                                             accuracy_filename)
            dataset_args = " --imagenet-val-file " + \
                os.path.join(env['MLC_DATASET_AUX_PATH'], "val.txt")
            accuracy_log_file_option_name = " --mlperf-accuracy-file "
            datatype_option = " --dtype " + env['MLC_IMAGENET_ACCURACY_DTYPE']

        elif model == "retinanet":
            accuracy_filename = "accuracy-openimages.py"
            accuracy_filepath = os.path.join(env['MLC_MLPERF_INFERENCE_CLASSIFICATION_AND_DETECTION_PATH'], "tools",
                                             accuracy_filename)
            dataset_args = " --openimages-dir " + \
                os.getcwd()  # just to make the script happy
            accuracy_log_file_option_name = " --mlperf-accuracy-file "
            datatype_option = ""

        elif 'bert' in model:
            accuracy_filename = "accuracy-squad.py"
            accuracy_filepath = os.path.join(
                env['MLC_MLPERF_INFERENCE_BERT_PATH'], accuracy_filename)
            dataset_args = " --val_data '" + env['MLC_DATASET_SQUAD_VAL_PATH'] + "' --vocab_file '" + \
                env['MLC_DATASET_SQUAD_VOCAB_PATH'] + \
                "' --out_file predictions.json "
            accuracy_log_file_option_name = " --log_file "
            datatype_option = " --output_dtype " + \
                env['MLC_SQUAD_ACCURACY_DTYPE']

        elif 'rgat' in model:
            accuracy_filename = "accuracy_igbh.py"
            accuracy_filepath = os.path.join(
                env['MLC_MLPERF_INFERENCE_RGAT_PATH'], "tools", accuracy_filename)
            dataset_args = " --dataset-path '" + env['MLC_DATASET_IGBH_PATH'] + "' --dataset-size '" + \
                env['MLC_DATASET_IGBH_SIZE'] + "'"
            accuracy_log_file_option_name = " --mlperf-accuracy-file "
            datatype_option = ""
            out_baseline_accuracy_string = f""" --output-file {os.path.join(output_dir, "accuracy", "baseline_accuracy.txt")} """
            out_compliance_accuracy_string = f""" --output-file {os.path.join(output_dir, "accuracy", "compliance_accuracy.txt")} """

        elif 'stable-diffusion-xl' in model:
            pass  # No compliance check for now
        elif 'gpt' in model:
            pass  # No compliance check for now
        elif 'llama2-70b' in model:
            pass  # No compliance check for now
        elif 'mixtral-8x7b' in model:
            pass  # No compliance check for now
        else:
            pass  # Not giving an error now. But accuracy paths need to be done for other benchmarks which may need the non-determinism test
            # return {'return': 1, 'error': f'Accuracy paths not done for model
            # {model}'}
    scenario = env['MLC_MLPERF_LOADGEN_SCENARIO']

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

    # if env.get("MLC_MLPERF_FIND_PERFORMANCE_MODE", '') == "yes" and mode ==
    # "performance" and scenario != "Server":
    if mode == "performance" and scenario != "Server":
        os.chdir(output_dir)
        if not os.path.exists("mlperf_log_summary.txt"):
            return {'return': 0}

        if scenario in ["Offline", "Server"]:
            metric = "target_qps"
        elif scenario.endswith("Stream"):
            metric = "target_latency"
        else:
            return {'return': 1,
                    'error': 'Unsupported scenario: {}'.format(scenario)}

        import re
        import yaml
        pattern = {}
        pattern["Offline"] = "Samples per second: (.*)\n"
        pattern["SingleStream"] = "Mean latency \\(ns\\)\\s*:(.*)"
        pattern["MultiStream"] = "Mean latency \\(ns\\)\\s*:(.*)"
        print("\n")
        with open("mlperf_log_summary.txt", "r") as fp:
            summary = fp.read()

        result = re.findall(pattern[scenario], summary)

        if not result:
            return {
                'return': 1, 'error': f'No {metric} found in performance summary. Pattern checked "{pattern[metric]}"'}

        value = result[0].strip()
        if "\\(ns\\)" in pattern[scenario]:
            value = str(float(value) / 1000000)  # convert to milliseconds

        sut_name = state['MLC_SUT_CONFIG_NAME']
        sut_config = state['MLC_SUT_CONFIG'][sut_name]
        sut_config_path = state['MLC_SUT_CONFIG_PATH'][sut_name]
        if scenario not in sut_config[model_full_name]:
            sut_config[model_full_name][scenario] = {}
        sut_config[model_full_name][scenario][metric] = value

        print(
            f"SUT: {sut_name}, model: {model_full_name}, scenario: {scenario}, {metric} updated as {value}")
        print(f"New config stored in {sut_config_path}")
        with open(sut_config_path, "w") as f:
            yaml.dump(sut_config, f)

    if mode in ["performance", "accuracy"]:
        # if measurements file exist read it
        if os.path.exists("measurements.json"):
            with open("measurements.json", "r") as file:
                measurements = json.load(file)  # Load JSON data from the file
        else:
            measurements = {}
        measurements['starting_weights_filename'] = env.get(
            'MLC_ML_MODEL_STARTING_WEIGHTS_FILENAME', env.get(
                'MLC_ML_MODEL_FILE', measurements.get(
                    'starting_weights_filename', '')))
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

        if env.get("MLC_MLPERF_PRINT_SUMMARY", "").lower() not in [
                "no", "0", "false"]:
            print("\n")
            print(mlperf_log_summary)

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
        power = None
        power_efficiency = None
        if power_result:
            power_result_split = power_result.split(",")
            if len(power_result_split) == 2:  # power and power efficiency
                power = power_result_split[0]
                power_efficiency = power_result_split[1]

        state['mlc-mlperf-inference-results'][state['MLC_SUT_CONFIG_NAME']
                                              ][model][scenario][mode] = result
        state['mlc-mlperf-inference-results'][state['MLC_SUT_CONFIG_NAME']
                                              ][model][scenario][mode + '_valid'] = valid.get(mode, False)

        state['mlc-mlperf-inference-results-last'][mode] = result
        state['mlc-mlperf-inference-results-last'][mode +
                                                   '_valid'] = valid.get(mode, False)

        if power:
            state['mlc-mlperf-inference-results'][state['MLC_SUT_CONFIG_NAME']
                                                  ][model][scenario]['power'] = power
            state['mlc-mlperf-inference-results'][state['MLC_SUT_CONFIG_NAME']
                                                  ][model][scenario]['power_valid'] = valid['power']
            state['mlc-mlperf-inference-results-last']['power'] = power
            state['mlc-mlperf-inference-results-last']['power_valid'] = valid['power']
        if power_efficiency:
            state['mlc-mlperf-inference-results'][state['MLC_SUT_CONFIG_NAME']
                                                  ][model][scenario]['power_efficiency'] = power_efficiency
            state['mlc-mlperf-inference-results-last']['power_efficiency'] = power_efficiency

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
            mlc_version="unknown"


        x = ''
        if env.get('MLC_HOST_OS_FLAVOR', '') != '':
            x += env['MLC_HOST_OS_FLAVOR']
        if env.get('MLC_HOST_OS_VERSION', '') != '':
            x += ' ' + env['MLC_HOST_OS_VERSION']
        if x != '':
            host_info['os_version_sys'] = x

        if env.get('MLC_HOST_SYSTEM_NAME', '') != '':
            host_info['system_name'] = env['MLC_HOST_SYSTEM_NAME']

        # Check CM automation repository
        repo_name = 'mlcommons@mlperf-automations'
        repo_hash = ''
        mlc = i['automation'].action_object
        r = mlc.access({'action': 'find', 'automation': 'repo',
                       'item': 'mlcommons@mlperf-automations,9e97bb72b0474657'})
        if r['return'] == 0 and len(r['list']) == 1:
            repo_path = r['list'][0].path
            if os.path.isdir(repo_path):
                repo_name = os.path.basename(repo_path)

                # Check dev
                # if repo_name == 'cm4mlops': repo_name = 'mlcommons@cm4mlops'

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

        readme_init = "*Check [CM MLPerf docs](https://docs.mlcommons.org/inference) for more details.*\n\n"

        readme_body = "## Host platform\n\n* OS version: {}\n* CPU version: {}\n* Python version: {}\n* MLC version: {}\n\n".format(platform.platform(),
                                                                                                                                    platform.processor(), sys.version, mlc_version)

        x = repo_name
        if repo_hash != '':
            x += ' --checkout=' + str(repo_hash)

        readme_body += "## CM Run Command\n\nSee [CM installation guide](https://docs.mlcommons.org/inference/install/).\n\n" + \
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
                    'mlperf-inference-implementation') and state['mlperf-inference-implementation'].get('print_deps'):

                extra_readme_body += "\n## Dependent automation scripts for the MLPerf Inference Implementation\n"

                print_deps = state['mlperf-inference-implementation']['print_deps']
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
            "nvidia",
            test,
            "run_verification.py")
        if test == "TEST06":
            cmd = f"{env['MLC_PYTHON_BIN_WITH_PATH']}  {SCRIPT_PATH}  -c  {COMPLIANCE_DIR}  -o  {OUTPUT_DIR} --scenario {scenario} --dtype int32"
        else:
            cmd = f"{env['MLC_PYTHON_BIN_WITH_PATH']}  {SCRIPT_PATH}  -r {RESULT_DIR} -c  {COMPLIANCE_DIR}  -o  {OUTPUT_DIR}"

        print(cmd)
        os.system(cmd)

        if test == "TEST01":

            run_script_input = i['run_script_input']
            automation = i['automation']

            SCRIPT_PATH = os.path.join(env['MLC_MLPERF_INFERENCE_SOURCE'], "compliance", "nvidia", test,
                                       "create_accuracy_baseline.sh")
            TEST01_DIR = os.path.join(OUTPUT_DIR, "TEST01")
            OUTPUT_DIR = os.path.join(OUTPUT_DIR, "TEST01", "accuracy")
            if not os.path.exists(OUTPUT_DIR):
                os.makedirs(OUTPUT_DIR)

            ACCURACY_DIR = os.path.join(RESULT_DIR, "accuracy")
            if not os.path.exists(ACCURACY_DIR):
                print("Accuracy run not yet completed")
                return {
                    'return': 1, 'error': 'TEST01 needs accuracy run to be completed first'}

            cmd = "cd " + TEST01_DIR + " &&  bash " + SCRIPT_PATH + " " + os.path.join(ACCURACY_DIR, "mlperf_log_accuracy.json") + " " + \
                os.path.join(COMPLIANCE_DIR, "mlperf_log_accuracy.json")
            env['CMD'] = cmd
            print(cmd)
            r = automation.run_native_script(
                {'run_script_input': run_script_input, 'env': env, 'script_name': 'verify_accuracy'})
            if r['return'] > 0:
                return r

            verify_accuracy_file = os.path.join(
                TEST01_DIR, "verify_accuracy.txt")
            with open(verify_accuracy_file, 'r') as file:
                data = file.read().replace('\n', '\t')

            if 'TEST PASS' not in data:
                print("\nDeterministic TEST01 failed... Trying with non-determinism.\n")
            # #Normal test failed, trying the check with non-determinism

                baseline_accuracy_file = os.path.join(
                    TEST01_DIR, "mlperf_log_accuracy_baseline.json")
                CMD = "cd " + ACCURACY_DIR + " && " + env['MLC_PYTHON_BIN_WITH_PATH'] + ' ' + accuracy_filepath + accuracy_log_file_option_name + \
                    baseline_accuracy_file + ' ' + dataset_args + \
                    datatype_option + out_baseline_accuracy_string

                env['CMD'] = CMD
                r = automation.run_native_script(
                    {'run_script_input': run_script_input, 'env': env, 'script_name': 'verify_accuracy'})
                if r['return'] > 0:
                    return r

                if os.stat(baseline_accuracy_file).st_size == 0:
                    return {'return': 1,
                            'error': f"{baseline_accuracy_file} is empty"}

                CMD = "cd " + ACCURACY_DIR + " &&  " + env['MLC_PYTHON_BIN_WITH_PATH'] + ' ' + accuracy_filepath + accuracy_log_file_option_name + \
                    os.path.join(TEST01_DIR, "mlperf_log_accuracy.json") + \
                    dataset_args + datatype_option + out_compliance_accuracy_string

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

    # portion of the code where the avg utilisation and system informations are extracted
    # NOTE: The section is under development and print statements are added
    # for further debugging
    if env.get('MLC_PROFILE_NVIDIA_POWER', '') == "on":
        import pandas as pd
        system_utilisation_info_dump = {}
        logs_dir = output_dir
        # logs_dir = env.get('MLC_LOGS_DIR', env['MLC_RUN_DIR'])
        sys_utilisation_log = pd.read_csv(
            os.path.join(
                logs_dir,
                'sys_utilisation_info.txt'),
            dtype={
                'cpu_utilisation': float,
                'used_memory_gb': float})
        with open(os.path.join(logs_dir, 'mlperf_log_detail.txt'), 'r') as file:
            log_txt = file.read()
            # patterns for matching the power_begin and power_end in mlperf log
            pattern_begin = r'\"key\"\:\s\"power_begin\"\,\s\"value\"\:\s\"(.*?)\"'
            pattern_end = r'\"key\"\:\s\"power_end\"\,\s\"value\"\:\s\"(.*?)\"'
            # match the patterns with the text present in the log details file
            match_begin = re.findall(pattern_begin, log_txt)[0]
            match_end = re.findall(pattern_end, log_txt)[0]
            power_begin_time = pd.Timestamp(datetime.strptime(
                match_begin, '%m-%d-%Y %H:%M:%S.%f')).replace(tzinfo=timezone.utc)
            power_end_time = pd.Timestamp(datetime.strptime(
                match_end, '%m-%d-%Y %H:%M:%S.%f')).replace(tzinfo=timezone.utc)
        # converts timestamp key value to datetime objects
        sys_utilisation_log['timestamp'] = pd.to_datetime(
            sys_utilisation_log['timestamp'])
        '''
        for i in range(len(sys_utilisation_log['timestamp'])):
            print(f"{sys_utilisation_log['timestamp'][i]} {power_begin_time}")
            print(sys_utilisation_log['timestamp'][i]>=power_begin_time)
        '''
        # print(f"{sys_utilisation_log['timestamp'][0]} {power_begin_time}")
        # print(sys_utilisation_log['timestamp'][0]>=power_begin_time)
        filtered_log = sys_utilisation_log[(sys_utilisation_log['timestamp'] >= power_begin_time) &
                                           (sys_utilisation_log['timestamp'] <= power_end_time)]
        # print(filtered_log)
        # Calculate average of cpu_utilisation and used_memory_gb
        system_utilisation_info_dump["avg_cpu_utilisation"] = filtered_log['cpu_utilisation'].mean(
        )
        system_utilisation_info_dump["avg_used_memory_gb"] = filtered_log['used_memory_gb'].mean(
        )
        print("\nSystem utilisation info for the current run:")
        print(system_utilisation_info_dump)
        print("\n")

    if state.get(
            'mlperf-inference-implementation') and state['mlperf-inference-implementation'].get('version_info'):
        env['MLC_MLPERF_RUN_JSON_VERSION_INFO_FILE'] = os.path.join(
            output_dir, "mlc-version-info.json")
        env['MLC_MLPERF_RUN_DEPS_GRAPH'] = os.path.join(
            output_dir, "mlc-deps.png")
        env['MLC_MLPERF_RUN_DEPS_MERMAID'] = os.path.join(
            output_dir, "mlc-deps.mmd")
        with open(os.path.join(output_dir, "mlc-version-info.json"), "w") as f:
            f.write(
                json.dumps(
                    state['mlperf-inference-implementation']['version_info'],
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
