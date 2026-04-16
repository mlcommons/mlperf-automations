import yaml
import sys
import json
import os

TRIGGER_FILES = ['meta.yaml', 'customize.py', 'run.sh']


def get_file_info(filepath):
    with open(filepath, 'r') as file:
        content = yaml.safe_load(file)
        tests = content.get('tests', {})
        needs_pat = tests.get('needs_pat', False)
        if tests and not needs_pat:
            num_tests = len(tests.get('run_inputs', []))
        else:
            num_tests = 0
        uid = content['uid']
        return uid, num_tests


def deduplicate_by_directory(filenames):
    """For each directory, return at most one file using priority: meta.yaml > customize.py > run.sh"""
    priority = {name: i for i, name in enumerate(TRIGGER_FILES)}
    dir_best = {}
    for file in filenames:
        basename = os.path.basename(file)
        if basename not in priority:
            continue
        dirpath = os.path.dirname(file)
        if dirpath not in dir_best or priority[basename] < priority[os.path.basename(dir_best[dirpath])]:
            dir_best[dirpath] = file
    return list(dir_best.values())


def get_meta_path(filepath):
    """Return the meta.yaml path in the same directory as filepath."""
    return os.path.join(os.path.dirname(filepath), 'meta.yaml')


def process_files(files):
    filenames = files.split(",")
    selected = deduplicate_by_directory(filenames)
    return [
        {
            "file": file,
            "uid": uid,
            "num_run": i
        }
        for file in selected
        for uid, num_tests in [get_file_info(get_meta_path(file))]
        for i in range(1, num_tests + 1)
    ]


def get_modified_metas(files):
    filenames = files.split(",")
    selected = deduplicate_by_directory(filenames)
    return [
        {
            "file": file,
            "uid": uid,
        }
        for file in selected
        for uid, num_tests in [get_file_info(get_meta_path(file))]
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
