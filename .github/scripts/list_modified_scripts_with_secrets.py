import yaml
import sys
import json
import os


def get_file_info(filepath):
    with open(filepath, 'r') as file:
        content = yaml.safe_load(file)
        tests = content.get('tests', [])
        needs_pat = content.get('needs_pat', False)
        if tests and needs_pat:
            num_tests = len(tests.get('run_inputs', []))
        else:
            num_tests = 0
        uid = content['uid']
        return uid, num_tests


def process_files(files):
    filenames = files.split(",")
    return [
        {
            "file": file,
            "uid": uid,
            "num_run": i
        }
        for file in filenames if os.path.basename(file) == 'meta.yaml'
        for uid, num_tests in [get_file_info(file)]
        for i in range(1, num_tests + 1)
    ]


if __name__ == "__main__":
    changed_files = sys.stdin.read().strip()
    processed_files = process_files(changed_files)
    json_processed_files = json.dumps(processed_files)
    print(json_processed_files)