# Developer: Grigori Fursin

from mlc import utils
import os
import shutil


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    logger = i['automation'].logger

    if 'MLC_ML_MODEL_FILE_WITH_PATH' not in env:
        return {
            'return': 1, 'error': 'Please select a variation specifying the model to run'}

    run_opts = env.get('MLC_RUN_OPTS', '')

    if env.get('MLC_MLPERF_BACKEND', '') != '':
        run_opts += " -b " + env['MLC_MLPERF_BACKEND']

    if env.get('MLC_MLPERF_RUNNER', '') != '':
        run_opts += " -r " + env['MLC_MLPERF_RUNNER']

    if env.get('MLC_MLPERF_CONCURRENCY', '') != '':
        run_opts += " --concurrency " + env['MLC_MLPERF_CONCURRENCY']

    if env.get('MLC_MLPERF_EXECUTION_PROVIDER', '') != '':
        run_opts += " --ep " + env['MLC_MLPERF_EXECUTION_PROVIDER']

    if env.get('MLC_MLPERF_INTRAOP', '') != '':
        run_opts += " --intraop " + env['MLC_MLPERF_INTRAOP']

    if env.get('MLC_MLPERF_INTEROP', '') != '':
        run_opts += " --interop " + env['MLC_MLPERF_INTEROP']

    if env.get('MLC_MLPERF_EXECMODE', '') != '':
        run_opts += " --execmode " + env['MLC_MLPERF_EXECUTION_MODE']

    if env.get('MLC_MLPERF_LOADGEN_SAMPLES', '') != '':
        run_opts += " --samples " + env['MLC_MLPERF_LOADGEN_SAMPLES']

    if env.get('MLC_MLPERF_LOADGEN_EXPECTED_QPS', '') != '':
        run_opts += " --loadgen_expected_qps " + \
            env['MLC_MLPERF_LOADGEN_EXPECTED_QPS']

    if env.get('MLC_MLPERF_LOADGEN_DURATION_SEC', '') != '':
        run_opts += " --loadgen_duration_sec " + \
            env['MLC_MLPERF_LOADGEN_DURATION_SEC']

    if env.get('MLC_MLPERF_OUTPUT_DIR', '') != '':
        run_opts += " --output " + env['MLC_MLPERF_OUTPUT_DIR']

    if env.get('MLC_ML_MODEL_CODE_WITH_PATH', '') != '':
        run_opts += " --model_code " + env['MLC_ML_MODEL_CODE_WITH_PATH']

    if env.get('MLC_ML_MODEL_CFG_WITH_PATH', '') != '':
        run_opts += " --model_cfg " + env['MLC_ML_MODEL_CFG_WITH_PATH']
    else:
        # Check cfg from command line
        cfg = env.get('MLC_ML_MODEL_CFG', {})
        if len(cfg) > 0:
            del (env['MLC_ML_MODEL_CFG'])

            import json
            import tempfile
            tfile = tempfile.NamedTemporaryFile(mode="w+", suffix='.json')

            fd, tfile = tempfile.mkstemp(suffix='.json', prefix='mlc-cfg-')
            os.close(fd)

            with open(tfile, 'w') as fd:
                json.dump(cfg, fd)

            env['MLC_APP_LOADGEN_GENERIC_PYTHON_TMP_CFG_FILE'] = tfile

            run_opts += " --model_cfg " + tfile

    if env.get('MLC_ML_MODEL_SAMPLE_WITH_PATH', '') != '':
        run_opts += " --model_sample_pickle " + \
            env['MLC_ML_MODEL_SAMPLE_WITH_PATH']

    # Add path to file model weights at the end of command line

    run_opts += ' ' + env['MLC_ML_MODEL_FILE_WITH_PATH']

    env['MLC_RUN_OPTS'] = run_opts

    logger.info('')
    logger.info('Assembled flags: {}'.format(run_opts))
    logger.info('')

    return {'return': 0}


def postprocess(i):

    env = i['env']

    tfile = env.get('MLC_APP_LOADGEN_GENERIC_PYTHON_TMP_CFG_FILE', '')

    if tfile != '' and os.path.isfile(tfile):
        os.remove(tfile)

    return {'return': 0}
