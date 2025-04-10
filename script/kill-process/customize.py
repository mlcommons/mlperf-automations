from mlc import utils
import os
import subprocess


def generate_kill_command(env):
    kill_cmd = ""

    if env.get("MLC_KILL_PROCESS_GROUP"):
        if env.get("MLC_KILL_PROCESS_ID"):
            process_id = env["MLC_KILL_PROCESS_ID"]
            # Find process group and kill all processes in it
            kill_cmd = f"pkill -g $(ps -o pgid= -p {process_id} | tr -d ' ')"

        elif env.get("MLC_KILL_PROCESS_NAME"):
            process_name = env["MLC_KILL_PROCESS_NAME"]
            # Find process group of the first matching process name and kill
            # all in that group
            kill_cmd = f"pkill -g $(pgrep -o {process_name} | xargs ps -o pgid= -p | tr -d ' ')"

        elif is_true(env.get("MLC_KILL_BUSIEST_PROCESS_GROUP")):
            kill_cmd = r"busy_pgid=\$(ps -eo pgid,pcpu --sort=-pcpu | head -n 2 | tail -n 1 | awk '{print $1}') && kill -- -\$busy_pgid"

    else:
        if env.get("MLC_KILL_PROCESS_ID"):
            process_id = env["MLC_KILL_PROCESS_ID"]
            kill_cmd = f"kill {process_id}"  # Kill a single process by ID

        elif env.get("MLC_KILL_PROCESS_NAME"):
            process_name = env["MLC_KILL_PROCESS_NAME"]
            # Kill all processes matching the name
            kill_cmd = f"pkill {process_name}"

    
    env["MLC_RUN_CMD"] = kill_cmd if kill_cmd else "echo 'No valid input provided'"


def preprocess(i):

    env = i['env']
    state = i['state']
    os_info = i['os_info']

    generate_kill_command(env)

    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    return {'return': 0}
