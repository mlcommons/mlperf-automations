import os


def preprocess(i):
    env = i['env']
    logger = i['automation'].logger

    python_bin = env.get('MLC_PYTHON_BIN_WITH_PATH', '').strip()
    if not python_bin:
        return {'return': 1, 'error': 'MLC_PYTHON_BIN_WITH_PATH not set — get,python dependency failed'}

    script_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'get_redfish_power_info.py'
    )

    output_file = env.get('MLC_REDFISH_OUTPUT_FILE', 'redfish_capture.yaml')
    if not os.path.isabs(output_file):
        output_file = os.path.join(os.getcwd(), output_file)
    env['MLC_REDFISH_OUTPUT_FILE'] = output_file

    endpoint = env.get('MLC_REDFISH_ENDPOINT', 'http://localhost:8000')
    username = env.get('MLC_REDFISH_USERNAME', '')
    password = env.get('MLC_REDFISH_PASSWORD', '')
    insecure = env.get('MLC_REDFISH_INSECURE', 'yes')

    cmd_parts = [python_bin, script_path,
                 f'--endpoint={endpoint}',
                 f'--output={output_file}']

    if username:
        cmd_parts += [f'--username={username}', f'--password={password}']

    insecure_lower = insecure.lower()
    if insecure_lower in ('yes', 'true', '1', 'on'):
        cmd_parts.append('--insecure')
    else:
        cmd_parts.append('--no-insecure')

    env['MLC_REDFISH_CMD'] = ' '.join(f'"{p}"' if ' ' in p else p for p in cmd_parts)
    logger.info(f'Redfish capture command: {env["MLC_REDFISH_CMD"]}')

    return {'return': 0}


def postprocess(i):
    env = i['env']
    logger = i['automation'].logger

    output_file = env.get('MLC_REDFISH_OUTPUT_FILE', '')
    if output_file and os.path.exists(output_file):
        env['MLC_REDFISH_OUTPUT_FILE_PATH'] = output_file
        logger.info(f'Redfish power info written to: {output_file}')
    else:
        logger.warning(f'Expected output file not found: {output_file}')

    return {'return': 0}
