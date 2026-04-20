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

    summarizer_input_dir = submission_dir
    if not os.path.isdir(os.path.join(submission_dir, 'results')):
        # Training results repos can be organized as /<org>/{systems,results,benchmarks}.
        # In that case, ask result_summarizer to auto-discover all orgs.
        summarizer_input_dir = os.path.join(submission_dir, '{*}')

    cmd = [
        os.environ.get('MLC_PYTHON_BIN_WITH_PATH', 'python'),
        '-m',
        'mlperf_logging.result_summarizer',
        summarizer_input_dir,
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
