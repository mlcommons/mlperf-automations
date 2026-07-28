import os
import shutil


def _resolve_redfishtool_bin(env, python_bin, logger):
    """Find the redfishtool executable installed by the
    get,generic-python-lib,_package.redfishtool dependency.

    Resolution order:
      1. Explicit override via --redfishtool_bin / MLC_REDFISH_TOOL_BIN.
      2. Whatever 'redfishtool' resolves to on PATH.
      3. A console script installed alongside the resolved Python
         interpreter (pip installs put console scripts in the same bin/
         directory as python/pip for that environment).
    """
    override = env.get('MLC_REDFISH_TOOL_BIN', '').strip()
    if override:
        return override

    on_path = shutil.which('redfishtool')
    if on_path:
        return on_path

    sibling = os.path.join(os.path.dirname(python_bin), 'redfishtool')
    if os.path.exists(sibling):
        return sibling

    logger.warning(
        'Could not locate the redfishtool executable on PATH or next to '
        f'{python_bin}; falling back to bare "redfishtool" and hoping '
        'it resolves at run.sh execution time.')
    return 'redfishtool'


def preprocess(i):
    env = i['env']
    logger = i['automation'].logger

    python_bin = env.get('MLC_PYTHON_BIN_WITH_PATH', '').strip()
    if not python_bin:
        return {
            'return': 1, 'error': 'MLC_PYTHON_BIN_WITH_PATH not set — get,python dependency failed'}

    script_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'get_redfish_power_info.py'
    )

    redfishtool_bin = _resolve_redfishtool_bin(env, python_bin, logger)
    env['MLC_REDFISH_TOOL_BIN'] = redfishtool_bin

    # MLC_OUTDIRNAME is set and chdir'd to by the engine before preprocess() runs.
    # Fall back to cwd for standalone / non-mlcr invocations.
    outdir = env.get('MLC_OUTDIRNAME', '') or os.getcwd()

    scope = env.get('MLC_REDFISH_SCOPE', 'full') or 'full'
    lean_scope = scope == 'inference-optional-nameplate'

    endpoint = env.get('MLC_REDFISH_ENDPOINT', 'http://localhost:8000')
    username = env.get('MLC_REDFISH_USERNAME', '')
    password = env.get('MLC_REDFISH_PASSWORD', '')

    cmd_parts = [python_bin, script_path,
                 f'--endpoint={endpoint}',
                 f'--redfishtool-bin={redfishtool_bin}',
                 f'--scope={scope}']

    if username:
        cmd_parts += [f'--username={username}', f'--password={password}']

    nameplate_output = env.get('MLC_REDFISH_NAMEPLATE_OUTPUT_FILE', '')
    if lean_scope and not nameplate_output:
        # The lean scope's only purpose is the nameplate file, so give it a
        # sensible default rather than making the caller supply one.
        nameplate_output = 'redfish_nameplate_power.yaml'

    if not lean_scope:
        output_file = env.get('MLC_REDFISH_OUTPUT_FILE', 'redfish_capture.yaml')
        if not os.path.isabs(output_file):
            output_file = os.path.join(outdir, output_file)
        env['MLC_REDFISH_OUTPUT_FILE'] = output_file
        cmd_parts.append(f'--output={output_file}')

    if nameplate_output:
        if not os.path.isabs(nameplate_output):
            nameplate_output = os.path.join(outdir, nameplate_output)
        env['MLC_REDFISH_NAMEPLATE_OUTPUT_FILE'] = nameplate_output
        system_name = env.get('MLC_REDFISH_SYSTEM_NAME', 'System')
        cmd_parts += [f'--nameplate-output={nameplate_output}',
                      f'--system-name={system_name}']
    elif lean_scope:
        return {
            'return': 1,
            'error': '_inference_optional_nameplate requires a nameplate output '
                     'path (MLC_REDFISH_NAMEPLATE_OUTPUT_FILE) — this should never '
                     'happen given the default set above; check meta.yaml default_env.'}

    env['MLC_REDFISH_CMD'] = ' '.join(
        f'"{p}"' if ' ' in p else p for p in cmd_parts)
    logger.info(f'Redfish capture command: {env["MLC_REDFISH_CMD"]}')

    return {'return': 0}


def postprocess(i):
    env = i['env']
    logger = i['automation'].logger

    scope = env.get('MLC_REDFISH_SCOPE', 'full') or 'full'
    lean_scope = scope == 'inference-optional-nameplate'

    if not lean_scope:
        output_file = env.get('MLC_REDFISH_OUTPUT_FILE', '')
        if output_file and os.path.exists(output_file):
            env['MLC_REDFISH_OUTPUT_FILE_PATH'] = output_file
            logger.info(f'Redfish power info written to: {output_file}')
        else:
            logger.warning(f'Expected output file not found: {output_file}')

    nameplate_output = env.get('MLC_REDFISH_NAMEPLATE_OUTPUT_FILE', '')
    if nameplate_output:
        if os.path.exists(nameplate_output):
            env['MLC_REDFISH_NAMEPLATE_OUTPUT_FILE_PATH'] = nameplate_output
            logger.info(
                f'Redfish nameplate power YAML written to: {nameplate_output}')
        else:
            logger.warning(
                f'Nameplate power YAML not found (no PSU data from BMC?): {nameplate_output}')

    return {'return': 0}
