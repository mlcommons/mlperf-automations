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

    if env.get('MLC_RUN_DIR', '') == '':
        env['MLC_RUN_DIR'] = os.getcwd()
    logs_dir = env.get('MLC_LOGS_DIR', env['MLC_RUN_DIR'])

    # perf / instruction-mix profiling (opt-in via _perf-record / _perf-stat /
    # _insmix or --perf_record / --perf_stat / --insmix). Wraps MLC_RUN_CMD.
    perf_out = env.get('MLC_BENCHMARK_PERF_OUTPUT_DIR', '') or logs_dir
    requested = [m for m in (
        ('record', env.get('MLC_BENCHMARK_PERF_RECORD', '')),
        ('insmix', env.get('MLC_BENCHMARK_INSMIX', '')),
        ('stat', env.get('MLC_BENCHMARK_PERF_STAT', ''))) if is_true(m[1])]
    perf_post_cmd = ''
    if requested and os_info['platform'] != 'windows':
        if len(requested) > 1:
            logger.warning('Multiple perf modes requested ({}); using {}'.format(
                ', '.join(m[0] for m in requested), requested[0][0]))
        mode = requested[0][0]
        if mode == 'record':
            data = os.path.join(perf_out, 'perf.data')
            freq = env.get('MLC_BENCHMARK_PERF_FREQ', '')
            freq_opt = '-F ' + freq + ' ' if freq else ''
            perf_prefix = 'perf record -g ' + freq_opt + '-o ' + q + data + q + ' -- '
            report = os.path.join(perf_out, 'perf_report.txt')
            perf_post_cmd = ('perf report -i ' + q + data + q + ' --stdio > ' +
                             q + report + q + ' 2>/dev/null || true')
            env['MLC_BENCHMARK_PERF_DATA'] = data
            env['MLC_BENCHMARK_PERF_REPORT_FILE'] = report
        elif mode == 'insmix':
            # True dynamic instruction mix via Intel SDE (emulated, host-agnostic).
            sde_bin = env.get('MLC_INTEL_SDE_BIN_WITH_PATH', 'sde64')
            out = os.path.join(perf_out, 'sde-mix-out.txt')
            perf_prefix = q + sde_bin + q + ' -mix -omix ' + q + out + q + ' -- '
            perf_post_cmd = 'echo Intel SDE instruction mix written to ' + q + out + q
            env['MLC_BENCHMARK_INSMIX_FILE'] = out
        else:  # stat
            events = env.get('MLC_BENCHMARK_PERF_EVENTS', '')
            ev_opt = '-e ' + events + ' ' if events else ''
            out = os.path.join(perf_out, 'perf_stat.txt')
            perf_prefix = 'perf stat ' + ev_opt + '-o ' + q + out + q + ' '
            perf_post_cmd = ('echo ===== perf stat ===== && cat ' +
                             q + out + q)
            env['MLC_BENCHMARK_PERF_STAT_FILE'] = out
        env['MLC_RUN_PREFIX0'] = perf_prefix + env.get('MLC_RUN_PREFIX0', '')
        logger.info('Perf profiling enabled ({}): {}'.format(mode, perf_prefix))

    x = env.get('MLC_RUN_PREFIX0', '')
    if x != '':
        env['MLC_RUN_CMD'] = x + ' ' + env.get('MLC_RUN_CMD', '')

    if os_info['platform'] != 'windows' and not is_false(
            env.get('MLC_SAVE_CONSOLE_LOG', True)):
        env['MLC_RUN_CMD'] += r" 2>&1 | tee " + q + os.path.join(
            logs_dir, "console.out") + q + r"; echo \${PIPESTATUS[0]} > exitstatus"

    enable_system_info_profiling = env.get(
        'MLC_PROFILE_NVIDIA_POWER', '') == "on" or is_true(
        env.get('MLC_PROFILE_SYSTEM_INFO', ''))

    # additional arguments and tags for measuring system informations
    if enable_system_info_profiling:
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

    if enable_system_info_profiling:
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
    if enable_system_info_profiling:
        post_run_cmd += r"echo killing process \$cmd_pid && kill -TERM \${cmd_pid}"
        print(
            f"Post run command for killing the process that measures the runtime system information: {post_run_cmd}")

    # perf record needs a post-run step to render the human-readable report.
    if perf_post_cmd:
        post_run_cmd = post_run_cmd + ' ; ' + perf_post_cmd if post_run_cmd else perf_post_cmd

    env['MLC_POST_RUN_CMD'] = post_run_cmd

    # Print info
    logger.info(
        '***************************************************************************')
    logger.info('MLC script::benchmark-program/run.sh')
    logger.info('')
    logger.info('Run Directory: {}'.format(env.get('MLC_RUN_DIR', '')))

    logger.info('')
    logger.info('CMD: {}'.format(env.get('MLC_RUN_CMD', '')))

    logger.info('')

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
