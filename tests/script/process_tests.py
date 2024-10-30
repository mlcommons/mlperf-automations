import sys
import os
import cmind as cm
import check as checks
import json
import yaml

files=sys.argv[1:]

for file in files:
    print(file)
    if not os.path.isfile(file):
        continue
    if not file.endswith("_cm.json") and not file.endswith("_cm.yaml"):
        continue
    script_path = os.path.dirname(file)
    f = open(file)
    if file.endswith(".json"):
        data = json.load(f)
    elif file.endswith(".yaml"):
        data = yaml.safe_load(f)
    uid = data['uid']

    r = cm.access({'action':'test', 'automation':'script', 'artifact': uid, 'quiet': 'yes', 'out': 'con'})
    checks.check_return(r)
