from mlc import utils
import os
import subprocess


def preprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    # Start constructing the argument string
    args = f"--subject '{env.get('MLC_EMAIL_SUBJECT', '')}' "


    # Process other arguments
    args += f"--to_addresses '{env.get('MLC_EMAIL_TO_ADDRESSES', '')}' "
    args += f"--cc_addresses '{env.get('MLC_EMAIL_CC_ADDRESSES', '')}' "
    args += f"--bcc_addresses '{env.get('MLC_EMAIL_BCC_ADDRESSES', '')}' "
    args += f"--content_file '{env.get('MLC_EMAIL_CONTENT_FILE', '')}' "


    # Process attachments
    args += f"--attachments '{env.get('MLC_EMAIL_ATTACHMENTS', '')}'"

    # Add flags for SMTP server, email and password if needed
    if env.get('MLC_EMAIL_USE_SMTP_SERVER'):
        args += "--use_smtp_server "
        args += f"--email '{env.get('MLC_EMAIL_SMPT_EMAIL', '')}' "
        args += f"--password '{env.get('MLC_EMAIL_SMTP_PASSWORD', '')}' "
        args += f"--smtp_server '{env.get('MLC_EMAIL_SMTP_SERVER', '')}' "

    subject = env.get('MLC_EMAIL_SUBJECT', '')
    to_address = ",".join(env.get('MLC_EMAIL_TO_ADDRESS', []))

    env['MLC_RUN_CMD'] = f"""{env['MLC_PYTHON_BIN_WITH_PATH']} {os.path.join(env['MLC_TMP_CURRENT_SCRIPT_PATH'], 'send-email.py')} {args}"""

    print(env)
    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    return {'return': 0}
