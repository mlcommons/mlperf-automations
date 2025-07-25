from mlc import utils
import os
import json
import shutil
import subprocess
import sys
from utils import *


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    state = i['state']
    script_path = i['run_script_input']['path']
    logger = i['automation'].logger

    rerun = True if env.get("MLC_RERUN", "") != '' else False

    env['MLC_MLPERF_SKIP_RUN'] = env.get('MLC_MLPERF_SKIP_RUN', "no")

    mlperf_path = env['MLC_MLPERF_INFERENCE_SOURCE']
    submission_checker_dir = os.path.join(mlperf_path, "tools", "submission")
    sys.path.append(submission_checker_dir)

    version = env.get('MLC_MLPERF_INFERENCE_VERSION', "4.1")

    required_files = []
    required_files = get_checker_files()

    if 'MLC_MLPERF_LOADGEN_SCENARIO' not in env:
        env['MLC_MLPERF_LOADGEN_SCENARIO'] = "Offline"

    if 'MLC_MLPERF_LOADGEN_MODE' not in env:
        logger.info("\nNo mode given. Using accuracy as default\n")
        env['MLC_MLPERF_LOADGEN_MODE'] = "accuracy"

    if env.get('OUTPUT_BASE_DIR', '') == '':
        env['OUTPUT_BASE_DIR'] = env.get(
            'MLC_MLPERF_INFERENCE_RESULTS_DIR', os.getcwd())

    if 'MLC_NUM_THREADS' not in env:
        if 'MLC_MINIMIZE_THREADS' in env:
            env['MLC_NUM_THREADS'] = str(int(env['MLC_HOST_CPU_TOTAL_CORES']) //
                                         (int(env.get('MLC_HOST_CPU_SOCKETS', '1')) * int(env.get('MLC_HOST_CPU_TOTAL_CORES', '1'))))
        else:
            env['MLC_NUM_THREADS'] = env.get('MLC_HOST_CPU_TOTAL_CORES', '1')

    print("Using MLCommons Inference source from '" +
          env['MLC_MLPERF_INFERENCE_SOURCE'] + "'")

    if 'MLC_MLPERF_CONF' not in env:
        env['MLC_MLPERF_CONF'] = os.path.join(
            env['MLC_MLPERF_INFERENCE_SOURCE'], "mlperf.conf")

    RUN_CMD = ""
    state['RUN'] = {}

    scenario = env['MLC_MLPERF_LOADGEN_SCENARIO']
    state['RUN'][scenario] = {}

    model_full_name = env.get('MLC_ML_MODEL_FULL_NAME', env['MLC_MODEL'])

    if model_full_name != env['MLC_MODEL']:
        if 'model_mapping' not in state['MLC_SUT_CONFIG']:
            state['MLC_SUT_CONFIG']['model_mappings'] = {}
        state['MLC_SUT_CONFIG']['model_mappings'][model_full_name] = env['MLC_MODEL']

    if model_full_name not in i['state']['MLC_SUT_CONFIG'][env['MLC_SUT_NAME']]:
        i['state']['MLC_SUT_CONFIG'][env['MLC_SUT_NAME']][model_full_name] = {}

    if scenario not in i['state']['MLC_SUT_CONFIG'][env['MLC_SUT_NAME']
                                                    ][model_full_name]:
        i['state']['MLC_SUT_CONFIG'][env['MLC_SUT_NAME']
                                     ][model_full_name][scenario] = {}

    conf = i['state']['MLC_SUT_CONFIG'][env['MLC_SUT_NAME']
                                        ][model_full_name][scenario]

    mode = env['MLC_MLPERF_LOADGEN_MODE']

    user_conf = ''
    if env['MLC_MLPERF_RUN_STYLE'] == "fast":
        fast_factor = int(env['MLC_FAST_FACTOR'])
    else:
        fast_factor = 1

    ml_model_name = env['MLC_MODEL']
    if 'bert' in ml_model_name:
        ml_model_name = "bert"
    if 'dlrm' in ml_model_name:
        ml_model_name = "dlrm-v2"
    if '3d-unet' in ml_model_name:
        ml_model_name = "3d-unet"
    if 'gptj' in ml_model_name:
        ml_model_name = "gptj"
    if 'llama2-70b' in ml_model_name:
        ml_model_name = "llama2-70b"

    query_count = None

    value = None
    if scenario in ['Offline', 'Server', 'ConstantStream']:
        metric = "target_qps"
        tolerance = 1.01
        # value = env.get('MLC_MLPERF_LOADGEN_SERVER_TARGET_QPS') if scenario == "Server" else env.get('MLC_MLPERF_LOADGEN_OFFLINE_TARGET_QPS')
        value = env.get('MLC_MLPERF_LOADGEN_TARGET_QPS')
    elif scenario in ['SingleStream', 'MultiStream']:
        metric = "target_latency"
        value = env.get('MLC_MLPERF_LOADGEN_TARGET_LATENCY')
        if value:
            if scenario == "SingleStream" and (
                    1000 / float(value) * 660 < 100):
                env['MLC_MLPERF_USE_MAX_DURATION'] = 'no'
            elif scenario == "MultiStream" and (1000 / float(value) * 660 < 662):
                env['MLC_MLPERF_USE_MAX_DURATION'] = 'no'
        if not is_true(env.get('MLC_MLPERF_MODEL_EQUAL_ISSUE_MODE', 'no')) and not is_false(env.get(
                'MLC_MLPERF_USE_MAX_DURATION', "yes")):
            tolerance = 0.4  # much lower because we have max_duration
        else:
            tolerance = 0.9
    else:
        return {'return': 1, 'error': 'Invalid scenario: {}'.format(scenario)}

    if value:
        metric_value = value
        conf[metric] = value
    else:
        if metric in conf:
            print(
                "Original configuration value {} {}".format(
                    conf[metric], metric))
            metric_value = str(
                float(
                    conf[metric]) *
                tolerance)  # some tolerance
            print(
                "Adjusted configuration value {} {}".format(
                    metric_value, metric))
        else:
            # if env.get("MLC_MLPERF_FIND_PERFORMANCE_MODE", '') == "yes":
            if metric == "target_qps":
                if is_true(env.get("MLC_MLPERF_FIND_PERFORMANCE_MODE", '')):
                    logger.info(
                        "In find performance mode: using 1 as target_qps")
                else:
                    logger.info(
                        "No target_qps specified. Using 1 as target_qps")
                conf[metric] = 1
            if metric == "target_latency":
                if is_true(env.get("MLC_MLPERF_FIND_PERFORMANCE_MODE", '')):
                    logger.info(
                        "In find performance mode: using 0.5ms as target_latency")
                else:
                    logger.info("No target_latency specified. Using default")
                if is_false(env.get('MLC_MLPERF_USE_MAX_DURATION', 'yes')) or is_true(env.get(
                        'MLC_MLPERF_MODEL_EQUAL_ISSUE_MODE', 'no')):
                    # Total number of queries needed is a multiple of dataset
                    # size. So we dont use max_duration and so we need to be
                    # careful with the input latency
                    if '3d-unet' in env['MLC_MODEL']:
                        conf[metric] = 400
                    elif 'gptj' in env['MLC_MODEL']:
                        conf[metric] = 1000
                    else:
                        conf[metric] = 100
                else:
                    conf[metric] = 0.5
            metric_value = conf[metric]
            # else:
            # return {'return': 1, 'error': f"Config details missing for
            # SUT:{env['MLC_SUT_NAME']}, Model:{env['MLC_MODEL']}, Scenario:
            # {scenario}. Please input {metric} value"}

    # Pass the modified performance metrics to the implementation
    if is_true(env.get("MLC_MLPERF_FIND_PERFORMANCE_MODE", '')):
        if metric == "target_latency" and env.get(
                'MLC_MLPERF_LOADGEN_TARGET_LATENCY', '') == '':
            env['MLC_MLPERF_LOADGEN_TARGET_LATENCY'] = conf[metric]
        elif metric == "target_qps" and env.get('MLC_MLPERF_LOADGEN_TARGET_QPS', '') == '':
            env['MLC_MLPERF_LOADGEN_TARGET_QPS'] = conf[metric]

    if env['MLC_MLPERF_RUN_STYLE'] == "fast":
        if scenario == "Offline":
            metric_value = float(metric_value) / fast_factor
        if scenario in ["SingleStream", "MultiStream"]:
            metric_value = float(metric_value) * fast_factor

    elif env['MLC_MLPERF_RUN_STYLE'] == "test":
        if scenario == "Offline":
            metric_value = float(env.get('MLC_MLPERF_INFERENCE_TEST_QPS', 1))
        if scenario in ["SingleStream"]:
            metric_value = 1000

    elif env['MLC_MLPERF_RUN_STYLE'] == "valid":
        if scenario == "Offline":
            required_min_queries_offline = {}
            required_min_queries_offline = get_required_min_queries_offline(
                env['MLC_MODEL'], version)

        if mode == "compliance" and scenario == "Server":  # Adjust the server_target_qps
            test = env.get("MLC_MLPERF_LOADGEN_COMPLIANCE_TEST", "TEST01")
            if test == "TEST01":
                metric_value = str(
                    float(metric_value) *
                    float(
                        env.get(
                            "MLC_MLPERF_TEST01_SERVER_ADJUST_FACTOR",
                            0.96)))
            # if test == "TEST05":
            #    metric_value = str(float(metric_value) * float(env.get("MLC_MLPERF_TEST05_SERVER_ADJUST_FACTOR", 0.97)))
            if test == "TEST04":
                metric_value = str(
                    float(metric_value) *
                    float(
                        env.get(
                            "MLC_MLPERF_TEST04_SERVER_ADJUST_FACTOR",
                            0.97)))

    conf[metric] = metric_value
    user_conf += ml_model_name + "." + scenario + \
        "." + metric + " = " + str(metric_value) + "\n"

    if env.get('MLC_MLPERF_LOADGEN_PERFORMANCE_SAMPLE_COUNT', '') != '':
        performance_sample_count = env['MLC_MLPERF_LOADGEN_PERFORMANCE_SAMPLE_COUNT']
        user_conf += ml_model_name + ".*.performance_sample_count_override = " + \
            performance_sample_count + "\n"

    log_mode = mode
    if 'MLC_MLPERF_POWER' in env and mode == "performance":
        log_mode = "performance_power"

    env['MLC_MLPERF_INFERENCE_FINAL_RESULTS_DIR'] = os.path.join(
        env['OUTPUT_BASE_DIR'], env['MLC_OUTPUT_FOLDER_NAME'])

    sut_name = env.get(
        'MLC_SUT_NAME',
        env['MLC_MLPERF_BACKEND'] +
        "-" +
        env['MLC_MLPERF_DEVICE'])
    OUTPUT_DIR = os.path.join(env['MLC_MLPERF_INFERENCE_FINAL_RESULTS_DIR'], sut_name,
                              model_full_name, scenario.lower(), mode)

    env['MLC_MLPERF_INFERENCE_RESULTS_SUT_PATH'] = os.path.join(
        env['MLC_MLPERF_INFERENCE_FINAL_RESULTS_DIR'], sut_name)

    if 'MLC_MLPERF_POWER' in env and mode == "performance":
        env['MLC_MLPERF_POWER_LOG_DIR'] = os.path.join(OUTPUT_DIR, "tmp_power")

    if mode == "accuracy":
        pass
    elif mode == "performance":
        OUTPUT_DIR = os.path.join(OUTPUT_DIR, "run_1")
    elif mode == "compliance":
        test = env.get("MLC_MLPERF_LOADGEN_COMPLIANCE_TEST", "TEST01")
        OUTPUT_DIR = os.path.join(
            env['OUTPUT_BASE_DIR'],
            env['MLC_OUTPUT_FOLDER_NAME'],
            sut_name,
            model_full_name,
            scenario.lower(),
            test)
        if test == "TEST01":
            audit_path = os.path.join(test, ml_model_name)
        else:
            audit_path = test

        if env['MLC_BENCHMARK_GROUP'] == "automotive":
            audit_full_path = os.path.join(
                env['MLC_MLPERF_INFERENCE_SOURCE'],
                "compliance",
                audit_path,
                "audit.config")
        else:
            audit_full_path = os.path.join(
                env['MLC_MLPERF_INFERENCE_SOURCE'],
                "compliance",
                "nvidia",
                audit_path,
                "audit.config")

        env['MLC_MLPERF_INFERENCE_AUDIT_PATH'] = audit_full_path
        # copy the audit conf to the run directory incase the implementation is
        # not supporting the audit-conf path
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        shutil.copyfile(
            audit_full_path,
            os.path.join(
                OUTPUT_DIR,
                "audit.config"))

    env['MLC_MLPERF_OUTPUT_DIR'] = OUTPUT_DIR
    env['MLC_LOGS_DIR'] = OUTPUT_DIR
    env['MLC_MLPERF_LOADGEN_LOGS_DIR'] = OUTPUT_DIR

    if mode == "accuracy":
        output_dir = env['MLC_MLPERF_OUTPUT_DIR']
        env['MLC_MLPERF_ACCURACY_RESULTS_DIR'] = output_dir
    else:
        env['MLC_MLPERF_ACCURACY_RESULTS_DIR'] = ''

    run_exists = run_files_exist(
        log_mode,
        OUTPUT_DIR,
        required_files,
        env,
        logger)

    if 'MLC_MLPERF_POWER' in env and env.get(
            'MLC_MLPERF_SHORT_RANGING_RUN', '') != 'no' and env['MLC_MLPERF_RUN_STYLE'] == "valid" and mode == "performance":
        short_ranging = True
    else:
        short_ranging = False

    if short_ranging:
        import copy
        ranging_user_conf = copy.deepcopy(user_conf)
        ranging_user_conf += ml_model_name + "." + \
            scenario + ".min_duration = 300000" + "\n"

    if env['MLC_MLPERF_RUN_STYLE'] == "test":
        max_duration_test_s = int(env.get('MLC_MLPERF_MAX_DURATION_TEST', 30))
        max_duration_test = str(max_duration_test_s * 1000)  # in milliseconds
        query_count = int(env.get('MLC_TEST_QUERY_COUNT', 5))
        min_query_count = int(
            env.get(
                'MLC_MLPERF_INFERENCE_MIN_QUERY_COUNT',
                query_count))
        max_query_count = max(
            min_query_count, int(
                env.get(
                    'MLC_MLPERF_INFERENCE_MAX_QUERY_COUNT', query_count)))
        user_conf += ml_model_name + "." + scenario + \
            ".max_query_count = " + str(max_query_count) + "\n"
        user_conf += ml_model_name + "." + scenario + \
            ".min_query_count = " + str(min_query_count) + "\n"
        user_conf += ml_model_name + "." + scenario + ".min_duration = 0" + "\n"
        user_conf += ml_model_name + "." + scenario + \
            ".sample_concatenate_permutation = 0" + "\n"
        env['MLC_MLPERF_MAX_QUERY_COUNT'] = max_query_count

        # max_duration is effective for all scenarios except the Offline
        if not is_false(env.get('MLC_MLPERF_USE_MAX_DURATION', 'yes')):
            if scenario != "Offline":
                user_conf += ml_model_name + "." + scenario + \
                    f".max_duration = {max_duration_test}" + "\n"

    elif env['MLC_MLPERF_RUN_STYLE'] == "fast":
        user_conf += ml_model_name + "." + scenario + \
            ".sample_concatenate_permutation = 0" + "\n"
        max_duration_fast_s = int(env.get('MLC_MLPERF_MAX_DURATION_FAST', 120))
        max_duration_fast = str(max_duration_fast_s * 1000)  # in milliseconds
        if scenario == "Server" or scenario == "ConstantStream":
            user_conf += ml_model_name + "." + scenario + \
                f".max_duration = {max_duration_fast}" + "\n"
            target_qps = conf['target_qps']
            query_count = str(int((660 / fast_factor) * (float(target_qps))))
            user_conf += ml_model_name + "." + scenario + \
                ".max_query_count = " + query_count + "\n"
            env['MLC_MLPERF_MAX_QUERY_COUNT'] = query_count

    else:
        max_duration_valid_s = int(
            env.get('MLC_MLPERF_MAX_DURATION_VALID', 660))
        max_duration_valid = str(
            max_duration_valid_s *
            1000)  # in milliseconds
        max_duration_ranging_s = int(
            env.get('MLC_MLPERF_MAX_DURATION_RANGING', 300))
        max_duration_ranging = str(
            max_duration_ranging_s *
            1000)  # in milliseconds
        if scenario in ["MultiStream", "SingleStream"]:
            if env.get('MLC_MLPERF_INFERENCE_MIN_DURATION', '') != '':
                user_conf += ml_model_name + "." + scenario + ".min_duration = " + \
                    env['MLC_MLPERF_INFERENCE_MIN_DURATION'] + " \n"
            elif not is_false(env.get('MLC_MLPERF_USE_MAX_DURATION', 'yes')) and not is_true(env.get(
                    'MLC_MLPERF_MODEL_EQUAL_ISSUE_MODE', 'no')) and env.get('MLC_MLPERF_SINGLESTREAM_TARGET_LATENCY_PERCENTILE') != '99.9':
                user_conf += ml_model_name + "." + scenario + \
                    f".max_duration = {max_duration_valid}" + "\n"
            if scenario in ["SingleStream"] and env.get('MLC_MLPERF_SINGLESTREAM_TARGET_LATENCY_PERCENTILE') == '99.9' and env.get(
                    'MLC_MLPERF_DEFAULT_MAX_QUERY_COUNT', '') != '' and env.get('MLC_MLPERF_TARGET_LATENCY', '') == '':
                user_conf += ml_model_name + "." + scenario + \
                    f".max_query_count = {env.get('MLC_MLPERF_DEFAULT_MAX_QUERY_COUNT')}" + "\n"
            if scenario == "MultiStream":
                user_conf += ml_model_name + "." + scenario + ".min_query_count = " + \
                    env.get(
                        'MLC_MLPERF_INFERENCE_MULTISTREAM_MIN_QUERY_COUNT',
                        "662") + "\n"
            if short_ranging:
                ranging_user_conf += ml_model_name + "." + scenario + \
                    f".max_duration = {max_duration_ranging} \n "
        elif scenario == "Offline":
            query_count = int(float(conf['target_qps']) * 660)
            query_count = str(max(query_count, required_min_queries_offline))

            # user_conf += ml_model_name + "." + scenario + ".max_query_count = " + str(int(query_count)+40) + "\n"
            if short_ranging:
                ranging_query_count = str(int(float(conf['target_qps']) * 300))
                ranging_user_conf += ml_model_name + "." + scenario + \
                    ".max_query_count = " + str(ranging_query_count) + "\n"
                ranging_user_conf += ml_model_name + "." + scenario + ".min_query_count = 0 \n"

    if query_count:
        # needed for squad accuracy checker
        env['MLC_MAX_EXAMPLES'] = str(query_count)

    import uuid
    from pathlib import Path
    key = uuid.uuid4().hex
    user_conf_path = os.path.join(script_path, "tmp", key + ".conf")
    user_conf_file = Path(user_conf_path)
    user_conf_file.parent.mkdir(exist_ok=True, parents=True)
    user_conf_file.write_text(user_conf)

    if short_ranging:
        ranging_user_conf_path = os.path.join(
            script_path, "tmp", "ranging_" + key + ".conf")
        ranging_user_conf_file = Path(ranging_user_conf_path)
        ranging_user_conf_file.write_text(ranging_user_conf)

    if (env.get('MLC_MLPERF_LOADGEN_QUERY_COUNT', '') == '') and query_count and (
            (mode != "accuracy") or (env['MLC_MLPERF_RUN_STYLE'] != "valid")):
        env['MLC_MLPERF_LOADGEN_QUERY_COUNT'] = str(query_count)

    if not run_exists or rerun:

        logger.info("Output Dir: '" + OUTPUT_DIR + "'")
        logger.info(user_conf)
        if env.get('MLC_MLPERF_POWER', '') == "yes" and os.path.exists(
                env.get('MLC_MLPERF_POWER_LOG_DIR', '')):
            shutil.rmtree(env['MLC_MLPERF_POWER_LOG_DIR'])
    else:
        if not env.get('MLC_MLPERF_COMPLIANCE_RUN_POSTPONED', False):
            logger.warning("Run files exist, skipping run...\n")
        env['MLC_MLPERF_SKIP_RUN'] = "yes"

    if not run_exists or rerun or not measure_files_exist(OUTPUT_DIR,
                                                          required_files[4]) or env.get("MLC_MLPERF_LOADGEN_COMPLIANCE", "") == "yes" or env.get("MLC_REGENERATE_MEASURE_FILES", False):

        env['MLC_MLPERF_TESTING_USER_CONF'] = os.path.join(
            os.path.dirname(user_conf_path), key + ".conf")  # user_conf_path
        env['MLC_MLPERF_RANGING_USER_CONF'] = os.path.join(
            os.path.dirname(user_conf_path),
            "ranging_" + key + ".conf")  # ranging_user_conf_path for a shorter run

        if short_ranging:
            env['MLC_MLPERF_USER_CONF'] = r"\${MLC_MLPERF_USER_CONF}"
        else:
            env['MLC_MLPERF_USER_CONF'] = os.path.join(
                os.path.dirname(user_conf_path), key + ".conf")  # user_conf_path
    else:
        print(
            f"Measure files exist at {OUTPUT_DIR}. Skipping regeneration...\n")
        env['MLC_MLPERF_USER_CONF'] = ''

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if is_true(env.get('MLC_MLPERF_RESULTS_DIR_SHARED', '')):
        os.chmod(OUTPUT_DIR, 0o2775)

    return {'return': 0}


def run_files_exist(mode, OUTPUT_DIR, run_files, env, logger):
    import submission_checker as checker
    from log_parser import MLPerfLog

    is_valid = True

    file_loc = {
        "accuracy": 0,
        "performance": 1,
        "power": 2,
        "performance_power": 3,
        "measure": 4,
        "compliance": 1}

    required_files = run_files[file_loc[mode]]
    if mode == "performance_power":
        for file_ in run_files[2]:
            file_path = os.path.join(
                os.path.dirname(OUTPUT_DIR), "power", file_)
            if (not os.path.exists(file_path)
                    or os.stat(file_path).st_size == 0):
                return False
        # We need performance files too in the run directory
        required_files += run_files[1]

    for file_ in required_files:
        file_path = os.path.join(OUTPUT_DIR, file_)
        if (not os.path.exists(file_path) or os.stat(
                file_path).st_size == 0) and file_ != "accuracy.txt":
            return False

        if file_ == "mlperf_log_detail.txt" and "performance" in mode:
            mlperf_log = MLPerfLog(file_path)
            if (
                "result_validity" not in mlperf_log.get_keys()
                or mlperf_log["result_validity"] != "VALID"
                or "error_invalid_config" in mlperf_log.get_keys()
            ):
                return False

    if mode == "compliance":
        # If a performance run followed the last compliance run, compliance
        # check needs to be redone
        RESULT_DIR = os.path.split(OUTPUT_DIR)[0]
        COMPLIANCE_DIR = OUTPUT_DIR
        OUTPUT_DIR = os.path.dirname(COMPLIANCE_DIR)

        # If reference test result is invalid, don't do compliance run
        file_path = os.path.join(
            RESULT_DIR,
            "performance",
            "run_1",
            "mlperf_log_detail.txt")
        mlperf_log = MLPerfLog(file_path)
        if (
            "result_validity" not in mlperf_log.get_keys()
            or mlperf_log["result_validity"] != "VALID"
        ):
            env['MLC_MLPERF_COMPLIANCE_RUN_POSTPONED'] = True
            return True

        test = env['MLC_MLPERF_LOADGEN_COMPLIANCE_TEST']

        if env['MLC_BENCHMARK_GROUP'] == "automotive":
            SCRIPT_PATH = os.path.join(
                env['MLC_MLPERF_INFERENCE_SOURCE'],
                "compliance",
                test,
                "run_verification.py")
        else:
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

        logger.info(cmd)
        os.system(cmd)

        is_valid = checker.check_compliance_perf_dir(COMPLIANCE_DIR)

        if not is_valid and 'Stream' in env['MLC_MLPERF_LOADGEN_SCENARIO']:
            # We have the determined latency, compliance test failed, so lets
            # not use max duration
            env['MLC_MLPERF_USE_MAX_DURATION'] = 'no'
            env['MLC_MLPERF_INFERENCE_MIN_DURATION'] = '990000'  # Try a longer run

        return is_valid

    if "power" in mode and not is_true(
            env.get('MLC_MLPERF_SKIP_POWER_CHECKS', 'no')):
        from power.power_checker import check as check_power_more
        try:
            is_valid = check_power_more(os.path.dirname(OUTPUT_DIR)) == 0
        except BaseException:
            is_valid = False
        return is_valid

    return is_valid


def measure_files_exist(OUTPUT_DIR, run_files):
    for file in run_files:
        file_path = os.path.join(OUTPUT_DIR, file)
        if not os.path.exists(file_path):
            return False
    return True


def get_checker_files():
    import submission_checker as checker

    REQUIRED_ACC_FILES = checker.REQUIRED_ACC_FILES
    REQUIRED_PERF_FILES = checker.REQUIRED_PERF_FILES
    REQUIRED_POWER_FILES = checker.REQUIRED_POWER_FILES
    REQUIRED_PERF_POWER_FILES = checker.REQUIRED_PERF_POWER_FILES
    REQUIRED_MEASURE_FILES = checker.REQUIRED_MEASURE_FILES
    return REQUIRED_ACC_FILES, REQUIRED_PERF_FILES, REQUIRED_POWER_FILES, REQUIRED_PERF_POWER_FILES, REQUIRED_MEASURE_FILES


def get_required_min_queries_offline(model, version):

    import submission_checker as checker

    version_split = version.split(".")
    if int(version[0]) < 4:
        return 24756

    REQUIRED_MIN_QUERIES = checker.OFFLINE_MIN_SPQ_SINCE_V4
    mlperf_model = model
    mlperf_model = mlperf_model.replace("resnet50", "resnet")

    if "llama3_1" in mlperf_model:
        mlperf_model = mlperf_model.replace("_", ".")

    return REQUIRED_MIN_QUERIES[mlperf_model]
