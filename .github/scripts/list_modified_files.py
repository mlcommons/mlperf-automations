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


def get_trigger_directories(filenames):
    """Return unique directories that contain a changed trigger file (meta.yaml, customize.py, run.sh)."""
    dirs = set()
    for file in filenames:
        if os.path.basename(file) in TRIGGER_FILES:
            dirs.add(os.path.dirname(file))
    return dirs


def get_meta_paths(files):
    """Return deduplicated meta.yaml paths for directories with any trigger file changed."""
    filenames = files.split(",")
    dirs = get_trigger_directories(filenames)
    return [os.path.join(d, 'meta.yaml') for d in dirs]


def process_files(files):
    meta_paths = get_meta_paths(files)
    return [
        {
            "file": meta,
            "uid": uid,
            "num_run": i
        }
        for meta in meta_paths
        for uid, num_tests in [get_file_info(meta)]
        for i in range(1, num_tests + 1)
    ]


def get_modified_metas(files):
    meta_paths = get_meta_paths(files)
    return [
        {
            "file": meta,
            "uid": uid,
        }
        for meta in meta_paths
        for uid, num_tests in [get_file_info(meta)]
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
