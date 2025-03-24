from mlc import utils
import os
import subprocess


def preprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    # Start constructing the argument string
    args = f"--subject \"{env.get('MLC_EMAIL_SUBJECT', '')}\" "

    # Process other arguments
    args += f"--to_addresses \"{','.join(env.get('MLC_TO_ADDRESS', []))}\" "
    args += f"--cc_addresses \"{env.get('MLC_CC_ADDRESS', '')}\" "
    args += f"--bcc_addresses \"{env.get('MLC_BCC_ADDRESS', '')}\" "
    args += f"--content_file \"{env.get('MLC_CONTENT_FILE', '')}\" "

    # Process attachments
    attachments = ' '.join(env.get('MLC_ATTACHMENTS', '').split())
    args += f"--attachments \"{attachments}\" "

    # Add flags for SMTP server, email and password if needed
    if env.get('USE_SMTP_SERVER'):
        args += "--use_smtp_server "
        args += f"--email \"{env.get('EMAIL', '')}\" "
        args += f"--password \"{env.get('PASSWORD', '')}\" "
        args += f"--smtp_server \"{env.get('SMTP_SERVER', '')}\" "

    subject = env.get('MLC_EMAIL_SUBJECT', '')
    to_address = ",".join(env.get('MLC_TO_ADDRESS', []))

    env['MLC_RUN_CMD'] = f"""{env['MLC_PYTHON_BIN_WITH_PATH'] {os.path.join(env['MLC_TMP_CURRENT_SCRIPT_PATH'], 'send-email.py')} {args}"""

    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    return {'return': 0}
