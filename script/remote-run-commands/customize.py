from mlc import utils
import os
import subprocess

def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    cmd_string = ''

    # pre_run_cmds = env.get('MLC_SSH_PRE_RUN_CMDS', ['source $HOME/cm/bin/activate'])
    pre_run_cmds = env.get('MLC_SSH_PRE_RUN_CMDS', [])

    files_to_copy = env.get('MLC_SSH_FILES_TO_COPY', [])

    run_cmds = env.get('MLC_SSH_RUN_COMMANDS', [])

    run_cmds = pre_run_cmds + run_cmds

    for i, cmd in enumerate(run_cmds):
        if 'cm ' in cmd:
            # cmd=cmd.replace(":", "=")
            cmd = cmd.replace(";;", ",")
            run_cmds[i] = cmd

    cmd_string += " ; ".join(run_cmds)
    user = env.get('MLC_SSH_USER', os.environ.get('USER'))
    password = env.get('MLC_SSH_PASSWORD', None)
    host = env.get('MLC_SSH_HOST')
    if password:
        password_string = " -p " + password
    else:
        password_string = ""


    ssh_cmd = ["ssh"]

    if env.get("MLC_SSH_SKIP_HOST_VERIFY"):
        ssh_cmd += ["-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null"]

    key_file = env.get("MLC_SSH_KEY_FILE")
    if key_file:
        ssh_cmd += ["-i", key_file]

    ssh_cmd_str = " ".join(ssh_cmd)



    ssh_run_command = ssh_cmd_str + " " +user + "@" + host + \
        password_string + " '" + cmd_string + "'"
    env['MLC_SSH_CMD'] = ssh_run_command


    # ---- Use sshpass if password is provided ----
    rsync_base = ["rsync", "-avz"]

    if password:
        rsync_base = ["sshpass", "-p", password] + rsync_base

    # ---- Execute copy commands ----
    for file in files_to_copy:
        cmd = [
            "rsync",
            "-avz",
            "-e", " ".join(ssh_cmd),   # rsync expects a single string here
            file,
            f"{user}@{host}:",
        ]

        print("Executing:", " ".join(cmd))

        result = subprocess.run(
            cmd,
            env=os.environ,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"❌ rsync failed for {file}\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )

        print(f"✅ Copied {file} successfully")


    return {'return': 0}


def postprocess(i):

    return {'return': 0}
