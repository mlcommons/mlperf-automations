# Developer: Grigori Fursin

import os


def main():
    # For now quick prototype hardwired to "summary.json" from MLPerf
    # Later need to clean it and make it universal

    print('')
    print('Reading summary.json ...')
    print('')

    import json
    filename = os.environ.get('MLPERF_INFERENCE_SUBMISSION_SUMMARY', '')
    if filename == '':
        filename = 'summary'
    filename += '.json'

    f = open(filename)

    results = json.load(f)

    f.close()

    print('=========================================================')
    print('Sending results to W&B dashboard ...')
    print('')

    import wandb

    env = os.environ

    dashboard_user = env.get('MLC_MLPERF_DASHBOARD_WANDB_USER', '')
    if dashboard_user == '':
        dashboard_user = 'cmind'

    dashboard_project = env.get('MLC_MLPERF_DASHBOARD_WANDB_PROJECT', '')
    if dashboard_project == '':
        dashboard_project = 'mlc-mlperf-dse-testing'

    for k in results:

        result = results[k]

        organization = str(result.get('Organization', ''))
        if organization == '':
            organization = 'anonymous'

        label = organization

        system_name = str(result.get('SystemName', ''))
        if system_name != '':
            label += '(' + system_name + ')'

        qps = result.get('Result', 0.0)
        # since v4.1 mlperf results return a key:value pairs for accuracy. We
        # are taking only the first key:value here
        result_acc = result.get('Accuracy')
        accuracy = 0.0
        if result_acc:
            acc_split = result_acc.split(":")
            if len(acc_split) > 1:
                accuracy = float(acc_split[1]) / 100

        result['performance'] = qps
        result['qps'] = qps
        result['accuracy'] = accuracy

        # Check extra env variables
        x = {
            "lang": "MLC_MLPERF_LANG",
            "device": "MLC_MLPERF_DEVICE",
            "submitter": "MLC_MLPERF_SUBMITTER",
            "backend": "MLC_MLPERF_BACKEND",
            "model": "MLC_MLPERF_MODEL",
            "run_style": "MLC_MLPERF_RUN_STYLE",
            "rerun": "MLC_RERUN",
            "hw_name": "MLC_HW_NAME",
            "max_batchsize": "MLC_MLPERF_LOADGEN_MAX_BATCHSIZE",
            "num_threads": "MLC_NUM_THREADS",
            "scenario": "MLC_MLPERF_LOADGEN_SCENARIO",
            "test_query_count": "MLC_TEST_QUERY_COUNT",
            "run_checker": "MLC_RUN_SUBMISSION_CHECKER",
            "skip_truncation": "MLC_SKIP_TRUNCATE_ACCURACY"
        }

        for k in x:
            env_key = x[k]
            if os.environ.get(env_key, '') != '':
                result['mlc_misc_input_' + k] = os.environ[env_key]

        wandb.init(entity=dashboard_user,
                   project=dashboard_project,
                   name=label)

        wandb.log(result)

        wandb.finish()

    print('=========================================================')


if __name__ == '__main__':
    main()
