from mlc import utils
import os
import shutil


def preprocess(i):

    os_info = i['os_info']
    env = i['env']

#    print ('')
#    print ('Running preprocess function in customize.py ...')

    return {'return': 0}


def postprocess(i):

    os_info = i['os_info']
    env = i['env']
    state = i['state']
    automation = i['automation']
    logger = automation.action_object.logger

#    print ('')
#    print ('Running postprocess function in customize.py ...')

    # Saving predictions to JSON file to current directory
    # Should work with "cm docker script" ?

    data = state.get('mlc_app_image_classification_onnx_py', {})

    fjson = 'mlc-image-classification-onnx-py.json'
    fyaml = 'mlc-image-classification-onnx-py.yaml'

    output = env.get('MLC_APP_IMAGE_CLASSIFICATION_ONNX_PY_OUTPUT', '')
    if output != '':
        if not os.path.exists(output):
            os.makedirs(output)

        fjson = os.path.join(output, fjson)
        fyaml = os.path.join(output, fyaml)

    try:
        import json
        with open(fjson, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.warning('CM warning: {}'.format(e))
        logger.warning('CM warning: {}'.format(e))

    try:
        import yaml
        with open(fyaml, 'w', encoding='utf-8') as f:
            yaml.dump(data, f)
    except Exception as e:
        logger.warning('{}'.format(e))

    top_classification = data.get('top_classification', '')

    if top_classification != '':
        x = 'Top classification: {}'.format(top_classification)
        logger.info('=' * len(x))
        logger.info(x)

    return {'return': 0}
