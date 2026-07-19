import os
import json
import re


def preprocess(i):

    env = i['env']

    json_file = env.get('MLC_VALIDATE_JSON_FILE', '')
    if not json_file:
        return {'return': 1,
                'error': 'json_file is required (--json_file=<path>)'}

    if not os.path.isfile(json_file):
        return {'return': 1, 'error': f'JSON file not found: {json_file}'}

    with open(json_file, 'r') as f:
        raw = f.read()

    # Extract JSON block from potentially mixed log+json output
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if not match:
        return {'return': 1, 'error': 'No JSON object found in file'}

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError as e:
        return {'return': 1, 'error': f'Invalid JSON: {e}'}

    errors = []

    # Check return code
    expected_return = env.get('MLC_VALIDATE_EXPECTED_RETURN', '')
    if expected_return != '':
        actual = data.get('return')
        if actual != int(expected_return):
            errors.append(f'Expected return={expected_return}, got {actual}')

    # Check env keys exist
    env_keys = env.get('MLC_VALIDATE_ENV_KEYS', '')
    if env_keys:
        result_env = data.get('env', {})
        for key in env_keys.split(','):
            key = key.strip()
            if key and key not in result_env:
                errors.append(f'Expected env key "{key}" not found')

    # Check env keys do NOT exist
    not_env_keys = env.get('MLC_VALIDATE_NOT_ENV_KEYS', '')
    if not_env_keys:
        result_env = data.get('env', {})
        for key in not_env_keys.split(','):
            key = key.strip()
            if key and key in result_env:
                errors.append(
                    f'Env key "{key}" should not be present but was found')

    # Check env key=value pairs (format: KEY=VALUE;KEY2=VALUE2)
    env_key_values = env.get('MLC_VALIDATE_ENV_KEY_VALUES', '')
    if env_key_values:
        result_env = data.get('env', {})
        for pair in env_key_values.split(';'):
            if '=' in pair:
                k, v = pair.split('=', 1)
                k = k.strip()
                v = v.strip()
                actual_v = result_env.get(k)
                if actual_v is None:
                    errors.append(f'Expected env key "{k}" not found')
                elif str(actual_v) != v:
                    errors.append(f'Expected env {k}="{v}", got "{actual_v}"')

    # Check dep tags exist in deps list (semicolon-separated groups)
    dep_tags = env.get('MLC_VALIDATE_DEP_TAGS', '')
    if dep_tags:
        deps = data.get('deps', [])
        all_dep_tags = [d.get('tags', '') for d in deps]
        for tag_set in dep_tags.split(';'):
            tag_set = tag_set.strip()
            if tag_set and not any(tag_set in t for t in all_dep_tags):
                errors.append(
                    f'Expected dep tags "{tag_set}" not found in deps: {all_dep_tags}')

    if errors:
        error_msg = 'JSON validation failed:\n' + \
            '\n'.join(f'  - {e}' for e in errors)
        return {'return': 1, 'error': error_msg}

    print('JSON validation PASSED')
    return {'return': 0}


def postprocess(i):
    return {'return': 0}
