import sys
import os
import mlc
import json
import yaml

files = sys.argv[1:]

for file in files:
    print(file)
    if not os.path.isfile(file) or not "script" in file:
        continue
    if not file.endswith("meta.json") and not file.endswith("meta.yaml"):
        continue
    script_path = os.path.dirname(file)
    f = open(file)
    if file.endswith(".json"):
        data = json.load(f)
    elif file.endswith(".yaml"):
        data = yaml.safe_load(f)
    if data.get('uid', '') == '':
        continue  # not a CM script meta
    uid = data['uid']

    ii = {
        'action': 'test', 'target': 'script', 'item': uid, 'quiet': 'yes', 'out': 'con'
    }
    if os.environ.get('DOCKER_MLC_REPO', '') != '':
        ii['docker_mlc_repo'] = os.environ['DOCKER_MLC_REPO']
    if os.environ.get('DOCKER_MLC_REPO_BRANCH', '') != '':
        ii['docker_mlc_repo_branch'] = os.environ['DOCKER_MLC_REPO_BRANCH']
    if os.environ.get('TEST_INPUT_INDEX', '') != '':
        ii['test_input_index'] = os.environ['TEST_INPUT_INDEX']
    print(ii)
    ret = mlc.access(ii)
    if ret['return'] > 0:
        raise Exception(r['error'])
    ii = {'action': 'rm', 'target': 'cache', 'f': True}
    ret = mlc.access(ii)
