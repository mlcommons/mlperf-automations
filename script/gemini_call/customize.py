from mlc import utils
import os
import json
import yaml


def write_gemini_yaml(model, system_prompt, user_prompt,
                      filename='gemini-prompt.yaml'):
    data = {
        'model': model,
        'contents': [
            {
                'role': 'user',
                'parts': [
                    {'text': f"{system_prompt}\n\n{user_prompt}"}
                ]
            }
        ],
        'generationConfig': {
            'temperature': 0.7,
            'maxOutputTokens': 200
        }
    }

    with open(filename, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)


def preprocess(i):
    env = i['env']
    state = i['state']

    if 'MLC_GEMINI_CONFIG_PATH' not in env or not os.path.exists(
            env['MLC_GEMINI_CONFIG_PATH']):
        if 'user_prompt' in state:
            model = env.get('MLC_GEMINI_MODEL', 'gemini-2.0-flash')
            user_prompt = state['user_prompt']
            system_prompt = state.get(
                'system_prompt',
                'You are an AI agent expected to answer questions correctly')
            write_gemini_yaml(
                model,
                system_prompt,
                user_prompt,
                'tmp-gemini-prompt.yaml')
            env['MLC_GEMINI_CONFIG_PATH'] = 'tmp-gemini-prompt.yaml'

    env['MLC_RUN_CMD'] = f'{env["MLC_PYTHON_BIN_WITH_PATH"]} "{os.path.join(env["MLC_TMP_CURRENT_SCRIPT_PATH"], "gemini_call.py")}"'

    return {'return': 0}


def postprocess(i):
    env = i['env']
    state = i['state']

    filename = 'tmp-gemini-results.json'
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    state['MLC_GEMINI_RESPONSE'] = data['content']
    os_info = i['os_info']
    return {'return': 0}
