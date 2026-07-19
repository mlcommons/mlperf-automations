from mlc import utils
import os
import subprocess
import json


import yaml


def write_openai_yaml(model, system_prompt, user_prompt,
                      filename='openai-prompt.yaml'):
    data = {
        'model': model,
        'messages': [
            {
                'role': 'system',
                'content': system_prompt
            },
            {
                'role': 'user',
                'content': user_prompt
            }
        ],
        'max_tokens': 200,
        'temperature': 0.7
    }

    with open(filename, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)


def preprocess(i):

    env = i['env']
    state = i['state']

    if 'MLC_OPENAI_CONFIG_PATH' not in env or not os.path.exists(
            env['MLC_OPENAI_CONFIG_PATH']):
        if 'user_prompt' in state:
            model = env.get('MLC_OPENAI_MODEL', 'gpt-4o')
            user_prompt = state['user_prompt']
            system_prompt = state.get(
                'system_prompt',
                'You are an AI agent expected to answer questions correctly')
            write_openai_yaml(
                model,
                system_prompt,
                user_prompt,
                'tmp-openai-prompt.yaml')
            env['MLC_OPENAI_CONFIG_PATH'] = 'tmp-openai-prompt.yaml'

    os_info = i['os_info']

    env['MLC_RUN_CMD'] = f"""{env['MLC_PYTHON_BIN_WITH_PATH']} {os.path.join(env['MLC_TMP_CURRENT_SCRIPT_PATH'], 'openai_call.py')} """

    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    filename = 'tmp-openai-results.json'
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    state['MLC_OPENAI_RESPONSE'] = data['content']

    os_info = i['os_info']

    return {'return': 0}
