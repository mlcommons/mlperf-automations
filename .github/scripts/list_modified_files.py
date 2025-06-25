import yaml
import sys
import json
import os


def get_file_info(filepath):
    with open(filepath, 'r') as file:
        content = yaml.safe_load(file)
        tests = content.get('tests', [])
        needs_pat = content.get('needs_pat', False)
        if tests and not needs_pat:
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


def get_modified_metas(files):
    filenames = files.split(",")
    return [
        {
            "file": file,
            "uid": uid,
        }
        for file in filenames if os.path.basename(file) == 'meta.yaml'
        for uid, num_tests in [get_file_info(file)]
    ]


if __name__ == "__main__":
    changed_files = sys.stdin.read().strip()
    processed_files = process_files(changed_files)
    modified_metas = get_modified_metas(changed_files)
    json_processed_files = json.dumps(processed_files)
    print(json_processed_files)
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write(
            f"processed_files={json.dumps({'file_info': processed_files, 'modified_metas': modified_metas})}\n")
