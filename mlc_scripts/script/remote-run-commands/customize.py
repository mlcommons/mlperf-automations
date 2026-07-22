from mlc import utils
import os
import subprocess
import platform
from utils import is_true
import shlex


def copy_over_ssh(file, ssh_cmd, user, host,
                  target_directory, logger, copy_back=False,
                  password=None, is_windows=False):
    # Check if rsync is available
    rsync_available = True
    try:
        subprocess.run(["rsync", "--version"],
                       capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        rsync_available = False
    if not rsync_available:
        logger.info(f"⚠️  rsync not found. Skipping file copy for {file}")
        logger.info(
            "   On Windows, install rsync via WSL, Cygwin, or use Git Bash")
        return {"error": 1, "error_msg": "rsync not found", "skip": "true"}
    if copy_back:
        cmd = [
            "rsync",
            "-avz",
            "-e", " ".join(ssh_cmd),   # rsync expects a single string here
            f"{user}@{host}:{file}",
            target_directory
        ]
    else:
        cmd = [
            "rsync",
            "-avz",
            "-e", " ".join(ssh_cmd),   # rsync expects a single string here
            file,
            f"{user}@{host}:{target_directory}/"
        ]
    subprocess_env = os.environ
    if password and not is_windows:
        # sshpass -e (reads SSHPASS from the environment) instead of -p
        # <password>, so the password never appears in argv/logged command.
        cmd = ["sshpass", "-e"] + cmd
        subprocess_env = {**os.environ, "SSHPASS": password}
    logger.info(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        env=subprocess_env,
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

    post_run_cmds = env.get('MLC_SSH_POST_RUN_CMDS', [])

    run_cmds = pre_run_cmds + run_cmds + post_run_cmds

    for i, cmd in enumerate(run_cmds):
        if 'cm ' in cmd:
            # cmd=cmd.replace(":", "=")
            cmd = cmd.replace(";;", ",")
            run_cmds[i] = cmd

    # Use semicolon for Unix-like systems, the remote server will handle it
    cmd_string += " ; ".join(run_cmds)

    # Escape single quotes so cmd_string survives SSH single-quote wrapping
    if not is_windows:
        cmd_string = cmd_string.replace("'", "'\\''")

    # Get username - on Windows, USERNAME is the env var, not USER
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

    if not is_true(env.get('MLC_SKIP_SSH_KEY_FILE', '')):
        if key_file:
            ssh_cmd += ["-i", key_file]

    ssh_cmd_str = " ".join(ssh_cmd)

    if is_windows:
        safe_cmd_string = subprocess.list2cmdline([cmd_string])
    else:
        safe_cmd_string = shlex.quote(cmd_string)

    # sshpass -e (reads SSHPASS from the environment) instead of -p
    # <password>: run.sh/run.bat unconditionally echo MLC_SSH_CMD before
    # eval'ing it, so the password must never appear inside the command
    # string itself. SSHPASS is exported into run.sh's shell below since
    # run.sh exports every key in this env dict.
    if password and not is_windows:
        ssh_prefix = "sshpass -e "
        env['SSHPASS'] = password
    else:
        ssh_prefix = ""

    remote_shell = env.get('MLC_SSH_REMOTE_SHELL', '')
    if remote_shell:
        # Pipe commands to the specified shell on the remote to avoid nested
        # quoting issues
        ssh_run_command = f"printf '%s\\n' {safe_cmd_string} | {ssh_prefix}{ssh_cmd_str} {user}@{host} {remote_shell}"
    else:
        ssh_run_command = f"{ssh_prefix}{ssh_cmd_str} {user}@{host} {safe_cmd_string}"

    env['MLC_SSH_CMD'] = ssh_run_command

    target_directory = env.get('MLC_SSH_TARGET_COPY_DIRECTORY', '')

    # ---- Execute copy commands ----
    for file in files_to_copy:
        r = copy_over_ssh(file, ssh_cmd, user, host, target_directory, logger,
                          password=password, is_windows=is_windows)

    return {'return': 0}


def postprocess(i):

    os_info = i['os_info']

    env = i['env']

    logger = i["automation"].logger

    is_windows = os_info['platform'] == 'windows'

    files_to_copy_back = env.get('MLC_SSH_FILES_TO_COPY_BACK', [])
    if isinstance(files_to_copy_back, str):
        files_to_copy_back = [files_to_copy_back]

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

    if not is_true(env.get('MLC_SKIP_SSH_KEY_FILE', '')):
        key_file = env.get("MLC_SSH_KEY_FILE")
        if key_file:
            ssh_cmd += ["-i", key_file]

    target_directory = env.get('MLC_SSH_PATH_TO_COPY_BACK_FILES', '') or '.'
    # ---- Execute copy commands ----
    for file in files_to_copy_back:
        r = copy_over_ssh(
            file,
            ssh_cmd,
            user,
            host,
            target_directory,
            logger,
            copy_back=True,
            password=password,
            is_windows=is_windows)

    return {'return': 0}
