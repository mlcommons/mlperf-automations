from mlc import utils
import os


def preprocess(i):
    env = i['env']
    if not env.get('MLC_AGENT_MODEL_URL') and not env.get('MLC_AGENT_MODEL_PATH'):
        return {'return': 1,
                'error': 'get-ml-model-agent-gguf needs --model_url=<gguf url> '
                         'or --model_path=<local file.gguf>'}
    return {'return': 0}


def postprocess(i):
    env = i['env']

    model_path = env.get('MLC_AGENT_MODEL_PATH', '')
    if not model_path or not os.path.isfile(model_path):
        return {'return': 1,
                'error': f'GGUF model not found after download: {model_path!r}'}

    env['MLC_ML_MODEL_FILE_WITH_PATH'] = model_path
    if not env.get('MLC_AGENT_MODEL_NAME'):
        env['MLC_AGENT_MODEL_NAME'] = os.path.basename(model_path)
    return {'return': 0}
