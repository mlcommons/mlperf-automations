from mlc import utils
import os
import configparser


def preprocess(i):

    os_info = i['os_info']
    env = i['env']

    if not env['MLC_MLPERF_RUN_CMD']:
        env['MLC_MLPERF_RUN_CMD'] = os.path.join(
            i['run_script_input']['path'], "dummy.sh")

    if 'MLC_MLPERF_POWER_TIMESTAMP' in env:
        timestamp = ""
    else:
        timestamp = " --no-timestamp-path"

    if 'MLC_MLPERF_LOADGEN_LOGS_DIR' not in env:
        env['MLC_MLPERF_LOADGEN_LOGS_DIR'] = os.path.join(
            os.getcwd(), "loadgen_logs")

    run_cmd = env['MLC_MLPERF_RUN_CMD'].replace("'", '"')
    run_cmd = run_cmd.replace('"', '\\"')
    cmd = env['MLC_PYTHON_BIN_WITH_PATH'] + ' ' +\
        os.path.join(env['MLC_MLPERF_POWER_SOURCE'], 'ptd_client_server', 'client.py') + \
        " -a " + env['MLC_MLPERF_POWER_SERVER_ADDRESS'] + \
        " -p " + env.get('MLC_MLPERF_POWER_SERVER_PORT', "4950") + \
        " -w '" + run_cmd + \
        "' -L " + env['MLC_MLPERF_LOADGEN_LOGS_DIR'] + \
        " -o " + env['MLC_MLPERF_POWER_LOG_DIR'] + \
        " -n " + env['MLC_MLPERF_POWER_NTP_SERVER'] + \
        timestamp

    if 'MLC_MLPERF_POWER_MAX_AMPS' in env and 'MLC_MLPERF_POWER_MAX_VOLTS' in env:
        cmd = cmd + " --max-amps " + env['MLC_MLPERF_POWER_MAX_AMPS'] + \
            " --max-volts " + env['MLC_MLPERF_POWER_MAX_VOLTS']

    env['MLC_MLPERF_POWER_RUN_CMD'] = cmd

    return {'return': 0}
