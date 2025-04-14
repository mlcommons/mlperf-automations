from mlc import utils
from utils import is_true
import os


def preprocess(i):
    os_info = i['os_info']
    env = i['env']

    return {'return': 0}


def postprocess(i):

    os_info = i['os_info']
    env = i['env']

    env['MLC_MLPERF_RUN_CMD'] = env.get('MLC_RUN_CMD')

    if is_true(env.get('MLC_MLPERF_POWER', '')):

        if not is_false(env.get('MLC_MLPERF_SHORT_RANGING_RUN', '')):
            # Write '0' to the count.txt file in MLC_RUN_DIR
            count_file = os.path.join(env.get('MLC_RUN_DIR', ''), 'count.txt')
            with open(count_file, 'w') as f:
                f.write('0')

            if os_info['platform'] != 'windows':
                # Construct the shell command with proper escaping
                env['MLC_MLPERF_RUN_CMD'] = r"""
MLC_MLPERF_RUN_COUNT=\$(cat \${MLC_RUN_DIR}/count.txt);
echo \${MLC_MLPERF_RUN_COUNT};
MLC_MLPERF_RUN_COUNT=\$((MLC_MLPERF_RUN_COUNT+1));
echo \${MLC_MLPERF_RUN_COUNT} > \${MLC_RUN_DIR}/count.txt;

if [ \${MLC_MLPERF_RUN_COUNT} -eq 1 ]; then
export MLC_MLPERF_USER_CONF="\${MLC_MLPERF_RANGING_USER_CONF}";
else
export MLC_MLPERF_USER_CONF="\${MLC_MLPERF_TESTING_USER_CONF}";
fi
;

                """ + env.get('MLC_RUN_CMD', '').strip()
            else:
                env['MLC_MLPERF_RUN_CMD'] = r"""
:: Read the current count from the file
set /p MLC_MLPERF_RUN_COUNT=<%MLC_RUN_DIR%\count.txt
echo !MLC_MLPERF_RUN_COUNT!

:: Increment the count
set /a MLC_MLPERF_RUN_COUNT=!MLC_MLPERF_RUN_COUNT! + 1
echo !MLC_MLPERF_RUN_COUNT! > %MLC_RUN_DIR%\count.txt

:: Check the value and set the environment variable accordingly
if !MLC_MLPERF_RUN_COUNT! EQU 1 (
    set MLC_MLPERF_USER_CONF=%MLC_MLPERF_RANGING_USER_CONF%
) else (
    set MLC_MLPERF_USER_CONF=%MLC_MLPERF_TESTING_USER_CONF%
)
                """ + env.get('MLC_RUN_CMD', '').strip()
        else:
            # Just use the existing MLC_RUN_CMD if no ranging run is needed
            env['MLC_MLPERF_RUN_CMD'] = env.get('MLC_RUN_CMD', '').strip()

    return {'return': 0}
