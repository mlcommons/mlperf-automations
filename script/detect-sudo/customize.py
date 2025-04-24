from mlc import utils
from utils import is_true
import os
import subprocess
import select
import sys
import grp
import threading
import getpass


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    logger = automation.logger

    quiet = is_true(env.get('MLC_QUIET', False))

    if os.geteuid() == 0:
        env['MLC_SUDO'] = ''  # root user does not need sudo
        env['MLC_SUDO_USER'] = "yes"
    else:
        if can_execute_sudo_without_password(logger) or prompt_sudo(logger) == 0:
            env['MLC_SUDO_USER'] = "yes"
            env['MLC_SUDO'] = 'sudo'

        else:
            env['MLC_SUDO_USER'] = "no"
            env['MLC_SUDO'] = ''

    return {'return': 0}


def can_execute_sudo_without_password(logger):
    try:
        # Run a harmless command using sudo
        result = subprocess.run(
            # -n prevents sudo from prompting for a password
            ['sudo', '-n', 'true'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Check the return code; if it's 0, sudo executed without needing a
        # password
        if result.returncode == 0:
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return False


def reset_terminal():
    """Reset terminal to default settings."""
    subprocess.run(['stty', 'sane'])


def prompt_retry(logger, timeout=10, default_retry=False):
    """Prompt the user with a yes/no question to retry the command, with a 10-second timeout."""

    # Check if we're in an interactive terminal
    if not sys.stdin.isatty():
        if default_retry:
            logger.info(f"Non-interactive environment detected. Automatically retrying.")
        else:
            logger.warning(f"Non-interactive environment detected. Skipping retry.")
        return default_retry  # Automatically use the default in non-interactive terminals

    print(
        f"Timeout occurred. Do you want to try again? (y/n): ",
        end='',
        flush=True)

    # Use select to wait for user input with a timeout
    ready, _, _ = select.select([sys.stdin], [], [], timeout)

    if ready:
        answer = sys.stdin.readline().strip().lower()
        if answer in ['y', 'n']:
            return answer == 'y'  # Return True if 'y', False if 'n'
        logger.error("\nInvalid input. Please enter 'y' or 'n'.")
        return prompt_retry(logger, timeout)  # Re-prompt on invalid input
    else:
        logger.info("\nNo input received in 10 seconds. Exiting.")
        return False  # No input within the timeout, so don't retry


def is_user_in_sudo_group(logger):
    """Check if the current user is in the 'sudo' group."""
    try:
        sudo_group = grp.getgrnam('sudo').gr_mem
        return os.getlogin() in sudo_group
    except KeyError:
        # 'sudo' group doesn't exist (might be different on some systems)
        return False
    except Exception as e:
        logger.error(f"Error checking sudo group: {str(e)}")
        return False


def timeout_input(prompt, timeout=15, default=""):
    """Prompt user for input with a timeout (cross-platform)."""
    result = [default]  # Store the input result

    def get_input():
        try:
            result[0] = getpass.getpass(prompt)
        except EOFError:  # Handle Ctrl+D or unexpected EOF
            result[0] = default

    input_thread = threading.Thread(target=get_input)
    input_thread.daemon = True  # Daemonize thread
    input_thread.start()
    input_thread.join(timeout)  # Wait for input with timeout

    return result[0]  # Return user input or default


def prompt_sudo(logger):
    if os.geteuid() != 0 and not is_user_in_sudo_group(logger):  # No sudo required for root user

        # Prompt for the password

        if not os.isatty(sys.stdin.fileno()):
            logger.warning("Skipping password prompt - non-interactive terminal detected!")
            password = None
        else:
            # password = getpass.getpass("Enter password (-1 to skip): ")
            password = timeout_input(
                "Enter password (-1 to skip): ",
                timeout=15,
                default=None)

        # Check if the input is -1
        if password == "-1":
            logger.warning("Skipping sudo command.")
            return -1

        # Run the command with sudo, passing the password
        try:
            if password is None:
                r = subprocess.check_output(
                    ['sudo', '-S', 'echo'],
                    text=True,
                    stderr=subprocess.STDOUT,
                    timeout=15      # Capture the command output
                )
            else:
                r = subprocess.check_output(
                    ['sudo', '-S', 'echo'],
                    input=password + "\n",  # Pass the password to stdin
                    text=True,
                    stderr=subprocess.STDOUT,
                    timeout=15      # Capture the command output
                )
            return 0
        except subprocess.TimeoutExpired:
            logger.info("Timedout")
            reset_terminal()  # Reset terminal to sane state
            if not prompt_retry():  # If the user chooses not to retry or times out
                return -1
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e.output.decode('utf-8')}")
            reset_terminal()  # Reset terminal in case of failure
            return -1
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            reset_terminal()  # Always reset terminal after error
            return -1

    return 0


def postprocess(i):

    env = i['env']

    return {'return': 0}
