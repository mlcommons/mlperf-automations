import os
import subprocess


def main():
    submission_dir = os.environ.get('MLC_MLPERF_TRAINING_RESULTS_PATH', '').strip()
    ruleset = os.environ.get('MLC_MLPERF_TRAINING_RESULTS_RULESET', '').strip()
    summary_csv = os.environ.get('MLC_MLPERF_TRAINING_RESULTS_SUMMARY_CSV', '').strip()

    if submission_dir == '':
        raise RuntimeError('MLC_MLPERF_TRAINING_RESULTS_PATH is not set')
    if ruleset == '':
        raise RuntimeError('MLC_MLPERF_TRAINING_RESULTS_RULESET is not set')
    if summary_csv == '':
        raise RuntimeError('MLC_MLPERF_TRAINING_RESULTS_SUMMARY_CSV is not set')

    cmd = [
        os.environ.get('MLC_PYTHON_BIN_WITH_PATH', 'python'),
        '-m',
        'mlperf_logging.result_summarizer',
        submission_dir,
        'training',
        ruleset,
        '--csv',
        summary_csv
    ]
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as exc:
        raise RuntimeError('Python executable not found: {}'.format(cmd[0])) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            'Failed to generate training summary using command: {} (exit code {})'.format(
                ' '.join(cmd), exc.returncode
            )
        ) from exc


if __name__ == '__main__':
    main()
