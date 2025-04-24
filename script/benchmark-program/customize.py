from mlc import utils
import os
from utils import *


def preprocess(i):
    os_info = i['os_info']
    env = i['env']
    logger = i['automation'].logger
    q = '"' if os_info['platform'] == 'windows' else "'"

    if env.get('MLC_RUN_CMD', '') == '':
        if env.get('MLC_BIN_NAME', '') == '':
            x = 'run.exe' if os_info['platform'] == 'windows' else 'run.out'
            env['MLC_BIN_NAME'] = x

        if os_info['platform'] == 'windows':
            env['MLC_RUN_CMD'] = env.get(
                'MLC_RUN_PREFIX', '') + env['MLC_BIN_NAME']
            if env.get('MLC_RUN_SUFFIX', '') != '':
                env['MLC_RUN_CMD'] += ' ' + env['MLC_RUN_SUFFIX']

        else:
            if is_true(env['MLC_ENABLE_NUMACTL']):
                env['MLC_ENABLE_NUMACTL'] = "1"
                MLC_RUN_PREFIX = "numactl " + env['MLC_NUMACTL_MEMBIND'] + ' '
            else:
                MLC_RUN_PREFIX = ''

            MLC_RUN_PREFIX += env.get('MLC_RUN_PREFIX', '')

            env['MLC_RUN_PREFIX'] = MLC_RUN_PREFIX

            MLC_RUN_SUFFIX = (
                env['MLC_REDIRECT_OUT'] +
                ' ') if 'MLC_REDIRECT_OUT' in env else ''
            MLC_RUN_SUFFIX += (env['MLC_REDIRECT_ERR'] +
                               ' ') if 'MLC_REDIRECT_ERR' in env else ''

            env['MLC_RUN_SUFFIX'] = env['MLC_RUN_SUFFIX'] + \
                MLC_RUN_SUFFIX if 'MLC_RUN_SUFFIX' in env else MLC_RUN_SUFFIX

            if env.get('MLC_RUN_DIR', '') == '':
                env['MLC_RUN_DIR'] = os.getcwd()

            env['MLC_RUN_CMD'] = f"""{MLC_RUN_PREFIX} {q}{os.path.join(env['MLC_RUN_DIR'], env['MLC_BIN_NAME'])}{q} {env['MLC_RUN_SUFFIX']}"""

    x = env.get('MLC_RUN_PREFIX0', '')
    if x != '':
        env['MLC_RUN_CMD'] = x + ' ' + env.get('MLC_RUN_CMD', '')

    if os_info['platform'] != 'windows' and not is_false(
            env.get('MLC_SAVE_CONSOLE_LOG', True)):
        logs_dir = env.get('MLC_LOGS_DIR', env['MLC_RUN_DIR'])
        env['MLC_RUN_CMD'] += r" 2>&1 | tee " + q + os.path.join(
            logs_dir, "console.out") + q + r"; echo \${PIPESTATUS[0]} > exitstatus"

    # additional arguments and tags for measuring system informations(only if
    # 'MLC_PROFILE_NVIDIA_POWER' is 'on')
    if env.get('MLC_PROFILE_NVIDIA_POWER', '') == "on":
        env['MLC_SYS_UTILISATION_SCRIPT_TAGS'] = ''
        # this section is for selecting the variation
        if env.get('MLC_MLPERF_DEVICE', '') == "gpu":
            env['MLC_SYS_UTILISATION_SCRIPT_TAGS'] += ',_cuda'
        elif env.get('MLC_MLPERF_DEVICE', '') == "cpu":
            env['MLC_SYS_UTILISATION_SCRIPT_TAGS'] += ',_cpu'
        # this section is for supplying the input arguments/tags
        env['MLC_SYS_UTILISATION_SCRIPT_TAGS'] += ' --log_dir=\'' + \
            logs_dir + '\''   # specify the logs directory
        # specifying the interval in which the system information should be
        # measured
        if env.get('MLC_SYSTEM_INFO_MEASUREMENT_INTERVAL', '') != '':
            env['MLC_SYS_UTILISATION_SCRIPT_TAGS'] += ' --interval=\"' + \
                env['MLC_SYSTEM_INFO_MEASUREMENT_INTERVAL'] + '\"'

    # generate the pre run cmd - recording runtime system infos
    pre_run_cmd = ""

    if env.get('MLC_PRE_RUN_CMD_EXTERNAL', '') != '':
        pre_run_cmd += env['MLC_PRE_RUN_CMD_EXTERNAL']

    if env.get('MLC_PROFILE_NVIDIA_POWER', '') == "on":
        if pre_run_cmd != '':
            pre_run_cmd += ' && '

        # running the script as a process in background
        pre_run_cmd = pre_run_cmd + 'mlcr runtime,system,utilisation' + \
            env['MLC_SYS_UTILISATION_SCRIPT_TAGS'] + ' --quiet  & '
        # obtain the command if of the background process
        pre_run_cmd += r" cmd_pid=\$!  && echo CMD_PID=\$cmd_pid"
        print(
            f"Pre run command for recording the runtime system information: {pre_run_cmd}")

    env['MLC_PRE_RUN_CMD'] = pre_run_cmd

    # generate the post run cmd - for killing the process that records runtime
    # system infos
    post_run_cmd = ""
    if env.get('MLC_PROFILE_NVIDIA_POWER', '') == "on":
        post_run_cmd += r"echo killing process \$cmd_pid && kill -TERM \${cmd_pid}"
        print(
            f"Post run command for killing the process that measures the runtime system information: {post_run_cmd}")

    env['MLC_POST_RUN_CMD'] = post_run_cmd

    # Print info
    logger.info('***************************************************************************')
    logger.info('CM script::benchmark-program/run.sh')
    logger.info('')
    logger.info('Run Directory: {}'.format(env.get('MLC_RUN_DIR', '')))

    logger.info('')
    logger.info('CMD: {}'.format(env.get('MLC_RUN_CMD', '')))

    logger.info('')

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
