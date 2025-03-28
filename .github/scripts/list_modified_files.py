import yaml
import sys
import json


def get_file_info(filepath):
    with open(filepath, 'r') as file:
        content = yaml.safe_load(file)
        tests = content.get('tests', [])
        if tests:
            num_tests = len(tests.get('run_inputs', []))
        else:
            num_tests = 0
        uid = content['uid']
        return uid, num_tests


def process_files(files):
    filenames = files.split()
    return [
        {
            "file": file,
            "uid": uid,
            "num_run": i
        }
        for file in filenames
        for uid, num_tests in [get_file_info(file)] if file.endswith('meta.yaml')
        for i in range(1, num_tests + 1)
    ]


if __name__ == "__main__":
    changed_files = sys.stdin.read().strip()
    processed_files = process_files(changed_files)
    json_processed_files = json.dumps(processed_files)
    print(f"::set-output name=processed_files::{json_processed_files}")
