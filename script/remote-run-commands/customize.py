from mlc import utils
import os
import subprocess
import platform
from utils import is_true
import shlex

def copy_over_ssh(file, ssh_cmd, user, host, target_directory, logger):
    # Check if rsync is available
    rsync_available = True
    try:
        subprocess.run(["rsync", "--version"],
                       capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        rsync_available = False
    if not rsync_available:
        logger.info(f"⚠️  rsync not found. Skipping file copy for {file}")
        logger.info("   On Windows, install rsync via WSL, Cygwin, or use Git Bash")
        return {"error": 1, "error_msg": "rsync not found", "skip": "true"}
    cmd = [
        "rsync",
        "-avz",
        "-e", " ".join(ssh_cmd),   # rsync expects a single string here
        file,
        f"{user}@{host}:{target_directory}/"
    ]
    logger.info("Executing:", " ".join(cmd))
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
    logger.info(f"✅ Copied {file} successfully")
    return {"error": 0, "error_msg": "", "skip": "false"}

def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    cmd_string = ''

    logger = i["automation"].logger

    is_windows = os_info['platform'] == 'windows'

    # pre_run_cmds = env.get('MLC_SSH_PRE_RUN_CMDS', ['source $HOME/mlcflow/bin/activate'])
    pre_run_cmds = env.get('MLC_SSH_PRE_RUN_CMDS', [])

    files_to_copy = env.get('MLC_SSH_FILES_TO_COPY', [])

    if "<<<HOME>>>" in env.get('MLC_SSH_KEY_FILE', ''):
        env['MLC_SSH_KEY_FILE'] = env['MLC_SSH_KEY_FILE'].replace(
            "<<<HOME>>>", os.path.expanduser("~"))

    run_cmds = env.get('MLC_SSH_RUN_COMMANDS', [])

    run_cmds = pre_run_cmds + run_cmds

    for i, cmd in enumerate(run_cmds):
        if 'cm ' in cmd:
            # cmd=cmd.replace(":", "=")
            cmd = cmd.replace(";;", ",")
            run_cmds[i] = cmd

    # Use semicolon for Unix-like systems, the remote server will handle it
    cmd_string += " ; ".join(run_cmds)

    # Get username - on Windows, USERNAME is the env var, not USER
    user = env.get('MLC_SSH_USER', os.environ.get(
        'USER') or os.environ.get('USERNAME'))
    password = env.get('MLC_SSH_PASSWORD', None)
    host = env.get('MLC_SSH_HOST')
    port = env.get('MLC_SSH_PORT', '22')

    if password:
        password_string = " -p " + password
    else:
        password_string = ""

    ssh_cmd = ["ssh", "-p", port]

    if env.get("MLC_SSH_SKIP_HOST_VERIFY"):
        # Use NUL on Windows, /dev/null on Unix
        null_device = "NUL" if is_windows else "/dev/null"
        ssh_cmd += ["-o", "StrictHostKeyChecking=no",
                    "-o", f"UserKnownHostsFile={null_device}"]

    key_file = env.get("MLC_SSH_KEY_FILE")

    if not is_true(env.get('MLC_SKIP_SSH_KEY_FILE', '')):
        if key_file:
            ssh_cmd += ["-i", key_file]

    ssh_cmd_str = " ".join(ssh_cmd)

    # Use double quotes on Windows, single quotes on Unix for better
    # compatibility
    quote_char = '"' if is_windows else "'"
    ssh_run_command = ssh_cmd_str + " " + user + "@" + host + \
        password_string + " " + quote_char + cmd_string + quote_char
    env['MLC_SSH_CMD'] = ssh_run_command

    # ---- Use sshpass if password is provided (only on Unix-like systems) ----
    rsync_base = ["rsync", "-avz"]

    if password and not is_windows:
        rsync_base = ["sshpass", "-p", password] + rsync_base

    target_directory = env.get('MLC_SSH_TARGET_COPY_DIRECTORY', '')

    # ---- Execute copy commands ----
    for file in files_to_copy:
        r = copy_over_ssh(file, ssh_cmd, user, host, target_directory, logger)

    return {'return': 0}


def postprocess(i):

    os_info = i['os_info']

    env = i['env']

    logger = i["automation"].logger

    is_windows = os_info['platform'] == 'windows'

    files_to_copy_back = env.get('MLC_SSH_FILES_TO_COPY_BACK', [])

    user = env.get('MLC_SSH_USER', os.environ.get(
        'USER') or os.environ.get('USERNAME'))
    password = env.get('MLC_SSH_PASSWORD', None)
    host = env.get('MLC_SSH_HOST')
    port = env.get('MLC_SSH_PORT', '22')

    ssh_cmd = ["ssh", "-p", port]

    if env.get("MLC_SSH_SKIP_HOST_VERIFY"):
        # Use NUL on Windows, /dev/null on Unix
        null_device = "NUL" if is_windows else "/dev/null"
        ssh_cmd += ["-o", "StrictHostKeyChecking=no",
                    "-o", f"UserKnownHostsFile={null_device}"]

    key_file = env.get("MLC_SSH_KEY_FILE")
    if key_file:
        ssh_cmd += ["-i", key_file]

    # ---- Use sshpass if password is provided (only on Unix-like systems) ----
    rsync_base = ["rsync", "-avz"]

    if password and not is_windows:
        rsync_base = ["sshpass", "-p", password] + rsync_base

    target_directory = env.get('MLC_SSH_PATH_TO_COPY_BACK_FILES', '')
    # ---- Execute copy commands ----
    for file in files_to_copy_back:
        r = copy_over_ssh(file, ssh_cmd, user, host, target_directory, logger)

    return {'return': 0}
